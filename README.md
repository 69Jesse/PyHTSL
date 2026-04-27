# PyHTSL
PyHTSL is a Python wrapper for [HTSL](https://github.com/BusterBrown1218/HTSL) created to simplify the process of making housings on [Hypixel](https://hypixel.net/)

## Prerequisites
- [ChatTriggers](https://www.chattriggers.com/) and [HTSL](https://github.com/BusterBrown1218/HTSL)
- [Python](https://www.python.org/) 3.12 or newer

## Installation
To install PyHTSL, make sure Git is available in your system's PATH, then run the following command:
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

experience = PlayerStat('experience').as_long()
reward = PlayerStat('reward').as_double()
multiplier = PlayerStat('multiplier').as_double()
global_multiplier = GlobalStat('multiplier').as_double()

experience += reward * multiplier * global_multiplier
chat(f'&eYour EXP has been updated to &a{experience}&e!')

level = PlayerStat('level').as_long()
EXP_TO_LEVEL_UP = 100  # Python variable, ! not ! a stat

with IfAll(experience >= EXP_TO_LEVEL_UP):
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
var "tmp0" = "%var.player/reward 0.0%D" false
var "tmp0" *= "%var.player/multiplier 0.0%D" false
var "tmp0" *= "%var.global/multiplier 0.0%D" false
var "experience" += "%var.player/tmp0 0%L" true

chat "&eYour EXP has been updated to &a%var.player/experience 0%&e!"

if and (var "experience" >= 100 0) {
    var "experience" -= 100 true
    var "level" += 1 true
    chat "&eYou leveled up to &dLevel %var.player/level 0%&e!"
} else {
    var "tmp0" = 100 false
    var "tmp0" -= "%var.player/experience 0%L" false
    chat "&eOnly &a%var.player/tmp0 0% EXP&e left to level up!"
}
```
