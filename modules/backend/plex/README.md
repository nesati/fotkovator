# Plex

Klient pro multimediální server [Plex](https://plex.tv).

## Instalace


```shell
pip install -r modules/backend/plex/requirements.txt
```

## Argumenty

`XPlexToken` - (povinný) Autorizařní toeken plex servru (viz [návod na jeho získání](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/))

`base_url` - (povinný) Url plex serveru

`section` - (povinný) Název knihovny s fotkami v Plexu

`max_concurency` - (volitelný, výchozí hodnota: 8) Počet fotek které analyzovat současně


## Příklad konfigurace

```yaml
backend:
  module: plex
  XPlexToken: '********************'
  base_url: "http://localhost:32400/"
  section: Foto
```
