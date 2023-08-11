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
import asyncio
import matplotlib.pyplot as plt

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


#------------------------------------------------
#--------------Declare the class and helper functions-----------------
#------------------------------------------------

class Experiment_Runner:
    def __init__(self, blockName):
        self.blockName = blockName
        self.last_init_time = time.time()
        self.init_message_sent = False
        self.episode_mode = False
        self.run_mode = False
        #self.update_recieved = False
        self.run_done = False
        
        #-------Tracking variables----------------
        self.e = 0
        self.i_counter = 0
        
        
        #-------Performance Measures----------------
        self.episode_reward  = 0
        #Episode done
        self.done = False
        self.reward_per_episode = []


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

    def update_handler(self, signal):
        update_info = signal['update_info']
        state = int(update_info['state'])
        action = update_info['action']
        self.next_state = int(update_info['next_state'])
        reward = update_info['reward']
        self.done = update_info['done'] 
        
        #print("exp runner got update")
        #print(signal)

        self.episode_reward += reward    #Increment reward   
        self.state = self.next_state
        
        #Update internal variables
        #Update step counter.
        self.i_counter += 1
        '''
        if self.e % 10 == 0 and self.e != 0:
            print("-" * 10)
            print("episode", self.e, "step:", self.i_counter)
        '''
        #print("into update handler")
        #--------------------------------------------------------
        #If at max step or is done, then record reward and reset.
        #--------------------------------------------------------
        if self.i_counter > self.run['max_steps'] or self.done == True:
            #Add reward to run reward record
            self.reward_per_episode.append(self.episode_reward)
            
            #Reset episode reward
            self.episode_reward = 0
            
            #Reset counter
            self.i_counter = 0
            
            #Increment episode
            self.e += 1
            #print("episode_counter", self.e)
            
            if self.e >= self.run['n_episodes']:
                #Done with experiment
                #-------------Send output messages to visualizer-----------------
                print("sending output to visualizer")

                out_message = {"tag": "run_results", "signal": {'reward_per_episode': self.reward_per_episode}}
                
                print(self.blockName, 'sending', out_message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message) 

                #------------Send message back to experiment hyper-runner----------------
                print("Done with run")                
                print("sending output to experiment generator")

                out_message = {"tag": "run_complete", "signal": {'reward_per_episode': self.reward_per_episode}}
                
                print(self.blockName, 'sending', out_message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message)     

                
                #Run done
                self.run_done = True    
                
            else: 
                #Send env_reset message.
                out_message = {"tag": "env_reset", "signal": {'reset': 'yes'}}
                
                #print(self.blockName, 'sending', out_message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message) 
                
                #-----------------------
                #-------Run Request-----
                #-----------------------
                #if a run was requested and the run isn't over 
                #send another step request after the episode finishes
                if self.run_mode and not self.run_done:
                    #Send step request with signal for new episode.
                    out_signal = {'step': self.i_counter, 'episode': self.e}
                    out_message = {"tag": "step_request", "signal": out_signal }
                    #print("sending run request from experiment runner")
                    #print(self.blockName, 'sending', out_message)

                    #Publish it
                    self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                    self.pubSocket.send_json(out_message)       
                    
                    #End of episode actions
                    if self.e % 5 == 0 and self.e != 0:
                        print("-" * 10)
                        print("episode", self.e)
                        
                        print("Probabilities")
                        print([policy_object['prob_trajectory'][self.e] for policy_object in self.run['hp_struct']['policy_objects']])
             

                    
        #--------------------------------------------
        #------------Episode_request-----------------
        #--------------------------------------------
        #If not at end of episode and episode requested , send another one.
        else:
            if (self.episode_mode or self.run_mode) and not self.run_done:
                #Send step request with signal for new episode.
                out_signal = {'step': self.i_counter, 'episode': self.e}
                out_message = {"tag": "step_request", "signal": out_signal }
                
                if self.run['debug_mode']: print(self.blockName, 'sending', out_message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message)
                

        
        #if self.run_mode and not self.run_done:   

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
            
            #print("Runner got: ", message)

            #--------------Check if its a command argument-----------
            if topic == "commandChain":
                if message['command'] == 'stop':
                #Shut down.
                    keepRunning = False
                    print("Generator shutting down")
                    
            #----------------Update Information-------------------
            if tag == 'update':
                #Save
                self.update_handler(signal)   
                
            #-----------------Button Click------------------------
            if tag == 'step_request':   
                #Send step request with signal for new episode.
                out_signal = {'step': self.i_counter, 'episode': self.e}
                out_message = {"tag": "step_request", "signal": out_signal }
                
                if self.run['debug_mode']: print(self.blockName, 'sending', message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message)
                
                if self.init_message_sent == False:
                    run_json = json.dumps(run, cls=MyEncoder)

                    out_message = {"tag": "init_details", "signal": {'run': run_json}}
                    
                    if self.run['debug_mode']: print(self.blockName, 'sending', out_message['tag'])

                    #Publish it
                    self.pubSocket.send_string('init_details', zmq.SNDMORE)
                    self.pubSocket.send_json(out_message)
                    
                    #Set init sent to true
                    self.init_message_sent = True
                    
            if tag == 'episode_request':
                if self.init_message_sent == False:
                    run_json = json.dumps(run, cls=MyEncoder)

                    out_message = {"tag": "init_details", "signal": {'run': run_json}}
                    
                    if self.run['debug_mode']: print(self.blockName, 'sending', out_message['tag'])

                    #Publish it
                    self.pubSocket.send_string('init_details', zmq.SNDMORE)
                    self.pubSocket.send_json(out_message)
                    
                    #Set init sent to true
                    self.init_message_sent = True
                    
                    #Wait for a second for all to initialize
                    time.sleep(1)
                    
                #Change to episode mode
                self.episode_mode = True
                
                #Trigger the loop with a step_request
                out_signal = {'step': self.i_counter, 'episode': self.e}
                out_message = {"tag": "step_request", "signal": out_signal }
                
                if self.run['debug_mode']: print(self.blockName, 'sending', message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message)   
            
            if tag == 'run_request':
                #Reset variables
                self.e = 0
                self.i_counter = 0
                self.reward_per_episode = []
                self.episode_reward = 0
                self.done = False
                self.run_done = False
                
                #Reset run to be the new one.
                self.run = json.loads(signal['run'])
                
                #Sends out the run to other blocks.
            
                run_json = json.dumps(self.run, cls=MyEncoder)

                out_message = {"tag": "init_details", "signal": {'run': run_json}}
                
                if self.run['debug_mode']: print(self.blockName, 'sending', out_message['tag'])

                #Publish it
                self.pubSocket.send_string('init_details', zmq.SNDMORE)
                self.pubSocket.send_json(out_message)
                
                #Set init sent to true
                self.init_message_sent = True
                
                #Wait for a second for all to initialize
                time.sleep(2)
                    
                #Change to episode mode
                self.run_mode = True
                
                #-------------Trigger the loop with a step_request---------------------
                print("Experiment runner triggering loop")
                out_signal = {'step': self.i_counter, 'episode': self.e}
                out_message = {"tag": "step_request", "signal": out_signal }
                
                #if self.run['debug_mode']: print(self.blockName, 'sending', message)
                print(self.blockName, 'sending', out_message)

                #Publish it
                self.pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                self.pubSocket.send_json(out_message)  
                

                
        
        '''
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
        '''

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
