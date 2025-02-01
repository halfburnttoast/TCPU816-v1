#       
#  Written by HalfBurntToast
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.


#!/usr/bin/python3
import serial
import serial.tools.list_ports
import argparse
import time
import os
show_debug = True

g_rate = 115200 
g_ser  = None
g_MAXADDR   = 0x10000


def write_line(serial_device, string):
    s = string + '\r'
    if(show_debug):
        print(s)
    for c in s:
        serial_device.write(str.encode(c))
        time.sleep(0.05)
    serial_device.flush()
    serial_device.reset_input_buffer()
    time.sleep(0.20)


def main():

    # parse args
    parser = argparse.ArgumentParser(epilog = '''
        A tool to copy a romfile into an EEPROM.''')
    parser.add_argument("romfile", help = "the assembled rom file to be loaded", type = str) 
    args = parser.parse_args()

    # decode args
    rom = args.romfile

    # open file
    try:
        f = open(rom, 'rb')
    except FileNotFoundError as e:
        print("File \'" + rom + "\' not found!")
        exit()
    except Exception as e:
        print(f"Error: {e}")
        exit()

    # open serial channel
    print("Connecting to serial device...")
    try:
        device = serial.tools.list_ports.comports()[0].device
        global g_ser
        g_ser = serial.Serial(device, g_rate)
    except IndexError:
        print("No available serial device detected!")
        exit()
    except Exception as e:
        print(f"Error: {e}")
        exit()

    # open and send file contents 
    write_line(g_ser, "A 0")
    with open(rom, 'rb') as f:
        while True:
            buf = f.read(8)
            out = 'W '
            for i, b in enumerate(buf):
                out = out + '{:02X}'.format(buf[i]) + ' '
            write_line(g_ser, out)
            if len(buf) < 8:
                break

    print("\nWrite complete.")





if __name__ == '__main__':
    main()
