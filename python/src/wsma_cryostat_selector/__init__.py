__version__ = '0.0.1'

from time import sleep
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

default_IP = "192.168.42.100"


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

    #: int: address of the controller's angle register (angle in degrees)
    _angle_addr = 2005
    
    #: int: address of the controller's angle error register (angular error in degrees)
    _angle_error_addr = 2006
    
    #: int: address of the controller's angle tolerance register (the allowed angular error in degrees)
    _angle_tolerance_addr = 2007
    
    #: int: address of the controller's resolver turns register
    _resolver_turns_addr = 1012
    
    #: int: address of the controller's resolver position register
    _resolver_position_addr = 2013
    
    _time_step = 0.25

    def __init__(self, ip_address=default_IP):
        """Create a SelectorWheel object for communication with one Selector Wheel Controller.
        Opens a Modbus TCP connection to the Selector Wheel controller at `ip_address`, and reads the
        current _position, speed etc.
        Args:
            ip_address (str): IP Address of the controller to communicate with
        """
        #: (:obj:`ModbusTcpClient`): Client for communicating with the controller
        self._client = ModbusTcpClient(ip_address)

        #: int: Current position of the Selector Wheel in degrees
        self._position = self.get_position()

        #: int: Current speed setting of the Selector Wheel
        self._speed = self.get_speed()

        #: float: Current angle the Selector Wheel in degrees.
        self._angle = self.get_angle()

        #: float: Current angle error of the Selector Wheel in degrees.
        self._angle_error = self.get_angle_error()
        
        #: float: Angle tolerance of the Selector Wheel in degrees before a move is needed.
        self._angle_tolerance = self.get_angle_tolerance()

        #: int: Last movement time in ms.
        self._time = self.get_time()

    @property
    def position(self):
        """int: Position of the Selector Wheel. One of 1-4."""
        return self._position

    @property
    def delta(self):
        """int: Position error of the Selector Wheel. Value is error in degrees x 100."""
        return self._delta

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
    def time(self):
        """int: Time taken for last commanded move. Value is the time take in milliseconds."""
        return self._time

    def get_command_position(self):
        """Read the commanded position from the controller.
        Returns:
            int: commanded position."""
        r = self._client.read_input_registers(self._compos_addr)
        if r.isError():
            raise RuntimeError("Could not get current position")
        else:
            return r.registers[0]

    def get_position(self):
        """Read the current position from the controller.
        Returns:
            int: current position."""
        r = self._client.read_input_registers(self._curpos_addr)
        if r.isError():
            raise RuntimeError("Could not get current position")
        else:
            return r.registers[0]

    def get_status(self):
        """Read the current status from the controller.
        Returns:
            int: current status. Either 1 for motion in progress or 0 for motion complete."""
        r = self._client.read_input_registers(self._retcode_addr)
        if r.isError():
            raise RuntimeError("Could not get current status")
        else:
            return r.registers[0]

    def get_speed(self):
        """Read the current speed setting from the controller.
        Returns:
            int: current speed setting."""
        r = self._client.read_input_registers(self._speed_addr)
        if r.isError():
            raise RuntimeError("Could not get current speed setting")
        else:
            return r.registers[0]
        
    def get_angle(self):
        """Read the current angle of the wheel from the controller.
        
        Returns:
            float: angle in degrees."""
        r = self._client.read_input_registers(self._angle_addr)
        if r.isError():
            raise RuntimeError("Could not get current angle")
        else:
            decoder = BinaryPayloadDecoder.fromRegisters(r.registers, byteorder=Endian.Big, wordorder=Endian.Big)
            result = decoder.decode_32bit_float()
            return result

    def get_angle_error(self):
        """Read the current angle error of the wheel from the controller.
        
        Returns:
            float: angle error in degrees."""
        r = self._client.read_input_registers(self._angle_error_addr)
        if r.isError():
            raise RuntimeError("Could not get current angle error")
        else:
            decoder = BinaryPayloadDecoder.fromRegisters(r.registers, byteorder=Endian.Big, wordorder=Endian.Big)
            result = decoder.decode_32bit_float()
            return result
        
    def get_angle_tolerance(self):
        """Read the current angle tolerance of the wheel from the controller.
        
        Returns:
            float: angle in degrees."""
        r = self._client.read_input_registers(self._angle_tolerance_addr)
        if r.isError():
            raise RuntimeError("Could not get current angle tolerance")
        else:
            decoder = BinaryPayloadDecoder.fromRegisters(r.registers, byteorder=Endian.Big, wordorder=Endian.Big)
            result = decoder.decode_32bit_float()
            return result
        
    def get_time(self):
        """Read the time take for the last movement from the controller.
        Returns:
            int: time taken for the last move in milliseconds."""
        r = self._client.read_input_registers(self._time_addr)
        if r.isError():
            raise RuntimeError("Could not get last movement time")
        else:
            return r.registers[0]

    def get_resolver_turns(self):
        """Read the current turn count of the resolver.
        Returns:
            int: resolver turn count"""
        r = self._client.read_input_registers(self._resolver_turns_addr)
        if r.isError():
            raise RuntimeError("Could not get current _position error")
        else:
            return r.registers[0]

    def get_resolver_position(self):
        """Read the current position of the resolver.
        Returns:
            int: current position of the resolver"""
        r = self._client.read_input_registers(self._resolver_position_addr)
        if r.isError():
            raise RuntimeError("Could not get current _position error")
        else:
            decoder = BinaryPayloadDecoder.fromRegisters(r.registers, byteorder=Endian.Big, wordorder=Endian.Big)
            result = decoder.decode_32bit_float()
            return result

    def set_speed(self, speed):
        """Set the speed of motion for the wheel.
        Args:
            speed (int): Speed setting. One of 1 (slowest), 2 or 3 (fastest). 1 and 2 are more reliable.
        """
        if speed not in range(1,4):
            raise ValueError("Speed must be an integer between 1 and 3")

        w = self._client.write_registers(self._speed_addr, speed)
        if w.isError():
            raise RuntimeError("Could not set speed on controller")
        else:
            self._speed = self.get_speed()

    def set_position(self, position):
        """Set the _position for the wheel.
        !This will start motion to requested position at the current speed!
        Args:
            position (int): Position setting. One of 1, 2, 3, or 4.
        """
        if position not in range(1, 5):
            raise ValueError("Requested position must be an integer between 1 and 4")

        w = self._client.write_registers(self._compos_addr, position)
        if w.isError():
            raise RuntimeError("Could not set position on controller")

        # Sleep to allow motion to start
        sleep(self._time_step/4)
        # Wait for motion to complete.
        while self.get_status():
            sleep(self._time_step/4)

        self.update_all()

    def home(self):
        """Move the wheel to the home position, and then to position 1.
        Selector wheel controller automatically homes on power on."""
        w = self._client.write_registers(self._compos_addr, 5)
        if w.isError():
            raise RuntimeError("Could not request homing procedure")

        # Sleep to allow motion to start
        sleep(self._time_step/4)
        # Wait for motion to complete.
        while self.get_status():
            sleep(self._time_step/4)

        self.update_all()
        
    def update_all(self):
        """Get all status variables from controller."""
        self.get_command_position()
        self.get_position()
        self.get_speed()
        self.get_angle()
        self.get_angle_error()
        self.get_angle_tolerance()
        self.get_time()
        self.get_resolver_turns()
        self.get_resolver_position()


class DummySelector(Selector):
    """A dummy selector wheel that just stores information without attempting
    any communication, for testing purposes"""
    def __init__(self, ip_address="0.0.0.0"):
        """Create a DummySelector object for testing purposes.
        Args:
            ip_address (str): IP Address of the controller to communicate with
        """
        self._position = 1
        self._speed = 1
        self._delta = 42
        self._time = 35

    def get_position(self):
        """Read the current setpoint position from self._position
        Returns:
            int: current setpoint position."""
        return self._position

    def get_speed(self):
        """Read the current speed setting from self._speed
        Returns:
            int: current speed setting."""
        return self._speed

    def get_status(self):
        """Read the current status from the controller. Dummy version is always 0.
        Returns:
            int: current status. Either 1 for motion in progress or 0 for motion complete."""
        return 0

    def get_delta(self):
        """Read the current position error from self._delta.
        Returns:
            int: current position error in degrees x 100."""
        return self._delta

    def get_time(self):
        """Read the time take for the last movement from self._time.
        Returns:
            int: time taken for the last move in milliseconds."""
        return self._time

    def set_position(self, position):
        """Set the _position for the wheel.
        Dummy version changes the position and increments _delta by the speed
        Args:
            position (int): Position setting. One of 1, 2, 3, or 4.
        """
        if position in range(1,5):
            self._position = position
            self._delta = self._delta + self._speed
        else:
            raise ValueError("Illegal position {} passed to Selector.set_position()".format(position))

    def set_speed(self, speed):
        """Set the speed of motion for the wheel.
        Args:
            speed (int): Speed setting. One of 1 (slowest), 2 or 3 (fastest). 1 and 2 are more reliable.
        """
        if speed in range(1,4):
            self._speed = speed
        else:
            raise ValueError("Illegal speed {} passed to Selector.set_speed()".format(speed))

    def home(self):
        """Move the wheel to the home position, and then to position 1.
        Also sets speed to 1.
        Dummy version sets position to 1, speed to 1 and resets delta
        Selector wheel controller automatically homes on power on."""
        self._position = 1
        self._speed = 1
        self._delta = 42

