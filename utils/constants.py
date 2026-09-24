# ==============================================================================
# TEMPORAL MAPPINGS
# ==============================================================================
MONTHS_LIST = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
]
MONTH_MAP = {month: index+1 for index, month in enumerate(MONTHS_LIST)}

DAYS_LIST = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DAYS_MAP = {day: index+1  for index, day in enumerate(DAYS_LIST)}

# Specific 0-indexed map for PostgreSQL ISODOW minus 1 calculations (nPETS)
ISODOW_MAP_0_INDEXED = {
    0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 
    3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
}

# ==============================================================================
# DATABASE TABLE WHITELISTS (Security mappings)
# ==============================================================================
# Prevents SQL Injection by restricting table access strictly to known names
VALID_TABLES = {
    "Atmospheric Gases": 'port_thessaloniki_gases',
    "Particles": 'port_thessaloniki_particles',
    "Acoustic/Sound Levels": 'port_thessaloniki_noise',
}

VALID_FUEL_TABLES = {
    "regional_fuel_con": "Region",
    "prefecture_fuel_con": "Prefecture"
}

VALID_NPETS_TOOLS = {
    "ELPI": "elpi",
    "OPS": "ops",
    "METADATA": "metadata"
}

# ==============================================================================
# UI DROPDOWNS & MAPPINGS (nPETS)
# ==============================================================================
NPETS_TOOLS = ["ELPI", "OPS", "METADATA"]
NPETS_PLACES = ["SKG Airport", "SKG Port", "SKG CERTH", "SKG AUTH Main Road"]
NPETS_SEASONS = ["Warm", "Cold"]
NPETS_TIMEFRAMES = ["Day", "Hour"]

NPETS_PLACE_MAPPING = {
    "SKG Airport": 'Airport', 
    "SKG Port": 'Port', 
    "SKG CERTH": 'Background', 
    "SKG AUTH Main Road": 'Road'
}

NPETS_REVERSE_PLACE_MAPPING = {v: k for k, v in NPETS_PLACE_MAPPING.items()}