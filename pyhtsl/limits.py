from .actions.apply_inventory_layout import ApplyInventoryLayoutExpression
from .actions.apply_potion_effect import ApplyPotionEffectExpression
from .actions.change_player_group import ChangePlayerGroupExpression
from .actions.change_velocity import ChangeVelocityExpression
from .actions.chat import ChatExpression
from .actions.clear_potion_effects import ClearPotionEffectsExpression
from .actions.display_action_bar import DisplayActionBarExpression
from .actions.display_menu import DisplayMenuExpression
from .actions.display_title import DisplayTitleExpression
from .actions.drop_item import DropItemExpression
from .actions.enchant_held_item import EnchantHeldItemExpression
from .actions.exit_function import ExitFunctionExpression
from .actions.fail_parkour import FailParkourExpression
from .actions.full_heal import FullHealExpression
from .actions.function import Function
from .actions.give_experience_levels import GiveExperienceLevelsExpression
from .actions.give_item import GiveItemExpression
from .actions.kill_player import KillPlayerExpression
from .actions.launch_to_target import LaunchToTargetExpression
from .actions.parkour_checkpoint import ParkourCheckpointExpression
from .actions.pause_execution import PauseExecutionExpression
from .actions.play_sound import PlaySoundExpression
from .actions.player_health import PlayerHealthPlaceholder
from .actions.player_hunger import PlayerHungerPlaceholder
from .actions.player_max_health import PlayerMaxHealthPlaceholder
from .actions.random import RandomExpression
from .actions.remove_item import RemoveItemExpression
from .actions.reset_inventory import ResetInventoryExpression
from .actions.set_compass_target import SetCompassTargetExpression
from .actions.set_gamemode import SetGamemodeExpression
from .actions.set_player_team import SetPlayerTeamExpression
from .actions.teleport_player import TeleportPlayerExpression
from .actions.trigger_function import TriggerFunctionExpression
from .expression.binary_expression import BinaryExpression
from .expression.condition.conditional_expression import (
    ConditionalExpression,
    ConditionalMode,
)
from .expression.expression import Expression
from .placeholders import PlaceholderEditable

LIMITS: dict[type[Expression] | type[PlaceholderEditable], int] = {
    # expressions
    ConditionalExpression: 25,
    ChangePlayerGroupExpression: 1,
    KillPlayerExpression: 1,
    FullHealExpression: 5,
    DisplayTitleExpression: 5,
    DisplayActionBarExpression: 5,
    ResetInventoryExpression: 1,
    ParkourCheckpointExpression: 1,
    GiveItemExpression: 40,
    RemoveItemExpression: 40,
    ChatExpression: 20,
    ApplyPotionEffectExpression: 22,
    ClearPotionEffectsExpression: 5,
    GiveExperienceLevelsExpression: 5,
    BinaryExpression: 25,
    TeleportPlayerExpression: 5,
    FailParkourExpression: 1,
    PlaySoundExpression: 25,
    SetCompassTargetExpression: 5,
    SetGamemodeExpression: 1,
    RandomExpression: 25,
    TriggerFunctionExpression: 10,
    ApplyInventoryLayoutExpression: 5,
    EnchantHeldItemExpression: 25,
    PauseExecutionExpression: 30,
    SetPlayerTeamExpression: 1,
    DisplayMenuExpression: 10,
    DropItemExpression: 5,
    ChangeVelocityExpression: 5,
    LaunchToTargetExpression: 5,
    # TODO SetPlayerWeatherExpression: 5,
    # TODO SetPlayerTimeExpression: 5,
    # TODO ToggleNameTagDisplayExpression: 5,
    ExitFunctionExpression: 1,
    # placeholders
    PlayerMaxHealthPlaceholder: 5,
    PlayerHealthPlaceholder: 5,
    PlayerHungerPlaceholder: 5,
}


class Counter:
    count: dict[type[Expression] | type[PlaceholderEditable], int]

    def __init__(self) -> None:
        self.count = {}

    @staticmethod
    def expression_into_cls(
        expression: Expression,
    ) -> type[Expression] | type[PlaceholderEditable]:
        if isinstance(expression, BinaryExpression):
            expr = expression.into_assignment_expression()
            if isinstance(expr.left, PlaceholderEditable):
                return type(expr.left)
        return type(expression)

    def increment(self, expression: Expression) -> None:
        cls = self.expression_into_cls(expression)
        self.count[cls] = self.count.get(cls, 0) + 1

    def would_exceed(self, expression: Expression) -> bool:
        cls = self.expression_into_cls(expression)
        new_count = self.count.get(cls, 0) + 1
        limit = LIMITS.get(cls)
        return limit is not None and new_count > limit


def fix_action_limits(
    expressions: list[Expression],
    *,
    nesting_possible: bool = True,
    function_name_if_exceeds: str | None = None,
    always_in_conditional: bool = False,
) -> tuple[list[Expression], list[Expression]]:
    """Fix action limits for a list of expressions.

    Returns a tuple of the fixed expressions that fit within a single block,
    and the remaining expressions that exceed the limits and need to be put in a new block.
    """
    result: list[Expression] = []
    global_counter = Counter()
    i = 0

    while i < len(expressions):
        expr = expressions[i]
        can_nest = nesting_possible and expr.can_be_nested()
        should_wrap = can_nest and (
            always_in_conditional or global_counter.would_exceed(expr)
        )

        if should_wrap:
            dummy = ConditionalExpression([], ConditionalMode.AND)
            if global_counter.would_exceed(dummy):
                break

            group: list[Expression] = []
            group_counter = Counter()
            while i < len(expressions) and expressions[i].can_be_nested():
                if group_counter.would_exceed(expressions[i]):
                    break
                group_counter.increment(expressions[i])
                group.append(expressions[i])
                i += 1

            if not group:
                break

            cond = ConditionalExpression(
                conditions=[],
                mode=ConditionalMode.AND,
                if_expressions=group,
            )
            global_counter.increment(cond)
            result.append(cond)
        else:
            if global_counter.would_exceed(expr):
                break
            global_counter.increment(expr)
            result.append(expr)
            i += 1

    remaining = list(expressions[i:])

    if remaining and function_name_if_exceeds is not None:
        trigger = TriggerFunctionExpression(Function(name=function_name_if_exceeds))

        while global_counter.would_exceed(trigger) and result:
            last = result.pop()
            global_counter = Counter()
            for r in result:
                global_counter.increment(r)
            if isinstance(last, ConditionalExpression) and not last.conditions:
                remaining = last.if_expressions + remaining
            else:
                remaining = [last] + remaining

        global_counter.increment(trigger)
        result.append(trigger)

    return result, remaining
