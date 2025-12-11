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

        # Whether we are waiting for challenge/block resolution
        self.awaiting_challenge = False
        self.awaiting_block = False
        self.block_type = None

    def get_player(self, player_id):
        for p in self.players:
            if p.id == player_id:
                return p
        return None
