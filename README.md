# Odisi-TCPClient
Program to create a TCP client that connects to an Odisi 6001 OFDR system. The program receives the datastream coming from the equipment and saves it into a CSV file.

How to use:

- First, make sure that the Odisi software is running. Acquire and set the sensor key if necessary. Also, make sure to set all desired gages and segments before 'Arming' the system.
- Once everything is set up, run the program. You can now 'Arm' the Odisi if you have not done so already.
- With the system in 'Armed' mode, you should receive a 'Metadata updated!' message from the program. Once this message is received, you can now make a measurement with the 'Start' button in the Odisi software.
- Note that everytime you want to make a measurement, you should first wait for a 'Metadata updated!' message from the program.
- Click the 'Stop' button in the Odisi software when you want to stop the measurement.
- Now the program will ask for a filename to save the received data into a CSV file. If you do not want to save the current data, type 'del' (or 'DEL') and press enter. The data will be discarded.
- The program will keep running and saving incoming data until the user presses Ctrl+C.

- Important note: If you click the 'Disarm' button in the Odisi software, you will need to re-arm the system to receive data from the Odisi again. However, if you click the 'View' button in the Odisi software (while in 'Disarmed' mode), the equipment will enter a state where it is measuring and the user can change certain settings, such as desired gages and segments. As the equipment is currently measuring, it will send data to the client. This data, i.e. the 'View' window data, should be discarded by the user because the configuration is not yet fully set. For this, type 'del' when the program asks for a filename to save the data into a CSV file. This datastream will end when you re-enter the 'Arm' mode. In summary:
        - If after measuring you go into 'Disarmed' mode, you will need to re-arm the system to receive data again.
        - If while in 'Disarmed' mode you enter the 'View' window, the Odisi will start sending data until you re-enter the 'Arm' mode.
        - This received data should be discarded by the user typing 'del' when the program asks for a filename to save the data.
        - If you want to change configurations, such as gages and segments, do it while in the 'View' window, but discard the received data afterwards.

Notes:
- This program only receives data from the Odisi system. No commands are sent from this client to the equipment.
- This program is designed to work with a single Odisi system simultaneously.
- Wifi connection through Santa Anna network does not allow for TCP connections, so an Ethernet cable is used to connect the user's PC to the Odisi laptop. To get the Odisi Laptop's IP from the Odisi software: Settings -> Streaming Properties (in 'Disarmed' mode). Then, change the server IP address in this script, if necessary.
- The program can be used in the same laptop as the Odisi software, just changing the server IP address in the script to '127.0.0.1' (in the main() function).
- System/Equipment: Luna Odisi 6001 OFDR, Software: Odisi-6-UserInterface-v2.4.2, Program: Python3 script.