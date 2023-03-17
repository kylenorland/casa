#Kyle Norland
#8-8-22
#Reads in raw drawio save files and converts to graph and other formats

#Imports
import xmltodict
from urllib.parse import quote, unquote
import xml.etree.ElementTree as ET
import zlib
import base64
import os
import json
from watchdog.observers import Observer #Monitoring file changes
from watchdog.events import FileSystemEventHandler
import time
import argparse
import datetime

#------------DrawIO Decoder functions-------------(Not by me)
def js_encode_uri_component(data):
    return quote(data, safe='~()*!.\'')


def js_decode_uri_component(data):
    return unquote(data)


def js_string_to_byte(data):
    return bytes(data, 'iso-8859-1')


def js_bytes_to_string(data):
    return data.decode('iso-8859-1')


def js_btoa(data):
    return base64.b64encode(data)

def js_atob(data):
    return base64.b64decode(data)

def pako_inflate_raw(data):
    decompress = zlib.decompressobj(-15)
    decompressed_data = decompress.decompress(data)
    decompressed_data += decompress.flush()
    return decompressed_data

def drawio_decode(original_data):
    '''
    #original_data = '%3Cmxfile%20host%3D%22Electron%22%20modified%3D%222021-11-15T10%3A44%3A54.487Z%22%20agent%3D%225.0%20(Macintosh%3B%20Intel%20Mac%20OS%20X%2011_6_1)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20draw.io%2F14.5.1%20Chrome%2F89.0.4389.82%20Electron%2F12.0.1%20Safari%2F537.36%22%20etag%3D%22S6Lk2QkhAN9aeDDzQv4n%22%20version%3D%2214.5.1%22%20type%3D%22device%22%3E%3Cdiagram%20id%3D%223ZARfinUemRlELbDbWll%22%20name%3D%22Page-1%22%3EtZTBcoIwEEC%2FhmNngFihV6ltZ6rtgUPPGVghncAycRHo1zdIEClq9eAJ8rJhsy9LLBZk9aviRbrGGKTl2nFtsWfLdR3HnutHS5qOeMzrQKJEbIIGEIofMNA2tBQxbEeBhChJFGMYYZ5DRCPGlcJqHLZBOc5a8AQmIIy4nNIvEVPaUd%2F1Bv4GIkn7zM78qZvJeB9sKtmmPMbqCLGlxQKFSN1bVgcgW3m9l27dy5nZw8YU5HTNgk%2B22WTOqi4X4cc6iJj37rsP7qz7zI7L0lRsdktNrwBibcQMUVGKCeZcLge6UFjmMbR5bD0aYlaIhYaOht9A1Jjj5SWhRill0sx2OdtEZ4szaIuliuBSRaYA4ioBuhTIDoeguxcwA1KNXqhAchK78U64aaPkEDeY1i9G9i3i3Yl4kaDSxJkcwKC3dVWlgiAs%2BN5Cpf%2B6Uyp3oAjqyzKnpZsF7NG0bPNnXA1%2FgNO3dXrU%2FXP7XrbYOVsn2lVKfTnA%2F6bGWu%2FgbeZf6c2%2F3ZseDlfHfu7oAmbLXw%3D%3D%3C%2Fdiagram%3E%3C%2Fmxfile%3E'
    uri_decoded_data = js_decode_uri_component(original_data)
    ## Extract diagram data from resulting XML
    root = ET.fromstring(uri_decoded_data)
    diagram_data = root[0].text
    '''
    diagram_data = original_data
    
    ## Decode Base64
    diagram_data = js_atob(diagram_data)
    decompressed_diagram_data = pako_inflate_raw(diagram_data)
    ## Turn decompressed data into a usable string
    string_diagram_data = js_bytes_to_string(decompressed_diagram_data)
    string_diagram_data = js_decode_uri_component(string_diagram_data)
    #print(string_diagram_data)
    return(string_diagram_data)

#------------------------------------------------

def raw_to_dict(save_file_name, output_folder):
    #--------------------------------------------------------------
    #----Conversion from Encoded .drawio format to xmldict---------
    #--------------------------------------------------------------
    #Read in the xml
    print("Reading in ", save_file_name)
    with open(save_file_name) as f:
        doc = xmltodict.parse(f.read())
        
    for element in doc['mxfile']['diagram']:
        print(element)
        

    raw_diagram = doc['mxfile']['diagram']['#text']
    #print("Raw diagram: \n", raw_diagram)

    '''
    vals = chunk_bytes.decode("utf-8").split("".join(map(chr, [0])))
    print(vals)
    '''
        
    #Convert it to a readable format (It is URI encoded and then zlib encoded?)
    #Use decoding from open source project https://github.com/jgraph/drawio #Now jgraph, diagrams.net
    decoded_diagram = drawio_decode(raw_diagram)
    
    '''
    print("\n Decoded diagram: \n", decoded_diagram)
    print(decoded_diagram)
    print("-----------------")
    '''
    
    #Output to file:
    with open(os.path.join(output_folder, 'mxGraphModel.txt'), 'w') as f:
        f.write(decoded_diagram)
    
    #Decode it from xml again
    diagram_dict = xmltodict.parse(decoded_diagram)
    '''
    print("Raw Dict")
    for element in diagram_dict['mxGraphModel']['root']['mxCell']:
        print(element)
    '''    
        
    return diagram_dict    
      
def dict_to_graph(diagram_dict, output_folder):
    #--------------------------------------------------------------
    #--------------------Conversion to Graph Format----------------
    #--------------------------------------------------------------
    decoder = 0

    #Initialize vertex and edge arrays.
    vertices = []
    edges = []

    #For each mxCell?
    for key, value in diagram_dict['mxGraphModel']['root'].items():
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
                    additional['width'] = geometry['@width']
                    additional['height'] = geometry['@height']


            #If a vertex, add to vertex list
            if '@vertex' in entry:
                #print("Vertex")
                newVertex = {"id": entry['@id'], "parent": entry["@parent"]}

                #Add geometry information
                newVertex.update(additional)

                if '@value' in entry:
                    newVertex['value'] = entry['@value']
                vertices.append(newVertex)
                
            #If edge add to edge list    
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

    #Needs checking, maybe do recursive?
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
        vertex['outputs'] = [vertex['id']]

    for edge in edges:
        for vertex in vertices:
            if vertex['id'] == edge['target']:
                vertex['inputs'].append(edge['source'])
                
            #Vertices just output themselves
            #if vertex['id'] == edge['source']:
            #    vertex['outputs'].append(edge['target'])


    #Output to graph representation json file
    graph_dict = {}
    graph_dict['vertices'] = vertices
    graph_dict['edges'] = edges
    
    with open(os.path.join(output_folder, 'graph_form.json'), 'w') as f:
        json.dump(graph_dict, f)   

    return graph_dict

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

def gui_interpreter(graph_dict):
    print("-------Running GUI Interpreter--------")
    #Find the guiRoot
    guiRoot = None
    for vertex in graph_dict['vertices']:
        if vertex['value'] == "GUI":
            guiRoot = vertex['id']
            break

    #If each root exists, recurse through the file and output to file
    if guiRoot:
        guiVertices = getSubTree(guiRoot, graph_dict['vertices'])

        #Print output
        print("GUI Vertices")
        for vertex in guiVertices:
            print(str(vertex))

        #Print to file
        with open(os.path.join(output_folder, "guiTree.json"), "w") as outFile:
            output = {"vertices": guiVertices}
            outFile.write(json.dumps(output))  
            
def code_interpreter(graph_dict):
    print("-------Running GUI Interpreter--------")
    #Find the codeRoot
    codeRoot = None
    for vertex in graph_dict['vertices']:
        if vertex['value'] == "CODE":
            codeRoot = vertex['id']
            break            

    if codeRoot:
        codeVertices = getSubTree(codeRoot, graph_dict['vertices'])

        #Print code vertices
        print("Code Vertices")
        for vertex in codeVertices:
            print(str(vertex))

        #Print to file
        with open(os.path.join(output_folder, "codeTree.json"), "w") as outFile:
            output = {"vertices": codeVertices}
            outFile.write(json.dumps(output)) 

class  MyHandler(FileSystemEventHandler):
    def __init__(self, save_file_path, output_folder):
        self.save_file_path = save_file_path
        self.output_folder = output_folder
        self.last_fired = datetime.datetime.now()
        print("initializing handler")
    
    def  on_modified(self,  event):
        save_file_path = self.save_file_path
        output_folder = self.output_folder
        
        print(f'event type: {event.event_type} path : {event.src_path}')
        

        if event.src_path == save_file_path:
            #Check if recently fired
            if (datetime.datetime.now() - self.last_fired).total_seconds() > 2:
                #Update last fired
                self.last_fired = datetime.datetime.now()
                
                #Convert from raw to dictionary to graph structure
                diagram_dict = raw_to_dict(save_file_path, output_folder)
                graph_dict = dict_to_graph(diagram_dict, output_folder)
                
                #Convert to interpreted second stage structures like gui, code, CASA, and RL.
                gui_interpreter(graph_dict)
                code_interpreter(graph_dict) 
                
                
    def  on_created(self,  event):
        print(f'event type: {event.event_type} path : {event.src_path}')
    def  on_deleted(self,  event):
        print(f'event type: {event.event_type} path : {event.src_path}')


if __name__ == "__main__":
    #Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("save_file_folder", type=str, default=os.path.join('.'), nargs='?', help="enter the file folder of the drawio")
    parser.add_argument("save_file_name", type=str, default=os.path.join('test_reader.drawio'), nargs='?', help="enter the file name of the drawio")
    parser.add_argument("output_folder_path", type=str, default=os.path.join('.', 'outputs'), nargs='?', help="enter the folder path of where the outputs should go")
    
    args = parser.parse_args()

    #Global Variables
    
    #Change which save file to pay attention to.
    #save_file_path = os.path.join('.','drawio_software', 'test_reader.drawio')
    save_file_folder = args.save_file_folder
    save_file_path = os.path.join(args.save_file_folder, args.save_file_name)
    output_folder = args.output_folder_path
    
    print("file folder")
    print(save_file_folder)
    
    print("file path")
    print(save_file_path)
    
    continuous_update = True
    file_modified = False
    
    #Ensure folder structure exists
    os.makedirs(output_folder, exist_ok=True)


    #---Loop or event listener: Check for updates to the file.-----
    #https://dev.to/stokry/monitor-files-for-changes-with-python-1npj

    #Initialize Update Watcher
    event_handler = MyHandler(save_file_path, output_folder)
    observer = Observer()
    observer.schedule(event_handler,  path=save_file_folder,  recursive=False)
    print("Monitoring changes to ", save_file_path)
    observer.start()

    #Run Update Watcher
    if continuous_update:
        #Register file event listener?
        try:
            while  True:
                time.sleep(1)     
        except  KeyboardInterrupt:
            observer.stop()
        observer.join()    

    
    
    
    


     
        
        
        
        
 


