DOMAIN = "domologica"

CONF_BASE_URL = "base_url"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

# Wizard / Options
CONF_ALIASES = "aliases"  # dict: {"48": "Luce Cucina", ...}
CONF_ENABLED_ELEMENTS = "enabled_elements"  # list: ["48","25",...]

DEFAULT_SCAN_INTERVAL = 20

SERVICE_REFRESH = "refresh"
SERVICE_COMMAND = "command"

ATTR_ELEMENT_ID = "element_id"
ATTR_ACTION = "action"

PLATFORMS = ["light", "switch", "sensor", "cover"]
