# Fotkovátor

Systém na automatické štítkování fotek.

## Instalace

Pro jakoukoliv instalaci je nejprve potřeba [Python](https://www.python.org/) a závislosti, které lze nainstalovat příkazem: 

```shell
pip intall -r requirements.txt
```

Další kroky se odvíjejí od zvolených [modulů](#Konfigurace-modulů). Většinou však stačí:

```shell
pip intall -r modules/<cesta k modulu>/requirements.txt
```

## Konfigurace

Celý systém se konfiguruje v souboru `fotkovator.yaml`.

## Použití

Program zapnete spuštěním:

```shell
python fotkovator.py
```

Program okamžitě začne zpracovávat fotky z nakonfigurovaného backendu.

## Konfigurace modulů

### Lokální soubory

Přístup k lokálním souborům je umožněn modulem `localfs`.

#### Argumenty

`path` - *Povinný* Cesta ke složce s obrázky.


#### Příklad konfigurace

```yaml
backend:
  module: localfs
  path: './photos'
```

## TODO

## Credits

[py-event-bus](https://github.com/joeltok/py-event-bus)