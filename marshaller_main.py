"""
marshaller_main.py
Uses a timer interrupt to poll for the existence of data in the uart buffer.
This will allow other things to get done rather than spending all the time
polling. Need to think about where to insert disable_irq and enable_irq.
Save onto espp32 as main.py to use.
"""
import machine
from machine import UART
import time
import select

import network
from esp import espnow
import ujson as json 

class Marshaller:
    

    #Class attributes
    _storage_name   = "componentIds.json"
    _mac_dict = {}
    
    
    #set up the uart
    baud = 115200
    uart1 = UART(1, baudrate = baud, tx=17, rx=16 )
    uart1.init(baud, bits=8, parity=None, stop=1)
    print('uart ready')

    #set up the polling
    uart_poll = select.poll()
    uart_poll.register(uart1, select.POLLIN)
    print('polling ready')
    #set up the timer interrupt
    polling_timer = machine.Timer(0)
    print('timer ready')
   
    #esp-now needs an iniitalized network
    w0 = network.WLAN(network.STA_IF)
    w0.active(True)
    #create espnow interface
    esp_if = espnow.ESPNow()
    esp_if.init()

    
    def __init__(self):
        print('In init')
        #cmds_dict holds commands targeted at this object. To add
        #new commmands, add in the command name and write a
        #callback handler of the same name. The dictionary can be
        #used to invoke the command action.
        
        self.cmds_dict = {}
        self.cmds_dict ["set_axis_mac_ids"] = self.set_axis_mac_ids
        self.this_mac = ""
        
        
        #Finish up the callback link to the timer now that we have
        #an instance
        self.polling_timer.init(period=300, mode=machine.Timer.PERIODIC,
                                callback=self.on_timer_interrupt)
        print('Leave init')

    def set_axis_mac_ids(self, parms, block):
        for axis, mac_str in parms:
            self._mac_dict[axis] = mac_str
        print (f"in set_axis_mac, {self._mac_dict}")
        self.this_mac = self._mac_dict.get('m')
        for peer_mac_str in self._mac_dict.values():
            peer_mac_bytes = self.mac_str_to_bytes(peer_mac_str)
            self.esp_if.add_peer(peer_mac_bytes)
        self.esp_if.config( on_recv = self.on_espnow_recv_cb)
            

        
    def mac_str_to_bytes(self, mac_str):
        """ given a mac address as a string in the form hh:hh:hh:hh:hh:hh,
        the equivalent valued byte array is returned that can be used to
        specify components for comm"""
        mac_vals = mac_str.split(':')
        mac_addr_bytes = [int(b, 16) for b in mac_vals]
        return bytes(mac_addr_bytes)    
    
    def read_uart(self):
        #time.sleep_ms(500)
        bytes_read = self.uart1.read()
        if bytes_read != None:
            cmd = json.loads(bytes_read)
            print(f"in read_uart, cmd is: {cmd}")
            #bytes_read = bytes_read.decode('utf-8').rstrip('\n')
            print(f"cmd: {len(cmd)}: <{cmd}>. It is of type {type(cmd)}.")
            #TODO: This is stopgap just to check. BAD CODE!!!!!!
            if cmd[1] != 'm':
                self.send_cmd_over_esp( cmd[1], cmd[0], cmd[2], cmd[3])
            else:
                self.cmds_dict.get(cmd[0])( cmd[2], cmd[3])



            
            
    def serialize( self, str_list):
        """ Serializes a list of string elements using json in order to
        transport over uart"""
        return json.dumps(str_list)




    def send_cmd_over_esp( self, axis, cmd, parm, block):
        cmd_list = [cmd, parm, block]
        serial_cmd = self.serialize(cmd_list)
        mac_str = self._mac_dict.get(axis)
        mac_bytes = self.mac_str_to_bytes(mac_str)
        success = self.esp_if.send( mac_bytes, serial_cmd, True)
        if not success:
            print('espnow message send failed.')

    def on_espnow_recv_cb(self, e):
        while self.esp_if.poll():
            print(e.irecv(0))


    def on_timer_interrupt(self, timer ):
        #print('In on_timer_interrupt')
        events = self.uart_poll.poll(5)
        for file in events:
            if file[0] == self.uart1:
                state = machine.disable_irq()
                self.read_uart()
                machine.enable_irq(state)


marshaller = Marshaller()
while True:
    pass


