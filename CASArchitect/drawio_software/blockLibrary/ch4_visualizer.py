#Head Material
#leftPorts=0
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 3/21/23
Description: Block to Visualize Outputs
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
from collections import deque
import numpy as np
import random
import os
import time
from datetime import datetime
import re
import matplotlib.pyplot as plt
import copy

#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = []
pubTopics = ['cats']
blockName = "source--"

logfile = open("blockLogs/ch4_visualizer.txt", "w")
logfile.write("Got to here")

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
class Visualizer:
    def __init__(self, blockName):
        self.blockName = blockName
        self.initialized = False
        print("initializing visualizer")  
    
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

    def analyze_experiment(self, experiment):
        #Read in experiment as json
        experiment = json.loads(experiment)
        
        #Set up save Location
        os.makedirs(os.path.join('results', str(experiment['generation_time']) + '_experiment'), exist_ok=True)
        
        #Save the json
        
        #Set up the figure   
        fig = plt.figure()
        ax = plt.subplot(111)
        
        #For output in folder, if meets conditions, graph all.
        total_run_rewards = {}
        num_runs = 1    #Special adjustment, averaging actually not necessary in this case.
        plot_names = []

        for iterator, entry in enumerate(experiment['runs']):    
            run = entry['output_dict']
            #avg_reward = [x['avg'] for x in run['stats']]
            reward_per_episode = run['reward_per_episode']
            
            running_avg = []
            window = 10
            for point in range(window, len(reward_per_episode)):
                running_avg.append(np.mean(reward_per_episode[point-window: point]))
                    
            
            
            #Make label
            set_name = ""
            set_name += "set_name"
            #set_name += "eps_max: " + str(entry['epsilon_max']) + " seed: " + str(entry['np_seed'])
            plot_names.append(set_name)
            
            #Generate equivalent number of timesteps for x axis
            #timesteps = [(x * pop_size * episode_len) for x in range(0,len(avg_reward))]
            
            
            ax.plot(running_avg, label=entry['label'], c=entry['color'])
            '''
            if iterator in total_run_rewards:
                temp_list = []
                temp_list = [a + b for a,b in zip(total_run_rewards[iterator], avg_reward)]  
                total_run_rewards[iterator] = temp_list[:]
                
            else:
                total_run_rewards[iterator] = avg_reward
            '''
            
        '''    
        #Plot each of the iterators
        for key, value in total_run_rewards.items():
            avg_value = [x / num_runs for x in value]
            #print("avg_value: ", avg_value)
            ax.plot(avg_value, label= plot_names[key], c=)
        '''
        
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.4,
                     box.width, box.height * 0.6])
            
        plt.title("Tester")
        plt.ylabel("Reward")
        plt.xlabel("# Generations")
        #plt.ylim(-0.1, 1.1)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fancybox=True, shadow=True)
        save_name = os.path.join('results', str(experiment['generation_time']) + '_experiment', 'avg_reward_vs_generation.pdf')
        plt.savefig(save_name, bbox_inches='tight')
        plt.show()

    def plot_run(self, reward_per_episode):
    
        #Save time
        save_time = time.time()
        
        #Add the run results on
        self.run['reward_per_episode'] = reward_per_episode
        
        #Save the results
        out_folder_name = str(save_time) + '_experiment'
        os.makedirs(os.path.join('drawio_software', 'results', out_folder_name), exist_ok=True)

        save_name = "json_output.json"
        with open(os.path.join('results', out_folder_name, save_name ), 'w') as f:
            json.dump(self.run, f, cls=MyEncoder)  
                
    
        #Plot and save the figure.   
        fig = plt.figure()
        ax = plt.subplot(111)
        
        running_avg = []
        window = 1
        for point in range(window, len(reward_per_episode)):
            running_avg.append(np.mean(reward_per_episode[point-window: point]))
        
        ax.plot(running_avg)
        
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.4,
                     box.width, box.height * 0.6])
                     
            
        plt.title("Tester")
        plt.ylabel("Reward")
        plt.xlabel("# Generations")
        #plt.ylim(-0.1, 1.1)
        #ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fancybox=True, shadow=True)
        save_name = os.path.join('drawio_software', 'results', save_times + '_experiment', 'avg_reward_vs_generation.pdf')
        plt.savefig(save_name, bbox_inches='tight')
        
        #print("show figure")
        #plt.show()              
                   
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
                print("visualizer initializing run")
                self.init_run_details(self.run)
                self.initialized = True
                    
            #-------------Post Init Actions----------------------
            if self.initialized:
                tag = message['tag']
                signal = message['signal']
                if message['tag'] =='run_results':
                    #Handle the results of the run
                    print('visualizer recieved info')
                    self.plot_run(signal['reward_per_episode'])
                    
                if message['tag'] =='experiment_results':
                    #Handle the results of the run
                    print('visualizer recieved experiment')
                    self.analyze_experiment(signal['experiment'])
                    
                    #out_message = {"tag": "run_results", "signal": {'reward_per_episode': self.reward_per_episode}}
                   
                    
                    
#------------Initialize
visualizer = Visualizer(blockName)

#----------------------Init zmq-------------------------          
visualizer.init_zmq(subTopics, pubTopics)

#-------------Run Loop--------------------
i = 0
print(visualizer.blockName, "starting")
keepRunning = True
while keepRunning:
    visualizer.handle_messages()
