from abc import ABC, abstractmethod
import re

from .line_type import LineType

from typing import TYPE_CHECKING, Generator, final

if TYPE_CHECKING:
    from .writer import ExportContainer


__all__ = ('Fixer',)


GOTO_LINE_REGEX = re.compile(r'^goto (.+?) "(.+)"')


class Part:
    name: str | None
    lines: list[tuple[str, LineType]]

    def __init__(
        self,
        name: str | None,
        lines: list[tuple[str, LineType]],
    ) -> None:
        self.name = name
        self.lines = lines


class Counter:
    mapping: dict[LineType, int]

    def __init__(self) -> None:
        self.mapping = {}

    def increment(self, line_type: LineType) -> int:
        self.mapping[line_type] = self.mapping.get(line_type, 0) + 1
        return self.mapping[line_type]

    def reset(self) -> None:
        self.mapping.clear()

    def possible_to_increment(
        self,
        line_type: LineType,
    ) -> bool:
        self.increment(line_type)
        possible = not self.limit_reached()
        self.mapping[line_type] -= 1
        return possible

    IF_ENTER_LIMIT: int = 15

    def if_enters(self) -> int:
        return self.mapping.get(LineType.if_and_enter, 0) + self.mapping.get(
            LineType.if_or_enter, 0
        )

    def can_add_another_if_enter(self) -> bool:
        return self.if_enters() < Counter.IF_ENTER_LIMIT

    def add_fake_if_enter(self) -> None:
        self.mapping[LineType.if_and_enter] = (
            self.mapping.get(LineType.if_and_enter, 0) + 1
        )

    def add_fake_function_trigger(self) -> None:
        self.mapping[LineType.trigger_function] = (
            self.mapping.get(LineType.trigger_function, 0) + 1
        )

    def remove_fake_function_trigger(self) -> None:
        self.mapping[LineType.trigger_function] -= 1

    def limit_reached(self) -> bool:
        return (
            self.if_enters() > Counter.IF_ENTER_LIMIT
            or self.mapping.get(LineType.variable_change, 0) > 25
            or self.mapping.get(LineType.display_title, 0) > 5
            or self.mapping.get(LineType.pause_execution, 0) > 30
            # 9 instead of 10 to account for the filler function call if nessessary
            # This results in some tiny inefficiencies in some cases.
            # See [9 INSTEAD OF 10] for a fix in one case. Maybe TODO:
            # fix it fully, but right now I have no clue how to do that.
            or self.mapping.get(LineType.trigger_function, 0) > 9
        )


class Addon(ABC):
    lines: list[tuple[str, LineType]]
    add_to_middle_index: int
    container: 'ExportContainer'

    def __init__(
        self,
        lines: list[tuple[str, LineType]],
        add_to_middle_index: int,
        *,
        container: 'ExportContainer',
    ) -> None:
        self.lines = lines
        self.add_to_middle_index = add_to_middle_index
        self.container = container

    @abstractmethod
    def add_to_middle(self, append_to: list[tuple[str, LineType]]) -> int:
        raise NotImplementedError

    @abstractmethod
    def add_to_end(self, append_to: list[tuple[str, LineType]]) -> None:
        raise NotImplementedError


@final
class EmptyIfAddon(Addon):
    def __init__(
        self,
        lines: list[tuple[str, LineType]],
        add_to_middle_index: int,
        *,
        container: 'ExportContainer',
    ) -> None:
        for i, (line, line_type) in enumerate(lines):
            lines[i] = ('    ' + line, line_type)
        super().__init__(lines, add_to_middle_index, container=container)
        self.container.logger.log(
            '\x1b[38;2;0;255;0mNote:\x1b[0m Added a conditional to prevent too many stat changes.'
        )

    def add_to_middle(self, append_to: list[tuple[str, LineType]]) -> int:
        for line in reversed(
            (
                ('if and () {', LineType.if_and_enter),
                *self.lines,
                ('}', LineType.if_exit),
            )
        ):
            append_to.insert(self.add_to_middle_index, line)
        return len(self.lines) + 2

    def add_to_end(self, append_to: list[tuple[str, LineType]]) -> None:
        pass


FILLER_COMMENT_SUFFIX: str = '  // PyHTSL filler'


@final
class NewFunctionAddon(Addon):
    raw_function_name: str | None
    function_index: int

    def __init__(
        self,
        lines: list[tuple[str, LineType]],
        add_to_middle_index: int,
        function_name: str | None,
        function_index: int,
        *,
        container: 'ExportContainer',
    ) -> None:
        super().__init__(lines, add_to_middle_index, container=container)
        self.raw_function_name = function_name
        self.function_index = function_index
        if not self.has_unknown_name():
            self.container.logger.log(
                f'\x1b[38;2;0;255;0mNote:\x1b[0m Created a new function named "\x1b[38;2;255;0;0m{self.function_name()}\x1b[0m" to prevent too many stat changes.'
            )
        else:
            self.container.logger.log(
                '\x1b[38;2;255;0;0mWarning:\x1b[0m You exceeded the conditional limit, and you are not in an explicit container.'
                '\n         To prevent this, use the \x1b[38;2;255;0;0m@create_function()\x1b[0m decorator or the \x1b[38;2;255;0;0mgoto()\x1b[0m function.'
                f'\n         I created the function with the name "\x1b[38;2;255;0;0m{self.function_name()}\x1b[0m" to prevent any issues.'
            )

    def has_unknown_name(self) -> bool:
        return self.raw_function_name is None

    def function_name(self) -> str:
        return f'{self.raw_function_name if not self.has_unknown_name() else "!!! Rename Me"} {self.function_index}'

    def add_to_middle(self, append_to: list[tuple[str, LineType]]) -> int:
        append_to.insert(
            self.add_to_middle_index,
            (
                f'function "{self.function_name()}" false' + FILLER_COMMENT_SUFFIX,
                LineType.trigger_function,
            ),
        )
        return 1

    def create_goto_line(self) -> tuple[str, LineType]:
        return (
            f'goto function "{self.function_name()}"' + FILLER_COMMENT_SUFFIX,
            LineType.goto,
        )

    def add_to_end(self, append_to: list[tuple[str, LineType]]) -> None:
        append_to.append(self.create_goto_line())
        append_to.extend(self.lines)


class Fixer:
    container: 'ExportContainer'
    lines: list[tuple[str, LineType]]
    new_functions_added: list[NewFunctionAddon]

    def __init__(self, container: 'ExportContainer') -> None:
        self.container = container
        self.lines = container.lines.copy()
        self.new_functions_added = []

    def fix(self) -> list[tuple[str, LineType]]:
        if not self.lines:
            return []

        parts: list[Part] = []
        for part in self.create_parts():
            addons = self.fix_lines(part.lines, current_name=part.name)
            for addon in addons:
                if isinstance(addon, NewFunctionAddon):
                    self.new_functions_added.append(addon)
                addon.add_to_end(part.lines)
            parts.append(part)

        lines: list[tuple[str, LineType]] = []
        for part in parts:
            lines.extend(part.lines)
        for addon in reversed(self.new_functions_added):
            lines.insert(0, addon.create_goto_line())

        try:
            self.fix_goto_order(lines)
        except IndexError:
            return []

        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            if line[1] is not LineType.goto:
                continue
            if i < (len(lines) - 1) and lines[i + 1][1] is LineType.goto:
                continue
            lines[i] = ('\n\n' + line[0], line[1])

        return lines

    def find_container_and_name_from_goto(
        self, line: str
    ) -> tuple[str, str] | tuple[None, None]:
        match = GOTO_LINE_REGEX.match(line)
        if match is None:
            return (None, None)
        return (match.group(1), match.group(2))

    def create_parts(
        self,
        lines: list[tuple[str, LineType]] | None = None,
    ) -> Generator[Part, None, None]:
        if lines is None:
            lines = self.lines
        name: str | None = None
        current_lines: list[tuple[str, LineType]] = []
        for line, line_type in lines:
            if line_type is LineType.goto:
                yield Part(name, current_lines)
                _, name = self.find_container_and_name_from_goto(line)
                current_lines = [(line, line_type)]
                continue
            current_lines.append((line, line_type))
        if current_lines:
            yield Part(name, current_lines)

    def remove_rest_from_lines(
        self,
        lines: list[tuple[str, LineType]],
        index: int,
    ) -> list[tuple[str, LineType]]:
        rest: list[tuple[str, LineType]] = []
        for _ in range(index, len(lines)):
            rest.append(lines.pop(index))
        return rest

    def create_and_remove_line_sections_inside_if(
        self,
        lines: list[tuple[str, LineType]],
        index: int,
    ) -> Generator[list[tuple[str, LineType]], None, None]:
        counter: Counter = Counter()
        section: list[tuple[str, LineType]] = []
        for _ in range(index, len(lines)):
            line, line_type = lines[index]
            if (
                line_type is LineType.if_exit
                or line_type is LineType.else_exit
                or line_type is LineType.else_enter  # Have to reset counter here
            ):
                break
            lines.pop(index)

            assert not line_type.is_if_enter()
            if counter.possible_to_increment(line_type):
                counter.increment(line_type)
                section.append((line, line_type))
                continue
            yield section
            section = [(line, line_type)]
            counter.reset()
            counter.increment(line_type)
        if section:
            yield section

    def create_and_remove_line_section_that_can_be_inside_if(
        self,
        lines: list[tuple[str, LineType]],
        index: int,
    ) -> list[tuple[str, LineType]]:
        counter: Counter = Counter()
        section: list[tuple[str, LineType]] = []
        for _ in range(index, len(lines)):
            line, line_type = lines[index]
            if line_type.is_if_enter():
                break
            if not counter.possible_to_increment(line_type):
                break
            lines.pop(index)
            counter.increment(line_type)
            section.append((line, line_type))
        return section

    def fix_lines(
        self,
        lines: list[tuple[str, LineType]],
        *,
        current_name: str | None,
        function_index: int = 1,
    ) -> list[Addon]:
        counter: Counter = Counter()

        is_inside_random: bool = False

        index: int = 0
        addons: list[Addon] = []

        while index < len(lines):
            _, line_type = lines[index]
            index += 1

            if line_type is LineType.random_enter:
                is_inside_random = True
                continue
            if line_type is LineType.random_exit:
                is_inside_random = False
                continue
            if is_inside_random:
                continue

            if counter.possible_to_increment(line_type):
                counter.increment(line_type)
                if line_type.is_if_enter() or line_type is LineType.else_enter:
                    line_sections = list(
                        self.create_and_remove_line_sections_inside_if(lines, index)
                    )
                    previous_section: list[tuple[str, LineType]] = []
                    for i, section in enumerate(line_sections):
                        if i == 0:
                            for _ in range(len(section)):
                                lines.insert(index, section.pop(0))
                                index += 1
                            previous_section = lines
                        else:
                            function_index += 1
                            addon = NewFunctionAddon(
                                lines=section,
                                add_to_middle_index=index
                                if previous_section is lines
                                else len(previous_section),
                                function_name=current_name,
                                function_index=function_index,
                                container=self.container,
                            )
                            addons.append(addon)
                            index_diff = addon.add_to_middle(previous_section)
                            if previous_section is lines:
                                index += index_diff
                            previous_section = section
                continue

            # [9 INSTEAD OF 10]
            if line_type is LineType.trigger_function and index == len(lines):
                counter.remove_fake_function_trigger()
                index -= 1
                continue

            if counter.can_add_another_if_enter():
                counter.add_fake_if_enter()
                addon = EmptyIfAddon(
                    lines=self.create_and_remove_line_section_that_can_be_inside_if(
                        lines, index - 1
                    ),
                    add_to_middle_index=index - 1,
                    container=self.container,
                )
                addons.append(addon)
                index += addon.add_to_middle(lines) - 2
            else:
                counter.add_fake_function_trigger()
                rest = self.remove_rest_from_lines(lines, index - 1)
                function_index += 1
                rest_addons = self.fix_lines(
                    rest, current_name=current_name, function_index=function_index
                )
                addon = NewFunctionAddon(
                    lines=rest,
                    add_to_middle_index=index,
                    function_name=current_name,
                    function_index=function_index,
                    container=self.container,
                )
                addons.append(addon)
                index += addon.add_to_middle(lines)
                addons.extend(rest_addons)

        return addons

    def find_goto_line_child_index(
        self, parent_line: str, child_line: str
    ) -> int | None:
        prefix = parent_line.removesuffix('"') + ' '
        suffix = '"' + FILLER_COMMENT_SUFFIX
        if not child_line.startswith(prefix):
            return None
        if not child_line.endswith(suffix):
            return None

        try:
            return int(child_line[len(prefix) : -len(suffix)].strip())
        except ValueError:
            return None

    def fix_goto_order(self, lines: list[tuple[str, LineType]]) -> None:
        gotos: list[tuple[tuple[str, LineType], tuple[str, str]]] = []
        while True:
            line = lines[0]
            if line[1] is not LineType.goto:
                break
            pair = self.find_container_and_name_from_goto(line[0])
            if pair[0] is None:
                break
            gotos.append((line, pair))
            lines.pop(0)
        if not gotos:
            return
        lines.insert(0, gotos.pop(-1)[0])

        visited_indexes: set[int] = set()
        parents_with_children: dict[
            tuple[tuple[str, LineType], tuple[str, str]],
            list[tuple[tuple[str, LineType], int]],
        ] = {}
        for i, (line, pair) in enumerate(gotos):
            if i in visited_indexes:
                continue
            is_child_of_any = False
            for maybe_parent_line, _ in gotos:
                if (
                    self.find_goto_line_child_index(
                        maybe_parent_line[0],
                        line[0],
                    )
                    is not None
                ):
                    is_child_of_any = True
                    break
            if is_child_of_any:
                continue

            children = parents_with_children.setdefault((line, pair), [])
            for j, (maybe_child_line, _) in enumerate(gotos):
                if i == j:
                    continue
                index = self.find_goto_line_child_index(
                    line[0],
                    maybe_child_line[0],
                )
                if index is not None:
                    children.append((maybe_child_line, index))
                    visited_indexes.add(j)

        for parent, children in reversed(parents_with_children.items()):
            children.sort(key=lambda x: x[1])
            for line, _ in reversed(children):
                lines.insert(0, line)
            lines.insert(0, parent[0])
