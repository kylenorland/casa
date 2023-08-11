#Head Material
#leftPorts=0
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 3/16/23
Description: Basic Random Policy
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
from collections import deque
import datetime
import numpy as np
import random

#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = []
pubTopics = ['cats']
blockName = "source--"


logfile = open("blockLogs/random_policy.txt", "w")
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

#-------------------------------------------------
#----------------Class Definition-----------------
class Random_Policy:
    def __init__(self, blockName):
        self.blockName = blockName
        self.initialized = False
        self.q_table_initialized = False
        print("initializing q_policy")  
    
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
        #def load_run_details(self, run, env):
    
    def init_run_details(self, run):
        #Init the environment
        self.run = run
        
        #Init settings
        for k, v in run.items():
            setattr(self, k, v)  

        self.initialized = True             
        
        #self.hp_struct = {'policy_objects': []}
        

    def get_action(self, signal):
        #Init the Q_table
        self.n_observations = signal['env_details']['n_observations']
        self.n_actions = signal['env_details']['n_actions']
        
        #Pick a random number in the range of actions (only works for 1d ones right now)
        return random.randint(0, self.n_actions-1)
    
    def update_policy(self, signal):
        pass
                    
    def handle_messages(self):
        #print("Preparing to poll")
        #----Poll-------------
        socks = dict(self.poller.poll(500))
        #print("socks", socks)
        
        #-----Read In--------
        for socket in socks:
            topic = socket.recv_string()
            message = socket.recv_json()

            #-------------Pre-Init Actions---------------
            if topic == "commandChain":
                if message['command'] == 'stop':
                #Shut down.
                    keepRunning = False
                    print("Generator shutting down")
            
            if message['tag'] == 'init_details':
                self.run = json.loads(message['signal']['run'])
                #print('recieved init details')

                #Set up run
                print("random_policy initializing run")
                self.init_run_details(self.run)
                self.initialized = True
                    
            #-------------Post Init Actions----------------------
            if self.initialized:
                tag = message['tag']
                signal = message['signal']
                if message['tag'] =='state':
                    #print('random_policy recieved state')
                    
                    #print("random policy responding to state")
                    #Convert the action to an int
                    action = int(self.get_action(signal))
                    
                    #Reply with suggested action
                    out_message = {"tag": "action", "signal": {'action': action, 'policy_name': 'random_policy'}}
                    
                    if self.run['debug_mode']: print(self.blockName, 'sending', out_message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message) 
                    
                if message['tag'] == 'update':
                    #print('random_policy recieved update message')
                    #print(signal)
                    
                    self.update_policy(signal)
                    
                    
#------------Initialize
random_policy = Random_Policy(blockName)

#----------------------Init zmq-------------------------          
random_policy.init_zmq(subTopics, pubTopics)

#-------------Run Loop--------------------
i = 0
print(random_policy.blockName, "starting")
keepRunning = True
while keepRunning:
    random_policy.handle_messages()
