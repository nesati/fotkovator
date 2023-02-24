# Fotkovátor

Fotkovátor je modulární systém na automatické štítkování fotek napsaný v Pythonu.

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

Celý systém se konfiguruje v souboru `fotkovator.yaml` ve formátu [yaml](https://yaml.org/). Je nutné zvolit právě jednu `database` (databázi) a právě jeden `backend` (zdroj obrázků). Všechny ostatní moduly jsou volitelné. Je však doporučené nainstalovat a nakonfigurovat alespoň jeden modul kategorie `frontend` (uživatelské rozhraní).

Nyní se podívejme na příklad konfigurace.

```yaml
backend:  # konfigurace zdroje obrázků
  module: localfs  # volba modulu (Lokální soubory)
  path: './photos'  # konfigurace modulu

database:  # konfigurace databáze
  module: PostgreSQL  # volba modulu
  password: mysecretpassword  # konfigurace modulu

modules:  # volitelné moduly
  - module: tag.metadata
  - module: frontend.basic_webserver # volba modulu (webové uživatelské rozhraní)
    # konfigurace modulu
    port: 8080
  - module: tag.face_recognition
```

Pro detailní návod na konfiguraci jednotlivých modulů zajděte do sekce [Konfigurace modulů](#konfigurace-modulů).

## Použití

Program zapnete příkazem:

```shell
python fotkovator.py
```

Program okamžitě začne zpracovávat fotky z nakonfigurovaného zdroje. Způsob otevření uživatelského rozhraní záleží na nakonfigurovaném rozhraní.

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

## Možnosti rozšíření

Způsoby, kterými lze vylepšit tento projekt, ale nejsou jeho součástí.

### Moduly

Možnosti rozšíření kompatibilní se současným modulárním systémem.

- Android aplikce (backend + frontend)
- Modul co umožňuje spouštení ostatních modulů na jiném počítači (cloud GPU)

### Další

- Moduly nahrazující fotky
  - Kolorizace černobílých fotek
  - Koprese
- [CLIP](https://openai.com/blog/clip/) vyhledávání

## Credits

[py-event-bus](https://github.com/joeltok/py-event-bus)