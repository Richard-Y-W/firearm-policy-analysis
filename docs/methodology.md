# Methodology

## Main Question

Do states adopting permitless concealed carry experience different changes in firearm death rates than states that do not?

## Policy Definition

The primary treatment is manually coded permitless concealed carry:

- Statewide concealed carry allowed without first obtaining a carry permit
- Annual state-year coding uses the first calendar year in which the law is effective
- Arkansas, Mississippi, and Vermont are handled as non-clean edge cases in the legal audit

Phase 3A uses the Tufts State Firearm Law Database for external firearm-law controls:

- permit-to-purchase laws
- waiting periods
- universal background checks
- ERPO/red-flag laws
- safe-storage laws
- stand-your-ground laws
- dealer licensing

## Outcomes

CDC WONDER state-year crude death rates per 100,000:

- Total firearm deaths
- Firearm homicide
- Firearm suicide

## Baseline Design

For each state:

`A = average(post-period rate) - average(pre-period rate)`

Adopter and non-adopter `A` values are compared using Welch's t-test.

## Extensions

- Alternative pre/post windows
- Event-study and difference-in-differences models
- Separate homicide and suicide outcomes
- External firearm-law control sensitivity models
