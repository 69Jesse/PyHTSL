from .team import Team

from abc import ABC, abstractmethod
from typing import final


class Stat(ABC):
    name: str
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    @staticmethod
    def get_prefix() -> str:
        raise NotImplementedError

    @abstractmethod
    @staticmethod
    def get_placeholder_word() -> str:
        raise NotImplementedError

    def get_placeholder(self) -> str:
        return f'%stat.{self.get_placeholder_word()}/{self.name}%'

    def get_htsl_formatted(self) -> str:
        return f'{self.get_prefix()} {self.name}'

    def __str__(self) -> str:
        return self.get_placeholder()

    def __repr__(self) -> str:
        return self.get_htsl_formatted()



@final
class PlayerStat(Stat):
    @staticmethod
    def get_prefix() -> str:
        return 'stat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'player'


@final
class GlobalStat(Stat):
    @staticmethod
    def get_prefix() -> str:
        return 'globalstat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'global'


@final
class TeamStat(Stat):
    team: Team
    def __init__(self, name: str, team: Team | str) -> None:
        super().__init__(name)
        self.team = team if isinstance(team, Team) else Team(team)

    @staticmethod
    def get_prefix() -> str:
        return 'teamstat'

    @staticmethod
    def get_placeholder_word() -> str:
        return 'team'

    def get_htsl_formatted(self) -> str:
        return f'{super().get_htsl_formatted()} {self.team.name}'
