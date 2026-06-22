# PyHTSW
*(formerly PyHTSL)*

PyHTSW is a Python frontend for [HTSW](https://github.com/LGHousing/htsw) created to simplify the process of making housings on [Hypixel](https://hypixel.net/)

## Prerequisites
- [HTSW](https://github.com/LGHousing/htsw)
- [Python](https://www.python.org/) 3.13 or newer

## Installation
To install PyHTSW, make sure Git is available in your system's PATH, then run the following command:
```bash
pip install "git+https://github.com/69Jesse/PyHTSW.git" --upgrade
```

## Usage
To use PyHTSW, you need to import anything from the package (examples below) and run your Python file like you would with any other Python file.
```
python file.py
```
This generates an htsw project folder named `file` in your HTSW projects folder, which you can then import with HTSW.

## Example
The following Python file named `experience.py`:
```python
from pyhtsw import Else, GlobalStat, IfAll, PlayerStat, chat

experience = PlayerStat('experience')
reward = PlayerStat('reward')
multiplier = PlayerStat('multiplier')
global_multiplier = GlobalStat('multiplier')

experience += reward * multiplier * global_multiplier
chat(f'&aYour EXP has been updated to &6{experience}g')

level = PlayerStat('level')
EXP_TO_LEVEL_UP = 100  # Python variable, ! not ! a stat

with IfAll(experience >= EXP_TO_LEVEL_UP):
    experience -= EXP_TO_LEVEL_UP
    level += 1
    chat(f'&eYou leveled up to &dLevel {level}&e!')
with Else:
    chat(f'&eOnly &a{EXP_TO_LEVEL_UP - experience} EXP&e left to level up!')
```
```
python experience.py
```
Generates the project `experience/` with this `import.json`:
```json
{
  "functions": [
    {
      "name": "experience",
      "actions": "functions/experience.htsl"
    }
  ]
}
```
and this `functions/experience.htsl`:
```
// Generated with PyHTSW (https://github.com/69Jesse/PyHTSW)
var "tmp0" = %var.player/reward% false
var "tmp0" *= %var.player/multiplier% false
var "tmp0" *= %var.global/multiplier% false
var "experience" += %var.player/tmp0% true
chat "&aYour EXP has been updated to &6%var.player/experience%g"
if and (var "experience" >= 100) {
    var "experience" -= 100 true
    var "level" += 1 true
    chat "&eYou leveled up to &dLevel %var.player/level%&e!"
} else {
    var "tmp0" = 100 false
    var "tmp0" -= "%var.player/experience 0%L" false
    chat "&eOnly &a%var.player/tmp0 0% EXP&e left to level up!"
}
```
