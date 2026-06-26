"""Lay a container's importables out as nested htsw projects, one folder per
Python module, mirroring the package tree.

Each node's `import.json` `include`s its children (so the root reaches the whole
tree) plus the other modules its actions reference (so a subtree still resolves
when imported on its own). The package tree is acyclic, so cross-reference edges
are the only thing that can form an htsw include cycle; they are added greedily
and any that would close a cycle is dropped with a warning (the reference still
resolves through the root, where containment already pulls every module in).
"""

import json
import posixpath
from collections.abc import Generator
from typing import TYPE_CHECKING

from .importable import Project, build_import_json, module_to_folder
from .utils.log import log

if TYPE_CHECKING:
    from .block import Block
    from .expression.expression import Expression
    from .importable import Importable


class _Node:
    def __init__(self, dotted: str) -> None:
        self.dotted = dotted  # '' is the project root (entry script / __main__)
        self.importables: list[Importable] = []
        self.children: dict[str, _Node] = {}
        self.folder = module_to_folder(dotted or None)

    @property
    def import_json_relpath(self) -> str:
        return (
            posixpath.join(self.folder, 'import.json') if self.folder else 'import.json'
        )


def _module_key_to_node(module: str | None, prefix: tuple[str, ...]) -> str:
    """Dotted node path for `module` after stripping the shared package prefix.
    The entry script and the common ancestor itself both land at the root ('')."""
    if not module or module == '__main__':
        return ''
    return '.'.join(module.split('.')[len(prefix) :])


def _common_prefix(importables: list['Importable']) -> tuple[str, ...]:
    """Longest shared dotted prefix of the real (non-entry-script) modules, so a
    single-module or single-package export roots at the project root rather than
    nesting under its own package path."""
    paths = [
        imp.module.split('.')
        for imp in importables
        if imp.module and imp.module != '__main__'
    ]
    if not paths:
        return ()
    prefix = paths[0]
    for path in paths[1:]:
        cut = 0
        while cut < len(prefix) and cut < len(path) and prefix[cut] == path[cut]:
            cut += 1
        prefix = prefix[:cut]
    return tuple(prefix)


def _build_tree(importables: list['Importable']) -> dict[str, _Node]:
    nodes: dict[str, _Node] = {'': _Node('')}
    prefix = _common_prefix(importables)

    def get_node(dotted: str) -> _Node:
        existing = nodes.get(dotted)
        if existing is not None:
            return existing
        node = _Node(dotted)
        nodes[dotted] = node
        parts = dotted.split('.')
        parent = get_node('.'.join(parts[:-1])) if len(parts) > 1 else nodes['']
        parent.children[parts[-1]] = node
        return node

    for importable in importables:
        dotted = _module_key_to_node(importable.module, prefix)
        target = nodes[''] if not dotted else get_node(dotted)
        target.importables.append(importable)
    return nodes


def _importable_blocks(importable: 'Importable') -> list['Block']:
    blocks: list[Block] = []
    for attr in ('block', 'left', 'right', 'on_enter', 'on_exit'):
        block = getattr(importable, attr, None)
        if block is not None:
            blocks.append(block)
    for slot in getattr(importable, 'slots', None) or ():
        if slot.block is not None:
            blocks.append(slot.block)
    return blocks


def _walk(expressions: list['Expression']) -> Generator['Expression']:
    for expression in expressions:
        yield expression
        for nested in expression.nested_expressions_refs():
            yield from _walk(nested)


def _node_targets(
    node: _Node,
    key_to_module: dict[tuple[str, str], str | None],
    nodes: dict[str, _Node],
) -> set[str]:
    """Dotted paths of the nodes whose importables `node`'s actions reference."""
    targets: set[str] = set()
    for importable in node.importables:
        for block in _importable_blocks(importable):
            for expression in _walk(block.expressions):
                for ref in expression.referenced_importables():
                    if ref not in key_to_module:
                        continue
                    target = nodes.get(key_to_module[ref] or '')
                    if target is not None and target is not node:
                        targets.add(target.dotted)
    return targets


def _resolve_includes(
    nodes: dict[str, _Node],
    importables: list['Importable'],
) -> dict[str, list[str]]:
    """For each node, the dotted paths of the cross-reference edges to emit
    (besides its containment children). Greedily skips any edge that would close
    an include cycle."""
    prefix = _common_prefix(importables)
    key_to_module: dict[tuple[str, str], str | None] = {
        (importable.kind, importable.identifier()): _module_key_to_node(
            importable.module,
            prefix,
        )
        for importable in importables
    }
    adjacency: dict[str, set[str]] = {dotted: set() for dotted in nodes}
    for node in nodes.values():
        for child in node.children.values():
            adjacency[node.dotted].add(child.dotted)

    def reaches(start: str, goal: str) -> bool:
        seen = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            if current == goal:
                return True
            for nxt in adjacency[current]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return False

    candidates: list[tuple[str, str]] = []
    for node in nodes.values():
        for target in _node_targets(node, key_to_module, nodes):
            candidates.append((node.dotted, target))

    cross: dict[str, list[str]] = {dotted: [] for dotted in nodes}
    for source, target in sorted(candidates):
        if reaches(source, target):
            continue  # already pulled in via containment or an earlier edge
        if reaches(target, source):
            log(
                f'\x1b[38;2;255;191;0mSkipping cross-module include '
                f'{source or "<root>"} -> {target} (would create an import.json '
                f'cycle); it still resolves through the root.\x1b[0m',
            )
            continue
        adjacency[source].add(target)
        cross[source].append(target)
    return cross


def export_project(project: Project, importables: list['Importable']) -> None:
    nodes = _build_tree(importables)
    cross = _resolve_includes(nodes, importables)

    # Items are placed in their owning module's folder; apply the same shared
    # prefix stripping the tree used so cross-node .snbt paths line up.
    prefix = _common_prefix(importables)
    project.module_folder = lambda module: module_to_folder(
        _module_key_to_node(module, prefix),
    )

    for node in nodes.values():
        project.node_folder = node.folder
        start = node.folder or '.'

        includes: list[str] = []
        for child in sorted(node.children.values(), key=lambda c: c.folder):
            includes.append(posixpath.relpath(child.import_json_relpath, start))
        for target in cross[node.dotted]:
            includes.append(
                posixpath.relpath(nodes[target].import_json_relpath, start),
            )

        data = build_import_json(project, node.importables)
        if includes:
            data = {'include': includes, **data}
        project.write(node.import_json_relpath, json.dumps(data, indent=2) + '\n')

    project.node_folder = ''
