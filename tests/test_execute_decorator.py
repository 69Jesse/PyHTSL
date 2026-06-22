"""The `execute` decorator defers its callback until after finalization.

A function block looks empty while the container it lives in is still being
built -- its callback has not run yet. Inside a plain `with ExecutionContext`
that is exactly what you see. The `execute` decorator runs its callback later
(in the atexit hook, after everything has finalized), so by then the block is
populated.
"""

from pyhtsw import ExecutionContext, chat, create_function, execute

with ExecutionContext():

    @create_function('execute decorator test')
    def func() -> None:
        chat('hello from the test function')

    # The block's callback has not run yet -- nothing has finalized.
    assert func.block is not None
    assert func.block.is_empty(), func.block


# Exiting the context above finalized the block, running its callback. The
# `execute` callback runs even later (atexit), so it sees the populated block.
@execute()
def run() -> None:
    assert func.block is not None
    assert not func.block.is_empty(), func.block
