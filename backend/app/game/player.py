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
        card = self.cards.pop(index)
        # update alive flag
        if len(self.cards) == 0:
            self.alive = False
        return card
    
    def add_coins(self,coins_added):
        self.coins += coins_added  
    
    def add_card(self,card):
        self.cards.append(card)
    
    @property
    def influence(self):
        return len(self.cards)
    
    def is_alive(self):
        return self.influence > 0
    
