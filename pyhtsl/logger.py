class AntiSpamLogger:
    messages: list[tuple[str, int]]
    def __init__(self) -> None:
        self.messages = []

    def log(self, message: str) -> None:
        if self.messages and self.messages[-1][0] == message:
            self.messages[-1] = (message, self.messages[-1][1] + 1)
        else:
            self.messages.append((message, 1))

    def publish(self) -> None:
        content = '\n' * (len(self.messages) > 0)
        for message, amount in self.messages:
            content += '\n' + message + f' \x1b[38;2;255;0;0m(x{amount})\x1b[0m' * (amount > 1)
        content += '\n' * (len(self.messages) > 0)
        if content:
            print(content)
