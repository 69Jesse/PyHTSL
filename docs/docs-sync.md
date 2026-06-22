# Docs Sync

The htsw reference docs under `docs/htsw/` in this repo are a **vendored copy**
of the htsw project's docs. The HTSW Reference section of this book links into
them.

To refresh that copy from a local checkout of the htsw repo:

```sh
python scripts/sync_docs.py <path-to-htsw-repo>
```

The tool:

- Validates the path exists and contains `docs/` and `book.toml`.
- Clears `docs/htsw/` and re-copies the htsw `docs/` tree into it.
- Copies htsw's `book.toml` into `docs/htsw/` for provenance (it is not used to
  build this book).
- Prints how many files were copied and the destination.

It is idempotent — re-run it any time the upstream htsw docs change.
