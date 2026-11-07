# Step 1: import packages and read in data
import pandas as pd
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


app_ui = ui.page_fluid(
    ui.panel_title("Wildfire Data Dashboard"),
    ui.card(
        ui.card_header("Acres Burned vs. Fair Plan Enrollment Change"),
        ui.output_plot("wildfire_chart"),
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


app = App(app_ui, server)
