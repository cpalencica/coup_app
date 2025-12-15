from app.game.engine import GameEngine
from app.game.actions import Action


def test_player_can_declare_and_resolve_income():
    """Example test that acts as a player: declares INCOME and resolves it."""
    eng = GameEngine()
    eng.add_player(1, "Alice")
    eng.add_player(2, "Bob")
    eng.start()

    actor = eng.current_player()
    start_coins = actor.coins

    eng.declare_action(actor.id, Action.INCOME)

    # skip challenge/block phases for this simple example
    eng.state.awaiting_challenge = False
    eng.state.awaiting_block = False

    res = eng.resolve()
    assert res == "Action resolved"
    assert actor.coins == start_coins + 1
