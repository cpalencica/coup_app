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
# Ensure blocker does NOT have contessa
p2.cards = [Card.DUKE, Card.ASSASSIN]

print('P2 cards before:', p2.cards)

eng.declare_action(1, Action.ASSASSINATE, target_id=2)
print('After declare: P1 coins=', p1.coins)
eng.block(2, Card.CONTESSA)
print('Block declared by P2')

# Player 1 challenges the block (and should win)
res = eng.challenge(1)
print('challenge result:', res)
print('pending_blocker:', eng.state.pending_blocker)
print('awaiting_challenge_target:', eng.state.awaiting_challenge_target)

# Action should proceed to resolve (no pending block)
res = eng.resolve()
print('resolve:', res)
print('P2 alive:', p2.is_alive(), 'P2 cards:', p2.cards)
assert p1.coins == 0
assert not p2.is_alive() or p2.influence < 2
print('Test passed')
