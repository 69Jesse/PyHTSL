from pyhtsl import (
    PlayerStat,
    RandomWhole,
    chat,
)


RANDOM_1_100 = RandomWhole(1, 101)


rng = PlayerStat('rng').with_value(RANDOM_1_100)

chat(f'&aRandom number: {rng}')
rng += 5 + RANDOM_1_100
chat(f'&aAdded random number: {rng}')
chat(f'&aAnother random number: {RANDOM_1_100}')
