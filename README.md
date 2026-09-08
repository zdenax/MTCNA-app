# MTCNA-app

> **Poznámka:** repo obsahuje jen samotnou kvízovou aplikaci (Flask
> server + UI). Žádné banky otázek zde nejsou a nejsou ani nikde
> v historii commitů — nejsou předmětem tohoto repozitáře.

MikroTik MTCNA cert kvíz appka. Dva běhy, jeden HTML zdroj.

## Screenshoty

| Desktop | Mobil — otázka | Mobil — menu |
|---|---|---|
| ![desktop](docs/screenshots/desktop-question.png) | ![mobil otázka](docs/screenshots/mobile-question.png) | ![mobil menu](docs/screenshots/mobile-menu.png) |

## Soubory

- `mtcna_web.py` — Flask app, port 5050, jen localhost.
- `mtcna_web_network.py` — Flask app pro LAN/testování na mobilu (import HTML z `mtcna_web.py`).
- `mtcna_quiz_standalone.html` — starší statická verze bez serveru.
- `build_pwa.py` — sestavení standalone verze z bank otázek.

## Spuštění

```bash
python3 mtcna_web.py            # localhost:5050
python3 mtcna_web_network.py    # LAN, pro test na telefonu
```

Banku otázek (JSON) je potřeba doplnit vlastní — stačí libovolný `*.json`
soubor vedle `mtcna_web.py` (kromě `progress.json`) v tomto formátu:

```json
[
  {
    "number": 1,
    "text": "Znění otázky",
    "options": ["Odpověď A", "Odpověď B", "Odpověď C"],
    "correct": 0
  }
]
```

Appka automaticky najde všechny takové soubory a nabídne je v
rozbalovacím seznamu "Zdroj" — žádná další registrace není potřeba.
