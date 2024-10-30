import numpy as np

class measurementHandler:
    """ Measurement class
    """
    def __init__(self):
        self.measurement = np.array([])     # Can be obtained from measurement[data]
        self.sequenceNumber = 0     # Can be obtained from measurement[sequence number]     
        
        self.position = []          # Can be obtained from metadata[gage pitch]*measurement[number of gages]        
        self.time = [] 
        self.gagesNumber = 0        
        self.posNames = []

        self.bufferSize = 0 
        self.buffer = np.zeros([])
        self.bufferIndex = 0       
           
    def checkSequenceNumber(self,newSequenceN):
        """ Function that checks if a package has been lost using the sequence number value
        """
        if self.sequenceNumber == 0:
            self.sequenceNumber = newSequenceN
        elif newSequenceN == (self.sequenceNumber + 1) and self.sequenceNumber != 0:
            self.sequenceNumber = newSequenceN
        else:
            # For some reason some packages are lost, but is really rare.
            print("Package lost! %i %i" % (self.sequenceNumber, newSequenceN))
            self.sequenceNumber = newSequenceN
            raise Exception('Sequence number error!')

    def emptyBuffer(self):
        """ Function that empties the buffer
        """
        if self.bufferIndex > 0:
            # Append the non-empty part of the buffer to self.measurement
            self.measurement = np.vstack((self.measurement, self.buffer[:self.bufferIndex]))
            self.bufferIndex = 0

    def setPositionArray(self,newData,metadata):
        """ Function to get the position array from the metadata"""
        # Check for the 3 possible cases of position vector:
        # 1. Full fiber measurement
        if not metadata.userDefinedGagesFlag and not metadata.userDefinedSegmentFlag:            
            initPos = 0
            posVector = np.linspace(initPos,metadata.gagePitch*newData['number of gages'],num=newData['number of gages'])
            self.position = [ round(elem, 2) for elem in posVector ]      

        # 2. N-points measurement (no segments)
        elif metadata.userDefinedGagesFlag and not metadata.userDefinedSegmentFlag:            
            self.position = metadata.userDefinedGagesLocs
            self.posNames = metadata.userDefinedGagesNames

        # 3. N-points, M-segments
        elif metadata.userDefinedGagesFlag and metadata.userDefinedSegmentFlag:            
            temporalPos = [ round(elem, 2) for elem in metadata.userDefinedGagesLocs ]                        
            temporalNames = metadata.userDefinedGagesNames
            for i in range(len(metadata.userDefinedSegmentLocs)):
                temporalSegmentArray = np.linspace(metadata.userDefinedSegmentLocs[i],metadata.userDefinedSegmentLocs[i]+metadata.gagePitch*(metadata.userDefinedSegmentSize[i]-1),num=metadata.userDefinedSegmentSize[i])
                for j in range(metadata.userDefinedSegmentSize[i]):                    
                    temporalPos.append(round(float(temporalSegmentArray[j]),2))
                    temporalNames.append(metadata.userDefinedSegmentNames[i]+'['+str(j)+']')                
            
            self.position = temporalPos
            self.posNames = temporalNames


    def processMeasurement(self,newData,metadata):
        """ Function that handles the received measurement packages
        """
        # Check if data has something
        if len(newData['data']) == 0 or metadata.checkStatus() == 'init':
            return
        
        # Check if a sequence has been lost using the sequence number value
        try:
            self.checkSequenceNumber(newData['sequence number'])
        except:
            raise Exception('Sequence number error!')
        
        # Get number of gages and pre-allocate memory for data (only once)
        if self.gagesNumber == 0:
            self.gagesNumber = newData['number of gages']
            self.bufferSize = 1000
            self.measurement = np.zeros((1,self.gagesNumber))
            self.buffer = np.zeros(((self.bufferSize, self.gagesNumber)))

        # Position vector (should only be calculated once per measurement cycle)
        if len(self.position) == 0:
            self.setPositionArray(newData,metadata)
        
        # Time vector (append the time stamp from newData)
        # Maybe the same memory treatment should be applied for this vector
        # With date:
        #timeStampStr = str(newData['day']) + '/' + str(newData['month']) + '/' + str(newData['year']) + ' ' + str(newData['hours']) + ':' + str(newData['minutes']) + ':' + str(newData['seconds']) + '.' + str(newData['milliseconds']).zfill(3)  + str(newData['microseconds']).zfill(3)           
        # No date:
        timeStampStr = str(newData['hours']) + ':' + str(newData['minutes']) + ':' + str(newData['seconds']) + '.' + str(newData['milliseconds']).zfill(3) + str(newData['microseconds']).zfill(3)    
        self.time.append(timeStampStr)  

        # Add new data to buffer
        self.buffer[self.bufferIndex] = newData['data']
        self.bufferIndex += 1

        # If buffer is full, append to self.measurement. 
        # This is to avoid re-allocating memory every time a new measurement is received. 
        # When 1000 measurements are received, the buffer will be emptied.        
        if self.bufferIndex == self.bufferSize:
            self.measurement = np.vstack((self.measurement, self.buffer))
            self.bufferIndex = 0