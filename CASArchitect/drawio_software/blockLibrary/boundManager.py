#Head Material
#leftPorts=0
#rightPorts=0
#done


#Block Description
'''
Author: Kyle Norland
Date: 10/5/20
Description: Boundary manager that rejects messages from internal ids
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

with open("blockLogs/boundLog.txt", "w") as logfile:
    logfile.write(str(time.localtime()))
    #------------------
    #--Pull arguments--
    #------------------
    numArgs = len(sys.argv)
    logfile.write("There are " + str(numArgs) + " arguments" + "\n")
    #print("There are " + str(numArgs) + " arguments")

    if numArgs >= 3:
        proxyInputPort = int(sys.argv[1])
        proxyOutputPort = int(sys.argv[2])
        stringArchitecture = sys.argv[3]
        try:
            jsonArch = json.loads(stringArchitecture)
            subTopics = jsonArch['subTopics']
            pubTopics = jsonArch['pubTopics']
            blockName = jsonArch['blockName']
            participatingIps = jsonArch['participatingIps']
            internalIds = jsonArch['internalIds']
            externalSubs = jsonArch['externalSubs']
            computerIp = jsonArch['computerIp']
            #print("boundManager participating ips are: " + str(participatingIps))
            #print("boundManager internal ids are: " + str(internalIds))
            #print("computer ip is: " + str(computerIp))
        except:
            logfile.write("Something in the json loading process broke"+ "\n")
            print("Something in the json loading process broke")

    #------------------------------------------
    #-------Connect to the sockets (modified)--
    #------------------------------------------
    #polls: all local messages, external boundManagers (not self)
    #outputs to self, internal input.
    subSocketList = []   #All except for localProxySocket
    pubSocketList = []

    #ZMQ Context
    context = zmq.Context()

    #Set up poller (Some code from: https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/multisocket/zmqpoller.html)
    poller = zmq.Poller()

    #Local Proxy
    localProxySocket = context.socket(zmq.SUB)
    localProxySocket.connect("tcp://127.0.0.1:" + str(proxyOutputPort))
    localProxySocket.setsockopt_string(zmq.SUBSCRIBE, "")
    poller.register(localProxySocket, zmq.POLLIN)

    #Register external boundary managers
    for extBoundIp in participatingIps:
        if extBoundIp != computerIp:    #Don't select self
            subSocket = context.socket(zmq.SUB)
            socketAddress = "tcp://" + str(extBoundIp) + ":" + "9846"
            subSocket.connect(socketAddress)
            subSocket.setsockopt_string(zmq.SUBSCRIBE, "")
            subSocketList.append(subSocket)
            poller.register(subSocket, zmq.POLLIN)

    #Register publish sockets
    #Internal to the loopback ip on the proxy input port.
    internalPubSocket = context.socket(zmq.PUB)
    internalPubSocket.connect("tcp://127.0.0.1:" + str(proxyInputPort))
    pubSocketList.append(internalPubSocket)

    #External to port 9846 on the local ip
    externalPubSocket = context.socket(zmq.PUB)
    externalPubSocket.bind("tcp://0.0.0.0:" + "9846") #Bind since it's not connecting to proxy
    pubSocketList.append(externalPubSocket)

    #-------------------------------------------------------------
    #----------Run Loop (polls, checks and forwards)------------
    #-------------------------------------------------------------
    #Basic run pattern: Poll, (log), check against internal ids, publish
    print("starting loop")
    while True:
        socks = dict(poller.poll(500))
        for socket in socks:
            topic = socket.recv_string()
            data = socket.recv_json()

            #Check if message is from internal, if it is, send out only local ids.
            if socket == localProxySocket:
                print("From local proxy socket: " + str(topic))
                if topic in internalIds:
                    externalPubSocket.send_string(topic, zmq.SNDMORE)
                    externalPubSocket.send_json(data)

            #If message from external, don't allow local ids and check for known subscriptions
            if socket != localProxySocket:
                #print("Not from local proxy socket")
                if (topic not in internalIds) and (topic in externalSubs):
                    #Forward to internal
                    internalPubSocket.send_string(topic, zmq.SNDMORE)
                    internalPubSocket.send_json(data)
