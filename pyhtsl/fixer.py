from abc import ABC, abstractmethod
import re

from .line_type import LineType

from typing import Generator, Optional, final


__all__ = (
    'Fixer',
)


GOTO_LINE_REGEX = re.compile(r'^goto (.+?) "(.+)"$')


class AntiSpamLogger:
    last_logged: Optional[str]
    amount_logged: int
    def __init__(self) -> None:
        self.last_logged = None
        self.amount_logged = 0

    def log(self, message: str) -> None:
        if self.last_logged is not None and self.last_logged != message:
            print(f' \x1b[38;2;255;0;0m(x{self.amount_logged})\x1b[0m' * (self.amount_logged > 1))
        if self.last_logged == message:
            self.amount_logged += 1
            return
        self.last_logged = message
        self.amount_logged = 1
        print(message, end='')


LOGGER = AntiSpamLogger()


class Part:
    name: Optional[str]
    lines: list[tuple[str, LineType]]
    def __init__(
        self,
        name: Optional[str],
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
        return self.mapping.get(LineType.if_and_enter, 0) + self.mapping.get(LineType.if_or_enter, 0)

    def can_add_another_if_enter(self) -> bool:
        return self.if_enters() < Counter.IF_ENTER_LIMIT

    def add_fake_if_enter(self) -> None:
        self.mapping[LineType.if_and_enter] = self.mapping.get(LineType.if_and_enter, 0) + 1

    def add_fake_function_trigger(self) -> None:
        self.mapping[LineType.trigger_function] = self.mapping.get(LineType.trigger_function, 0) + 1

    def remove_fake_function_trigger(self) -> None:
        self.mapping[LineType.trigger_function] -= 1

    def limit_reached(self) -> bool:
        return (
            self.if_enters() > Counter.IF_ENTER_LIMIT
            or self.mapping.get(LineType.player_stat_change, 0) > 10
            or self.mapping.get(LineType.global_stat_change, 0) > 10
            or self.mapping.get(LineType.team_stat_change, 0) > 10
            or self.mapping.get(LineType.misc_stat_change, 0) > 10

            # 9 instead of 10 to account for the filler function call if nessessary
            # This can result in some weird behavior but should not be a problem
            # See [SECOND PART] where this is reverted to not cause any issues
            # TODO fix it fully, have no clue how to do that tho...
            or self.mapping.get(LineType.trigger_function, 0) > 9
        )


class Addon(ABC):
    lines: list[tuple[str, LineType]]
    add_to_middle_index: int
    def __init__(
        self,
        lines: list[tuple[str, LineType]],
        add_to_middle_index: int,
    ) -> None:
        self.lines = lines
        self.add_to_middle_index = add_to_middle_index

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
    ) -> None:
        super().__init__(lines, add_to_middle_index)
        LOGGER.log('\x1b[38;2;0;255;0mNote:\x1b[0m Added a conditional to prevent too many stat changes.')

    def add_to_middle(self, append_to: list[tuple[str, LineType]]) -> int:
        for line in reversed((
            ('if and () {', LineType.if_and_enter),
            *self.lines,
            ('}', LineType.if_exit),
        )):
            append_to.insert(self.add_to_middle_index, line)
        return len(self.lines) + 2

    def add_to_end(self, append_to: list[tuple[str, LineType]]) -> None:
        pass


@final
class NewFunctionAddon(Addon):
    raw_function_name: Optional[str]
    function_index: int
    def __init__(
        self,
        lines: list[tuple[str, LineType]],
        add_to_middle_index: int,
        function_name: Optional[str],
        function_index: int,
    ) -> None:
        super().__init__(lines, add_to_middle_index)
        self.raw_function_name = function_name
        self.function_index = function_index
        if not self.has_unknown_name():
            LOGGER.log(f'\x1b[38;2;0;255;0mNote:\x1b[0m Created a new function named "\x1b[38;2;255;0;0m{self.function_name()}\x1b[0m" to prevent too many stat changes.')
        else:
            LOGGER.log(
                '\x1b[38;2;255;0;0mWarning:\x1b[0m You exceeded the conditional limit, and you are not in an explicit container.'
                '\n         To prevent this, use the \x1b[38;2;255;0;0m@create_function()\x1b[0m decorator or the \x1b[38;2;255;0;0mgoto()\x1b[0m function.'
                f'\n         I created the function with the name "\x1b[38;2;255;0;0m{self.function_name()}\x1b[0m" to prevent any issues.'
            )

    def has_unknown_name(self) -> bool:
        return self.raw_function_name is None

    def function_name(self) -> str:
        return f'{self.raw_function_name if not self.has_unknown_name() else "!!! Rename Me"} {self.function_index}'

    def add_to_middle(self, append_to: list[tuple[str, LineType]]) -> int:
        append_to.insert(self.add_to_middle_index, (
            (
                f'function "{self.function_name()}" false'
                '  // PyHTSL filler'
            ),
            LineType.trigger_function,
        ))
        return 1

    def create_goto_line(self) -> tuple[str, LineType]:
        return (
            (
                f'goto function "{self.function_name()}"'
                '  // PyHTSL filler'
            ),
            LineType.goto,
        )

    def add_to_end(self, append_to: list[tuple[str, LineType]]) -> None:
        append_to.append(self.create_goto_line())
        append_to.extend(self.lines)


class Fixer:
    lines: list[tuple[str, LineType]]
    new_functions_added: list[NewFunctionAddon]
    def __init__(self, lines: list[tuple[str, LineType]]) -> None:
        self.lines = lines
        self.new_functions_added = []

    def fix(self) -> list[tuple[str, LineType]]:
        parts: list[Part] = []
        for part in self.create_parts():
            addons = self.fix_lines(part.lines, current_name=part.name)
            for addon in addons:
                if isinstance(addon, NewFunctionAddon):
                    self.new_functions_added.append(addon)
                addon.add_to_end(part.lines)
            parts.append(part)

        lines = []
        for part in parts:
            lines.extend(part.lines)
        for addon in reversed(self.new_functions_added):
            lines.insert(0, addon.create_goto_line())

        LOGGER.log('')
        return lines

    def find_container_and_name_from_goto(self, line: str) -> tuple[Optional[str], Optional[str]]:
        match = GOTO_LINE_REGEX.match(line)
        if match is None:
            return (None, None)
        return (match.group(1), match.group(2))

    def create_parts(
        self,
        lines: Optional[list[tuple[str, LineType]]] = None,
    ) -> Generator[Part, None, None]:
        if lines is None:
            lines = self.lines
        name: Optional[str] = None
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
            if line_type is LineType.if_exit or line_type is LineType.else_exit:
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
        current_name: Optional[str],
        function_index: int = 1,
    ) -> list[Addon]:
        counter: Counter = Counter()

        index: int = 0
        addons: list[Addon] = []

        while index < len(lines):
            _, line_type = lines[index]
            index += 1

            if counter.possible_to_increment(line_type):
                counter.increment(line_type)
                if line_type.is_if_enter() or line_type is LineType.else_enter:
                    line_sections = list(self.create_and_remove_line_sections_inside_if(lines, index))
                    previous_section: list[tuple[str, LineType]] = []
                    for i, section in enumerate(line_sections):
                        if i == 0:
                            for _ in range(len(section)):
                                lines.insert(index, section.pop(0))
                                index += 1
                            previous_section = lines
                        else:
                            function_index += 1
                            addon = NewFunctionAddon(section, index if previous_section is lines else len(previous_section), current_name, function_index)
                            addons.append(addon)
                            index_diff = addon.add_to_middle(previous_section)
                            if previous_section is lines:
                                index += index_diff
                            previous_section = section
                continue

            # [SECOND PART]
            if line_type is LineType.trigger_function and index == len(lines):
                counter.remove_fake_function_trigger()
                index -= 1
                continue

            if counter.can_add_another_if_enter():
                counter.add_fake_if_enter()
                addon = EmptyIfAddon(
                    lines=self.create_and_remove_line_section_that_can_be_inside_if(lines, index - 1),
                    add_to_middle_index=index - 1,
                )
                addons.append(addon)
                index += addon.add_to_middle(lines) - 2
            else:
                counter.add_fake_function_trigger()
                rest = self.remove_rest_from_lines(lines, index - 1)
                function_index += 1
                rest_addons = self.fix_lines(rest, current_name=current_name, function_index=function_index)
                addon = NewFunctionAddon(
                    lines=rest,
                    add_to_middle_index=index,
                    function_name=current_name,
                    function_index=function_index,
                )
                addons.append(addon)
                index += addon.add_to_middle(lines)
                addons.extend(rest_addons)

        return addons
