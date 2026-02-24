# papadam/docs

MkDocs documentation site for papadam.
Fork of [papad-docs](https://gitlab.com/servelots/papad/papad-docs).

---

## Local preview

```bash
docker compose --profile docs up
# → docs available at http://localhost:8001
```

Or without Docker:

```bash
pip install mkdocs
mkdocs serve
```

MkDocs has live reload — changes appear immediately.

---

## Contributing

- Edit files in `docs/docs/`
- Add new pages to `mkdocs.yml` nav
- Store screenshots in `docs/static/<section>/`
- License: CC-BY-SA 4.0
