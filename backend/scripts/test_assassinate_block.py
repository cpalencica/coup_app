import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.game.engine import GameEngine
from app.game.actions import Action
from app.game.cards import Card

# Simulate: player1 assassinates player2, player2 blocks with Contessa, no challenges
eng = GameEngine()
eng.add_player(1, "Alice")
eng.add_player(2, "Bob")
eng.start()

# Ensure player 1 has enough coins
p1 = eng.state.get_player(1)
p2 = eng.state.get_player(2)

p1.coins = 3

# Player 1 declares assassinate on player 2
msg = eng.declare_action(1, Action.ASSASSINATE, target_id=2)
print("declare_action:", msg)
print(f"After declare: P1 coins={p1.coins}")

# Player 2 blocks with Contessa
msg = eng.block(2, Card.CONTESSA)
print("block:", msg)

# No one challenges the block -> block stands; cancel action
msg = eng.cancel_action()
print("cancel_action:", msg)

print(f"After block resolves: P1 coins={p1.coins}, P2 alive={p2.is_alive()}, P2 cards={p2.cards}")

# Assertions
assert p1.coins == 0, "Player 1 should have spent 3 coins even if blocked"
assert p2.is_alive(), "Player 2 should still be alive (block succeeded)"
print('Test passed')
