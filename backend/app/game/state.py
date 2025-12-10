class GameState:
    def __init__(self):
        self.players = []
        self.deck = []
        self.discard = []
        self.current_player_idx = 0

        # Pending action system
        self.pending_action = None
        self.pending_actor = None
        self.pending_target = None
        self.pending_challenge = None