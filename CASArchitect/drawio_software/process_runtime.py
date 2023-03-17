#Author: Kyle Norland
#Date: 3/12/23
#Description: Simplified CASA runtime for local runtimes.
#May also include a PySide6 front end for the GUI root
#Stops on command from zmq socket. No override currently implemented.

#-----------------------------
#---------Imports-------------
#-----------------------------
import os, sys, time, datetime
import json
import zmq
import subprocess
import signal #For sending sigint
import copy

#------------Globals-----------------
#Set directory to drawio_software folder
cwd = os.getcwd()
print("Working directory is: ", cwd)
if cwd != 'K:\Dissertation\Projects\Chapter 5 CASA Github\CASArchitect\drawio_software':
    #Then running from main CASA, switch to drawio_software folder
    print("Changing directories")
    os.chdir(os.path.join('.', 'drawio_software'))
    
block_lib_folder_path = os.path.join('.', 'blockLibrary')
drawio_reader_output_folder = os.path.join('.', 'outputs')
running_processes = []
#-----------------------------
#---------Functions-----------
#-----------------------------


#-----------------------------
#----------Main---------------
#-----------------------------

if __name__ == "__main__":
    #--------------------Start ZMQ Context----------------------
    #Establish zmq context
    context = zmq.Context()
    
    #--------------------Load in the code graph--------------------------
    with open(os.path.join(drawio_reader_output_folder, "codeTree.json"), "r") as outFile:
        #Load JSON in and print
        code_tree = json.load(outFile)
    #print(code_tree)
    
    #--------------------Load in the gui graph---------------------------
    with open(os.path.join(drawio_reader_output_folder, "guiTree.json"), "r") as outFile:
        #Load JSON in and print
        gui_tree = json.load(outFile)
    #print(gui_tree)    
    
            
    
    #-------------------Determine the structures needed and check if they exist (Comp/Comms/Bound/Blocks)--------------
    #Start with single comms manager.
    print("Starting Comms Manager")
    
    #-------------Find ports that are free to be used-----------------
    testSocket = context.socket(zmq.PUB)
    subPort = 8000
    pubPort = 9000

    while subPort < 9000:
        try:
            testSocket.bind("tcp://127.0.0.1:" + str(subPort))
            print("Subscribing to " + str(subPort))
            rCode = testSocket.unbind("tcp://127.0.0.1:" + str(subPort))
            break
        except:
            subPort += 1

    while pubPort < 10000:
        try:
            testSocket.bind("tcp://127.0.0.1:" + str(pubPort))
            print("Publishing to " + str(pubPort) + "\n")
            rCode = testSocket.unbind("tcp://127.0.0.1:" + str(pubPort))
            break
        except:
            pubPort +=1
    
    #Start the comms process with the ports (sys.executable goes and finds the python executable)
    new_process = subprocess.Popen([sys.executable, os.path.join(block_lib_folder_path, 'commsManager.py'), str(subPort), str(pubPort)])
    
    #Add process to record
    new_process_dict = {'name': 'commsManager', 'process': new_process}
    running_processes.append(new_process_dict)
    
    #print("updated process dict")
    #print(running_processes)
    
    #Pause to let system set up
    time.sleep(1)
    
    
    #-------------------------Add GUI----------------------------------
    #Start the comms process with the ports (sys.executable goes and finds the python executable)
    new_process = subprocess.Popen([sys.executable, os.path.join(block_lib_folder_path, 'gui_container.py'), str(subPort), str(pubPort)])
    
    #Add process to record
    new_process_dict = {'name': 'guiContainer', 'process': new_process}
    running_processes.append(new_process_dict)   
   
    
    #------------------------------------------------------------------
    #------------------------Add Blocks--------------------------------
    #------------------------------------------------------------------
    
    #Simple blocks (block name is value
    print("Starting Up Blocks")
    for vertex in code_tree['vertices']:
        #Check if block exists
        print("Checking", os.path.join(block_lib_folder_path, vertex['value'] + '.py'))
        if os.path.isfile(os.path.join(block_lib_folder_path, vertex['value'] + '.py')):
            ##Prepare the instructions for the block
            #----------sdfsdsdf Add the global signal here---------
            block_info = {}
            block_info['subTopics'] = [str(x) for x in vertex['inputs']]
            #------------Global listeners---------------------
            block_info['subTopics'].append('init_details')
            block_info['subTopics'].append('global')
            
            block_info['pubTopics'] = [str(x) for x in vertex['outputs']]
            block_info['blockName'] = vertex['value']
        
            #Start the process (sys.executable goes and finds the python executable)
            new_process = subprocess.Popen([sys.executable, os.path.join(block_lib_folder_path, vertex['value'] + '.py'), str(subPort), str(pubPort), json.dumps(block_info)])
            
            #Add process to record
            new_process_dict = {'name': vertex['value'], 'process': new_process}
            running_processes.append(new_process_dict)
    
    print("Currently running processes")
    for entry in running_processes: print(entry)
    print("---")
       
    #------------------------------------------------------------------
    #-----------------Listen for stop signal at port 9600--------------
    #------------------------------------------------------------------
    #ttl is max length of time to run
    ttl = 300000
    
    #Start timer
    startTime = time.time()
    currentTime = startTime
    
    #Connect to ports
    pubSocket = context.socket(zmq.PUB)
    pubSocket.connect("tcp://127.0.0.1:" + str(subPort))

    #Listen to testbed signal
    subSocket = context.socket(zmq.SUB)
    subSocket.connect("tcp://127.0.0.1:" + str(9600))

    #Subscribe to compManagerRequest
    subTopic = 'compManagerRequest'
    subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())
    print("Comp Manager subscribing to: " + subTopic + "\n")

    #Set up a poller
    poller = zmq.Poller()
    poller.register(subSocket, zmq.POLLIN)
    
    #Wait for a sec
    #time.sleep(5)
    
    while((currentTime - startTime) < ttl):
        #Check for stop signal 1 second timeout
        socks = dict(poller.poll(1000))
        #print("Checking")
        #Receive the data if available
        #print(len(socks))
        if subSocket in socks and socks[subSocket] == zmq.POLLIN:
            topic = subSocket.recv_string()
            data = subSocket.recv_json()
            print("The topic is: " + str(topic))
            if(data['signalBody'] == 'stop_system'):
                #Break out of the loop;
                print("compManager breaking out of the run loop")
                break

        #Update the time;
        currentTime = time.time()
        
    print("Stopping processes")
    for process_dict in running_processes:
        process_dict['process'].terminate()
        #if process_dict['name'] == 'drawio_listener':
            #process_dict['process'].terminate()    
        
    '''
    #Kill all the code (With SIGINT) after sending out stop signal
    print(" ")
    print("Closing Blocks")
    try:
        #pubSocket = context.socket(zmq.PUB)
        #pubSocket.connect("tcp://127.0.0.1:" + str(subPort))
        #time.sleep(0.5)

        sendData = {'sender':'compManager', 'command':'stop'}
        pubSocket.send_string("commandChain", zmq.SNDMORE)
        pubSocket.send_json(sendData)
        print("The closing message succeeded")
    except:
        print("The closing message failed")

    time.sleep(3)
    print("-------------------------------------\n")

    for block in blockArchitecture['blocks']:
        if block['running'] == True:
            print("Closing " + str(block['blockName']) + " as " + str(block['pid']))
            #Changed this to kill processes differently for windows
            if(str(sys.platform) == 'win32'):
                #Signals not supported on windows
                #https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/
                print("Harder to programmatically close threads in windows: All blocks need to have self closing abilities") 
            else:
                block['process'].send_signal(signal.SIGINT)
    #Close file
    f.close()
    '''    

        