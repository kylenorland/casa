import json
from inspect import getmembers, isfunction
import time
import collections

def initialize():
	#Load graph
	with open("codeTree.txt", "r") as graphFile:
		graphDict = json.loads(graphFile.read())

	#Assemble graph into code
	#Ignore parent entries for now. Just pull out a chain.

	vertices = graphDict['vertices']
	edges = graphDict['edges']
	
	vertexDict = {1000:{'id': 1000, 'children':[], 'value': 'root'}}
	
	#Add children to details
	for vertex in vertices:
		vertex['children'] = []
		vertexDict[vertex['id']] = vertex
		
	for key, vertex in vertexDict.items():
		if 'parent' in vertex:
			parentId = vertex['parent']
			if parentId in vertexDict:
				vertexDict[parentId]['children'].append(vertex['id'])
	'''	
	#Add inputs and outputs to details
	for edge in edges:
		if edge['source'] in vertexDict and edge['target'] in vertexDict:
			vertexDict[edge['source']]['outputs'].append(edge['target'])
			vertexDict[edge['target']]['inputs'].append(edge['source'])
	'''


	#Load in the config details
	for key, vertex in vertexDict.items():
		print(vertex['value'])
		print('Children')
		for child in vertex['children']:
			value = vertexDict[child]['value']
			print(value)
			if value[0:6] == 'config':
				print(value[7:])
				configDict = json.loads(str(value[7:]))
				vertex['configuration'] = {}
				for value in configDict:
					vertex['configuration'][value] = configDict[value]
		print('--------------')
	
	
	#Available block list
	availableBlocks = ['accelerometer', 'rms', 'averager reset', 'averager', 'thresholder', 'logger', 'root']
	for key, vertex in vertexDict.items():
		print(vertex)	
		
	print("----------------------------------------")
	print("Running")
	for key, vertex in vertexDict.items():
		if vertex['value'] in availableBlocks:
			print(vertex['value'] + ": " + str(vertex['configuration']))				
	
	
	#CASA Translator
	casaTranslator = True
	if casaTranslator:
		eArgs = []
		#Manually add webSocketInterface and boundManager
		webSockI = {"name": "webSocketInterface", "path": "webSocketInterface.py", "subTopics": [], "pubTopics": [9], "sensorMacs": [], "inputFiles": [], "computerIp": "localhost"}
		eArgs.append(webSockI)
		boundManager = {"name": "boundManager", "path": "boundManager.py", "subTopics": [], "pubTopics": [], "sensorMacs": [], "participatingIps": ["192.168.87.35"], "computerIp": "192.168.87.35", "internalIds": [], "externalSubs": []}
		for key, vertex in vertexDict.items():
			boundManager["internalIds"].append(str(key))
		eArgs.append(boundManager)
		
		#Now, add each individual
		availableBlocks = ['autoGenerator', 'autoMid', 'autoSink', 'computer']
		for key, vertex in vertexDict.items():
			if vertex['value'] in availableBlocks:
				subTopics = []
				for topic in vertex['inputs']:
					subTopics.append(str(topic))
				newObj = {"name": vertex['value'], "path": vertex['value'] + '.py', "subTopics": subTopics, "pubTopics": [str(vertex['id'])], "sensorMacs": [], "inputFiles": [], "computerIp": vertexDict[vertex['parent']]['configuration']['ip']} 
				eArgs.append(newObj)
		
		#Print it all to file
		for arg in eArgs:
			print(arg)
			
		#Dump it
		with open('envConfig/externalArgs.txt', 'w') as outfile:
			json.dump(eArgs, outfile)
		

#-----------Run the app-----------------------
initialize()

