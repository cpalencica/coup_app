'''
Enum class for the different types of cards in the game.
'''

from enum import Enum

class Card(Enum):
    DUKE = "Duke"
    ASSASSIN = "Assassin"
    CAPTAIN = "Captain"
    AMBASSADOR = "Ambassador"
    CONTESSA = "Contessa"

ALL_CARDS = [
    Card.DUKE, Card.DUKE, Card.DUKE,
    Card.ASSASSIN, Card.ASSASSIN, Card.ASSASSIN,
    Card.CAPTAIN, Card.CAPTAIN, Card.CAPTAIN,
    Card.AMBASSADOR, Card.AMBASSADOR, Card.AMBASSADOR,
    Card.CONTESSA, Card.CONTESSA, Card.CONTESSA,
]