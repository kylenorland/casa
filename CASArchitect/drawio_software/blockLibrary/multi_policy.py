#**********************************

#------------Imports--------------

#**********************************
import policy_lib               #Custom policies
import numpy as np 
rng = np.random.default_rng(12345)
np.set_printoptions(suppress = True) 
import seaborn as sns           #For plotting style
import graph_plotter            #Custom visualizer
import vector_grid_goal         #Custom environment
import gym                      #Support for RL environment.
import matplotlib.pyplot as plt
import time
import os
import json
import copy
import ch4_grapher
import random

import warnings
warnings.filterwarnings("ignore")



#--------------------------------------------------
#---------------General Functions------------------
#--------------------------------------------------
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
   
def init_environment(env_config):
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
        env = vector_grid_goal.CustomEnv(grid_dims=env_config['grid_dims'], player_location=env_config['player_location'], goal_location=env_config['goal_location'], map=env_config['env_map'])

    return env                
            

#********************************

#----------Default Run Settings-----

#***********************************
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
sns.set(style='darkgrid')
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

#-----Init the environment-------
'''
#Env Config
default_run['env_config'] = {}
#default_run['env_config']['env_name'] = 'FrozenLake-v1'
default_run['env_config']['is_slippery'] = False
default_run['env_config']['env_name'] = 'vector_grid_goal'
#env = vector_grid_goal.CustomEnv(grid_dims=default_run['grid_dims'], player_location=default_run['player_location'], goal_location=default_run['goal_location'], map=default_run['env_map'])
#default_run['env'] = env
'''

#*************************************************************
#--------------Adjust Parameters for Experiment---------------
#*************************************************************
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
    
    #plt.plot(r_prob_trajectory)
    #plt.plot(q_prob_trajectory)
    #plt.show()
    
    #-------------Design Policies-----------------------
    
    #Greedy Policy (Q_Learner)
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'Q_Policy',
    'prob_trajectory': q_prob_trajectory,
    })
    
    #Random Policy
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'Random_Policy',
    'prob_trajectory': r_prob_trajectory,
    })
    
    hp_structs.append(copy.deepcopy(new_hp_struct))
    
    #----------------Adjust Other Parameters-------------------------
    a_policy_chances = [0.3]
    random_seeds = rng.integers(low=0, high=9999, size=1)
    
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
    
    #plt.plot(r_prob_trajectory)
    #plt.plot(q_prob_trajectory)
    #plt.show()
    
    #-------------Design Policies-----------------------
    
    #Greedy Policy (Q_Learner)
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'Q_Policy',
    'prob_trajectory': q_prob_trajectory,
    })
    
    #Random Policy
    new_hp_struct['policy_objects'].append( {
    'policy_name': 'Random_Policy',
    'prob_trajectory': r_prob_trajectory,
    })
    
    hp_structs.append(copy.deepcopy(new_hp_struct))
    
    #----------------Adjust Other Parameters-------------------------
    a_policy_chances = [0.3]
    random_seeds = rng.integers(low=0, high=9999, size=1)
    
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
#----------------------------------------------
#----------------Generate The Experiment-------
#----------------------------------------------
#Generate or Load Experiment
folder_mode = False
generate_mode = True

experiment = {'runs': []}

if generate_mode:
    #Generate experiment
    #experiment = copy.deepcopy(gen_epsilon_greedy_mix_experiment(default_run))
    experiment = copy.deepcopy(gen_down_right_experiment(default_run))

    #Save experiment to folder
    experiment_name = str(experiment['generation_time']) + '.json'
    
    if not os.path.exists('saved_experiments'):
        os.makedirs('saved_experiments', exist_ok = True) 
    
    with open(os.path.join('saved_experiments', experiment_name), 'w') as f:
        json.dump(experiment, f, cls=MyEncoder)


#----------------------------------------------
#---------------Run The Experiment-------------
#----------------------------------------------
for run in experiment['runs']:
    #Start Timer
    #print("Run")
    #print(run)
    run['run_start_time'] = time.time()
    
    #Init the environment
    env = init_environment(run['env_config'])

    #****************************************************************
    #-----Init Policy Orc and the Desired Hyperpolicy----------------
    #****************************************************************
    Orc = policy_lib.Orc(run, env)

    Orc.init_action_stochastic_hp(run['hp_struct'])
    
    
    #********************************
    #---------Init Graphics----------
    #********************************
    #plotter = graph_plotter.Graph_Visualizer(run['grid_dims'][0], run['grid_dims'][1])

    #------------Take variables out of run dict for clarity---------
    n_episodes = run['n_episodes']
    max_epsilon = run['max_epsilon']             #initialize the exploration probability to 1
    epsilon = max_epsilon
    epsilon_decay = run['epsilon_decay']       #exploration decreasing decay for exponential decreasing
    min_epsilon = run['min_epsilon']
    max_steps = run['max_steps']
    
    #analytic_policy_active = run['analytic_policy_active']
    #analytic_policy_chance = run['analytic_policy_chance']
    #default_policy = Q_policy
    
    
    #Initialize Result Structures.
    reward_per_episode = []

    #********************************
    #---------Run Loop---------------
    #********************************
    for e in range(n_episodes):
        #------------Reset Environment--------------
        state = env.reset()
        done = False
        episode_reward = 0
        
        prev_run = []
        prev_first = 0
        prev_last = 0
        
        
        for i in range(max_steps):
            #------------DETERMINE ACTION FROM HYPERPOLICY---------------
            signal = {'tag': 'action_request', 'message': {'state': state, 'episode': e}}
            #Determine action
            action = Orc.run_action_stochastic_hp(signal)
            #print("Action: ", action)
            
            #------------RUN ACTION--------------------
            next_state, reward, done, _ = env.step(action)
            
            #For now, translate states to ints
            state = int(state)
            action = int(action)
            next_state = int(next_state)
            
            #-------------UPDATE POLICIES-----
            message = {}
            message['state'] = state
            message['action'] = action
            message['next_state'] = next_state
            message['reward'] = reward
            message['done'] = done
            
            signal = {'tag': 'update_info', 'message': message}
            #print("input signal", signal)
            #Update policies
            Orc.run_action_stochastic_hp(signal)
            
            episode_reward += reward    #Increment reward
            state = next_state          #update state to next_state
            
            #If done, end episode
            if done: break
        
            
            
        #------------------------------------------------------
        #--------------End of Episode Updates and Displays-----
        #------------------------------------------------------
        #Update reward record
        reward_per_episode.append(episode_reward) 
        
        #Decrease epsilon
        #epsilon = max(min_epsilon, np.exp(-epsilon_decay*e))
        #print("epsilon", epsilon)
        
        #Decrease analytic solver chance
        #run['analytic_policy_chance'] = max(min_epsilon, np.exp(-epsilon_decay*e))
        
        if e % 10 and e != 0:
            #print("--------------Episode:", str(e), "-----------------")
            pass
        if run['visualizer'] and e% run['vis_frequency'] == 0 and e != 0:
            #Get greedy path
            path, action_list, Q_path_reward = Q_policy.greedy_run()
            print(path, action_list, Q_path_reward)
            
            #Get current analytic path
            recommended_path = Analytic_policy.get_path()
        
            #plotter.draw_plot(Analytic_policy.state_reward, Analytic_policy.known_states, Analytic_policy.known_edges, path, recommended_path)
            #time.sleep(0.5)
            #input("Pause")
        
        if run['analytic_policy_active'] and e % run['analytic_policy_update_frequency'] == 0 and e != 0:
            #print('ap')
            #Make the conversion to the proper form
            Analytic_policy.convert_to_alg_form()
            
            #Run the solver
            if len(Analytic_policy.learned_info) > 0:
                Analytic_policy.update_policy(run)
            
            
            
        

    #----------------------------------------
    #-----------End of Run Actions------
    #----------------------------------------
    '''
    running_avg = []
    window = 50
    for point in range(window, len(reward_per_episode)):
        running_avg.append(np.mean(reward_per_episode[point-window: point]))
            
    #plt.plot(running_avg)
    '''
    run['output_dict']['reward_per_episode'] = reward_per_episode
    

#--------------------------------------------------------
#--------------End of Experiment Processing--------------
#--------------------------------------------------------

#Save
#save_name = str(round(time.time())) + "_json_output.json"

out_folder_name = str(experiment['generation_time']) + '_experiment'
os.makedirs(os.path.join('results', out_folder_name), exist_ok=True)

save_name = "json_output.json"
with open(os.path.join('results', out_folder_name, save_name ), 'w') as f:
    json.dump(experiment, f, cls=MyEncoder)    

#Save a text file with the changed variables
save_name = '+'.join(experiment['variables'])
file_path = os.path.join('results', out_folder_name, save_name)
with open(file_path, 'w') as f:
    pass

print("Processing Visuals")
ch4_grapher.Analyze_Experiment(experiment)
    
        
'''        
plt.legend(["With Analytical Crossover","Regular Q"])
plt.title("Rewards vs Episode")
plt.savefig(os.path.join('output_images','rewards' +"croosover"+'.png'))
plt.show()        
'''            
