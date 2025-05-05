from ..placeholders import PlaceholderEditable


__all__ = (
    'PlayerMaxHealth',
)


PlayerMaxHealth = PlaceholderEditable(
    assignment_left_side='maxHealth',
    assignment_right_side='%player.maxhealth%',
    comparison_left_side='placeholder "%player.maxhealth%"',
    comparison_right_side='%player.maxhealth%',
    in_string='%player.maxhealth%',
)
