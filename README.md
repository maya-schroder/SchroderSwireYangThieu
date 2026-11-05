# SchroderSwireYangThieu
ENV 712 project repository for team members Maya Schroder, Matt Swire, Nigel Yang, and Lam Thieu.

We are studying wildfire risk and socio-economic status in California to understand how Fair Plan adoption is associated with these factors.

# Folder Structure
## Data
Raw data can be found in the `raw` folder. This is data pulled directly from the source (census.data.gov, California Fair Plan data in PDFs, etc.). Once our data is processed, we place it in the `processed` folder. Processed data includes both the files that join multiple data sources, as well as cleaned versions of raw data (e.g., Calidornia Fair Plan CSVs).


## Docs
Docs include our Team Charter and Week 2 updates. Additional documentation associated with our project may be uploaded here in the future.


## Scripts
Current scripts included in our repo are as follows:
* `ACS_County_Income.ipynb` pulls in ACS income data for 2021-2024, looking at median income on a county level. We save the API pull as a CSV in our `raw` data folder.
* `CA_FAIR_Plan_Analysis.R` reviews and analyzes California Fair Plan enrollment over time, creating CSVs that organize trends.
* `cal_fire_shapefiles.ipynb` analyzes California wildfire shapefiles. 
* `cfp_general_plan_data_scrape.ipynb` scrapes the California Fair Plan general plan PDF data to create a CSV
* `cfp_risk_exposure.ipynb` scrapes the California Fair Plan exposure and risk PDF data to create a CSV
* `County_Exploratory_Analysis.ipynb` builds a county-level table (Fair Plan policy growth 2022-2024, 2022 median income, and acres burned 2022-2024) and uses it for our exploratory figures and summary table: income vs. policy growth, acres burned vs. policy growth, a summary table by income group, and policy trends by income group. 
* `fire_income_connect.ipynb` join the wildfire and ACS income data to create a preliminary map showing the overlap. We will expand on this in the next couple weeks.
* `Income_CalFAIR_Redux.R` joins the California Fair Plan CSV files and the ACS CSVs to compare Fair Plan policies and income by county
* `Spatial-VectorData.ipynb` is a script created by John Fay to share spatial data basics in Python. We are using this for reference.

Scripts in the `Dashboard` folder compile our data for the dashboard. These include spatial scripts and non-spatial data analysis.

Scripts in the `old` folder are scripts we wrote when processing and joining the data at a zip code level. We moved to county-level after assessing the feasibility of working with zip codes and ZCTAs (Census zip code tract area groupings) and ultimately determined that county-level would be more appropriate given our timeline.


## Data Dictionary 
We do not have a single CSV that stores all of our data, but general key terms associated with our processed data can be found here:
* **county** is our general join key across different data sources
* **year** is the other join key across different data sources (2021-2024 is the primary overlap, but we are looking at Fair Plan data up to 2026 to get a sense of general trends)
* **policies** refer to the number of Fair Plan policies in a county in a year, while **exposure** is the amount of risk California is taking on by insuring these homeowners ($). We use absolute and percent change to evaluate growth by county over time.
* **income** is the median income in a county measured by the ACS each year. We are using the ACS five-year estimates, so 2021 represents median income across 2017-2021. Income is represented in dollars for that year (e.g., 2021 income is represented in 2021 dollars)
* **income_moe** represents the Census margin of error associated with the median income estimate. We do not plan to directly incorporate this in our analysis, but it is helpful to include nonetheless

The county table (`County_Income_CFP_Fire_2022_2024.csv`, from `County_Exploratory_Analysis.ipynb`) has one row per county (58 rows) and adds these columns:
* **policies_2022**, **policies_2023**, **policies_2024** are the number of Fair Plan policies in the county in each year
* **policy_growth_pct** is the percent change in Fair Plan policies from 2022 to 2024, measured against the county's own 2022 policies. Counties that started with very few policies (Colusa, Glenn, Kings, Sutter had fewer than 50 in 2022) can show large percent changes from small increases
* **Median_income** is the county's ACS median household income for 2022 (the 2018-2022 five-year estimate, in 2022 dollars)
* **acres_burned_total** is the total acres burned inside the county by wildfires in 2022-2024, from the CAL FIRE perimeters split by county. Counties with no fire in those years are 0. This measures fires that actually happened, not wildfire risk
* **income_group** splits the counties into three equal-sized groups by 2022 median income (Lower, Middle, Higher income)


README last updated 11/5/2026.