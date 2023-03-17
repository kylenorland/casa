#Head Material
#leftPorts=0
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 9/9/20
Description: General purpose block template
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
from collections import deque

#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = []
pubTopics = ['cats']
blockName = "source--"


logfile = open("blockLogs/generatorLog.txt", "w")
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

#---------------------------------------
#-------Connect to the sockets----------
#---------------------------------------
context = zmq.Context()

pubSocket = context.socket(zmq.PUB)
pubSocket.connect("tcp://127.0.0.1:" + str(proxyInputPort))

subSocket = context.socket(zmq.SUB)
subSocket.connect("tcp://127.0.0.1:" + str(proxyOutputPort))


for subTopic in subTopics:
    subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())

#Subscribe to the command chain.
subTopic = 'commandChain'
subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())

#-------------------------------------------------------------
logfile.write("Publishing to: " + str(pubTopics[0]))

#Set up poller (Some code from: https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/multisocket/zmqpoller.html)
poller = zmq.Poller()
poller.register(subSocket, zmq.POLLIN)

i = 0
keepRunning = True
while keepRunning:
    socks = dict(poller.poll(500))
    for socket in socks:
        topic = socket.recv_string()
        data = socket.recv_json()

        #Check if its a command argument
        if topic == "commandChain":
            if data['command'] == 'stop':
            #Shut down.
                keepRunning = False
                print("Generator shutting down")

    #Generate the data
    data = {"tag": "Generic", "signal": str(i)}
    i += 1
    print(data['signal'])
    logfile.write(pubTopics[0] + ": " + data['signal']+ "\n")

    #Publish it
    pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
    pubSocket.send_json(data)

    time.sleep(0.25)
