import xmltodict
import json



def print_nested_dict(dict_obj, indent = 0):
    ''' Pretty Print nested dictionary with given indent level
    '''
    # Iterate over all key-value pairs of dictionary
    #print(dict_obj['mxGraphModel'])
    #print(dict_obj['mxGraphModel']['root'])

    #Initialize vertex and edge arrays.
    vertices = []
    edges = []
    print("hi")

    for key, value in dict_obj['mxGraphModel']['root'].items():
        for entry in value:
            print(str(entry))
            #print("The id is %s"%(entry['@id']))
            #If geometry is present, save those parts.
            if 'mxGeometry' in entry:
                additional = {}
                geometry = entry['mxGeometry']
                if '@x' in geometry:
                    additional['x'] = geometry['@x']
                    additional['y'] = geometry['@y']
                if '@width' in geometry:
                    additional['width'] = geometry['@width']
                    additional['height'] = geometry['@height']


            #If a vertex, add to vertex list
            if '@vertex' in entry:
                #print("Vertex")
                newVertex = {"id": entry['@id'], "parent": entry["@parent"]}

                #Add additional information
                newVertex.update(additional)

                if '@value' in entry:
                    newVertex['value'] = entry['@value']
                vertices.append(newVertex)
            if '@edge' in entry:
                #print("Edge")
                newEdge = {"id": entry['@id'], "source": entry['@source'], "target": entry['@target']}
                if '@value' in entry:
                    newEdge['value'] = entry['@value']
                edges.append(newEdge)
            #print("-" * 25)

    print("Vertices")
    for vertex in vertices:
        print(vertex)
    print("-" * 25)

    print("Edges")
    for edge in edges:
        print(edge)
    print("-" * 25)

    #Now, translate ids into numerical 1000+ ones starting with 1000
    translationTable = {}
    globalId = 1000

    for vertex in vertices:
        translationTable[vertex['id']] = globalId
        globalId += 1
        #Check if parent is already on there, if not add it:
        if 'parent' in vertex:
            if vertex['parent'] not in translationTable:
                translationTable[vertex['parent']] = globalId
                globalId += 1

    for edge in edges:
        translationTable[edge['id']] = globalId
        globalId += 1

    #Print the table
    print()
    print("Translation table")
    for translation in translationTable:
        print(str(translation) + ": " + str(translationTable[translation]))

    #Now actually do the translation
    for vertex in vertices:
        for key, value in vertex.items():
            if value in translationTable:
                vertex[key] = translationTable[value]
    for edge in edges:
        for key, value in edge.items():
            if value in translationTable:
                edge[key] = translationTable[value]

    #Modified
    print("")
    print("Modified")

    print("Vertices")
    for vertex in vertices:
        print(vertex)
    print("-" * 25)

    print("Edges")
    for edge in edges:
        print(edge)
    print("-" * 25)



    #Add input and output signals to the vertices
    for vertex in vertices:
        vertex['inputs'] = []
        vertex['outputs'] = []

    for edge in edges:
        for vertex in vertices:
            if vertex['id'] == edge['target']:
                vertex['inputs'].append(edge['source'])
            if vertex['id'] == edge['source']:
                vertex['outputs'].append(edge['target'])



       #Find the codeRoot
    codeRoot = None
    for vertex in vertices:
        if vertex['value'] == "computer":
            codeRoot = vertex['id']
            break

    #Sketchy and might break tree recursion
    def getSubTree(rootId, tree):
        outputList = []
        for node in tree:
            if node['parent'] == rootId:
                outputList.append(node)
                subOutput = getSubTree(node['id'], tree) #Depth first tree traversal
                for output in subOutput:
                    outputList.append(output)
        return outputList

    #Start the recursions
    if codeRoot:
        codeVertices = getSubTree(codeRoot, vertices)


    #Print code vertices
    print("Code Vertices")
    for vertex in codeVertices:
        print(str(vertex))

    #Print to file
    with open("codeTree.txt", "w") as outFile:
        output = {"vertices": codeVertices, 'edges': edges}
        outFile.write(json.dumps(output))



#Run the function
with open('test.xml', 'r') as xmlFile:
    data = xmlFile.read()
    parsed = xmltodict.parse(data, process_namespaces=True)
    print_nested_dict(parsed)
