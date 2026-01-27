from ..writer import HTSL_IMPORTS_FOLDER


__all__ = ('delete_all_items_from_imports_folder',)


def delete_all_items_from_imports_folder() -> None:
    for path in HTSL_IMPORTS_FOLDER.iterdir():
        if not path.is_file():
            continue
        if not path.suffix == '.json':
            continue
        if not path.name.startswith('_'):
            continue
        path.unlink()
        print(
            'Found and \033[38;2;255;0;0mdeleted\033[0m the following \033[38;2;255;0;0m.json file\033[0m:'
            f'\n  \033[38;2;255;0;0m-\033[0m {path.absolute()}'
        )
