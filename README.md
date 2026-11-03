# jaapgerritsma.nl

Statische versie van de website van Jaap Gerritsma (1942–2025), medisch wetenschapper en schrijver.
Overgezet van WordPress (Savvii) naar GitHub Pages in november 2026.

- `docs/` is de site zoals hij online staat (GitHub Pages: branch `main`, map `/docs`).
- Alle oude adressen uit WordPress zijn behouden, ook `/wp-content/uploads/...`.
- Geen cookies, geen analytics. Lettertypen (Newsreader, IBM Plex Mono) staan in de site zelf.
- Elke pagina heeft een Content-Security-Policy en referrer-policy als `<meta>`-tag (GitHub Pages kan geen headers sturen). Alleen YouTube-embeds (youtube-nocookie.com) mogen van buiten komen; zie `CSP` in `build.py`.

## Opnieuw opbouwen

Alleen nodig als de inhoud verandert. Zet de WordPress-export in `src/export.xml` en de map
`wp-content/uploads` in `zip_in/`, en draai:

    python3 build.py src/export.xml docs

De export en uploads staan bewust niet in deze repo (zie `.gitignore`).
