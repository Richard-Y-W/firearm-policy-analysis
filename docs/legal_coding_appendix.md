# Legal Coding Appendix

## Treatment Rule

The primary treatment is a statewide law allowing eligible adults to carry a concealed handgun in public without first obtaining a carry permit. The panel codes the first calendar year in which the statewide permitless concealed-carry rule is in effect. Partial-year changes are coded to the effective calendar year because the analytic panel is annual.

Permitless open carry is not treated as permitless concealed carry. States that allow open carry without a permit but retain a concealed-carry permit requirement remain untreated in the primary coding.

## Audit Statuses

- `source_verified`: the state adopted statewide permitless concealed carry during the 1999-2024 panel and the audit row includes legal timing and source URLs.
- `not_adopted_verified`: the state had no statewide permitless concealed-carry adoption through 2024 and the audit row includes source URLs for the concealed-carry requirement and, where relevant, open-carry scope.
- `partial`: the state has a coding complication that should not be treated as fully clean without a narrower statutory review.
- `baseline_permitless_verified`: the state was already permitless before the panel began, so it is not a within-panel adoption event.
- `ambiguous_reviewed`: the state has reviewed sources but the clean annual treatment date is ambiguous enough to exclude from the primary map and handle by sensitivity analysis.

## Edge Cases

Arkansas remains excluded from the primary clean-adoption map. The audit records the 2023 statutory clarification and the analysis separately reports Arkansas treatment-year sensitivity runs using 2021 and 2023.

Mississippi remains `partial` because the 2015 and 2016 changes differ in how broadly permitless concealed carry applied. The current panel year is retained for consistency, but the row should not be used as a clean binary statutory field without a deeper Mississippi-specific review.

Vermont is recorded as `baseline_permitless_verified` because it did not adopt permitless carry during the 1999-2024 panel; it entered the panel without a carry-permit requirement.

## Source Strategy

The audit table stores row-level source URLs in `data/policy/permitless_carry_legal_audit.csv`. Non-adopter verification uses a combination of state carry-permit pages, statutory citations, Giffords concealed-carry/open-carry summaries, and open-carry reference summaries where the key distinction is open versus concealed carry.

The current source pass is enough to distinguish clean treated states, verified untreated states, baseline permitless states, partial cases, and ambiguous cases. It is not yet a full manuscript-grade coding of every permit-screening mechanism. Fields such as training removal, background-check permit-screening changes, and violent-misdemeanor screening should still receive statute-level review before they are modeled as separate mechanisms.
