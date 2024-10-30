class metadataHandler:    
    """ Metadata class
    """
    def __init__(self):
        self.checkSum = '0000'      
        self.status = ''
        self.sensorLength = 0
        self.sensorType = ''
        self.gagePitch = 0
        self.measurementRate = 0

        self.userDefinedGagesFlag = False
        self.userDefinedGagesLocs = []
        self.userDefinedGagesNames = []
        self.userDefinedGagesIndex = []

        self.userDefinedSegmentFlag = False
        self.userDefinedSegmentLocs = []            
        self.userDefinedSegmentIndex = []
        self.userDefinedSegmentNames = []
        self.userDefinedSegmentSize = []
        
    def updateStatus(self,newData):
        """ Function that reads the incoming metadata system status and updates it accordingly.         
        """
        if newData['system status'] == '':  # Welcome message
            self.status = 'init'            
        elif newData['system status'] == 'stopped':
            self.status = 'stop'
        elif newData['system status'] == 'measuring':
            self.status = 'measuring'
        return

    def checkStatus(self):
        """ Function that checks the current system status stored in the object.
        """
        if self.status == '':
            self.status = 'init'
        return self.status            

    def checksumChanged(self,newChecksum):
        """ Function that checks if the checksum has been modified with respect to the currently stored one.
        """
        if newChecksum != self.checkSum:
            # The received message is different from the one stored                   
            return True
        else:            
            return False
        
    def resetChecksum(self):
        """ Function that resets the checksum to the default value.
        """
        self.checkSum = '0000'
        return
        
    def getGages(self,newData):
        """ Function that process the newData JSON to obtain the number and information of gages.
        """
       
        # 3 cases:
        # - 0 gages, 0 segments: full fiber measurement
        # - N (>0) gages, 0 segments: N-points measurement
        # - N (>0) gages, M (>0) segments: N-points measurement, plus M segments measurement, which
        # have X points each
        
        if 'gages' not in newData['sensors'][0] and ('segments' not in newData['sensors'][0] or newData['sensors'][0]['segments'][0]['segment name'] == 'default'):    # Full measurement
            self.userDefinedGagesFlag = False
            self.userDefinedSegmentFlag = False

        elif 'gages' in newData['sensors'][0] and 'segments' not in newData['sensors'][0]:    # N-points measurement
            self.userDefinedGagesFlag = True
            self.userDefinedSegmentFlag = False

            # Get the gages and their locations
            self.userDefinedGagesLocs = []
            self.userDefinedGagesIndex = []
            self.userDefinedGagesNames = []
            for i in range(len(newData['sensors'][0]['gages'])):
                self.userDefinedGagesLocs.append(newData['sensors'][0]['gages'][i]['location (mm)'])  
                self.userDefinedGagesIndex.append(newData['sensors'][0]['gages'][i]['index'])  
                self.userDefinedGagesNames.append(newData['sensors'][0]['gages'][i]['gage name'])

        elif 'gages' in newData['sensors'][0] and 'segments' in newData['sensors'][0]:    # N-points, M-segments measurement
            self.userDefinedGagesFlag = True
            self.userDefinedSegmentFlag = True

           # Get the gages and their locations
            self.userDefinedGagesLocs = []
            self.userDefinedGagesIndex = []
            self.userDefinedGagesNames = []
            for i in range(len(newData['sensors'][0]['gages'])):
                self.userDefinedGagesLocs.append(newData['sensors'][0]['gages'][i]['location (mm)'])  
                self.userDefinedGagesIndex.append(newData['sensors'][0]['gages'][i]['index'])  
                self.userDefinedGagesNames.append(newData['sensors'][0]['gages'][i]['gage name'])

            # Get segments
            self.userDefinedSegmentLocs = []            
            self.userDefinedSegmentIndex = []
            self.userDefinedSegmentNames = []
            self.userDefinedSegmentSize = []
            for i in range(len(newData['sensors'][0]['segments'])):                                       
                self.userDefinedSegmentLocs.append(newData['sensors'][0]['segments'][i]['location (mm)'])
                self.userDefinedSegmentIndex.append(newData['sensors'][0]['segments'][i]['index'])
                self.userDefinedSegmentNames.append(newData['sensors'][0]['segments'][i]['segment name'])
                self.userDefinedSegmentSize.append(newData['sensors'][0]['segments'][i]['size'])       
                
    def processMetadata(self,newChecksum,newData,measuringFlag):    
        """ Function that handles the received metadata packages        
        """
        # First check if received message is from previous session: (sometimes it stucks)
        if self.checkStatus() == 'init' and newData['system status'] == 'measuring':
            return

        # Update and check system status: 
        self.updateStatus(newData)        
        if self.checkStatus() == 'init':
            print('Connection stablished with server!')
            print('Acquiring metadata, please wait before measuring (the Odisi should be in "Arm" mode)...')
            return 
        
        # Check if checksum has been modified:
        # When the Odisi is measuring it still sends metadata packages every 5 seconds.
        # These packages have a different checksum because the 'system status' has changed, 
        # but all the other metadata is the same.
        if self.checksumChanged(newChecksum) and not measuringFlag:
            # Update metadata parameters:
            self.checkSum = newChecksum     
            self.gagePitch = newData['sensors'][0]['gage pitch (mm)']
            self.sensorLength = newData['sensors'][0]['length (m)']
            self.sensorType = newData['sensors'][0]['sensor type']
            self.measurementRate = newData['measurement rate']       
            
            # Obtain gages:
            self.getGages(newData)

            print('Metadata updated!')            
            return
        else:
            # Do nothing            
            return             