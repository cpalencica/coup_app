'''
enum class to define different possible actions in the game.
'''
from enum import Enum

class Action(Enum):
    INCOME = "income"
    FOREIGN_AID = "foreign_aid"
    COUP = "coup"
    TAX = "tax"
    STEAL = "steal"
    ASSASSINATE = "assassinate"
    EXCHANGE = "exchange"
    BLOCK = "block"
    CHALLENGE = "challenge"