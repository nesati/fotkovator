# CLIP vyhledávání

[CLIP](https://openai.com/research/clip) je neuronová síť propojující obrázky a text. Modul `search.CLIP` tuto 
schopnost využívá k seřazování výsledků vyhledávání podle štítků. Vyhledávejte pokud možno v angličtině viz [první CLIP modul](../../modules/tag/CLIP/README.md).

## Instalace

Modul vyžaduje databázi s podporou vektorů (např.: [`database.PostgreSQL_kNN`](../../database/PostgreSQL_kNN/README.md)).

```shell
pip install -r modules/search/CLIP/requirements.txt
```

## Argumenty

`model` - (volitelný, výchozí hodnota: `ViT-B/32`) verze CLIPu, kterou požívat

## Příklad konfigurace

```yaml
search:
  module: CLIP
```