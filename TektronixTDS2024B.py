# Copyright 2010 Jim Bridgewater

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Python interface to the Tektronix TDS2024B oscilloscope

11/04/09 Jim Bridgewater (jwbwater at gmail dot com)
Adapted this from code written for the Keithley 2400. 

11/13/09 
Started developing this code under Linux.  The writes work fine,
but the reads never worked perfectly.  Switching to WinXP since
that's what the lab computer is running.

3/30/2010 Jim Bridgewater
Added read_immediate_measurement_value function for potentiometric
sensor measurements which require a large number of samples more
than precise timing between samples.

#################################################################
# The user functions defined in this module are:
#################################################################

acquire_samples(channel_list):
read_immediate_measurement_value(channel):
read_esr():
read_opc():
read_stb():
read_wfmpre():
set_acquire_mode(mode):
set_bandwidth_off(channel):
set_coupling_ac(channel):
set_coupling_dc(channel):
set_immediate_measurement_type(type):
set_seconds_per_division(seconds):
set_volts_per_division(channel,volts):
'''

#################################################################
# Import libraries
#################################################################
import sys, time, os, visa
from errors import Error

#################################################################
# Global Declarations
#################################################################
Debug = 0  # set to 1 to enable printing of error codes
end_of_line = "\n"
scope_resource_name = "USB::0x0699::0x036A::C041309::INSTR"

#################################################################
# Global Variables
#################################################################
oscilloscope = None

#################################################################
# Function definitions
#################################################################


# Single sequence scope acquisition
def acquire_samples(channel_list, samples = 2500):
  for channel in [1,2,3,4]:
    if channel in channel_list:
      write("select:ch" + str(channel) + " on")
    else:
      write("select:ch" + str(channel) + " off")
  write("dese 1")  # enable *opc in device event status enable register
  write("*ese 1")  # enable *opc in event status enable register
  write("*sre 0")  # no need to enable service requests
  write("acquire:stopafter sequence; state on")
  write("trigger force")
  while read_opc() == '0\n':
    time.sleep(0.2)
  write("data:width 1;start 1;stop " + str(samples) + ";encdg ascii")
  write("wfmpre:ch" + str(channel_list[0]) + ":xincr?")
  #write("wfmpre?")
  #preamble = read()
  #if Debug:
  #  print "preamble", preamble
  #x_factor = float(preamble.split("XINCR ")[1].split(";")[0])
  x_factor = float(read().split("XINCR ")[1])
  if Debug:
    print "x mult", x_factor
  time_data = []
  for data_point in range(samples):
    time_data.append(x_factor*data_point)
  data = [time_data]
  for channel in channel_list:
    write("data:source ch" + str(channel))
    write("curve?")
    data_strings = read().strip(":CURVE ,").split(",")
    write("wfmpre?")
    preamble = read()
    y_factor = float(preamble.split("YMULT ")[1].split(";")[0])
    y_offset = float(preamble.split("YOFF ")[1].split(";")[0])
    if Debug:
      print "y mult", y_factor
      print "y offset", y_offset   
    voltage_data = []
    for data_string in data_strings:
      voltage_data.append(y_factor*(int(data_string) - y_offset))
    data.append(voltage_data)
  return data


# read event status register
def read_esr():
  write("*esr?")
  return read()


# read identification string
def read_idn():
  write("*idn?")
  return read()


# read immediate measurement value
def read_immediate_measurement_value(channel_list):
  data = []
  for channel in channel_list:
    write("measurement:immed:source1 ch" + str(channel))
    write("measurement:immed:value?")
    data.append(read().split("VALUE ")[1])
  return data


# read operation complete bit from event status register
def read_opc():
  write("*opc?")
  return read()


# read status byte register
def read_stb():
  write("*stb?")
  return read()


# read waveform preamble
def read_wfmpre():
  write("wfmpre?")
  return read()


def set_acquire_mode(mode):
  write("acquire:mode " + mode)


def set_bandwidth_off(channel):
  write("ch" + str(channel) + ":bandwidth off")


def set_coupling_ac(channel):
  write("ch" + str(channel) + ":coupling ac")


def set_coupling_dc(channel):
  write("ch" + str(channel) + ":coupling dc")


def set_immediate_measurement_type(type):
  write("measurement:immed:type " + type)


def set_seconds_per_division(seconds):
  write("horizontal:main:scale " + str(seconds))


def set_volts_per_division(channel,volts):
  write("ch" + str(channel) + ":scale " + str(volts))


# This function writes command codes to the instrument. 
def write(command_code):
  global oscilloscope
  try:
    if oscilloscope == None:
      oscilloscope = visa.instrument(scope_resource_name)
    if Debug:
      print "write: " + command_code
    oscilloscope.write(command_code)
  except visa.VisaIOError:
    print "ERROR: Unable to open the USB communication link to the "\
    "Tektronix TDS2024B, make sure it is plugged in."


# This function reads the data stream returned by the instrument. 
def read():
  global oscilloscope
  try:
    if oscilloscope == None:
      oscilloscope = visa.instrument(scope_resource_name)
    data = oscilloscope.read()
    if Debug:
      print "read: " + data
    return data
  except visa.VisaIOError:
    print "ERROR: Unable to open the USB communication link to the "\
    "Tektronix TDS2024B, make sure it is plugged in."


# This function writes a command and reads the instrument's response.
def query(command):
  write(command)
  return read()
