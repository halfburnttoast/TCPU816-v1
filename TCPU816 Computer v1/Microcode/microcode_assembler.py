#!/usr/bin/env python3

# No AI was used when writing this program or ANY of my programs <3

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


import argparse
import io
import json
import logging
import struct
from typing import NamedTuple

# The maximum number of microcode steps allowed by hardware.
# This must be set to the exact numerical range of the IDX defined by 2^n where
# 'n' is the counter bit-width.
# For the TCPU816 v1.1, this is 5-bits. 2^5 = 32
g_instruction_size = 32


# Used to pre-set the first and last line of every microprogram.
# If defined, the assembler automatically inserts these lines at the
# beginning and end of each microprogram, respectively.
# Define in source file using .header and .footer keywords.
g_header = None
g_footer = None


g_keywords = [
    ".begin",
    ".end",
    ".header",
    ".footer",
    ".args",
]


# PC_COUNT cannot occur at the same time as either RAM_WE or RF_WE. Otherwise
# memory corruption will occur.
g_set_mem = [
    "RAM_WE",
    "PC_COUNT",
    "RF_WE",
]


# Decoder #1 mapping
g_set_a = [
    "CONST_OE_00RAM_OE",
    "ALU_OE",
    "PCOUT_L",
    "PCOUT_H",
    "ASR_OE",
    "RF_OE",
    "ED_OE",
]

# Decoder #2 mapping
g_set_b = [
    "JMP",
    "JEQ",
    "JCS",
    "IRX_CLR",
    "CARRY_SET",
    "CARRY_CLR",
    "CONST_OE_FF",
]

# Decoder #3 mapping
g_set_c = [
    "IR_WE",
    "RAM_WE",
    "RF_WE",
    "ALU_EN",
    "MARL_L",
    "MARL_H",
]

# Addresses of control labels in hex
g_inst_const: dict = {
    'NONE'          :   0,          # default behavior, use for inserting blank lines in description file

    # set a
    'CONST_OE_00'   :   0,
    'RAM_OE'        :   1,
    'ALU_OE'        :   2,
    'PCOUT_L'       :   3,
    'PCOUT_H'       :   4,
    'ASR_OE'        :   5,
    'RF_OE'         :   6,
    'ED_OE'         :   7,

    # set b
    'JMP'           :   8,
    'JEQ'           :   9,
    'JCS'           :   0xA,
    'IRX_CLR'       :   0xB,
    'CARRY_SET'     :   0xC,
    'CARRY_CLR'     :   0xD,
    'CONST_OE_FF'   :   0xE,

    # set c
    'IR_WE'         :   0x10,
    'RAM_WE'        :   0x20,
    'RF_WE'         :   0x30,
    'ALU_EN'        :   0x40,
    'MARL_L'        :   0x50,
    'MARL_H'        :   0x60,
    'ED_WE'         :   0x70,
    
    # unrestricted
    'ALU_CLR'       :   0x80,
    'ALU_NAND'      :   0x100,
    'ALU_SUB'       :   0x200,
    'RF_IN_A'       :   0x400,
    'RF_IN_B'       :   0x800,
    'RF_OUT_A'      :   0x1000,
    'RF_OUT_B'      :   0x2000,
    'MAR_SEL'       :   0x4000,
    'PC_COUNT'      :   0x8000,

    # Register file aliases
    'RF_IN_X'       :   0x0,
    'RF_IN_Y'       :   0x400,
    'RF_IN_TMP'     :   0x800,
    'RF_IN_A'       :   0xC00,
    'RF_OUT_X'      :   0x0,
    'RF_OUT_Y'      :   0x1000,
    'RF_OUT_TMP'    :   0x2000,
    'RF_OUT_A'      :   0x3000,
}


class OpCode(NamedTuple):
    name: str
    code: int
    args: int
    assembled_program: list


def assembly_error(pgm_name: str, message: str, line_num: int, line: str):
    logging.error(f"Assembly error: {message}")
    logging.error(f"Error occured on microprogram '{pgm_name}' [line {line_num}] - {line}")
    exit(1)


def extract_microprograms(code_in: list) -> list:
    """
    Parses and returns list of lists of microprograms delimited by .begin and .end keywords.

    :param code_in: List of lines from readlines.
    :return: List of lists, each sublist containing one microprogram
    """

    micro_programs: list = []
    current_program: list = []
    in_program: bool = False
    for line in code_in:

        # if present, set the header and footer. These can only appear once.
        if ".header" in line:
            global g_header
            if not g_header:
                g_header = line[line.find(" ") :].lstrip()
                logging.info(f"Header set to '{g_header}'")
                continue
            else:
                logging.error("Error: .header keyword can only appear once.")
                logging.error(f"{line}")
                exit(1)
        if ".footer" in line:
            global g_footer
            if not g_footer:
                g_footer = line[line.find(" ") :].lstrip()
                logging.info(f"Footer set to '{g_footer}'")
                continue
            else:
                logging.error("Error: .footer keyword can only appear once.")
                logging.error(f"{line}")
                exit(1)

        if ".begin" in line:
            if in_program:
                logging.error("Error: Expected .end keyword before .begin")
                logging.error(f"Error occured near: '{line}'")
                exit(1)
            current_program.append(line)
            in_program = True
            continue
        if ".end" in line:
            if not in_program:
                print("Error: Expected .begin keyword before .end")
                if len(micro_programs) > 0:
                    logging.error(f"Error occured after '{micro_programs[-1][0]}' program.")
                else:
                    logging.error("Error occured at top of file.")
                exit(1)
            current_program.append(line)
            micro_programs.append(current_program)
            current_program = []
            in_program = False
            continue
        current_program.append(line)
    return micro_programs


def clean_lines(lines: list) -> list:
    """
    Removes comments from a list of lines along with whitespace/empty lines

    :param lines: List of lines.
    :return: List of lines without comments, whitespace, or empty lines.
    """

    out_lines = list()
    for line in lines:
        if ";" in line:
            out_lines.append(str(line[0 : line.index(";")]))
        else:
            out_lines.append(line)

    # remove leading and trailing whitespace
    out_lines = [x.strip() for x in out_lines]

    # remove empty lines
    out_lines = [x for x in out_lines if x != ""]

    # return cleaned lines
    return out_lines


def generate_microprogram(program_number: int, program: list, strict_args: bool = False) -> OpCode:
    """
    Calculates the control signal codes from the lines passed in. Automatically checks for conflicting
    control codes. Tracks PC_COUNT usage to account for .args keyword.

    Note: Each microprogram must be exactly g_instruction_size elements long. This is a hardware
    requirement. The output is padded with zeros to meet this requirement.

    :param program: List of text lines containing control label names separated by '|' character.
    :return OpCode instance containing name and assembled code.
    """

    code_out: list = list([0] * g_instruction_size)
    pgm_name: str = ""
    index = 0
    arg_counter = 0
    expected_args = 0
    if g_header:
        program.insert(0, g_header)
    if g_footer:
        program.insert(-1, g_footer)
    for idx, line in enumerate(program):
        if ".begin" in line:
            try:
                pgm_name = [x for x in line.split(" ") if x][1]
            except IndexError:
                logging.error(f"Program #{program_number}: Opcode name expected after .begin keyword.")
                exit(1)
            continue
        if ".end" in line:
            break
        if ".args" in line:
            try:
                expected_args = int(line[line.find(" ") :])
                logging.debug(f"Expected args set: {expected_args}")
                if expected_args < 0:
                    raise ValueError()
            except ValueError as _:
                assembly_error(pgm_name,"Invalid number of args. Must be positive integer.", idx, line,)
            continue

        # if not keyword, begin evaluating line
        line = line.replace(" ", "")
        tokens = line.split("|")

        # check the validity of labels within the decoders. Only one label from each set can be active at once
        # as per hardware config
        set_a = set(tokens) & set(g_set_a)
        set_b = set(tokens) & set(g_set_b)
        set_c = set(tokens) & set(g_set_c)
        if len(set_a) > 1:
            assembly_error(pgm_name, f"Line contains multiple signals from same set. {set_a}", idx, line)
        if len(set_b) > 1:
            assembly_error(pgm_name, f"Line contains multiple signals from same set. {set_b}", idx, line)
        if len(set_c) > 1:
            assembly_error(pgm_name, f"Line contains multiple signals from same set. {set_c}", idx, line)

        # prevent PC_COUNT from incrementing when RAM or RF is being written to
        if len(set(tokens) & set(g_set_mem)) > 1:
            assembly_error(pgm_name, "Cannot use PC_COUNT along with RF_WE or RAM_WE at the same time. Will cause memory corruption.", idx, line)

        # Check if signals conflict between sets A and B. Activating one of these
        # decoders deactivates the other in hardware. Thus, it's impossible to have
        # two labels from these sets active at the same time.
        if bool(set_a) and bool(set_b):
            assembly_error(pgm_name, f"Line contains instructions in conflicting sets! {set_a | set_b}", idx, line)

        # This is a protection in place for a hardware bug in TCPU816 v1.1.
        # Due to an oversight with the decoders, using CARRY_CLR/CARRY_SET
        # causes the databus to go floating state when it isn't being driven. 
        # But, a microinstruction like:
        #       ALU_EN | CARRY_CLR
        # implies that it will write zero to the ALU because of CONST_OE_00. 
        # This DOES NOT happen in version 1.1. Trying to use the above 
        # microinstruction would latch undefined data because CONST_OE_00's 
        # decoder is disabled. 
        # If any contol label from decoder #2 is active at the same time as
        # a write from decoder #3, throw a warning.
        if bool(set_b) and bool(set_c):
            assembly_error(pgm_name, f"Attempted to latch undefined value, databus not driven! {set_b | set_c}", idx, line)


        code = 0
        for t in tokens:
            try:
                code = code | g_inst_const[t.replace(" ", "")]
            except KeyError as e:
                assembly_error(pgm_name, f"Invalid control label {e}.", idx, line)
        code_out[index] = code
        index += 1
        if index >= 32:
            assembly_error(pgm_name, f"Program '{pgm_name}' exceeds size limit!", idx, line)

        # the first line always contains PC_COUNT, so ignore the first instance of this.
        if "PC_COUNT" in line and idx > 0:
            arg_counter += 1

    # check if the program counter has been incremented the expected number of times
    if expected_args > 0 or strict_args:
        if expected_args != arg_counter:
            logging.error(f"On program {pgm_name} - invalid num of args. Expected {expected_args}, got {arg_counter}")
            exit(1)
    return OpCode(pgm_name, program_number, arg_counter, code_out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        type=argparse.FileType("r"),
        help="Microcode description file."
    )
    parser.add_argument(
        "-o",
        action="store_true",
        help="Generate single binary image file for Logisim."
    )
    parser.add_argument(
        "-r",
        action="store_true",
        help="Generate high/low binary ROM images for real hardware EEPROMs.",
    )
    parser.add_argument(
        "-t",
        action="store_true",
        help="Generate JSON opcode table mapping that can be imported into an assembler.",
    )
    parser.add_argument(
        "-s",
        action="store_true",
        help="Enable strict argument tracking. '.args' keyword is enforced for each program."
    )
    args = parser.parse_args()

    # init logging
    logging.basicConfig(level=logging.ERROR)
    logging.info("TCPU816-v1.1 microcode assembler")
    logging.info("Parsing file: %s", args.file)

    # open and read lines from microcode description file, save filename
    source_file: io.TextIOWrapper = args.file
    file_name = source_file.name.split(".")[0]
    lines = [x.strip(" \n\t") for x in source_file.readlines()]
    source_file.close()

    # clean and split up lines into individual groups of microprograms
    lines = clean_lines(lines)
    programs: list = extract_microprograms(lines)

    # start building microprograms
    main_out: list = []
    opcode_table: dict = {}
    for index, program in enumerate(programs):
        opcode: OpCode = generate_microprogram(index, program, args.s)
        main_out = main_out + opcode.assembled_program
        opcode_table[opcode.name] = {"code": opcode.code, "args": [opcode.args]}
    logging.debug(f"Opcode table: {opcode_table}")

    # output opcode table to JSON.
    if args.t:
        output_file_name = f"{file_name}_opcode_table.json"
        try:
            with open(output_file_name, "w") as f:
                json.dump(obj=opcode_table, indent=4, fp=f)
        except PermissionError as e:
            logging.error(f"Unable open output file for writing\n{e}")
        logging.info(f"opcode_table dict written to {output_file_name}")

    # write single output file
    if args.o:
        output_file_name = f"{file_name}.bin"
        try:
            with open(output_file_name, "wb") as f:
                for b in main_out:
                    f.write(bytes(struct.pack(">H", b)))
        except PermissionError as e:
            logging.error("Unable to open output file for writing.")
            logging.error(e)
            exit(1)           
        logging.info(f"Output written to file: {output_file_name}")

    # write individual high and low rom images for physical eeproms
    if args.r:
        output_file_name_low = f"{file_name}_L.bin"
        output_file_name_high = f"{file_name}_H.bin"
        try:
            rom_file_low = open(output_file_name_low, "wb")
            rom_file_high = open(output_file_name_high, "wb")
        except PermissionError as e:
            logging.error("Unable to open output file for writing.")
            logging.error(e)
            exit(1)
        bytepack = bytes()
        for b in main_out:
            bytepack = bytepack + struct.pack(">H", b)
        for i in range(0, len(bytepack), 2):
            rom_file_high.write(bytepack[i].to_bytes(1, "little"))
            rom_file_low.write(bytepack[i + 1].to_bytes(1, "little"))
        rom_file_low.close()
        rom_file_high.close()
        logging.info(f"Output written to files: {output_file_name_low}, {output_file_name_high}")

    print(f"Assembly successful for {len(opcode_table.keys())} opcodes.")
    logging.info(f"Memory size: {len(main_out)}x16-bit words.")
    return 0


if __name__ == "__main__":
    main()
