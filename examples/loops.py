# can be replaced with `from pyhtsl import *`
from pyhtsl import (
    PlayerStat,
    IfAnd,
    Else,
    chat,
)


chat('&aChecking for empty teams..')
# This remains Python, so you can do things like this:
for letter in ('A', 'B', 'C', 'D', 'E', 'F'):
    stat = PlayerStat(f'team_{letter}_players')
    with IfAnd(stat == 0):
        chat(f'&eTeam {letter} is empty!')
    with Else:
        chat(f'&aTeam {letter} has {stat} player(s)!')


"""Output:

// Generated with PyHTSL https://github.com/69Jesse/PyHTSL
chat "&aChecking for empty teams.."
if and (stat team_A_players == 0) {
chat "&eTeam A is empty!"
} else {
chat "&aTeam A has %stat.player/team_A_players% player(s)!"
}
if and (stat team_B_players == 0) {
chat "&eTeam B is empty!"
} else {
chat "&aTeam B has %stat.player/team_B_players% player(s)!"
}
if and (stat team_C_players == 0) {
chat "&eTeam C is empty!"
} else {
chat "&aTeam C has %stat.player/team_C_players% player(s)!"
}
if and (stat team_D_players == 0) {
chat "&eTeam D is empty!"
} else {
chat "&aTeam D has %stat.player/team_D_players% player(s)!"
}
if and (stat team_E_players == 0) {
chat "&eTeam E is empty!"
} else {
chat "&aTeam E has %stat.player/team_E_players% player(s)!"
}
if and (stat team_F_players == 0) {
chat "&eTeam F is empty!"
} else {
chat "&aTeam F has %stat.player/team_F_players% player(s)!"
}
"""
