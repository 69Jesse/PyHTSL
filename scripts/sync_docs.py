"""Vendors the htsw reference docs into this repo at docs/htsw/.

Run as: python scripts/sync_docs.py <path-to-htsw-repo>
"""

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = HERE.parent / 'docs' / 'htsw'


def sync(htsw_repo: Path) -> None:
    htsw_repo = htsw_repo.resolve()
    docs = htsw_repo / 'docs'
    book = htsw_repo / 'book.toml'
    if not htsw_repo.is_dir():
        raise SystemExit(f'Not a directory: {htsw_repo}')
    if not docs.is_dir():
        raise SystemExit(f'Missing docs/ in htsw repo: {docs}')
    if not book.is_file():
        raise SystemExit(f'Missing book.toml in htsw repo: {book}')

    # Clear any previous copy, then re-vendor the reference content only —
    # the theme/ folder is mdBook build tooling, not docs.
    if DEST.exists():
        shutil.rmtree(DEST)
    shutil.copytree(docs, DEST, ignore=shutil.ignore_patterns('theme'))
    shutil.copy2(book, DEST / 'book.toml')

    count = sum(1 for path in DEST.rglob('*') if path.is_file())
    print(f'Copied {count} files from {docs} to {DEST}')


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/sync_docs.py <path-to-htsw-repo>')
    sync(Path(sys.argv[1]))


if __name__ == '__main__':
    main()
