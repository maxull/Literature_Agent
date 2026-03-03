# TODO

- [ ] Add a short architecture diagram to `README.md` covering fetch -> rank -> summarize -> UI.
- [ ] Add tests for digest schema stability consumed by `shiny_app/app.py`.
- [ ] Add a smoke test that loads the latest digest and validates required keys.
- [ ] Define and document a fallback behavior when no digest files are present.
- [ ] Review `config.yaml` defaults (`days_back`, `max_summaries_total`) for weekly operating targets.
