@"

\# Firearm Policy Analysis



This project studies whether states adopting permitless concealed carry experienced different changes in firearm death rates than non-adopting states.



\## Data sources

\- CDC WONDER state-year mortality exports

\- RAND State Firearm Law Database v6.0



\## Structure

\- data/raw/cdc\_wonder/ : raw CDC WONDER exports

\- data/raw/rand/ : raw RAND law database

\- data/processed/ : cleaned merged analysis panel

\- src/data/ : data cleaning and panel construction

\- src/analysis/ : statistical analysis and figures

\- notebooks/ : exploratory and public-facing notebooks

\- outputs/ : figures and tables



\## Main outcomes

\- Total firearm deaths

\- Firearm homicide

\- Firearm suicide



\## Main design

\- State-year panel

\- Pre/post change score analysis

\- Welch t-test

\- Event-study / DiD robustness checks

"@ | Set-Content README.md

