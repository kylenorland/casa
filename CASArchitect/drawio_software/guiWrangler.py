import library
import json
from inspect import getmembers, isfunction
import time
import zmq
import collections

from tkinter import *
from tkinter import ttk
import os


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


def runLoop():
    if len(gMQ) > 0:
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

    root.after(10, runLoop)




class ButtonObj():
    def __init__(self, vertex, master=None):
        self.id = vertex['id']
        self.inputs = vertex['inputs']
        self.outputs = vertex['outputs']

    def buttonHandler(self):
        print("Button Clicked")
        gMQ.appendleft({"tag":self.id, "signal": {'value':1}})

    def handleMessage(self, message):
        if message['tag'] in self.inputs:
            print("Recieved message from: " + message['tag'])


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





class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master

        # widget can take all window
        self.pack(fill=BOTH, expand=1)


        #Load graph
        with open(os.path.join('outputs',"guiTree.txt"), "r") as graphFile:
            graphDict = json.loads(graphFile.read())

        #Assemble graph into code
        #Ignore parent entries for now. Just pull out a chain.

        vertices = graphDict['vertices']

        #Create buttons from vertices
        for vertex in vertices:
            if vertex['value'] == "Button":
                newObject = ButtonObj(vertex)
                newButton = Button(self, text=vertex['value'], command = newObject.buttonHandler, width = int(float(vertex['width']) * 1/6) , height = int(float(vertex['height']) * 1/14))
                newButton.place(x=int(vertex['x']), y=int(vertex['y']))
                newObject.button = newButton
                objectList.append(newObject)
                idList.append(newObject.id)

            if vertex['value'] == "TextBox":
                newObject = TextBoxObj(vertex)
                newTextBox = Entry()
                newTextBox.place(x=int(vertex['x']), y=int(vertex['y']))
                newObject.textbox = newTextBox
                objectList.append(newObject)
                idList.append(newObject.id)



#-----------Run the app-----------------------
root = Tk()
app = Window(root)
root.wm_title("Autogen Front End -By Kyle Norland")
root.geometry("800x600")
root.after(500,runLoop)
root.mainloop()









#Run loop
