"""Permitless-carry legal timing used by the panel builders.

The mapping is limited to within-panel adoption events. Baseline permitless
states and legally ambiguous reviewed states are tracked separately so they are
not silently treated as clean post-adoption events.
"""

PERMITLESS_ADOPTION = {
    "Alaska": 2003,
    "Arizona": 2010,
    "Wyoming": 2011,
    "Kansas": 2015,
    "Mississippi": 2015,
    "Maine": 2015,
    "West Virginia": 2016,
    "Idaho": 2016,
    "Missouri": 2017,
    "New Hampshire": 2017,
    "North Dakota": 2017,
    "South Dakota": 2019,
    "Kentucky": 2019,
    "Oklahoma": 2019,
    "Montana": 2021,
    "Iowa": 2021,
    "Tennessee": 2021,
    "Texas": 2021,
    "Utah": 2021,
    "Georgia": 2022,
    "Indiana": 2022,
    "Ohio": 2022,
    "Alabama": 2023,
    "Florida": 2023,
    "Nebraska": 2023,
    "Louisiana": 2024,
    "South Carolina": 2024,
}

BASELINE_PERMITLESS_STATES = {
    "Vermont",
}

REVIEWED_AMBIGUOUS_STATES = {
    "Arkansas",
}
