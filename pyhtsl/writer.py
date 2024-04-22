import os
from pathlib import Path
import atexit
import sys
import re
from enum import Enum, auto

from types import TracebackType
from typing import Optional, Callable


__all__ = (
    'HERE',
    'HTSL_IMPORTS_FOLDER',
    'LineType',
    'WRITER',
)


HERE: Path = Path(__file__).parent

DOT_MINECRAFT: Path = Path(os.getenv('APPDATA')) / '.minecraft'  # type: ignore
if not DOT_MINECRAFT.exists():
    raise FileNotFoundError('Could not find your .minecraft folder')

HTSL_IMPORTS_FOLDER: Path = DOT_MINECRAFT / 'config' / 'ChatTriggers' / 'modules' / 'HTSL' / 'imports'
if not HTSL_IMPORTS_FOLDER.exists():
    raise FileNotFoundError('Could not find your HTSL imports folder')

PYHTSL_FOLDER: Path = HTSL_IMPORTS_FOLDER / 'pyhtsl'
if not PYHTSL_FOLDER.exists():
    PYHTSL_FOLDER.mkdir()


class LineType(Enum):
    player_stat_change = auto()
    global_stat_change = auto()
    team_stat_change = auto()
    if_and_enter = auto()
    if_or_enter = auto()
    if_exit = auto()
    else_enter = auto()
    else_exit = auto()
    trigger_function = auto()
    exit_function = auto()
    cancel_event = auto()
    miscellaneous = auto()
    goto = auto()


class Fixer:
    stat_limit: int = 10
    conditional_limit: int = 15
    def new_counter(self) -> dict[LineType, int]:
        return {line_type: 0 for line_type in LineType}

    def conditional_enter_count(self, counter: dict[LineType, int]) -> int:
        return counter[LineType.if_and_enter] + counter[LineType.if_or_enter]

    def fix(self, lines: list[tuple[str, LineType]]) -> None:
        container_name: Optional[str] = None
        inside_conditional: bool = False
        outside_counter: dict[LineType, int] = self.new_counter()
        inside_counter: dict[LineType, int] = self.new_counter()

        # \x1b[38;2;0;255;0mNote:\x1b[0m
        # \x1b[38;2;255;0;0mWarning:\x1b[0m


        for index, (line, line_type) in enumerate(lines):
            if line_type is LineType.goto:
                if inside_conditional:
                    raise ValueError('Cannot use goto inside an if or else statement')
                match = re.search(r'"(.+?)"$', line)
                if match is None:
                    raise ValueError(f'Invalid goto line: {line}')
                container_name = match.group(1)
                outside_counter = self.new_counter()
                continue

            counter = inside_counter if inside_conditional else outside_counter
            counter[line_type] += 1

            if line_type in (
                LineType.if_exit,
                LineType.else_exit,
            ):
                if not inside_conditional:
                    raise ValueError('Cannot exit an if statement that was never entered')
                inside_conditional = False
                inside_counter = self.new_counter()
                continue

            if line_type in (
                LineType.if_and_enter,
                LineType.if_or_enter,
                LineType.else_enter,
            ):
                if inside_conditional:
                    raise ValueError('Cannot nest if statements')
                inside_conditional = True
                if self.conditional_enter_count(outside_counter) <= self.conditional_limit:
                    continue
                print('new function')
                ...

            if line_type in (
                LineType.player_stat_change,
                LineType.global_stat_change,
                LineType.team_stat_change,
            ):
                if counter[line_type] <= self.stat_limit:
                    continue
                print('new empty conditional')
                ...


class Writer:
    lines: list[tuple[str, LineType]] = []
    exception_raised: bool = False
    registered_functions: list[Callable[[], None]] = []
    in_front_index: int = 0
    file_name: str
    htsl_file: Path
    python_save_file: Path
    def write(
        self,
        line: str,
        line_type: LineType,
        *,
        append_to_previous_line: bool = False,
        add_to_front: bool = False,
    ) -> None:
        if append_to_previous_line:
            assert not add_to_front
            self.lines[-1] = (self.lines[-1][0] + ' ' + line, line_type)
        else:
            if add_to_front:
                self.lines.insert(self.in_front_index, (line, line_type))
                self.in_front_index += 1
            else:
                self.lines.append((line, line_type))

    def fix_lines(self) -> None:
        ...

    def write_to_files(self) -> None:
        self.file_name = os.path.basename(sys.argv[0]).rsplit('.', 1)[0]

        self.htsl_file = HTSL_IMPORTS_FOLDER / f'{self.file_name}.htsl'
        self.htsl_file.write_text(
            '// Generated with PyHTSL https://github.com/69Jesse/PyHTSL\n'
            + '\n'.join((line for line, _ in self.lines))
        )
        if len(sys.argv) > 1 and sys.argv[1] == 'code':
            os.system(f'code "{self.htsl_file.absolute()}"')

        self.python_save_file = PYHTSL_FOLDER / f'{self.file_name}.py'
        index: int = 1
        while self.python_save_file.exists():
            index += 1
            self.python_save_file = PYHTSL_FOLDER / f'{self.file_name}_{index}.py'
        self.python_save_file.write_text(Path(sys.argv[0]).read_text())

    def exception_hook(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: Optional[TracebackType],
    ) -> None:
        self.exception_raised = True
        sys.__excepthook__(exc_type, exc_value, traceback)

    def on_program_exit(self) -> None:
        if self.exception_raised:
            return
        for func in self.registered_functions:
            func()
        Fixer().fix(self.lines)
        self.write_to_files()
        print((
            '\n\x1b[38;2;0;255;0mAll done! Your .htsl file is written to the following location:\x1b[0m'
            f'\n{self.htsl_file.absolute()}'
            f'\nExecute it with HTSL by using the following name: \x1b[38;2;255;0;0m{self.file_name}\x1b[0m'
            '\n'
        ))


WRITER = Writer()
sys.excepthook = WRITER.exception_hook
atexit.register(WRITER.on_program_exit)
