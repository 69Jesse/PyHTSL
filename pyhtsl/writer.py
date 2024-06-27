import os
from pathlib import Path
import atexit
import sys
from .line_type import LineType
from .fixer import Fixer

from types import TracebackType
from typing import Optional, Callable


__all__ = (
    'HERE',
    'HTSL_IMPORTS_FOLDER',
    'WRITER',
)


HERE: Path = Path(__file__).parent

if os.name == 'nt':
    DOT_MINECRAFT: Path = Path(os.getenv('APPDATA')) / '.minecraft'  # type: ignore
elif os.name == 'posix':
    DOT_MINECRAFT: Path = Path.home() / 'Library' / 'Application Support' / 'minecraft'
else:
    raise OSError('Unsupported operating system')
if not DOT_MINECRAFT.exists():
    raise FileNotFoundError('Could not find your minecraft folder')

HTSL_IMPORTS_FOLDER: Path = DOT_MINECRAFT / 'config' / 'ChatTriggers' / 'modules' / 'HTSL' / 'imports'
if not HTSL_IMPORTS_FOLDER.exists():
    raise FileNotFoundError('Could not find your HTSL imports folder')

PYHTSL_FOLDER: Path = HTSL_IMPORTS_FOLDER / 'pyhtsl'
if not PYHTSL_FOLDER.exists():
    PYHTSL_FOLDER.mkdir()


# class Fixer:
#     stat_limit: int = 10
#     conditional_limit: int = 15

#     last_line: Optional[str]
#     last_line_count: int

#     insertions: dict[int, list[tuple[str, LineType]]]
#     pops: set[int]
#     container_name: Optional[str]
#     container_index: int
#     inside_conditional: bool
#     inside_filler_conditional: bool
#     inside_filler_goto_inside_conditional: bool
#     outside_counter: dict[LineType, int]
#     inside_counter: dict[LineType, int]
#     old_outside_counter: dict[LineType, int]

#     def maybe_change_lines_edge_cases(
#         self,
#         lines: list[tuple[str, LineType]],
#     ) -> None:
#         for index in range(len(lines) - 1, -1, -1):
#             line, line_type = lines[index]
#             if line_type is LineType.misc_stat_change and line.startswith('maxHealth'):
#                 try:
#                     next_line, next_line_type = lines[index + 1]
#                     if next_line_type is not LineType.miscellaneous or next_line != 'fullHeal':
#                         raise IndexError
#                     lines[index] = (line + ' true', line_type)
#                     lines.pop(index + 1)
#                 except IndexError:
#                     lines[index] = (line + ' false', line_type)

#     def new_counter(self) -> dict[LineType, int]:
#         return {line_type: 0 for line_type in LineType}

#     def conditional_enter_count(self, counter: dict[LineType, int]) -> int:
#         return counter[LineType.if_and_enter] + counter[LineType.if_or_enter]

#     def write_debug_line(self, line: str) -> None:
#         if self.last_line is not None and self.last_line != line:
#             print(f' \x1b[38;2;255;0;0m(x{self.last_line_count})\x1b[0m' * (self.last_line_count > 1))
#         if self.last_line == line:
#             self.last_line_count += 1
#             return
#         self.last_line = line
#         self.last_line_count = 1
#         print(line, end='')

#     def on_goto_container_line(
#         self,
#         index: int,
#         line: str,
#     ) -> None:
#         if self.inside_conditional and not self.inside_filler_conditional:
#             raise ValueError('Cannot use goto inside an if or else statement')
#         if self.inside_filler_conditional:
#             self.insertions.setdefault(index, []).append((
#                 '}',
#                 LineType.if_exit,
#             ))
#         match = re.search(r'"(.+?)"$', line)
#         if match is None:
#             raise ValueError(f'Invalid goto line: {line}')
#         self.container_name = match.group(1)
#         self.container_index = 1
#         self.reset_most_attributes()

#     def on_conditional_enter_line(
#         self,
#         index: int,
#         line_type: LineType,
#     ) -> None:
#         if self.inside_conditional and line_type is not LineType.else_enter:
#             raise ValueError('Cannot nest if statements')
#         self.inside_conditional = True
#         if self.conditional_enter_count(self.outside_counter) <= self.conditional_limit:
#             return
#         self.create_filler_goto_function(index=index, line_type=line_type)

#     def on_conditional_exit_line(
#         self,
#         index: int,
#     ) -> None:
#         if self.inside_filler_goto_inside_conditional:
#             self.inside_conditional = False
#             self.inside_filler_conditional = False
#             self.inside_filler_goto_inside_conditional = False
#             self.outside_counter = self.old_outside_counter
#             return
#         if not self.inside_conditional:
#             raise ValueError('Cannot exit an if statement that was never entered')
#         self.inside_conditional = False
#         self.inside_counter = self.new_counter()

#     def on_stat_change_line(
#         self,
#         index: int,
#         line_type: LineType,
#         counter: dict[LineType, int],
#     ) -> None:
#         if counter[line_type] <= self.stat_limit:
#             return
#         if self.inside_filler_conditional:
#             self.insertions.setdefault(index, []).append((
#                 '}',
#                 LineType.if_exit,
#             ))
#             self.inside_counter = self.new_counter()
#             self.inside_conditional = False
#             self.inside_filler_conditional = False
#         if self.inside_conditional:
#             return self.create_filler_goto_inside_conditional(index=index, line_type=line_type)
#         if self.conditional_enter_count(self.outside_counter) >= self.conditional_limit:
#             self.create_filler_goto_function(index=index, line_type=line_type)
#         else:
#             self.create_filler_conditional(index=index, line_type=line_type)

#     def create_filler_conditional(
#         self,
#         index: int,
#         line_type: LineType,
#     ) -> None:
#         if self.inside_conditional:
#             return self.create_filler_goto_inside_conditional(index=index, line_type=line_type)
#         self.insertions.setdefault(index, []).append((
#             'if and () {  // PyHTSL filler',
#             LineType.if_and_enter,
#         ))
#         self.outside_counter[LineType.if_and_enter] += 1
#         self.inside_counter = self.new_counter()
#         self.inside_counter[line_type] += 1
#         self.inside_conditional = True
#         self.inside_filler_conditional = True
#         self.write_debug_line('\x1b[38;2;0;255;0mNote:\x1b[0m Added a conditional to prevent too many stat changes.')

#     def create_filler_goto_function(
#         self,
#         index: int,
#         line_type: LineType,
#     ) -> None:
#         if self.inside_filler_conditional:
#             raise ValueError('That should not have happened..')
#         if self.inside_conditional and not self.inside_filler_goto_inside_conditional:
#             return self.create_filler_goto_inside_conditional(index=index, line_type=line_type)
#         self.container_index += 1
#         if self.container_name is not None:
#             new_container_name = f'{self.container_name} {self.container_index}'
#             self.insertions.setdefault(index, []).append((
#                 f'function "{new_container_name}"  // PyHTSL filler',
#                 LineType.trigger_function,
#             ))
#             for i, lt in (
#                 (0, LineType.goto),
#                 (index, LineType.goto_move_to_end if self.inside_filler_goto_inside_conditional else LineType.goto),
#             ):
#                 self.insertions.setdefault(i, []).append((
#                     f'goto function "{new_container_name}"  // PyHTSL filler',
#                     lt,
#                 ))
#             self.write_debug_line(f'\x1b[38;2;0;255;0mNote:\x1b[0m Created a new function named "\x1b[38;2;255;0;0m{new_container_name}\x1b[0m" to prevent too many stat changes.')
#         else:
#             new_container_name = 'Unknown Function'
#             self.insertions.setdefault(index, []).append((
#                 f'// function "{new_container_name} {self.container_index}"       // PyHTSL filler, uncomment and change name',
#                 LineType.trigger_function,
#             ))
#             for i, lt in (
#                 (0, LineType.goto),
#                 (index, LineType.goto_move_to_end if self.inside_filler_goto_inside_conditional else LineType.goto),
#             ):
#                 self.insertions.setdefault(i, []).append((
#                     f'// goto function "{new_container_name} {self.container_index}"  // PyHTSL fille, uncomment and change name',
#                     lt,
#                 ))
#             self.write_debug_line(
#                 '\x1b[38;2;255;0;0mWarning:\x1b[0m You exceeded the conditional limit, and you are not in an explicit container.'
#                 '\n         To prevent this, use the \x1b[38;2;255;0;0m@create_function()\x1b[0m decorator or the \x1b[38;2;255;0;0mgoto()\x1b[0m function.'
#                 '\n         Or uncomment the line I created for you and change the name of the function.'
#             )
#         self.outside_counter = self.new_counter()
#         if not self.inside_filler_goto_inside_conditional:
#             self.outside_counter[line_type] += 1

#     def create_filler_goto_inside_conditional(
#         self,
#         index: int,
#         line_type: LineType,
#     ) -> None:
#         assert self.inside_conditional
#         assert not self.inside_filler_conditional
#         self.old_outside_counter = self.outside_counter
#         before_inside_filler = self.inside_filler_goto_inside_conditional
#         self.inside_filler_goto_inside_conditional = True
#         self.create_filler_goto_function(index=index, line_type=line_type)
#         if not before_inside_filler:
#             self.insertions[index].insert(1, (
#                 '}',
#                 LineType.if_exit,
#             ))
#         self.inside_counter = self.new_counter()
#         self.inside_counter[line_type] += 1

#     def reset_most_attributes(self) -> None:
#         self.inside_conditional = False
#         self.inside_filler_conditional = False
#         self.inside_filler_goto_inside_conditional = False
#         self.outside_counter = self.new_counter()
#         self.inside_counter = self.new_counter()

#     def fix(self, lines: list[tuple[str, LineType]]) -> None:
#         """I'm so sorry"""
#         self.maybe_change_lines_edge_cases(lines)        

#         self.last_line = None
#         self.last_line_count = 0
#         self.insertions = {}
#         self.pops = set()
#         self.container_name = None
#         self.container_index = 1
#         self.reset_most_attributes()

#         for index, (line, line_type) in enumerate(lines):
#             if line_type is LineType.goto:
#                 self.on_goto_container_line(index=index, line=line)
#                 continue

#             counter = self.inside_counter if self.inside_conditional else self.outside_counter
#             counter[line_type] += 1

#             if line_type in (
#                 LineType.if_exit,
#                 LineType.else_exit,
#             ):
#                 self.on_conditional_exit_line(index=index)
#                 continue
#             if line_type in (
#                 LineType.if_and_enter,
#                 LineType.if_or_enter,
#                 LineType.else_enter,
#             ):
#                 self.on_conditional_enter_line(index=index, line_type=line_type)
#                 continue
#             if line_type in (
#                 LineType.player_stat_change,
#                 LineType.global_stat_change,
#                 LineType.team_stat_change,
#             ):
#                 self.on_stat_change_line(index=index, line_type=line_type, counter=counter)
#                 continue

#         self.write_debug_line('')

#         for i in range(len(lines) - 1, -1, -1):
#             if i in self.pops:
#                 lines.pop(i)
#             insertions = self.insertions.get(i, None)
#             if insertions is None:
#                 continue
#             for insertion in reversed(insertions):
#                 lines.insert(i, insertion)

#         if len(self.insertions) > 0 and self.insertions[max(self.insertions.keys())][-1][1] is LineType.if_and_enter:
#             lines.append(('}', LineType.if_exit))

#         move_to_end: set[int] = set()
#         pop: set[int] = set()
#         flag: bool = False
#         for index, (line, line_type) in enumerate(lines):
#             if line_type is LineType.goto_move_to_end:
#                 flag = True
#             if flag:
#                 pop.add(index)
#                 if line_type is LineType.if_exit:
#                     flag = False
#                     continue
#                 move_to_end.add(index)
        
#         end: list[tuple[str, LineType]] = []
#         assert move_to_end.issubset(pop)
#         for index in sorted(pop, reverse=True):
#             entry = lines.pop(index)
#             if index in move_to_end:
#                 end.insert(0, entry)
#         lines.extend(end)


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

    def write_to_files(self) -> bool:
        if not self.lines:
            print('Nothing found to write to your .htsl file. \x1b[38;2;255;0;0mPyHTSL will not do anything.\x1b[0m')
            return False

        self.file_name = os.path.basename(sys.argv[0]).rsplit('.', 1)[0]

        args: list[str] = sys.argv[1:]
        if 'lines' in args and self.lines:
            max_line_length: int = max(len(line) for line, _ in self.lines)
            content = '\n'.join(
                f'{line.ljust(max_line_length)}  // {line_type}'
                for line, line_type in self.lines
            )
        else:
            content = '\n'.join((line for line, _ in self.lines))

        encoding: str = 'utf-8'
        self.htsl_file = HTSL_IMPORTS_FOLDER / f'{self.file_name}.htsl'
        self.htsl_file.write_text(
            f'// Generated with PyHTSL https://github.com/69Jesse/PyHTSL\n{content}',
            encoding=encoding,
        )
        if 'code' in args:
            os.system(f'code "{self.htsl_file.absolute()}"')

        self.python_save_file = PYHTSL_FOLDER / f'{self.file_name}.py'
        index: int = 1
        while self.python_save_file.exists():
            index += 1
            self.python_save_file = PYHTSL_FOLDER / f'{self.file_name}_{index}.py'
        self.python_save_file.write_text(Path(sys.argv[0]).read_text(encoding=encoding), encoding=encoding)

        return True

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

        fixer = Fixer(self.lines)
        fixer.fix()

        if not self.write_to_files():
            return
        print((
            '\n\x1b[38;2;0;255;0mAll done! Your .htsl file is written to the following location:\x1b[0m'
            f'\n{self.htsl_file.absolute()}'
            f'\nExecute it with HTSL by using the following name: \x1b[38;2;255;0;0m{self.file_name}\x1b[0m'
            '\n'
        ))


WRITER = Writer()
sys.excepthook = WRITER.exception_hook
atexit.register(WRITER.on_program_exit)
