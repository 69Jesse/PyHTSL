from ..placeholders import PlaceholderCheckable


__all__ = ('PlayerPositionYaw',)


PlayerPositionYaw = PlaceholderCheckable(
    assignment_right_side='%player.pos.yaw%',
    comparison_left_side='placeholder "%player.pos.yaw%"',
    comparison_right_side='%player.pos.yaw%',
    in_string='%player.pos.yaw%',
)
