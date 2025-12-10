'''
keep track of player information and state
'''

class Player:
    def __init__(self, player_id, name):
        self.id = player_id
        self.name = name
        self.cards = []
        self.coins = 2
        self.alive = True

    def lose_card(self, index):
        return self.cards.pop(index)