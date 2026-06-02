# Legal Coding Appendix

## Treatment Rule

The primary treatment is a statewide law allowing eligible adults to carry a concealed handgun in public without first obtaining a carry permit. The panel codes the first calendar year in which the statewide permitless concealed-carry rule is in effect. Partial-year changes are coded to the effective calendar year because the analytic panel is annual.

Permitless open carry is not treated as permitless concealed carry. States that allow open carry without a permit but retain a concealed-carry permit requirement remain untreated in the primary coding.

## Verification Standard

The legal audit is designed to support the binary treatment timing used in the state-year panel. A row is treated as verified only when the audit table records the adoption or non-adoption status, the relevant carry scope, legal timing where applicable, source URLs, and coding notes. The current audit standard is therefore sufficient for distinguishing clean within-panel adopters, verified non-adopters, baseline permitless states, ambiguous cases, and partial cases.

The audit is not yet a full statute-level mechanism dataset. The detailed screening fields are retained so they can be audited later, but they should not be interpreted as final measures of training removal, background-check screening changes, violent-misdemeanor screening changes, or other eligibility mechanisms unless a future pass verifies the underlying statutory language state by state.

## Reconciliation Checks

`src/analysis/policy_audit.py` validates that the audit table has one row per state, required columns, required fields for verified rows, and treatment-year consistency against the processed panel. The generated `outputs/tables/policy_audit/policy_audit_summary.csv` flags any mismatch between the audit year and the analytic `permitless_year` field.

Rows marked `partial`, `ambiguous_reviewed`, or `baseline_permitless_verified` are intentionally not clean within-panel treatment events. They remain documented in the audit table so the analysis can explain why they are excluded from or handled differently in primary treatment timing.

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

## Minimum Standard for a Manuscript Mechanism Appendix

Before mechanism-specific models are presented as manuscript evidence, each state row should add statutory text or official bill history for the permit application, training, background-check, and disqualifier provisions before and after permitless-carry adoption. The appendix should then record whether each mechanism changed because of permitless carry itself, changed through a separate contemporaneous bill, was already absent before adoption, or remained in place for optional permits only.

That additional pass would let the project distinguish the broad policy timing question from narrower mechanism questions. Until then, the main analysis should describe permitless carry as a statewide concealed-carry permit requirement change and should avoid attributing the estimates to a specific permit-screening component.
