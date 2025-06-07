## 🇪🇺 EUR-Lex Dutch Legislation Crawler

This job scrapes Dutch-language EU from [EUR-Lex](https://eur-lex.europa.eu/) using the advanced search page. It extracts:

- URL to the Dutch legal document
- Full legal text in Dutch
- Marks the source as `"EUR-Lex"`

The script is scheduled to run every other day via GitHub Actions. Results are pushed to [`vGassen/EUR-Lex-Dutch-Legislation`](https://huggingface.co/datasets/vGassen/EUR-Lex-Dutch-Legislation).
