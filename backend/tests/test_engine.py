import pytest

from app.game.engine import GameEngine
from app.game.actions import Action
from app.game.cards import Card, ALL_CARDS
from app.game.exceptions import InvalidActionError, GameNotStartedError, NotPlayersTurnError


def make_engine_with_players(n=2):
    eng = GameEngine()
    for i in range(1, n + 1):
        eng.add_player(i, f"p{i}")
    eng.start()
    return eng


def test_start_deals_two_cards_each_and_sets_deck():
    eng = make_engine_with_players(2)
    assert len(eng.state.players) == 2
    for p in eng.state.players:
        assert len(p.cards) == 2
    # ALL_CARDS has 15 entries; dealing 4 cards leaves 11
    assert len(eng.state.deck) == len(ALL_CARDS) - 4


def test_income_action_adds_one_coin_and_advances_turn():
    eng = make_engine_with_players(2)
    actor = eng.state.players[eng.state.current_player_idx]
    start_coins = actor.coins

    eng.declare_action(actor.id, Action.INCOME)
    res = eng.resolve()

    assert res == "Action resolved"
    assert actor.coins == start_coins + 1
    # turn advances to next living player
    assert eng.state.current_player_idx != 0


def test_steal_transfers_coins_when_uncontested():
    eng = make_engine_with_players(2)
    actor = eng.state.players[0]
    target = eng.state.players[1]

    # set deterministic coins
    actor.coins = 0
    target.coins = 2

    eng.state.current_player_idx = 0
    eng.declare_action(actor.id, Action.STEAL, target.id)

    # bypass challenge/block phases for this test
    eng.state.awaiting_challenge = False
    eng.state.awaiting_block = False

    res = eng.resolve()
    assert res == "Action resolved"
    assert actor.coins == 2
    assert target.coins == 0


def test_challenge_against_tax_when_actor_has_no_duke_causes_actor_to_lose_and_cancel():
    eng = make_engine_with_players(2)
    actor = eng.state.players[0]
    challenger = eng.state.players[1]

    # make sure actor does NOT have a Duke
    actor.cards = [Card.CAPTAIN, Card.AMBASSADOR]

    eng.state.current_player_idx = 0
    eng.declare_action(actor.id, Action.TAX)

    # challenger performs challenge
    msg = eng.challenge(challenger.id)
    assert "Challenge successful" in msg
    # actor should have lost one influence
    assert actor.influence == 1
    # pending action cleaned up and turn advanced
    assert eng.state.pending_action is None


def test_block_claim_validated_causes_challenger_to_lose_and_action_blocked():
    # actor (1) assassinates target (2); target blocks with Contessa and challenger (3) challenges
    eng = make_engine_with_players(3)
    actor = eng.state.players[0]
    target = eng.state.players[1]
    challenger = eng.state.players[2]

    eng.state.current_player_idx = 0

    # prepare cards so target actually has a Contessa to validate block
    target.cards = [Card.CONTESSA, Card.AMBASSADOR]
    actor.cards = [Card.ASSASSIN, Card.DUKE]
    challenger.cards = [Card.CAPTAIN, Card.AMBASSADOR]

    eng.declare_action(actor.id, Action.ASSASSINATE, target.id)

    # target declares block with Contessa
    eng.block(target.id, Card.CONTESSA)

    # challenger challenges the block
    msg = eng.challenge(challenger.id)
    assert "challenger lost" in msg or "Challenge failed" in msg

    # resolve should then treat the action as blocked
    res = eng.resolve()
    assert res == "Action blocked"
    # challenger should have lost one influence (card)
    assert challenger.influence == 1


def test_start_requires_two_players():
    eng = GameEngine()
    with pytest.raises(GameNotStartedError):
        eng.start()


def test_not_players_turn_raises():
    eng = make_engine_with_players(2)
    other = eng.state.players[(eng.state.current_player_idx + 1) % 2]
    with pytest.raises(NotPlayersTurnError):
        eng.declare_action(other.id, Action.INCOME)


def test_coup_requires_7_coins():
    eng = make_engine_with_players(2)
    actor = eng.state.players[eng.state.current_player_idx]
    actor.coins = 6
    target = eng.state.players[1]
    with pytest.raises(InvalidActionError):
        eng.declare_action(actor.id, Action.COUP, target.id)


def test_forced_coup_at_10_coins():
    eng = make_engine_with_players(2)
    actor = eng.state.players[0]
    actor.coins = 10
    with pytest.raises(InvalidActionError):
        eng.declare_action(actor.id, Action.INCOME)


def test_coup_reduces_coins_and_target_loses():
    eng = make_engine_with_players(2)
    actor = eng.state.players[0]
    target = eng.state.players[1]
    actor.coins = 7
    eng.state.current_player_idx = 0
    eng.declare_action(actor.id, Action.COUP, target.id)
    eng.state.awaiting_challenge = False
    eng.state.awaiting_block = False
    prev_influence = target.influence
    res = eng.resolve()
    assert res == "Action resolved"
    assert actor.coins == 0
    assert target.influence == prev_influence - 1


def test_deck_reshuffle_on_empty_deck_during_exchange():
    eng = make_engine_with_players(2)
    actor = eng.state.players[eng.state.current_player_idx]
    eng.state.deck = []
    eng.state.discard = [Card.DUKE, Card.CAPTAIN]
    eng.declare_action(actor.id, Action.EXCHANGE)
    eng.state.awaiting_challenge = False
    eng.state.awaiting_block = False
    res = eng.resolve()
    assert res == "Action resolved"
    assert actor.influence == 2


def test_next_turn_skips_dead_players():
    eng = make_engine_with_players(3)
    eng.state.players[1].cards = []
    eng.state.players[1].alive = False
    eng.state.current_player_idx = 0
    eng.next_turn()
    assert eng.state.current_player_idx == 2


def test_challenge_actor_has_card_challenger_loses():
    eng = make_engine_with_players(2)
    actor = eng.state.players[0]
    challenger = eng.state.players[1]
    actor.cards = [Card.DUKE, Card.CAPTAIN]
    eng.state.current_player_idx = 0
    eng.declare_action(actor.id, Action.TAX)
    msg = eng.challenge(challenger.id)
    assert "challenger lost" in msg or "Challenge failed" in msg
    assert challenger.influence == 1
