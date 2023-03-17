//--------------------------
//------BUTTONS-------------
//--------------------------
$( "#startDrawioListenerButton" ).click(function() {
	requestDict = {'saveName': $("#drawio_filename").val()}
	console.log($("#drawio_filename").val())
	console.log(requestDict)

	//------Send the data to the server------
	const url = "http://localhost:5000/startDrawioChangeListener";

	// request options
	const options = {
			method: 'POST',
			body: JSON.stringify(requestDict),
			headers: {
					'Content-Type': 'application/json'
			}
	}
	// send POST request
	fetch(url, options)
			.then(res => res.json()) //Resolve the response to json
			.then(res => console.log(res));
});

$( "#stopDrawioListenerButton" ).click(function() {
  fetch("http://localhost:5000/stopDrawioChangeListener")
	.then(function (response) {
	console.log("Listener Stop Requested")
	return response;
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });
});

$( "#runButton" ).click(function() {
  fetch("http://localhost:5000/startDrawioSystem")
	.then(function (response) {
	console.log("System Start Requested")
	return response;
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });
});

$( "#stopButton" ).click(function() {
  fetch("http://localhost:5000/stopDrawioSystem")
	.then(function (response) {
	console.log("System Stop Requested")
	return response;
  })
	.catch(function (error) {
    console.log("Error: " + error);
  });
});