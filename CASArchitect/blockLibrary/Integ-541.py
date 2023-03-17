#Head Material
#leftPorts=1
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
import math
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


    #-------------------------------------------------------------

    #Globals
    pWeight = 0.5
    iWeight = 0.1
    dWeight = 0
    plusWeight = 1

    #Set up poller (Some code from: https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/multisocket/zmqpoller.html)
    poller = zmq.Poller()
    poller.register(subSocket, zmq.POLLIN)

    while True:
        #Reset recieved flags and current values
        pValRecieved = False
        iValRecieved = False
        dValRecieved = False
        plusValRecieved = False

        #Current values
        pValue = 0
        iValue = 0
        dValue = 0
        plusValue = 0

        #Loop through the message in queue and gather all new values.
        areMessages = True
        while areMessages == True:
            socks = dict(poller.poll(100))
            #print("The socket length is: " + str(len(socks)))
            if len(socks) > 0:
                topic = subSocket.recv_string()
                data = subSocket.recv_json()
                #print(topic)
                print("Combiner recieving data: " + str(data))

                #Update the current weighted values
                if data['componentType'] == 'proportional':
                    pValue = pWeight * data['force']
                    pValRecieved = True
                elif data['componentType'] == 'integral':
                    iValue = iWeight * data['force']
                    iValRecieved = True
                elif data['componentType'] == 'derivative':
                    dValue = dWeight * data['force']
                elif data['componentType'] == 'plus':
                    plusValue = plusWeight * data['force']

            else:
                areMessages = False
            #Once messages processed, set to false again.
            #areMessages = False
        #Receive the data until the queue is empty (Watch for error)
        #topic = subSocket.recv_string()
        #data = subSocket.recv_json()



        #Combine the weighted values and send if any are present
        if pValRecieved or iValRecieved or dValRecieved or plusValRecieved:
            print("Individual forces: " + str(pValue) + " " + str(iValue) + " " + str(dValue) + " " + str(((-1* math.copysign(1,pValue) * plusValue))))
            totalForce = pValue + iValue + dValue + ((-1* math.copysign(1,pValue) * plusValue))
            print("Combined force: " + str(totalForce))
            if(abs(totalForce) < 3):
                restrictedForce = totalForce
            else:
                restrictedForce = (math.copysign(1,totalForce) * 3)
            sendData = {'signalTag': 'combinedForce', 'force': totalForce, 'restrictedForce': restrictedForce, 'pValue': pValue, 'iValue': iValue, 'plusValue': (-1* math.copysign(1,pValue) * plusValue)}

            #Send the combined value on to the next block
            pubTopic = pubTopics[0]
            pubSocket.send_string(pubTopic, zmq.SNDMORE)
            pubSocket.send_json(sendData)
