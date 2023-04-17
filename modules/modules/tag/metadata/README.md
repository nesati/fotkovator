# Zpracování metadat

Modul `metadata` přidává štítky na základě informací, které nejsou obsaženy v obraze samotném. Například datum pořízení obrázku, složky ve kterých se nachází, název fotoaparátu atd.

## Instalace

```shell
pip install -r modules/modules/tag/metadata/requirements.txt
```

## Příklad konfigurace

```yaml
modules:
  - module: tag.metadata
```