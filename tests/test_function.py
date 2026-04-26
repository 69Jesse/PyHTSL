from pyhtsl import Container, chat, create_function, trigger_function


with Container() as container:
    @create_function('greet')
    def greet() -> None:
        chat('hello')

    trigger_function(greet)

expected = (
    'function "greet" false\n'
    '\n'
    '\n'
    'goto "function" "greet"\n'
    '    chat "hello"'
)
assert container.into_htsl() == expected, container.into_htsl()
