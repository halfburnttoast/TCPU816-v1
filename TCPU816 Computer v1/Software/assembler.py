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
import re
import io
import logging
import argparse

log_level = logging.DEBUG
lfmt = "%(levelname)s [%(funcName)s]: %(message)s"
logging.basicConfig(level=log_level, format=lfmt)

opcode_matrix = {
    'nop'   : {'code' : 0x00, 'args': []},

    # External IO
    'edo'   : {'code' : 0x01, 'args': [2]},
    'edi'   : {'code' : 0x02, 'args': [2]},

    # Load register
    'ldai'  : {'code' : 0x03, 'args': [1]},
    'ldxi'  : {'code' : 0x04, 'args': [1]},
    'ldyi'  : {'code' : 0x05, 'args': [1]},
    'ldar'  : {'code' : 0x06, 'args': [2]},
    'ldarx' : {'code' : 0x07, 'args': [2]},
    'ldary' : {'code' : 0x08, 'args': [2]},
    'ldari' : {'code' : 0x09, 'args': [2]},

    # Store register
    'star'   : {'code' : 0x0A, 'args': [2]},
    'stxr'   : {'code' : 0x0B, 'args': [2]},
    'styr'   : {'code' : 0x0C, 'args': [2]},
    'starx'  : {'code' : 0x0D, 'args': [2]},
    'stary'  : {'code' : 0x0E, 'args': [2]},
    'stari'  : {'code' : 0x0F, 'args': [2]},

    # increment
    'ina'  : {'code' : 0x10, 'args': []},
    'inx'  : {'code' : 0x11, 'args': []},
    'iny'  : {'code' : 0x12, 'args': []},

    # Deincrement
    'dea'  : {'code' : 0x13, 'args': []},
    'dex'  : {'code' : 0x14, 'args': []},
    'dey'  : {'code' : 0x15, 'args': []},    

    # Transfer
    'tax'   : {'code' : 0x16, 'args': []},
    'txa'   : {'code' : 0x17, 'args': []},
    'tya'   : {'code' : 0x18, 'args': []},
    'tay'   : {'code' : 0x19, 'args': []},
    'txy'   : {'code' : 0x1A, 'args': []},
    'tyx'   : {'code' : 0x1B, 'args': []},
    'tsa'   : {'code' : 0x1C, 'args': []},
    'tas'   : {'code' : 0x1D, 'args': []},

    # Carry flag
    'sec'   : {'code' : 0x1E, 'args': []},
    'clc'   : {'code' : 0x1F, 'args': []},

    # ALU
    'addi'  : {'code' : 0x20, 'args': [1]},
    'addr'  : {'code' : 0x21, 'args': [2]},
    'addx'  : {'code' : 0x22, 'args': []},
    'addy'  : {'code' : 0x23, 'args': []},
    'subi'  : {'code' : 0x24, 'args': [1]},
    'subr'  : {'code' : 0x25, 'args': [2]},
    'subx'  : {'code' : 0x26, 'args': []},
    'suby'  : {'code' : 0x27, 'args': []},
    'nandi' : {'code' : 0x28, 'args': [1]},
    'nandr' : {'code' : 0x29, 'args': [2]},
    'nandx' : {'code' : 0x2A, 'args': []},
    'nandy' : {'code' : 0x2B, 'args': []},
    'asr'   : {'code' : 0x2C, 'args': []},
    'asr2'  : {'code' : 0x2D, 'args': []},
    'asr4'  : {'code' : 0x2E, 'args': []},
    'andi'  : {'code' : 0x2F, 'args': [1]},
    'ori'   : {'code' : 0x30, 'args': [1]},
    'nota'  : {'code' : 0x31, 'args': []},
    'xori'  : {'code' : 0x32, 'args': [1]},


    # Jmp
    'jmp'   : {'code' : 0x33, 'args': [2]},
    'jeq'   : {'code' : 0x34, 'args': [2]},
    'jcs'   : {'code' : 0x35, 'args': [2]},
    'jgt'   : {'code' : 0x35, 'args': [2]}, # alias for JCS
    'jmpr'  : {'code' : 0x36, 'args': [2]},

    # stack
    'rsp'   : {'code' : 0x37, 'args': []},
    'pha'   : {'code' : 0x38, 'args': []},
    'phx'   : {'code' : 0x39, 'args': []},
    'phy'   : {'code' : 0x3A, 'args': []},
    'pla'   : {'code' : 0x3B, 'args': []},
    'plx'   : {'code' : 0x3C, 'args': []},
    'ply'   : {'code' : 0x3D, 'args': []},
    'jsr'   : {'code' : 0x3E, 'args': [2]},
    'rts'   : {'code' : 0x3F, 'args': []},
    'ldsa'  : {'code' : 0x40, 'args': [1]},
    'stsa'  : {'code' : 0x41, 'args': [1]},

    # compare
    'cpai'  : {'code' : 0x42, 'args': [1]},
    'cpar'  : {'code' : 0x43, 'args': [2]},
    'cpxi'  : {'code' : 0x44, 'args': [1]},
    'cpyi'  : {'code' : 0x45, 'args': [1]},

    # store zero
    'stz'   : {'code' : 0x46, 'args': [2]},

    # bit testing
    'bit'   : {'code' : 0x47, 'args': [1]},

    # memory inc/dec
    'incr'  : {'code' : 0x48, 'args': [2]},
    'decr'  : {'code' : 0x49, 'args': [2]},

    # push immediate
    'phi'   : {'code' : 0x4A, 'args': [1]},

    # roll left - USES TEMP BYTE
    'rola'  : {'code' : 0x4B, 'args': []},
    'rolm'  : {'code' : 0x4C, 'args': [2]},

    # logic memory
    'orr'   : {'code' : 0x4D, 'args': [2]},

    # remote port
    'edor'  : {'code' : 0x4E, 'args': [2]},
    'edir'  : {'code' : 0x4F, 'args': [2]}

}


def assemble(lines: list, program_offset: int = 0) -> list:
    """
    Assembles the input list into assembly instructions. Automatically handles
    labels and arrays. 

    Args    :   lines: list (list of strings)
    Returns :   asm_out: list (list of integers - machine code)
    """
    asm_out = list()
    label_dict = dict()
    ram_index = 0
    for line in lines:
        inst = line.split(" ")
        inst = [x for x in inst if x != '']

        # process program offset
        if inst[0] == "@":
            ram_index = int(inst[1], 16)
            print(f"RAM index set to {hex(ram_index)}")
            continue

        # process label
        if inst[0][-1] == ':':
            label_temp = inst[0].strip(':')
            if(label_temp in label_dict.keys()):
                logging.error("Error: label '" + label_temp + "' has multiple definitions")
                logging.error(label_dict)
                quit()
            label_dict[inst[0].strip(':')] = '{:04X}'.format(int(ram_index.to_bytes(2, 'little').hex(), 16))
            continue    

        # process array
        if inst[0] == ".hex":
            inst.pop(0)
            for i in inst:
                asm_out.append(int(i, 16))
                ram_index = ram_index + 1
            continue

        # process ascii array
        if inst[0] == ".ascii":
            inst.pop(0)
            line = " ".join(inst)
            for c in line[1:-1]:
                asm_out.append('{:02X}'.format(ord(c)))
                ram_index = ram_index + 1
            continue
        
        # otherwise, process opcode and arguments
        opcode = inst[0]
        asm_out.append(opcode_matrix[opcode]['code'])       # append OPCODE
        inst.pop(0)
        ram_index = ram_index + 1
        
        # process arguments (if any)
        arguments: list = opcode_matrix[opcode]['args']
        if arguments:
            for arg in arguments:
                i = str(inst.pop(0))
                if i[0] == '$':
                    i = i.strip('$')
                    asm_out.append(int(i[0:2], 16))
                    if arg == 2:
                        i = '{:04X}'.format(int(i, 16))
                        asm_out.append(int(i[2:4], 16))
                else:
                    if i[0] == '>' or i[0] == '<':
                        asm_out.append(i)
                        continue
                    asm_out.append("<" + i)
                    if arg == 2:
                        asm_out.append(">" + i)
        ram_index = ram_index + sum(opcode_matrix[opcode]['args'])

    # replace labels with addresses
    logging.debug(label_dict)
    for i, line in enumerate(asm_out):
        if type(line) is str:
            if line[0] == '>':
                line = line[1:]
                if line[0] == '$':
                    asm_out[i] = line[3:5]
                else:
                    asm_out[i] = label_dict[line][2:4]
            elif line[0] == '<':
                line = line[1:]
                if line[0] == '$':
                    asm_out[i] = line[1:3]
                else:
                    asm_out[i] = label_dict[line][0:2]

    # replace hex strings with integers
    for i, v in enumerate(asm_out):
        if type(v) == str:
            asm_out[i] = int(v, 16)
    return asm_out
        
        

def process_vars(lines: list) -> list:
    """
    Locates and processes all variable macros (.alias). Basically the same as 
    #define in C header files. Replaces all instances of the label with the literal
    value defined.

    Args    :   lines:list (list of strings)
    Returns :   lines:list (modified)
    """
    var_dict = dict()
    pop_list = list()
    for i, line in enumerate(lines):
        line: str = line.replace('\t', ' ')
        tokens = [l for l in line.split(" ") if l]

        # if alias directive (replaces instances of VAR with VALUE)
        if(tokens[0] == ".alias"):
            if(tokens[1] in var_dict.keys()):
                logging.error("Error: alias '" + tokens[1] + "' has multiple definitions")
                quit(1)
            if '$' in tokens[2]:
                var_dict[tokens[1]] = '$' + (int(tokens[2].strip('$'), 16).to_bytes(2, 'little')).hex().upper()
                pop_list.append(i)
            if '\'' in tokens[2]:
                var_dict[tokens[1]] = '$' + '{:02X}'.format(ord(tokens[2].replace('\'', '')))
                pop_list.append(i)
        
    for i in pop_list[::-1]:
        lines.pop(i)
    for i, line in enumerate(lines):
        for key in list(var_dict.keys()):
            if key in line:
                lines[i] = re.sub(r"\b" + re.escape(key) + r"\b", var_dict[key], line)
                line = lines[i]
    logging.debug("VAR DICT:")
    logging.debug(var_dict)
    return lines


def process_virtual_opcodes(lines: list) -> list:
    """
    Alpha-1 does not contain some opcodes in hardware but this assembler
    supports adding in virtual opcodes.

    This function replaces virtual opcodes (JNE, JCC, etc) with equivalent instructions
    inserted into 'lines'

    Args    :   lines: list
    Returns :   lines: list (modified)
    """

    temp_label_prefix = 'INTERNAL_TEMP_LABEL_'
    virtual_opcodes = ('jcc', 'jne', 'halt', 'jlt')
    lines_out = list()
    index = 0

    for i, line in enumerate(lines):
        line = line.replace('\t', ' ')
        tokens = [l for l in line.split(" ") if l]
        opcode = tokens[0]
        if opcode in virtual_opcodes:
            match opcode:
                case "jcc" | "jlt":
                    temp_label = temp_label_prefix + (str(index))
                    dest = tokens[1]
                    lines_out.append('jcs ' + temp_label)
                    lines_out.append('jmp ' + dest)
                    lines_out.append(temp_label + ':')
                    index += 1
                case "jne":
                    temp_label = temp_label_prefix + (str(index))
                    dest = tokens[1]
                    lines_out.append('jeq ' + temp_label)
                    lines_out.append('jmp ' + dest)
                    lines_out.append(temp_label + ':')
                    index += 1
                case "halt":
                    temp_label = temp_label_prefix + (str(index))
                    lines_out.append(temp_label + ":")
                    lines_out.append('jmp ' + temp_label)
                    index += 1
        else:
            lines_out.append(line)
    return lines_out
                    




def read_file_to_lines(source_file: io.TextIOWrapper) -> list:
    """
    Extracts lines from source file. Removes spaces and special characters.
    Returns list of sanatized lines.

    Args    :   source_file: io.TextIOWrapper 
    Returns :   lines: list (list of strings)
    """
        
    # extract lines, remove spaces and special characters
    # note that if I plan on adding ascii lines, I need to change this so it only removes
    # the last instance of these characters
    temp = [x.split("//")[0].strip(" \n\t") for x in source_file.readlines()]
    
    # remove blank lines
    temp = [x for x in temp if x != '']
    
    # close and return lines
    source_file.close()

    return temp


def remove_comments(lines: list) -> list:
    out_lines = list()
    for line in lines:
        if ';' in line and '"' not in line:
            out_lines.append(str(line[0:line.index(';')]))
        else:
            out_lines.append(line)
            
    # remove blank lines
    out_lines = [x for x in out_lines if x != '']
    return out_lines



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", action="store_true", help="Output HEX machine code to console.")
    parser.add_argument("-d", action="store_true", help="Output DEC machine code to console.")
    parser.add_argument("-n", action="store_true", help="Do not output binary file.")
    parser.add_argument("file", type=argparse.FileType('r'), help="ASM source file.")
    args = parser.parse_args()

    source_file: io.TextIOWrapper = args.file
    
    # get program lines
    lines = read_file_to_lines(source_file)
    
    # remove comments
    lines = remove_comments(lines)

    # process virtual opcodes
    lines = process_virtual_opcodes(lines)
    
    # replace variable instances
    lines = process_vars(lines)
    
    # assemble
    lines = assemble(lines)

    print(f"\nAssembly complete. Binary size: {str(len(lines))} bytes.\n")

    if args.x:
        for i in lines:
            print('{:02X}'.format(i), end = ', ')
        print("")
    
    if args.d:
        for i in lines:
            print(i, end=', ')
        print("")
    
    # output binary
    if not args.n:
        output_filename = args.file.name.split(".")[0] + ".bin"
        f = open(output_filename, "wb")
        b_count = f.write(bytes(lines))
        f.flush()
        f.close()


if __name__ == '__main__':
    main()
