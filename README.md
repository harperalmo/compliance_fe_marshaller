marshaller

Language: miicropython for the the esp32

PROJECT DESCRIPTION:
This is a module that runs an esp32 microcontroller attached to a Raspberry Pi
via serial lines. The marhsaller's job is to send commands and receive messages
from a backend system that runs stepper motors so a digital indicator can take 
compliance measurements at specific locations on an instrument's soundboard. 
This process is outlined in David Hurd's Left Brain Lutherie book. 

The controlling front end software is run by a user interacting with the 
commander, whoose code is stored in the compliance_fe_commander repository.


