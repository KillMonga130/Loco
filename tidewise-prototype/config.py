"""
TideWise Configuration
Adjust these settings for different locations and alert thresholds
"""

# TARGET LOCATION: Port Elizabeth (Gqeberha), South Africa
LOCATION = {
    'name': 'Port Elizabeth',
    'country': 'South Africa',
    'latitude': -33.96,
    'longitude': 25.60,
    'timezone': 'Africa/Johannesburg'
}

# NOAA DATA SOURCES
NOAA_GFS_BASE_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
NOAA_WAVE_BASE_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfswave.pl"

# DATA FETCH SETTINGS
DATA_GRID_SIZE = 0.5  # Degrees lat/lon around target (larger = more context)
UPDATE_INTERVAL_HOURS = 3  # How often to fetch new data
CACHE_HOURS = 6  # How long to cache downloaded data

# ALERT THRESHOLDS (These will be tuned based on testing)
THRESHOLDS = {
    'yellow': {
        'pressure_drop_3h': 3.0,      # hPa drop in 3 hours
        'wave_height': 2.5,            # meters
        'surge_probability': 0.30      # 30%
    },
    'orange': {
        'pressure_drop_3h': 5.0,      # hPa drop in 3 hours
        'wave_height': 3.5,            # meters
        'surge_probability': 0.60      # 60%
    },
    'red': {
        'pressure_drop_3h': 8.0,      # hPa drop in 3 hours
        'wave_height': 5.0,            # meters
        'surge_probability': 0.85      # 85%
    }
}

# SIMULATED SENSOR SETTINGS (for testing without real hardware)
SIMULATE_SENSORS = True
SENSOR_NOISE_LEVEL = 0.02  # 2% random noise in simulated readings

# DATA STORAGE
DATA_DIR = "data_cache"
LOG_FILE = "tidewise.log"

# DEBUG MODE
DEBUG = True  # Set to False in production
VERBOSE_LOGGING = True
