#Author: Kyle Norland
#Date: 5/24/22
#Purpose: Create a grid environment for a box to move to a goal
# box. Designed for either a vector or a dnn to solve.



#------------Imports----------------
import os
os.environ['SDL_AUDIODRIVER'] = 'dsp'
#import pygame
import numpy as np
import random
import math
import time
from copy import deepcopy

from gym import Env
from gym.spaces import Box, Discrete
#from stable_baselines3 import DQN


#--------------Global Controls---------------------
goal_reward_val = 20
regular_reward_val = 10
step_cost = 0

class CustomEnv(Env):
    #--------------------Properties-----------------------
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 10}

    #----------------------Methods------------------------
    def __init__(self, grid_dims = (-1,-1), player_location = (-1,-1), goal_location = (-1,-1), map='random'):
        #Colors
        self.white = (255,255,255)
        self.black = (0,0,0)
        self.bright_blue = (0, 255, 255)
        self.red = (255, 0, 0)

        #Set window dimensions
        self.width = 500
        self.height = 500

        #Set up screen and clock
        self.screen = None
        self.clock = None
        self.isopen = True


        #Play field
        #Grid Dimensions
        if grid_dims[0] == -1 and player_location[1] == -1:
            self.field_width = 10
            self.field_height = 10
        else:
            self.field_width = grid_dims[0] 
            self.field_height = grid_dims[1]
            
        self.field = np.zeros((self.field_width, self.field_height))
        
        #Randomly add rewards to map
        reward_percentage = 0.2
        if map == 'random':
            indices = np.random.choice(np.arange(self.field.size), replace=False,
                               size=int(self.field.size * reward_percentage))
            self.field[np.unravel_index(indices, self.field.shape)] = 1
        
        else:
            self.field = map
            
        #print("Field")
        #print(self.field)
        
        #Make backup
        self.run_base_field = deepcopy(self.field)  #Gets refreshed on restart
        self.base_field = deepcopy(self.field)      #Stays the same
        
        
        #Player Location
        if player_location[0] == -1 and player_location[1] == -1:
            self.base_player_x = 0  
            self.base_player_y = 0
        else:
            self.base_player_x = player_location[0] 
            self.base_player_y = player_location[1] 
        
        self.player_x = self.base_player_x
        self.player_y = self.base_player_y
        
        
        #Goal Location
        if goal_location[0] == -1 and goal_location[1] == -1:
            self.base_goal_x = self.field_width - 1   
            self.base_goal_y = self.field_height - 1
        else:
            self.base_goal_x = goal_location[0] 
            self.base_goal_y = goal_location[1] 
            
        self.goal_x = self.base_goal_x
        self.goal_y = self.base_goal_y

        #Block size
        self.block_size = math.floor(self.width / self.field_width)

        #Define spaces
        self.observation_space = Discrete(self.field_width * self.field_height)
        self.num_actions = 4
        self.action_space = Discrete(self.num_actions)        

    def step(self, action):
        #----------Hardcoded Action------------
        if action > self.num_actions - 1 or action < 0:
            print("Can't do this")
            raise Exception("Action out of range")

        #Calculate Next State
        player_move_x = 0
        player_move_y = 0
        
        if action == 0: player_move_x = -1  #Left
        elif action == 1: player_move_y = -1 #Up
        elif action == 2: player_move_x = +1 #Right
        elif action == 3: player_move_y = +1 #Down
        else: print("No action")
        
        self.player_x = self.player_x + player_move_x
        self.player_y = self.player_y + player_move_y
        
        #Ensure player is in bounds
        if self.player_x > self.field_width-1: self.player_x = self.field_width-1
        if self.player_x < 0: self.player_x = 0
        if self.player_y > self.field_height-1: self.player_y = self.field_height-1
        if self.player_y < 0: self.player_y = 0
       
       
       #Update the state of the graphics
       #Just plain white blocks for now
        for i in range(0, self.field.shape[0]):
            for j in range(0, self.field.shape[1]):
                if ((i == self.player_x and j == self.player_y) or
                    (i == self.goal_x and j == self.goal_y)
                    ):
                    self.field[i,j] = 2
                else:
                    self.field[i,j] = self.run_base_field[i,j]
        
        #Determine rewards and done
        global goal_reward_val
        global regular_reward_val
        global step_cost
        
        #Goal Found
        if (self.player_x == self.goal_x and
            self.player_y == self.goal_y
            ):
            reward = goal_reward_val
            done = True
        else: 
            #Give reward from base state if non-zero
            if self.run_base_field[self.player_y][self.player_x] != 0:
                 reward = regular_reward_val
            else: 
                reward = 0

            self.run_base_field[self.player_y][self.player_x] = 0
            done = False
        
        #Decrement with step cost
        reward = reward - step_cost
        
        #Return info to the player
        #Todo return as single number. From the bottom up vectorized.
        #print('----')
        #print("Base field")
        #print(self.run_base_field)
        self.state = int((self.player_y * self.field_width) + self.player_x)
        #print("x", self.player_x, " y: ", self.player_y, "state ", self.state, "reward", reward)
        #print("The reward returned is: ", reward)
        return np.array(self.state), reward, done, {}
            
        #(self.state, dtype=np.float32)
            
            
    def render(self, mode="human"):
        #Note: This might be temporary once the main grid can
        #just be rendered directly from array to image.
        #Make sure pygame is imported
       
        #Initialize pygame stuff if not already set up
        try:
            import pygame
            from pygame import gfxdraw
        except ImportError:
            raise DependencyNotInstalled(
                "pygame is not installed, run `pip install gym[classic_control]`"
            )    

        if self.screen is None:
            pygame.init()
            pygame.display.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            #Set caption
            pygame.display.set_caption("Grid goal game")
            
        if self.clock is None:
            self.clock = pygame.time.Clock()
        
        
        
       #-------------Handle Events------------------
        for event in pygame.event.get():
            # stops program when red x clicked
            if event.type == pygame.QUIT:
                pygame.quit()         
        
        #------------Draw the environment------------
        #Clear screen
        self.screen.fill(self.black)
        
        #Draw the rendered screen from the field state.
        #print("Field pre_render")
        #print(self.field)
        for i in range(0, self.field_width):
            for j in range(0, self.field_height):
                #Remember that graphics squares are upside down.
                #Draw a black square if 0, white square if 1
                #Blue for player
                square_color = self.black
                if self.field[i,j] == 1: square_color = self.red
                if self.field[i,j] == 2: square_color = self.white
                    
                pygame.draw.rect(self.screen, square_color, (i * self.block_size, self.height - (j* self.block_size) - self.block_size, self.block_size, self.block_size))
        
        
        #Render to pygame screen or to an array depending one mode.
        if mode == "human":
            pygame.event.pump()
            self.clock.tick(self.metadata["render_fps"])
            pygame.display.flip()
 
        if mode == "rgb_array":
            return np.transpose(
                np.array(pygame.surfarray.pixels3d(self.screen)), axes=(1, 0, 2)
            )
        else:
            return self.isopen
    
    def reset(self):
        #TODO Change player location, and return as single number.
        #print("resetting")
        
        #Reset player location to the original position.
        self.player_x = self.base_player_x #int(self.field_width / 2)
        self.player_y = self.base_player_y #int(self.field_height / 2)
        
        #Reset the goal location to the upper right corner
        #Note: Could be random in the future
        self.goal_x = self.base_goal_x
        self.goal_y = self.base_goal_y
        
        #Reset the base field (resources)
        self.run_base_field = deepcopy(self.base_field)
        
        #Return the state of the player
        self.state = int((self.player_y * self.field_width) + self.player_x)
        return self.state
        
#-----------------------------------
#---------------MAIN----------------
#-----------------------------------
#Initialize pygame





#-----------------------------------
#--------------Run Loop-------------
#-----------------------------------
"""
#Initialize pygame
pygame.init()

#Initialize the object
env = CustomEnv()


keep_running = True
for i in range(0,20):
    #Check for exit
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            keep_running = False
    
    
    if(keep_running):
        env.step()
        env.render()
        time.sleep(1)
"""  
    
