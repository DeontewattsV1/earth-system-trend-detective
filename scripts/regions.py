"""Shared catalog: study regions and NASA variables for Earth System Trend Detective.

Every box obeys NASA POWER's regional API limits (one parameter per call,
box between 2 and 10 degrees on each side).
"""

REGIONS = {
    "svalbard": dict(
        name="Svalbard & Barents Sea (Arctic)", lat=(76, 80), lon=(10, 20),
        kind="Polar ocean / sea-ice margin",
        why="Arctic amplification: the fastest-warming region on Earth in most records.",
    ),
    "sahel": dict(
        name="Central Sahel (Niger–Mali–Burkina Faso)", lat=(12, 16), lon=(-5, 5),
        kind="Semi-arid savanna / desert edge",
        why="Rainfall collapsed in the 1970s–80s droughts and has partly recovered since.",
    ),
    "amazon": dict(
        name="Southern Amazon (Rondônia–Mato Grosso)", lat=(-12, -6), lon=(-64, -56),
        kind="Tropical rain forest / deforestation frontier",
        why="Deforestation arc: warming and drying of the land surface are reported.",
    ),
    "california": dict(
        name="California Central Valley & Sierra Nevada", lat=(35, 39), lon=(-122, -118),
        kind="Irrigated valley + mountain snowpack",
        why="Repeated megadrought years; soil moisture and snow are water-supply indicators.",
    ),
    "delhi": dict(
        name="Delhi & Upper Indo-Gangetic Plain", lat=(27, 30), lon=(75.5, 78.5),
        kind="Atmosphere above a megacity",
        why="Heavy aerosol pollution can dim sunlight reaching the ground.",
    ),
    "murray": dict(
        name="Murray–Darling Basin (SE Australia)", lat=(-36, -30), lon=(142, 148),
        kind="Inland river basin / farmland",
        why="Large swings between drought (Millennium Drought) and floods.",
    ),
    "sfbay": dict(
        name="San Francisco Bay–Delta Estuary", lat=(37, 39), lon=(-123, -121),
        kind="Tidal estuary",
        why="Estuary where land, ocean and atmosphere meet; coastal fog and heat matter.",
    ),
}

# id: (POWER parameter, short name, units, definition, source, transform)
VARIABLES = {
    "T2M": dict(
        label="Air temperature (2 m)", units="°C", source="MERRA-2 reanalysis (NASA GMAO)",
        definition="How warm the air is about head-height above the ground, averaged over the month.",
        decade_units="°C per decade",
    ),
    "T2M_MAX": dict(
        label="Daily maximum temperature (2 m)", units="°C", source="MERRA-2 reanalysis (NASA GMAO)",
        definition="The hottest temperature reached each day, averaged over the month — a heat indicator.",
        decade_units="°C per decade",
    ),
    "PRECTOTCORR": dict(
        label="Precipitation (bias-corrected)", units="mm/day", source="MERRA-2 reanalysis, bias-corrected (NASA GMAO / POWER)",
        definition="Rain plus snow (as water) falling per day, corrected toward gauge/satellite observations.",
        decade_units="mm/day per decade",
    ),
    "EVLAND": dict(
        label="Evaporation from land", units="mm/day", source="MERRA-2 land surface model (NASA GMAO)",
        definition="Water returned from soil, plants and lakes to the air each day (evapotranspiration).",
        decade_units="mm/day per decade",
    ),
    "GWETROOT": dict(
        label="Root-zone soil wetness", units="0–1 (fraction)", source="MERRA-2 land surface model (NASA GMAO)",
        definition="How full the soil's root zone (top ~1 m) is with water: 0 = bone dry, 1 = saturated.",
        decade_units="per decade",
    ),
    "RH2M": dict(
        label="Relative humidity (2 m)", units="%", source="MERRA-2 reanalysis (NASA GMAO)",
        definition="How close the air is to being saturated with water vapor.",
        decade_units="% per decade",
    ),
    "QV2M": dict(
        label="Specific humidity (2 m)", units="g/kg", source="MERRA-2 reanalysis (NASA GMAO)",
        definition="Grams of water vapor in each kilogram of air — the actual amount of moisture.",
        decade_units="g/kg per decade",
    ),
    "WS10M": dict(
        label="Wind speed (10 m)", units="m/s", source="MERRA-2 reanalysis (NASA GMAO)",
        definition="Average wind speed 10 meters above the surface.",
        decade_units="m/s per decade",
    ),
    "ALLSKY_SFC_SW_DWN": dict(
        label="Sunlight reaching the ground", units="MJ/m²/day", source="NASA CERES SYN1deg (2001–) / GEWEX SRB (before)",
        definition="Solar energy arriving at the surface through clouds and haze. Falls when air is dirtier or cloudier.",
        decade_units="MJ/m²/day per decade",
    ),
    "CLOUD_AMT": dict(
        label="Cloud amount", units="%", source="NASA CERES SYN1deg (2001–) / GEWEX SRB (before)",
        definition="Percentage of the sky covered by cloud.",
        decade_units="% per decade",
    ),
    "SNODP": dict(
        label="Snow depth", units="cm", source="MERRA-2 land surface model (NASA GMAO)",
        definition="How deep the snow on the ground is, averaged over the month.",
        decade_units="cm per decade",
    ),
}

START_YEAR, END_YEAR = 1981, 2025
