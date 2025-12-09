"""Domologica integration for Home Assistant via HACS"""

from homeassistant.helpers import discovery

async def async_setup(hass, config):

    url = config.get(
        "domologica_url",
        "http://192.168.5.2/api/element_xml_statuses.xml"
    )
    hass.data["domologica_url"] = url

    # Carica piattaforme
    hass.async_create_task(
        discovery.async_load_platform(hass, "light", "domologica", {}, config)
    )
    hass.async_create_task(
        discovery.async_load_platform(hass, "cover", "domologica", {}, config)
    )
    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", "domologica", {}, config)
    )

    return True
