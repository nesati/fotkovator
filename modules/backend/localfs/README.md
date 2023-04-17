# Lokální soubory

Přístup k lokálním souborům je umožněn modulem `localfs`. Periodicky kontroluje změny v souborovém systému. Nakonfigurovanou složku musíte vytvořit ručně, pak do ní můžete vkládat a z ní odstraňovat fotky a obrázky libovolně a systém by si měl poradit.

## Instalace

```shell
pip install -r modules/backend/localfs/requirements.txt
```

## Argumenty

`path` - (povinný) Cesta ke složce s obrázky

`max_concurency` - (volitelný, výchozí hodnota: 16) Počet fotek které analyzovat současně

## Příklad konfigurace

```yaml
backend:
  module: localfs
  path: './photos'
```