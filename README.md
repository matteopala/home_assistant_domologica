# homeassistant_domologica
Home Assistant Domologica Integration
# Domologica Home Assistant Integration

Custom component per Home Assistant per integrare la domotica Domologica.

## Caratteristiche

- Supporto per luci (`light`), tapparelle (`shutter`) e sensori generici (`sensor`)
- Aggiornamento asincrono e caching interno
- Compatibile con HACS per installazione e aggiornamenti automatici
- URL XML centrale configurabile

## Configurazione

Aggiungere nel `configuration.yaml`:

```yaml
domologica:
  domologica_url: "http://192.168.5.2/api/element_xml_statuses.xml"
