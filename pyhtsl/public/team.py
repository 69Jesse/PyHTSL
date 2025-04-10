from ..condition import PlaceholderValue

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .team_stat import TeamStat
    from .team_players import TeamPlayers


__all__ = (
    'Team',
)


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

    if TYPE_CHECKING:
        def stat(self, key: str) -> TeamStat:
            return TeamStat(key, self)

        def players(self) -> PlaceholderValue:
            return TeamPlayers(self)
