# Code from Chapter 5: Complex Adaptive Systems Architect (CASA): A Software for the Development of Distributed, Agent-Based Software and the Implementation of SBRL Systems.
Code supporting the CASA Application, described in Chapter 5.

## Installation Instructions
### Prerequisites:
* Miniconda or Anaconda
* Browser
* Draw.IO Desktop Version (If using the Draw.IO front end)

### Installation Steps
1. Clone repository
2. Install packages as requested by error messages. (Most packages should be listed at the tops of files: CASArchitect/testBedServer.py and CASArchitect/citizenServer.py

## Run Steps
### Web Front End:
1. Run CASArchitect/testBedServer.py using python.
2. Go to localhost:5000 in your browser.
3. Click the "Go to Web Interface" Button.
4. Operate the interface as described in the dissertation document.

### Draw.IO Front End:
1. Run CASArchitect/testBedServer.py using python.
2. Go to localhost:5000 in your browser.
3. Click the "Go to Drawio Interface" Button.
4. Enter the Draw.IO file name that you will be designing your system in.
5. Click "Start Drawio listener"
6. Edit and save your Draw.IO file
7. Click "Run System" and "Stop System" to toggle system operation.
8. Click "Stop Drawio Listener" when done working.


## Notes:
* Bluetooth and Computer scans in web interface currently only work on Linux.
* Draw.IO front end should work with both Linux and Windows.

## Future Improvements
The code will likely be refactored into a more convenient form soon (Docker Image), for users who are not used to working with Linux and Anaconda.

## Made improvements or have questions?
Contact the author at kylenorland@arizona.edu
