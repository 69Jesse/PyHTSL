from abc import ABC, abstractmethod
import re

from .line_type import LineType

from typing import Generator, Optional, final


__all__ = (
    'Fixer',
)


GOTO_LINE_REGEX = re.compile(r'^goto (.+?) "(.+)"$')


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

    def possible_to_increment(
        self,
        line_type: LineType,
    ) -> bool:
        self.increment(line_type)
        possible = not self.limit_reached()
        self.mapping[line_type] -= 1
        return possible

    IF_ENTER_LIMIT: int = 5

    def if_enters(self) -> int:
        return self.mapping.get(LineType.if_and_enter, 0) + self.mapping.get(LineType.if_or_enter, 0)

    def can_add_another_if_enter(self) -> bool:
        return self.if_enters() < Counter.IF_ENTER_LIMIT

    def add_fake_if_enter(self) -> None:
        self.mapping[LineType.if_and_enter] = self.mapping.get(LineType.if_and_enter, 0) + 1

    def limit_reached(self) -> bool:
        return (
            self.if_enters() > Counter.IF_ENTER_LIMIT
            or self.mapping.get(LineType.player_stat_change, 0) > 5
            or self.mapping.get(LineType.global_stat_change, 0) > 5
            or self.mapping.get(LineType.team_stat_change, 0) > 5
            or self.mapping.get(LineType.misc_stat_change, 0) > 5
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
    def add_to_middle(self, append_to: list[tuple[str, LineType]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_to_end(self, append_to: list[tuple[str, LineType]]) -> None:
        raise NotImplementedError


@final
class NoChangeAddon(Addon):
    def add_to_middle(self, append_to: list[tuple[str, LineType]]) -> None:
        for line in reversed(self.lines):
            append_to.insert(self.add_to_middle_index, line)

    def add_to_end(self, append_to: list[tuple[str, LineType]]) -> None:
        pass


@final
class EmptyIfAddon(Addon):
    def add_to_middle(self, append_to: list[tuple[str, LineType]]) -> None:
        for line in reversed((
            ('if and () {', LineType.if_and_enter),
            *self.lines,
            ('}', LineType.if_exit),
        )):
            append_to.insert(self.add_to_middle_index, line)

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

    def function_name(self) -> str:
        return f'{self.raw_function_name if self.raw_function_name is not None else "Rename Me"} {self.function_index}'

    def maybe_commented(self) -> str:
        return '// ' if self.raw_function_name is None else ''

    def add_to_middle(self, append_to: list[tuple[str, LineType]]) -> None:
        append_to.insert(self.add_to_middle_index, (
            f'{self.maybe_commented()}function "{self.function_name()}" false',
            LineType.trigger_function,
        ))

    def create_goto_line(self) -> tuple[str, LineType]:
        return (
            (
                f'{self.maybe_commented()}goto function "{self.function_name()}"'
                '  // PyHTSL filler '
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
            self.process_part(part)
            parts.append(part)

        lines = []
        for part in parts:
            lines.extend(part.lines)
        for addon in reversed(self.new_functions_added):
            lines.insert(0, addon.create_goto_line())
        return lines

    def find_container_and_name_from_goto(self, line: str) -> tuple[Optional[str], Optional[str]]:
        match = GOTO_LINE_REGEX.match(line)
        if match is None:
            return (None, None)
        return (match.group(1), match.group(2))

    def create_parts(self) -> Generator[Part, None, None]:
        name: Optional[str] = None
        current_lines: list[tuple[str, LineType]] = []
        for line, line_type in self.lines:
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

    def create_possible_parts_inside_if(
        self,
        lines: list[tuple[str, LineType]],
        index: int,
    ) -> Generator[list[tuple[str, LineType]], None, None]:
        counter: Counter = Counter()
        part: list[tuple[str, LineType]] = []
        for _ in range(index, len(lines)):
            line, line_type = lines[index]
            if line_type is LineType.if_exit:
                return
            lines.pop(index)

            assert not line_type.is_if_enter()
            if counter.possible_to_increment(line_type):
                counter.increment(line_type)
                part.append((line, line_type))
                continue
            yield part
            part = [(line, line_type)]
            counter = Counter()
            counter.increment(line_type)
        if part:
            yield part

    def get_addons_from_lines(
        self,
        lines: list[tuple[str, LineType]],
        *,
        current_name: Optional[str],
        function_index: int,
    ) -> Generator[Addon, None, None]:
        counter: Counter = Counter()
        index: int = 0

        while index < len(lines):
            _, line_type = lines[index]
            index += 1

            if counter.possible_to_increment(line_type):
                if line_type.is_if_enter():
                    for part in self.create_possible_parts_inside_if(
                        lines,
                        index + 1,
                    ):
                        print(part)
                        if counter.can_add_another_if_enter():
                            yield EmptyIfAddon(part, index)
                            counter.add_fake_if_enter()
                        else:
                            yield NewFunctionAddon(part, index, current_name, function_index)
                            function_index += 1
                    continue

                counter.increment(line_type)
                continue

            yield NoChangeAddon(
                lines[index - 1:],
                index,
            )

            rest = self.remove_rest_from_lines(lines, index)
            yield NewFunctionAddon(rest, index, current_name, function_index)
            function_index += 1

    def process_part(self, part: Part) -> None:
        addons: list[Addon] = []
        for addon in self.get_addons_from_lines(
            part.lines,
            current_name=part.name,
            function_index=2,
        ):
            print(addon)
            addons.append(addon)

        for addon in reversed(addons):
            addon.add_to_middle(part.lines)
        for addon in addons:
            addon.add_to_end(part.lines)
