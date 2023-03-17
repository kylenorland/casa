#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 11/10/20
Description: Integral Controller for 541 Project
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
subTopics = ['cats']
pubTopics = ['bats']
data = "value"
blockName = "mid block--"
with open("blockLogs/midLog.txt", "w") as logfile:
    logfile.write(str(time.localtime()))
    #------------------
    #--Pull arguments--
    #------------------
    numArgs = len(sys.argv)
    logfile.write("There are " + str(numArgs) + " arguments" + "\n")
    print("There are " + str(numArgs) + " arguments")

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
            logfile.write("Something in the json loading process broke"+ "\n")
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
        logfile.write("Subscribing to: " + subTopic + "\n")

    #----------------------------------------------
    #---------Run Loop---------------------
    #-------------------------------------------------------------
    #Globals/constants
    memoryLength = 5
    memoryList = deque()


    print("I block running")
    while True:
        #Reset total values
        totalIntegral = 0

        #Receive the data
        topic = subSocket.recv_string()
        data = subSocket.recv_json()
        #print("I block recieved: " + str(data))

            #Process it
        if(data['signalTag'] == 'envUpdate'):
            error = data['error']

            #Add to list;
            memoryList.appendleft(error)

            #Drop one if it's greater than the memory length;
            if len(memoryList) > memoryLength:
                memoryList.pop()

            #Calculate the total
            for entry in memoryList:
                totalIntegral += float(entry)

            sendData = {'componentType': 'integral', 'force': totalIntegral}
            print("I block sending")
            #Publish it
            pubTopic = pubTopics[0]
            pubSocket.send_string(pubTopic, zmq.SNDMORE)
            pubSocket.send_json(sendData)
