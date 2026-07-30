# Port Analytics Mappings
PORT_TABLE_MAPPING = {
    "Atmospheric Gases": 'port_thessaloniki_gases',
    "Particles": 'port_thessaloniki_particles',
    "Acoustic/Sound Levels": 'port_thessaloniki_noise',
}

MONTHS_LIST = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

DAYS_LIST = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

MONTH_MAP = {month: int(index) + 1 for index, month in enumerate(MONTHS_LIST)}
DAYS_MAP = {day: index for index, day in enumerate(DAYS_LIST)}

VALID_TABLES = {
    "Atmospheric Gases": "port_thessaloniki_gases",
    "Particles": "port_thessaloniki_particles",
    "Acoustic/Sound Levels": "port_thessaloniki_noise"
}