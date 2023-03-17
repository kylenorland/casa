#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 2/3/21
Description: Python block that coordinates internal c or python classes.
Reference: https://realpython.com/python-bindings-overview/

'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
from collections import deque
import subBlockLib

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


    #-----------------------------------------
    #----------Determine Desired Libraries/Architecture-----
    #-----------------------------------------

    #------------------------------------------
    #-------------Python Bindings Practice-----
    #------------------------------------------

    #Generate classes
    #Always generate pubSub
    pubSub = subBlockLib.PubSub()

    blockList = []

    #From json
    for block in configJson:
        if block['class'] == "Source":
            newBlock = subBlockLib.Source(pubSub, block)
            pubSub.addPublisher(block['pubTopics'][0], newBlock)
            blockList.append(newBlock)

        if block['class'] == "Adder":
            newBlock = subBlockLib.Adder(pubSub, block)
            pubSub.addSubscriber(block['subTopics'][0], newBlock)
            pubSub.addPublisher(block['pubTopics'][0], newBlock)
            blockList.append(newBlock)

        if block ['class'] == "Sink":
            newBlock = subBlockLib.Sink(pubSub, block)
            pubSub.addSubscriber(block['subTopics'][0], newBlock)
            blockList.append(newBlock)



    #Run loop
    #Initial signal
    #pubSub.inQ.appendleft({"signalName":"1", "value": 1})
    for i in range(0,100):
        pubSub.run()
        for block in blockList:
            block.run()
