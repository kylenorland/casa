import json
import zmq


def printOut(input):
    print(str(input))

def reciever(socket):
    topic = socket.recv_string()
    data = socket.recv_json()
    print("recieved: " + str(data['signal']))
    return float(data['signal'])


#Function Agents:
def covert_to_dict(signal):
    signal_dict = {'value': signal}
    return signal_dict 

def addOne(signal):
    necessary_arguments = ['value']
    print("Running addOne")
    #-------------CHECKS------------------
    if isinstance(signal, (int, float)):
        signal = convert_to_dict(signal)
    
    #Now it should be a dict, check that all arguments are there.
    if isinstance(signal, (dict)):
        for arg in necessary_arguments:
            if arg not in signal:
                return 1
    
    #-----------FUNCTION------------------
    return {'value': signal['value'] + 1}


def printValue(signal):
    necessary_arguments = ['value']
    print("Running printValue")
    
    #-------------CHECKS------------------
    if isinstance(signal, (int, float)):
        signal = convert_to_dict(signal)
    
    #Now it should be a dict, check that all arguments are there.
    if isinstance(signal, (dict)):
        for arg in necessary_arguments:
            if arg not in signal:
                return 1
    
    #-----------FUNCTION------------------
    print(signal['value'])
    return 0  

def Q_Learner(signal):
    necessary_arguments = ['value']
    print("Running addOne")
    #-------------CHECKS------------------
    if isinstance(signal, (int, float)):
        signal = convert_to_dict(signal)
    
    #Now it should be a dict, check that all arguments are there.
    if isinstance(signal, (dict)):
        for arg in necessary_arguments:
            if arg not in signal:
                return 1
    
    #-----------FUNCTION------------------
    return {'value': signal['value'] + 1}

def frozen_lake_v1(signal):
    necessary_arguments = ['value']
    print("Running addOne")
    #-------------CHECKS------------------
    if isinstance(signal, (int, float)):
        signal = convert_to_dict(signal)
    
    #Now it should be a dict, check that all arguments are there.
    if isinstance(signal, (dict)):
        for arg in necessary_arguments:
            if arg not in signal:
                return 1
    
    #-----------FUNCTION------------------
    return {'value': signal['value'] + 1}


#For Looping Agent     
def emit_episode_signal(signal):
    necessary_arguments = ['value']
    print("Running addOne")
    #-------------CHECKS------------------
    if isinstance(signal, (int, float)):
        signal = convert_to_dict(signal)
    
    #Now it should be a dict, check that all arguments are there.
    if isinstance(signal, (dict)):
        for arg in necessary_arguments:
            if arg not in signal:
                return 1
    
    #-----------FUNCTION------------------
    return {'value': signal['value'] + 1}




#Processing Functions
def readCSV():
    #Imports
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from pandas import DataFrame

    #The clustering toolkits
    from sklearn import datasets
    from sklearn.mixture import GaussianMixture
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_samples, silhouette_score

    import csv
    #import quatMath
    import asyncio
    import os
    import sys
    import csv
    import math
    import json
    from numpy import convolve

    #Inputs
    folderPath = "./data/gyro"
    outputFolderPath = "procQuat"

    #Global Data Structures
    rawArrays = []
    fileNames = []
    startTimes = []
    endTimes = []
    interpArrays = []
    avgdArrays = []
    finalArrays = []
    kernelSize = 20

    #Iterate through directory (8 sensor output files), and find the latest start and earliest end to trim the sequence.
    for m in range(0,8):
    		firstSI = m
    		firstName = ""
    		firstArray = []

    		#Get first one
    		fileName = os.listdir(folderPath)[firstSI]
    		firstName = fileName[0:8]
    		print(fileName)
    		fileNames.append(firstName)
    		with open(folderPath + "/" + os.listdir(folderPath)[firstSI], "r") as dataFile:
    			csvReader = csv.reader(dataFile, delimiter=',', quotechar='|')
    			#Skip first row of headers
    			rowIndex = 0
    			for row in csvReader:
    				if rowIndex != 0:
    					newRow = [float(row[0]), float(row[3]), float(row[4]), float(row[5])]
    					firstArray.append(newRow)
    				rowIndex += 1
    			print(rowIndex)

            #Add the characteristics from the data set to the global structures
    		rawArrays.append(firstArray)
    		startTimes.append(firstArray[0][0])
    		endTimes.append(firstArray[-1][0])

    #Record the latest start and earliest finish
    startTime = max(startTimes)
    endTime = min(endTimes)

    #Round them to the nearest 10 ms
    adjStart = math.ceil(startTime/10) * 10 #Round up to nearest 10 milliseconds.
    adjEnd = math.ceil(endTime/10) * 10 #Round up to nearest 10 milliseconds because np.arange doesn't include end point.


    #----------------------------------------------------
    #-----Linearly Interpolate data at 10ms intervals----
    #----------------------------------------------------
    #Generate 10 millisecond spaced points between and including the two end points
    masterX = np.arange(adjStart, adjEnd, 10)

    for m in range(0,8):
    		#Change to numpy array
    		rawArrays[m] = np.array(rawArrays[m])

    		#Initialize blank arrays for x: timestamp, and y: magnitude
    		xVals  = np.zeros(len(rawArrays[m]))
    		yVals = np.zeros(len(rawArrays[m]))

    		for i in range(0, len(rawArrays[m])):
    			row = rawArrays[m][i]
    			xVals[i] = row[0] #Timestamp

                #Calculate magnitude of the data
    			yVals[i] = math.sqrt(float(row[1])**2 + float(row[2])**2 + float(row[3])**2) #Magnitude

            #Interpolate
    		interpArray = np.interp(masterX, xVals, yVals) #Returns yVals for masterX

            #Run a kernel over the data to take a rolling average
    		avgdArray = np.convolve(interpArray, np.ones(kernelSize), 'valid') / kernelSize  #Take rolling average

    		finalArrays.append(avgdArray)
    		#plt.plot(avgdArray, label=(fileNames[m]))

    #Output final array to a csv
    print("finalArrays:", len(rawArrays)," ", len(rawArrays[0]))
    finalArrays = np.array(finalArrays)
    finalArrays = finalArrays.T
    print(finalArrays.shape)
    #Write output to csv
    #Make an intermediate folder if it doesn't exist
    if not os.path.isdir("./data/midstages"): os.mkdir("./data/midstages")

    with open("./data/midstages/" + 'loaded.csv', 'w', newline='') as csvfile:
        for dataline in finalArrays:
            csvwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(dataline)

        print("Finished writing output to csv")

def gmm():
    #Imports
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from pandas import DataFrame

    #The clustering toolkits
    from sklearn import datasets
    from sklearn.mixture import GaussianMixture
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_samples, silhouette_score

    import csv
    #import quatMath
    import asyncio
    import os
    import sys
    import csv
    import math
    import json
    from numpy import convolve

    #----------------------------
    #-------The GMM component (currently independent)----
    #----------------------------
    print("Running gmm on the data")

    preppedArray = []
    with open("./data/midstages/" + 'loaded.csv', "r") as dataFile:
        csvReader = csv.reader(dataFile, delimiter=',', quotechar='|')
        for row in csvReader:
            preppedArray.append(row)

    preppedArray = np.array(preppedArray)
    preppedArray = preppedArray.astype(np.float)
    preppedArray = preppedArray.T
    print("The shape of prepped is ", preppedArray.shape)

    #---------------------------------------------------------------------
    #--------Generate a data frame from the pre-processed data------------
    #---------------------------------------------------------------------
    preppedArray = preppedArray[0:100, 2000:4000]
    print("The incoming shape")
    print(len(preppedArray), len(preppedArray[0]))

    #Initialize the model
    n_components = 4
    gmm = GaussianMixture(n_components = n_components)

    #Fit the model
    gmm.fit(preppedArray)
    labels = gmm.predict(preppedArray)

    print("Labels shape")
    print(labels.shape)

    print("Means")
    #print(gmm.means_.shape)
    #print(gmm.means_)

    #Scatter plot all
    plt.clf()
    X = np.arange(0,len(preppedArray[0]))
    for i in range(0, len(preppedArray)):
        plt.plot(X, preppedArray[i], c='gray')

    for i in range(0, len(gmm.means_)):
        plt.plot(X, gmm.means_[i])

    plt.show()

def kmeans():
    #----------------------------------------------
    #---------K-means clustering----------------
    #----------------------------------------------

    #Imports
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_samples, silhouette_score
    import csv
    import matplotlib.pyplot as plt
    #------------------------
    #----Load the data-------
    #------------------------

    print("Running k-means on the data")

    preppedArray = []
    with open("./data/midstages/" + 'loaded.csv', "r") as dataFile:
        csvReader = csv.reader(dataFile, delimiter=',', quotechar='|')
        for row in csvReader:
            preppedArray.append(row)

    preppedArray = np.array(preppedArray)
    preppedArray = preppedArray.astype(np.float)
    preppedArray = preppedArray.T
    print("The shape of prepped is ", preppedArray.shape)

    #-------------------------------
    #--------Run K-means------------
    #-------------------------------

    xVals = []
    interCluster = []
    scores = []
    sVals = []

    for i in range(3,5):
    	kmeans = KMeans(n_clusters=i, random_state=0).fit(preppedArray)
    	print(kmeans.labels_)
    	sVals.append(silhouette_score(preppedArray, kmeans.labels_))
    	print("Score")
    	print(kmeans.inertia_)
    	print("metrics")
    	xVals.append(i)
    	scores.append(kmeans.inertia_)
    	centerArray = kmeans.cluster_centers_



    plt.clf()

    '''
    #plt.plot(xVals, scores, 'o')
    plt.plot(xVals, sVals, 'o')
    #plt.plot(xVals, interCluster, 'o')
    #plt.title("Number of Clusters vs Avg Silhouette Score: 4 Body (4-6)")
    plt.title("Number of Clusters vs Avg Silhouette Score: 4 Body (6-15)")
    plt.xlabel("Number of Clusters")
    plt.ylabel("Inertia Score")
    plt.vlines(x=4, ymin=0, ymax = max(sVals) , colors='red', label='number of rigid bodies')
    plt.legend()
    plt.show()
    '''
    centerArray = kmeans.cluster_centers_

    #Plot the clusters
    for i in range(0, len(centerArray)):
    	plt.plot(centerArray[i], label="cluster " + str(i))

    plt.legend(loc="upper left")
    plt.show()

def kmeans_gmm():
    #Imports
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from pandas import DataFrame
    import time

    #The clustering toolkits
    from sklearn import datasets
    from sklearn.mixture import GaussianMixture
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_samples, silhouette_score

    import csv
    #import quatMath
    import asyncio
    import os
    import sys
    import csv
    import math
    import json
    from numpy import convolve

    #----------------------------------------------
    #---------K-means clustering----------------
    #----------------------------------------------
    #Imports
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_samples, silhouette_score
    import csv
    import matplotlib.pyplot as plt
    #------------------------
    #----Load the data-------
    #------------------------

    print("Running k-means on the data")

    preppedArray = []
    with open("./data/midstages/" + 'loaded.csv', "r") as dataFile:
        csvReader = csv.reader(dataFile, delimiter=',', quotechar='|')
        for row in csvReader:
            preppedArray.append(row)

    preppedArray = np.array(preppedArray)
    preppedArray = preppedArray.astype(np.float)
    preppedArray = preppedArray.T
    print("The shape of prepped is ", preppedArray.shape)

    #-------------------------------
    #--------Run K-means------------
    #-------------------------------

    #Restrict the data to a smaller group
    preppedArray = preppedArray[0:100, :]

    xVals = []
    interCluster = []
    scores = []
    sVals = []

    for i in range(3,5):
    	kmeans = KMeans(n_clusters=i, random_state=0).fit(preppedArray)
    	print(kmeans.labels_)
    	sVals.append(silhouette_score(preppedArray, kmeans.labels_))
    	print("Score")
    	print(kmeans.inertia_)
    	print("metrics")
    	xVals.append(i)
    	scores.append(kmeans.inertia_)
    	centerArray = kmeans.cluster_centers_

    centerArray = kmeans.cluster_centers_

    #Initialize the gmm with the kmeans cluster centers
    print("Running gmm on the data")

    #Initialize the model
    n_components = 4
    gmm = GaussianMixture(n_components = n_components, covariance_type='spherical')

    #Fit the model
    #Start timer
    initial = time.perf_counter()
    gmm.fit(preppedArray)
    #Finish timer
    final = time.perf_counter() - initial
    print("Time to process: ", str(final))

    labels = gmm.predict(preppedArray)

    print("Labels shape")
    print(labels.shape)

    print("Means")
    #print(gmm.means_.shape)
    #print(gmm.means_)

    #Plot cluster centers
    plt.clf()
    X = np.arange(0,len(preppedArray[0]))
    for i in range(0, len(preppedArray)):
        plt.plot(X, preppedArray[i], c='gray')

    for i in range(0, len(gmm.means_)):
        plt.plot(X, gmm.means_[i])

    plt.show()
