from .condition import PlaceholderValue, Condition
from ..group import Group
from ..team import Team

from typing import final, Literal


__all__ = (
    'RawCondition',
    'PlayerPing',
    'PlayerExperience',
    'PlayerLevel',
    'PlayerProtocol',
    'PlayerLocationX',
    'PlayerLocationY',
    'PlayerLocationZ',
    'PlayerLocationYaw',
    'PlayerLocationPitch',
    'PlayerGroupPriority',
    'HouseGuests',
    'HouseCookies',
    'DateUnix',
    'DoingParkour',
    'PlayerSneaking',
    'PlayerFlying',
    'PlayerHealth',
    'PlayerMaxHealth',
    'PlayerHunger',
    'CanPVP',
    'BlockType',
    'DamageCause',
    'FishingEnvironment',
    'RequiredGroup',
    'RequiredPermission',
    'WithinRegion',
    'HasItem',
    'HasPotionEffect',
    'RequiredGamemode',
    'RequiredTeam',
)


@final
class RawCondition(Condition):
    name: str
    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name


PlayerPing = PlaceholderValue('%player.ping%')
PlayerExperience = PlaceholderValue('%player.experience%')
PlayerLevel = PlaceholderValue('%player.level%')
PlayerProtocol = PlaceholderValue('%player.protocol%')
PlayerLocationX = PlaceholderValue('%player.location.x%')
PlayerLocationY = PlaceholderValue('%player.location.y%')
PlayerLocationZ = PlaceholderValue('%player.location.z%')
PlayerLocationYaw = PlaceholderValue('%player.location.yaw%')
PlayerLocationPitch = PlaceholderValue('%player.location.pitch%')
PlayerGroupPriority = PlaceholderValue('%player.group.priority%')
HouseGuests = PlaceholderValue('%house.guests%')
HouseCookies = PlaceholderValue('%house.cookies%')
DateUnix = PlaceholderValue('%date.unix%')

DoingParkour = RawCondition('doingParkour')
PlayerSneaking = RawCondition('isSneaking')
PlayerFlying = RawCondition('isFlying')
PlayerHealth = PlaceholderValue('health')
PlayerMaxHealth = PlaceholderValue('maxHealth')
PlayerHunger = PlaceholderValue('hunger')
CanPVP = RawCondition('canPvp')


class TinyCondition(Condition):
    __slots__ = ()


@final
class BlockType(TinyCondition):
    block_name: str
    match_type_only: bool
    def __init__(
        self,
        block_name: str,
        match_type_only: bool = False,
    ) -> None:
        self.block_name = block_name
        self.match_type_only = match_type_only

    def __str__(self) -> str:
        return f'blockType "{self.block_name}" {str(self.match_type_only).lower()}'


@final
class DamageCause(TinyCondition):
    damage_cause: str
    def __init__(
        self,
        damage_cause: Literal[
            'entity Attack',
            'projectile',
            'suffocation',
            'fall',
            'lava',
            'fire',
            'fire_tick',
            'drowning',
            'starvation',
            'poison',
            'thorns',
        ],
    ) -> None:
        self.damage_cause = damage_cause

    def __str__(self) -> str:
        return f'damageCause "{self.damage_cause}"'


@final
class FishingEnvironment(TinyCondition):
    environment: str
    def __init__(
        self,
        environment: Literal['water', 'lava'],
    ) -> None:
        self.environment = environment

    def __str__(self) -> str:
        return f'fishingEnv "{self.environment}"'


@final
class RequiredGroup(TinyCondition):
    group: Group
    include_higher_groups: bool
    def __init__(
        self,
        group: Group | str,
        include_higher_groups: bool = False,
    ) -> None:
        self.group = group if isinstance(group, Group) else Group(group)
        self.include_higher_groups = include_higher_groups

    def __str__(self) -> str:
        return f'hasGroup "{self.group.name}" {str(self.include_higher_groups).lower()}'


@final
class RequiredPermission(TinyCondition):
    permission: str
    def __init__(
        self,
        permission: str,
    ) -> None:
        self.permission = permission

    def __str__(self) -> str:
        return f'hasPermission "{self.permission}"'


@final
class WithinRegion(TinyCondition):
    region: str
    def __init__(
        self,
        region: str,
    ) -> None:
        self.region = region

    def __str__(self) -> str:
        return f'inRegion "{self.region}"'


@final
class HasItem(TinyCondition):
    item: str
    what_to_check: str
    where_to_check: str
    required_amount: str
    def __init__(
        self,
        item: str,
        what_to_check: Literal['item_type', 'metadata'] = 'metadata',
        where_to_check: Literal['hand', 'armor', 'hotbar', 'inventory', 'anywhere'] = 'anywhere',
        required_amount: Literal['any_amount', 'equal_or_greater_amount'] = 'any_amount',
    ) -> None:
        self.item = item
        self.what_to_check = what_to_check
        self.where_to_check = where_to_check
        self.required_amount = required_amount

    def __str__(self) -> str:
        return f'hasItem "{self.item}" {self.what_to_check} {self.where_to_check} {self.required_amount}'


class HasPotionEffect(TinyCondition):
    effect: str
    def __init__(
        self,
        effect: Literal[
            'speed',
            'slowness',
            'haste',
            'mining_fatigue',
            'strength',
            'instant_health',
            'instant_damage',
            'jump_boost',
            'nausea',
            'regeneration',
            'resistance',
            'fire_resistance',
            'water_breathing',
            'invisibility',
            'blindness',
            'night_vision',
            'hunger',
            'weakness',
            'poison',
            'wither',
            'health_boost',
            'absorption',
        ],
    ) -> None:
        self.effect = effect

    def __str__(self) -> str:
        return f'hasPotion "{self.effect}"'


class RequiredGamemode(TinyCondition):
    gamemode: str
    def __init__(
        self,
        gamemode: Literal['adventure', 'survival', 'creative'],
    ) -> None:
        self.gamemode = gamemode

    def __str__(self) -> str:
        return f'isGamemode "{self.gamemode}"'


class RequiredTeam(TinyCondition):
    team: Team
    def __init__(
        self,
        team: Team | str,
    ) -> None:
        self.team = team if isinstance(team, Team) else Team(team)

    def __str__(self) -> str:
        return f'isTeam "{self.team.name}"'
