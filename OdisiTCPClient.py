""" Script to read Odisi measurements directly into the user PC.

Important things to keep in mind:
- Wifi connection through Santa Anna network does not allow for TCP connections (not even pinging works!). 
    For this reason, an Ethernet cable is used to connect the user's PC to the Odisi laptop. 
- To stablish the connection, get the Odisi Laptop's IP from the Odisi software -> Settings -> Streaming Properties 
    (or just using the terminal + ifconfig). Then, change the server IP address in this script, if necessary.
- If the connection is not possible (host not reachable or time out errors) try reconnecting the Ethernet cable and
    restarting the Odisi software.
- Currently, only one channel and only one Odisi equipment connection at a time are supported.
- The measurements are stored into a CSV file found in the same folder as this script.
- A measurement cycle refers to the time between the user pressing the 'Start' button and the 
    'Stop' button in the Odisi software.
- Note that when the 'View' option is selected in the Odisi software after selecting the 'Disarm' option, it starts sending 
    measurement data without the user asking for it. The proper adquisition of this data is not suported, and thus should be 
    discarded by the user via the command terminal with "DEL". This is because there is no way of differentiating this data from 
    the regular measuring data obtained after selecting the 'Start' button. 
    To finish this measurement stream, select the "Arm" option in the software.
- Sometimes the keyboard interruption is not detected. In this case, just delete the terminal and start a new one.
- If the Odisi configuration is to be changed, it has to be in 'Disarmed' mode. After changing the configuration,
    wait for a 'Metadata updated!...' message to start measuring again.
- Measurements can be received in three formats from the Odisi:
    - Full fiber measurement (no gages, no segments)
    - Gages measurement (multiple gages, no segments)
    - Gages and segments measurements (multiple gages, multiple segments)
"""

import socket
import json
import csv
import numpy as np
import metadataHandler, measurementHandler

def connectClient(ipAddress):
    """ Function to create client socket and connect it to Odisi server.  
    """
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = (ipAddress, 50000)
    print('Connecting to %s port %s' % server_address)
    sock.connect(server_address)

    return sock

def parseReceivedData(receivedData, storedData=''):
    """ Function to parse received data from Odisi.
    Inputs:
        receivedData: bytes
            Received data from Odisi.
        storedData: bytes
            Data stored from previous iteration.
    Outputs:
        receivedData: bytes
            Data received from Odisi.
        storedData: bytes
            Data stored from previous iteration.
        checksum: str
            Checksum of the received package.
    """
    # Parsing principles:
    # Append all successively received data until a '\x00' terminator is found
    # Multiple packages could be received in a single TCP message
    # If 1 or more complete packages are found in the message, return them as a list
    # If no complete packages are found, store the data and return it to use it in the next iteration
    # It is possible to return the complete packages and the non-complete stored data for next iteration
    # Also return the checksum of each complete package

    def extractChecksum(data):
        try:
            return data.decode("utf-8").split('\n')[1].replace('\x00','')
        except IndexError:
            return None

    # First, handle any stored data from previous iteration
    workingData = storedData + receivedData
    packages = []
    checksums = []

    # Keep processing while we find terminators
    while b'\x00' in workingData:
        parts = workingData.split(b'\x00', 1)
        completePackage = parts[0]
        workingData = parts[1]

        # Process the complete package
        if completePackage.startswith(b'{'):
            package = completePackage.decode('utf-8')
            checksum = extractChecksum(completePackage)     
            package = package.strip('\r\n' + checksum)       
            packages.append(package)
            checksums.append(checksum)

    # Store remaining data if it starts with a new package
    newStoredData = workingData if workingData.startswith(b'{') else b''
    
    if packages:
        return packages, newStoredData, checksums
    return None, workingData, None

def getMeasurementCycle(connectedSocket, metadataObj, measurementObj):
    """ Function to retrieve and return the measurement data of a single measurement cycle from Odisi.

    This function keeps receiving TCP messages (metadata or measurement) until a complete measurement cycle is received.    
    """
    storedData = b''
    measurementStarted = False
      
    while True:        
        receivedData = connectedSocket.recv(4096)
        #print(receivedData)

        result = parseReceivedData(receivedData, storedData)
        packages, storedData, checksums = result if result[0] else ([], result[1], [])

        if packages:
            for package, checksum in zip(packages, checksums):                
                receivedDataJSON = json.loads(package)

                if receivedDataJSON['message type'] == 'metadata':                        
                    metadataObj.processMetadata(checksum, receivedDataJSON, measurementStarted)
                    # Check if the measurement has stopped:
                    # (It may be slow because the program has to wait for the Odisi to send a metadata package
                    # containing the 'stopped' status after the measuring is done, which may take up to 5 seconds)
                    if metadataObj.checkStatus() == 'stop' and measurementStarted:
                        measurementObj.emptyBuffer()
                        return measurementObj.measurement[1:,:], measurementObj.time, measurementObj.position, measurementObj.posNames
                elif receivedDataJSON['message type'] == 'measurement':
                    # Sometimes the Odisi sends empty packages for some reason
                    if len(receivedDataJSON['data']) != 0:                                                 
                        if not measurementStarted and metadataObj.checkStatus() == 'stop':
                            measurementStarted = True
                            print('Acquiring measurement...')
                        try:                        
                            measurementObj.processMeasurement(receivedDataJSON, metadataObj)                        
                        except: # Just to avoid stopping the program when there is a package continuity error (very rare)
                            pass
                    else:
                        pass
                elif receivedDataJSON['message type'] == 'tare': # I've never seen a tare package lol
                    pass

def saveMeasurementsCSV(measurementData, timeData, positionData, positionNames, filename):
    """Save measurement data, time data and position data to a CSV file.

    Maybe include metadata information such as measurement rate, gage pitch, sensor type, etc.?
    """
    # Maybe check for filename validity?
    if not filename.endswith('.csv'):
        filename += '.csv'
        
    # Create header with position values
    if len(positionNames) != 0:
        header = ['Gage/Segment Name']
        header.extend([name for name in positionNames])
        tempHeader = ['X-axis']
        tempHeader.extend([f'{pos:.2f}' for pos in positionData])
        header = np.vstack((header,tempHeader)).tolist()
    else:
        header = ['X-axis']
        header.extend([f'{pos:.2f}' for pos in positionData])

        
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        if len(positionNames) != 0:
            for i in range(len(header)):
                writer.writerow(header[i])
        else:      
            writer.writerow(header)
    
        # Write data rows
        for i in range(len(timeData)):
            row = [timeData[i]]
            row.extend(measurementData[i])
            writer.writerow(row)

    return filename            

def receiveAndProcessData(connectedSocket):
    """ Function to receive data from Odisi.

    It obtains the measurement data, time data, and position data from one measurement cycle. 
    Then, the data is processed (for now only stored into a CSV or JSON file).
    Afterwards, a new measurement cycle is started.
    This keeps running until the user stops the program with a Keyboard Interruption (ctrl + c).
    """
    metadataObj = metadataHandler.metadataHandler()
    
    try:        
        while True:
            measurementObj = measurementHandler.measurementHandler()
            
            # Get measurement data, time data, and position data from one measurement cycle
            measurementData, timeData, positionData, posNames = getMeasurementCycle(connectedSocket, metadataObj, measurementObj)            

            # Process the data
            print('Processing data, please wait before measuring again!')
            print(f"Received {len(measurementData)} measurements")
            
            # Get filename from user
            userinput = input("Enter filename to save the data or type 'DEL' to delete the current data: ")
            if userinput != 'DEL' and userinput != 'del':
                filenameOut = saveMeasurementsCSV(measurementData, timeData, positionData, posNames,userinput)
                print(f"Data saved to {filenameOut}")
            else:
                print("Data deleted!")   # Actually does not delete anything, just skips the saving.

            metadataObj.resetChecksum() # Force an update on the metadata parameters to avoid problems when changing the config.
            print("Wait for metadata update before measuring again!")
            
            # measurementObj = None # ?

    except KeyboardInterrupt:
        print("Program stopped by user")
        return

def main():
    # Read the IP address from the Odisi device (in Settings -> Streaming Properties)
    socketObj = connectClient('169.254.151.199')

    try:
        receiveAndProcessData(socketObj)        
    finally:
        print('Closing socket')
        socketObj.close()

if __name__ == "__main__":
    main()