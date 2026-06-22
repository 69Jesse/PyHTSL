"""ctx.print captures output via redirect_stdout (everything happens at __exit__)."""

import io
from contextlib import redirect_stdout

from pyhtsw import ExecutionContext, PlayerStat

# Plain text
buf = io.StringIO()
with redirect_stdout(buf):
    with ExecutionContext() as ctx:
        ctx.print('hello')

output = buf.getvalue()
assert 'hello' in output, output


# Stat reference is substituted with the put value
buf = io.StringIO()
with redirect_stdout(buf):
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_long()
        ctx.put(x, 42)
        ctx.print('value:', x)

output = buf.getvalue()
assert 'value:' in output, output
assert '42' in output, output


# Multiple prints all show up
buf = io.StringIO()
with redirect_stdout(buf):
    with ExecutionContext() as ctx:
        ctx.print('first')
        ctx.print('second')
        ctx.print('third')

output = buf.getvalue()
assert 'first' in output, output
assert 'second' in output, output
assert 'third' in output, output
# In order
assert output.index('first') < output.index('second') < output.index('third')


# Computed values are printed after the writes finish
buf = io.StringIO()
with redirect_stdout(buf):
    with ExecutionContext() as ctx:
        x = PlayerStat('x').as_long()
        y = PlayerStat('y').as_long()
        ctx.put(x, 10)
        y.value = x + 5
        ctx.print('y =', y)

output = buf.getvalue()
assert '15' in output, output
