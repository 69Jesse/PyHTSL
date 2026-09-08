from helpers import expect_exception

from pyhtsw import (
    Container,
    Else,
    EmulatedHouse,
    IfAll,
    IfAny,
    PlayerStat,
    chat,
    function,
)
from pyhtsw.expression.condition.conditional_expression import ConditionalExpression
from pyhtsw.expression.expression import Expression
from pyhtsw.ext import Nestable


def has_nested_conditional(expressions: list[Expression]) -> bool:
    for expression in expressions:
        if not isinstance(expression, ConditionalExpression):
            continue
        branches = (*expression.if_expressions, *expression.else_expressions)
        if any(isinstance(e, ConditionalExpression) for e in branches):
            return True
        if has_nested_conditional(list(branches)):
            return True
    return False


a = PlayerStat('na').as_long()
b = PlayerStat('nb').as_long()
c = PlayerStat('nc').as_long()


# === A conjunctive path merges into the guard, with no flag ===

with Container() as container:

    @function('Merge')
    def merge() -> None:
        with Nestable():
            with IfAll(a == 1):
                chat('lead')
                with IfAll(b == 2):
                    chat('deep')


assert container.into_htsl() == (
    'if and (var "na" == 1 0) {\n'
    '    chat "lead"\n'
    '}\n'
    'if and (var "na" == 1 0, var "nb" == 2 0) {\n'
    '    chat "deep"\n'
    '}'
), container.into_htsl()


# === A disjunctive step materialises a flag ===

with Container() as container:

    @function('Flag')
    def flag() -> None:
        with Nestable():
            with IfAll(a == 1):
                with IfAny(c == 1, c == 2):
                    chat('an')
                with Else:
                    chat('a')


assert container.into_htsl() == (
    'if or (var "nc" == 1 0, var "nc" == 2 0) {\n'
    '    var "tmp0" = 1 false\n'
    '} else {\n'
    '    var "tmp0" = 0 false\n'
    '}\n'
    'if and (var "na" == 1 0, var "tmp0" == 1 0) {\n'
    '    chat "an"\n'
    '}\n'
    'if and (var "na" == 1 0, var "tmp0" == 0 0) {\n'
    '    chat "a"\n'
    '}'
), container.into_htsl()


# === A body that writes what the guard reads gets a flag instead of a re-test ===

with Container() as container:

    @function('Unsafe')
    def unsafe() -> None:
        with Nestable():
            with IfAll(a > 5):
                a.value = 0
                with IfAll(b > 0):
                    chat('hi')


htsl = container.into_htsl()
assert 'var "tmp0" = 1' in htsl, htsl
assert 'if and (var "na" > 5 0, var "nb" > 0 0)' not in htsl, htsl


# === Nothing nested means nothing changes ===

with Container() as plain:

    @function('Plain')
    def plain_body() -> None:
        with IfAll(a == 1):
            chat('one')
        with IfAny(b == 1, b == 2):
            chat('two')


with Container() as wrapped:

    @function('Plain')
    def wrapped_body() -> None:
        with Nestable():
            with IfAll(a == 1):
                chat('one')
            with IfAny(b == 1, b == 2):
                chat('two')


assert plain.into_htsl() == wrapped.into_htsl(), wrapped.into_htsl()


# === Four levels deep, and the output is flat ===

with Container() as container:

    @function('Deep')
    def deep() -> None:
        with Nestable():
            with IfAll(a == 1):
                with IfAll(b == 1):
                    with IfAll(c == 1):
                        with IfAll(a == 2):
                            chat('bottom')


block = next(b for b in container.blocks if b.get_name() == 'Deep')
assert not has_nested_conditional(list(block.expressions))
assert container.into_htsl() == (
    'if and (var "na" == 1 0, var "nb" == 1 0, var "nc" == 1 0, var "na" == 2 0) {\n'
    '    chat "bottom"\n'
    '}'
), container.into_htsl()


# === The region has to be opened at the top level of a block ===

with Container():

    @function('Misplaced')
    def misplaced() -> None:
        with IfAll(a == 1), expect_exception(SyntaxError), Nestable():
            pass


# === Flattened branches execute the same as the nested source would ===

for values in ((1, 2), (1, 9), (9, 2)):
    with EmulatedHouse(ignore_action_limits=True) as house:
        out = PlayerStat('nout').as_long().with_auto_unset(False)
        house.put(a, values[0], ignore_warning=True)
        house.put(b, values[1], ignore_warning=True)
        out.value = 0
        with Nestable():
            with IfAll(a == 1):
                out.value += 1
                with IfAny(b == 2, b == 3):
                    out.value += 10
                with Else:
                    out.value += 100

        expected = 0
        if values[0] == 1:
            expected += 1
            expected += 10 if values[1] in (2, 3) else 100

        def check(_expected: int = expected, _out: PlayerStat = out) -> None:
            assert int(house.get_raw(_out)) == _expected, (
                house.get_raw(_out),
                _expected,
            )

        house.assert_all(check)

print('test_nesting OK')
