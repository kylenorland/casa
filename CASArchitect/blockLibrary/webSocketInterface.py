#Head Material
#leftPorts=1
#rightPorts=1
#done


#Block Description
'''
Author: Kyle Norland
Date: 9/21/20
Description: Translates between websockets and zmq.
'''
#---------------------------------
#-------------Imports---------
#---------------------------------
import zmq
import json
import time
import sys
import asyncio
import websockets

from collections import deque

#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = []
pubTopics = ['cats']
blockName = "source--"


logfile = open("blockLogs/webSocketIntLog.txt", "w")
logfile.write("Starting at: " + str(time.time()) + "\n")
print("Web socket interface starting at: " + str(time.time()) + "\n")
#------------------
#--Pull arguments--
#------------------
numArgs = len(sys.argv)
#print("There are " + str(numArgs) + " arguments")

if numArgs >= 3:
    proxyInputPort = int(sys.argv[1])
    proxyOutputPort = int(sys.argv[2])
    stringArchitecture = sys.argv[3]
    try:
        #print(stringArchitecture)
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


#-------------------------------------------------------------
#Define and start a websocket server that waits for websocket info and puts it
#on the zmq wire.

print("Web Socket Listening \n")

async def echo(websocket, path):
    ##NOTE: Replaced for compatibility with python 3.5
    #async for message in websocket:
    while True:
        message = await websocket.recv()
        data = json.loads(message)  #Load message from web socket
        pubTopic = data["sender"]  #pubTopic is the original modules globalId
        sendData = data["message"]  #data is the original message from the javascript
        print(pubTopic + ": " + str(sendData)+ "\n")

        pubSocket.send_string(pubTopic, zmq.SNDMORE)
        pubSocket.send_json(sendData)

        response = "Sent message"
        await websocket.send(response)

start_server = websockets.serve(echo, "localhost", 9615)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
