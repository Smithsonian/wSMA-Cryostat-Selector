#!/usr/bin/env python
import logging
import sys
import os
import time

import threading
import json

from retrying import retry
import systemd.daemon
import signal

from smax import SmaxRedisClient, SmaxConnectionError, SmaxKeyError, join, normalize_pair
from gclib import GclibError

from selector_interface import SelectorInterface as HardwareInterface

# Change these based on system setup
default_smax_config = os.path.expanduser("~smauser/wsma_config/smax_config.json")
default_config = os.path.expanduser("~smauser/wsma_config/cryostat/selector/selector_config.json")

# Change these lines per application
daemon_name = "selector_smax_daemon"

# add a logging level for status output
def add_logging_level(level_name, level_num, method_name=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `level_name` becomes an attribute of the `logging` module with the value
    `level_num`. `method_name` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `method_name` is not specified, `level_name.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present 

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not method_name:
        method_name = level_name.lower()

    if hasattr(logging, level_name):
       raise AttributeError('{} already defined in logging module'.format(level_name))
    if hasattr(logging, method_name):
       raise AttributeError('{} already defined in logging module'.format(method_name))
    if hasattr(logging.getLoggerClass(), method_name):
       raise AttributeError('{} already defined in logger class'.format(method_name))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(level_num, message, *args, **kwargs)

    logging.addLevelName(level_num, level_name)
    setattr(logging, level_name, level_num)
    setattr(logging.getLoggerClass(), method_name, logForLevel)
    setattr(logging, method_name, logToRoot)

try:
    add_logging_level('STATUS', logging.WARNING+5)
except AttributeError:
    pass

# Change between testing and production
logging_level = logging.INFO

logging.basicConfig(format='%(levelname)s - %(message)s', level=logging_level)

READY = 'READY=1'
STOPPING = 'STOPPING=1'

def _is_smaxconnectionerror(exception):
    return isinstance(exception, SmaxConnectionError)

def _is_gclibconnectionerror(exception):
    return isinstance(exception, GclibError)

class SelectorSmaxService:
    def __init__(self, config=default_config, smax_config=default_smax_config):
        """Service object initialization code"""
        self.logger = self._init_logger()
        
        # Configure SIGTERM behavior
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        # A list of control keys
        self.control_keys = None

        # Read the hardware and SMAX configuration
        self.read_config(config, smax_config)
        self.logger.info('Read Config File')

        # The SMAXRedisClient instance
        self.smax_client = None
        
        # The simulated hardware class
        self.hardware = None

        # Log that we managed to create the instance
        self.logger.info(f'{daemon_name} instance created')
        
        # A time to delay between loops
        self.delay = 1.0

    def _init_logger(self):
        logger = logging.getLogger(daemon_name)
        logger.setLevel(logging_level)
        file_handler = logging.FileHandler(f'{daemon_name.lower()}.log')
        file_handler.setLevel(logging_level)
        fileFormatter = logging.Formatter('%(asctime)s: %(levelname)s - %(message)s')
        fileFormatter.default_msec_format = '%s.%03d'
        file_handler.setFormatter(fileFormatter)
        logger.addHandler(file_handler)
        return logger
    
    def read_config(self, config, smax_config=None):
        """Read the configuration file."""
        # Read the file
        with open(config) as fp:
            self._config = json.load(fp)
            fp.close()
        
        # If smax_config is given, update the hardware specific config file with the smax_config
        if smax_config:    
            with open(smax_config) as fp:
                s_config = json.load(fp)
                fp.close()
            self.logger.debug("Got smax_config")
            self.logger.debug(s_config)
            if "smax_table" in self._config["smax_config"]:
                smax_root = s_config["smax_table"]
                self._config["smax_config"]["smax_table"] = ":".join([smax_root, self._config["smax_config"]["smax_table"]])
                del s_config["smax_table"]
            self._config["smax_config"].update(s_config)
        
        # parse the _config dictionary and set up values
        self.smax_server = self._config["smax_config"]["smax_server"]
        self.smax_port = self._config["smax_config"]["smax_port"]
        self.smax_db = self._config["smax_config"]["smax_db"]
        self.smax_table = self._config["smax_config"]["smax_table"]
        self.smax_key = self._config["smax_config"]["smax_key"]
        
        self.logger.info("SMAX Configuration:")
        self.logger.info(f"\tSMAX Server: {self.smax_server}")
        self.logger.info(f"\tSMAX Port  : {self.smax_port}")
        self.logger.info(f"\tSMAx DB    : {self.smax_db}")
        self.logger.info(f"\tSMAX Table : {self.smax_table}")
        self.logger.info(f"\tSMAX Key   : {self.smax_key}")
        
        
        self.control_keys = self._config["smax_config"]["smax_control_keys"]
        self.logger.info("Control keys:")
        for k in self.control_keys.keys():
            self.logger.info(f"\t {k} : {self.control_keys[k]}")
        
        self.logging_interval = self._config["logging_interval"]
        self.logger.info(f"Logging Interval {self.logging_interval}")

    def start(self):
        """Code to be run before the service's main loop"""
        # Start up code
        
        # Create the hardware interface
        self.hardware = HardwareInterface(config=self._config, logger=self.logger, parent=self)
        
        # Create the SMA-X interface
        #
        # There's no point to us starting without a SMA-X connection, so this call will
        # use retrying, and hang until we get a connection.
        self.connect_to_smax()
        
        try:
            self.connect_to_hardware()
            self.logger.status('Created hardware interface object')
        except Exception as e:
            self.logger.error(f'Hardware connection failed.')
            
        
        # Initialize the hardware
        self.initialize_hardware()

        # systemctl will wait until this notification is sent
        # Tell systemd that we are ready to run the service
        systemd.daemon.notify(READY)

        # Run the service's main loop
        self.run()
    
    @retry(wait_exponential_multiplier=1000, wait_exponential_max=30000, retry_on_exception=_is_gclibconnectionerror)
    def connect_to_hardware(self):
        """Create a connection to hardware.  Retry this if the connection fails"""
        try:
            self.hardware.connect_hardware()
            self.logger.status(f'Connected to hardware')
            self.smax_client.smax_share(join(self.table, self.key), 'comm_status', 'connection error')
            self.smax_client.smax_share(join(self.table, self.key), 'comm_error', repr(e))
        except GclibError as e:
            self.logger.error(f'Could not connect to hardware: {e}')
            self.smax_client.smax_share(join(self.table, self.key), 'comm_status', 'connection error')
            self.smax_client.smax_share(join(self.table, self.key), 'comm_error', repr(e))
            raise e
        
    
    def initialize_hardware(self):
        """Run this code to get initial values for the hardware from SMA-X, and to initialize the hardware"""
        
        initialize_config = self._config["smax_config"]["smax_init_keys"]
        
        init_kwargs = {}
        for smax_key, kw in initialize_config.items():
            try:
                value = self.smax_client.smax_pull(join(self.smax_table, self.smax_key), smax_key)
            except SmaxKeyError:
                continue
            init_kwargs[kw] = value
        
        self.hardware.initialize_hardware(init_kwargs)
        
    @retry(wait_exponential_multiplier=1000, wait_exponential_max=30000, retry_on_exception=_is_smaxconnectionerror)
    def connect_to_smax(self):
        """creates a connection to SMA-X that we have to close properly when the
        service terminates."""
        try:
            if self.smax_client is None:
                self.smax_client = SmaxRedisClient(redis_ip=self.smax_server, redis_port=self.smax_port, redis_db=self.smax_db, program_name=daemon_name, \
                                                    debug=logging_level==logging.DEBUG, logger=self.logger)
            else:
                self.smax_client.smax_connect_to(self.smax_server, self.smax_port, self.smax_db)

            self.logger.status(f'SMA-X client connected to {self.smax_server}:{self.smax_port} DB:{self.smax_db}')
        except SmaxConnectionError as e:
            self.logger.warning(f'Could not connect to {self.smax_server}:{self.smax_port} DB:{self.smax_db}')    
            raise e
        
        # Register pubsub channels specified in config["smax_config"]["control_keys"] to the 
        # callbacks specified in the config.
        for k in self.control_keys.keys():
            self.smax_client.smax_subscribe(join(self.smax_table, self.smax_key, k), callback=getattr(self.hardware, self.control_keys[k]))
            self.logger.debug(f'connected {getattr(self.hardware, self.control_keys[k])} to {join(self.smax_table, self.smax_key, k)}')
        self.logger.info('Subscribed to pubsub notifications')

    def run(self):
        """Run the main service loop"""
        
        # Launch the logging thread as a daemon so that it can be shut down quickly
        self.logging_thread = threading.Thread(target=self.logging_loop, daemon=True, name='Logging')
        self.logging_thread.start()
        
        self.logger.status("Started logging thread")
        
        try:
            while True:
                time.sleep(self.delay)

        except KeyboardInterrupt:
            # Monitor for SIGINT, which we've set as the terminate signal in the
            # .service file
            self.logger.status('SIGINT (keyboard interrupt) received...')
            self.stop()
            
    def logging_loop(self):
        """The loop that will run in the thread to carry out logging"""
        while True:
            self.logger.debug("tick")
            next_log_time = time.monotonic() + self.logging_interval
            try:
                self.smax_logging_action()
            except Exception as e:
                pass

            # Try to run on a regular schedule, but if smax_logging_action takes too long,
            # just wait logging_interval between finishing one smax_logging_action and starting next.
            curr_time = time.monotonic()
            if next_log_time > curr_time:
                time.sleep(next_log_time - curr_time)
            else:
                time.sleep(self.logging_interval)
                
        
    def smax_logging_action(self):
        """Run the code to write logging data to SMAX"""
        # If we've lost the connection, lets reconnect
        # This will hang until a connection happens - this doesn't
        # cost us anything, as we need an SMA-X connection to
        # to do anything with the hardware.
        # Gather data
        self.logger.debug("In logging action")
        
        if self.smax_client is None:
            self.logger.warning(f'Lost SMA-X connection to {self.smax_server}:{self.smax_port} DB:{self.smax_db}')
            self.connect_to_smax()
                
        logged_data = self.hardware.logging_action()

        self.logger.info(f"Received data for {len(logged_data)} keys.")    
        # write values to SMA-X
        # Retry if connection is missing
        try:
            for k in logged_data.keys():
                self.logger.debug(f"key in logged_data.keys(): {k}")
                table, key = normalize_pair(join(self.smax_table, self.smax_key), k)
                self.smax_client.smax_share(table, key, logged_data[k])
            self.logger.status(f'Wrote hardware data to SMAX ')
        except SmaxConnectionError:
            self.logger.warning(f'Lost SMA-X connection to {self.smax_server}:{self.smax_port} DB:{self.smax_db}')
            self.connect_to_smax()
            self.smax_logging_action()
            
    def _handle_sigterm(self, sig, frame):
        self.logger.info('SIGTERM received...')
        self.stop()

    def stop(self):
        """Clean up after the service's main loop"""
        # Tell systemd that we received the stop signal
        systemd.daemon.notify(STOPPING)

        self.logger.status('Cleaning up...')
        
        # Clean up the hardware
        self.logger.status('Disconnecting hardware...')
        self.hardware.disconnect_hardware()

        # Put the service's cleanup code here.
        if self.smax_client:
            self.smax_client.smax_unsubscribe()
            self.smax_client.smax_disconnect()
            self.logger.status('SMA-X client disconnected')
        else:
            self.logger.warning('SMA-X client not found, nothing to clean up')

        # Exit to finally stop the serivce
        sys.exit(0)


if __name__ == '__main__':
    # Do start up stuff
    service = SelectorSmaxService()
    service.start()
