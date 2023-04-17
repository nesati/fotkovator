# Webové rozhraní

Jednoduchý způsob jak přistupovat k Fotkovátoru je přes webový prohlížeč. Webový server implementuje modul `basic_webserver`. Pokud nezměníte konfiguraci stačí po zapnutí Fotkovátoru navštívit [localhost:5000](http://localhost:5000).

## Instalace

```shell
pip install -r modules/modules/frontend/basic_webserver/requirements.txt 
```

## Argumenty

`port` - (volitelný, výchozí hodnota: 5000) port na kterém poslouchat

`host` - (volitelný, výchozí hodnota: localhost) interface kde poslouchat

## Příklad konfigurace

```yaml
modules:
  - module: frontend.basic_webserver
    port: 8080 # příklad změny portu
```