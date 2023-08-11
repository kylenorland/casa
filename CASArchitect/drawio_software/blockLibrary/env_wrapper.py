#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 3/14/23
Description: environment wrapper for CASA
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
from collections import deque
import vector_grid_goal         #Custom environment
import gym                      #Support for RL environment.
import numpy as np

#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = []
pubTopics = ['cats']
blockName = "source--"


logfile = open("blockLogs/env_wrapper.txt", "w")
logfile.write("Got to here")
#------------------
#--Pull arguments--
#------------------
numArgs = len(sys.argv)
print("There are " + str(numArgs) + " arguments")

if numArgs >= 3:
    proxyInputPort = int(sys.argv[1])
    proxyOutputPort = int(sys.argv[2])
    stringArchitecture = sys.argv[3]
    try:
        print(stringArchitecture)
        jsonArch = json.loads(stringArchitecture)
        subTopics = jsonArch['subTopics']
        pubTopics = jsonArch['pubTopics']
        blockName = jsonArch['blockName']
    except:
        print("Something in the json loading process broke")
#------------------



#------------------------------------------------
#--------------Declare the class and helper functions-----------------
#------------------------------------------------    
    
class Env_Wrapper:
    def __init__(self, blockName):
        self.blockName = blockName
        self.initialized = False

        print("initializing policy orc")  
    def init_zmq(self, subTopics, pubTopics):
        self.context = zmq.Context()
        self.subTopics = subTopics
        self.pubTopics = pubTopics

        self.pubSocket = self.context.socket(zmq.PUB)
        self.pubSocket.connect("tcp://127.0.0.1:" + str(proxyInputPort))

        self.subSocket = self.context.socket(zmq.SUB)
        self.subSocket.connect("tcp://127.0.0.1:" + str(proxyOutputPort))

        #------------Subscribe to general topics---------------------
        for subTopic in self.subTopics:
            self.subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())

        #--------------Subscribe to the command chain.----------------
        subTopic = 'commandChain'
        self.subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())

        #-----------------Set up poller------------------------- 
        #(Some code from: https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/multisocket/zmqpoller.html)
        self.poller = zmq.Poller()
        self.poller.register(self.subSocket, zmq.POLLIN)    

    
    def init_run_details(self):
        #Init the environment
        self.env = self.init_environment(self.run['env_config'])
        
        self.state = self.env.reset()
        print("initialized state is ", self.state)
        self.done = False
        self.episode_reward = 0
        
        self.prev_run = []
        self.prev_first = 0
        self.prev_last = 0
        self.initialized = True
        
    def init_environment(self, env_config):
        print("Env wrapper initializing environment")
        env_name = env_config['env_name']
        
        if env_name == 'FrozenLake-v1':
            env = gym.make("FrozenLake-v1", desc=None, map_name="4x4", is_slippery=env_config['is_slippery'])
            #env = gym.make("FrozenLake-v1", is_slippery=False)
        
        if env_name == 'vector_grid_goal':
            grid_dims = (7,7)
            player_location = (0,0)
            goal_location = (6,6)
            custom_map = np.array([[0,1,1,1,0,0,0],
                                    [0,0,1,0,0,1,0],
                                    [0,0,0,0,0,0,1],
                                    [0,0,0,0,0,0,0],
                                    [0,0,0,0,0,0,1],
                                    [0,0,0,0,0,0,0],
                                    [0,0,0,0,0,0,0]])
        
            #env = vector_grid_goal.CustomEnv(grid_dims=grid_dims, player_location=player_location, goal_location=goal_location, map=custom_map)
            self.env = vector_grid_goal.CustomEnv(grid_dims=env_config['grid_dims'], player_location=env_config['player_location'], goal_location=env_config['goal_location'], map=np.asarray(env_config['env_map']))

        return self.env     

    def handle_messages(self):
        #print("Preparing to poll")
        #----Poll-------------
        socks = dict(self.poller.poll(500))
        #print("socks", socks)
        
        #-----Read In--------
        for socket in socks:
            topic = socket.recv_string()
            message = socket.recv_json()
            tag = message['tag']
            signal = message['signal']

        #-------------Pre Init Actions Available----------------------
            if topic == "commandChain":
                if message['command'] == 'stop':
                #Shut down.
                    keepRunning = False
                    print("Generator shutting down")
            
            if message['tag'] == 'init_details':
                self.run = json.loads(message['signal']['run'])
                #Set up run
                print("env_wrapper initializing run")
                self.init_run_details()
                self.initialized = True
                    
            #--------------Post Init Actions Available------------------
            if self.initialized:    
                #-------------Respond to request for state--------------------
                if message['tag'] == 'state_request':
                    
                    #Send state back
                    signal = {
                    'state': self.state,
                    'env_details': {
                    'n_observations':  self.env.observation_space.n,
                    'n_actions': self.env.action_space.n,
                    }
                    }
                    
                    out_message = {"tag": "state", "signal": signal }
                    
                    if self.run['debug_mode']: print(self.blockName, 'sending', out_message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message) 
                    
                #---------------Run action-------------------
                if message['tag'] == 'action':
                    #print('env wrapper recieved action')
                    #print(tag, signal)
                    
                    #Respond to the action
                    #Run the action on the environment.
                    
                    #------------RUN ACTION--------------------
                    action = signal['action']
                    #print("Env taking action", action)
                    next_state, reward, done, _ = self.env.step(int(action))
                    
                    #-------------Send Updated State after Action is Run-----------------
                    update_info = {}
                    update_info['state'] = int(self.state)
                    update_info['action'] = int(action)
                    update_info['next_state'] = int(next_state)
                    update_info['reward'] = reward
                    update_info['done'] = done
                    
                    signal = {'update_info': update_info}
                    
                    #Send out a state_update
                    out_message = {"tag": "update", "signal": signal }
                    
                    if self.run['debug_mode']: print(self.blockName, 'sending', out_message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message) 
                    
                    #Update state
                    self.state = int(next_state)
                    
                    '''
                    #Reset if done?
                    if done:
                        self.state = int(env.reset())
                    '''
                        
                if message['tag'] == 'env_reset':
                    #Reset env
                    self.state = int(self.env.reset())

#---------------------Initialize -----------------------
#Init Core
env_wrapper = Env_Wrapper(blockName) 

#Init zmq               
env_wrapper.init_zmq(subTopics, pubTopics)

#Init unique components.

#----------------------Run loop---------------------------
i = 0
print(env_wrapper.blockName, "starting")
keepRunning = True
while keepRunning:
    env_wrapper.handle_messages()
