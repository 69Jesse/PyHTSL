"""Generate the `pyhtsw-development` Claude Code skill from the docs.

Run after scripts/sync_docs.py:
    python scripts/create_skill.py <skills-dir>

Creates <skills-dir>/pyhtsw-development/ with a SKILL.md that points to the
bundled reference docs under reference/ (progressive disclosure). The skill is
model-invocable so Claude reaches for it whenever you write pyhtsw.
"""

import argparse
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / 'docs'
SKILL_NAME = 'pyhtsw-development'

DESCRIPTION = (
    'Write PyHTSW, a Python frontend that generates htsw projects for Hypixel '
    'Housing. Use whenever working with pyhtsw, pyhtsl, htsw, htsl or Hypixel '
    'Housing scripts — defining functions, events, items, menus, regions or '
    'NPCs, using stats/conditions/locations, or exporting a project. Consult it '
    'before writing or editing any pyhtsw code.'
)

# Curated blurbs for the known pages; any other .md is listed generically.
PAGE_BLURBS = {
    'overview.md': 'What PyHTSW is and how it relates to htsw.',
    'installation.md': 'Installing the package and where output goes.',
    'project-structure.md': 'Laying out a multi-file project: the uv project, flat modules, main.py wiring, asset paths.',
    'exporting.md': 'The project model: projects folder, import.json, building and validating.',
    'importables.md': 'Functions, events, items, regions, menus and NPCs.',
    'items.md': 'Defining items, referencing them, and SNBT.',
    'locations.md': 'The Location type used by location-taking actions.',
    'expressions.md': 'Stats, arithmetic, conditionals and interpolation.',
    'simulator.md': 'Running expressions in-Python for testing.',
    'docs-sync.md': 'How the vendored htsw reference under reference/htsw/ is refreshed.',
}


def render_frontmatter() -> str:
    return '\n'.join(
        ['---', f'name: {SKILL_NAME}', f'description: {DESCRIPTION}', '---'],
    )


def render_body(reference: Path) -> str:
    pages = sorted(p.name for p in reference.glob('*.md'))
    toc: list[str] = []
    for page in pages:
        blurb = PAGE_BLURBS.get(page, page.removesuffix('.md').replace('-', ' '))
        toc.append(f'- [{page.removesuffix(".md")}](reference/{page}) — {blurb}')
    htsw = ''
    if (reference / 'htsw').is_dir():
        htsw = (
            '\n## HTSW reference\n\n'
            'The underlying htsw format (import.json schema, the HTSL action/condition '
            'language) is documented under [reference/htsw/](reference/htsw/) — consult '
            'it for action and condition semantics.\n'
        )
    return f"""{render_frontmatter()}

# PyHTSW development

PyHTSW is a Python frontend for **htsw**: you write Python and running the script
generates an htsw project (an `import.json` plus the `.htsl` action scripts and
`.snbt` items it references) for Hypixel Housing.

Reach for this skill whenever writing or editing pyhtsw code. The bundled
reference below is the source of truth — read the relevant page before relying on
memory, and prefer it over guessing API shapes.

## Key facts

- Importables are declared at module level or inside `with Container():`.
  Functions/events use decorators (`@create_function`, `@create_event`); items,
  regions, menus and NPCs are classes whose constructor options are class keyword
  arguments, with `@Item.right_click` / `on_right_click=` style handlers.
- Items are referenced from actions by the class (declared, by name) or by an
  `Item(...)` instance (cosmetic, by `.snbt` path); never a raw string. htsw
  generates interaction keys automatically.
- Menus: `class M(Menu, size=...)` (size is `Literal[1..6]` rows, 9 columns);
  `@Menu.element(item=, x=row, y=col, xy_check=)`, negatives allowed.
- Location actions take a `Location` (`Location.custom/house_spawn/invokers/current`).
- Running a script exports a project folder into the htsw projects folder.
- Importables register at **import time**, so a multi-file project's `main.py`
  must import every feature module; `@create_function`/`@create_event` bodies run
  lazily at export, so cross-module references resolve regardless of import order.
  Beyond a one-off script, follow [project-structure](reference/project-structure.md)
  and validate the build with `htsw check` (see [exporting](reference/exporting.md)).

## Reference

{chr(10).join(toc)}
{htsw}"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate the pyhtsw-development skill.',
    )
    parser.add_argument('skills_dir', type=Path, help='Claude Code skills directory')
    args = parser.parse_args()

    if not DOCS.is_dir():
        raise SystemExit(f'No docs/ found at {DOCS}; run scripts/sync_docs.py first.')

    skill_dir = args.skills_dir.expanduser().resolve() / SKILL_NAME
    reference = skill_dir / 'reference'
    if reference.exists():
        shutil.rmtree(reference)
    # Copy the docs as the skill's reference material (skip mdBook-only files).
    shutil.copytree(
        DOCS,
        reference,
        ignore=shutil.ignore_patterns('book.toml', 'SUMMARY.md'),
    )

    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / 'SKILL.md').write_text(render_body(reference) + '\n', encoding='utf-8')

    print(f'Wrote {skill_dir / "SKILL.md"}')
    print(f'  reference files: {sum(1 for _ in reference.rglob("*") if _.is_file())}')


if __name__ == '__main__':
    main()
