# Shared configuration constants for multimodal transport planner

# Distance thresholds
WALKING_RADIUS_M = 500  # Maximum walking distance for interchange (500 meters)
PROXIMITY_THRESHOLD_M = 200  # For finding very close alternatives

# Time buffers (in minutes)
TRANSFER_BUFFER_MIN = 5  # Minimum time to change transport
INTERCHANGE_BUFFER_MIN = 10  # Time buffer for BMTC-Metro-BMTC transfers
WALKING_TIME_PER_100M = 1  # 1 minute per 100 meters walking

# Metro line colors (for UI)
METRO_COLORS = {
    "Green": "#2e7d32",
    "Purple": "#6a1b9a",
    "Yellow": "#f9a825",
}

# Operational hours
BMTC_START_HOUR = 5  # 05:00
BMTC_END_HOUR = 23
BMTC_END_MINUTE = 30  # 23:30

# Multimodal routing
MAX_MULTIMODAL_OPTIONS = 5  # Show top 5 multimodal alternatives
MAX_TRANSFERS_MULTIMODAL = 2  # Max transfers per leg
