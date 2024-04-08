# can be replaced with `from pyhtsl import *`
from pyhtsl import (
    PlayerStat,
    GlobalStat,
    chat,
    IfAnd,
    Else,
)


experience = PlayerStat('experience')
reward = PlayerStat('reward')
multiplier = PlayerStat('multiplier')
global_multiplier = GlobalStat('multiplier')

experience += reward * multiplier * global_multiplier
chat(f'&aYour EXP has been updated to &6{experience}g')


level = PlayerStat('level')
EXP_TO_LEVEL_UP = 100  # Python variable, ! not ! a stat

with IfAnd(experience >= EXP_TO_LEVEL_UP):
    experience -= EXP_TO_LEVEL_UP
    level += 1
    chat(f'&eYou leveled up to &dLevel {level}&e!')
with Else:
    chat(f'&eOnly &a{EXP_TO_LEVEL_UP - experience} EXP&e left to level up!')



"""Output:

// Generated with PyHTSL https://github.com/69Jesse/PyHTSL
stat temp1 = "%stat.player/reward%"
stat temp1 *= "%stat.player/multiplier%"
stat temp1 *= "%stat.global/multiplier%"
stat experience += "%stat.player/temp1%"
chat "&aYour EXP has been updated to &6%stat.player/experience%g"
if and (stat experience >= 100) {
stat experience -= "100"
stat level += "1"
chat "&eYou leveled up to &dLevel %stat.player/level%&e!"
} else {
stat temp1 = "100"
stat temp1 -= "%stat.player/experience%"
chat "&eOnly &a%stat.player/temp1% EXP&e left to level up!"
}
"""
