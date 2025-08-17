import datetime
import pytz

# Korean Standard Time timezone
KST = pytz.timezone('Asia/Seoul')

# Default Digimon data with exact spawn times synchronized with dsrworldwiki.com
DEFAULT_DIGIMONS = [
    {
        "nombre": "Pumpkinmon",
        "tipo": "Data",
        "tipo_icon": "💾",
        "mapa": "Shibuya",
        "recompensa": "Digital Hazard Coin",
        "recompensa_icon": "🪙",
        "horarios": [
            {"hora": 19, "minuto": 30},
            {"hora": 21, "minuto": 30}
        ],
        "recurrencia_dias": 1,
        "fecha_inicio": datetime.datetime(2025, 8, 18, 19, 30, tzinfo=KST),
        "imagen": "https://dsrworldwiki.com/assets-opt/digimons/pumpmon-800.0d183a820368.avif",
        "color": 0x0099FF
    },
    {
        "nombre": "Datamon",
        "tipo": "Virus",
        "tipo_icon": "🦠",
        "mapa": "Odaiba Entrance",
        "recompensa": "Digital Hazard Coin",
        "recompensa_icon": "🪙",
        "horarios": [
            {"hora": 20, "minuto": 40}
        ],
        "recurrencia_dias": 1,
        "fecha_inicio": datetime.datetime(2025, 8, 18, 20, 40, tzinfo=KST),
        "imagen": "https://dsrworldwiki.com/assets-opt/digimons/datamon-800.0616d90fb62c.avif",
        "color": 0xFF3366
    },
    {
        "nombre": "Gotsumon",
        "tipo": "Data",
        "tipo_icon": "💾",
        "mapa": "Shibuya",
        "recompensa": "Digital Hazard Coin",
        "recompensa_icon": "🪙",
        "horarios": [
            {"hora": 23, "minuto": 0},
            {"hora": 1, "minuto": 0}
        ],
        "recurrencia_dias": 1,
        "fecha_inicio": datetime.datetime(2025, 8, 18, 23, 0, tzinfo=KST),
        "imagen": "https://dsrworldwiki.com/assets-opt/digimons/gottsumon-800.ca5003fad519.avif",
        "color": 0x0099FF
    },
    {
        "nombre": "BlackSeraphimon",
        "tipo": "Virus",
        "tipo_icon": "🦠",
        "mapa": "??? (Spiral Mountain -> Apocalymon Map)",
        "recompensa": "Evil Digital Hazard Coin",
        "recompensa_icon": "💰",
        "horarios": [
            {"hora": 16, "minuto": 0}
        ],
        "recurrencia_dias": 5,
        "fecha_inicio": datetime.datetime(2025, 8, 23, 16, 0, tzinfo=KST),
        "imagen": "https://dsrworldwiki.com/assets-opt/digimons/blackseraphimon-800.4544de9758c5.avif",
        "color": 0xFF3366
    },
    {
        "nombre": "Omegamon",
        "tipo": "Vacuna",
        "tipo_icon": "🛡️",
        "mapa": "Valley Of Darkness",
        "recompensa": "Sacred Codes",
        "recompensa_icon": "⭐",
        "horarios": [
            {"hora": 14, "minuto": 30}
        ],
        "recurrencia_dias": 6,
        "fecha_inicio": datetime.datetime(2025, 8, 24, 14, 30, tzinfo=KST),
        "imagen": "https://dsrworldwiki.com/assets-opt/digimons/omegamon-800.7a602017a50c.avif",
        "color": 0x00FF00
    },
    {
        "nombre": "Ophanimon",
        "tipo": "Vacuna",
        "tipo_icon": "🛡️",
        "mapa": "??? (Spiral Mountain -> Apocalymon Map)",
        "recompensa": "Evil Digital Hazard Coin",
        "recompensa_icon": "💰",
        "horarios": [
            {"hora": 16, "minuto": 0}
        ],
        "recurrencia_dias": 12,
        "fecha_inicio": datetime.datetime(2025, 8, 30, 16, 0, tzinfo=KST),
        "imagen": "https://dsrworldwiki.com/assets-opt/digimons/ophanimon-800.8dffa51532ee.avif",
        "color": 0x00FF00
    },
    {
        "nombre": "Megidramon",
        "tipo": "Virus",
        "tipo_icon": "🦠",
        "mapa": "Valley Of Darkness",
        "recompensa": "Sacred Codes",
        "recompensa_icon": "⭐",
        "horarios": [
            {"hora": 16, "minuto": 0}
        ],
        "recurrencia_dias": 13,
        "fecha_inicio": datetime.datetime(2025, 8, 31, 16, 0, tzinfo=KST),
        "imagen": "https://dsrworldwiki.com/assets-opt/digimons/megidramon-800.ffeaccae5bb5.avif",
        "color": 0xFF3366
    }
]

# Embed colors for different alert types
EMBED_COLORS = {
    "spawn": 0xFF0000,      # Red for spawn alerts
    "warning": 0xFFFF00,    # Yellow for early warnings  
    "info": 0x00FFFF,       # Cyan for information
    "success": 0x00FF00,    # Green for success
    "error": 0xFF3366       # Red for errors
}

# Type emojis for different Digimon types
TYPE_EMOJIS = {
    "Data": "💾",
    "Virus": "🦠",
    "Vacuna": "🛡️"
}

# Reward emojis for different reward types
REWARD_EMOJIS = {
    "Digital Hazard Coin": "🪙",
    "Evil Digital Hazard Coin": "💰",
    "Sacred Codes": "⭐"
}

# Alert system settings
ALERT_SETTINGS = {
    "early_warning_minutes": 20,  # Early warning 20 minutes before
    "spawn_alert": True,          # Alert when raid spawns
    "mention_everyone": True      # Mention @everyone on spawns
}
