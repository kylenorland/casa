#Head Material
#leftPorts=0
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 3/14/23
Description: Policy manager
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
import random

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
class Orc:
    def __init__(self, blockName):
        self.blockName = blockName
        self.initialized = False
        self.e = 0
        self.i_counter = 0
        print("initializing policy orc")
        #self.episode_reward = 0
        #self.global_rewards = 
    
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
        self.run = run
        #Init the environment
        #self.env = init_environment(run['env_config'])
        
        #Init the correct stochastic policy
        if self.run['hyperpolicy'] == 'a_stochastic':
            print("Using stochastic hyperpolicy")
            self.init_action_stochastic_hp()    
        #self.init_random_hp()
        
        self.initialized = True
        
        #self.hp_struct = {'policy_objects': []}
        
    def init_random_hp(self):
        #Policy response list
        self.prl = []
        self.prl.append({'name': 'q_policy', 'received': False, 'action':None})
        self.prl.append({'name': 'random_policy', 'received': False, 'action':None})
        
    def run_random_hp(self, message):
        tag = message['tag']
        signal = message['signal']
        
        if tag == 'action':
            #Add, check if both present, choose randomly.
            for policy in self.prl:
                if policy['name'] == signal['policy_name']:
                    policy['received'] = True
                    policy['action'] = signal['action']
            
            all_received = True
            for policy in self.prl:
                if not policy['received']:
                    all_received = False
                    
            if all_received:
                #print("hp got all policy responses")
                #Choose randomly
                chosen_policy = random.choice(self.prl)
                action = chosen_policy['action']
                
                #Send the signal on to the env_wrapper.
                out_signal = {'action': action}
                                    
                out_message = {"tag": "action", "signal": out_signal}
                
                #print(self.blockName, 'sending', out_message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message)

                #Reset the policy received flags
                for policy in self.prl:
                    policy['received'] = False
                    
    def init_action_stochastic_hp(self):
        #Get first hp struct from run details
        self.hp_struct = self.run['hp_struct']
        
        #Set up policy response list.
        self.prl = []
        
        for entry in self.hp_struct['policy_objects']:
            self.prl.append({'name': entry['policy_name'], 'received': False, 'action':None})
        
        #Print prl
        #print('policy response list')
        #print(self.prl)

            
    def run_action_stochastic_hp(self, message):
        #print('in action stochastic hp')
        #print(message)
        tag = message['tag']
        signal = message['signal']
        
        #print("prl", self.prl)
        
        #Working with prl which manages communication
        #and hp_struct, which holds details for decision.
        
        if tag == 'action':
            #Add, check if both present, choose randomly.
            for policy in self.prl:
                if policy['name'] == signal['policy_name']:
                    policy['received'] = True
                    policy['action'] = signal['action']
            
            #Check if all received (Add timer?)
            all_received = True
            for policy in self.prl:
                if not policy['received']:
                    all_received = False
            
            #If all received
            if all_received:
                #print("hp got all policy responses")
                #Choose according to hyperpolicy (Weighted random in this case)
                #Calculate probabilities of each policy
                prob_array = [x['prob_trajectory'][self.e] for x in self.hp_struct['policy_objects']]
                
                if self.run['debug_mode']: print('prob_array',  prob_array)
                
                #Choose the policy randomly
                chosen_policy_object = random.choices(self.hp_struct['policy_objects'], prob_array)[0] #First one in returned list
                chosen_policy_name = chosen_policy_object['policy_name']
                
                #Get it from the prl
                chosen_prl_policy = next(item for item in self.prl if item['name'] == chosen_policy_name)
                
                
                action = chosen_prl_policy['action']
                
                if self.run['debug_mode']: print('Chosen policy: ', chosen_prl_policy['name'], 'action: ', action)
                
                #Send the signal on to the env_wrapper.
                out_signal = {'action': action}             
                out_message = {"tag": "action", "signal": out_signal}
                
                if self.run['debug_mode']: print(self.blockName, 'sending', out_message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message)

                #Reset the policy received flags
                for policy in self.prl:
                    policy['received'] = False

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
            
            #if self.run['debug_mode']: print('policy_orc recieved', message)
            #print('policy_orc recieved', message)

            #--------------Pre Init Actions---------------------
            if topic == "commandChain":
                if message['command'] == 'stop':
                #Shut down.
                    keepRunning = False
                    print("Generator shutting down")
            
            
            if message['tag'] == 'init_details':
                self.run = json.loads(message['signal']['run'])
                #print('received init details')

                if not self.initialized:
                    #Set up run
                    print("policy orc initializing run")
                    self.init_run_details(self.run)
                    self.initialized = True
                    
            #----------------Post Init Actions----------------------
            if self.initialized:
                if message['tag'] == 'step_request':
                    #Update the current episode and step
                    self.e = signal['episode']
                    self.i_counter = signal['step']
                
                    #Triggered by experiment runner
                    
                    #Request state from env_wrapper    
                    out_message = {"tag": "state_request", "signal": {}}
                    
                    if self.run['debug_mode']: print(self.blockName, 'sending', message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message)
                    
                if message['tag'] == 'state':
                    #print('Policy orc received state')
                    
                    #Send states to policies (Just forward the signal with the details of the state)
                    out_message = {"tag": "state", "signal": message['signal']}
                    
                    if self.run['debug_mode']: print(self.blockName, 'sending', message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message) 

                    
                if message['tag'] == 'action':
                    #if self.run['debug_mode']: print('Policy orc received action message')
                    #if self.run['debug_mode']: print(signal)
                    
                    if self.run['hyperpolicy'] == 'a_stochastic':
                        if self.run['debug_mode']: print("using action stochastic hp")
                        self.run_action_stochastic_hp(message)
                    else:
                        self.run_random_hp(message)
                    
                    #self.recieve_action(signal)
                    
                if message['tag'] == 'update':
                    #Send it on to policies
                    if self.run['debug_mode']: print('Policy orc received update')
                    
                    #Respond to the action 
                    #Send action requests to policies (Just forward the signal with the details of the state)
                    out_message = {"tag": "update", "signal": signal}
                    
                    if self.run['debug_mode']: print(self.blockName, 'sending', out_message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message) 
                    
                if message['tag'] == 'env_reset':
                    #Send it on to env_wrapper
                    
                    out_message = {"tag": "env_reset", "signal": signal}
                    
                    if self.run['debug_mode']: print(self.blockName, 'sending', out_message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message) 
                    
                     
                    
                    
#------------Initialize
orc = Orc(blockName)

#----------------------Init zmq-------------------------          
orc.init_zmq(subTopics, pubTopics)

#-------------Run Loop--------------------
i = 0
print(orc.blockName, "starting")
keepRunning = True
while keepRunning:
    orc.handle_messages()
