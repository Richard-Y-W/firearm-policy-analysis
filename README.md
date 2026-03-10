\# WRHC 2026 — Permitless Carry Policy Analysis



This repository analyzes whether adoption of permitless carry laws is associated with changes in firearm death rates across U.S. states.



The analysis uses CDC WONDER mortality data and a quasi-experimental comparison between adopting states and non-adopting states.



---



\# Data



Source: CDC WONDER mortality database



Outcomes analyzed:



• Total firearm deaths  

• Firearm homicide  

• Firearm suicide  



Panel structure:



State × Year (1999–2024)



Outcome variable:



Firearm deaths per 100,000 population



---



\# Method



For each adopting state:



A = mean(post adoption rate) − mean(pre adoption rate)



We compare the distribution of A between:



• states adopting permitless carry  

• states that did not adopt



Statistical test:



Welch two-sample t-test



Robustness windows:



• 2-year pre vs 2-year post  

• 3-year pre vs 3-year post  

• 5-year pre vs 5-year post



---



\# Results



Combined results table:



| Outcome | Window | p-value |

|-------|------|------|

| Total firearm deaths | 2y | 0.019 |

| Total firearm deaths | 3y | 0.192 |

| Total firearm deaths | 5y | 0.201 |

| Firearm homicide | 2y | 0.800 |

| Firearm homicide | 3y | 0.598 |

| Firearm homicide | 5y | 0.634 |

| Firearm suicide | 2y | 0.000036 |

| Firearm suicide | 3y | 0.035 |

| Firearm suicide | 5y | 0.000697 |



Key observation:



Any observed increase in firearm deaths appears to be primarily driven by \*\*firearm suicides rather than firearm homicides\*\*.



---



\# Event-Time Plots



\## Total Firearm Deaths



!\[Total firearm deaths](outputs/figures/event_time_total_firearm_deaths.png)



---



\## Firearm Homicide



!\[Firearm homicide](outputs/figures/event_time_firearm_homicide.png)



---



\## Firearm Suicide



!\[Firearm suicide](outputs/figures/event_time_firearm_suicide.png)



---



\# Interpretation



The results suggest that states adopting permitless carry laws experienced larger increases in firearm suicide rates relative to non-adopting states during the study window.



No statistically significant differences were detected for firearm homicide.



These findings are descriptive and do not establish causal effects but highlight potential relationships between firearm access policy and suicide outcomes.



---



\# Repository Structure



```

src/

&nbsp;   data/

&nbsp;       build\_analysis\_panel.py

&nbsp;       build\_homicide\_panel.py

&nbsp;       build\_suicide\_panel.py



&nbsp;   analysis/

&nbsp;       run\_wrhc\_total\_analysis.py

&nbsp;       run\_wrhc\_homicide\_analysis.py

&nbsp;       run\_wrhc\_suicide\_analysis.py

&nbsp;       combine\_results.py



data/

&nbsp;   raw/

&nbsp;       cdc\_wonder/



outputs/

&nbsp;   figures/

&nbsp;   tables/

```



---



\# How to Reproduce



```

python src/data/build\_analysis\_panel.py

python src/analysis/run\_wrhc\_total\_analysis.py



python src/data/build\_homicide\_panel.py

python src/analysis/run\_wrhc\_homicide\_analysis.py



python src/data/build\_suicide\_panel.py

python src/analysis/run\_wrhc\_suicide\_analysis.py



python src/analysis/combine\_results.py

```



---



\# Authors

Yucheng Wang





WRHC 2026 Research Project

