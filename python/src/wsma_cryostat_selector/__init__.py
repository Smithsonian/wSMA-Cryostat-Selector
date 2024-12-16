__version__ = '1.0.1'

from time import sleep

from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.constants import Endian

default_IP = "192.168.42.100"
default_port = 502


class Selector(object):
    """Class for communicating with the wSMA Selector Wheel Controller.
    The SelectorWheel object wraps a pymodbus.ModbusTcpClient instance which
    communicates with the Selector Wheel Controller over TCP/IP.
    """
        #: int: address of the controller's commanded register, i.e. the _position of the wheel.
    _compos_addr = 1000
    
    #: int: address of the controller's current position register, i.e. the _position of the wheel
    _curpos_addr = 1001
    
    #: int: address of the controller's speed register.
    _speed_addr = 1002

    #: int: address of the controller's return code register.
    _retcode_addr = 1003

    #: int: address of the controller's time register.
    _time_addr = 1004

    #: int: address of the controller's angle error register (angular error in degrees)
    _angle_addr = 2005
    
    #: int: address of the controller's angle error register (angular error in degrees)
    _angle_error_addr = 2006
    
    #: int: address of the controller's angle error register (angular error in degrees)
    _angle_tolerance_addr = 2007
    
    #: int: address of the controller's angle offset register (angular offset in degress)
    _angle_offset_addr = 2008
    
    #: int: address of the controller's position 1 setting
    _pos_1_addr = 1009
    
    #: int: address of the controller's position 2 setting
    _pos_2_addr = 1010
    
    #: int: address of the controller's position 3 setting
    _pos_3_addr = 1011
    
    #: int: address of the controller's position 4 setting
    _pos_4_addr = 1012
    
    #: int: address of the controller's resolver turns register
    _resolver_turns_addr = 2013
    
    #: int: address of the controller's resolver position register
    _resolver_position_addr = 2014

    def __init__(self, ip_address=default_IP, debug=False):
        """Create a SelectorWheel object for communication with one Selector Wheel Controller.
        Opens a Modbus TCP connection to the Selector Wheel controller at `ip_address`, and reads the
        current _position, speed etc.
        Args:
            ip_address (str): IP Address of the controller to communicate with
        """
        #: (:obj:`ModbusTcpClient`): Client for communicating with the controller
        self._debug = debug
        
        self._time_step = 0.1
        
        self.connect(ip_address)
        
    def connect(self, ip_address=default_IP, port=default_port):
        self._client = ModbusTcpClient(ip_address, port=port)

        self.update_all()
        
    def disconnect(self):
        """Disconnect from the modbus server"""
        self._client.disconnect()
        
    @property
    def command_position(self):
        """int: Last commanded position of the Selector Wheel. One of 1-5."""
        return self._command_position

    @property
    def position(self):
        """int: Position of the Selector Wheel. One of 1-4."""
        return self._position

    @property
    def angle_error(self):
        """int: Position error of the Selector Wheel. Value is error in degrees x 100."""
        return self._angle_error

    @property
    def speed(self):
        """int: Speed of the Selector Wheel. Value is one of 1 (slowest) to 3 (fastest)."""
        return self._speed

    @property
    def angle(self):
        """float: Angle of the Selector Wheel in degrees."""
        return self._angle

    @property
    def angle_error(self):
        """float: Angle error of the Selector Wheel in degrees."""
        return self._angle_error

    @property
    def angle_tolerance(self):
        """float: Angle tolerance of the Selector Wheel in degrees before a move is needed."""
        return self._angle_tolerance
    
    @property
    def angle_offset(self):
        """float: Angle tolerance of the Selector Wheel in degrees before a move is needed."""
        return self._angle_offset

    @property
    def time(self):
        """int: Time taken for last commanded move. Value is the time take in milliseconds."""
        return self._time
    
    @property
    def pos_1(self):
        """int: Position of 1st selector position"""
        return self._pos_1

    @property
    def pos_2(self):
        """int: Position of 1st selector position"""
        return self._pos_2
    
    @property
    def pos_3(self):
        """int: Position of 1st selector position"""
        return self._pos_3
    
    @property
    def pos_4(self):
        """int: Position of 1st selector position"""
        return self._pos_4
    
    @property
    def resolver_turns(self):
        """int: Resolver turns"""
        return self._resolver_turns
    
    @property
    def resolver_position(self):
        """int: Resolver position"""
        return self._resolver_position
    
    @property
    def status(self):
        """int: Selector Wheel status"""
        return self._status
    
    def read_value(self, register):
        """Pick which read method to use based on the register number.
        
        The Galil controller uses 1xxx registers for ints and 2xxx registers for floats."""
        if register >= 2000:
            return self.read_float(register)
        else:
            return self.read_int(register)
        
    def write_value(self, register, value):
        """Pick which write method to use based on the register number.
        
        The Galil controller uses 1xxx registers for ints and 2xxx registers for floats."""
        if register >= 2000:
            return self.write_float(register, value)
        else:
            return self. write_int(register, value)
    
    def read_int(self, register):
        """Read a variable value from the Galil controller"""
        r = self._client.read_input_registers(register)
        if r.isError():
            raise RuntimeError(f"Could not read register {register}")
        
        return int(r.registers[0])
    
    def read_float(self, register):
        """Read a variable value from the Galil controller"""
        r = self._client.read_input_registers(register)
        if r.isError():
            raise RuntimeError(f"Could not read register {register}")
        
        decoder = BinaryPayloadDecoder.fromRegisters(r.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
        result = decoder.decode_32bit_float()
        return result
    
    def write_int(self, var_name, value):
        """Read a variable value from the Galil controller"""
        cmd = f'{var_name}={value}'
        if self._debug:
            print(f"Calling '{cmd}'")
        
        w = self._client.write_single_register(self._compos_addr, value, slave=1)
        if w.isError():
            raise RuntimeError("Could not set position on controller")
    
    def write_float(self, var_name, value):
        """Read a variable value from the Galil controller"""
        cmd = f'{var_name}={value}'
        if self._debug:
            print(f"Calling '{cmd}'")
        
        builder = BinaryPayloadBuilder(
            wordorder=Endian.BIG,
            byteorder=Endian.BIG
        )
        builder.add_32bit_float(tolerance)
        registers = builder.to_registers()
        w = self._client.write_registers(self._angle_tolerance_addr, registers, slave=1)
        if w.isError():
            raise RuntimeError("Could not set angle tolerance on controller")    

    def get_command_position(self):
        """Read the commanded position from the controller."""
        ret = self.read_value(self._compos_addr)
        self._command_position = int(ret)
        
        return self.command_position

    def get_position(self):
        """Read the current position from the controller."""
        ret = self.read_value(self._curpos_addr)
        self._position = int(ret)
        
        return self.position

    def get_pos_1(self):
        """Read pos_1 from the controller."""
        ret = self.read_value(self._pos_1_addr)
        self._pos_1 = int(ret)

        return self.pos_1

    def get_pos_2(self):
        """Read pos_2 from the controller."""
        ret = self.read_value(self._pos_2_addr)
        self._pos_2 = int(ret)

        return self.pos_2
    
    def get_pos_3(self):
        """Read pos_1 from the controller."""
        ret = self.read_value(self._pos_3_addr)
        self._pos_3 = int(ret)

        return self.pos_3

    def get_pos_4(self):
        """Read pos_4 from the controller."""
        ret = self.read_value(self._pos_4_addr)
        self._pos_4 = int(ret)

        return self.pos_4

    def get_status(self):
        """Read pos_1 from the controller."""
        ret = self.read_value(self._status_addr)
        self._status = int(ret)

        return self.status
    
    def get_speed(self):
        """Read speed from the controller."""
        ret = self.read_value(self._speed_addr)
        self._speed = int(ret)

        return self.speed

    def get_angle(self):
        """Read wheel angle from the controller."""
        ret = self.read_value(self._angle_addr)
        self._angle = ret

        return self.angle

    def get_angle_error(self):
        """Read wheel angle error from the controller."""
        ret = self.read_value(self._angle_error_addr)
        self._angle_error = ret

        return self.angle_error

    def get_angle_tolerance(self):
        """Read the angle tolerance from the controller."""
        ret = self.read_value(self._angle_tolerance_addr)
        self._angle_tolerance = ret

        return self.angle_tolerance
    
    def get_angle_offset(self):
        """Read the angle offset from the controller."""
        ret = self.read_value(self._angle_offset_addr)
        self._angle_offset = ret

        return self.angle_offset
    
    def get_time(self):
        """Read the time taken for the last movement from the controller."""
        ret = self.read_value(self._time_addr)
        self._time = ret

        return self.time

    def get_resolver_turns(self):
        """Read the resolver turn count from the controller."""
        ret = self.read_value(self._resolver_turns_addr)
        self._resolver_turns = int(ret)

        return self.resolver_turns

    def get_resolver_position(self):
        """Read pos_1 from the controller."""
        ret = self.read_value(self._resolver_position_addr)
        self._resolver_position = int(ret)

        return self.resolver_position
           
    def update(self, debug=False):
        """Update all the data from the selector."""
        self.get_command_position()
        self.get_position()
        self.get_speed()
        self.get_time()
        self.get_status()
        self.get_angle()
        self.get_angle_error()
        self.get_angle_tolerance()
        self.get_angle_offset()
        if debug:
            self.update_extra()
            
    def update_extra(self):
        """Get the extra status variables from the controller.
        
        These will only change when the wheel is rehomed."""
        self.get_pos_1()
        self.get_pos_2()
        self.get_pos_3()
        self.get_pos_4()
        self.get_resolver_turns()
        self.get_resolver_position()

    def update_all(self):
        """Get all the status variables from the controller"""
        self.update()
        self.update_extra()

    def set_speed(self, speed):
        """Set the speed of motion for the wheel.
        Args:
            speed (int): Speed setting. One of 1 (slowest), 2 or 3 (fastest). 1 and 2 are more reliable.
        """
        if speed not in range(1,4):
            raise ValueError("Speed must be an integer between 1 and 3")

        self.write_value(self._speed_var, int(speed))
        self._speed = self.get_speed()

    def set_position(self, position):
        """Set the _position for the wheel.
        !This will start motion to requested position at the current speed!
        Args:
            position (int): Position setting. One of 1, 2, 3, or 4.
        """
        if position not in range(1, 5):
            raise ValueError("Requested position must be an integer between 1 and 4")

        self.write_value(self._compos_addr, int(position))
        # Sleep to allow motion to start
        sleep(self._time_step/4)
        # Wait for motion to complete.
        while self.get_status():
            sleep(self._time_step/4)

        self.update()
        
    def set_angle_tolerance(self, tolerance):
        """Set the angle tolerance for corrections.
        
        Args:
            tolerance (float): angle tolerance in degrees"""
        if tolerance < 0.0:
            tolerance = abs(tolerance)

        self.write_value(self._angle_tolerance_addr, f"{tolerance:.3f}")
        self._angle_tolerance = self.get_angle_tolerance()

    def set_angle_offset(self, offset):
        """Set the angle offset from the nominal position that the wheel should go to.
        This allows the wheel to be jogged from the nominal positions - helpful in alignment,
        or for tweaking the angle of the polarizing grid.
        
        Small offsets in pointing may occur with offsets.
        
        Args:
            offset (float): angle offset in degrees"""
        self.write_value(self._angle_offset_addr, f"{offset:.3f}")
        self._angle_offset = self.get_angle_offset()
        
    def zero_angle_offset(self):
        """Reset the angle offset to zero"""

    def home(self):
        """Move the wheel to the home position, and then to position 1.
        Selector wheel controller automatically homes on power on."""
        self.write_value(self._compos_addr, 5)
        # Sleep to allow motion to start
        sleep(self._time_step/4)
        # Wait for motion to complete.
        while self.get_status():
            sleep(self._time_step/4)

        self.update_all()
