#Author: Kyle Norland
#Date: Updated 3/14/23
#Description: Container class for Tkinter objects within CASA

#---------------------------------------------------
#---------------------Imports-----------------------
#---------------------------------------------------
import json
from inspect import getmembers, isfunction
import time
import zmq
import collections

from tkinter import *
from tkinter import ttk
import os
import sys

#--------------------------------------------------------
#------------------Classes and Functions-----------------
#--------------------------------------------------------
class ButtonObj():
    def __init__(self, vertex, outMessages, master=None):
        self.id = vertex['id']
        self.inputs = vertex['inputs']
        self.outputs = vertex['outputs']
        self.outMessages = outMessages

    def buttonHandler(self):
        print("Button Clicked")
        self.outMessages.appendleft({"tag":self.id, "signal": {'tag': 'start_run', 'signal': {'value':1}}})

    def handleMessage(self, message):
        if message['tag'] in self.inputs:
            print("Recieved message from: " + message['tag'])

'''
class TextBoxObj():
        def __init__(self, vertex, master=None):
            self.id = vertex['id']
            self.inputs = vertex['inputs']
            self.outputs = vertex['outputs']

        def handleMessage(self, message):
            if message['tag'] in self.inputs:
                print("Recieved message from: " + str(message['tag']))
                global idList
                if message['tag'] in idList:
                    gMQ.appendleft({'tag':self.id, 'signal':self.textbox.get()})
                else:
                    print("Recieved external content")
'''

class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master

        # widget can take all window
        self.pack(fill=BOTH, expand=1)


class Gui_Container:
    def __init__(self):   
        print("initializing gui container")
        
        #------------Initialize internal data structures---------------
        #gMQ is an input queue.
        #outMessages is an output queue
        
        self.gMQ = collections.deque()
        self.outMessages = collections.deque()
        self.objectList = []
        self.idList = []
        self.subTopics = []

        
    def init_gui(self, gui_file):
        #----------Load gui file and initialize sub_objects-------------
        #Load graph
        with open(gui_file, "r") as graphFile:
            self.gui_dict = json.loads(graphFile.read())        
        
        #Init tk root
        self.root = Tk()
        
        #Init Window
        self.app = Window(self.root)

        #Create subobjects from vertices
        for vertex in self.gui_dict['vertices']:
            if vertex['value'] == "Button":
                newObject = ButtonObj(vertex, self.gMQ)
                
                #self.app should attach it to generated window
                newButton = Button(
                self.app, 
                text=vertex['value'], 
                command = newObject.buttonHandler, 
                width = int(float(vertex['width']) * 1/6) , 
                height = int(float(vertex['height']) * 1/14),
                background='#00BFFF',
                )
                
                newButton.place(x=int(vertex['x']), y=int(vertex['y']))
                newObject.button = newButton
                self.objectList.append(newObject)
                self.idList.append(newObject.id)
        
        #Get the inputs to subscribe to.
        for vertex in self.gui_dict['vertices']:
            self.subTopics.extend(vertex['inputs'])

        
            '''
            if vertex['value'] == "TextBox":
                newObject = TextBoxObj(vertex)
                newTextBox = Entry()
                newTextBox.place(x=int(vertex['x']), y=int(vertex['y']))
                newObject.textbox = newTextBox
                objectList.append(newObject)
                idList.append(newObject.id)
            '''  
                
        #Other tkinter
        self.root.wm_title("CASArchitect Front End -By Kyle Norland")
        self.root.iconbitmap('logo.ico')
        self.root.geometry("600x600")
        #self.root.configure(background='yellow')
        #self.root['bg'] = 'yellow'

    def init_zmq(self):
        self.context = zmq.Context()
        #self.pubTopics = pubTopics

        self.pubSocket = self.context.socket(zmq.PUB)
        self.pubSocket.connect("tcp://127.0.0.1:" + str(proxyInputPort))

        self.subSocket = self.context.socket(zmq.SUB)
        self.subSocket.connect("tcp://127.0.0.1:" + str(proxyOutputPort))

        #------------Subscribe to general topics---------------------
        for subTopic in self.subTopics:
            self.subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())

        #--------------Subscribe to the command chain.----------------
        subTopic = 'commandChain'
        self.subSocket.setsockopt(zmq.SUBSCRIBE, subTopic.encode())

        #-----------------Set up poller------------------------- 
        #(Some code from: https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/multisocket/zmqpoller.html)
        self.poller = zmq.Poller()
        self.poller.register(self.subSocket, zmq.POLLIN)
        
    def init_run_details(self, env):
        #Init the environment
        self.env = init_environment(run['env_config'])

    def handle_messages(self):
        #Check gMQ
        #print("gMQ")
        #print(self.gMQ)
        
        #Add code to get external messages
        
        #If message queue active, handle the messages
        if len(self.gMQ) > 0:
            message = self.gMQ.pop()
            #Internal handling
            for entry in self.objectList:
                entry.handleMessage(message)

            #Send to external
            self.outMessages.appendleft(message)

        #Send the outgoing messages
        #print("outgoing messages")
        #print(self.outMessages)
        if len(self.outMessages) > 0:
            outMessage = self.outMessages.pop()
            print('gui_container sending', outMessage)
            #Channel
            self.pubSocket.send_string(str(outMessage['tag']), zmq.SNDMORE)
            
            #Message
            self.pubSocket.send_json(outMessage['signal'])

        self.root.after(10, self.handle_messages)        
        
       
        '''
        #print("Preparing to poll")
        #----Poll-------------
        socks = dict(self.poller.poll(500))
        #print("socks", socks)
        
        #-----Read In--------
        for socket in socks:
            topic = socket.recv_string()
            message = socket.recv_json()

            print(self.blockName, 'recieved ' message)
            #--------------Check if its a command argument-----------
            if topic == "commandChain":
                if message['command'] == 'stop':
                #Shut down.
                    keepRunning = False
                    print("Generator shutting down")
            
            #-------If button click---------------
            if message['tag'] == 'button_click':
                
                #For now, send simple state message.
                out_message = {"tag": "action_request", "signal": {'state': 2}}
                
                print(self.blockName, 'sending' message)

                #Publish it
                pubSocket.send_string(pubTopics[0], zmq.SNDMORE)
                pubSocket.send_json(out_message)
        '''

#---------------------Initialize -----------------------
#Defaults:
proxyInputPort = 8000
proxyOutputPort = 9000
subTopics = []
pubTopics = ['cats']
blockName = "source--"


#logfile = open("blockLogs/gui_container.txt", "w")
#logfile.write("Got to here")

#------------------
#--Pull arguments--
#------------------
numArgs = len(sys.argv)
print("There are " + str(numArgs) + " arguments")


#Load comms manager ports
if numArgs >= 2:

    proxyInputPort = int(sys.argv[1])
    proxyOutputPort = int(sys.argv[2])
   
    
    '''
    stringArchitecture = sys.argv[3]
    try:
        print(stringArchitecture)
        jsonArch = json.loads(stringArchitecture)
        subTopics = jsonArch['subTopics']
        pubTopics = jsonArch['pubTopics']
        blockName = jsonArch['blockName']
    except:
        print("Something in the json loading process broke")
    '''
 

#Init Core Gui Details
gui_container = Gui_Container() 

#Init GUI
gui_container.init_gui(os.path.join('outputs', 'guiTree.json'))


#Init zmq             
gui_container.init_zmq()


#Init unique components.

#----------------------Run loop---------------------------
gui_container.root.after(500,gui_container.handle_messages)
gui_container.root.mainloop()




'''
#----------------------Run loop---------------------------
i = 0
print(env_wrapper.blockName, "starting")
keepRunning = True
while keepRunning:
    env_wrapper.handle_messages()




#Initialize zmq
context = zmq.Context()
outSocket = context.socket(zmq.PUB)
outSocket.bind("tcp://127.0.0.1:8000")

inSocket = context.socket(zmq.SUB)
inSocket.connect("tcp://127.0.0.1:9000")
inSocket.setsockopt_string(zmq.SUBSCRIBE, "")

#Initialize internal queues
gMQ = collections.deque()
outMessages = collections.deque()
objectList = []
idList = []

#-----------Run the app-----------------------
root = Tk()
app = Window(root)
root.wm_title("Autogen Front End -By Kyle Norland")
root.geometry("800x600")
root.after(500,runLoop)
root.mainloop()
'''