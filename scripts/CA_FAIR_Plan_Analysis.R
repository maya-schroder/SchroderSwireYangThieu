# FAIR Plan Table (combined)
CFP_trends <- CFP_policies_long %>%
  inner_join(
    CFP_exposure_long,
    by = c("county", "year"),
    relationship = "one-to-one"
  ) %>%
  mutate(
    exposure_per_policy = exposure / policies
  )


# Total Number of Policies & Exposure
CFP_statewide <- CFP_trends %>%
  group_by(year) %>%
  summarise(
    total_policies = sum(policies),
    total_exposure = sum(exposure),
    .groups = "drop"
  ) %>%
  arrange(year) %>%
  mutate(
    policy_growth = total_policies / lag(total_policies) - 1,
    exposure_growth = total_exposure / lag(total_exposure) - 1,
    exposure_per_policy = total_exposure / total_policies
  )

print(CFP_statewide)

# Policies Changing Trend
ggplot(CFP_statewide,
       aes(x = year, y = total_policies)) +
  geom_line(linewidth = 1) +
  geom_point(size = 3) +
  scale_x_continuous(breaks = 2022:2026) +
  scale_y_continuous(labels = scales::comma) +
  labs(
    title = "California FAIR Plan Policies in Force",
    subtitle = "Fiscal Years 2022–2026",
    x = "Fiscal Year",
    y = "Number of Policies"
  ) +
  theme_minimal()

ggplot(CFP_statewide,
       aes(x = year, y = total_exposure / 1e9)) +
  geom_line(linewidth = 1) +
  geom_point(size = 3) +
  scale_x_continuous(breaks = 2022:2026) +
  labs(
    title = "California FAIR Plan Total Exposure",
    subtitle = "Fiscal Years 2022–2026",
    x = "Fiscal Year",
    y = "Total Exposure (Billion USD)"
  ) +
  theme_minimal()


# 2022-2026 Cumulative Growth Rate per County
CFP_county_growth <- CFP_trends %>%
  group_by(county) %>%
  summarise(
    policies_2022 = policies[year == 2022],
    policies_2026 = policies[year == 2026],
    exposure_2022 = exposure[year == 2022],
    exposure_2026 = exposure[year == 2026],
    .groups = "drop"
  ) %>%
  mutate(
    policy_growth_pct = if_else(
      policies_2022 > 0,
      (policies_2026 / policies_2022 - 1) * 100,
      NA_real_
    ),
    exposure_growth_pct = if_else(
      exposure_2022 > 0,
      (exposure_2026 / exposure_2022 - 1) * 100,
      NA_real_
    ),
    policy_increase = policies_2026 - policies_2022
  )

CFP_county_growth %>%
  arrange(desc(policy_growth_pct)) %>%
  slice_head(n = 10)



# Top 10 Counties in CA witnessed Largest FAIR Plan Increase
CFP_county_growth %>%
  arrange(desc(policy_increase)) %>%
  slice_head(n = 10) %>%
  ggplot(
    aes(
      x = reorder(county, policy_increase),
      y = policy_increase
    )
  ) +
  geom_col(fill = "steelblue") +
  coord_flip() +
  scale_y_continuous(labels = scales::comma) +
  labs(
    title = "Top 10 California Counties by Increase in FAIR Plan Policies",
    subtitle = "Fiscal Years 2022–2026",
    x = "County",
    y = "Net Increase in Policies"
  ) +
  theme_minimal()

# Top 10 Counties' Contribution to Entire State
CFP_top10_contribution <- CFP_county_growth %>%
  arrange(desc(policy_increase)) %>%
  slice_head(n = 10) %>%
  summarise(
    top10_increase = sum(policy_increase)
  ) %>%
  mutate(
    statewide_increase =
      sum(CFP_county_growth$policy_increase),
    contribution_pct =
      top10_increase / statewide_increase * 100
  )
print(CFP_top10_contribution)


write_csv(
  CFP_statewide,
  here("data/processed/CFP_statewide_trends_2022_2026.csv")
)

write_csv(
  CFP_county_growth,
  here("data/processed/CFP_county_growth_2022_2026.csv")
)

write_csv(
  CFP_trends,
  here("data/processed/CFP_county_trends_2022_2026.csv")
)
