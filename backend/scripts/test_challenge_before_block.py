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
# Ensure actor has no assassin to be challenged
p1.cards = [Card.DUKE, Card.CAPTAIN]

print('P1 cards before:', p1.cards)

eng.declare_action(1, Action.ASSASSINATE, target_id=2)
print('After declare: P1 coins=', p1.coins)

# Player 2 challenges the actor immediately (before blocking)
res = eng.challenge(2)
print('challenge result:', res)
print('Action pending?', eng.state.pending_action is not None)
print('P1 alive?:', p1.is_alive())
assert eng.state.pending_action is None
print('Test passed')
