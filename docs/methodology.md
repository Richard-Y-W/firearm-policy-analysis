# Methodology

## Main Question

Do states adopting permitless concealed carry experience different changes in firearm death rates than states that do not?

## Policy Definition

RAND State Firearm Law Database v6.0:

- Law class: carrying a concealed weapon (CCW)
- Law class subtype: shall issue, permit not required

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
