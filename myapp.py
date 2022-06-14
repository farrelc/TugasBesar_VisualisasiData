# !pip install geopandas
# !pip install pyshp

import pandas as pd
import geopandas as gpd
import json
from bokeh.io import curdoc
from bokeh.models import (CDSView, ColorBar, ColumnDataSource,
                          CustomJS, CustomJSFilter, 
                          GeoJSONDataSource, HoverTool,
                          LinearColorMapper, Slider)
from bokeh.layouts import column, row, widgetbox
from bokeh.palettes import brewer
from bokeh.plotting import figure

import re
import random
import shapefile
from shapely.geometry import shape, Point

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

# Create shapely.Point objects based on longitude and latitude
df_cleaned = pd.read_csv('data/final.csv')
geometry = []
for index, row in df_cleaned.iterrows():
    geometry.append(Point(row['LongitudeMeasure'], 
                          row['LatitudeMeasure']))
lead_sites_contig = df_cleaned.copy()
lead_sites_contig['geometry'] = geometry

# Read dataframe to geodataframe
lead_sites_crs = {'init': 'epsg:4326'}
lead_sites_geo = gpd.GeoDataFrame(lead_sites_contig,
                                  crs = lead_sites_crs,
                             geometry = lead_sites_contig.geometry)
# Get x and y coordinates
lead_sites_geo['x'] = [geometry.x for geometry in lead_sites_geo['geometry']]
lead_sites_geo['y'] = [geometry.y for geometry in lead_sites_geo['geometry']]
p_df = lead_sites_geo.drop('geometry', axis = 1).copy()
p_df = p_df[['country', 'pretty_name', 'position', 'value', 'age', 'x', 'y']]

sitesource = ColumnDataSource(p_df)

# Plots the water sampling sites based on month in slider
sites = p.circle('x', 'y', source = sitesource, color = 'red', 
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
# Make a column layout of widgetbox(slider) and plot, and add it to the current document
layout = column(p)
curdoc().add_root(layout)