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

    container_name: Optional[str]
    container_index: int
    inside_conditional: bool
    inside_empty_conditional: bool
    outside_counter: dict[LineType, int]
    inside_counter: dict[LineType, int]
    def __init__(self) -> None:
        self.container_name = None
        self.container_index = 1
        self.inside_conditional = False
        self.inside_empty_conditional = False
        self.outside_counter = self.new_counter()
        self.inside_counter = self.new_counter()

    def new_counter(self) -> dict[LineType, int]:
        return {line_type: 0 for line_type in LineType}

    @property
    def contional_statements_count(self) -> int:
        return self.outside_counter[LineType.if_and_enter] + self.outside_counter[LineType.if_or_enter]

    def call_next_container(
        self,
        lines: list[tuple[str, LineType]],
        index: int,
    ) -> int:
        if self.container_name is None:
            print(
                '\x1b[38;2;255;0;0mWarning:\x1b[0m You exceeded the conditional limit, and you are not in an explicit container.'
                '\n         To prevent this, use the \x1b[38;2;255;0;0m@create_function()\x1b[0m decorator or the \x1b[38;2;255;0;0mgoto()\x1b[0m function.'
            )
            return index
        self.container_index += 1
        new_container_name = f'{self.container_name} {self.container_index}'
        lines.insert(index - 1, (f'goto function "{new_container_name}"', LineType.goto))
        self.outside_counter = self.new_counter()
        index += 1
        print(f'\x1b[38;2;0;255;0mNote:\x1b[0m Created a new container named "\x1b[38;2;255;0;0m{new_container_name}\x1b[0m" to prevent too many stat changes.')
        return index

    def create_empty_conditional(
        self,
        lines: list[tuple[str, LineType]],
        index: int,
    ) -> int:
        if not self.inside_empty_conditional:
            lines.insert(index, ('if and () {', LineType.if_and_enter))
            self.outside_counter[LineType.if_and_enter] += 1
            self.inside_empty_conditional = True
            self.inside_conditional = True
            self.inside_counter = self.new_counter()
            line_type = lines[index][1]
            self.inside_counter[line_type] += 1
            print('\x1b[38;2;0;255;0mNote:\x1b[0m Added an empty conditional to prevent too many stat changes.')
        else:
            lines.insert(index - 1, ('}', LineType.if_exit))
            self.inside_empty_conditional = False
            self.inside_conditional = False
            return self.create_empty_conditional(lines, index)
        index += 1
        return index

    def maybe_exit_empty_conditional(
        self,
        lines: list[tuple[str, LineType]],
        index: int,
        add: int,
    ) -> int:
        if self.inside_empty_conditional:
            lines.insert(index + add, ('}', LineType.if_exit))
            index += 1
            self.inside_empty_conditional = False
            self.inside_conditional = False
            return index
        return index

    def check_conditional_limit(
        self,
        lines: list[tuple[str, LineType]],
        index: int,
    ) -> int:
        if self.contional_statements_count > self.conditional_limit:
            index = self.call_next_container(lines, index)
        return index

    def fix(self, lines: list[tuple[str, LineType]]) -> None:
        # TODO DIFFERENT APPROACH
        # mark indixes of where to add
        index: int = -1
        while index < len(lines) - 1:
            index += 1
            line, line_type = lines[index]
            if line_type is LineType.goto:
                if self.inside_conditional and not self.inside_empty_conditional:
                    raise ValueError('Cannot use goto inside an if or else statement')
                match = re.search(r'"(.+?)"$', line)
                if match is None:
                    raise ValueError(f'Invalid goto line: {line}')
                self.maybe_exit_empty_conditional(lines, index, 0)
                self.container_name = match.group(1)
                self.outside_counter = self.new_counter()
                self.container_index = 1
                continue

            counter = self.inside_counter if self.inside_conditional else self.outside_counter
            counter[line_type] += 1

            if line_type in (LineType.if_and_enter, LineType.if_or_enter, LineType.else_enter):
                if self.inside_conditional:
                    raise ValueError('Cannot nest if statements')
                index = self.check_conditional_limit(lines, index)
                self.inside_conditional = True
                continue

            if line_type in (LineType.if_exit, LineType.else_exit):
                if not self.inside_conditional:
                    print('\n'.join((line for line, _ in lines)))
                    raise ValueError('Cannot exit an if statement that was never entered')
                self.inside_conditional = False
                self.inside_counter = self.new_counter()
                continue

            if line_type in (LineType.player_stat_change, LineType.global_stat_change, LineType.team_stat_change):
                if counter[line_type] > self.stat_limit:
                    if self.contional_statements_count >= self.conditional_limit:
                        index = self.maybe_exit_empty_conditional(lines, index, -1)
                        index = self.call_next_container(lines, index)
                        index -= 2
                    else:
                        index = self.create_empty_conditional(lines, index)
                    continue

        self.maybe_exit_empty_conditional(lines, index, 1)
        if self.inside_conditional:
            raise ValueError('Unclosed if statement')


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
