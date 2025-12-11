import random

from .cards import Card, ALL_CARDS
from .actions import Action
from .player import Player
from .state import GameState
from .exceptions import *


class GameEngine:
    def __init__(self):
        self.state = GameState()

    ###########################################
    # Player + Game Initialization
    ###########################################

    def add_player(self, player_id, name):
        if self.state.deck:
            raise GameNotStartedError("Game already started")
        self.state.players.append(Player(player_id, name))

    def start(self):
        if len(self.state.players) < 2:
            raise GameNotStartedError("Need at least 2 players")

        # Shuffle deck
        self.state.deck = ALL_CARDS.copy()
        random.shuffle(self.state.deck)

        # Deal 2 cards to each player
        for p in self.state.players:
            p.cards = [self._draw_card(), self._draw_card()]

        # Reset turn pointer to the first alive player
        self.state.current_player_idx = 0

    ###########################################
    # Turn and Helpers
    ###########################################

    def current_player(self):
        return self.state.players[self.state.current_player_idx]

    def next_turn(self):
        # advance to next living player
        n = len(self.state.players)
        for _ in range(n):
            self.state.current_player_idx = (self.state.current_player_idx + 1) % n
            if self.current_player().is_alive():
                break

    ###########################################
    # Declare Action
    ###########################################

    def declare_action(self, player_id, action, target_id=None):
        if self.current_player().id != player_id:
            raise NotPlayersTurnError("Not your turn")

        player = self.state.get_player(player_id)
        if player is None:
            raise InvalidActionError("Unknown player")

        target = self.state.get_player(target_id) if target_id else None
        if target_id and target is None:
            raise InvalidActionError("Unknown target player")

        # Check coup coin requirement
        if action == Action.COUP and player.coins < 7:
            raise InvalidActionError("Not enough coins for coup")

        # Force coup if player has 10+ coins
        if player.coins >= 10 and action != Action.COUP:
            raise InvalidActionError("Must coup when having 10+ coins")

        # Store pending action
        self.state.pending_action = action
        self.state.pending_actor = player
        self.state.pending_target = target

        # Determine if challenge is possible
        if action in [Action.TAX, Action.STEAL, Action.ASSASSINATE, Action.EXCHANGE]:
            self.state.awaiting_challenge = True
        else:
            self.state.awaiting_challenge = False

        # Determine if block is possible
        if action in [Action.FOREIGN_AID, Action.STEAL, Action.ASSASSINATE]:
            self.state.awaiting_block = True
        else:
            self.state.awaiting_block = False

        return "Action declared"

    ###########################################
    # Challenge
    ###########################################

    def challenge(self, challenger_id):
        if not self.state.awaiting_challenge:
            raise InvalidActionError("No challenge available")

        challenger = self.state.get_player(challenger_id)
        actor = self.state.pending_actor
        action = self.state.pending_action
        
        # If there is a pending block, the challenge targets the block claim
        if self.state.pending_blocker is not None:
            blocker = self.state.pending_blocker
            required_card = self.state.pending_block_claim

            # Blocker actually has the card -> challenger loses
            if required_card in blocker.cards:
                lost = challenger.lose_card(0)
                self.state.discard.append(lost)

                # Blocker reveals + redraws
                blocker.cards.remove(required_card)
                self.state.discard.append(required_card)
                new_card = self._draw_card()
                blocker.cards.append(new_card)

                # Block is validated
                self.state.pending_block_valid = True
                # block stands; action will be cancelled at resolve
                self.state.awaiting_challenge = False
                return "Challenge failed (challenger lost influence) — block stands"

            else:
                # Blocker loses influence; block fails and action proceeds
                lost = blocker.lose_card(0)
                self.state.discard.append(lost)

                # clear pending block so action can proceed
                self.state.pending_blocker = None
                self.state.pending_block_claim = None
                self.state.pending_block_valid = False
                self.state.awaiting_challenge = False
                return "Challenge successful (block failed) — action continues"

        # Otherwise the challenge targets the actor's claimed card for the action
        required_card = {
            Action.TAX: Card.DUKE,
            Action.STEAL: Card.CAPTAIN,
            Action.ASSASSINATE: Card.ASSASSIN,
            Action.EXCHANGE: Card.AMBASSADOR
        }.get(action, None)

        if required_card is None:
            raise InvalidActionError("This action cannot be challenged")

        # Check if actor actually had the card
        if required_card in actor.cards:
            # Actor wins challenge
            lost = challenger.lose_card(0)
            self.state.discard.append(lost)

            # Actor reveals + redraws the correct card
            actor.cards.remove(required_card)
            self.state.discard.append(required_card)
            new_card = self._draw_card()
            actor.cards.append(new_card)

            # Challenge is resolved — continue to block phase or resolution
            self.state.awaiting_challenge = False

            return "Challenge failed (challenger lost influence)"

        else:
            # Actor loses influence
            lost = actor.lose_card(0)
            self.state.discard.append(lost)

            # End action immediately
            self._cleanup_pending()
            self.next_turn()
            return "Challenge successful (action cancelled)"

    ###########################################
    # Block
    ###########################################

    def block(self, blocker_id, block_type):
        if not self.state.awaiting_block:
            raise InvalidActionError("No block available")

        blocker = self.state.get_player(blocker_id)

        if blocker is None:
            raise InvalidActionError("Unknown blocker")

        # Track block so challenge can target it. Expect `block_type` to be a Card enum value
        self.state.pending_blocker = blocker
        self.state.pending_block_claim = block_type
        self.state.pending_block_valid = None
        self.state.awaiting_block = False
        self.state.awaiting_challenge = True  # other players may challenge the block

        return "Block declared"

    ###########################################
    # Resolve Final Action
    ###########################################

    def resolve(self):
        action = self.state.pending_action
        actor = self.state.pending_actor
        target = self.state.pending_target

        # If a block was declared and still stands (or hasn't been cleared), cancel action
        if self.state.pending_blocker is not None:
            # If block exists and wasn't invalidated by a successful challenge, treat as blocked
            # (if pending_blocker was cleared by a challenge, this will be None and action proceeds)
            self._cleanup_pending()
            self.next_turn()
            return "Action blocked"

        # Income
        if action == Action.INCOME:
            actor.coins += 1

        # Foreign Aid
        elif action == Action.FOREIGN_AID:
            actor.coins += 2

        # Coup
        elif action == Action.COUP:
            actor.coins -= 7
            lost = target.lose_card(0)
            self.state.discard.append(lost)

        # Tax
        elif action == Action.TAX:
            actor.coins += 3

        # Assassinate
        elif action == Action.ASSASSINATE:
            actor.coins -= 3
            lost = target.lose_card(0)
            self.state.discard.append(lost)

        # Steal
        elif action == Action.STEAL:
            stolen = min(2, target.coins)
            target.coins -= stolen
            actor.coins += stolen

        # Exchange
        elif action == Action.EXCHANGE:
            new_cards = [self._draw_card(), self._draw_card()]
            actor.cards.extend(new_cards)
            # For now player keeps first two they pick — keep simple
            while len(actor.cards) > 2:
                c = actor.cards.pop()  # discard extras
                self.state.discard.append(c)

        # Cleanup
        self._cleanup_pending()
        self.next_turn()

        return "Action resolved"

    ###########################################
    # Utility
    ###########################################

    def _draw_card(self):
        # Draw a card from deck; if deck empty, reshuffle discard into deck
        if not self.state.deck:
            if self.state.discard:
                self.state.deck = self.state.discard.copy()
                self.state.discard.clear()
                random.shuffle(self.state.deck)
            else:
                raise InvalidActionError("No cards left to draw")
        return self.state.deck.pop()

    def _cleanup_pending(self):
        self.state.pending_action = None
        self.state.pending_actor = None
        self.state.pending_target = None
        self.state.awaiting_challenge = False
        self.state.awaiting_block = False
        self.state.block_type = None
        # clear block-specific pending state
        self.state.pending_blocker = None
        self.state.pending_block_claim = None
        self.state.pending_block_valid = None
