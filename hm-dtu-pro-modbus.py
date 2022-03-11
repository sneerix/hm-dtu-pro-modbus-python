#!/usr/bin/python3

import sys
import time

# pip3 install pymodbus
from pymodbus.client.sync import ModbusTcpClient

# pip3 install influxdb (?)
from influxdb import InfluxDBClient

ModbusHost         = "192.168.X.X"
ModbusPort         = "502"

InfluxDBHost       = "192.168.X.X"
InfluxDBPort       = "8086"
InfluxDBLogin      = "LoGiN"
InfluxDBPassword   = "Pa$$W0rd"
InfluxDBDatabase   = "database_name"

HMInverterCount    = 2

def db_write(measurement_name, value):
  json_body = [
    {
      "measurement": measurement_name,
      "fields": {
        "value": value
      }
    }
  ]

  db_client.write_points(json_body)


def arr_of_word2string(array):
    string = ''
    for i in array:
        a,b = i.to_bytes(2,'big')
        string = string + chr(a) + chr(b)

    return string

def unsigned2signed(unsigned_value):
    signed_value = unsigned_value if unsigned_value < (1 << 16-1) else unsigned_value - (1 << 16)
    return signed_value

def read_registers(inv_nr):

  print("inverter number: ", inv_nr)

  offset_base = 0x1000
  offset_step = 0x28

  if modbus_client.connect():
    rr    = modbus_client.read_holding_registers(offset_base + offset_step*inv_nr, 20)
  else:
    print("problem reading registers")
    print(modbus_client.last_error())
    sys.exit(1)

  if rr:

    regs = rr.registers

    PVVoltage            = regs[4]/10
    PVCurrent            = regs[5]/100
    GridVoltage          = regs[6]/10
    GridFreq             = regs[7]/100
    PVPower              = regs[8]/10
    PVTodayProd          = regs[9]
    PVTotalProd1         = regs[10]*10
    PVTotalProd2         = regs[11]
    PVTotalProd          = PVTotalProd1 + PVTotalProd2
    Temp                 = unsigned2signed(regs[12]/10)
    OperatingStatus      = regs[13]
    AlarmCode            = regs[14]
    AlarmCount           = regs[15]
    LinkStatus           = regs[16]

    print("PVVoltage:       ", PVVoltage , "V")
    print("PVCurrent:       ", PVCurrent , "A")
    print("PVPower:         ", PVPower, "W")
    print("PVTodayProd:     ", PVTodayProd, "Wh")
    print("PVTotalProd:     ", PVTotalProd, "Wh")
    print("GridVoltage:     ", GridVoltage, "V")
    print("GridFreq:        ", GridFreq, "Hz")
    print("Temp:            ", Temp, "oC")
    print("OperatingStatus: ", OperatingStatus)
    print("AlarmCode:       ", AlarmCode)
    print("AlarmCount:      ", AlarmCount)
    print("LinkStatus:      ", LinkStatus)

    data_end_time = int(time.time() * 1000)

    measurement = "hoymiles_inverter_" + str(inv_nr)

    data = []
    data.append("{measurement} PVVoltage={PVVoltage},PVCurrent={PVCurrent},PVPower={PVPower},GridVoltage={GridVoltage},GridFreq={GridFreq},Temp={Temp},OperatingStatus={OperatingStatus} {timestamp}"
      .format(measurement=measurement,
      PVVoltage=PVVoltage,
      PVCurrent=PVCurrent,
      PVPower=PVPower,
      GridVoltage=GridVoltage,
      GridFreq=GridFreq,
      Temp=Temp,
      OperatingStatus=OperatingStatus,
      timestamp=data_end_time))

    db_client.write_points(data, time_precision='ms', batch_size=10000, protocol='line')

  else:
    print("got no meter regs")


print(time.strftime("%Y-%m-%d %H:%M:%S"))

modbus_client = ModbusTcpClient(host=ModbusHost, port=ModbusPort, auto_open=True, auto_close=True)

db_client     = InfluxDBClient(host=InfluxDBHost, port=InfluxDBPort, username=InfluxDBLogin, password=InfluxDBPassword, database=InfluxDBDatabase)

for inverter_nr in range(HMInverterCount):
  read_registers(inverter_nr)
  time.sleep(0.2)

