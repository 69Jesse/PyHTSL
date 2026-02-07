import os
from pathlib import Path


__all__ = (
    'set_htsl_imports_folder',
    'get_htsl_import_folder',
    'disable_global_export',
    'display_htsl',
)


HERE: Path = Path(__file__).parent
CACHED_HTSL_IMPORTS_FOLDER_PATH: Path = HERE / 'cached_htsl_imports_folder.txt'

INDENT: str = ' ' * 4

DISABLE_GLOBAL_EXPORT: bool = False

DISPLAY_HTSL: bool = False


def set_htsl_imports_folder(htsl_folder: Path | str) -> None:
    if isinstance(htsl_folder, str):
        htsl_folder = Path(htsl_folder)
    if not htsl_folder.is_dir():
        raise NotADirectoryError('The provided HTSL imports folder is not a directory.')
    if not htsl_folder.exists():
        raise FileNotFoundError('The provided HTSL imports folder does not exist.')
    content = (
        CACHED_HTSL_IMPORTS_FOLDER_PATH.read_text()
        if CACHED_HTSL_IMPORTS_FOLDER_PATH.exists()
        else None
    )
    new_content = htsl_folder.resolve().as_posix()
    if content is not None and content == new_content:
        return
    CACHED_HTSL_IMPORTS_FOLDER_PATH.write_text(new_content)

    print(
        f'\nSaved your HTSL imports folder \x1b[38;2;0;255;0m{htsl_folder.as_posix()}\x1b[0m for future use at\n\x1b[38;2;0;255;0m{CACHED_HTSL_IMPORTS_FOLDER_PATH}\x1b[0m'
    )


def get_htsl_import_folder() -> Path:
    maybe_path: Path | None = None
    if CACHED_HTSL_IMPORTS_FOLDER_PATH.exists():
        raw_path = CACHED_HTSL_IMPORTS_FOLDER_PATH.read_text().strip()
        if raw_path:
            maybe_path = Path(raw_path)
    elif os.name == 'nt':
        maybe_path = (
            Path(os.getenv('APPDATA') or '')
            / '.minecraft'
            / 'config'
            / 'ChatTriggers'
            / 'modules'
            / 'HTSL'
            / 'imports'
        )
    elif os.name == 'posix':
        maybe_path = (
            Path.home()
            / 'Library'
            / 'Application Support'
            / 'minecraft'
            / 'config'
            / 'ChatTriggers'
            / 'modules'
            / 'HTSL'
            / 'imports'
        )

    if maybe_path is not None:
        maybe_path = maybe_path.resolve()
        if maybe_path.exists():
            set_htsl_imports_folder(maybe_path)
            return maybe_path

    print('\x1b[38;2;255;0;0mCould not find your HTSL imports folder.\x1b[0m')
    while True:
        raw_path = input(
            'Please enter the path to your \x1b[38;2;0;255;0mHTSL imports folder\x1b[0m (relative or absolute): '
        ).strip()
        if not raw_path:
            print('\x1b[38;2;255;0;0mPlease provide a valid path.\x1b[0m')
            continue
        maybe_path = Path(raw_path).resolve()
        try:
            set_htsl_imports_folder(maybe_path)
            return maybe_path
        except (FileNotFoundError, NotADirectoryError) as e:
            print(f'\x1b[38;2;255;0;0m{e.__class__.__name__}: {e}\x1b[0m')
            continue


def disable_global_export(value: bool = True) -> None:
    global DISABLE_GLOBAL_EXPORT
    DISABLE_GLOBAL_EXPORT = value


def display_htsl(value: bool = True) -> None:
    global DISPLAY_HTSL
    DISPLAY_HTSL = value
