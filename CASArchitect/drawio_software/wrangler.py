#Kyle Norland
#8-9-22
#Single message board memory. Functional agents. One thread, so should be quick functions.
#Dependencies: Library, codeTree, running guiWrangler

#---------------------------------------------------------
#----------------Library Imports--------------------------
#---------------------------------------------------------

import library
import json
from inspect import getmembers, isfunction
import time
import zmq
import collections
import os

#Initialize zmq
context = zmq.Context()
outSocket = context.socket(zmq.PUB)
outSocket.bind("tcp://127.0.0.1:9000")

inSocket = context.socket(zmq.SUB)
inSocket.connect("tcp://127.0.0.1:8000")
inSocket.setsockopt_string(zmq.SUBSCRIBE, "")

'''
#Initialize internal queues
gMQ = collections.deque()
outMessages = collections.deque()
'''
#--------------------------------------------
#-----Initialize Internal Memory Structures--
#--------------------------------------------
message_board = []
next_message_board = []


#--------------------------------------------------------------
#------------Initialize agents from codeTree file.-------------
#--------------------------------------------------------------
#Load graph
with open(os.path.join('outputs',"codeTree.txt"), "r") as graphFile:
    graphDict = json.loads(graphFile.read())

#See what functions are available in the library.
availFuncts = []
for member in getmembers(library, isfunction):
    availFuncts.append(member[0])


print("The available functions are:")
for funct in availFuncts:
    print(funct)
print("\n")

#Assemble graph into code
vertices = graphDict['vertices']
function_agents = []

for vertex in vertices:
    if vertex['value'] in availFuncts:
        print(vertex['value'], " is available")
        function_agents.append(vertex)

#--------------------------------------
#--------------Run Loop---------------
#---------------------------------------
keep_running = True

while keep_running:
    #Load in all incoming external messages
    if inSocket.poll(1) == zmq.POLLIN:
        while inSocket.poll(1) == zmq.POLLIN:
            topic = inSocket.recv_string()
            data = inSocket.recv_json()
            message_board.append({'tag': topic, 'signal': data})
            print("New external message: ", topic, " ", data)

    #For each agent, check if a message on the board matches their input criteria
    #If so, run the function with signal as input.
    #Message format {tag: xx, signal: xx or {}}
    #if len(message_board) > 0:
        #print("Message Board")
        #for message in message_board: print(message)
    
    for agent in function_agents:
        for message in message_board:
            #print(message['tag'], agent['inputs'])
            if int(message['tag']) in agent['inputs']:
                #print("matched")
                func_to_run = getattr(library, agent['value'])
                result = func_to_run(message['signal'])
                
                next_message_board.append({'tag': agent['id'], 'signal': result})

    #Update the message board and clear the next one
    message_board = next_message_board[:]
    next_message_board = []

    #Sleep a little
    if len(message_board) > 0:
        time.sleep(0.001)
    else:
        time.sleep(0.1)




'''
#---------------------------------------
#--Establish external output/input loop-
#---------------------------------------
keep_running = True

while keep_running:
    #Get all messages in input queue if they exist:
    if len(gMQ) == 0:
        topic = inSocket.recv_string()
        data = inSocket.recv_json()
        gMQ.appendleft({'tag': topic, 'signal': data})

    if len(gMQ) > 0:
        print('hi')
        message = gMQ.pop()
        #Internal handling
        for object in objectList:
            object.handleMessage(message)
        #Send to external
        outMessages.appendleft(message)

    #Send the outgoing messages
    if len(outMessages) > 0:
        outMessage = outMessages.pop()
        print(outMessage)
        outSocket.send_string(str(outMessage['tag']), zmq.SNDMORE)
        outSocket.send_json(outMessage['signal'])


def addOne(message):
    message['value'] = int(message['value']) + 1
    return message

def printOut(message):
    print("Printing Message")
    print(message)





class FunctionRunner():
    def __init__(self, vertex, functionRoot, master=None):
        self.id = vertex['id']
        self.inputs = vertex['inputs']
        self.outputs = vertex['outputs']
        self.functionRoot = functionRoot

    def handleMessage(self, message):
        global gMQ
        if int(message['tag']) in self.inputs:
            print("Recieved message from: " + str(message['tag']))
            gMQ.appendleft({'tag':self.id, 'signal':'hi'})






#-----------Run the app-----------------------
initialize()
while True:
    runLoop()
'''
