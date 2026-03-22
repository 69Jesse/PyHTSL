from pyhtsl.actions.apply_inventory_layout import ApplyInventoryLayoutExpression
from pyhtsl.actions.apply_potion_effect import ApplyPotionEffectExpression
from pyhtsl.actions.change_velocity import ChangeVelocityExpression
from pyhtsl.actions.chat import ChatExpression
from pyhtsl.actions.clear_potion_effects import ClearPotionEffectsExpression
from pyhtsl.actions.display_menu import DisplayMenuExpression
from pyhtsl.actions.drop_item import DropItemExpression
from pyhtsl.actions.enchant_held_item import EnchantHeldItemExpression
from pyhtsl.actions.exit_function import ExitFunctionExpression
from pyhtsl.actions.fail_parkour import FailParkourExpression
from pyhtsl.actions.give_experience_levels import GiveExperienceLevelsExpression
from pyhtsl.actions.give_item import GiveItemExpression
from pyhtsl.actions.launch_to_target import LaunchToTargetExpression
from pyhtsl.actions.parkour_checkpoint import ParkourCheckpointExpression
from pyhtsl.actions.pause_execution import PauseExecutionExpression
from pyhtsl.actions.play_sound import PlaySoundExpression
from pyhtsl.actions.player_health import PlayerHealthPlaceholder
from pyhtsl.actions.player_hunger import PlayerHungerPlaceholder
from pyhtsl.actions.random import RandomExpression
from pyhtsl.actions.remove_item import RemoveItemExpression
from pyhtsl.actions.set_compass_target import SetCompassTargetExpression
from pyhtsl.actions.set_gamemode import SetGamemodeExpression
from pyhtsl.actions.set_player_team import SetPlayerTeamExpression
from pyhtsl.actions.teleport_player import TeleportPlayerExpression
from pyhtsl.actions.trigger_function import TriggerFunctionExpression
from pyhtsl.expression.binary_expression import BinaryExpression

from .actions.change_player_group import ChangePlayerGroupExpression
from .actions.display_action_bar import DisplayActionBarExpression
from .actions.display_title import DisplayTitleExpression
from .actions.full_heal import FullHealExpression
from .actions.kill_player import KillPlayerExpression
from .actions.player_max_health import PlayerMaxHealthPlaceholder
from .actions.reset_inventory import ResetInventoryExpression
from .expression.condition.conditional_expression import ConditionalExpression
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

    def increment(self, expression: Expression) -> None:
        cls: type[Expression] | type[PlaceholderEditable] | None = None
        if isinstance(expression, BinaryExpression):
            expr = expression.into_assignment_expression()
            if isinstance(expr.left, PlaceholderEditable):
                cls = type(expr.left)
        if cls is None:
            cls = type(expression)
        self.count[cls] = self.count.get(cls, 0) + 1

    def limit_reached(self) -> bool:
        for cls, count in self.count.items():
            limit = LIMITS.get(cls)
            if limit is not None and count > limit:
                return True
        return False


def fix_action_limits(expressions: list[Expression]) -> list[Expression]:
    return expressions
