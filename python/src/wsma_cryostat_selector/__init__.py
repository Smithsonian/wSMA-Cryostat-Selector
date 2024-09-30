__version__ = '0.2.0'

from time import sleep

import gclib

default_IP = "192.168.42.100"


class Selector(object):
    """Class for communicating with the wSMA Selector Wheel Controller.
    The SelectorWheel object wraps a pymodbus.ModbusTcpClient instance which
    communicates with the Selector Wheel Controller over TCP/IP.
    """
    #: str: Galil firmware variable holding the commanded position
    _compos_var = 'A[0]'
    
    #: str: Galil firmware variable holding the current position, i.e. the _position of the wheel
    _curpos_var = 'A[1]'
    
    #: int: address of the controller's speed register.
    _speed_var = 'A[2]'

    #: int: address of the controller's return code register.
    _status_var = 'A[3]'

    #: int: address of the controller's time register.
    _time_var = 'A[4]'

    #: int: address of the controller's angle error register (angular error in degrees)
    _angle_var = 'A[5]'
    
    #: int: address of the controller's angle error register (angular error in degrees)
    _angle_error_var = 'A[6]'
    
    #: int: address of the controller's angle error register (angular error in degrees)
    _angle_tolerance_var = 'A[7]'
    
    #: int: address of the controller's position 1 setting
    _pos_1_var = 'POS[0]'
    
    #: int: address of the controller's position 2 setting
    _pos_2_var = 'POS[1]'
    
    #: int: address of the controller's position 3 setting
    _pos_3_var = 'POS[2]'
    
    #: int: address of the controller's position 4 setting
    _pos_4_var = 'POS[3]'
    
    #: int: address of the controller's resolver turns register
    _resolver_turns_var = 'R[0]'
    
    #: int: address of the controller's resolver position register
    _resolver_position_var = 'R[1]'

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
        
        self._client = gclib.py()
        
        self.connect(ip_address)
        
    def connect(self, ip_address=default_IP):
        
        try:
            self._client.GOpen(f"{ip_address} -s ALL")
        
            self.update_all()
        except gclib.GclibError as e:
            print(f"GCLib error: {str(e)}")
        
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
    
    def read_value(self, var_name):
        """Read a variable value from the Galil controller"""
        cmd = f'MG {var_name}'
        if self._debug:
            print(f"Calling '{cmd}'")
        try:
            ret = self._client.GCommand(cmd)
        except gclib.GclibError as e:
            raise RuntimeWarning('GCLib: Unknown variable')
        
        return float(ret)
    
    def write_value(self, var_name, value):
        """Read a variable value from the Galil controller"""
        cmd = f'{var_name}={value}'
        if self._debug:
            print(f"Calling '{cmd}'")
        try:
            ret = self._client.GCommand(cmd)
        except gclib.GclibError as e:
            raise RuntimeWarning(f'GCLib: Error writing value {e}')

    def get_command_position(self):
        """Read the commanded position from the controller."""
        ret = self.read_value(self._compos_var)
        self._command_position = int(ret)
        
        return self.command_position

    def get_position(self):
        """Read the current position from the controller."""
        ret = self.read_value(self._curpos_var)
        self._position = int(ret)
        
        return self.position

    def get_pos_1(self):
        """Read pos_1 from the controller."""
        ret = self.read_value(self._pos_1_var)
        self._pos_1 = int(ret)

        return self.pos_1

    def get_pos_2(self):
        """Read pos_2 from the controller."""
        ret = self.read_value(self._pos_2_var)
        self._pos_2 = int(ret)

        return self.pos_2
    
    def get_pos_3(self):
        """Read pos_1 from the controller."""
        ret = self.read_value(self._pos_3_var)
        self._pos_3 = int(ret)

        return self.pos_3

    def get_pos_4(self):
        """Read pos_4 from the controller."""
        ret = self.read_value(self._pos_4_var)
        self._pos_4 = int(ret)

        return self.pos_4

    def get_status(self):
        """Read pos_1 from the controller."""
        ret = self.read_value(self._status_var)
        self._status = int(ret)

        return self.status
    
    def get_speed(self):
        """Read speed from the controller."""
        ret = self.read_value(self._speed_var)
        self._speed = int(ret)

        return self.speed

    def get_angle(self):
        """Read wheel angle from the controller."""
        ret = self.read_value(self._angle_var)
        self._angle = ret

        return self.angle

    def get_angle_error(self):
        """Read wheel angle error from the controller."""
        ret = self.read_value(self._angle_error_var)
        self._angle_error = ret

        return self.angle_error

    def get_angle_tolerance(self):
        """Read the angle tolerance from the controller."""
        ret = self.read_value(self._angle_tolerance_var)
        self._angle_tolerance = ret

        return self.angle_tolerance
    
    def get_time(self):
        """Read the time taken for the last movement from the controller."""
        ret = self.read_value(self._time_var)
        self._time = ret

        return self.time

    def get_resolver_turns(self):
        """Read the resolver turn count from the controller."""
        ret = self.read_value(self._resolver_turns_var)
        self._resolver_turns = int(ret)

        return self.resolver_turns

    def get_resolver_position(self):
        """Read pos_1 from the controller."""
        ret = self.read_value(self._resolver_position_var)
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

        self.write_value(self._compos_var, int(position))
        sleep(self._time_step)
        self._client.GMotionComplete('A')

        self.update()
        
    def set_angle_tolerance(self, tolerance):
        """Set the angle tolerance for corrections.
        
        Args:
            tolerance (float): angle tolerance in degrees"""
        if tolerance < 0.0:
            tolerance = abs(tolerance)

        self.write_value(self._angle_tolerance_var, f"{tolerance:.3f}")
        self._angle_tolerance = self.get_angle_tolerance()

    def home(self):
        """Move the wheel to the home position, and then to position 1.
        Selector wheel controller automatically homes on power on."""
        self.write_value(self._compos_var, 5)
        sleep(self._time_step)
        self._client.GMotionComplete('A')
        sleep(self._time_step)

        self.update_all()
