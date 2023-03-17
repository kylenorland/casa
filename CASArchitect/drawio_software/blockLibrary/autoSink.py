#Head Material
#leftPorts=1
#rightPorts=0
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
subTopics = ['bats']
pubTopics = []
data = "value"
blockName = "sinkBlock"

with open("blockLogs/sinkLog.txt", "w") as logFile:
    logFile.write(str(time.localtime()))
    #------------------
    #--Pull arguments--
    #------------------
    numArgs = len(sys.argv)
    print("There are " + str(numArgs) + " arguments")
    logFile.write("There are " + str(numArgs) + " arguments" + "\n")

    if numArgs >= 3:
        proxyInputPort = int(sys.argv[1])
        proxyOutputPort = int(sys.argv[2])
        stringArchitecture = sys.argv[3]
        try:
            jsonArch = json.loads(stringArchitecture)
            subTopics = jsonArch['subTopics']
            pubTopics = jsonArch['pubTopics']
            blockName = jsonArch['blockName']

        except:
            logFile.write("Something in the json loading process broke" + "\n")
    #------------------

    #---------------------------------------
    #-------Connect to the sockets----------
    #---------------------------------------
    context = zmq.Context()

    pubSocket = context.socket(zmq.PUB)
    pubSocket.connect("tcp://127.0.0.1:" + str(proxyInputPort)) #NOT BIND!!

    subSocket = context.socket(zmq.SUB)
    subSocket.connect("tcp://127.0.0.1:" + str(proxyOutputPort))

    for subTopic in subTopics:
        print(subTopic)
        subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())


    #------------------------------------------
    #--------RUN LOOP------------------------
    #--------------------------------------

    while True:
        #Receive the data
        topic = subSocket.recv_string()
        data = subSocket.recv_json()

        #Process it
        #No processing

        #Print it to file
        logFile.write(topic + ": " + str(data) + "\n")
        print("sink recieved", data)
    #---------------------------------------------------------------





