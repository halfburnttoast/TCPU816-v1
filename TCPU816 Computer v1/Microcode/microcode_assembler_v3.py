#!/usr/bin/env python3

import argparse
import io
import logging
import json
import struct
from enum import Enum
from typing import NamedTuple

__version__ = '3.3.1'

# The maximum number of microcode steps allowed by hardware.
# This must be set to the exact numerical range of the IDX defined by 2^n where
# 'n' is the counter bit-width.
# For the TCPU816 v1.1, this is 5-bits. 2^5 = 32
g_instruction_size = 32

# Usable instruction register bits in hardware.
# Not the bit width of the register itself. Instead this is
# the bits used alongside the IDX counter. Used for maximum
# opcode warning generation. See schematic to derive this.
# For the TCPU816 v1.1, this is 8 bits.
g_instruction_reg_width = 8

# PC_COUNT cannot occur at the same time as either RAM_WE or RF_WE. Otherwise
# memory corruption will occur.
g_set_mem = [
    "RAM_WE",
    "PC_COUNT",
    "RF_WE",
]

# Decoder #1 mapping
g_set_a = [
    "CONST_OE_00",
    "RAM_OE",
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
    'CONST_OE_00'   :   0,          # This MUST be equivilent to NONE, AKA 0
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
    'RF_IN_0'       :   0x400,
    'RF_IN_1'       :   0x800,
    'RF_OUT_0'      :   0x1000,
    'RF_OUT_1'      :   0x2000,
    'MAR_SEL'       :   0x4000,
    'PC_COUNT'      :   0x8000,

    # Register file aliases
    #       IN      OUT
    # A:    0x0     0x0
    # X:    0x400   0x1000
    # Y:    0x800   0x2000
    # T:    0xC00   0x3000

    'RF_IN_ACC'     :   0x0,
    'RF_IN_X'       :   0x400,
    'RF_IN_Y'       :   0x800,
    'RF_IN_TMP'     :   0xC00,
    'RF_OUT_ACC'    :   0x0,
    'RF_OUT_X'      :   0x1000,
    'RF_OUT_Y'      :   0x2000,
    'RF_OUT_TMP'    :   0x3000,
}


class AddrMode(NamedTuple):
    name: str
    args: int
    format: str


class AddressModes(Enum):
    NONE = AddrMode("NONE", 0, '')
    IMM = AddrMode("IMM", 1, "#$nn")
    IND = AddrMode("IND", 2, "$nnnn")
    DIND = AddrMode("DIND", 2, "($nnnn)")
    DINDX = AddrMode("DINDX", 2, "($nnnn),X")
    DINDY = AddrMode("DINDY", 2, "($nnnn),Y")
    INDX = AddrMode("INDX", 2, "$nnnn,X")
    INDY = AddrMode("INDY", 2, "$nnnn,Y")
    SRIX = AddrMode("SRIX", 1, "*($nn),X")
    SRIY = AddrMode("SRIY", 1, "*($nn),Y")
    SRR = AddrMode("SRR", 1, "*($nn)")


class OpCode(NamedTuple):
    name: str
    code: int
    args: int
    mode: AddrMode
    note: str
    cycles: int
    assembled_program: list



def assembly_error(line_num: int, message: str):
    logging.error(f"On line #{line_num}: {message}")
    exit(1)


def assemble(input_pack: dict)-> list[OpCode]:
    """
    Takes in the dictionary pack from the preprocess function and 
    calculates the microcode integers. Replaces the strings in each
    mode grouping with a fixed-size list of integers.

    :param: input_pack: Dict of formatted, grouped, and preprocessed string lines.
    :return: list of OpCode namedtuple objects
    """

    output = []
    opcode_counter = 0
    for opcode in input_pack:
        note = input_pack[opcode]['note']
        note = note[note.index(" "):]
        for mode in input_pack[opcode]['modes']:
            assembly = list([0] * g_instruction_size)
            expected_args: int = AddressModes[mode.name].value.args
            arg_counter = 0
            for idx, line in enumerate(input_pack[opcode]['modes'][mode]):
                line_num = line[0]
                line_str = line[1].replace(" ", "")
                tokens = line_str.split("|")

                # check the validity of labels within the decoders. Only one label from each set can be active at once
                # as per hardware config
                set_a = set(tokens) & set(g_set_a)
                set_b = set(tokens) & set(g_set_b)
                set_c = set(tokens) & set(g_set_c)
                if len(set_a) > 1:
                    assembly_error(line_num, f"Line contains multiple signals from same set. {set_a}")
                if len(set_b) > 1:
                    assembly_error(line_num, f"Line contains multiple signals from same set. {set_b}")
                if len(set_c) > 1:
                    assembly_error(line_num, f"Line contains multiple signals from same set. {set_c}")
                
                # Check if signals conflict between sets A and B. Activating one of these
                # decoders deactivates the other in hardware. Thus, it's impossible to have
                # two labels from these sets active at the same time.
                if bool(set_a) and bool(set_b):
                    assembly_error(line_num, f"Line contains instructions in conflicting sets! {set_a | set_b}", idx, line)

                # prevent PC_COUNT from incrementing when RAM or RF is being written to
                if len(set(tokens) & set(g_set_mem)) > 1:
                    assembly_error(line_num, f"Cannot use PC_COUNT along with RF_WE or RAM_WE at the same time. Will cause memory corruption.")

                # This is a protection in place for a hardware bug in TCPU816 v1.1.
                # Due to an oversight with the decoders, using CARRY_CLR/CARRY_SET
                # causes the databus to go floating state when it isn't being driven. 
                # But, a microinstruction like:
                #       ALU_EN | CARRY_CLR
                # implies that it will write zero to the ALU because of CONST_OE_00. 
                # This DOES NOT happen in version 1.1. Trying to use the above 
                # microinstruction would latch undefined data because CONST_OE_00's 
                # decoder is disabled. 
                # If any control label (except CONST_OE_FF) from decoder #2 is active at the same time as
                # a write from decoder #3, throw a warning.
                if (bool(set_b) and bool(set_c)) and "CONST_OE_FF" not in line_str:
                   logging.warning(f"Line #{line_num}: Attempted to latch undefined value, databus not driven! {set_b | set_c}")

                # calculate code for line and insert into output assembly list
                code = 0
                for t in tokens:
                    try:
                        code = code | g_inst_const[t.replace(" ", "")]
                    except KeyError as e:
                        assembly_error(line_num, f"Invalid control label {e}")
                    assembly[idx] = code
                if idx >= 32:
                    assembly_error(line_num, f"Opcode {opcode} mode {mode} exceeds size limit.")
                if "PC_COUNT" in line_str:
                    arg_counter += 1
            if arg_counter == 0:
                assembly_error(0, f"Opcode {opcode} mode {mode} - missing PC_COUNT.")

            # remove one arg_counter count. Each instruction must have at least one PC_COUNT, but the first PC_COUNT isn't an argument
            arg_counter -= 1

            # TODO: Come up with a different way to override expected argumnt counts.
            if expected_args != arg_counter:
                #assembly_error(0, f"Opcode {opcode} mode {mode} - Mismatching argument count. Expected {expected_args} - found {arg_counter}")
                logging.warning(f"Opcode {opcode} mode {mode} - Mismatching argument count. Expected {expected_args} - found {arg_counter}")
            output.append(
                OpCode(
                    name = opcode,
                    code = opcode_counter,
                    args = expected_args,       # risky, won't be able to dynamically set the output arguments 
                    mode = mode,
                    note = note,
                    cycles = len(input_pack[opcode]['modes'][mode]),
                    assembled_program = assembly
                )
            )
            opcode_counter += 1
    return output



def preprocess(lines: list) -> dict:
    """
    Takes raw text input and begins grouping them into a dict. 
    Follows the format:

    {
        "<Mnemonic>": {
            <AddressingMode>: [List of lines],
            <AddressingMode>: [List of lines],
            etc...
        },
        "<Mnemonic>": {
            <AddressingMode>: [List of lines],
        },
        etc...
    }

    If defined, inserts header and footer into each [List of lines].
    
    :param lines: List of lists of lines along with line numbers (see clean_lines function).
    :return Nested dictionary of organized lines.
    """

    header: list | None = None
    footer: list | None = None
    opcode: str | None = None
    mode: AddrMode | None = None
    output: dict = dict()
    for line in lines:
        line_num = line[0]
        line_str = line[1]

        # for debugging; delete later
        if ".exit" in line:
            logging.debug(f".exit keyword triggered on line {line_str}")
            break

        # if present, set the header and footer. These can only appear once.
        if ".header" in line_str:
            if not header:
                header = [0, line_str[line_str.find(" "):].lstrip()]
                logging.info(f"Header set to '{header} on line {line_num}'")
                continue
            else:
                logging.error(".header keyword can only appear once.")
                logging.error(f"{line_num}: {line_str}")
                exit(1)
        if ".footer" in line_str:
            if not footer:
                footer = [0, line_str[line_str.find(" "):].lstrip()]
                logging.info(f"Footer set to '{footer}' on line {line_num}")
                continue
            else:
                logging.error(".footer keyword can only appear once.")
                logging.error(f"{line_num}: {line_str}")
                exit(1)

        # .begin block opens the outer dictionary for an opcode. Must be closed by .end
        if ".begin" in line_str:
            if opcode:
                logging.error("Expected .end keyword before .begin")
                logging.error(f"{line_num}: {line_str}")
                exit(1)
            try:
                opcode = [l for l in line_str.split(" ") if l][1]
            except IndexError:
                logging.error("Expected opcode name after .begin keyword.")
                logging.error(f"{line_num}: {line_str}")
                exit(1)
            if opcode in output.keys():
                logging.error(f"Opcode {opcode} already defined!")
                logging.error(f"{line_num}: {line_str}")
                exit(1)     
            output[opcode] = dict()
            output[opcode]['modes'] = dict()
            continue

        # close opcode block, append footer to last opened list if defined.
        if ".end" in line_str:
            if not opcode:
                logging.error("Expected .begin keyword to precede .end")
                logging.error(f"{line_num}: {line_str}")
                exit(1)
            if not mode:
                logging.error(f"Expected at least one .mode declaration before .end in opcode {opcode}")
                logging.error(f"{line_num}: {line_str}")
                exit(1)
            if footer:
                output[opcode]['modes'][mode].append(footer)
            opcode = None
            mode = None
            continue

        # for opcode documentation. Included in JSON.
        # Pass the line as-is
        if ".note" in line_str:
            output[opcode]['note'] = line_str
            continue

        # defines the addressing mode. Must appear in AddressingMode
        # If mode is already opened, append footer and create new list for new addressing mode.
        if ".mode" in line_str:
            if not opcode:
                logging.error(f"Mode argument declared outside opcode definition. {line}")
                logging.error(f"{line_num}: {line_str}")
                exit(1)
            if mode:
                output[opcode]['modes'][mode].append(footer)

            # fetch mode and create new sub dictionary entry
            
            try:
                _m = [l for l in line_str.split(" ") if l][1]
                mode: AddrMode = AddressModes[_m]
                if mode in output[opcode]['modes'].keys():
                    logging.error(f"Mode {mode} for opcode {opcode} already defined!")
                    logging.error(f"{line_num}: {line_str}")
                    exit(1)
                logging.debug(f"Opened mode {mode} for opcode {opcode}")
            except IndexError:
                logging.error("Expected mode argument.")
                logging.error(f"{line_num}: {line_str}")
                exit(1)
            # except KeyError as e:
            #     logging.error(f"Invalid addresing mode inside opcode {opcode}: {line}")
            #     logging.error(f"{line_num}: {line_str}")
            #     exit(1)
            output[opcode]['modes'][mode] = []

            # if header is defined, insert it into the top of the new sublist
            if header:
                output[opcode]['modes'][mode].append(header)
            continue
        if not opcode:
            logging.error(f"Not inside opcode block. {line}")
            logging.error(f"{line_num}: {line_str}")
            exit(1)
        if not mode:
            logging.error(f"In opcode {opcode}: Not inside mode block. {line}")
            logging.error(f"{line_num}: {line_str}")
            exit(1)
        output[opcode]['modes'][mode].append([line_num, line_str])
    return output



def clean_lines(lines: list) -> list:
    """
    Removes comments from a list of lines along with whitespace/empty lines

    :param lines: List of lines.
    :return: List of lists in format [[line num, line string],[line num, line string]...]
    """

    out_lines = list()
    for i, line in enumerate(lines):
        if ";" in line:
            cleaned_line = str(line[0 : line.index(";")])
            #out_lines.append(str(line[0 : line.index(";")]))
        else:
            cleaned_line = line
            #out_lines.append(line)
        out_lines.append([i + 1, cleaned_line.strip()])

    # remove empty lines
    out_lines = [x for x in out_lines if x[1] != ""]

    # return cleaned lines
    return out_lines



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        type=argparse.FileType("r"),
        help="Microcode description file."
    )
    parser.add_argument(
        "-o", "--one-file",
        action="store_true",
        help="Generate single binary image file for Logisim."
    )
    parser.add_argument(
        "-r", "--rom-files",
        action="store_true",
        help="Generate high/low binary ROM images for real hardware EEPROMs.",
    )
    parser.add_argument(
        "-t", "--op-table",
        action="store_true",
        help="Generate JSON opcode table mapping that can be imported into an assembler.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Output debug logging info to console."
    )
    parser.add_argument(
        "-g", "--gen_docs",
        action="store_true",
        help="Auto generate opcode documentation text file."
    )
    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    # init logging
    lfmt = "%(levelname)s [%(funcName)s]: %(message)s"
    logging.basicConfig(level=log_level, format=lfmt)
    logging.info(f"TCPU816 microcode assembler - v{__version__}")
    logging.info(f"Parsing file: {args.file.name}")
    logging.debug(args.file)

    # open and read lines from microcode description file, save filename
    source_file: io.TextIOWrapper = args.file
    file_name = source_file.name.split(".")[0]
    lines = [x.strip(" \n\t") for x in source_file.readlines()]
    source_file.close()

    # clean and split up lines into individual groups of microprograms
    lines = clean_lines(lines)
    programs: dict = preprocess(lines)
    assembly_pack = assemble(programs)

    # build list of compiled assembly only
    assembly = []
    for op in assembly_pack:
        assembly = assembly + op.assembled_program

    max_opcodes = (2 ** g_instruction_reg_width)
    if len(assembly_pack) > max_opcodes:
        logging.warning(f"Number of assembled opcodes exceeds IR limit. {len(assembly_pack)} / {max_opcodes}")

    # output JSON formatted opcode table
    if args.op_table:
        output_file_name = f"{file_name}_opcode_table.json"
        output_dict = dict(dict())
        for op in assembly_pack:
            if op.name not in output_dict.keys():
                output_dict[op.name] = {
                    'note' : op.note
                }
            output_dict[op.name][op.mode.name] = {
                "code": op.code,
                "args": op.args,
                "cycles": op.cycles,
            }
        try:
            with open(output_file_name, mode="w") as f:
                json.dump(obj=output_dict, fp=f, indent=4)
        except PermissionError as e:
            logging.error(f"Unable open output file for writing\n{e}")
        logging.info(f"opcode_table dict written to {output_file_name}")

    # automatically build opcode documentation 
    if args.gen_docs:
        output_file_name: str = f"{file_name}_doc.txt"
        output_lines: list = []
        output_lines.append("TCPU816 Opcodes:\n")
        output_lines.append("Note: All '$nn' or '$nnnn' arguments may be replaced by a label name.\n")
        output_lines.append("Note: Use > and < characters to specify high and low bytes.\n")
        output_lines.append("Note: This document was automatically generated.")
        output_lines.append("Opcode modes are formatted as: <opcode>: <mnemonic> - <example>\n\n")
        output_dict = dict(dict())
        for op in assembly_pack:
            if op.name not in output_dict.keys():
                output_dict[op.name] = {
                    'note' : op.note,
                    'modes': {}
                }
            output_dict[op.name]['modes'][op.mode.name] = {
                "code": op.code,
                "mode": op.mode.name,
                "format": op.mode.value.format
            }

        for op_name, op in output_dict.items():
            output_lines.append(f"{op_name} - {op['note']}\n")
            for mode_name, mode in op['modes'].items():
                op_num = '{:02X}'.format(mode["code"])
                output_lines.append(f"\t0x{mode["code"]:02X}: {mode_name}    \t-\t {op_name} {mode["format"]}\n")
            output_lines.append("\n")
        with open(output_file_name, mode="w") as f:
            f.writelines(output_lines)


    # output single binary file for logisim
    if args.one_file:
        output_file_name = f"{file_name}.bin"
        try:
            with open(output_file_name, "wb") as f:
                for b in assembly:
                    f.write(bytes(struct.pack(">H", b)))
        except PermissionError as e:
            logging.error("Unable to open output file for writing.")
            logging.error(e)
            exit(1)
        logging.info(f"Output written to file: {output_file_name}")

    # write individual high and low rom images for physical eeproms
    if args.rom_files:
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
        for b in assembly:
            bytepack = bytepack + struct.pack(">H", b)
        for i in range(0, len(bytepack), 2):
            rom_file_high.write(bytepack[i].to_bytes(1, "little"))
            rom_file_low.write(bytepack[i + 1].to_bytes(1, "little"))
        rom_file_low.close()
        rom_file_high.close()
        logging.info(f"Output written to files: {output_file_name_low}, {output_file_name_high}")

    print(f"Assembly successful for {len(assembly_pack)} / {max_opcodes} opcodes.")
    logging.info(f"Memory size: {len(assembly)} 16-bit words.")
    return 0



if __name__ == '__main__':
    main()