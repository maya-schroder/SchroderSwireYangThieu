# SchroderSwireYangThieu
ENV 712 project repository for team members Maya Schroder, Matt Swire, Nigel Yang, and Lam Thieu.

We are studying wildfire risk and socio-economic status in California to understand how Fair Plan adoption is associated with these factors.

# Folder Structure
## Data
Raw data can be found in the `raw` folder. This is data pulled directly from the source (census.data.gov, California Fair Plan data in PDFs, etc.). Once our data is processed, we place it in the `processed` folder. Processed data includes both the files that join multiple data sources, as well as cleaned versions of raw data (e.g., Calidornia Fair Plan CSVs).


## Docs
Currently, docs only includes our Team Charter, which lays out our goals and workplan to accomplish this project. The Team Charter is subject to change.


## Scripts
Current scripts included in our repo are as follows:
* `ACS_Import_Clean.ipynb` checks ACS CSV files and pulls in ACS shapefile data
* `cal_fire_shapefiles.ipynb` analyze California wildfire shapefiles. We plan to join this with ACS data
* `cfp_commercial_risk_data_scrape.ipynb` scrapes the California Fair Plan commercial policies PDF data to create a CSV
* `cfp_general_plan_data_scrape.ipynb` scrapes the California Fair Plan general plan PDF data to create a CSV
* `cfp_residential_risk_data_scrape.ipynb` scrapes the California Fair Plan residential policies PDF data to create a CSV
* `CSV_Data_Quality_Audit.ipynb` checks the data joined in `Income_CalFairPlan_2021_2024.R` to ensure that joins were performed correctly and checks the status of missing data.
* `Income_CalFairPlan_2021_2024.R` joins the California Fair Plan CSV files and the ACS CSVs to compare Fair Plan policies and income by zip code
* `Preliminary_Exploratory_Analysis.ipynb` performs initial analysis of the joined CSV to help inform our ability to conduct further analysis

## Data Dictionary 
To be completed in week 3 upon creation of final processed data that has sticthed toghether US Census Data, California Fair Plan Insurance Data, and wildfire data. Further time is needed before final update. 

README last updated 10/29/2026