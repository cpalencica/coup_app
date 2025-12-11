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
            p.cards = [self.state.deck.pop(), self.state.deck.pop()]

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
        target = self.state.get_player(target_id) if target_id else None

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

        required_card = {
            Action.TAX: Card.DUKE,
            Action.STEAL: Card.CAPTAIN,
            Action.ASSASSINATE: Card.ASSASSIN,
            Action.EXCHANGE: Card.AMBASSADOR
        }[action]

        # Check if actor actually had the card
        if required_card in actor.cards:
            # Actor wins challenge
            challenger_card_idx = 0  # for now force first card
            lost = challenger.lose_card(challenger_card_idx)
            self.state.discard.append(lost)

            # Actor reveals + redraws the correct card
            actor.cards.remove(required_card)
            self.state.discard.append(required_card)
            new_card = self.state.deck.pop()
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

        # Track block so challenge can target it
        self.state.block_type = block_type
        self.state.awaiting_block = False
        self.state.awaiting_challenge = True  # you can challenge the block

        return "Block declared"

    ###########################################
    # Resolve Final Action
    ###########################################

    def resolve(self):
        action = self.state.pending_action
        actor = self.state.pending_actor
        target = self.state.pending_target

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
            new_cards = [self.state.deck.pop(), self.state.deck.pop()]
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

    def _cleanup_pending(self):
        self.state.pending_action = None
        self.state.pending_actor = None
        self.state.pending_target = None
        self.state.awaiting_challenge = False
        self.state.awaiting_block = False
        self.state.block_type = None
