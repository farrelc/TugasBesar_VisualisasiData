import numpy as np
import pandas as pd
import geopandas as gpd
from bokeh.io import curdoc
from bokeh.models import (ColorBar, ColumnDataSource,
                          GeoJSONDataSource, HoverTool,
                          LinearColorMapper, Slider, Select,
                          TableColumn, DataTable)
from bokeh.layouts import grid
from bokeh.palettes import brewer
from bokeh.plotting import figure

df = pd.read_csv('data/players_active.csv')
gdf = gpd.read_file('map/ne_110m_admin_0_countries.shp')[['ADMIN', 'geometry']]
gdf.columns = ['country', 'geometry']

gdf_merge = gdf.merge(df, left_on='country', right_on='country_of_birth')

gdf_map = gdf_merge.copy()
gdf_map.drop_duplicates(subset=['country'], keep='first', inplace=True)
gdf_map = gdf_map[['country', 'geometry']]

count_players_df = pd.DataFrame(df['country_of_birth'].value_counts()).reset_index()
count_players_df.columns = ['country', 'counts']
gdf_map =  gdf_map.merge(count_players_df, left_on='country', right_on='country')

# Input GeoJSON source that contains features for plotting
geosource = GeoJSONDataSource(geojson = gdf_map.to_json())

# Define color palettes
palette = brewer['BuGn'][6]
palette = palette[::-1]

# Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
color_mapper = LinearColorMapper(palette = palette, low = 0, high = 600)

# Define custom tick labels for color bar.
tick_labels = {'0': '0', '100': '100',
               '200': '200', '300': '300',
               '400': '400', '500': '500',
               '600': '600'
               }
# Create color bar.
color_bar = ColorBar(color_mapper = color_mapper, 
                     label_standoff = 6,
                     width = 500, height = 20,
                     border_line_color = None,
                     location = (0,0), 
                     orientation = 'horizontal',
                     major_label_overrides = tick_labels)
               
# Create figure object.
p = figure(title = 'World Active Football Player Distribution Map, 2021', 
           plot_height = 600,
           plot_width = 950, 
           toolbar_location = 'below',
           tools = "pan, wheel_zoom, box_zoom, reset")
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
# Add patch renderer to figure.
country = p.patches('xs','ys', source = geosource,
                   fill_color = {'field': 'counts',
                                 'transform' : color_mapper},
                   line_color = 'gray', 
                   line_width = 0.25, 
                   fill_alpha = 1)
# Create hover tool
p.add_tools(HoverTool(renderers = [country],
                      tooltips = [('Country','@country'),
                                ('Population','@counts')]))
# Specify layout
p.add_layout(color_bar, 'below')

# Import data of football players 
p_df = pd.read_csv('data/final.csv')
sitesource = ColumnDataSource(p_df)

# Plots the football players 
sites = p.circle('LongitudeMeasure', 'LatitudeMeasure', source = sitesource, color = 'red', 
                 size = 5, alpha = 0.3)
# Add hover tool
p.add_tools(HoverTool(renderers = [sites],
                      tooltips = [
                                  ('Name', '@pretty_name'),
                                  ('Age', '@age'),
                                  ('Country', '@country'),
                                  ('Position', '@position'),
                                  ('Market Value in £ (Pounds)', '@value'),
                                  ]))

def update(attr, old, new):
    df_temp = p_df.copy() 
    age = slider.value
    option = opt_select.value
    country = ct_select.value
    if option == 'Default':
        slider.visible = False
        df_temp = p_df.copy()
    else:
        slider.visible = True
        df_temp = p_df[p_df['age'] == int(age)]
    
    if country == 'All':
        table.visible = True
        df_temp = df_temp
    elif country == 'Only Populations':
        table.visible = False
        df_temp = df_temp[df_temp['country'] == '']
    else:
        table.visible = True
        df_temp = df_temp[df_temp['country'] == country]
    sitesource.data = df_temp

# Creating Slider
slider = Slider(title='Age', start=16, end=40, step=1, value=16)

# Changing value
slider.on_change('value', update)

# Create a dropdown Select widget for the show option: opt_select
opt_select = Select(
    options=['Default', 'Filter by Age'],
    value='Default',
    title='Optional'
)
# Attach the update_plot callback to the 'value' property of opt_select
opt_select.on_change('value', update)

# Get country
countries = list(np.unique(np.array(p_df['country'])))
countries.insert(0, 'Only Populations')
countries.insert(0, 'All')

# Create a dropdown Select widget for the countries data: ct_select
ct_select = Select(
    options=countries,
    value='All',
    title='Country',
    width=940
)
# Attach the update_plot callback to the 'value' property of ct_select
ct_select.on_change('value', update)

# Create column for table
columns = [
    TableColumn(field="pretty_name", title="Name"),
    TableColumn(field="age", title="Age"),
    TableColumn(field="country", title="Country"),
    TableColumn(field="position", title="Position"),
    TableColumn(field="market_value_in_gbp", title="Market Value in £"),
]
table = DataTable(source=sitesource, columns=columns, width=550, height=600)

# Make a column layout of widgetbox(slider) and plot, and add it to the current document
slider.visible = False
layout = grid([ct_select, [p, table], [opt_select, slider]])

curdoc().add_root(layout)