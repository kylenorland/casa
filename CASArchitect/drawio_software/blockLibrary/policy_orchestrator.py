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
        #def load_run_details(self, run, env):
    
    def init_run_details(self, run):
        self.run = run
        #Init the environment
        #self.env = init_environment(run['env_config'])
        
        #Init the correct stochastic policy
        self.init_random_hp()
        
        self.initialized = True
        
        #self.hp_struct = {'policy_objects': []}
        
    def init_random_hp(self):
        #Policy response list
        self.prl = []
        self.prl.append({'name': 'q_policy', 'recieved': False, 'action':None})
        self.prl.append({'name': 'random_policy', 'recieved': False, 'action':None})
        
    def run_random_hp(self, message):
        tag = message['tag']
        signal = message['signal']
        
        if tag == 'action':
            #Add, check if both present, choose randomly.
            for policy in self.prl:
                if policy['name'] == signal['policy_name']:
                    policy['recieved'] = True
                    policy['action'] = signal['action']
            
            all_recieved = True
            for policy in self.prl:
                if not policy['recieved']:
                    all_recieved = False
                    
            if all_recieved:
                print("hp got all policy responses")
                #Choose randomly
                chosen_policy = random.choice(self.prl)
                action = chosen_policy['action']
                
                #Send the signal on to the env_wrapper.
                out_signal = {'action': action}
                                    
                out_message = {"tag": "action", "signal": out_signal}
                
                print(self.blockName, 'sending', out_message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message)

                #Reset the policy recieved flags
                for policy in self.prl:
                    policy['recieved'] = False
                    
    def init_action_stochastic_hp(self, hp_struct):
        for entry in hp_struct['policy_objects']:
            #Should have: policy_name, prob_trajectory
            
            new_policy_obj = {
            'policy_name': entry['policy_name'],
            'policy': self.instantiate_policy(entry['policy_name']),
            'prob_trajectory': entry['prob_trajectory'],
            }
            
            #Add to policy list
            self.hp_struct['policy_objects'].append(copy.deepcopy(new_policy_obj))

            
    def run_action_stochastic_hp(self, signal):
        if signal['tag'] == 'action_request':
            #Random generate based off of prob_trajectories (based on episode for now)
            message = signal['message']
            episode = message['episode']
            
            #Calculate probabilities of each policy
            prob_array = [x['prob_trajectory'][episode] for x in self.hp_struct['policy_objects']]
            
            #Choose the policy randomly
            chosen_policy_object = random.choices(self.hp_struct['policy_objects'], prob_array)[0] #First one in returned list
            chosen_policy = chosen_policy_object['policy']
            
            #print("Chosen policy", chosen_policy_object['policy_name'])
            #print(chosen_policy)
            #print(chosen_policy['policy_name'])
            #Add a default policy
            
            return chosen_policy.get_action(message['state'])
            
        elif signal['tag'] == 'update_info':
            #Take the pieces out to be used.
            state = signal['message']['state']
            action = signal['message']['action']
            next_state = signal['message']['next_state']
            reward = signal['message']['reward']
            done = signal['message']['done']
            
            #Send update signal to all  (just Q learning actually updates)
            for policy_object in self.hp_struct['policy_objects']:
                policy = policy_object['policy']
                #Update the policy
                #print("updating")
                #print(policy)
                #print(signal['message'])
                policy.update_policy(signal['message'])


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


            #--------------Pre Init Actions---------------------
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
                    print("policy orc initializing run")
                    self.init_run_details(self.run)
                    self.initialized = True
                    
            #----------------Post Init Actions----------------------
            if self.initialized:
                if message['tag'] == 'step_request':
                    #Triggered by experiment runner
                    
                    #Request state from env_wrapper    
                    out_message = {"tag": "state_request", "signal": {}}
                    
                    print(self.blockName, 'sending', message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message)
                    
                if message['tag'] == 'state':
                    #print('Policy orc recieved state')
                    
                    #Send states to policies (Just forward the signal with the details of the state)
                    out_message = {"tag": "state", "signal": message['signal']}
                    
                    print(self.blockName, 'sending', message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message) 

                    
                if message['tag'] == 'action':
                    print('Policy orc recieved action message')
                    print(signal)
                    
                    self.run_random_hp(message)
                    
                    #self.recieve_action(signal)
                    
                if message['tag'] == 'update':
                    #Send it on to policies
                    print('Policy orc recieved update')
                    
                    #Respond to the action 
                    #Send action requests to policies (Just forward the signal with the details of the state)
                    out_message = {"tag": "update", "signal": signal}
                    
                    print(self.blockName, 'sending', message)

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
