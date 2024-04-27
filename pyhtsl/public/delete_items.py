from ..writer import HTSL_IMPORTS_FOLDER


__all__ = (
    'delete_all_items_from_imports_folder',
)


def delete_all_items_from_imports_folder() -> None:
    for path in HTSL_IMPORTS_FOLDER.iterdir():
        if not path.is_file():
            continue
        if not path.suffix == '.json':
            continue
        if not path.name.startswith('_'):
            continue
        path.unlink()
        print(f'Deleted "{path.absolute()}"')
