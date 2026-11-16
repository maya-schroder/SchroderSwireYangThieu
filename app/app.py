# Step 1: import packages and read in data
import pandas as pd
import numpy as np
import geopandas as gpd
import folium 
import seaborn as sns
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from shiny import App, render, req, ui
import statsmodels.formula.api as smf





# Set sns theme
sns.set_theme(
    style='white',
    font='sans-serif',
    rc={
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.edgecolor': '#B9BEC2',
        'axes.labelcolor': '#3A3F45',
        'axes.labelsize': 11,
        'axes.grid': True,
        'grid.color': '#ECEEEE',
        'grid.linewidth': 0.8,
        'xtick.color': '#5E656C',
        'ytick.color': '#5E656C',
        'text.color': '#22262B',
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
    },
)

try:
    root_fldr = Path(__file__).resolve().parent.parent
except NameError:
    root_fldr = Path.cwd().resolve()
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

fire_fair_plan_data = (
    all_data[['county', 'year', 'acres_burned_total', 'policies', 'exposure']]
    .sort_values(['county', 'year'])
    .reset_index(drop=True)
)

fire_fair_plan_data['fire_risk'] = (
    fire_fair_plan_data.groupby('year')['acres_burned_total']
    .transform(lambda s: pd.qcut(
        s, q=4,
        labels=['1. Lowest Risk', '2. Low-Moderate Risk',
                '3. High-Moderate Risk', '4. High Risk'],
        duplicates='drop'
    ))
)

group_policies = (
    fire_fair_plan_data
    .pivot_table(index='fire_risk', columns='year', values='policies',
                 aggfunc='sum', observed=True)
    .reset_index()
)

group_index = group_policies.copy()
for yr in [2022, 2023, 2024]:
    group_index[yr] = group_policies[yr] / group_policies[2022] * 100

group_trend = group_index.melt(
    id_vars='fire_risk', var_name='year', value_name='policies_index'
)
group_trend['year'] = group_trend['year'].astype(int)

risk_colors = {
    '1. Lowest Risk': '#F8BBBB',
    '2. Low-Moderate Risk': '#DF7A8E',
    '3. High-Moderate Risk': '#D2042D',
    '4. High Risk': '#800020',
}

# ---- Income vs. FAIR Plan ----
income_fair_plan_data = (
    all_data[['county', 'year', 'Median_income', 'policies', 'exposure']]
    .sort_values(['county', 'year'])
    .reset_index(drop=True)
)

income_fair_plan_data['policies_pct_change'] = (
    income_fair_plan_data.groupby('county')['policies'].pct_change() * 100
)

income_fair_plan_data = income_fair_plan_data.assign(
    dollars_per_policy=lambda df: df['exposure'] / df['policies']
)

income_colors_3yr = {2022: '#088F8F', 2023: '#00FF7F', 2024: '#B4C424'}
income_colors_2yr = {2023: '#00FF7F', 2024: '#B4C424'}

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

trends_data = (
    trends_data
    .assign(
        income_10k = lambda df: df['Median_income']/10000,
        log_acres  = lambda df: np.log(df['acres_burned_total']+1),
        small_base = lambda df: df['county'].isin(['Sutter','Glenn','Colusa','Kings']),
    )
)


m_income = smf.ols("policy_growth_pct ~ income_10k", data=trends_data).fit()

def tidy_ols(model, labels=None):
    ci = model.conf_int()
    out = pd.DataFrame({
        "Term": model.params.index,
        "Coefficient": model.params.values.round(3),
        "Std. error": model.bse.values.round(3),
        "p-value": [("<0.001" if p < 0.001 else f"{p:.3f}") for p in model.pvalues],
        "95% CI low": ci[0].values.round(3),
        "95% CI high": ci[1].values.round(3),
    })
    if labels:
        out["Term"] = out["Term"].replace(labels)
    return out

def fit_summary(model):
    return f"n = {int(model.nobs)} counties   |   R² = {model.rsquared:.3f}"


m_fire = smf.ols("policy_growth_pct ~ log_acres", data=trends_data).fit()

income_labels = {"Intercept": "Intercept", "income_10k": "Median income (per $10k)"}

fire_labels = {"Intercept": "Intercept", "log_acres": "Wildfire Acreage (log scale)"}


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


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
FONT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Public+Sans:wght@400;500;600&"
    "family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&display=swap"
)

CSS = """
:root {
    --ink: #22262B;
    --muted: #5E656C;
    --paper: #F1F2EF;
    --card: #FFFFFF;
    --rule: #DCDFDC;
    --ember: #B3341F;
    --char: #22262B;
}

html, body {
    background: var(--paper);
    color: var(--ink);
    font-family: 'Public Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
    line-height: 1.6;
}

.container-fluid { padding: 0; }

/* ---- header ---- */
.dash-header {
    background: var(--char);
    color: #F1F2EF;
    border-bottom: 6px solid var(--ember);
    padding: 3.25rem 1.5rem 2.75rem;
}
.dash-header-inner { max-width: 1040px; margin: 0 auto; }
.dash-header h1 {
    font-family: 'Source Serif 4', Georgia, serif;
    font-weight: 600;
    font-size: clamp(1.9rem, 4vw, 2.8rem);
    line-height: 1.15;
    letter-spacing: -0.01em;
    margin: 0 0 1rem;
}
.dash-header p {
    max-width: 68ch;
    margin: 0;
    font-size: 1.05rem;
    color: #D5D9D6;
}

/* ---- main column ---- */
.dash-main {
    max-width: 1040px;
    margin: 0 auto;
    padding: 2rem 1.5rem 1rem;
}

/* ---- figure cards ---- */
.figure-card.card {
    background: var(--card);
    border: 1px solid var(--rule);
    border-radius: 4px;
    box-shadow: none;
    margin-bottom: 2rem;
}
.figure-card .card-header {
    background: transparent;
    border-bottom: none;
    padding: 1.5rem 1.75rem 0;
    font-family: 'Source Serif 4', Georgia, serif;
    font-weight: 600;
    font-size: 1.4rem;
    line-height: 1.3;
}
.figure-card .card-body { padding: 0.75rem 1.75rem 1.5rem; }

.context {
    max-width: 70ch;
    margin: 0 0 1.25rem;
    padding-left: 1rem;
    border-left: 3px solid var(--ember);
}
.context p { margin: 0 0 0.6rem; }
.context p:last-child { margin-bottom: 0; }
.context .how-to { color: var(--muted); font-size: 0.95rem; }

/* plots sit centred in the card */
.figure-card .shiny-plot-output { margin: 0 auto; }

/* ---- map controls ---- */
.map-controls { margin-bottom: 0.75rem; }
.map-controls .form-group { margin-bottom: 0; max-width: 220px; }
.map-controls label { font-weight: 500; }

/* ---- footer ---- */
.dash-footer {
    max-width: 1040px;
    margin: 0 auto;
    padding: 0.5rem 1.5rem 3rem;
    color: var(--muted);
    font-size: 0.9rem;
}
.dash-footer p { max-width: 80ch; margin: 0; }

@media (max-width: 640px) {
    .dash-header { padding: 2.25rem 1.1rem 2rem; }
    .dash-main { padding: 1.25rem 0.75rem 0.5rem; }
    .figure-card .card-header { padding: 1.1rem 1.1rem 0; font-size: 1.2rem; }
    .figure-card .card-body { padding: 0.6rem 1.1rem 1.1rem; }
}
"""


def figure_card(title, context, how_to_read, *outputs, **kwargs):
    """A card with a title, background text, and the figure underneath."""
    return ui.card(
        ui.card_header(title),
        ui.div(
            ui.p(context),
            ui.p(ui.strong("Figure Description: "), how_to_read, class_="how-to"),
            class_="context",
        ),
        *outputs,
        class_="figure-card",
        **kwargs,
    )


app_ui = ui.page_fluid(
    ui.head_content(
        ui.tags.link(rel="preconnect", href="https://fonts.googleapis.com"),
        ui.tags.link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        ui.tags.link(rel="stylesheet", href=FONT_URL),
        ui.tags.style(CSS),
    ),

    # Header
    ui.div(
        ui.div(
            ui.h1("Wildfire, income, and California FAIR Plan enrollment"),
            ui.p(
                "The California FAIR Plan is the state's fire insurer of last resort, "
                "covering property owners who can't get a policy on the private market. "
                "This dashboard compares how FAIR Plan enrollment changed across "
                "California counties from 2022 to 2024 compared to wildfire acreage "
                "and median household income."
            ),
            class_="dash-header-inner",
        ),
        class_="dash-header",
    ),

    # Figures
    ui.div(
        figure_card(
            "Acres burned vs. FAIR Plan enrollment change",
            "As wildfire risk increases, we expect to see faster FAIR Plan growth. "
            "Each dot represents a county. It is plotted by the acres burned in a "
            "starting year against the percent change in FAIR Plan policies the following year.",
            "The x-axis is on a log scale, and each line is the "
            "fitted trend for one starting year. Only counties with at least one "
            "fire and growing enrollment are included.",
            ui.output_plot("wildfire_chart"),
        ),
        figure_card(
            "FAIR Plan policies by fire risk level",
            "Each year, counties are sorted into four equal-sized groups by the "
            "total acres burned in that year. Policies are added up within each group "
            "and indexed to 2022, so every group starts at 100.",
            "A line above 100 means enrollment has grown since 2022. Compare whether "
            "the higher-risk groups rise faster than the lower-risk ones. Groups are "
            "re-sorted every year, so a county can move between them.",
            ui.output_plot("risk_trend_chart"),
        ),
        figure_card(
            "Dollars per policy vs. median income",
            "Dollars per policy is county-level FAIR Plan exposure divided by the "
            "number of policies in a county. It is a rough measure of how much "
            "property value each policy covers. This chart asks whether wealthier "
            "counties carry larger policies.",
            "Each dot is a county in a given year.",
            ui.output_plot("income_dollars_chart"),
        ),
        figure_card(
            "Median income vs. percent change in enrollment",
            "This chart looks at whether the rate of FAIR Plan growth differs "
            "between lower- and higher-income counties. It shows year-over-year change, "
            "starting in 2023.",
            "The year in this case reflects the end year, with 2023 representing percent change in Fair Plan enrollment from 2022 to 2023.",
            ui.output_plot("income_enrollment_chart"),
        ),
        figure_card(
            "Median income and wildfire perimeters",
            "The map compares median income and wildfires. Counties are shaded by "
            "median household income, and the red shapes are that year's CAL FIRE "
            "fire perimeters.",
            "Darker blue means higher income. Hover over a county for its income, "
            "acres burned, and number of fires. Use the layer control in the map's "
            "corner to hide the fires or the income shading.",
            ui.div(
                ui.input_select(
                    "map_year", "Select year:",
                    choices=["2022", "2023", "2024"], selected="2022",
                ),
                class_="map-controls",
            ),
            ui.output_ui("income_fire_map"),
            full_screen=True,
        ),
        figure_card(
            "Income and FAIR Plan enrollment growth: Regression Analysis",
            "This model estimates how FAIR Plan enrollment growth changes with county "
            "median income, using ordinary least squares.",
            "The coefficient on income is the expected change in enrollment growth "
            "(percentage points) for each additional $10,000 of median income.",
            ui.output_data_frame("income_reg_table"),
            ui.output_text("income_reg_fit"),
        ),
        figure_card(
            "Wildfire Risk and FAIR Plan enrollment growth: Regression Analysis",
            "This model estimates how FAIR Plan enrollment growth changes with wildfire "
            "acreage, using ordinary least squares.",
            "The coefficient on acres is the expected change in enrollment growth "
            "for each 1 percent increase in wildfire acreage.",
            ui.output_data_frame("fire_reg_table"),
            ui.output_text("fire_reg_fit"),
                )
    ),

    # Footer
    ui.div(
        ui.p(
            "Sources: CAL FIRE historic fire perimeters (2022 to 2024), "
            "California FAIR Plan policy and exposure counts by county, and "
            "county median household income."
        ),
        class_="dash-footer",
    ),

    title="Wildfire Data Dashboard",
)

def server(input, output, session):
    @render.plot
    def wildfire_chart():
        g = sns.lmplot(
        data=fire_plot_data_all,
        x='acres_burned_total',
        y='policy_pct_change',
        hue='starting_year',
        palette=colors
         )
        g.set(
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

    @render.plot
    def risk_trend_chart():
        g = sns.relplot(
            data=group_trend,
            x='year', y='policies_index', hue='fire_risk',
            palette=risk_colors, kind='line', marker='o',
        ).set(
            xlabel='Year',
            ylabel='Policies (2022 = 100)',
            xticks=[2022, 2023, 2024],
        )
        sns.move_legend(
            g, title='Fire Risk', loc='upper left', frameon=True,
            bbox_to_anchor=(0.9, 1), facecolor="#FFFEFE"
        )
        return g.figure

    @render.plot
    def income_dollars_chart():
        g = sns.lmplot(
            data=income_fair_plan_data,
            x='dollars_per_policy', y='Median_income', hue='year',
            palette=income_colors_3yr,
        ).set(
            xlabel='$ per Policy',
            ylabel='Median Income',
        )
        g.ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
        sns.move_legend(
            g, title='Year', loc='upper left', frameon=True,
            bbox_to_anchor=(0.9, 1), facecolor="#FFFEFE"
        )
        return g.figure

    @render.plot
    def income_enrollment_chart():
        df = income_fair_plan_data.loc[income_fair_plan_data['year'] > 2022]

        fig, ax = plt.subplots()
        for yr, color in income_colors_2yr.items():
            sns.regplot(
            data=df[df['year'] == yr],
            x='Median_income', y='policies_pct_change',
            color=color, label=str(yr), ax=ax,
        )

        ax.set(
            xlabel='Median Income',
            ylabel='YoY % Change in Fair Plan Enrollment',
    )
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
        ax.legend(title='Year', loc='upper right', frameon=True, facecolor="#FFFEFE")
        fig.tight_layout()
        return fig
    
    @render.ui
    def income_fire_map():
        m = build_map(int(input.map_year()))
        return ui.HTML(m._repr_html_())

    @render.data_frame
    def income_reg_table():
        return render.DataGrid(tidy_ols(m_income, income_labels), width="100%")

    @render.text
    def income_reg_fit():
        return fit_summary(m_income)

    @render.data_frame
    def fire_reg_table():
        return render.DataGrid(tidy_ols(m_fire, fire_labels), width="100%")
    
    @render.text
    def fire_reg_fit():
        return fit_summary(m_fire)

app = App(app_ui, server)