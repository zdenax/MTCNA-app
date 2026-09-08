# MTCNA-app

> **Poznámka:** repo obsahuje jen samotnou kvízovou aplikaci (Flask
> server + UI). Banky otázek (`complete_all.json`, `mtcna_questions.json`)
> zde nejsou a nejsou nikde v historii commitů — nejsou předmětem
> tohoto repozitáře.

MikroTik MTCNA cert kvíz appka. Dva běhy, jeden HTML zdroj.

## Soubory

- `mtcna_web.py` — Flask app, port 5050, jen localhost.
- `mtcna_web_network.py` — Flask app pro LAN/testování na mobilu (import HTML z `mtcna_web.py`).
- `mtcna_quiz_standalone.html` — starší statická verze bez serveru.
- `mtcna_scraper.py` — Playwright scraper na stažení otázek (na vlastní databázi otázek, viz poznámka výše).
- `build_pwa.py` — sestavení standalone verze z bank otázek.

## Spuštění

```bash
python3 mtcna_web.py            # localhost:5050
python3 mtcna_web_network.py    # LAN, pro test na telefonu
```

Banku otázek (JSON) je potřeba doplnit vlastní — viz `mtcna_scraper.py`.
