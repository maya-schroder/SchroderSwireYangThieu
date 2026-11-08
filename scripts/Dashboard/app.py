# Step 1: import packages and read in data
import pandas as pd
import geopandas as gpd
import folium 
import seaborn as sns
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from shiny import App, render, req, ui




# Set sns theme
sns.set_theme(
    style='white',
    font='sans-serif'
    )

root_fldr = Path(__file__).resolve().parents[2] 
raw_fldr = root_fldr / 'data' / 'raw'
processed_fldr = root_fldr / 'data' / 'processed'

county_income = pd.read_csv(
    processed_fldr/'County_Income_CFP_2022_2024.csv',
    dtype={'GEOID': 'str'},
    )

county_fire = pd.read_csv(
    processed_fldr/'fire_by_county_2022_2024.csv',
    )
county_fire = county_fire.drop(columns=['Unnamed: 0', 'geometry'])

trends_data = pd.read_csv(
    processed_fldr/'County_Income_CFP_Fire_2022_2024.csv'
)

colors = {2022:'#AA4A44', 2023:'#FF3131'}

# Join Fair Plan and fire data
fire_totals = (
    county_fire
    .groupby(['county_name', 'year'], as_index=False)
    .agg(acres_burned_total=('acres_burned', 'sum'),
         total_fires = ('fire_name', 'count'))
)

fire_totals['county'] = fire_totals['county_name'].str.replace(' County', '')

fire_totals = fire_totals[['county', 'year', 'acres_burned_total', 'total_fires']]


all_data = pd.merge(
    left=county_income, 
    right=fire_totals,
    on=['county', 'year']
)

all_data['acres_burned_total'] = all_data['acres_burned_total'].fillna(0)

data_wide = (
    all_data.
    pivot_table(
        index = 'county',
        columns= 'year',
        values=['policies', 'acres_burned_total', 'total_fires', 'Median_income']
    )
)

data_wide.columns = [f"{year}_{val}" for val, year in data_wide.columns]

data_wide = data_wide.reset_index()

data_wide = data_wide.assign(
    policy_pct_change = lambda df: (df['2024_policies'] / df['2023_policies'] - 1) * 100
)

fp_fire_comp = data_wide[['county','policy_pct_change', '2023_acres_burned_total', '2023_total_fires']]

fire_plot_data = (fp_fire_comp
                  .loc[(fp_fire_comp['2023_acres_burned_total'] > 0) & (fp_fire_comp['policy_pct_change'] > 0)]
                  )

data_wide_2223 = data_wide.assign(
    policy_pct_change = lambda df: (df['2023_policies'] / df['2022_policies'] - 1) * 100
)

fp_fire_comp_2223 = data_wide_2223[['county','policy_pct_change', '2022_acres_burned_total', '2022_total_fires']]


fire_plot_data_22_23 = (fp_fire_comp_2223
                  .loc[(fp_fire_comp_2223['2022_acres_burned_total'] > 0) & (fp_fire_comp_2223['policy_pct_change'] > 0)]
                  )

fire_plot_data_all = pd.concat(
    [(fire_plot_data_22_23.assign(starting_year = 2022).rename(
        columns={'2022_acres_burned_total':'acres_burned_total','2022_total_fires':'total_fires'}
        )), (fire_plot_data.assign(starting_year = 2023).rename(
        columns={'2023_acres_burned_total':'acres_burned_total','2023_total_fires':'total_fires'}
        ))], ignore_index=True
)

#inserting file paths for the wildifre and income connect
fire_data = pd.read_csv(processed_fldr / 'fire_by_county_2022_2024.csv')
income_data = pd.read_csv(processed_fldr / 'County_Income_CFP_2022_2024.csv')

fire_data_clean = fire_data.drop(columns=[
    'Unnamed: 0', 'sqmi_burned', 'cause_description', 'fire_length_days'
])

income_data_clean = (
    income_data
    .assign(county_name = lambda d: d['county'].str.strip() + ' County')
    .drop(columns=['county', 'GEOID'])
)

fire_income_joined = fire_data_clean.merge(
    income_data_clean[['county_name', 'year', 'Median_income', 'policies', 'exposure']],
    on=['county_name', 'year'],
    how='left',
)

county_fire_summary = (
    fire_income_joined
    .groupby(['county_name', 'year'], as_index=False)
    .agg(
        total_acres_burned=('acres_burned', 'sum'),
        number_of_fires=('fire_name', 'nunique'),
        county_median_income=('Median_income', 'first'),
        county_policies=('policies', 'first'),
        county_exposure=('exposure', 'first')
    )
    .round({'total_acres_burned': 2})
)

# loading shapefiles in for the connect 
fire_shp = raw_fldr / 'cal_fire_historical_data' / 'California_Historic_Fire_Perimeters_-6302641808644124224.zip'
ca_county_boundaries = raw_fldr / 'ca_counties_boundaries.zip'

#aligning epsg to ensure the wildfire and income county data are the same coordinate system 
wildfires_gdf = gpd.read_file(fire_shp).to_crs(epsg=3310)
ca_counties_gdf = gpd.read_file(ca_county_boundaries).to_crs(epsg=3310)

#KEY FILTER!! Choosing the years to display in the widget
wildfires_gdf = wildfires_gdf[wildfires_gdf['YEAR_'].isin([2022, 2023, 2024])]
wildfires_gdf['geometry'] = wildfires_gdf.geometry.simplify(100) #simplifying the polygons to display faster in widget


# creating a flexible widget to be used in the master app to choose the year to display data
def build_map(map_year):
    counties_year = (
        ca_counties_gdf[['CDTFA_COUN', 'geometry']]
        .rename(columns={'CDTFA_COUN': 'county_name'})
        .merge(
            income_data_clean.query('year == @map_year')[['county_name', 'Median_income']],
            on='county_name',
            how='left'
        )
        .merge(
            county_fire_summary.query('year == @map_year')[['county_name', 'total_acres_burned', 'number_of_fires']],
            on='county_name',
            how='left'
        )
    )

    # counties shaded by income: darker = higher
    income_fire_map = counties_year.explore(
        column='Median_income',
        cmap='Blues',
        tiles='OpenStreetMap',
        style_kwds={'fillOpacity': 0.6, 'weight': 0.5, 'color': '#000000'},
        tooltip=['county_name', 'Median_income', 'total_acres_burned', 'number_of_fires'],
        legend=True,
        legend_kwds={'caption': f'Median Household Income ({map_year})'},
        name='County Median Income'
    )

    # that year's fire perimeters on top
    wildfires_gdf.query('YEAR_ == @map_year').explore(
        m=income_fire_map,
        color='#e21d1d',
        style_kwds={'fillOpacity': 0.8, 'weight': 0.5},
        tooltip=['FIRE_NAME', 'GIS_ACRES'],
        name=f'{map_year} Fires'
    )

    folium.LayerControl().add_to(income_fire_map)
    return income_fire_map


app_ui = ui.page_fluid(
    ui.panel_title("Wildfire Data Dashboard"),
    ui.card(
        ui.card_header("Acres Burned vs. Fair Plan Enrollment Change"),
        ui.output_plot("wildfire_chart"),
    ),
    ui.card(
        ui.card_header("Median Income & Wildfire Perimeters"),
        ui.input_select("map_year", "Select year:",
                        choices=["2022", "2023", "2024"], selected="2022"),
        ui.output_ui("income_fire_map"),
        full_screen=True,
    ),
)


def server(input, output, session):
    @render.plot
    def wildfire_chart():
        g = sns.lmplot(
        data=fire_plot_data_all,
        x='acres_burned_total',
        y='policy_pct_change',
        hue='starting_year',
        palette=colors,
        aspect=1.5
         )
        g.set(
            title='Acres Burned vs. Fair Plan Enrollment Change',
            xlabel='Acres Burned (Log Scale)',
            ylabel='% Change in Fair Plan Enrollment',
            xscale='log'
    )

        sns.move_legend(
            g,
            title='Starting Year',
            loc = 'upper left',
            frameon=True,
            bbox_to_anchor = (0.9,1),
            facecolor="#FFFEFE"
    )

        return g.figure
    
    @render.ui
    def income_fire_map():
        m = build_map(int(input.map_year()))
        return ui.HTML(m._repr_html_())



app = App(app_ui, server)
