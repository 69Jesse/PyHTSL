"""`~condition` must return an inverted clone, never mutate the original.

`PlayerSneaking` (and the other named conditions) are module-level singletons,
so an in-place `__invert__` would corrupt the shared object for every later
use — `print(PlayerSneaking, ~PlayerSneaking)` showed both as inverted.
"""

from pyhtsw import (
    Container,
    IfAll,
    PlayerSneaking,
    PlayerStat,
    RequiredGroup,
    RequiredTeam,
    WithinRegion,
    chat,
)

# Inverting a named condition does not mutate the original singleton.
assert PlayerSneaking.inverted is False
inverted = ~PlayerSneaking
assert inverted.inverted is True
assert PlayerSneaking.inverted is False  # original untouched
assert inverted is not PlayerSneaking

# Double invert round-trips to a non-inverted clone.
assert (~~PlayerSneaking).inverted is False

# The original and its inversion render distinctly in the same program.
with Container() as container:
    with IfAll(PlayerSneaking):
        chat('sneaking')
    with IfAll(~PlayerSneaking):
        chat('not sneaking')

assert container.into_htsl() == (
    'if and (isSneaking) {\n    chat "sneaking"\n}\n'
    'if and (!isSneaking) {\n    chat "not sneaking"\n}'
), container.into_htsl()

# After all of the above, the singleton is still usable as non-inverted.
with Container() as container:
    with IfAll(PlayerSneaking):
        chat('still works')

assert container.into_htsl() == ('if and (isSneaking) {\n    chat "still works"\n}'), (
    container.into_htsl()
)


# A comparison condition is likewise cloned, not mutated.
x = PlayerStat('x').as_long()
cond = x > 5
assert cond.inverted is False
neg = ~cond
assert neg.inverted is True
assert cond.inverted is False
assert neg is not cond


# Conditions backed by plain value objects (Group / Team / Region) clone too —
# their cloned_raw must not assume the value object implements `cloned()`.
for condition in (
    RequiredGroup('Helper'),
    RequiredTeam('red'),
    WithinRegion('spawn'),
):
    assert condition.inverted is False
    flipped = ~condition
    assert flipped.inverted is True
    assert condition.inverted is False  # original untouched
    assert flipped is not condition
    # equals_raw must also work without a `.equals()` on the value object
    assert condition.equals(condition.cloned())
    assert not condition.equals(flipped)

# They render with the inversion marker in real HTSL.
with Container() as container:
    with IfAll(~RequiredGroup('Helper', include_higher_groups=True)):
        chat('not helper+')

assert container.into_htsl() == (
    'if and (!hasGroup "Helper" true) {\n    chat "not helper+"\n}'
), container.into_htsl()
