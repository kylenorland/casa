#Head Material
#leftPorts=0
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 3/15/23
Description: Basic Greedy Q Policy
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

#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = []
pubTopics = ['cats']
blockName = "source--"


logfile = open("blockLogs/policy_orchestrator.txt", "w")
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
class Q_Policy:
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
        
    def init_q_table(self, env_details):
        #Init the Q_table
        self.n_observations = env_details['n_observations']
        self.n_actions = env_details['n_actions']
        self.Q_table = np.zeros((self.n_observations,self.n_actions))
        
    def get_action(self, state):
        return np.argmax(self.Q_table[state,:])
    
    def update_policy(self, signal):
        #print('updating')
        #print(message)
        #Get pieces out of message
        update_info = signal['update_info']
        state = update_info['state']
        action = update_info['action']
        next_state = update_info['next_state']
        reward = update_info['reward']
        done = update_info['done']
    
        #Update Q_table
        self.Q_table[state, action] = self.Q_table[state, action] + self.lr*(reward + self.gamma*max(self.Q_table[next_state,:]) - self.Q_table[state, action])  
        '''
        #Print Q Table
        print("Q table")
        np.set_printoptions(precision=4)
        np.set_printoptions(floatmode = 'fixed')
        np.set_printoptions(sign = ' ')
        for i, row in enumerate(self.Q_table):
            row_print = "{0:<6}{1:>8}".format(i, str(row))
            #print(i, ':', row)
            print(row_print)
        
        input("Stop")
        '''    
                    
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

                if not self.initialized:
                    #Set up run
                    print("q_policy initializing run")
                    self.init_run_details(self.run)
                    self.initialized = True
                    
            #-------------Post Init Actions----------------------
            if self.initialized:
                tag = message['tag']
                signal = message['signal']
                if message['tag'] =='state':
                    print('q_policy recieved state')
                    
                    
                    #Initialize q table if not done already
                    if not self.q_table_initialized:
                        self.init_q_table(signal['env_details'])
                    
                    print("q responding to state")
                    #Convert the action to an int
                    action = int(self.get_action(signal['state']))
                    
                    #Reply with suggested action
                    out_message = {"tag": "action", "signal": {'action': action, 'policy_name': 'q_policy'}}
                    
                    print(self.blockName, 'sending', out_message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message) 
                    
                if message['tag'] == 'update':
                    print('q_policy recieved update message')
                    print(signal)
                    self.update_policy(signal)
                    
                    
#------------Initialize
q_policy = Q_Policy(blockName)

#----------------------Init zmq-------------------------          
q_policy.init_zmq(subTopics, pubTopics)

#-------------Run Loop--------------------
i = 0
print(q_policy.blockName, "starting")
keepRunning = True
while keepRunning:
    q_policy.handle_messages()
