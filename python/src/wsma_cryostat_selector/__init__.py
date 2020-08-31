__version__ = '0.0.0'

from time import sleep
from pymodbus.client.sync import ModbusTcpClient

default_IP = "192.168.42.100"


class SelectorWheel(object):
    """Class for communicating with the wSMA Selector Wheel Controller.

    The SelectorWheel object wraps a pymodbus.ModbusTcpClient instance which
    communicates with the Selector Wheel Controller over TCP/IP.
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

    def __init__(self, ip_address=default_IP):
        """Create a SelectorWheel object for communication with one Selector Wheel Controller.

        Opens a Modbus TCP connection to the Selector Wheel controller at `ip_address`, and reads the
        current _position, speed etc.

        Args:
            ip_address (str): IP Address of the controller to communicate with
        """
        #: (:obj:`ModbusTcpClient`): Client for communicating with the controller
        self._client = ModbusTcpClient(ip_address)

        #: int: Current _position of the Selector Wheel
        self._position = self.get_position()

        #: int: Current speed setting of the Selector Wheel
        self._speed = self.get_speed()

        #: int: Current _position error of the Selector Wheel. Equal to the error in degrees x 100.
        self._delta = self.get_delta()

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
    def time(self):
        """int: Time taken for last commanded move. Value is the time take in milliseconds."""
        return self._time

    def get_position(self):
        """Read the current setpoint position from the controller.

        Returns:
            int: current setpoint position."""
        r = self._client.read_input_registers(self._setpoint_addr)
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

    def get_delta(self):
        """Read the current position error from the controller.

        Returns:
            int: current position error in degrees x 100."""
        r = self._client.read_input_registers(self._delta_addr)
        if r.isError():
            raise RuntimeError("Could not get current _position error")
        else:
            return r.registers[0]

    def get_time(self):
        """Read the time take for the last movement from the controller.

        Returns:
            int: time taken for the last move in milliseconds."""
        r = self._client.read_input_registers(self._time_addr)
        if r.isError():
            raise RuntimeError("Could not get last movement time")
        else:
            return r.registers[0]

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

        w = self._client.write_registers(self._setpoint_addr, position)
        if w.isError():
            raise RuntimeError("Could not set position on controller")

        # Sleep to allow motion to start
        sleep(self._time_step/4)
        # Wait for motion to complete.
        while self.get_status():
            sleep(self._time_step/4)

        self._position = self.get_position()
        self._delta = self.get_delta()
        self._time = self.get_time()

    def home(self):
        """Move the wheel to the home position, and then to position 1.

        Selector wheel controller automatically homes on power on."""
        w = self._client.write_registers(self._setpoint_addr, 5)
        if w.isError():
            raise RuntimeError("Could not request homing procedure")

        # Sleep to allow motion to start
        sleep(self._time_step/4)
        # Wait for motion to complete.
        while self.get_status():
            sleep(self._time_step/4)

        self._position = self.get_position()
        self._speed = self.get_speed()
        self._delta = self.get_delta()
        self._time = self.get_time()
