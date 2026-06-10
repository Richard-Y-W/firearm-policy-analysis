# Additional CDC WONDER Export Specs

This file records the CDC WONDER exports used for the reviewer-facing negative-control and sex/age checks. The exports can be fetched with:

```bash
python3 -m src.data.fetch_cdc_wonder_exports
```

Manual exports should be saved as tab-separated WONDER files in `data/raw/cdc_wonder/` using the filenames below.

## Negative-Control Mortality Outcomes

Use CDC WONDER Underlying Cause of Death. Match the existing panel split:

- 1999-2020 database: `https://wonder.cdc.gov/ucd-icd10.html`
- 2018-2024 Single Race database: `https://wonder.cdc.gov/ucd-icd10-expanded.html`

Export settings for each outcome:

- Group results by: `State`, `Year`
- Measures: `Deaths`, `Population`, `Crude Rate`
- Location: United States, all states
- Years:
  - old file: 1999-2020
  - new file: 2018-2024, later filtered to 2021-2024 in processing

Required filenames and ICD-10 codes:

| Outcome | Old export | New export | ICD-10 underlying-cause codes |
| --- | --- | --- | --- |
| Cancer mortality | `negative_control_cancer_1999_2020.xls` | `negative_control_cancer_2018_2024_single_race.xls` | `C00-C97` |
| Cardiovascular mortality | `negative_control_cardiovascular_1999_2020.xls` | `negative_control_cardiovascular_2018_2024_single_race.xls` | `I00-I99` |
| Motor-vehicle mortality | `negative_control_motor_vehicle_1999_2020.xls` | `negative_control_motor_vehicle_2018_2024_single_race.xls` | CDC 113-cause group: motor vehicle accidents (`GR113-114`) |

The motor-vehicle definition follows the CDC 113-cause motor-vehicle group rather than all transport codes. It is a negative-control mortality family, not a traffic-safety endpoint.

## Firearm-Suicide Sex/Age Stratification

Use CDC WONDER Underlying Cause of Death with firearm-suicide ICD-10 codes:

- `X72-X74`

Export settings:

- Group results by: `State`, `Year`, `Sex`, `Ten-Year Age Groups`
- Measures: `Deaths`, `Population`, `Crude Rate`
- Location: United States, all states
- Years:
  - old file: 1999-2020
  - new file: 2018-2024, later filtered to 2021-2024 in processing

Required filenames:

- `firearm_suicide_by_sex_age_1999_2020.xls`
- `firearm_suicide_by_sex_age_2018_2024_single_race.xls`

The analysis should collapse ten-year age groups into broad groups after export, then audit suppression before fitting models. The preferred broad groups are `15-24`, `25-44`, `45-64`, and `65+`. Under-15 firearm-suicide rows should be reported descriptively only if suppression permits; they should not drive the main stratified interpretation.
