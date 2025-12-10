import random
from .cards import ALL_CARDS, Card
from .actions import Action
from .player import Player
from .state import GameState
from .exceptions import *

class GameEngine:
    def __init__(self):
        self.state = GameState()

    def add_player(self, player_id, name):
        if self.state.deck:
            raise GameNotStartedError("Cannot add players after the game starts")
        self.state.players.append(Player(player_id, name))

    def start(self):
        # create + shuffle deck
        self.state.deck = ALL_CARDS.copy()
        random.shuffle(self.state.deck)

        # deal 2 cards to each player
        for player in self.state.players:
            player.cards = [self.state.deck.pop(), self.state.deck.pop()]

    def declare_action(self, player_id, action, target_id=None):
        # validate turn, validate action
        # set pending_action, pending_actor, pending_target
        pass

    def challenge(self, challenger_id):
        # resolve challenge
        pass

    def block(self, blocker_id, block_type):
        # resolve block
        pass

    def resolve(self):
        # actually apply the effects of the action
        pass
