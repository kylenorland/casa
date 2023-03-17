#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 3/15/23
Description: Sends experiment plans out (initialization)
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
import copy
import numpy as np
import seaborn as sns           #For plotting style
import os

#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = []
pubTopics = ['cats']
blockName = "source--"


logfile = open("blockLogs/experiment_runner.txt", "w")
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


#********************************

#----------Default Run Settings-----

#***********************************
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)

default_run = {}

#---------Env Settings------------
#Env Config
default_run['env_config'] = {}
default_run['env_config']['env_map'] = np.array([[0,0,0,0,0],
                        [0,1,0,1,0],
                        [0,0,0,1,0],
                        [0,1,0,0,1],
                        [0,0,1,0,0]])
#default_run['env_config']['env_name'] = 'FrozenLake-v1'
default_run['env_config']['env_name'] = 'vector_grid_goal'                        
default_run['env_config']['grid_dims'] = (len(default_run['env_config']['env_map'][0]),len(default_run['env_config']['env_map'][1]))
default_run['env_config']['player_location'] = (0,0)
default_run['env_config']['goal_location'] = (default_run['env_config']['grid_dims'][0] - 1, default_run['env_config']['grid_dims'][1] - 1)  
print(default_run['env_config']['grid_dims'] ,  default_run['env_config']['goal_location'])   

#----------Stochastic Controls--------------
default_run['seed'] = 6000

#------------Training Loop Controls-----------
default_run['n_episodes'] = 4000
default_run['max_steps'] = 30

#-------------Visualization Controls------------------
#sns.set(style='darkgrid')
default_run['visualizer'] = False
default_run['vis_steps'] = False             #Visualize every step
default_run['vis_frequency'] = 100           #Visualize every x episodes

#-------------Output Controls-----------------------
default_run['output_path'] = 'multi_policy_output'
if not os.path.exists(default_run['output_path']):
    os.makedirs(default_run['output_path'], exist_ok = True) 

default_run['output_dict'] = {} 

#--------------------------------------
#----------Policy Controls-------------
#--------------------------------------
#-----------orc_controls---------------
default_run['hyperpolicy'] = 'a_stochastic'

#-----------Q_Policy Control---------
default_run['gamma'] = 0.9             #discount factor 0.9
default_run['lr'] = 0.3                 #learning rate 0.1

#-----------Random Policy Control---------------
default_run['max_epsilon'] = 1              #initialize the exploration probability to 1
default_run['epsilon_decay'] = 0.001        #exploration decreasing decay for exponential decreasing
default_run['min_epsilon'] = 0.001

#-------------Analytic Policy Control---------------
default_run["mip_flag"] = True
default_run["cycle_flag"] = True
default_run['analytic_policy_update_frequency'] = 500
default_run['random_endpoints'] = False
default_run['reward_endpoints'] = True
default_run['analytic_policy_active'] = False
default_run['analytic_policy_chance'] = 0.0  



#-------------make a sample run--------------------
run = copy.deepcopy(default_run)

#------------------------------------------------
#--------------Declare the class and helper functions-----------------
#------------------------------------------------

class Experiment_Runner:
    def __init__(self, blockName):
        self.blockName = blockName
        self.last_init_time = time.time()

        print("initializing experiment runner") 
        
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

    def handle_messages(self):
        #----Poll-------------
        socks = dict(self.poller.poll(500))
        #print("socks", socks)
        
        #-----Read In--------
        for socket in socks:
            topic = socket.recv_string()
            message = socket.recv_json()
            tag = message['tag']
            signal = message['signal']

            #print(self.blockName, 'recieved ',  message)
            #--------------Check if its a command argument-----------
            if topic == "commandChain":
                if message['command'] == 'stop':
                #Shut down.
                    keepRunning = False
                    print("Generator shutting down")
                
                
            #-----------------Button Click------------------------
            if message['tag'] == 'step_request':
                #Send a step request to the policy orc
                out_message = {"tag": "step_request", "signal": signal }
                
                print(self.blockName, 'sending', message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message)


        #If time elapsed is greater than x milliseconds, send out init message            
        if (time.time() - self.last_init_time) > 5:
            run_json = json.dumps(run, cls=MyEncoder)

            out_message = {"tag": "init_details", "signal": {'run': run_json}}
            
            print(self.blockName, 'sending', out_message['tag'])

            #Publish it
            self.pubSocket.send_string('init_details', zmq.SNDMORE)
            self.pubSocket.send_json(out_message)
            
            #update the last time it was fired.
            self.last_init_time = time.time()

#---------------------Initialize -----------------------
#Init Core
experiment_runner = Experiment_Runner(blockName) 

#Init zmq               
experiment_runner.init_zmq(subTopics, pubTopics)

#Init unique components.

#----------------------Run loop---------------------------
i = 0
print(experiment_runner.blockName, "starting")
keepRunning = True
while keepRunning:
    experiment_runner.handle_messages()
