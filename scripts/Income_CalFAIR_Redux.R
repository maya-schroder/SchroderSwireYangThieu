library(tidyverse)
library(here)

Income_raw <- read.csv(here("data/raw/ca_county_income_2021_2024_raw.csv"))
CFP_risk <- read.csv(here("data/raw/cfp_risk_exposure_cleaned.csv")) 
CFP_general <- read.csv(here("data/raw/cfp_general_plans_cleaned.csv")) 

names(Income_raw)
names(CFP_risk)
names(CFP_general)
nrow(Income_raw)
nrow(CFP_risk)
nrow(CFP_general)


# Census Income Tidying and Basic Inspections of Case Number & NA values
Income_clean <- Income_raw %>%
  transmute(
    GEOID = str_pad(as.character(GEOID), 5, pad = "0"),
    county = str_remove(NAME, " County, California"),
    year = as.integer(year),
    Median_income = as.numeric(B19013_001E),
    Income_MOE = as.numeric(B19013_001_moe)
  )

Income_clean %>%
  count(year)
Income_clean %>%
  summarise(
    missing_income = sum(is.na(Median_income)),
    missing_moe = sum(is.na(Income_MOE))
  )

Income_clean %>%
  count(GEOID, year) %>%
  filter(n > 1)



## FAIR Plan Data Integration

# Number of Policies
CFP_policies_long <- CFP_general %>%
  select(county, starts_with("policies_")) %>%
  pivot_longer(
    cols = starts_with("policies_"),
    names_to = "year",
    names_prefix = "policies_",
    values_to = "policies"
  ) %>%
  mutate(year = as.integer(year))

# Exposure Amount
CFP_exposure_long <- CFP_risk %>%
  select(county, starts_with("exposure_")) %>%
  pivot_longer(
    cols = starts_with("exposure_"),
    names_to = "year",
    names_prefix = "exposure_",
    values_to = "exposure"
  ) %>%
  mutate(year = as.integer(year))

# 58 counties per year?
CFP_policies_long %>%
  count(year)

CFP_exposure_long %>%
  count(year)

# NAs existing?
CFP_policies_long %>%
  summarise(missing_policies = sum(is.na(policies)))

CFP_exposure_long %>%
  summarise(missing_exposure = sum(is.na(exposure)))

# Whether county names are consistent with that of Census
setdiff(unique(Income_clean$county),
        unique(CFP_policies_long$county))

setdiff(unique(CFP_policies_long$county),
        unique(Income_clean$county))




# Combining Three Data Tables
County_Income_CFP <- Income_clean %>%
  inner_join(
    CFP_policies_long,
    by = c("county", "year"),
    relationship = "one-to-one"
  ) %>%
  inner_join(
    CFP_exposure_long,
    by = c("county", "year"),
    relationship = "one-to-one"
  ) %>%
  arrange(year, county)


# Total rows
nrow(County_Income_CFP)

# Counties per year
County_Income_CFP %>%
  count(year)

# Checking NAs
County_Income_CFP %>%
  summarise(
    missing_income = sum(is.na(Median_income)),
    missing_moe = sum(is.na(Income_MOE)),
    missing_policies = sum(is.na(policies)),
    missing_exposure = sum(is.na(exposure))
  )

# Duplicates
County_Income_CFP %>%
  count(GEOID, year) %>%
  filter(n > 1)

# Data Structure
glimpse(County_Income_CFP)

# Data Export
dir.create(
  here("data/processed"),
  recursive = TRUE,
  showWarnings = FALSE
)

write_csv(
  County_Income_CFP,
  here("data/processed/County_Income_CFP_2022_2024.csv")
)
