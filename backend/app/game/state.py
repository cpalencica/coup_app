class GameState:
    def __init__(self):
        self.players = []
        self.deck = []
        self.discard = []

        # turn
        self.current_player_idx = 0

        # Pending action pipeline
        self.pending_action = None
        self.pending_actor = None
        self.pending_target = None

        # Pending block information
        self.pending_blocker = None
        # claim for block (Card enum) — what the blocker claims they have
        self.pending_block_claim = None
        # whether the declared block was validated by a challenge (True), invalidated (False), or not-yet-resolved (None)
        self.pending_block_valid = None

        # Whether we are waiting for challenge/block resolution
        self.awaiting_challenge = False
        self.awaiting_block = False
        self.block_type = None
        # Which entity is currently being challenged: 'actor' or 'block' or None
        self.awaiting_challenge_target = None

    def get_player(self, player_id):
        for p in self.players:
            if p.id == player_id:
                return p
        return None
