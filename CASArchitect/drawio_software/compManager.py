# !/usr/bin/python3
#Author: Kyle Norland
#Date: 9-14-20
#Description: Manages the computation for its subsystem. (Currently top level system)
import os, sys, time, datetime
import json
import zmq
import subprocess
import signal #For sending sigint


#-----------------------------------
#---------Defaults---------
#-----------------------------------
ttl = 5
computerAddress = 1   #This is the highest level explicit addressing field for the computer.

#-----------------------------------
#---------Pre-Operation Things---------
#-----------------------------------
#Load external arguments
numArgs = len(sys.argv)
print("There are " + str(numArgs) + " arguments")

if numArgs >= 1:
    externalArguments = json.loads(sys.argv[1])

    try:
        print("Preparing to run system for " + str(externalArguments['runTime']) + " seconds")
        ttl = externalArguments['runTime']
    except:
        print("Something in the json loading process went wrong")

#Establish zmq context
context = zmq.Context()

#-------------------------------------------------------------------------------------------
#---------Check for available ports to give to the comms manager and blocks----------------
#-------------------------------------------------------------------------------------------
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

#--------------------------------------------------------------
#---------Add a comms manager block with the correct info---------
#--------------------------------------------------------------
blockArchitecture = {"blocks": []}

#Just enough to call it for now
commsBlock = {"blockName": "commsManager.py", "proxyInputPort": subPort, "proxyOutputPort": pubPort}

blockArchitecture['blocks'].append(commsBlock)

#-----------------------------------
#---------Load JSON File from envConfig---------
#-----------------------------------
f = open('envConfig/externalArgs.txt')
data = json.load(f)

codeBlocks = data #Already in an array

for block in codeBlocks:
    #This method may need to change if there are too many arguments, but that should be done on the front end.
    newBlock = block
    newBlock["proxyInputPort"] = subPort
    newBlock["proxyOutputPort"] =  pubPort
    newBlock["runTime"] = ttl
    newBlock["running"] = False
    newBlock["blockName"] = block['path']

    blockArchitecture['blocks'].append(newBlock)

#-------------------------------------------
#---------Start the programs----------------
#-------------------------------------------
#Notes: Should include comms manager
with open('envConfig/runFile.txt', 'w') as runFile:
    runFileData = {'commsSubPort': subPort, 'commsPubPort': pubPort, 'processes': []}
    print("  ")
    print("---------------------------------------")
    print("---------------------------------------")
    print("Computation Manager Starting Up Blocks")
    print("---------------------------------------")
    print("---------------------------------------")
    for block in blockArchitecture['blocks']:
        #Start the block
        folderPath = "blockLibrary/"
        #block['proxyInputPort'], block['proxyOutputPort'], json.dumps(block)
        #Check if file exists (ie nonrunnable block)
        try:
            testFile = open(folderPath + block["blockName"])
            #If this doesn't throw an error, close it:
            testFile.close()

            if(str(sys.platform) == 'win32'):
                cmd = ["python", folderPath + block["blockName"], str(block['proxyInputPort']), str(block['proxyOutputPort']), json.dumps(block)]
            else:
                cmd = ["python3", folderPath + block["blockName"], str(block['proxyInputPort']), str(block['proxyOutputPort']), json.dumps(block)]

            newProcess = subprocess.Popen(cmd,
                                          shell=False
                                          )
            #Note: Do without shell (use list format)
            #rc = newProcess.wait() #if the shell is slow
            #Get pid
            pid = newProcess.pid
            print(block['blockName'] +" " + str(pid))

            block['pid'] = pid          # note not the actual, if shell=True
            block['process'] = newProcess
            block['running'] = True

            #Write the process to file;
            runFileData['processes'].append(str(pid))
            #print("Process starting: " + str(pid))

        except:
            print(block["blockName"] + " couldn't be found by the computer")

    #Write the json to file.
    try:
        serial_content = json.dumps(runFileData)
        runFile.write(serial_content)
    except:
        print("Json write failed")


    #Section End Art
    print("---------------------------------------")
    print("---------------------------------------")
    print("  ")
#--------------------------------------------------------------------------
#Kill the processes after a certain amount of time or upon command)
#--------------------------------------------------------------------------
#Start timer
startTime = time.time()
currentTime = startTime

#Pause for a sec to let the commms manager get started
time.sleep(0.5)

#Connect to ports
pubSocket = context.socket(zmq.PUB)
pubSocket.connect("tcp://127.0.0.1:" + str(subPort))

subSocket = context.socket(zmq.SUB)
subSocket.connect("tcp://127.0.0.1:" + str(pubPort))

#Subscribe to compManagerRequest
subTopic = 'compManagerRequest'
subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())
print("Comp Manager subscribing to: " + subTopic + "\n")

#Set up a poller
poller = zmq.Poller()
poller.register(subSocket, zmq.POLLIN)

while((currentTime - startTime) < ttl):
    #Check for stop signal 1 second timeout
    socks = dict(poller.poll(1000))
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
