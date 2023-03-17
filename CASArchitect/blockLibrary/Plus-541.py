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
    #globals
    turnRadius = 100 #Actually 96

    while True:
        #Receive the data
        topic = subSocket.recv_string()
        data = subSocket.recv_json()

        #Process it
        if(data['signalTag'] == 'envUpdate'):
            goalX = data['goalX']
            goalY = data['goalY']
            planeX = data['planeX']
            planeY = data['planeY']
            planeOrientation = data['planeOrientation']

            #Now, get the two angles
            leftAngle = planeOrientation + 90
            rightAngle = planeOrientation - 90
            if rightAngle < 0:
                rightAngle = 360 + rightAngle

            #Now, calculate a point in those directions
            leftPointX = planeX + (turnRadius * math.cos(math.radians(leftAngle)))
            leftPointY = planeY + (turnRadius * -(math.sin(math.radians(leftAngle)))) #To switch to the flipped y coordinates

            rightPointX = planeX + (turnRadius * math.cos(math.radians(rightAngle)))
            rightPointY = planeY + (turnRadius * -(math.sin(math.radians(rightAngle))))

            #Now, check the distance of the target point from both of these points
            leftDistance = math.sqrt(((leftPointX - goalX)**2) + ((leftPointY - goalY)**2))
            rightDistance = math.sqrt(((rightPointX - goalX)**2) + ((rightPointY - goalY)**2))

            #Print those to check
            #print("The left distance is: " + str(leftDistance))
            #print("The right distance is: " + str(rightDistance))

            print("The closer one is: " + str(min(leftDistance,rightDistance)))

            #Apply a push out force on the degree movement (To push it out so its reachable)
            inDistance = (turnRadius - (min(leftDistance,rightDistance)))
            pushOutForce = (1/10)*((inDistance + 10)**3)
            if inDistance < 0:
                pushOutForce = 0
            #((1/5)* inDistance) + math.copysign( #(1)*((1.03**(self.turnRadius - (min(leftDistance,rightDistance))))) - 2



            #Send it
            print("Plus sending")
            sendData = {'componentType': 'plus', 'force': pushOutForce}

            #Calculate right and left points

            #Publish it
            pubTopic = pubTopics[0]
            pubSocket.send_string(pubTopic, zmq.SNDMORE)
            pubSocket.send_json(sendData)
