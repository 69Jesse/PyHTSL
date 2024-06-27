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

    def possible_to_increment(self, line_type: LineType) -> bool:
        self.increment(line_type)
        possible = not self.limit_reached()
        self.mapping[line_type] -= 1
        return possible

    IF_ENTER_LIMIT: int = 15

    def limit_reached(self) -> bool:
        return (
            (self.mapping.get(LineType.if_and_enter, 0) + self.mapping.get(LineType.if_or_enter, 0)) >= self.IF_ENTER_LIMIT
            or self.mapping.get(LineType.player_stat_change, 0) >= 10
            or self.mapping.get(LineType.global_stat_change, 0) >= 10
            or self.mapping.get(LineType.team_stat_change, 0) >= 10
            or self.mapping.get(LineType.misc_stat_change, 0) >= 10
        )


class Addon(ABC):
    @abstractmethod
    def apply(self, lines: list[tuple[str, LineType]]) -> None:
        raise NotImplementedError


@final
class EmptyIfAddon(Addon):
    pass


@final
class NewFunctionAddon(Addon):
    name: Optional[str]
    index: int
    def __init__(
        self,
        name: Optional[str],
        index: int,
    ) -> None:
        self.name = name
        self.index = index

    def create_goto_line(self) -> tuple[str, LineType]:
        return (f'goto function "{self.name} {self.index}"', LineType.goto)


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

    def remove_rest_from_lines(self, lines: list[tuple[str, LineType]], index: int) -> list[tuple[str, LineType]]:
        rest: list[tuple[str, LineType]] = []
        for _ in range(index, len(lines)):
            rest.append(lines.pop(index))
        return rest

    def process_part(self, part: Part) -> None:
        counter: Counter = Counter()
        addons: list[Addon] = []
        for i, (line, line_type) in enumerate(part.lines):
            if i != 0 and line_type is LineType.goto:
                raise RuntimeError('This should never happen')
            if not counter.possible_to_increment(line_type):
                rest = self.remove_rest_from_lines(part.lines, i)
                print('\n'.join(map(str, rest)))
                break
            counter.increment(line_type)
