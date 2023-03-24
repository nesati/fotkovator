# Fotkovátor - Technická dokumentace

## Přehled systému
### Core

- čte konfiguraci
- spouští moduly

### Moduly

#### Blackend

- hlavní proces
- přistupuje k fotkám a obrázkům
- získává metadata fotek
- může být jen jeden

#### Štítky

- přidává štítky fotkám

#### Databáze

- ukládá dlouhodobě data
- zařizuje vyhledávání

#### Frontend

- umožňuje přístup uživateli
- může být jen jedna


## Tvorba modulu

## Události
### `rescan`

Oznamuje systému, že proběhne kontrola zdroje obrázků. Událost má dva argumety:
1. typ skenu
   - `manual`
     - událost způsobená uživatelem
     - všechny fotky se mají projít znovu
   - `periodic`
     - událost způsobená uběhnutím času
     - kontrolují se změny ve zdroji obrázků
2. `asyncio.Event` - Databáze připravená
   - databáze spouští tuto událost jakmile jsou provedeny potřebné akce pro skenování (např.: označení všech fotek za nenaskenované)
   - ostatní moduly čekají na tuto událost je-li to nutné

### `img_removed`

Oznamuje, že daný obrázek už není ve zdroji obrázků.
1. uid obrázku

### `new_image`

Oznamuje, že byl nalezen nový obrázek.

1. `uid` - identifikátor obrázku v databázi
2. `asyncio.Event` - Databáze připravená
   - databáze spouští tuto událost jakmile jsou provedeny potřebné akce pro přijetí dalších akcí na obrázku (např.: přidání štítku)
   - ostatní moduly čekají na tuto událost je-li to nutné
3. `PIL.Image` - Obrázek samotný
   - určen pro štítkovací moduly
4. `uri` - identifikátor obrázku ve zroji obrázků
5. `datetime.datetime` nebo `None` - datum a čas vzniku obrázku
6. `dict` - metadata získaná zdrojem
   - žádný klíč není zaručený

### `remove_tag`

Oznamuje, že má být odstraněn šítek od fotky.

1. `uid` - identifikátor obrázku v databázi
2. jméno tagu

### `rename_tag`

1. původní jméno tagu
2. nové jméno tagu

### `delete_tag`

Oznamuje, že daný štítek má přestat existovat. Jak na seznamu štítků tak u všech fotek, které ho mají.

1. jméno štítku

### `stop`

Oznamuje, že se systém vypne. Jakmile modul obdrží tuto událost má poslední šanci provést nutné operace k bezpečnému ukončení. Poté co všechny moduly tuto událost zpracují, jsou všechny úlohy ukončeny a fotkovátor se vypíná.

1. důvod vypnutí