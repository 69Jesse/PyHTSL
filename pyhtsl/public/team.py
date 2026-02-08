from typing import TYPE_CHECKING

from ..placeholders import PlaceholderCheckable

if TYPE_CHECKING:
    from ..stats.team_stat import TeamStat


__all__ = ('Team',)


class Team:
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
        from ..stats.team_stat import TeamStat
        return TeamStat(key, self)

    def players(self) -> PlaceholderCheckable:
        from .team_players import TeamPlayers
        return TeamPlayers(self)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.name}>'
