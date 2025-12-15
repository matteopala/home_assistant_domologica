# Domologica Integration for Home Assistant

Custom integration for Home Assistant to read XML statuses from Domologica devices and expose them as entities (lights, sensors, etc.).

## Features

- Polls a local XML file every 20 seconds.
- Updates light entities based on `isswitchedon` / `isswitchedoff` statuses.
- Supports multiple elements from the XML.
- Fully compatible with Home Assistant running on Docker Compose.

## Installation

### Via HACS

1. Open HACS in Home Assistant.
2. Click **Integrations → Explore & Add Repositories**.
3. Search for `Domologica`.
4. Add repository: `https://github.com/matteopala/home_assistant_domologica`
5. Install the integration.
6. Restart Home Assistant.

### Manual Installation

1. Clone the repository into `custom_components/domologica` inside your Home Assistant configuration folder:
   ```bash
   git clone https://github.com/matteopala/home_assistant_domologica custom_components/domologica
