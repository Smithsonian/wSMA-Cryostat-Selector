import sys
#import time
#import readline
#import traceback

from pymodbus.client.sync import ModbusTcpClient

IP1="192.168.42.100"
client = ModbusTcpClient(IP1)


setpoint_addr = 1000
speed_addr = 1002
retcode_addr = 1003
time_addr = 1004
delta_addr = 1005


speed = 1
setpoint = 2


w = client.write_registers(speed_addr, speed)
w = client.write_registers(setpoint_addr, setpoint)
if w.isError():
    print(f"Error writing: {w}")
else:
    print(f"Successfully wrote values.")

#time.sleep(5) #delay might be based on speed.  right now, it isn't.

r = client.read_input_registers(delta_addr, 1)
if r.isError():
    print(f"Error reading: {r}")
else:
    print(f"Read resolver position delta (100x degrees): {r.registers}")

r = client.read_input_registers(retcode_addr, 1)
if r.isError():
    print(f"Error reading return code: {r}")
else:
    print(f"Read return code: {r.registers}")

r = client.read_input_registers(time_addr, 1)
if r.isError():
    print(f"Error reading elapsed time: {r}")
else:
    print(f"Read movement time (ms): {r.registers}")


