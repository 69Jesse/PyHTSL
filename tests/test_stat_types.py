from pyhtsw import Container, PlayerStat

with Container() as container:
    s = PlayerStat('name').as_string()
    s.value = 'Alice'

assert container.into_htsl() == 'var "name" = "Alice" true', container.into_htsl()


with Container() as container:
    d = PlayerStat('score').as_double()
    d.value = 3.14

assert container.into_htsl() == 'var "score" = 3.14 true', container.into_htsl()


with Container() as container:
    long = PlayerStat('count').as_long()
    long.value = 100

assert container.into_htsl() == 'var "count" = 100 true', container.into_htsl()


with Container() as container:
    any_typed = PlayerStat('any')
    any_typed.value = 7

assert container.into_htsl() == 'var "any" = 7 true', container.into_htsl()


with Container() as container:
    long = PlayerStat('a').as_long()
    other = PlayerStat('b').as_double()
    # cross-type: assigning long-stat to double-stat reads it via fallback "0"
    other.value = long

assert container.into_htsl() == 'var "b" = "%var.player/a 0.0%D" true', (
    container.into_htsl()
)


# Same-type stat-to-stat assignment, ANY: bare placeholder (no quotes, no
# fallback shown). HTSL evaluates this in native mode, so the rhs reads as a
# direct stat reference rather than a string template.
with Container() as container:
    a = PlayerStat('a')
    b = PlayerStat('b')
    b.value = a

assert container.into_htsl() == 'var "b" = %var.player/a% true', container.into_htsl()


# Python-`str` rhs that happens to be a placeholder: `housing_type_as_rhs`
# wraps it in quotes, signalling string-mode to HTSL — which substitutes and
# casts at evaluation time. Compare to the bare form above.
with Container() as container:
    a = PlayerStat('a')
    c = PlayerStat('c')
    c.value = f'{a}'

assert container.into_htsl() == 'var "c" = "%var.player/a%" true', container.into_htsl()


# Same-type stat-to-stat with explicit numeric types: `into_string_rhs` adds
# the type-tagged form (`L` / `D`) inside quotes so HTSL parses through the
# matching backend type.
with Container() as container:
    a = PlayerStat('a').as_long()
    b = PlayerStat('b').as_long()
    b.value = a

assert container.into_htsl() == 'var "b" = "%var.player/a 0%L" true', (
    container.into_htsl()
)


with Container() as container:
    a = PlayerStat('a').as_double()
    b = PlayerStat('b').as_double()
    b.value = a

assert container.into_htsl() == 'var "b" = "%var.player/a 0.0%D" true', (
    container.into_htsl()
)


# Same-type STRING-to-STRING: quoted placeholder, no L/D suffix.
with Container() as container:
    a = PlayerStat('a').as_string()
    b = PlayerStat('b').as_string()
    b.value = a

assert container.into_htsl() == 'var "b" = "%var.player/a%" true', container.into_htsl()
