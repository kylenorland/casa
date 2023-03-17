
//----------------------------
//------SET UP CANVAS---------
//----------------------------
var canvas= $("#mainCanvas")[0];
var ctx = canvas.getContext("2d");

//---------------------------
//-------GLOBALS-----------
//---------------------------
selected = []
SVGVersion = {}
JSONVersion = {}
pushJSON = {"programs": []}

globalIdCounter = 1000

var canvasOffset=$("#mainCanvas").offset();
var offsetX=canvasOffset.left;
var offsetY=canvasOffset.top;
var canvasWidth=canvas.width;
var canvasHeight=canvas.height;

//--------------------------
//------CLASSES-------------
//--------------------------

//General Block Class

class Block{
	constructor(blockName, globalId, numLeftPorts, numRightPorts, x, y){
		//console.log("There are " + arguments.length)
		if(arguments.length > 1){
			this.objectType = this.constructor.name
			this.blockName = blockName
			this.globalId = globalId
			this.x = x
			this.y = y
			this.stackingIndex = 0
			this.draggable = true
			this.beingDragged = false
			this.interacting = false
			this.dragOffset = [0,0]
			this.expandable = false
			this.selected = false
			this.drawable = true
			this.blockType = "code"
			this.width = 120
			this.height = 45
			this.colOneTextYOffset = 20
			this.color = "black"
			this.fillColor = "rgb(36, 174, 54)";
			this.numLeftPorts = numLeftPorts
			this.numRightPorts = numRightPorts
			this.portRadius = 7
			this.portColor = "black"
			this.inputs = []
			this.outputs = []
			this.ports = []
			this.subObjects = []
			this.borderColor = "black"
			this.borderWidthDefault = "2"
			this.borderWidth = this.borderWidthDefault
			this.borderWidthSelected = "5"
			this.borderDetectProportion = 0.20
			this.rightBoundaryClicked = false
			this.bottomBoundaryClicked = false
			this.boundaryDragging = false
			this.zoomFactor = 1

			this.generatePorts()
		}else if(arguments.length == 1){
			let refObject = arguments[0]
			for(var propName in refObject){
				//console.log(propName + " is " + refObject[propName])
				this[propName] = refObject[propName]
			}
		}

	}
	generatePorts(){
        //Generate its ports
        for(var i=0; i<this.numLeftPorts; i++){
            let port = {
                'xPropOffset': 0,
                'xOffset': 0,
                'yPropOffset': (i / this.numLeftPorts),
                'yOffset': (this.height * (i / this.numLeftPorts)) + 10,
                'x': this.x,
                'y': this.y,
                'radius': this.portRadius,
                'color': this.portColor,
                'input': true,
                'output':false
            }
            this.ports.push(port)
        }
        for(var i=0; i<this.numRightPorts; i++){
            let port = {
                'xPropOffset': 1,
                'xOffset': this.width,
                'yPropOffset': (i / this.numRightPorts),
                'yOffset': (this.height * (i / this.numRightPorts)) + 10,
                'x': this.x,
                'y': this.y,
                'radius': this.portRadius,
                'color': this.portColor,
                'input': false,
                'output':true
            }
            this.ports.push(port)
        }
	}
		convertIds(conversionTable){
			//Switch out own id;
			this.globalId = conversionTable[this.globalId]
			//console.log("new global id is: " + this.globalId)

			//Switch out subObjects;
			for(var i=0; i<this.subObjects.length; i++){
				this.subObjects[i] = conversionTable[this.subObjects[i]]
			}
			//Switch out input and output ids;
			for(var i=0; i<this.inputs.length; i++){
				this.inputs[i] = conversionTable[this.inputs[i]]
			}
			//
			for(var i=0; i<this.outputs.length; i++){
				this.outputs[i] = conversionTable[this.outputs[i]]
			}


		}

		deleteObject(objId){
			for(var i=0; i < this.inputs.length; i++){
				if(this.inputs[i] == objId){
					console.log("Deleting " + objId + "from inputs")
					this.inputs.slice(i,1)
				}
			}
			for(var i=0; i < this.outputs.length; i++){
				if(this.outputs[i] == objId){
					console.log("Deleting " + objId + "from outputs")
					this.outputs.slice(i,1)
				}
			}
		}

    handleMouseDown(canMouseX, canMouseY){
				//Check if the click is on the boundaries if it's expandable
				this.boundaryDragging = false
				if(this.expandable){
					//Check if in right border;
					let xLeft = this.x + this.width - Math.trunc(this.borderDetectProportion * this.width)
					let xRight = this.x + this.width
					let yTop = this.y
					let yBottom = this.y + this.height

					if(canMouseX > xLeft && canMouseX < xRight && canMouseY > yTop && canMouseY < yBottom){
							console.log("Right Boundary Clicked")
							//console.log(this.parentObject.width)
							this.rightBoundaryClicked = true
							this.boundaryDragging = true
					}

					//Check if it's the bottom edge
					//Don't redeclare
					xLeft = this.x
					xRight = this.x + this.width
					yTop = this.y + this.height - Math.trunc(this.borderDetectProportion * this.height)
					yBottom = this.y + this.height

					console.log(Math.trunc(this.borderDetectProportion * this.height))

					if(canMouseX > xLeft && canMouseX < xRight && canMouseY > yTop && canMouseY < yBottom){
							console.log("Bottom Boundary Clicked")
							//console.log(this.parentObject.width)
							this.bottomBoundaryClicked = true
							this.boundaryDragging = true
					}


				}
				//If it wasn't on the border, handle a click like regular
				if(this.boundaryDragging == false){
					this.dragOffset[0] = this.x - canMouseX
					this.dragOffset[1] = this.y - canMouseY
					this.beingDragged = true

					//Turn on focus:
					this.selected = true
					//Toggle focus
					//this.selected = !this.selected // Toggle the selected property
				}
    }

    handleMouseMove(canMouseX, canMouseY){
        if(this.beingDragged){
            this.x = canMouseX + this.dragOffset[0]
            this.y = canMouseY + this.dragOffset[1]
        }

				if(this.expandable){
					//Handle if rightBoundary
					if(this.rightBoundaryClicked == true){
	            this.width = this.width + (canMouseX - (this.x + this.width))
	        }
					//Handle if bottomBoundary
					if(this.bottomBoundaryClicked == true){
						this.height = this.height + (canMouseY - (this.y + this.height))
					}
				}
    }

    handleMouseUp(){
        this.beingDragged = false
				this.selected = false

				if(this.expandable){
					this.rightBoundaryClicked = false
					this.bottomBoundaryClicked = false
					this.boundaryDragging = false
				}
    }
    /*


    handleMouseOut(){

    }
    */

	drawSelf(){

	    //Make updates
        if(this.selected){
            this.borderColor = "rgb(219, 53, 29)"
            this.borderWidth = this.borderWidthSelected
        }else{
           this.borderColor = "black"
           this.borderWidth = this.borderWidthDefault
        }
		// Print the rectangles
		ctx.beginPath();
		ctx.fillStyle = this.fillColor;
        ctx.fillRect(this.x, this.y, this.width, this.height);

        //Draw border
        ctx.lineWidth = this.borderWidth;
		ctx.strokeStyle = this.borderColor;
		ctx.rect(this.x, this.y, this.width, this.height);
		ctx.stroke();


		ctx.fillStyle = "rgb(0,0,0)";

		//Print the block name
		ctx.font = "14px Arial";
		ctx.fillText(this.blockName, this.x + 10, this.y + this.colOneTextYOffset);

		//Update and Draw its ports
	    for(var i=0; i < this.ports.length; i++){
	        var port = this.ports[i]
	        port.xOffset = port.xPropOffset * this.width
	        port.x = this.x + port.xOffset
	        port.yOffset = (this.height * port.yPropOffset) + 10
	        port.y = this.y + port.yOffset

            ctx.beginPath();
            ctx.arc(port.x, port.y, port.radius, 0, 2 * Math.PI, false);
            ctx.fillStyle = port.color;
            ctx.fill();
            ctx.lineWidth = 1;
            ctx.strokeStyle = '#003300';
            ctx.stroke();
		}
	}

	pushToJSON(){
	    var newProgram = {
	        "name": this.blockName,
	        "path": this.blockName + ".py",
	        "subTopics": [],
	        "pubTopics": [],
	        "sensorMacs": [],
					"inputFiles": [],
					"outputFiles":[],
	        "computerIp": "localhost"   //Default to localhost (Not accessible from other computers, so just good for front end.
	    }
	    //Inputs
        for(var j=0; j < this.inputs.length; j++){
            //newProgram.subTopics.push(String(this.inputs[j].globalId))
						newProgram.subTopics.push(String(this.inputs[j]))
        }
        //Outputs: (For now just the blocks globalId
        newProgram.pubTopics.push(String(this.globalId))


        //Special rule for blocks that interact with sensors of type "mwSensorDriver"
        //Check if it has a type
        if(this.hasOwnProperty("type")){
            if(this.type == "mwSensorDriver"){
                console.log(this.blockName + " is a driver type")
                //Check inputs and outputs for macAddress property
                for(var k=0; k < this.inputs.length; k++){
									let inputObject = allObjects.find(obj => obj.globalId == this.inputs[k])
										if(inputObject.hasOwnProperty("macAddress")){
                        newProgram.sensorMacs.push(inputObject.macAddress)
                    }
                }
                for(var k=0; k < this.outputs.length; k++){
									let outputObject = allObjects.find(obj => obj.globalId == this.outputs[k])
                    if(outputObject.hasOwnProperty("macAddress")){
                        newProgram.sensorMacs.push(outputObject.macAddress)
                    }
                }
            }
        }

				//Special rule for blocks that read from input files.
				if(this.hasOwnProperty("type")){
            if(this.type == "inputInterface"){
                console.log(this.blockName + " is a interfacing type")
                //Check inputs and outputs for macAddress property
                for(var k=0; k < this.inputs.length; k++){
									let inputObject = allObjects.find(obj => obj.globalId == this.inputs[k])
                    if(inputObject.hasOwnProperty("filePath")){
                        newProgram.inputFiles.push(inputObject.filePath)
                    }
                }
                for(var k=0; k < this.outputs.length; k++){
									let outputObject = allObjects.find(obj => obj.globalId == this.outputs[k])
                    if(outputObject.hasOwnProperty("filePath")){
                        newProgram.inputFiles.push(outputObject.filePath)
                    }
                }
            }
        }

				//Special rule for blocks that write to output files.
				if(this.hasOwnProperty("type")){
            if(this.type == "outputInterface"){
                console.log(this.blockName + " is a output interfacing type")
                //Check inputs and outputs for macAddress property
								console.log("The inputs are: " + this.inputs)
                for(var k=0; k < this.inputs.length; k++){
									let inputObject = allObjects.find(obj => obj.globalId == this.inputs[k])
                    if(inputObject.hasOwnProperty("filePath")){
                        newProgram.outputFiles.push(inputObject.filePath)
                    }
                }
                for(var k=0; k < this.outputs.length; k++){
									let outputObject = allObjects.find(obj => obj.globalId == this.outputs[k])
                    if(outputObject.hasOwnProperty("filePath")){
                        newProgram.outputFiles.push(outputObject.filePath)
                    }
                }
            }
        }

        //Check if upper left corner is contained within any of the computer blocks
				for(var i=0; i<allObjects.length; i++){
					//Check if object is a computer Type
					object = allObjects[i]
					if(object.hasOwnProperty('blockType')){
						if(object.blockType == 'computer'){

	            if(this.x > object.x && this.x < object.x + object.width && this.y > object.y && this.y < object.y + object.height){
	                newProgram.computerIp = object.ip
									console.log(this.blockName + " has a computer match with " + object.ip)
									console.log(this.x + " is between " + object.x + " and " + (object.x + object.width))
									console.log(this.y + " is between " + object.y + " and " + (object.y + object.height))
	            }
						}
					}
				}
				/*
        for(var i=0; i<computerBlocks.length; i++){
            console.log(this.x)
            console.log(this.y)
            console.log(computerBlocks[i].x)
            console.log(computerBlocks[i].y)

            if(this.x > computerBlocks[i].x && this.x < computerBlocks[i].x + computerBlocks[i].width && this.y > computerBlocks[i].y && this.y < computerBlocks[i].y + computerBlocks[i].width){
                newProgram.computerIp = computerBlocks[i].ip
            }
        }
				*/

        //Push it to the groups that matches
        for(var i=0; i<pushJSON.pushGroups.length; i++){
            //console.log("Trying to push to ip")
            //console.log(newProgram.computerIp)
            //console.log(pushJSON.pushGroups[i].ip)
            if(newProgram.computerIp == pushJSON.pushGroups[i].ip){
                pushJSON.pushGroups[i].blocks.push(newProgram)
            }
        }

    }
}

class boundary{
    //Nothing yet
}

class CodeBlock extends Block{
    constructor(blockName, globalId, numLeftPorts, numRightPorts, x, y){
			if(arguments.length > 1){
        super(blockName, globalId, numLeftPorts, numRightPorts, x, y)
			}else if(arguments.length == 1){
					super(arguments[0])
			}
    }
}

class ContainerBlock extends Block{
	constructor(blockName, globalId, numLeftPorts, numRightPorts, x, y){
		if(arguments.length > 1){
			super(blockName, globalId, numLeftPorts, numRightPorts, x, y)
			this.expandable = true
		}else if(arguments.length == 1){
				super(arguments[0])
		}
	}
}

class SubBlock extends Block{
	constructor(blockName, globalId, numLeftPorts, numRightPorts, x, y){
		if(arguments.length > 1){
			super(blockName, globalId, numLeftPorts, numRightPorts, x, y)
		}else if(arguments.length == 1){
				super(arguments[0])
		}
	}
}

class InputBlock extends Block{
    constructor(blockName, globalId, numLeftPorts, numRightPorts, x, y){
			if(arguments.length > 1){
        super(blockName, globalId, numLeftPorts, numRightPorts, x, y)
        this.blockType = 'input'
        this.fillColor = this.fillColor = "rgb(255, 102, 0)";
        this.socketAddress = "ws://localhost:9615"
			}
			else if(arguments.length == 1){
				super(arguments[0])
			}


    }
    handleMouseDown(canMouseX, canMouseY){
        //Calculate the drag offset and toggle the drag bool
        this.dragOffset[0] = this.x - canMouseX
        this.dragOffset[1] = this.y - canMouseY
        this.beingDragged = true

        //Toggle focus
        this.selected = !this.selected // Toggle the selected property

				//Store Self
				var _self = this
        //Send input to websocket
				let websocket = new WebSocket(this.socketAddress)
				websocket.onopen = function(e){
					console.log("Socket open")
					websocket.send(JSON.stringify({"sender": String(_self.globalId), "message": {"value": 1, "timestamp": Date.now(), "buttonName": String(_self.blockName)}}))
				}

			}
}

class ComputerBlock extends Block{
    constructor(blockName, globalId, ipAddress, numLeftPorts, numRightPorts, x, y){
			if(arguments.length > 1){
        super(blockName, globalId, numLeftPorts, numRightPorts, x, y)
        this.ip = ipAddress
				this.expandable = true // Allows for side boundaries
				this.stackingIndex = -1 //Should always be behind the default layer.
        this.blockType = 'computer'
        this.width= 200
        this.height = 100
        this.fillColor = this.fillColor = "rgb(178, 187, 184)"
        //Sub-Objects
        this.subObjects = []
        this.borderDetectWidth = 20
			}else if(arguments.length == 1){
					super(arguments[0])
			}
    }

    drawSelf(){
	    //Make updates
	    //Update sub-objects
        for(var i=0; i<this.subObjects.length; i++){
					let subObj = allObjects.find(obj => obj.globalId == this.subObjects[i])
          subObj.update()
        }

        if(this.selected){
            this.borderColor = "rgb(219, 53, 29)"
            this.borderWidth = this.borderWidthSelected
        }else{
           this.borderColor = "black"
           this.borderWidth = this.borderWidthDefault
        }
		// Print the rectangles
		ctx.beginPath();
		ctx.fillStyle = this.fillColor;
        ctx.fillRect(this.x, this.y, this.width, this.height);

        //Draw border
        ctx.lineWidth = this.borderWidth;
		ctx.strokeStyle = this.borderColor;
		ctx.rect(this.x, this.y, this.width, this.height);
		ctx.stroke();


		ctx.fillStyle = "rgb(0,0,0)";

		//Print the block name
		ctx.font = "14px Arial";
		ctx.fillText(this.blockName +" at: " +  this.ip, this.x + 10, this.y + this.colOneTextYOffset);

		//Update and Draw its ports
	    for(var i=0; i < this.ports.length; i++){
	        var port = this.ports[i]
	        port.xOffset = port.xPropOffset * this.width
	        port.x = this.x + port.xOffset
	        port.yOffset = (this.height * port.yPropOffset) + 10
	        port.y = this.y + port.yOffset

            ctx.beginPath();
            ctx.arc(port.x, port.y, port.radius, 0, 2 * Math.PI, false);
            ctx.fillStyle = port.color;
            ctx.fill();
            ctx.lineWidth = 1;
            ctx.strokeStyle = '#003300';
            ctx.stroke();
		}
	}
}

class SensorBlock extends Block{
    constructor(blockName, globalId, macAddress, numLeftPorts, numRightPorts, x, y){
			if(arguments.length > 1){
        super(blockName, globalId, numLeftPorts, numRightPorts, x, y)
        this.macAddress = macAddress
        this.blockType = 'sensor'
        this.width = 150
        this.height = 45
        this.fillColor = this.fillColor = "rgb(63, 177, 211)";
			}else if(arguments.length == 1){
					super(arguments[0])
			}
    }
}

class fileInputBlock extends Block{
	constructor(blockName, globalId, numLeftPorts, numRightPorts, x, y, filePath){
		if(arguments.length > 1){
			super(blockName, globalId, numLeftPorts, numRightPorts, x, y)
			this.filePath = filePath
			this.blockType = 'fileInput'
			this.width = 150
			this.height = 45
			this.fillColor = this.fillColor = "rgb(255, 153, 51)";
		}else if(arguments.length == 1){
				super(arguments[0])
		}
	}

}

class fileOutputBlock extends Block{
	constructor(blockName, globalId, numLeftPorts, numRightPorts, x, y, filePath){
		if(arguments.length > 1){
			super(blockName, globalId, numLeftPorts, numRightPorts, x, y)
			this.filePath = filePath
			this.blockType = 'fileOutput'
			this.width = 150
			this.height = 45
			this.fillColor = this.fillColor = "rgb(255, 153, 51)";
		}else if(arguments.length == 1){
				super(arguments[0])
		}
	}

}

//Connector Classes
class connector{
	constructor(sourcePort, sourceObject, globalId){
			if(arguments.length > 1){
				this.objectType = this.constructor.name
				this.globalId = globalId
				this.draggable = false
				this.stackingIndex = 1
				this.expandable = false
				this.selected = false
				this.drawable = true
				this.blockType = "connector"
				this.sourceId = sourceObject.globalId;
				this.sourcePort = sourcePort
				this.sourceX = this.sourcePort.x
				this.sourceY = this.sourcePort.y
				this.destId = null
				this.destPort =  null
				this.destX = null
				this.destY = null
				this.lineThickness = 2
				this.color = "black"
				this.arrowHyp = 20
				this.arrowAngle= Math.PI / 7
				this.arrowColor = "rgb(112, 128, 144)"
			}
			else if(arguments.length == 1){
				let refObject = arguments[0]
				for(var propName in refObject){
					//console.log(propName + " is " + refObject[propName])
					this[propName] = refObject[propName]
				}

				//Update port (Very clunky and assumes only one exit port per block) (Fix)
				let inputObject = loadedObjects.find(obj => obj.globalId == this.sourceId)
				console.log(this.sourceId)
				console.log(inputObject)
				this.sourcePort = inputObject.ports.find(obj => obj.output == true)
				this.sourceX = this.sourcePort.x;
				this.sourceY = this.sourcePort.y;

				let destObject = loadedObjects.find(obj => obj.globalId == this.destId)
				console.log(this.destId)
				console.log(destObject)
				this.destPort = destObject.ports.find(obj => obj.input == true)
				this.destX = this.destPort.x;
				this.destY = this.destPort.y;
			}
		}

		convertIds(conversionTable){
			//Switch out own id;
			this.globalId = conversionTable[this.globalId]

			//Switch source and dest id;
			this.sourceId = conversionTable[this.sourceId]
			this.destId = conversionTable[this.destId]
		}

		deleteObject(objId){

			if(objId == this.sourceId){
				console.log("Deleting connector")
				deleteQueue.push(this.globalId)
				//Delete self globally
			}
			if(objId == this.destId){
				console.log("Deleting connector")
				deleteQueue.push(this.globalId)
				//Delete self globally
			}
		}

    handleMouseDown(canMouseX, canMouseY){
        console.log("Connector Clicked")
    }
    handleMouseMove(canMouseX, canMouseY){
        console.log("Connector Clicked")
    }

    handleMouseUp(){
        console.log("Connector Clicked")
    }
	drawSelf(){
		ctx.beginPath();
		this.sourceX = this.sourcePort.x
		this.sourceY = this.sourcePort.y

    this.destX = this.destPort.x
    this.destY = this.destPort.y

		//Calc deltas for arrow direction;
		let deltaX = this.destX - this.sourceX
		let deltaY = this.destY - this.sourceY
		//Line angle plus pi-angle is first back minus the same is finishing line.
		//Cross line is perpendicular to the main one.
		let lineAngle = Math.atan2(-1* deltaY, deltaX) //Flip coordinates
		let backAngle = lineAngle + Math.PI - this.arrowAngle //Angle back.
		let crossAngle = lineAngle + ((3 * Math.PI) / 2)
		//let forwardAngle = lineangle + this.arrowAngle
		let crossLength = 2 * (Math.sin(this.arrowAngle) * this.arrowHyp)
		let backX = this.destX + (Math.cos(backAngle) * this.arrowHyp)
		let backY = this.destY - ((Math.sin(backAngle)) * this.arrowHyp) //Flipped coordinates

		ctx.strokeStyle = "rgb(0,0,0)";
		ctx.moveTo(this.sourceX, this.sourceY);
		ctx.lineTo(this.destX, this.destY);
		ctx.stroke();

		ctx.fillStyle = this.arrowColor
		ctx.beginPath();
		ctx.moveTo(this.destX, this.destY)
		//Back line
		ctx.lineTo(backX, backY)
		//Cross line;
		ctx.lineTo(backX + (Math.cos(crossAngle) * crossLength), backY - (Math.sin(crossAngle) * crossLength))
		//Forward Line;
		ctx.lineTo(this.destX, this.destY)
		//Fill in the shape
		ctx.fill();
		//Change color back
		ctx.fillStyle = "rgb(0,0,0)";
	}
}


//----------------------------------
//----Objects Arrays AND GLOBALS---
//------------------------------
allObjects = []
deleteQueue = []
//--------------------------
//------BUTTONS-------------
//--------------------------

$( "#scanButton" ).click(function() {
  fetch("http://localhost:5000/btscan")
	.then(function (response) {
	console.log("scan success")
	return response;
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });

});

$( "#scanComputersButton" ).click(function() {
  fetch("http://localhost:5000/computerScan")
	.then(function (response) {
	console.log("scan success")
	return response;
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });
});

$( "#getSensorsButton" ).click(function() {
  fetch("http://localhost:5000/getSensors")
	.then(function (response) {
	return response.json();
  })
	.then(function (myJson) {
        console.log(myJson)
		for(var j=0; j < myJson.length; j++){
		    console.log(j)
			//Turn the json into new objects
			//console.log(myJson[i])
			//Initialize sensor Object
			try{
                newSensor = new SensorBlock(myJson[j], globalIdCounter, myJson[j],1,1, 10, 50*j)
                globalIdCounter += 1;   //Increment the globalIdCounter
                console.log("Global id is: " + newSensor.globalId)
			    allObjects.push(newSensor)
			    //sensorBlocks.push(newSensor)
			}catch(error){
			    console.log(error);
			}


        //Print the objects
        drawAll()

		}
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });

});

$( "#refreshBlocksButton" ).click(function() {
  fetch("http://localhost:5000/refreshBlocks")
	.then(function (response) {
	console.log("refresh success")
	return response;
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });

});

$( "#getBlocksButton" ).click(function() {
  fetch("http://localhost:5000/getBlocks")
	.then(function (response) {
	return response.json();
  })
	.then(function (myJson) {
        console.log(myJson.blocks)
		for(var j=0; j < myJson.blocks.length; j++){
			//Turn the json into new objects
			//console.log(myJson[i])
			//Initialize block Object
			try{
                newBlock = new CodeBlock(myJson.blocks[j].name, globalIdCounter, myJson.blocks[j].leftPorts, myJson.blocks[j].rightPorts, 200, 50*j)
                globalIdCounter += 1 //Increment
                //console.log("Global id is: " + newBlock.globalId)

                //Add block type and other specialty properties
                //Add block type if it exists, otherwise, add as default.
                if(myJson.blocks[j].hasOwnProperty("type")){
                    newBlock.type = myJson.blocks[j].type
                }
                else{
                    newBlock.type = "defaultType"
                }
			    allObjects.push(newBlock)

			}catch(error){
			    console.log(error);
			}

		}
		//Print the objects
        drawAll()
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });

});

$( "#getComputersButton" ).click(function() {
  fetch("http://localhost:5000/getComputers")
	.then(function (response) {
	return response.json();
  })
	.then(function (myJson) {
        console.log(myJson)

		for(var j=0; j < myJson.computers.length; j++){
		    console.log(j)
			//Turn the json into new objects
			//console.log(myJson[i])
			//Initialize block Object
			try{
          computerData = myJson.computers[j]
          newComputer = new ComputerBlock(computerData.name, globalIdCounter, computerData.ip, 3, 3, 800, 100*j)
          globalIdCounter += 1 //Increment
			    allObjects.push(newComputer)
			    //computerBlocks.push(newComputer)
			}catch(error){
			    console.log(error);
			}


        //Print the objects
        console.log(allObjects)
        drawAll()

		}
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });

});

$( "#getInputsButton" ).click(function() {
  fetch("http://localhost:5000/getInputs")
	.then(function (response) {
	return response.json();
  })
	.then(function (myJson) {
        console.log(myJson.inputs)
		for(var j=0; j < myJson.inputs.length; j++){
		    console.log(j)
			//Turn the json into new objects
			//console.log(myJson[i])
			//Initialize input
			try{
                newBlock = new InputBlock(myJson.inputs[j].name, globalIdCounter, myJson.inputs[j].leftPorts, myJson.inputs[j].rightPorts, 350, 50*j)
                globalIdCounter += 1 //Increment
			    allObjects.push(newBlock)
			    //inputBlocks.push(newBlock)
			}catch(error){
			    console.log(error);
			}

		}
		//Print the objects
        drawAll()
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });

});

$( "#getFileInputsButton" ).click(function() {
  fetch("http://localhost:5000/getFileInputs")
	.then(function (response) {
	return response.json();
  })
	.then(function (myJson) {
        console.log(myJson.inputs)
		for(var j=0; j < myJson.inputs.length; j++){
		    console.log(j)
			//Turn the json into new objects
			//console.log(myJson[i])
			//Initialize input
			try{
                newBlock = new fileInputBlock(myJson.inputs[j].name, globalIdCounter, myJson.inputs[j].leftPorts, myJson.inputs[j].rightPorts, 500, 50*j, myJson.inputs[j].filePath)
                globalIdCounter += 1 //Increment
			    allObjects.push(newBlock)
					//fileInputBlocks.push(newBlock)
			}catch(error){
			    console.log(error);
			}

		}
		//Print the objects
        drawAll()
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });

});

$( "#getFileOutputsButton" ).click(function() {
  fetch("http://localhost:5000/getFileOutputs")
	.then(function (response) {
	return response.json();
  })
	.then(function (myJson) {
		console.log("hi")
    console.log(myJson.outputs)
		for(var j=0; j < myJson.outputs.length; j++){
		    console.log(j)
			//Turn the json into new objects
			//console.log(myJson[i])
			//Initialize input
			try{
                newBlock = new fileOutputBlock(myJson.outputs[j].name, globalIdCounter, myJson.outputs[j].leftPorts, myJson.outputs[j].rightPorts, 650, 50*j, myJson.outputs[j].filePath)
                globalIdCounter += 1 //Increment
			    allObjects.push(newBlock)
					//fileOutputBlocks.push(newBlock)
			}catch(error){
			    console.log(error);
			}

		}
		//Print the objects
        drawAll()
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });

});

$( "#pushButton" ).click(function() {
    console.log("code pushing");
    connectedObjects = []

    pushJSON = {"pushGroups": []} //Reset the pushJSON

    //Initialize the pushJSON with the ips of all the computers
		for(var i=0; i<allObjects.length; i++){
			//Check if object is a computer Type
			object = allObjects[i]
			if(object.hasOwnProperty('blockType')){
				if(object.blockType == 'computer'){
					var newObject = {
	                        "ip": object.ip,
	                        "blocks": []
	                        }
	        pushJSON.pushGroups.push(newObject)

				}
			}
		}
		/*
    for(var i=0; i<computerBlocks.length; i++){
        var newObject = {
                        "ip": computerBlocks[i].ip,
                        "blocks": []
                        }
        pushJSON.pushGroups.push(newObject)
    }
		*/
		//Print the current ip.


		async function fetchIp() {
			const response = await fetch("http://localhost:5000/getIP");
			const json = await response.json()
			console.log(json.ip)
			finishPush(json.ip);
		}
		fetchIp()


		function finishPush(localIp){
			console.log("The local ip is: " + localIp)
			//If it's the local block then add the web interface block
			console.log("The length is: " + String(pushJSON.pushGroups.length) )
			for(var i=0; i<pushJSON.pushGroups.length; i++){
				console.log(pushJSON.pushGroups[i].ip + " and " + localIp)
				if(pushJSON.pushGroups[i].ip == localIp){
					var newProgram = {
							"name": "webSocketInterface",
							"path": "webSocketInterface.py",
							"subTopics": [],
							"pubTopics": [9],
							"sensorMacs": [],
							"inputFiles": [],
							"computerIp": "localhost"   //Default to localhost
					}
					pushJSON.pushGroups[i].blocks.push(newProgram)
				}
			}

	    //Trigger the pushToJSON function of each connected object
	    for(var i=0; i<allObjects.length; i++){
	        //Add the active objects to the list if they have the inputs and outputs
	        if(allObjects[i].hasOwnProperty('outputs')){
	            if(allObjects[i].inputs.length !=0 || allObjects[i].outputs.length !=0){
	                connectedObjects.push(allObjects[i])
	                allObjects[i].pushToJSON()
	            }
	        }
	    }
	    console.log(pushJSON)


	    //------Send the data to the server------
	    const url = "http://localhost:5000/pushSystem";

	    // request options
	    const options = {
	        method: 'POST',
	        body: JSON.stringify(pushJSON),
	        headers: {
	            'Content-Type': 'application/json'
	        }
	    }
	    // send POST request
	    fetch(url, options)
	        .then(res => res.json()) //Resolve the response to json
	        .then(res => console.log(res));

		}
});

$( "#runButton" ).click(function() {
    console.log("system run requested");
    console.log("new version");
    //Prepare the JSON to be sent
    runData = {"ips": []}
    var runTime = Number($("#runTimeTextbox").val())
    console.log("Runtime requested " + runTime)
    runData['runTime'] = runTime

    //Get the ips with blocks
    for(var i=0; i<pushJSON.pushGroups.length; i++){
        if(pushJSON.pushGroups[i].blocks.length > 0){
        //Then it has blocks to run, add the ip to the list
            runData.ips.push(pushJSON.pushGroups[i].ip)
        }
    }


    //------Send the data to the server------
    const url = "http://localhost:5000/runSystem";

    // request options
    const options = {
        method: 'POST',
        body: JSON.stringify(runData),
        headers: {
            'Content-Type': 'application/json'
        }
    }

    // send POST request
    fetch(url, options)
        .then(res => res.json()) //Resolve the response to json
        .then(res => console.log(res));

});

$( "#stopButton" ).click(function() {
    console.log("system stop requested");

    //Prepare the JSON to be sent
    stopData = {'stopDetails': 'default'}

    //------Send the data to the server------
    const url = "http://localhost:5000/stopSystem";

    // request options
    const options = {
        method: 'POST',
        body: JSON.stringify(stopData),
        headers: {
            'Content-Type': 'application/json'
        }
    }

    // send POST request
    fetch(url, options)
        .then(res => res.json()) //Resolve the response to json
        .then(res => console.log(res));

});

$( "#reorderButton" ).click(function() {
    console.log("reordering")
    //console.log(allObjects)
		allObjects.sort((a, b) => {
			return a.stackingIndex - b.stackingIndex;
		});
		//console.log(allObjects)
});

$( "#saveButton" ).click(function() {

	//Put the necessary data into a json format
	console.log("the objects are")
	console.log(allObjects)
	saveObject = {'saveName': $("#saveName").val() ,'saveData':{'allObjects': allObjects}}

	//------Send the data to the server------
	const url = "http://localhost:5000/saveSystem";

	// request options
	const options = {
			method: 'POST',
			body: JSON.stringify(saveObject),
			headers: {
					'Content-Type': 'application/json'
			}
	}
	// send POST request
	fetch(url, options)
			.then(res => res.json()) //Resolve the response to json
			.then(res => console.log(res));

});

$( "#loadButton" ).click(function() {
	var loadName = $("#loadName").val()
	// Error check for .txt later (TODO)
	requestObject = {'loadName': loadName}

	//------Send the data to the server------
	const url = "http://localhost:5000/loadSystem";

	// request options
	const options = {
			method: 'POST',
			body: JSON.stringify(requestObject),
			headers: {
					'Content-Type': 'application/json'
			}
	}
	// send POST request
	fetch(url, options)
	.then(function (response) {
	return response.json();
  })
	.then(function (myJson) {

		//Set all object lists
		loadedObjects = myJson.allObjects
		console.log(loadedObjects)

		//Initialize a lookup object for the instantialized objects;
		midObjectList = []

		//console.log(loadedObjects)
		console.log("Got the loaded objects")
		for(var i=0; i < loadedObjects.length; i++){
			object = loadedObjects[i]
			if(object.hasOwnProperty('objectType')){
				//Create different objects depending on their Type
				console.log("The object type is: " + object.objectType)
				switch(object.objectType){
					case 'CodeBlock':
						newObject = new CodeBlock(object);
						break;
					case 'InputBlock':
						newObject = new InputBlock(object);
						break;
					case 'ComputerBlock':
						newObject = new ComputerBlock(object);
						break;
					case 'SensorBlock':
						newObject = new SensorBlock(object);
						break;
					case 'fileInputBlock':
						newObject = new fileInputBlock(object);
						break;
					case 'fileOutputBlock':
						newObject = new fileOutputBlock(object);
						break;
					case 'RightBoundary':
						newObject = new RightBoundary(object);
						break;
					case 'TopBoundary':
						newObject = new TopBoundary(object);
						break;
					case 'connector':
						newObject = new connector(object);
						break;
					default:
						console.log("Couldn't find a matching object type, panik")
				}
				//Add the new object to allObjects
				midObjectList.push(newObject)
				//allObjects.push(newObject)
			}
		}

		//Start at the current global Id, or the highest globalId in loaded. Need empty space here.
		let lowestId = globalIdCounter
		let highestId = globalIdCounter
		for(var i=0; i < midObjectList.length; i++){
			if(midObjectList[i].globalId > highestId){
				highestId = midObjectList[i].globalId
			}
			if(midObjectList[i].globalId < lowestId){
				lowestId = midObjectList[i].globalId
			}
		}


		console.log("The highest id is: " + highestId)

		//Generate a conversion table between the old ids and the new ones
		var idCounter = highestId + 1
		var conversionTable = {}
		for(var i=0; i < midObjectList.length; i++){
			object = midObjectList[i]
			conversionTable[object.globalId] = idCounter + i
			globalIdCounter = idCounter + i + 1 //Ensures that it is always bigger
		}

		//Trigger the individual conversions
		for(var i=0; i < midObjectList.length; i++){
			midObjectList[i].convertIds(conversionTable)
		}

		//Add the objects to the global object structure.
		for(var i=0; i < midObjectList.length; i++){
			allObjects.push(midObjectList[i])
		}

		//Print the newly loaded objects
    drawAll()
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });
});

$( "#clearButton" ).click(function() {
    if(confirm("Are you sure you want to delete your diagram?")){
			allObjects = []
      ctx.clearRect(0,0,canvasWidth,canvasHeight);
    }
});

/*
$( "#getContainerBlockButton" ).click(function() {
	newBlock = new ContainerBlock("ContainerBlock", globalIdCounter, 1, 1, 300, 100)
  globalIdCounter += 1 //Increment
	newBlock.type = "defaultType"
	allObjects.push(newBlock)
	drawAll()
});

*/

//---------------------------
//----Animation Functions----
//----------------------------
function drawAll(){
    ctx.clearRect(0,0,canvasWidth,canvasHeight);
    //Draw all
	for(i=0; i < allObjects.length; i++){
		if(allObjects[i].drawable == true){
			allObjects[i].drawSelf()
		}
	}
}


//-----------------------------
//----UTILITY FUNCTIONS--------
//-----------------------------
function sendInput(inputJson){
    //------Send the data to the server------
    const url = "http://localhost:5000/handleInputs";

    // request options
    const options = {
        method: 'POST',
        body: JSON.stringify(inputJson),
        headers: {
            'Content-Type': 'application/json'
        }
    }

    // send POST request
    fetch(url, options)
        .then(res => res.json()) //Resolve the response to json
        .then(res => console.log(res));

}

function deleteObject(){
	//Pull an entry from the beginning of the deleteQueue and delete it;
	objectId = deleteQueue.shift()
	console.log("Deleting " + objectId)

	//Delete the object itself
	for(var i=0; i < allObjects.length; i++){
		if(allObjects[i].globalId == objectId){
			allObjects.splice(i,1)
		}
	}
	//Run through the array, triggering all deleteObj;
	for(var i=0; i < allObjects.length; i++){
		allObjects[i].deleteObject(objectId)
		//console.log("At " + i)
	}
	//console.log("Past the deleteObject triggers")

	//Draw everything
	drawAll()
}
//------------------------------------
//------MOUSE INTERACTION-------
//------------------------------------
var isDragging=false;
var borderDragged = {};
var dragOffset = [0,0]
var objectFound = false
var creatingLink = false
var linkStart = null
var linkObjectStart = null
var doingDragSelect = false
var dragSelectStart = [0,0]

function handleMouseDown(e){
  canMouseX=parseInt(e.clientX-offsetX);
  canMouseY=parseInt(e.clientY-offsetY);

  console.log("mouseDown " + canMouseX + " " + canMouseY)

  //Check if any of the objects are being clicked on

  //Check ports first
  for(var i=0; i<allObjects.length; i++){
	  if(('ports' in allObjects[i]) && (objectFound == false)){
		  for(var j=0; j < allObjects[i].ports.length; j++){
			  port = allObjects[i].ports[j]
			  distance = Math.hypot(canMouseX - port.x, canMouseY - port.y)
			  if(distance <= port.radius){
				  objectFound = true
				  creatingLink = true
				  linkStart = port
				  linkObjectStart = allObjects[i]
				  console.log("Port clicked")
				  break
			  }
		  }
	  }

  }

	//Then check the regular blocks
  if(objectFound == false){
		objectClicked = false
	  for(var i=allObjects.length-1; i>=0; i--){     //Decrement loop because we want to interact with the blocks in the opposite order from which we drew them.
		object = allObjects[i]
		//objectClicked = false

		//If object clicked, make it selected and turn on the objectClicked flag.
		if(object.draggable == true){
            if(canMouseX > object.x && canMouseX < object.x + object.width && canMouseY > object.y && canMouseY < object.y + object.height){
                console.log(object.blockName + 'clicked')
                object.selected = true
                objectClicked = true
                break
            };
		}

	  };
			//If something was clicked, trigger the handleMouseDown of all selected objects.
				if(objectClicked == true){
					for(var i=allObjects.length-1; i>=0; i--){
						object = allObjects[i]
						if(object.hasOwnProperty('selected')){
							if(object.selected == true){
								object.handleMouseDown(canMouseX, canMouseY)
							}
						}
					}
				}

			//If nothing has been clicked, clear the selections
				if(objectClicked == false){
					doingDragSelect = true;
					dragSelectStart = [canMouseX, canMouseY];
				};
        drawAll()
  }

}

function handleMouseUp(e){
  canMouseX=parseInt(e.clientX-offsetX);
  canMouseY=parseInt(e.clientY-offsetY);
  console.log("mouseUp")
  for(var i=allObjects.length-1; i>=0; i--){     //Decrement loop because we want to interact with the blocks in the opposite order from which we drew them.
    object = allObjects[i]
    object.handleMouseUp(canMouseX, canMouseY)
  };

  if(creatingLink){//If creating a connector, check if you've arrived at another port(Not the same one)
	  //Check ports first
	  for(var i=0; i<allObjects.length; i++){
		  if(('ports' in allObjects[i])){ //Note: Not efficient to scan whole thing regardless
			  for(var j=0; j < allObjects[i].ports.length; j++){
				  port = allObjects[i].ports[j]
				  distance = Math.hypot(canMouseX - port.x, canMouseY - port.y)
				  if(distance <= port.radius){
					//Create a line object (Draw it too here?)
					if(linkStart == port){
						break //Its the same port
					}
					newConnector = new connector(linkStart, linkObjectStart, globalIdCounter)
					globalIdCounter += 1
					newConnector.destPort = port
					newConnector.destId = allObjects[i].globalId;
					newConnector.destX = port.x
					newConnector.destY = port.y


					//Add to the input and outputs of the blocks (Add the globalIds)
					console.log(newConnector.destId)
					sourceObject = linkObjectStart
          sourceObject.outputs.push(newConnector.destId)
					let destObject = allObjects[i]
          destObject.inputs.push(sourceObject.globalId)

					//Add to allObjects and connector objects
					allObjects.push(newConnector)
					//connectorBlocks.push(newConnector)
					//Draw Self
					newConnector.drawSelf()
					console.log("Connection established")
					break
				  }
			  }
		  }

	  }
  }

	if(doingDragSelect){
		console.log("Finishing drag select");

		if(Math.abs(dragSelectStart[0] - canMouseX) < 10 && Math.abs(dragSelectStart[1] - canMouseY) < 10){
			console.log("No movement, deselecting");
			for(var i=allObjects.length-1; i>=0; i--){     //Decrement loop because we want to interact with the blocks in the opposite order from which we drew them.
					object = allObjects[i];
					object.selected = false;
			}
		}
		else{
			//Select blocks inside of the selection box.
			sbR = Math.max(dragSelectStart[0], canMouseX)
			sbL = Math.min(dragSelectStart[0], canMouseX)
			sbT = Math.min(dragSelectStart[1], canMouseY)
			sbB = Math.max(dragSelectStart[1], canMouseY)
			for(var i=allObjects.length-1; i>=0; i--){     //Decrement loop because we want to interact with the blocks in the opposite order from which we drew them.
					object = allObjects[i];
					if(object.hasOwnProperty('selected')){
						//oL = object left
							oL = object.x;
							oR = object.x + object.width;
							oT = object.y;
							oB = object.y + object.height;
							if((sbT < oB) && (sbR > oL) && (sbL < oR) && (sbB > oT)){
								object.selected = true;
							}
					}
			}
		}

	}

  //clear all flags
  objectFound = false
  creatingLink = false
	doingDragSelect = false
  linkStart = null
  drawAll()
}

function handleMouseOut(e){
  canMouseX=parseInt(e.clientX-offsetX);
  canMouseY=parseInt(e.clientY-offsetY);
  // user has left the canvas, so clear the drag flag
  isDragging=false;
}

function handleMouseMove(e){
  canMouseX=parseInt(e.clientX-offsetX);
  canMouseY=parseInt(e.clientY-offsetY);
  // if the drag flag is set for an object, trigger it's move handler (print screen at end)
  changeMade = false
  for(var i=allObjects.length-1; i>=0; i--){     //Decrement loop because we want to interact with the blocks in the opposite order from which we drew them.
    object = allObjects[i]

    if(object.beingDragged == true || object.interacting == true || object.boundaryDragging == true){
        object.handleMouseMove(canMouseX, canMouseY)
        changeMade = true
        //break for multiple blocks
    }

  };
  if(changeMade){
   drawAll()   //Draw them all after any change
  }
  if(creatingLink){
    //Clear everything and draw it again, along with the new line
    ctx.clearRect(0,0,canvasWidth,canvasHeight);
    drawAll()

    ctx.beginPath();
    ctx.moveTo(linkStart.x, linkStart.y);
    ctx.lineTo(canMouseX, canMouseY);
    ctx.stroke();
  }

	if(doingDragSelect){
		//Clear everything and draw it again, along with a see through blue box
		ctx.clearRect(0,0,canvasWidth,canvasHeight);
		drawAll()

		ctx.beginPath();
		ctx.globalAlpha = 0.2;
		ctx.fillStyle = "#0000ff";
		ctx.fillRect(dragSelectStart[0], dragSelectStart[1], canMouseX - dragSelectStart[0], canMouseY - dragSelectStart[1]);
		ctx.stroke();
		ctx.globalAlpha = 1;
	}
}

function handleKeyDown(e){
	console.log(e.key + " pressed")
	//Delete handler
	if(e.key == "Delete"){
		deleteQueue = []
		console.log("Delete key pressed")
		//Delete all selected; Then run run the deleteObj method for everything.
		for(var i=0; i < allObjects.length; i++){
				object = allObjects[i];
				if(object.hasOwnProperty('selected')){
						if(object.selected == true){
							//console.log("Deleting " + object.globalId)
							deleteQueue.push(object.globalId)
						}
				}
		}
		//Request the deletions
		while(deleteQueue.length > 0){
			deleteObject()
		}
	}
	if(e.ctrlKey && e.key == '+'){
		print("yes")
	}
}

$("#mainCanvas").mousedown(function(e){handleMouseDown(e);});
$("#mainCanvas").mousemove(function(e){handleMouseMove(e);});
$("#mainCanvas").mouseup(function(e){handleMouseUp(e);});
$("#mainCanvas").mouseout(function(e){handleMouseOut(e);});
$(document.body).keydown(function(e){handleKeyDown(e);});

//https://www.tutorialspoint.com/html5/html5_drag_drop.html;

//Window reoffsetting
function reOffset(){
    var boundingBox=canvas.getBoundingClientRect();
    offsetX=boundingBox.left;
    offsetY=boundingBox.top;
    //console.log("Reoffset to " + offsetX + " " + offsetY)
}

$(window).scroll(reOffset)
$(window).resize(reOffset)
