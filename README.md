# PyHTSL
PyHTSL is a Python wrapper for [HTSL](https://github.com/BusterBrown1218/HTSL) created to simplify the process of making housings on [Hypixel](https://hypixel.net/)

## Prerequisites
- [ChatTriggers](https://www.chattriggers.com/) and [HTSL](https://github.com/BusterBrown1218/HTSL)
- [Python](https://www.python.org/) 3.12 (most likely works with lower versions, but havent tested, will soon.)

## Installation
To install PyHTSL, run the following command:
```bash
pip install "git+https://github.com/69Jesse/PyHTSL.git" --upgrade
```

## Usage
To use PyHTSL, you need to import anything from the package (examples below) and run your Python file like you would with any other Python file.
```
python file.py
```
This will create a file named `file.htsl` in the `imports` folder of HTSL, you can now import the generated file with HTSL by using the name `file`.

## Example
The following Python file named `example.py`:
```python
from pyhtsl import *  # You can import everything you need individually if you want

experience = PlayerStat('experience')
reward = PlayerStat('reward')
multiplier = PlayerStat('multiplier')
global_multiplier = GlobalStat('multiplier')

experience += reward * multiplier * global_multiplier
chat(f'&eYour EXP has been updated to &a{experience}&e!')

level = PlayerStat('level')
EXP_TO_LEVEL_UP = 100  # Python variable, ! not ! a stat

with IfAnd(experience >= EXP_TO_LEVEL_UP):
    experience -= EXP_TO_LEVEL_UP
    level += 1
    chat(f'&eYou leveled up to &dLevel {level}&e!')
with Else:
    chat(f'&eOnly &a{EXP_TO_LEVEL_UP - experience} EXP&e left to level up!')
```
```
python example.py
```
Will generate the following HTSL code in `example.htsl`:
```
// Generated with PyHTSL https://github.com/69Jesse/PyHTSL
stat temp1 = "%stat.player/reward%"
stat temp1 *= "%stat.player/multiplier%"
stat temp1 *= "%stat.global/multiplier%"
stat experience += "%stat.player/temp1%"
chat "&eYour EXP has been updated to &a%stat.player/experience%&e!"
if and (stat experience >= 100) {
stat experience -= "100"
stat level += "1"
chat "&eYou leveled up to &dLevel %stat.player/level%&e!"
} else {
stat temp1 = "100"
stat temp1 -= "%stat.player/experience%"
chat "&eOnly &a%stat.player/temp1% EXP&e left to level up!"
}
```
