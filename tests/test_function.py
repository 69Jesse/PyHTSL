from pyhtsw import Container, chat, create_function, trigger_function

with Container() as container:

    @create_function('greet')
    def greet() -> None:
        chat('hello')

    trigger_function(greet)

# No more goto wrappers: each block renders its own action list, and the
# function lands in its own file at export time.
expected = 'function "greet" false\n\n\nchat "hello"'
assert container.into_htsl() == expected, container.into_htsl()
