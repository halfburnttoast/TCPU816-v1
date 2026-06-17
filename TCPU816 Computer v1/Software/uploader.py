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

g_rate = 19200 
g_ser  = None
g_line_delay = 0.03
g_char_delay = 0.002

def main():

    # parse args
    parser = argparse.ArgumentParser(epilog = '''
        A tool to copy assembled ROM images into the TPC65's RAM at a given location.\n
        Interfaces with the TMON monitor to upload programs.
        ''')
    parser.add_argument("offset", help = "insert code into this hexadecimal address. (ex. 04D0)", type = str)
    parser.add_argument("romfile", help = "the assembled rom file to be loaded", type = str) 
    parser.add_argument("-r", action = "store_true", help = "run program after upload.")
    args = parser.parse_args()

    # decode args
    rom    = args.romfile
    offset = int(args.offset, 16)

    # open file
    try:
        f = open(rom, 'rb')
    except FileNotFoundError as e:
        print("File \'" + rom + "\' not found!")
        exit()

    # check if offset is within range
    if offset > 0xFFFF:
        print("Offset \'" + str(hex(offset)) + "\' out of range!")
        exit()

    # init serial 
    print("Connecting to serial device...")
    try:
        device = serial.tools.list_ports.comports()[0].device
        global g_ser
        g_ser = serial.Serial(device, g_rate)
    except IndexError:
        print("No available serial device detected!")
        exit()

    time.sleep(3)

    # set address
    print("Setting TPC program counter...")
    cmd = 'X ' + format(offset, 'x').upper()
    write_line(cmd)
    time.sleep(1)

    print("\nCopying rom file to TPC...", flush = True)
    while True:
        # read 16 bytes at a time
        buf = f.read(32)
        out = 'W '
        for i, b in enumerate(buf):
            out = out + '{:02X}'.format(buf[i]) + ' '
        write_line(out)
        if len(buf) < 32:
            break
        time.sleep(g_line_delay)

    print("\nDone!")

    if args.r:
        print("\nAutostarting program...")
        time.sleep(g_line_delay)
        cmd = 'X ' + format(offset, 'x').upper()
        write_line(cmd)
        time.sleep(g_line_delay * 2)
        cmd = 'R'
        write_line(cmd)
        time.sleep(g_line_delay)
        print("\nDone!")

    g_ser.close()

    

def write_line(string):
    s = string + '\r'
    for c in s:
        g_ser.write(str.encode(c))
        print('.', end = '', flush = True)
        time.sleep(g_char_delay)
    g_ser.flush()
    g_ser.reset_input_buffer()



if __name__ == '__main__':
    main()
