import os
from pathlib import Path

from .utils.log import log

__all__ = (
    'set_projects_folder',
    'get_projects_folder',
    'disable_global_export',
    'should_disable_global_export',
    'display_htsl',
    'should_display_htsl',
    'set_project_name',
    'get_project_name',
)


HERE: Path = Path(__file__).parent
CACHED_PROJECTS_FOLDER_PATH: Path = HERE / 'cached_projects_folder.txt'

INDENT: str = ' ' * 4


def _default_projects_folder() -> Path | None:
    if os.name == 'nt':
        return Path(os.getenv('APPDATA') or '') / '.minecraft' / 'htsw' / 'projects'
    if os.name == 'posix':
        return (
            Path.home()
            / 'Library'
            / 'Application Support'
            / 'minecraft'
            / 'htsw'
            / 'projects'
        )
    return None


_PROJECTS_FOLDER_OVERRIDE: Path | None = None


def set_projects_folder(folder: Path | str, *, save: bool = True) -> None:
    if isinstance(folder, str):
        folder = Path(folder)
    folder = folder.resolve()
    folder.mkdir(parents=True, exist_ok=True)

    global _PROJECTS_FOLDER_OVERRIDE
    _PROJECTS_FOLDER_OVERRIDE = folder

    if not save:
        return

    new_content = folder.as_posix()
    content = (
        CACHED_PROJECTS_FOLDER_PATH.read_text()
        if CACHED_PROJECTS_FOLDER_PATH.exists()
        else None
    )
    if content == new_content:
        return
    CACHED_PROJECTS_FOLDER_PATH.write_text(new_content)
    log(
        f'\nSaved your HTSW projects folder \x1b[38;2;0;255;0m{folder.as_posix()}\x1b[0m for future use at\n\x1b[38;2;0;255;0m{CACHED_PROJECTS_FOLDER_PATH}\x1b[0m',
    )


def get_projects_folder() -> Path:
    if _PROJECTS_FOLDER_OVERRIDE is not None:
        return _PROJECTS_FOLDER_OVERRIDE
    if CACHED_PROJECTS_FOLDER_PATH.exists():
        raw_path = CACHED_PROJECTS_FOLDER_PATH.read_text().strip()
        if raw_path:
            return Path(raw_path)

    default = _default_projects_folder()
    if default is not None:
        default = default.resolve()
        default.mkdir(parents=True, exist_ok=True)
        set_projects_folder(default)
        return default

    log('\x1b[38;2;255;0;0mCould not determine your HTSW projects folder.\x1b[0m')
    while True:
        log(
            'Please enter the path to your \x1b[38;2;0;255;0mHTSW projects folder\x1b[0m (relative or absolute): ',
            end='',
        )
        raw_path = input().strip()
        if not raw_path:
            log('\x1b[38;2;255;0;0mPlease provide a valid path.\x1b[0m')
            continue
        set_projects_folder(raw_path)
        return Path(raw_path).resolve()


DISABLE_GLOBAL_EXPORT: bool = False


def disable_global_export(value: bool = True) -> None:
    global DISABLE_GLOBAL_EXPORT
    DISABLE_GLOBAL_EXPORT = value


def should_disable_global_export() -> bool:
    return DISABLE_GLOBAL_EXPORT


DISPLAY_HTSL: bool = False


def display_htsl(value: bool = True) -> None:
    global DISPLAY_HTSL
    DISPLAY_HTSL = value


def should_display_htsl() -> bool:
    return DISPLAY_HTSL


PROJECT_NAME: str | None = None


def set_project_name(name: str) -> None:
    """Name the global export. Call this once (e.g. in main.py); the program's
    global container is then exported under this name instead of the script's
    filename."""
    global PROJECT_NAME
    PROJECT_NAME = name


def get_project_name() -> str | None:
    return PROJECT_NAME
