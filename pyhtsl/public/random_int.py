from ..condition import PlaceholderValue


__all__ = (
    'RandomInt',
)


class RandomInt(PlaceholderValue):
    __lower_bound: int
    __exclusive_upper_bound: int

    def __init__(
        self,
        lower_bound: int,
        exclusive_upper_bound: int,
    ) -> None:
        super().__init__(f'%random.int/{lower_bound} {exclusive_upper_bound}%')

    def __create_name(self) -> str:
        return f'%random.int/{self.lower_bound} {self.exclusive_upper_bound}%'

    @property
    def lower_bound(self) -> int:
        return self.__lower_bound

    @lower_bound.setter
    def lower_bound(self, value: int) -> None:
        self.__lower_bound = value
        self.name = self.__create_name()

    @property
    def exclusive_upper_bound(self) -> int:
        return self.__exclusive_upper_bound

    @exclusive_upper_bound.setter
    def exclusive_upper_bound(self, value: int) -> None:
        self.__exclusive_upper_bound = value
        self.name = self.__create_name()
