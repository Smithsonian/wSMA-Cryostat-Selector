__version__ = '0.0.0'

from time import sleep
import struct
import socket
from retrying import retry

from umodbus import conf
from umodbus.client import tcp

#from pymodbus.client.sync import ModbusTcpClient

default_IP = "192.168.42.100"
default_port = 502
default_timeout = 10

class Selector(object):
    """Class for communicating with the wSMA Selector Wheel Controller.

    The SelectorWheel object wraps a TCP/IP socket instance which
    communicates with the Selector Wheel Controller via umodbus.
    """
    #: int: address of the controller's setpoint register, i.e. the _position of the wheel.
    _setpoint_addr = 1000

    #: int: address of the controller's speed register.
    _speed_addr = 1002

    #: int: address of the controller's return code register.
    _retcode_addr = 1003

    #: int: address of the controller's time register.
    _time_addr = 1004

    #: int: address of the controller's _position error register.
    _delta_addr = 1005

    _time_step = 0.25

    def __init__(self, ip_address=default_IP, port=default_port, keep_alive=False, timeout=default_timeout):
        """Create a SelectorWheel object for communication with one Selector Wheel Controller.

        Opens a TCP socket connection to the Selector Wheel's Modbus controller at `ip_address`:`port`, and reads the
        current position, speed etc. using umodbus.

        Args:
            ip_address (str): IP Address of the controller to communicate with.
            port (int): Port number of the compressor's modbus server.
            keep_alive(bool): Keep the socket open or not
            timeout (float): Timeout for the socket connection in seconds.
        """
        #: str: IP address of compressor.
        self._ip_address = ip_address
        #: int: port of compressor's modbus server
        self._port = port
        #: bool: whether to keep the socket open
        self._keep_alive = keep_alive
        #: int: timeout for socket in seconds
        self._timeout = timeout

        #: bool: did the last attempt to update values fail
        self._stale = True

        #: (:obj:`socket.socket`): Client for communicating with the controller or None
        self._socket = None
        if self._keep_alive:
            self._connect()

        #: int: Current _position of the Selector Wheel
        self._position = self.get_position()

        #: int: Current speed setting of the Selector Wheel
        self._speed = self.get_speed()

        #: int: Current _position error of the Selector Wheel. Equal to the error in degrees x 100.
        self._delta = self.get_delta()

        #: int: Last movement time in ms.
        self._time = self.get_time()

    def _connect(self):
        """Connect a socket to the compressor's modbus port"""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self._timeout)
        self.__connect()

    @retry(stop_max_delay=10000, wait_random_min=500, wait_random_max=2000)
    def __connect(self):
        self._socket.connect((self._ip_address, self._port))

    def _disconnect(self):
        """Close the socket to the compressor"""
        self._socket.close()
        self._socket = None

    @retry(stop_max_delay=10000, wait_random_min=500, wait_random_max=2000)
    def __read_input_registers(self, addr, count=1, slave_id=1):
        """Private method to retry reading registers several times"""
        req = tcp.read_input_registers(slave_id=slave_id, starting_address=addr, quantity=count)
        try:
            resp = tcp.send_message(req, self._socket)
        except socket.timeout:
            self._connect()
            resp = tcp.send_message(req, self._socket)
        return resp


    def _read_input_registers(self, addr, count=1, slave_id=1):
        """Open a connection to the compressor, and send a modbus read request and return
        the int_list as an array of longs.

        Args:
            addr (int): Address of first Modbus register to read.
            count (int): Number of adjacent Modbus registers to read.
            slave_id (int): Modbus Slave ID. Defaults to 1.

        Returns:
            int or list(int): Contents of registers as 16 bit integers."""
        if not self._socket:
            self._connect()

        resp = self.__read_input_registers(addr, count=count, slave_id=slave_id)

        if not self._keep_alive:
            self._disconnect()

        return resp

    @retry(stop_max_delay=10000, wait_random_min=500, wait_random_max=2000)
    def __write_registers(self, addr, value, slave_id=1):
        """Private method to retry reading registers several times"""
        req = tcp.write_single_register(slave_id=slave_id, starting_address=addr, value=value)
        try:
            resp = tcp.send_message(req, self._socket)
        except socket.timeout:
            self._connect()
            resp = tcp.send_message(req, self._socket)
        return resp

    def _write_registers(self, addr, value, slave_id=1):
        """Open a connection to the compressor, and send a modbus write request.

        Args:
            addr (int): Address of first Modbus register to read.
            value (int): Value to write to the register.
            slave_id (int): Modbus Slave ID. Defaults to 1.

        Returns:
            int or list(int): byte array from compressor."""
        if not self._socket:
            self._connect()
        resp = self.__write_registers(addr, value, slave_id=slave_id)

        if not self._keep_alive:
            self._disconnect()

        return resp

    @property
    def position(self):
        """int: Position of the Selector Wheel. One of 1-4."""
        if self._stale:
            self._position = self.get_position()
        return self._position

    @property
    def delta(self):
        """int: Position error of the Selector Wheel. Value is error in degrees x 100."""
        if self._stale:
            self._delta = self.get_delta()
        return self._delta

    @property
    def speed(self):
        """int: Speed of the Selector Wheel. Value is one of 1 (slowest) to 3 (fastest)."""
        return self._speed

    @property
    def time(self):
        """int: Time taken for last commanded move. Value is the time take in milliseconds."""
        return self._time

    def get_position(self):
        """Read the current setpoint position from the controller.

        Returns:
            int: current setpoint position."""
        try:
            r = self._read_input_registers(self._setpoint_addr)
            if r.isError():
                self._stale = True
                raise RuntimeError("Could not get current position")
            else:
                self._stale = False
                return r.registers[0]
        except socket.timeout:
            self._stale = True

    def get_status(self):
        """Read the current status from the controller.

        Returns:
            int: current status. Either 1 for motion in progress or 0 for motion complete."""
        try:
            r = self._read_input_registers(self._retcode_addr)
            if r.isError():
                self._stale = True
                raise RuntimeError("Could not get current status")
            else:
                self._stale = False
                return r.registers[0]
        except socket.timeout:
            self._stale = True

    def get_speed(self):
        """Read the current speed setting from the controller.

        Returns:
            int: current speed setting."""
        try:
            r = self._read_input_registers(self._speed_addr)
            if r.isError():
                self._stale = True
                raise RuntimeError("Could not get current speed setting")
            else:
                self._stale = False
                return r.registers[0]
        except socket.timeout:
            self._stale = True

    def get_delta(self):
        """Read the current position error from the controller.

        Returns:
            int: current position error in degrees x 100."""
        try:
            r = self._read_input_registers(self._delta_addr)
            if r.isError():
                self._stale = True
                raise RuntimeError("Could not get current _position error")
            else:
                self._stale = False
                return r.registers[0]
        except socket.timeout:
            self._stale = True

    def get_time(self):
        """Read the time take for the last movement from the controller.

        Returns:
            int: time taken for the last move in milliseconds."""
        try:
            r = self._read_input_registers(self._time_addr)
            if r.isError():
                self._stale = True
                raise RuntimeError("Could not get last movement time")
            else:
                self._stale = False
                return r.registers[0]
        except socket.timeout:
            self._stale = True

    def set_speed(self, speed):
        """Set the speed of motion for the wheel.

        Args:
            speed (int): Speed setting. One of 1 (slowest), 2 or 3 (fastest). 1 and 2 are more reliable.
        """
        if speed not in range(1,4):
            raise ValueError("Speed must be an integer between 1 and 3")

        try:
            w = self._write_registers(self._speed_addr, speed)
            if w.isError():
                raise RuntimeError("Could not set speed on controller")
            else:
                self._speed = self.get_speed()
        except socket.timeout:
            raise RuntimeWarning("Timed out trying to set speed")

    def set_position(self, position):
        """Set the _position for the wheel.

        !This will start motion to requested position at the current speed!

        Args:
            position (int): Position setting. One of 1, 2, 3, or 4.
        """
        if position not in range(1, 5):
            raise ValueError("Requested position must be an integer between 1 and 4")

        try:
            w = self._write_registers(self._setpoint_addr, position)
            if w.isError():
                raise RuntimeError("Could not set position on controller")

            # Sleep to allow motion to start
            sleep(self._time_step/4)
            # Wait for motion to complete.
            while self.get_status():
                sleep(self._time_step/4)
        except socket.timeout:
            raise RuntimeWarning("Timed out trying to set position")

        self._position = self.get_position()
        self._delta = self.get_delta()
        self._time = self.get_time()

    def home(self):
        """Move the wheel to the home position, and then to position 1.

        Selector wheel controller automatically homes on power on."""
        try:
            w = self._write_registers(self._setpoint_addr, 5)
            if w.isError():
                raise RuntimeError("Could not request homing procedure")

            # Sleep to allow motion to start
            sleep(self._time_step/4)
            # Wait for motion to complete.
            while self.get_status():
                sleep(self._time_step/4)
        except socket.timout:
            raise RuntimeWarning("Timed out trying to home")

        self._position = self.get_position()
        self._speed = self.get_speed()
        self._delta = self.get_delta()
        self._time = self.get_time()


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
            raise ValueError("Illegal speed {} passed to Selector.set_speed()".format(position))

    def home(self):
        """Move the wheel to the home position, and then to position 1.
        Also sets speed to 1.

        Dummy version sets position to 1, speed to 1 and resets delta

        Selector wheel controller automatically homes on power on."""
        self._position = 1
        self._speed = 1
        self._delta = 42
