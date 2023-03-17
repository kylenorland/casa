#Head Material
#leftPorts=0
#rightPorts=0
#done


import zmq
import sys
import json


#-----Defaults------------
subPort = 8000
pubPort = 9000

#-----------------------------------
#-----Load sub/pub ports from args--
#-----------------------------------
logfile = open("blockLogs/commsLog.txt", "w")
logfile.write("Got to here")

numArgs = len(sys.argv)
logfile.write("There are " + str(numArgs) + " arguments" + "\n")
print("There are " + str(numArgs) + " arguments")

if numArgs >= 3:
    subPort = int(sys.argv[1])
    pubPort = int(sys.argv[2])


#Set up context
context = zmq.Context()

#Set up XSUB socket
xSubSocket = context.socket(zmq.XSUB)
try:
    xSubSocket.bind("tcp://127.0.0.1:" + str(subPort))
except:
    print("Sub-socket binding failed")
    logfile.write("Sub-socket binding failed")

#Set up XPUB socket
xPubSocket = context.socket(zmq.XPUB)


try:
    xPubSocket.bind("tcp://127.0.0.1:" + str(pubPort))
except:
    print("Pub-socket binding failed")


print("Starting proxy")

logfile.write("Sockets bound correctly")
logfile.close()

newProxy = zmq.proxy(xSubSocket, xPubSocket, None)
newProxy.start()
'''
#Forwarding
print("Listening for messages")
while True:
    message = xSubSocket.recv_string()
    print("Received ")
    print(message)
    xPubSocket.send_multipart(message)
'''
