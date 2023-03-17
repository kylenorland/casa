#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 2/8/21
Description: Class libraries for subblocks
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
from collections import deque

class Reciever:
    def __init__(self, context, sharedMemory, proxyOutputPort, subTopics):
        #context = zmq.Context()
        subSocket = context.socket(zmq.SUB)
        subSocket.connect("tcp://127.0.0.1:" + str(proxyOutputPort))

        for subTopic in subTopics:
            subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())

        #Subscribe to the command chain.
        subTopic = 'commandChain'
        subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())

        #Set up poller (Some code from: https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/multisocket/zmqpoller.html)
        self.poller = zmq.Poller()
        self.poller.register(subSocket, zmq.POLLIN)

    def recieve(self, sharedMemory):
        #Make sure there's a return value to give
        keepRunning = True

        #Poll the sockets
        socks = dict(self.poller.poll(500))
        for socket in socks:
            topic = socket.recv_string()
            data = socket.recv_json()

            #Check if its a command argument

            if topic == "commandChain":
                if data['command'] == 'stop':
                #Shut down.
                    keepRunning = False
            else:
                sharedMemory['recieveQueue'].appendleft(data)
                print("Recieved: " + str(data))

        return keepRunning


class Sender:
    def __init__(self, context, sharedMemory, proxyInputPort, pubTopics):
        self.pubSocket = context.socket(zmq.PUB)
        self.pubSocket.connect("tcp://127.0.0.1:" + str(proxyInputPort))
        self.pubTopics = pubTopics
        self.sharedMemory = sharedMemory

    def send(self, sharedMemory):
        #Pop off the queue;
        if len(sharedMemory['sendQueue']) > 0:
            data = sharedMemory['sendQueue'].pop()
            #Publish it
            print("sending: " + str(data))
            self.pubSocket.send_string(self.pubTopics[0], zmq.SNDMORE)
            self.pubSocket.send_json(data)


class AddOne:
    def __init__(self, sharedMemory):
        self.sharedMemory = sharedMemory

    def add(self):
        if len(self.sharedMemory['recieveQueue']) > 0:
            print("Adding")
            inObject = self.sharedMemory['recieveQueue'].pop()
            inData = float(inObject['signal'])
            outData = str(inData + 1)
            outObject = {"tag": "Generic", "signal": outData}
            self.sharedMemory['sendQueue'].appendleft(outObject)




class Source:
    def __init__(self, PubSub, initData):
        self.addAmount = 1
        self.blockName = initData['blockName']
        self.pubSub = PubSub
        self.inQ = collections.deque()
        self.outQ = collections.deque()
        self.subscribeSignals = None #initData['subTopics'][0]
        self.publishSignals = initData['pubTopics'][0]


    def run(self):
        #Process
        outputData = {'signalName': self.publishSignals, 'value': 1}

        #Publish
        self.pubSub.inQ.appendleft(outputData)

class Adder:
    def __init__(self, PubSub, initData):
        self.addAmount = 1
        self.blockName = initData['blockName']
        self.pubSub = PubSub
        self.inQ = collections.deque()
        self.outQ = collections.deque()
        self.subscribeSignals = initData['subTopics'][0]
        self.publishSignals = initData['pubTopics'][0]

    def run(self):
        while len(self.inQ) > 0:
            #Recieve
            data = self.inQ.pop()
            print(self.blockName + "recieved: " + str(data))

            #Process
            outputData = {'signalName': self.publishSignals, 'value': data['value'] + self.addAmount }

            #Publish
            self.pubSub.inQ.appendleft(outputData)

class Sink:
    def __init__(self, PubSub, initData):
        self.addAmount = 1
        self.blockName = initData['blockName']
        self.pubSub = PubSub
        self.inQ = collections.deque()
        self.outQ = collections.deque()
        self.subscribeSignals = initData['subTopics'][0]
        self.publishSignals = None #initData['pubTopics'][0]

    def run(self):
        while len(self.inQ) > 0:
            #Recieve
            data = self.inQ.pop()
            print(self.blockName + "recieved: " + str(data))

            #Process
            outputData = {'signalName': self.publishSignals, 'value': data['value']}

            print("System output is: " + str(outputData['value']))

class Subtractor:
    def __init__(self, PubSub):
        self.subtractAmount = 1
        self.pubSub = PubSub

class PubSub:
    def __init__(self):
        self.inQ = collections.deque()
        self.outQ = collections.deque()
        self.subscriptions = {}

    def addPublisher(self, signalName, publisher):
        if signalName not in self.subscriptions:
            self.subscriptions[signalName] = []

    def addSubscriber(self, signalName, subscriber):
        if signalName not in self.subscriptions:
            self.subscriptions[signalName] = []
        else:
            #If entry exists already
            self.subscriptions[signalName].append(subscriber)

    def run(self):
        while len(self.inQ) > 0:
            #Recieve
            data = self.inQ.pop()

            #Process
            #Nothing

            #Publish
            for subscriber in self.subscriptions[data['signalName']]:
                subscriber.inQ.appendleft(data)
