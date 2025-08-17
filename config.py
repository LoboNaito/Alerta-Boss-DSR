# Legacy config file - Data management moved to data/digimon_manager.py
# This file is kept for backward compatibility

# Import data from the new system
from data.default_data import (
    DEFAULT_DIGIMONS as DIGIMONS,
    EMBED_COLORS,
    TYPE_EMOJIS, 
    REWARD_EMOJIS,
    ALERT_SETTINGS,
    KST
)

# Configuration notes:
# - Digimon data is now managed via data/digimon_manager.py
# - Use /add_digimon, /remove_digimon, /update_digimon commands for management
# - Data is automatically saved to data/digimon_data.json
# - This file provides fallback access to default data
