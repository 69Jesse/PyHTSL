from ..placeholders import PlaceholderCheckable


__all__ = (
    'PlayerLocationYaw',
)


PlayerLocationYaw = PlaceholderCheckable(
    assignment_right_side='%player.location.yaw%',
    comparison_left_side='placeholder "%player.location.yaw%"',
    comparison_right_side='%player.location.yaw%',
    in_string='%player.location.yaw%',
)
