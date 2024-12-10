import logging

from pyModbusTCP.client import ModbusClient

logging.basicConfig()
logging.getLogger('pyModbusTCP.client').setLevel(logging.DEBUG)

c = ModbusClient(host="10.0.0.10")

test = c.write_single_register(1, 0)
test = c.write_single_register(16, 0)