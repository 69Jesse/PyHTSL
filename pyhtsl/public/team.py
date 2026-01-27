from ..placeholders import PlaceholderCheckable

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..stats.team_stat import TeamStat
    from .team_players import TeamPlayers


__all__ = ('Team',)


class Team:
    @staticmethod
    def _import_team_stat(team_stat: type['TeamStat']) -> None:
        globals()[team_stat.__name__] = team_stat

    @staticmethod
    def _import_team_players(team_players: ...) -> None:
        globals()[team_players.__name__] = team_players

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Team):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def stat(self, key: str) -> 'TeamStat':
        return TeamStat(key, self)

    def players(self) -> PlaceholderCheckable:
        return TeamPlayers(self)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}>'
