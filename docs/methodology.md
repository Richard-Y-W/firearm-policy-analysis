@"

\# Methodology



\## Main question

Do states adopting permitless concealed carry experience different changes in firearm death rates than states that do not?



\## Policy definition

RAND State Firearm Law Database v6.0:

\- Law Class: carrying a concealed weapon (ccw)

\- Law Class Subtype: shall issue (permit not required)



\## Outcomes

CDC WONDER state-year crude death rates per 100,000:

\- Total firearm deaths

\- Firearm homicide

\- Firearm suicide



\## Baseline design

For each state:

A = average(post-period rate) - average(pre-period rate)



Compare adopter and non-adopter A values using Welch's t-test.



\## Extensions

\- Alternative windows

\- Event-study / difference-in-differences

\- Separate homicide and suicide outcomes

"@ | Set-Content docs\\methodology.md

