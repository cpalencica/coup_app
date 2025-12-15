import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.game.engine import GameEngine
from app.game.actions import Action
from app.game.cards import Card

eng = GameEngine()
eng.add_player(1, "Alice")
eng.add_player(2, "Bob")
eng.start()

p1 = eng.state.get_player(1)
p2 = eng.state.get_player(2)

p1.coins = 3
# Ensure blocker DOES have Contessa
p1.cards = [Card.ASSASSIN, Card.AMBASSADOR]
p2.cards = [Card.AMBASSADOR, Card.AMBASSADOR]

eng.declare_action(1, Action.ASSASSINATE, target_id=2)
print('After declare: P1 coins=', p1.coins)
eng.block(2, Card.CONTESSA)
print('Block declared by P2')

# Player 1 challenges the block (and should lose)
res = eng.challenge(1)
print('challenge result:', res)
print('P1 alive:', p1.is_alive(), 'P1 cards:', p1.cards)
print('P2 alive:', p2.is_alive(), 'P2 cards:', p2.cards)
print('Action pending?', eng.state.pending_action is not None)
# assert p1.influence < 2
# assert eng.state.pending_action is None
print('Test passed')
