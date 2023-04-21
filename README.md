# Fotkovátor

[[teoretická práce]](documentation.pdf)

Fotkovátor je modulární systém na automatické štítkování fotek napsaný v Pythonu. Tento dokument obsahuje informace o instalaci a konfiguraci pro uživatele. Hledáte-li objasnění technických detailů implementace, najdete je v [technické dokumentaci](TECHNICAL_DOCS.md). Ještě detailnější popis pak najdete v [teoretické práci](documentation.pdf).

## Instalace

Nejprve potřeba mít nainstalovaný [Python](https://www.python.org/) 3.10 a manažer balíčků `pip`. Doporučil bych využití systému [Anaconda](https://docs.conda.io/en/latest/miniconda.html), kvůli instalaci balíčků vyžadovaných některými moduly a kvůli taktéž doporučené možnosti vytvořit virtuální prostředí:

```shell
conda create -n fotkovator python=3.10
conda activate fotkovator
```

Pro instalaci projektu samotného nejprve oklonujte repozitář:

```shell
git clone https://github.com/nesati/fotkovator
cd fotkovator
```

Od teď všechny příkazy předpokládají, že se nacházíte v kořenovém adresáři repozitáře. Dále nainstalujte závislosti příkazem:

```shell
pip install -r requirements.txt
```

Jednotlivé moduly pak mají svoje požadavky na instalaci, ale většinou stačí nainstalovat závislosti příkazem: `pip install -r modules/<cesta k modulu>/requirements.txt`. Bližší informace najdete v [sekcích jednotlivých modulů](#moduly).

## Konfigurace

Celý systém se konfiguruje v souboru `fotkovator.yaml` ve formátu [YAML](https://yaml.org/). Je nutné zvolit právě jednu databázi (`database`) a právě jeden zdroj obrázků (`backend`). Všechny ostatní moduly jsou volitelné. Je však doporučené nainstalovat a nakonfigurovat alespoň jeden modul kategorie uživatelské rozhraní (\verb|frontend|).

V repozitáři se nachází výchozí konfigurace, ve které najdete nakonfigurovaný zdroj fotek prohledávající složku \verb|photos|, kterou musíte vytvořit a vložit do ní fotky, které chcete oštítkovat, PostgreSQL klient připojující se na `postgres://fotkovator:mysecretpassword@localhost:5432/fotkovator`, Webovým uživatelským rozhraním na [localhost:8080](http://localhost:8080) a všemi štítkovacími moduly v repozitáři.

Projekt jsem testoval na operačních systémech Linux a Windows.

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

Pro detailní návod na konfiguraci jednotlivých modulů zajděte do sekce [Konfigurace modulů](#moduly).

## Použití

Program zapnete příkazem:

```shell
python fotkovator.py
```

Po spuštění načte konfiguraci a okamžitě začne zpracovávat fotky z nakonfigurovaného zdroje. Způsob otevření uživatelského rozhraní záleží na nakonfigurovaném rozhraní.

## Moduly

Návod na instalaci a konfiguraci jednotlivých modulů najdete ve složkách jednotlivých modulů. Tady je seznam všech 
modulů.

- Zdroje obrázků
  - [Lokální soubory](modules/backend/localfs/README.md)
  - [Plex](modules/backend/plex/README.md)
- Databáze
  - [PostgreSQL](modules/database/PostgreSQL/README.md)
  - [Vektorový PostgreSQL](modules/database/PostgreSQL_kNN/README.md)
- Vyhledávání
  - [CLIP vyhledávání](modules/search/CLIP/README.md)
- Moduly
  - Grafické rozhraní
    - [Webové rozhraní](modules/modules/frontend/basic_webserver/README.md)
  - Štítkovací
    - [Rozpoznání obličejů](modules/modules/tag/face_recognition/README.md)
    - [Zpracování metadat](modules/modules/tag/metadata/README.md)
    - [CLIP](modules/modules/tag/CLIP/README.md)
  - Další
    - [Záznamník událostí](modules/modules/misc/event_logger/README.md)

## Možnosti rozšíření

Způsoby, kterými lze vylepšit tento projekt, ale nejsou jeho součástí.

### Moduly

Možnosti rozšíření kompatibilní se současným modulárním systémem.

- Mobilní aplikce (backend + frontend)
- Modul co umožňuje spouštení ostatních modulů na jiném počítači (cloud GPU)
- Detekce duplicit
- OCR

### Další

- Moduly nahrazující fotky
  - Kolorizace černobílých fotek
  - Koprese
  - otočení fotek
  - upscaling
- Automatické kombinování podobných fotek
  - live photos
  - HDR/denoising
  - automatické panorama
  - aby se všichni dívali do kamery najednou
- [CLIP](https://openai.com/blog/clip/) vyhledávání viz [clip-retrieval](https://github.com/rom1504/clip-retrieval)

## Credits

[py-event-bus](https://github.com/joeltok/py-event-bus)