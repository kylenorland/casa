#Head Material
#leftPorts=0
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 3/22/23
Description: Block to generate experiments and feed them to the experiment runner
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
import os
import copy
import numpy as np 
import matplotlib.pyplot as plt
rng = np.random.default_rng(12345)

#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = []
pubTopics = ['cats']
blockName = "source--"


logfile = open("blockLogs/experiment_generator.txt", "w")
logfile.write("Got to here")

#-------------------------------------------------------------
#---------------------Helper Functions------------------------
#-------------------------------------------------------------
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

def get_discrete_state(self, state, bins, obsSpaceSize):
    #https://github.com/JackFurby/CartPole-v0
    stateIndex = []
    for i in range(obsSpaceSize):
        stateIndex.append(np.digitize(state[i], bins[i]) - 1) # -1 will turn bin into index
    return tuple(stateIndex)

#-------------------------------------------------------------
#---------------------Defaults--------------------------------
#-------------------------------------------------------------
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
default_run['n_episodes'] = 500 #4000
default_run['max_steps'] = 30 #30

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

default_run['debug_mode'] = False

#--------------------------------------
#----------Policy Controls-------------
#--------------------------------------
#-----------orc_controls---------------
default_run['hyperpolicy'] = 'a_stochastic'

#-----------Q_Policy Control---------
default_run['gamma'] = 0.9             #discount factor 0.9
default_run['lr'] = 0.3                 #learning rate 0.1

#-----------Random Policy Control---------------
default_run['max_epsilon'] = 0.5              #initialize the exploration probability to 1
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

#-------------------------------------------------------------
#------------Experiment Generator Functions------------------
#-------------------------------------------------------------
def gen_analytic_policy_active(default_run):
    #Description: Test epsilon setting 0 vs 50%
    #Try with two epsilon settings and 10 different random seeds.
    #epsilon_maxes = [0, 0.05, 0.1, 0.25, 0.5]
    
    a_policy_active_list = [True]
    a_policy_chances = [0.3]
    random_seeds = rng.integers(low=0, high=9999, size=1)
    
    new_experiment = {'runs':[]}
    new_experiment['generation_time']= time.time()
    new_experiment['variables'] = ['analytic_policy_active', 'analytic_policy_chance', 'np_seed']
    
    color_list = ['green', 'blue', 'red', 'yellow', 'orange', 'brown']
    color_counter = 0
    for policy_active in a_policy_active_list:
        for policy_chance in a_policy_chances:
            for seed in random_seeds:
                new_run = copy.deepcopy(default_run)
                
                #Adjusted Settings
                new_run['analytic_policy_active'] = policy_active
                new_run['analytic_policy_chance'] = policy_chance
                
                #Standard Settings
                new_run['np_seed'] = seed
                new_run['env_seed'] = seed
                new_run['python_seed'] = seed
                new_run['color'] = color_list[color_counter]
                new_run['label'] = "policy_active: " + str(policy_active) + " policy_chance: "+ str(policy_chance) +  " seed: " + str(seed)
                
                print("Settings: ", new_run['analytic_policy_active'], ": ", seed)
                
                #Add run to experiment
                new_experiment['runs'].append(copy.deepcopy(new_run))
            
            color_counter += 1   
    print("Returning new experiment")
    return new_experiment   


def gen_epsilon_greedy_mix_experiment(default_run):
    #Description: Test epsilon setting 0 vs 50%
    #Try with two epsilon settings and 10 different random seeds.
    #epsilon_maxes = [0, 0.05, 0.1, 0.25, 0.5]
    
    #Generate different hyperpolicy infos to test.
    hp_structs = []
    
    #---------Prep Action Level Stochastic HP Info--------------
    new_hp_struct = {'policy_objects': []}
    #run['min_epsilon']
    #Generate Policy Trajectories    
    r_prob_trajectory = [max(default_run['max_epsilon']*((1-default_run['epsilon_decay'])**e), default_run['min_epsilon']) for e in range(0, default_run['n_episodes'])]
    q_prob_trajectory = [(1-r_prob_trajectory[x]) for x in range(0, default_run['n_episodes'])]
    
    #Convert Prob Trajectories to Lists
    #r_prob_trajectory = r_prob_trajectory.tolist()
    #q_prob_trajectory = q_prob_trajectory.tolist()
    
    #plt.plot(r_prob_trajectory)
    #plt.plot(q_prob_trajectory)
    #plt.show()
    
    #-------------Design Policies-----------------------
    
    #Greedy Policy (Q_Learner)
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'q_policy',
    'prob_trajectory': q_prob_trajectory,
    })
    
    #Random Policy
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'random_policy',
    'prob_trajectory': r_prob_trajectory,
    })
    
    hp_structs.append(copy.deepcopy(new_hp_struct))
    
    #----------------Adjust Other Parameters-------------------------
    a_policy_chances = [0.3]
    random_seeds = rng.integers(low=0, high=9999, size=2)
    
    new_experiment = {'runs':[]}
    new_experiment['generation_time']= time.time()
    new_experiment['variables'] = ['hp_struct', 'analytic_policy_chance', 'np_seed']
    
    color_list = ['green', 'blue', 'red', 'yellow', 'orange', 'brown']
    color_counter = 0
    for hp_struct in hp_structs:
        for policy_chance in a_policy_chances:
            for seed in random_seeds:
                new_run = copy.deepcopy(default_run)
                
                #Adjusted Settings
                new_run['hp_struct'] = hp_struct
                new_run['analytic_policy_chance'] = policy_chance
                
                #Standard Settings
                new_run['np_seed'] = seed
                new_run['env_seed'] = seed
                new_run['python_seed'] = seed
                new_run['color'] = color_list[color_counter]
                new_run['label'] = " policy_chance: "+ str(policy_chance) +  " seed: " + str(seed)
                
                print("Settings: ", ": ", seed)
                
                #Add run to experiment
                new_experiment['runs'].append(copy.deepcopy(new_run))
            
            color_counter += 1   
    print("Returning new experiment")
    return new_experiment   


def gen_down_right_experiment(default_run):
    #Description: Test epsilon setting 0 vs 50%
    
    #Generate different hyperpolicy infos to test.
    hp_structs = []
    
    #---------Prep Action Level Stochastic HP Info--------------
    new_hp_struct = {'policy_objects': []}
    #run['min_epsilon']
    
    
    
    #---------------------------------------------------
    #--------------Generate Policy Info-----------------
    #---------------------------------------------------
    #Generate Policy Trajectories    
    r_prob_trajectory = [max(default_run['max_epsilon']*((1-default_run['epsilon_decay'])**e), default_run['min_epsilon']) for e in range(0, default_run['n_episodes'])]
    q_prob_trajectory = [(1-r_prob_trajectory[x]) for x in range(0, default_run['n_episodes'])]
    
    
    random_portion = 0.6
    dr_portion = 0.4
    
    r_prob_trajectory = [random_portion * x for x in r_prob_trajectory]
    dr_prob_trajectory = [dr_portion * x for x in r_prob_trajectory]
    
    #plt.plot(r_prob_trajectory)
    #plt.plot(q_prob_trajectory)
    #plt.plot(dr_prob_trajectory)
    #plt.show()
    
    #Greedy Policy (Q_Learner)
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'q_policy',
    'prob_trajectory': q_prob_trajectory,
    })
    
    #Random Policy
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'random_policy',
    'prob_trajectory': r_prob_trajectory,
    })

    #Down Right Policy
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'down_right_policy',
    'prob_trajectory': dr_prob_trajectory,
    })    
    
    
    hp_structs.append(copy.deepcopy(new_hp_struct))
    
    #----------------Adjust Other Parameters-------------------------
    a_policy_chances = [0.3]
    random_seeds = rng.integers(low=0, high=9999, size=3)
    
    new_experiment = {'runs':[]}
    new_experiment['generation_time']= time.time()
    new_experiment['variables'] = ['hp_struct', 'analytic_policy_chance', 'np_seed']
    
    color_list = ['green', 'blue', 'red', 'yellow', 'orange', 'brown']
    color_counter = 0
    for hp_struct in hp_structs:
        for policy_chance in a_policy_chances:
            for seed in random_seeds:
                new_run = copy.deepcopy(default_run)
                
                #Adjusted Settings
                new_run['hp_struct'] = hp_struct
                new_run['analytic_policy_chance'] = policy_chance
                
                #Standard Settings
                new_run['np_seed'] = seed
                new_run['env_seed'] = seed
                new_run['python_seed'] = seed
                new_run['color'] = color_list[color_counter]
                new_run['label'] = " policy_chance: "+ str(policy_chance) +  " seed: " + str(seed)
                
                print("Settings: ", ": ", seed)
                
                #Add run to experiment
                new_experiment['runs'].append(copy.deepcopy(new_run))
            
            color_counter += 1   
    print("Returning new experiment")
    return new_experiment
    
def gen_down_right_v_epsilon_experiment(default_run):
    #Description: Down right vs epsilon.
    
    #Generate different hyperpolicy infos to test.
    hp_structs = []
    
    #---------Prep Action Level Stochastic HP Info--------------
    
    #-------------------------Epsilon Struct----------------------------------- 
    new_hp_struct = {'policy_objects': []}
    #run['min_epsilon']
    #Generate Policy Trajectories    
    r_prob_trajectory = [max(default_run['max_epsilon']*((1-default_run['epsilon_decay'])**e), default_run['min_epsilon']) for e in range(0, default_run['n_episodes'])]
    q_prob_trajectory = [(1-r_prob_trajectory[x]) for x in range(0, default_run['n_episodes'])]
    
    #Convert Prob Trajectories to Lists
    #r_prob_trajectory = r_prob_trajectory.tolist()
    #q_prob_trajectory = q_prob_trajectory.tolist()
    
    #plt.plot(r_prob_trajectory)
    #plt.plot(q_prob_trajectory)
    #plt.show()
    
    #-------------Design Policies-----------------------
    
    #Greedy Policy (Q_Learner)
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'q_policy',
    'prob_trajectory': q_prob_trajectory,
    })
    
    #Random Policy
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'random_policy',
    'prob_trajectory': r_prob_trajectory,
    })
    
    hp_structs.append(copy.deepcopy(new_hp_struct))

    #-----------------Down Right Struct----------------------
    new_hp_struct = {'policy_objects': []}
    
    #Generate Policy Trajectories    
    r_prob_trajectory = [max(default_run['max_epsilon']*((1-default_run['epsilon_decay'])**e), default_run['min_epsilon']) for e in range(0, default_run['n_episodes'])]
    q_prob_trajectory = [(1-r_prob_trajectory[x]) for x in range(0, default_run['n_episodes'])]
    
    
    random_portion = 0.6
    dr_portion = 0.4
    
    r_prob_trajectory = [random_portion * x for x in r_prob_trajectory]
    dr_prob_trajectory = [dr_portion * x for x in r_prob_trajectory]
    
    #plt.plot(r_prob_trajectory)
    #plt.plot(q_prob_trajectory)
    #plt.plot(dr_prob_trajectory)
    #plt.show()
    
    #Greedy Policy (Q_Learner)
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'q_policy',
    'prob_trajectory': q_prob_trajectory,
    })
    
    #Random Policy
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'random_policy',
    'prob_trajectory': r_prob_trajectory,
    })

    #Down Right Policy
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'down_right_policy',
    'prob_trajectory': dr_prob_trajectory,
    })    
    
    
    hp_structs.append(copy.deepcopy(new_hp_struct))
    
    #----------------Adjust Other Parameters-------------------------
    a_policy_chances = [0.3]
    random_seeds = rng.integers(low=0, high=9999, size=3)
    
    new_experiment = {'runs':[]}
    new_experiment['generation_time']= time.time()
    new_experiment['variables'] = ['hp_struct', 'analytic_policy_chance', 'np_seed']
    
    color_list = ['green', 'blue', 'red', 'yellow', 'orange', 'brown']
    color_counter = 0
    for hp_struct in hp_structs:
        for policy_chance in a_policy_chances:
            for seed in random_seeds:
                new_run = copy.deepcopy(default_run)
                
                #Adjusted Settings
                new_run['hp_struct'] = hp_struct
                new_run['analytic_policy_chance'] = policy_chance
                
                #Standard Settings
                new_run['np_seed'] = seed
                new_run['env_seed'] = seed
                new_run['python_seed'] = seed
                new_run['color'] = color_list[color_counter]
                new_run['label'] = " policy_chance: "+ str(policy_chance) +  " seed: " + str(seed)
                
                print("Settings: ", ": ", seed)
                
                #Add run to experiment
                new_experiment['runs'].append(copy.deepcopy(new_run))
        
        #Different Colors for hp structs
        color_counter += 1   
    print("Returning new experiment")
    return new_experiment


#------------------------------------------------------Main--------------------------------------
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
#-------------------------------------------------
class Experiment_Generator:
    def __init__(self, blockName, default_run):
        self.blockName = blockName
        self.initialized = False
        self.default_run = default_run
        #self.exp_gen_function = gen_epsilon_greedy_mix_experiment(default_run)
        self.run_counter = 0
        print("initializing experiment generator")  
    
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
        
    def generate_experiment(self):
        #Global Experiment Generation
        #self.experiment = gen_epsilon_greedy_mix_experiment(self.default_run)
        #self.experiment = gen_down_right_experiment(self.default_run)
        self.experiment = gen_down_right_v_epsilon_experiment(self.default_run)
        
        #Save experiment to folder
        experiment_name = str(self.experiment['generation_time']) + '.json'
        saved_experiment_path = os.path.join('results', 'saved_experiments')
        
        if not os.path.exists(saved_experiment_path):
            os.makedirs(saved_experiment_path, exist_ok = True) 
        
        with open(os.path.join(saved_experiment_path, experiment_name), 'w') as f:
            json.dump(self.experiment, f, cls=MyEncoder)
        
        self.run_counter = 0
                    
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

            if topic == "commandChain":
                if message['command'] == 'stop':
                #Shut down.
                    keepRunning = False
                    print("Generator shutting down")
            
            #-----------Handle Starting Button Click (Send run request)--------------
            if message['tag'] =='start_run':
                print('Sending signal to start run')
                
                print("Run")
                out_run = self.experiment['runs'][self.run_counter]
                run_json = json.dumps(out_run, cls=MyEncoder)
                print(out_run)
                out_message = {"tag": "run_request", "signal": {'run': run_json}}
                
                print(self.blockName, 'sending', out_message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message) 
            
            #-------------Handle Experiment Ended Signal----------------
            if message['tag'] == 'run_complete':
                print("Experiment generator recieved run complete")
                
                #Add the run to the experiment results.
                self.experiment['runs'][self.run_counter]['output_dict']['reward_per_episode'] = signal['reward_per_episode']
                
                
                #Update run counter
                self.run_counter += 1

                
                if self.run_counter < len(self.experiment['runs']):
                    print('Sending signal to start run')
                    
                    out_run = self.experiment['runs'][self.run_counter]
                    run_json = json.dumps(out_run, cls=MyEncoder)
                    print(out_run)
                    out_message = {"tag": "run_request", "signal": {'run': run_json}}
                    
                    print(self.blockName, 'sending', out_message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message)
                    
                else:
                    print("Experiment Complete")
                    
                    #Send signal to visualizer
                    experiment_json = json.dumps(self.experiment, cls=MyEncoder)
                    out_message = {"tag": "experiment_results", "signal": {'experiment': experiment_json}}
                    
                    print(self.blockName, 'sending', out_message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message)
                    
                    
                    
#----------------------Initialize-----------------------
experiment_generator = Experiment_Generator(blockName, default_run)



#----------------------Init zmq--------------------------          
experiment_generator.init_zmq(subTopics, pubTopics)

#----------------------Generate Experiments--------------
experiment_generator.generate_experiment()

#-------------Run Loop--------------------
i = 0
print(experiment_generator.blockName, "starting")
keepRunning = True
while keepRunning:
    experiment_generator.handle_messages()
