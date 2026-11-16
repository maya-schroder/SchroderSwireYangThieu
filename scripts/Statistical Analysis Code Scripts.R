library(tidyverse)
library(here)

df <- read_csv(
  here("data/processed/County_Income_CFP_Fire_2022_2024.csv")
) %>%
  mutate(
    policy_increase = policies_2024 - policies_2022,
    income_group = factor(
      income_group,
      levels = c("Lower income",
                 "Middle income",
                 "Higher income")
    )
  )

# Growth rate check
df %>%
  mutate(
    recalculated_growth =
      (policies_2024 / policies_2022 - 1) * 100
  ) %>%
  summarise(
    max_difference =
      max(abs(recalculated_growth - policy_growth_pct))
  )



# 1. Areas affected by wildfire & FAIR Policy Growth
ggplot(df, aes(x = acres_burned_total, y = policy_growth_pct)) +
  geom_point(alpha = 0.7, size = 2.5) +
  geom_smooth(method = "lm", se = TRUE, color = "steelblue") +
  scale_x_continuous(
    trans = "log1p",
    labels = scales::comma
  ) +
  labs(
    title = "Wildfire Acreage and FAIR Plan Policy Growth",
    subtitle = "California Counties, 2022–2024",
    x = "Total Acres Burned (log1p scale)",
    y = "FAIR Plan Policy Growth (%)"
  ) +
  theme_minimal()


## Correlation Test
## area burned & policy growth
cor.test(
  df$acres_burned_total,
  df$policy_growth_pct,
  method = "pearson"
)
cor.test(
  df$acres_burned_total,
  df$policy_growth_pct,
  method = "spearman",
  exact = FALSE
)

## Income Group & Policy Growth
cor.test(
  df$Median_income,
  df$policy_growth_pct,
  method = "pearson"
)
cor.test(
  df$Median_income,
  df$policy_growth_pct,
  method = "spearman",
  exact = FALSE
)

## 2. Income Group & FAIR Plan Policy Increase
ggplot(df, aes(x = income_group, y = policy_growth_pct, fill = income_group)) +
  geom_boxplot(alpha = 0.5) +
  geom_jitter(
    width = 0.12,
    alpha = 0.6
  ) +
  labs(
    title = "FAIR Plan Policy Growth by Income Group",
    x = "County Income Group",
    y = "Policy Growth, 2022–2024 (%)"
  ) +
  theme_minimal() +
  theme(legend.position = "none")


income_summary <- df %>%
  group_by(income_group) %>%
  summarise(counties = n(), mean_growth = mean(policy_growth_pct),
            median_growth = median(policy_growth_pct),
            sd_growth = sd(policy_growth_pct), .groups = "drop")
print(income_summary)

kruskal.test(
  policy_growth_pct ~ income_group,
  data = df
)

# Counties with the most increase in Policy Numbers
top10 <- df %>%
  arrange(desc(policy_increase)) %>%
  slice_head(n = 10)

ggplot(top10, aes(
  x = reorder(county, policy_increase),
  y = policy_increase
)) +
  geom_col(fill = "steelblue") +
  coord_flip() +
  scale_y_continuous(
    labels = scales::comma
  ) +
  labs(
    title = "Counties with the Largest FAIR Plan Policy Increases",
    subtitle = "2022–2024",
    x = "County",
    y = "Net Increase in Policies"
  ) +
  theme_minimal()


dir.create(
  here("data/processed"),
  recursive = TRUE,
  showWarnings = FALSE
)

write_csv(
  income_summary,
  here("data/processed/Income_Group_Growth_Summary.csv")
)

write_csv(
  top10,
  here("data/processed/Top10_Policy_Increase_2022_2024.csv")
)




## 3. Annual Growth Rate Analysis
# Calculation of growth rate
Annual_growth <- df %>%
  mutate(growth_2023 = (policies_2023 / policies_2022 - 1) * 100, 
         growth_2024 = (policies_2024 / policies_2023 - 1) * 100) %>%
  select(county, Median_income, growth_2023, growth_2024) %>%
  pivot_longer(
    cols = starts_with("growth_"),
    names_to = "year",
    values_to = "annual_growth"
  ) %>%
  mutate(
    year = as.integer(str_remove(year, "growth_"))
  )

# Correlation Analysis
Annual_growth %>%
  group_by(year) %>%
  summarise(pearson_r = cor(Median_income, annual_growth, method = "pearson"),
            spearman_rho = cor(Median_income, annual_growth, method = "spearman"),
    .groups = "drop")

# Linear Regression for 2023 & 2024
model_2023 <- lm(annual_growth ~ Median_income,
  data = filter(Annual_growth, year == 2023)
)
summary(model_2023)

model_2024 <- lm(annual_growth ~ Median_income,
                 data = filter(Annual_growth, year == 2024))
summary(model_2024)


# The County with the Highest Growth Rate (> 400%) in 2024
Annual_growth %>%
  filter(year == 2024) %>%
  arrange(desc(annual_growth)) %>%
  slice_head(n = 5)

# Cook's distance
diagnostics_2024 <- filter(
  Annual_growth, year == 2024
) %>%
  mutate(
    cooks_d = cooks.distance(model_2024)
  )

diagnostics_2024 %>%
  filter(cooks_d > 4 / nrow(diagnostics_2024)) %>%
  arrange(desc(cooks_d))

ggplot(Annual_growth, aes(x = Median_income, y = annual_growth)) +
  geom_point(alpha = 0.7) +
  geom_smooth(method = "lm", se = TRUE) +
  facet_wrap(~year) +
  scale_x_continuous(labels = scales::dollar) +
  labs(title = "Income and Annual FAIR Plan Policy Growth",
       subtitle = "California Counties, 2023–2024",
    x = "2022 Median Household Income (USD)",
    y = "Annual Policy Growth (%)") +
  theme_minimal()


model_2024_without_CC <- lm(
  annual_growth ~ Median_income,
  data = Annual_growth %>%
    filter(year == 2024,
           county != "Contra Costa"))

summary(model_2024_without_CC)



## 4. Exposure peer policy & Median Income
Exposure_analysis <- Df %>%
  filter(
    year %in% 2022:2024,
    policies > 0
  ) %>%
  mutate(
    exposure_per_policy = exposure / policies
  )

### Correlation coefficient per year
Exposure_analysis %>%
  group_by(year) %>%
  summarise(
    pearson_r = cor(
      Median_income, exposure_per_policy
    ),
    spearman_rho = cor(
      Median_income, exposure_per_policy,
      method = "spearman"
    ),
    .groups = "drop"
  )

# Linear Regression per Year
exposure_models <- lapply(
  split(Exposure_analysis, Exposure_analysis$year),
  function(d) {
    lm(exposure_per_policy ~ Median_income, data = d)
  }
)

lapply(exposure_models, summary)



## Interaction term analysis
model_interaction <- lm(
  exposure_per_policy ~ Median_income * factor(year),
  data = Exposure_analysis
)

anova(model_interaction)
summary(model_interaction)




Df <- read_csv(here("data/processed/County_Income_CFP_2022_2024.csv"))
df %>%
  left_join(
    Df %>%
      filter(year == 2022) %>%
      select(county, income_2022 = Median_income),
    by = "county"
  ) %>%
  summarise(
    mismatches = sum(Median_income != income_2022, na.rm = TRUE),
    missing_matches = sum(is.na(income_2022))
  )


# 2024
model_exp_2024 <- exposure_models[["2024"]]

exp_diagnostics <- Exposure_analysis %>%
  filter(year == 2024) %>%
  mutate(
    cooks_d = cooks.distance(model_exp_2024)
  )

exp_diagnostics %>%
  filter(cooks_d > 4 / n()) %>%
  arrange(desc(cooks_d))

exp_diagnostics %>%
  filter(cooks_d > 4 / n()) %>%
  arrange(desc(cooks_d)) %>%
  select(county, Median_income,
         exposure_per_policy, cooks_d) %>%
  print(width = Inf)

# Four high impact counties excluded
model_exp_2024_sensitivity <- lm(
  exposure_per_policy ~ Median_income,
  data = exp_diagnostics %>%
    filter(cooks_d <= 4 / n())
)

summary(model_exp_2024_sensitivity)

library(purrr)
# Cook's distance for Regression Model every year
all_exp_diagnostics <- map_dfr(
  names(exposure_models),
  function(yr) {
    
    d <- Exposure_analysis %>%
      filter(year == as.integer(yr))
    
    d %>%
      mutate(
        cooks_d = cooks.distance(exposure_models[[yr]]),
        influential = cooks_d > 4 / n()
      )
  }
)

# Counties surpassing the impact threshold
all_exp_diagnostics %>%
  filter(influential) %>%
  select(year, county, cooks_d) %>%
  arrange(year, desc(cooks_d))




# Regression Redux after excluding the highest observations
sensitivity_models <- all_exp_diagnostics %>%
  group_split(year) %>%
  set_names(c("2022", "2023", "2024")) %>%
  map(function(d) {
    lm(
      exposure_per_policy ~ Median_income,
      data = filter(d, !influential)
    )
  })

# Extracting comparison results
Sensitivity_Analysis <- dplyr::bind_rows(
  
  # 1. Policy Growth 2024
  extract_model(
    model_2024,
    "Policy Growth 2024 - Full"
  ),
  
  extract_model(
    model_2024_without_CC,
    "Policy Growth 2024 - Without Contra Costa"
  ),
  
  # 2. Exposure per Policy 2022
  extract_model(
    exposure_models[["2022"]],
    "Exposure 2022 - Full"
  ),
  
  extract_model(
    sensitivity_models[["2022"]],
    "Exposure 2022 - Without 4 Influential Counties"
  ),
  
  # 3. Exposure per Policy 2023
  extract_model(
    exposure_models[["2023"]],
    "Exposure 2023 - Full"
  ),
  
  extract_model(
    sensitivity_models[["2023"]],
    "Exposure 2023 - Without 4 Influential Counties"
  ),
  
  # 4. Exposure per Policy 2024
  extract_model(
    exposure_models[["2024"]],
    "Exposure 2024 - Full"
  ),
  
  extract_model(
    sensitivity_models[["2024"]],
    "Exposure 2024 - Without 4 Influential Counties"
  )
)

print(Sensitivity_Analysis)
nrow(Sensitivity_Analysis)


# Results Export
write.csv(
  Sensitivity_Analysis,
  "Sensitivity_Analysis.csv",
  row.names = FALSE
)