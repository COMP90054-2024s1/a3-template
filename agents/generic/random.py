from template import Agent
import random


class myAgent(Agent):
    def __init__(self,_id):
        super().__init__(_id)
    
    def SelectAction(self,actions,game_state):
        print(actions)
        # print(game_state)
        return random.choice(actions)
