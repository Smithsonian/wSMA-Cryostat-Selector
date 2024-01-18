import logging
import os
import sys
import time
import datetime
import json

import systemd.daemon

import wsma_cryostat_selector

default_selector_IP = "selector-p1.proto1.lan"
default_port = 1
default_timeout = 10

default_config = "/home/smauser/wsma_config/cryostat/selector/selector_config.json"
default_smax_config = "/home/smauser/wsma_config/smax_config.json"

READY = 'READY=1'
STOPPING = 'STOPPING=1'

from smax import SmaxRedisClient

class SelectorSmaxService:
    def __init__(self, config=default_config, smax_config=default_smax_config):
        """Service object initialization code"""
        self.logger = self._init_logger()
        
        self._debug = False
        
        self.read_config(config, smax_config)

        # Selector object
        self.selector = None
        
        self.create_selector()
        
        # The SMAXRedisClient instance
        self.smax_client = None
        
        self._smax_meta = None
        
        # Log that we managed to create the instance
        self.logger.info('Selector-SMAX-Daemon instance created')
        
    def read_config(self, config, smax_config=None):
        """Read the configuration file."""
        # Read the file
        with open(config) as fp:
            self._config = json.load(fp)
            fp.close()
        
        # If smax_config is given, update the selector specific config file with the smax_config
        if smax_config:    
            with open(smax_config) as fp:
                s_config = json.load(fp)
                fp.close()
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
        self.smax_position_control_key = self._config["smax_config"]["smax_position_control_key"]
        self.smax_speed_control_key = self._config["smax_config"]["smax_speed_control_key"]
        
        self.logging_interval = self._config["logging_interval"]
        
    def create_selector(self):
        """Read selector configuration, and try to connect to it."""
        self._selector_ip = self._config["selector"]["ip_address"]
        self._selector_port = self._config["selector"]["port"]
        self._selector_data = self._config["selector"]["logged_data"]
        if self._config["selector"]["debug"]:
            self._selector_data.update(self._config["selector"]["debug_data"])
            self._debug = True
        
        try:
            self.selector = wsma_cryostat_selector.Selector(self._selector_ip)
            self.logger.info(f"Connected to selector at {self._selector_ip}:{self._selector_port}")
        except Exception as e:
            self.logger.warning(f'First attempt at connecting to selector failed with exception:\n {e.__str__()}\nRetrying...')
            try:
                self.selector = wsma_cryostat_selector.Selector(self._selector_ip)
                self.logger.info(f"Connected to selector at {self._selector_ip}:{self._selector_port}")
            except Exception as e:
                self.logger.error(f"Second attempt at connecting to selector failed with exception:\n {e.__str__()}")
        
    def _init_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        stdout_handler = logging.StreamHandler()
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(logging.Formatter('%(levelname)8s | %(message)s'))
        logger.addHandler(stdout_handler)
        return logger

    def start(self):
        """Code to be run before the service's main loop"""
        # Start up code

        # This snippet creates a connection to SMA-X that we have to close properly when the
        # service terminates
        if self.smax_client is None:
            self.smax_client = SmaxRedisClient(redis_ip=self.smax_server, redis_port=self.smax_port, redis_db=self.smax_db, program_name="example_smax_daemon")
        else:
            self.smax_client.smax_connect_to(self.smax_server, self.smax_port, self.smax_db)
        
        self.logger.info(f'SMA-X client connected to {self.smax_server}:{self.smax_port} DB:{self.smax_db}')
        
        # Get initial values and push to SMA-X
        self.smax_logging_action()
        
        # Push units metadata to SMA-X
        self.smax_set_units()
        
        # Set default values for pubsub channels
        try:
            self.smax_client.smax_pull(":".join([self.smax_table, self.smax_key]), self.smax_position_control_key)
        except:
            self.smax_client.smax_share(":".join([self.smax_table, self.smax_key]), self.smax_position_control_key, self._config["selector"]["default_position"])
            self.logger.info(f'Set initial position for selector to {self._config["selector"]["default_position"]}')

        try:
            self.smax_client.smax_pull(self.smax_table, self.smax_speed_control_key)
        except:
            self.smax_client.smax_share(self.smax_table, self.smax_speed_control_key, self._config["selector"]["default_speed"])
            self.logger.info(f'Set initial speed for selector to {self._config["selector"]["default_speed"]}')

        # Register pubsub channels
        self.smax_client.smax_subscribe(":".join([self.smax_table, self.smax_key, self.smax_position_control_key]), self.selector_position_control_callback)
        self.smax_client.smax_subscribe(":".join([self.smax_table, self.smax_key, self.smax_speed_control_key]), self.selector_speed_control_callback)
        self.logger.info('Subscribed to selector control pubsub notifications')

        # Set up the time for the next logging action
        self._next_log_time = time.monotonic() + self.logging_interval

        # systemctl will wait until this notification is sent
        # Tell systemd that we are ready to run the service
        systemd.daemon.notify(READY)

        # Run the service's main loop
        self.run()
        
    def smax_set_units(self):
        """Write units to smax - once only."""
        self._smax_meta = {"units":{}}
        for d in self._config["selector"]["logged_data"].keys():
            data = self._config["selector"]["logged_data"][d]
            unit = None
            if "units" in data.keys():
                unit = data["units"]
            self._smax_meta["units"][d] = unit
        if self._debug:
            for d in self._config["selector"]["logged_data"].keys():
                data = self._config["selector"]["logged_data"][d]
                unit = None
                if "units" in data.keys():
                    unit = data["units"]
                self._smax_meta["units"][d] = unit
        
        for d in self._smax_meta["units"]:
            self.smax_client.smax_push_meta("units", f"{self.smax_table}:{self.smax_key}:{d}", self._smax_meta["units"][d])
        self.logger.info("Wrote selector metadata to SMAX")

    def run(self):
        """Run the main service loop"""
        try:
            while True:
                # Put the service's regular activities here
                self.smax_logging_action()
                time.sleep(self.logging_interval)

        except KeyboardInterrupt:
            # Monitor for SIGINT, which we've set as the terminate signal in the
            # .service file
            self.logger.warning('SIGINT (keyboard interrupt) received...')
            self.stop()

    def smax_logging_action(self):
        """Run the code to write logging data to SMAX"""
        # Gather data
        logged_data = {}
        
        try:
            self.selector.update(self._debug)
            self.logger.info("Got data from selector.")
            logged_data['comms_status'] = 'good'
        except Exception as e:
            self.logger.warning(f"Failed to get update from selector with exception:\n{e.__str__()}\nRetrying.")
            try:
                time.sleep(0.5)
                self.selector.update(self._debug)
                self.logger.info("Got data from selector.")
                logged_data['comms_status'] = 'good'
            except Exception as e:
                self.logger.error(f"Failed to get update from selector with exception:\n{e.__str__()}")
                logged_data['comms_status'] = 'stale'
            
        # Read the values from the compressor
        for data in self._selector_data.keys():
            reading = self.selector.__getattribute__(data)
            logged_data[data] = reading
            self.logger.info(f'Got data for selector {data}: {reading:.3f}')
            
        # write values to SMAX
        for data in logged_data.keys():
            self.smax_client.smax_share(f"{self.smax_table}:{self.smax_key}", data, logged_data[data])
        self.logger.info(f'Wrote selector data to SMAX ')
        
        
    def selector_position_control_callback(self, message):
        """Run on a pubsub notification to smax_table:smax_position_control_key"""
        date = datetime.datetime.utcfromtimestamp(message.date)
        self.logger.info(f'Received PubSub notification for {message.smaxname} from {message.origin} with data {message.data} at {date}')
        
        if message.data:
            position = int(message.data)
            try:
                self.selector.set_position(position)
                self.logger.info(f'Set selector position to {position}.')
            except Exception as e:
                self.logger.warning(f'Failed to set selector position with exception:\n{e.__str__()}\nRetrying...')
                try:
                    self.selector.set_position(position)
                    self.logger.info(f'Set selector position to {position}.')
                except Exception as e:
                    self.logger.error(f'Failed to set selector position with exception:\n{e.__str__()}')
            
            
    def selector_speed_control_callback(self, message):
        """Run on a pubsub notification to smax_table:smax_speed_control_key"""
        date = datetime.datetime.utcfromtimestamp(message.date)
        self.logger.info(f'Received PubSub notification for {message.smaxname} from {message.origin} with data {message.data} at {date}')
        
        if message.data:
            try:
                speed = int(message.data)
                self.selector.set_speed(speed)
                self.logger.info(f'Set selector speed to {speed}')
            except Exception as e:
                self.logger.warning(f'Failed to set selector speed with exception:\n{e.__str__()}\nRetrying...')
                try:
                    speed = int(message.data)
                    self.selector.set_speed(speed)
                    self.logger.info(f'Set selector speed to {speed}')
                except Exception as e:
                    self.logger.error(f'Failed to set selector speed with exception:\n{e.__str__()}\n')

    def stop(self):
        """Clean up after the service's main loop"""
        # Tell systemd that we received the stop signal
        systemd.daemon.notify(STOPPING)

        # Put the service's cleanup code here.
        self.logger.info('Cleaning up...')
        if self.smax_client:
            self.smax_client.smax_unsubscribe()
            self.smax_client.smax_disconnect()
            self.logger.info('SMA-X client disconnected')
        else:
            self.logger.error('SMA-X client not found, nothing to clean up')
            
        if self.selector:
            self.selector.disconnect()
        # Exit to finally stop the serivce
        sys.exit(0)


if __name__ == '__main__':
    # Do start up stuff
    args = sys.argv[1:]
    service = SelectorSmaxService(*args)
    service.start()
