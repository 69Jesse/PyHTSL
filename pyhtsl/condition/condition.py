from .statements import IfStatement, ConditionalMode

from abc import ABC, abstractmethod
from enum import Enum

from typing import TYPE_CHECKING, final
if TYPE_CHECKING:
    from ..stat import Stat


class Condition(ABC):
    __slots__ = ()

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError


class Operator(Enum):
    Equal = '=='
    GreaterThan = '>'
    LessThan = '<'
    GreaterThanOrEqual = '>='
    LessThanOrEqual = '<='


@final
class PlaceholderValue:
    name: str
    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name

    @staticmethod
    def equals(
        left: 'Stat | PlaceholderValue',
        right: 'Stat | PlaceholderValue | int',
    ) -> Condition:
        return OperatorCondition(left, right, Operator.Equal)

    @staticmethod
    def not_equal(
        left: 'Stat | PlaceholderValue',
        right: 'Stat | PlaceholderValue | int',
    ) -> IfStatement:
        """Not equal does not exist on housing, so we do a little magic"""
        return IfStatement([
            OperatorCondition(left, right, Operator.LessThan),
            OperatorCondition(left, right, Operator.GreaterThan),
        ], mode=ConditionalMode.OR)

    @staticmethod
    def greater_than(
        left: 'Stat | PlaceholderValue',
        right: 'Stat | PlaceholderValue | int',
    ) -> Condition:
        return OperatorCondition(left, right, Operator.GreaterThan)

    @staticmethod
    def less_than(
        left: 'Stat | PlaceholderValue',
        right: 'Stat | PlaceholderValue | int',
    ) -> Condition:
        return OperatorCondition(left, right, Operator.LessThan)

    @staticmethod
    def greater_than_or_equal(
        left: 'Stat | PlaceholderValue',
        right: 'Stat | PlaceholderValue | int',
    ) -> Condition:
        return OperatorCondition(left, right, Operator.GreaterThanOrEqual)

    @staticmethod
    def less_than_or_equal(
        left: 'Stat | PlaceholderValue',
        right: 'Stat | PlaceholderValue | int',
    ) -> Condition:
        return OperatorCondition(left, right, Operator.LessThanOrEqual)

    def __eq__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> Condition:
        return PlaceholderValue.equals(self, other)

    def __ne__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> IfStatement:
        return PlaceholderValue.not_equal(self, other)

    def __gt__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> Condition:
        return PlaceholderValue.greater_than(self, other)

    def __lt__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> Condition:
        return PlaceholderValue.less_than(self, other)

    def __ge__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> Condition:
        return PlaceholderValue.greater_than_or_equal(self, other)

    def __le__(
        self,
        other: 'Stat | PlaceholderValue | int',
    ) -> Condition:
        return PlaceholderValue.less_than_or_equal(self, other)

    def __str__(self) -> str:
        return self.name


@final
class OperatorCondition(Condition):
    left: 'Stat | PlaceholderValue'
    right: 'Stat | PlaceholderValue | int'
    operator: Operator
    def __init__(
        self,
        left: 'Stat | PlaceholderValue',
        right: 'Stat | PlaceholderValue | int',
        operator: Operator,
    ) -> None:
        self.left = left
        self.right = right
        self.operator = operator

    def __str__(self) -> str:
        return f'{repr(self.left)} {self.operator.value} {str(self.right)}'


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
PlayerHealth = PlaceholderValue('%player.health%')
PlayerMaxHealth = PlaceholderValue('%player.max_health%')
PlayerHunger = PlaceholderValue('%player.hunger%')
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
