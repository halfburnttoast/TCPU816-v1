#!/usr/bin/env python3

#     The creation of this computer, and all related programs, was only possible
#     due to the incredible amount of open-source, freely available information
#     on electrical/computer/software engineering. So, I want this project in its
#     entirety to be open-source.

#     None of this code was written with AI. <3

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.


import argparse
import enum
import inspect
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import LiteralString

__version__ = '0.7.0'


class AssemblyError(Exception):
    def __init__(
            self,
            file_name: str,
            line_num: int,
            message: str,
            context: None | tuple = None
    ) -> None:
        self.file_name = file_name
        self.line_num = line_num
        self.message = message
        self.context = context
        super().__init__(f"{file_name}:{line_num}: {message}")


class AddressMode(enum.Enum):
    NONE = 0
    IMM = 1         # #$12
    IND = 2         # $1234
    DIND = 3        # $(1234)
    INDX = 4        # $1234,X
    INDY = 5        # $1234,Y
    DINDX = 6       # ($1234),X
    DINDY = 7       # ($1234),Y
    SRR = 8         # *($12)
    SRIX = 9        # *($12),X
    SRIY = 10       # *($12),Y


@dataclass
class SourceFile:
    file_name: str
    lines: list


def debug_dump_lines(out_lines: list) -> None:
    for i, v in enumerate(out_lines):
        pad: int = len(str(len(out_lines)))
        logging.debug(f"{str(i).rjust(pad)}: {v}")
    logging.debug("End dump.\n")



def assembly_error(
        file_name: str,
        line_num: int,
        message: str,
        context: None | tuple = None
) -> None:
    calling_function = inspect.stack()[1].function
    line_num = line_num + 1
    logging.fatal(f"[{calling_function}] {file_name}:{line_num}: {message}")
    if context is not None:
        logging.fatal(f"Context: {context}")
    raise AssemblyError(file_name, line_num, message, context)



def decode_argument(arg_str: str) -> list:
    """
    Takes in a 6502 formatted address and determines the
    addressing mode.

    :param arg_str: Raw argument string input (i.e. $(3100) ).
    :return: List containing [address string, addressing mode ENUM value].
    """

    if not hasattr(decode_argument, '_match_patterns'):
        _char_range = r"[0-9A-Z_.]"
        decode_argument._match_patterns = {
            "imm" : re.compile(rf"#([<>]?\$?{_char_range}+)$"),                  # #$12AB or #LABEL   (< or > to indicate high or low byte)
            "ind" : re.compile(rf"(\$?{_char_range}+)$"),                        # $12AB or LABEL
            "dind" : re.compile(rf"\((\$?{_char_range}+)\)$"),                   # ($12AB) or (LABEL)
            "indxy" : re.compile(rf"(\$?{_char_range}+),([XY])$"),               # $12AB,<X or Y> or LABEL,<X or Y>
            "dind_indexed" : re.compile(rf"\((\$?{_char_range}+)\),([XY])$"),    # ($12AB),<X or Y> or (LABEL),<X or Y>
            "srr" : re.compile(rf"\*\((\$?{_char_range}+)\)$"),                  # *($12) or *(LABEL),<X or Y>
            "srrxy" : re.compile(rf"\*\((\$?{_char_range}+)\),([XY])$"),         # *($12),<X or Y> or *(LABEL),<X or Y>
        }
        logging.debug("decode_argument regex patterns compiled.")
    patterns = getattr(decode_argument, '_match_patterns')
    imm_pattern = patterns['imm']
    ind_pattern = patterns['ind']
    dind_pattern = patterns['dind']
    indxy_pattern = patterns['indxy']
    dind_indexed_pattern = patterns['dind_indexed']
    srr_pattern = patterns['srr']
    srrxy_pattern = patterns['srrxy']

    arg_str = arg_str.replace(" ", "").upper()
    if match := re.match(dind_indexed_pattern, arg_str):
        return [match.group(1), AddressMode.DINDX if match.group(2) == "X" else AddressMode.DINDY]
    elif match := re.match(indxy_pattern, arg_str):
        return [match.group(1), AddressMode.INDX if match.group(2) == "X" else AddressMode.INDY]
    elif match := re.match(srr_pattern, arg_str):
        return [match.group(1), AddressMode.SRR]
    elif match := re.match(srrxy_pattern, arg_str):
        return [match.group(1), AddressMode.SRIX if match.group(2) == "X" else AddressMode.SRIY]
    elif match := re.match(dind_pattern, arg_str):
        return [match.group(1), AddressMode.DIND]
    elif match := re.search(imm_pattern, arg_str):
        return [match.group(1), AddressMode.IMM]
    elif match := re.match(ind_pattern, arg_str):
        return [match.group(1), AddressMode.IND]
    else:
        raise ValueError(f"Unknown/malformed argument '{arg_str}'")



def debug_test_arg_parse():
    logging.debug("ARGUMENT DECODE TEST:")
    l = [
        "#<LABEL",
        "#>LABEL",
        "#$1234",
        "#LABEL",
        "$12AB",
        "LABEL",
        "($12AB)",
        "(LABEL)",
        "$12AB,X",
        "$12AB,Y",
        "LABEL,X",
        "LABEL,Y",
        "(LABEL),X",
        "(LABEL),Y",
        "($12AB),X",
        "($12AB),Y",
        "*($12)",
        "*(LABEL)",
        "*($12),X",
        "*($12),Y",
    ]
    for i in l:
        logging.debug(f"{i}: {decode_argument(i)}")


def assemble(lines: list, microcode_table: dict) -> list:
    """
    Assembles the input list into machine code. Automatically handles
    labels and arrays

    :param microcode_table: 
    :param lines: list of line number and line strings.
    :return: asm_out: list of integers (machine code).
    """

    asm_out = []
    label_dict: dict = dict()
    ram_index: int = 0
    insertion_index: int = 0
    index_set: bool = False
    if not hasattr(assemble, '_match_patterns'):
        assemble._match_patterns = {
            "byte_int" : re.compile(r"\$([0-9A-Fa-f]{1,2}$)"),
            "word_int" : re.compile(r"\$([0-9A-Fa-f]{3,4}$)"),
            "label" : re.compile(r"([A-Za-z_.].*)\:$"),
            "substring" : re.compile(r'("([^"]*)"|[^",]+)')
        }
    patterns: dict = getattr(assemble, '_match_patterns')
    byte_int_pattern: re.Pattern = patterns['byte_int']
    word_int_pattern: re.Pattern = patterns['word_int']
    label_pattern: re.Pattern = patterns['label']
    substring_pattern: re.Pattern = patterns['substring']

    # Pass 1: primary assembly
    for file_name, line_num, line_tokens in lines:
        inst = line_tokens[0].upper()

        # process program offset
        if inst == '@':
            if index_set:
                assembly_error(file_name, line_num, "Program memory index already set!")
            else:
                index_set = True
            try:
                ram_index = int(line_tokens[1], 16)
                insertion_index = int(line_tokens[1], 16)
            except IndexError as e:
                assembly_error(file_name, line_num, f"Expected address value after offset declaration. {e}")
            except ValueError as e:
                assembly_error(file_name, line_num, f"Invalid address value. {e}")
            logging.debug(f"RAM index set: {ram_index}")
            continue

        # process label
        if inst[-1] == ':':
            try:
                label_temp: str = re.match(label_pattern, inst).group(1)
            except AttributeError:
                assembly_error(file_name, line_num, f"Invalid label name '{inst}'")
            if label_temp in label_dict.keys():
                assembly_error(file_name, line_num, "Error: label '" + label_temp + "' has multiple definitions")
            label_dict[label_temp] = '{:04X}'.format(int(ram_index.to_bytes(2, 'little').hex(), 16))
            logging.debug(f"Label added: {[label_temp, label_dict[label_temp]]}")
            continue

        # process hex array
        if inst == ".HEX":
            line_tokens.pop(0)
            if not len(line_tokens):
                logging.warning(f"{file_name}:{line_num}: Expected hex values after .hex keyword.")
            try:
                for i in line_tokens[0].split(','):
                    asm_out.append(int(i.strip('$'), 16))
                    ram_index = ram_index + 1
            except ValueError as e:
                assembly_error(file_name, line_num, f"Error parsing hex values. {e}")
            continue

        # process ascii array
        if inst == ".ASCII":
            line_tokens.pop(0)
            for c in line_tokens[0]:
                asm_out.append('{:02X}'.format(ord(c)))
                ram_index = ram_index + 1
            continue

        # process mixed data, comma separated
        if inst == ".BYTE":
            line_tokens.pop(0)
            items = re.findall(substring_pattern, line_tokens[0])
            items = [item[0].strip() for item in items]
            items = [item for item in items if len(item) > 0]
            for t in items:
                if '"' in t:
                    for c in t.replace('"', ''):
                        asm_out.append('{:02X}'.format(ord(c)))
                        ram_index = ram_index + 1
                elif '$' in t:
                    try:
                        num = int(t.strip('$'), 16)
                    except ValueError as e:
                        assembly_error(file_name, line_num, f"Error parsing DATA values. {e}")
                    if num > 0xFF:
                        assembly_error(file_name, line_num, f"DATA value too large. {num}")
                    asm_out.append('{:02X}'.format(num))
                    ram_index = ram_index + 1
                else:
                    try:
                        num = int(t, 10)
                    except ValueError as e:
                        assembly_error(file_name, line_num, f"Error parsing DATA values. {e}")
                    if num > 0xFF:
                        assembly_error(file_name, line_num, f"DATA value too large. {num}")
                    asm_out.append('{:02X}'.format(num))
                    ram_index = ram_index + 1
            continue


        # otherwise process opcode and argument
        opcode_name: str = inst
        addr_mode: str = AddressMode.NONE.name
        argument: None | str | LiteralString = None
        if opcode_name not in microcode_table.keys():
            assembly_error(file_name, line_num, f"Invalid opcode name '{opcode_name}'")

        # detect argument type and value (if applicable)
        if len(line_tokens) > 1:
            try:
                argument, addr_mode = decode_argument(line_tokens[1])
            except ValueError as e:
                assembly_error(file_name, line_num, f"Error parsing arguments. {e}")
            addr_mode = addr_mode.name
        try:
            opcode_dict = microcode_table[opcode_name][addr_mode]
        except KeyError as e:
            assembly_error(file_name, line_num, f"Invalid address mode {e} for opcode '{opcode_name}'")
        except TypeError:
            assembly_error(file_name, line_num, f"No matching addressing mode for opcode '{opcode_name}'")

        # append opcode to output along with arguments. If the argument is a label we need
        # to append the label because we don't know what address the label resolves to yet.
        asm_out.append(opcode_dict['code'])
        ram_index = ram_index + 1
        expected_args = opcode_dict['args']
        if expected_args > 0:
            if argument is None:
                assembly_error(file_name, line_num, f"No argument given for opcode '{opcode_name}' mode '{addr_mode}'.")

            # if this is supposed to resolve to a number (contains '$' before hex digits)
            if '$' in argument:
                word_arg: re.Pattern = re.match(word_int_pattern, argument)
                byte_arg: re.Pattern = re.match(byte_int_pattern, argument)
                if expected_args == 1:
                    if byte_arg:
                        asm_out.append(int(argument.replace('$', ''), 16))
                    elif word_arg:

                        # Attempt to extract the least significant byte from the value if it's < 0x100.
                        # This allows for things like '.alias TEST $11 ; lda #TEST' to work because
                        # process_variables will save the convert the aliased addresses to little-endian
                        # and pad out the most significant byte with zeros.
                        # But, this feels really hacky. Probably should think of something better...
                        val = argument.replace('$', '')
                        val = val[2:] + val[0:2]
                        val = int(val, 16)
                        if val < 0x100:
                            asm_out.append(val)
                        else:
                            assembly_error(file_name, line_num, f"Argument too large for opcode '{opcode_name}' mode '{addr_mode}' : {hex(val)}")
                    else:
                        assembly_error(file_name, line_num, "No matching argument for opcode '{opcode_name}' mode '{addr_mode}. {argument}'")
                elif expected_args == 2:
                    if word_arg:
                        arg = argument.replace('$', '')
                        arg_high = arg[2:4]
                        arg_low = arg[0:2]
                        asm_out.append(int(arg_low, 16))
                        asm_out.append(int(arg_high, 16))

                    # if argument isn't filled completely, convert it to a 16-bit address
                    elif byte_arg:
                        arg_low = argument.replace('$', '')
                        arg_high = 0
                        asm_out.append(int(arg_low, 16))
                        asm_out.append(arg_high)
                    else:
                        assembly_error(file_name, line_num,f"Mismatched argument for opcode {opcode_name} mode '{addr_mode}': {argument}")

            # if there's no $ character, it must be a label
            else:
                if expected_args == 1:
                    asm_out.append(argument)
                elif expected_args == 2:
                    asm_out.append('<' + argument)
                    asm_out.append('>' + argument)
            ram_index = ram_index + expected_args
        else:
            continue
        pass        # put breakpoint here for inter-instruction debugging
    logging.debug("Pass 1 complete.")

    # Pass #2: Replace labels in asm_out with addresses from label_dict
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
    logging.debug("Pass 2 complete.")

    # Pass 3: replace all hex-coded strings with integers
    for i, v in enumerate(asm_out):
        if type(v) == str:
            asm_out[i] = int(v, 16)
    logging.debug("Pass 3 complete.")
    logging.info(f"Program assembled for starting address {'0x{:04X}'.format(insertion_index)}")
    return asm_out




def tokenize_lines(lines: list) -> list:
    """
    Split the string portion of lines into a list of tokens.
    Maintains line numbers.

    NOTE: All lines with the .ascii keyword are added as-is, otherwise
    it will strip the spaces out of strings. .byte supports mixed data
    types including strings. So, it will also not remove spaces or do
    any further formatting.

    Output format now looks like:

    [
        [line number, [token1, token2, ...]],
        ...
    ]

    :param lines: List of line numbers and line strings.
    :return: List of line numbers and line tokens
    """

    if not hasattr(tokenize_lines, "_match_patterns"):
        tokenize_lines._match_patterns = {
            'ascii': re.compile(r"^.ascii\s+\"([^\"]+)\""),
            'byte': re.compile(r"^.byte\s+(.+)")
        }
    patterns: dict = getattr(tokenize_lines, "_match_patterns")
    ascii_pattern: re.Pattern = patterns['ascii']
    byte_pattern: re.Pattern = patterns['byte']

    out_lines = []
    for file_name, line_num, line_str in lines:
        if line_str.startswith('.ascii'):
            if match := re.match(ascii_pattern, line_str):
                out_lines.append([file_name, line_num, ['.ascii'] + [match.group(1)]])
            else:
                assembly_error(file_name, line_num, "Expected character string after .ascii keyword.")
        elif line_str.startswith('.byte'):
            if match := re.match(byte_pattern, line_str):
                out_lines.append([file_name, line_num, ['.byte'] + [match.group(1)]])
            else:
                assembly_error(file_name, line_num, "Expected data string after .byte keyword.")
        else:
            tokens = [t for t in line_str.split(" ") if t]
            inst = tokens.pop(0)
            args = "".join(tokens)
            out_lines.append([file_name, line_num, [inst] + ([args] if args else [])])
    logging.debug(f"Tokenized lines:")
    debug_dump_lines(out_lines)
    return out_lines



def process_variables(lines: list) -> list:
    """
    Locates and processes all variable macros (.alias). Basically the same as
    #define in C header files. Replaces all instances of the label with the literal
    value defined.

    Args    :   lines:list (list of strings)
    Returns :   lines:list (modified)
    """

    if not hasattr(process_variables, "_match_patterns"):
        process_variables._match_patterns = {
            'alias': re.compile(                #       .alias LABELNAME <$12AB or '<single character'>
                r"^.alias\s+"                   # .alias keyword
                r"([A-Za-z_.]+)\s+"             # group 1 - label name, can include underscores and periods
                r"\'?(\$?[A-Za-z0-9]+)'?"       # group 2 - hex address OR character. Capture $ in group if hex number.
            )
        }
    patterns = getattr(process_variables, "_match_patterns")
    alias_pattern: re.Pattern = patterns['alias']

    var_dict = dict()
    pop_list = list()

    # Start by building dict of variables. Save indicies of alias in pop_list
    for i, line_pack in enumerate(lines):
        file_name, line_num, line_str = line_pack
        if line_str.startswith('.alias'):
            if match := re.match(alias_pattern, line_str):
                label_name = match.group(1)
                argument = str(match.group(2))
                if label_name in var_dict:
                    assembly_error(file_name, line_num, f"Variable '{label_name}' already defined.")
                if '$' in argument:
                    try:
                        _arg = int(argument.strip('$'), 16)
                        _arg = _arg.to_bytes(2, 'little').hex().upper()
                    except ValueError:
                        assembly_error(file_name, line_num, f"Invalid numerical value. '{line_str}'")
                    except OverflowError:
                        assembly_error(file_name, line_num, f"Oversized value for alias. '{line_str}'")
                    var_dict[label_name] = '$' + _arg
                    pop_list.append(i)
                elif '\'' in argument:
                    try:
                        _chr = argument.replace('\'', '')
                        _chr = '{:02X}'.format(ord(_chr))
                    except TypeError:
                        assembly_error(file_name, line_num, f"Invalid character alias definition. '{line_str}'")
                    var_dict[label_name] = '$' + _chr
                    pop_list.append(i)
            else:
                assembly_error(file_name, line_num, f"Expected label and value after .alias keyword.")

    # remove all alias definitions from code base
    for i in pop_list[::-1]:
        lines.pop(i)

    # replace all instances of alias with real value
    for i, line in enumerate(lines):
        file_name, line_num, line_str = line
        for key in var_dict.keys():
            if key in line_str:
                out = re.sub(r"\b" + re.escape(key) + r"\b", var_dict[key], line_str)
                lines[i] = [file_name, line_num, out]
    logging.debug("VAR DICT (addresses are little-endian):")
    logging.debug(var_dict)
    logging.debug("After variable processing:")
    debug_dump_lines(lines)
    return lines



def process_virtual_opcodes(lines: list) -> list:
    """
    Processes virtual opcodes.
    Because the TCPU816 computer is a minimalist computer, it does
    not have certain opcodes implemented in hardware. This function
    will replace the virtual opcodes with their equivalent instructions
    and temporary labels.

    The virtual opcodes are:
    - HLT  - halts the CPU (by entering into an infinite loop)
    - HALT - alias; same as HLT
    - JCC  - jumps to label/address on ALU carry clear
    - JNE  - jumps to label/address on ALU not equal
    - JLT  - alias; same as JNE

    :param lines: List of lines.
    :return: List of lines with virtual opcodes replaced.
    """

    _label_counter = 0
    _temp_label_prefix = "INTERNAL_TEMP_LABEL_"
    def _generate_temp_label() -> str:
        nonlocal _label_counter
        _label_counter += 1
        return f"{_temp_label_prefix}{_label_counter}"
    def _current_temp_label() -> str:
        return f"{_temp_label_prefix}{_label_counter}"
    virtual_opcodes = {
        'hlt': lambda _: [
            f"{_generate_temp_label()}:",
            f"jmp {_current_temp_label()}",
        ],
        'jcc': lambda dest: [
            f"jcs {_generate_temp_label()}",
            f"jmp {dest}",
            f"{_current_temp_label()}:",
        ],
        'jne': lambda dest: [
            f"jeq {_generate_temp_label()}",
            f"jmp {dest}",
            f"{_current_temp_label()}:",
        ],
    }
    virtual_opcodes['halt'] = virtual_opcodes['hlt']
    virtual_opcodes['jlt'] = virtual_opcodes['jcc']

    out_lines = []
    for file_name, line_num, line_str in lines:
        line_str = line_str.replace('\t', '')
        tokens = [l for l in line_str.split(' ') if l]
        opcode = tokens[0].lower()
        if opcode in virtual_opcodes:
            target = tokens[1] if len(tokens) > 1 else None
            expansion = virtual_opcodes[opcode](target)
            for line in expansion:
                out_lines.append([file_name, line_num, line])
            continue
        else:
            out_lines.append([file_name, line_num, line_str])
    return out_lines




def process_line_labels(lines: list) -> list:
    """
    Splits labels defined on the same line as other content onto
    separate lines. This could be a preprocessor stage, I guess.
    But, for now, it's it's own function.

    :param lines: Input lines from preprocess.
    :return: Lines with same-line labels separated.
    """

    match_pattern = re.compile(r'^([A-Za-z][A-Za-z0-9]+\:).*')
    out_lines = []
    for file_name, line_num, line_str in lines:
        match = match_pattern.match(line_str)
        if match:
            _label = match.group(1)
            out_lines.append([file_name, line_num, _label])
            _line = line_str.replace(_label, "")
            if _line != "":
                out_lines.append([file_name, line_num, _line.strip()])
        else:
            out_lines.append([file_name, line_num, line_str])
    debug_dump_lines(out_lines)
    return out_lines



def preprocess(source_file: SourceFile) -> list:
    """
    Removes comments, empty lines, leading and trailing whitespace.
    Outputs list of lists, each sublist contains the line number and line string.

    :param lines: List of strings
    :return: List of lists containing file name, line number and line string.
    """

    # Prevent circular includes by tracking files already included.
    file_name = source_file.file_name
    if not hasattr(preprocess, "files_loaded"):
        preprocess.files_loaded = [file_name]
    elif file_name in preprocess.files_loaded:
        logging.warning(f"File {file_name} already loaded.")
        return []
    else:
        preprocess.files_loaded.append(file_name)
        
    # compile + cache regex
    if not hasattr(preprocess, "_match_patterns"):
        preprocess._match_patterns = {
            'preproc' : re.compile(r"#([A-Za-z]+)"),
            'include' : re.compile(r"#([A-Za-z]+)\s+(\".*\"$)")
        }
    patterns = getattr(preprocess, "_match_patterns")
    preproc_cmd_format = patterns['preproc']
    include_cmd_format = patterns['include']

    out_lines = list()
    for file_name, idx, line in source_file.lines:

        cmd = re.match(preproc_cmd_format, line)
        if cmd:
            cmd = cmd.group(1)
            logging.debug(f"Preprocessor command found: {cmd}")
            if cmd == 'include':
                try:
                    file_path = re.match(include_cmd_format, line).group(2).replace('"', '')
                except AttributeError:
                    assembly_error(file_name, idx, f"Expected file name/path after include command.")
                new_file = read_file_to_lines(file_path)
                out_lines = out_lines + preprocess(new_file)
                continue
            else:
                assembly_error(file_name, idx, f"Invalid preprocessor command: {cmd}")

        if ';' in line and '"' not in line:
            out = [file_name, idx, line[0:line.index(';')].strip()]
        else:
            out = [file_name, idx, line.strip()]
        if out[2] != '':
            out_lines.append(out)
    logging.debug("Cleaned lines before parse:")
    debug_dump_lines(out_lines)
    return out_lines



def read_file_to_lines(source_file_name: str) -> SourceFile:
    """
    Reads a file and returns a list of lines.

    :param source_file_name: Path to the file.
    :return: List of line strings
    """

    full_path = Path(source_file_name)
    file_name = full_path.name
    logging.debug(f"Opening file {full_path}")

    try:
        with open(full_path, "r") as f:
            raw_lines = f.readlines()
    except FileNotFoundError:
        logging.error(f"Input file {full_path} not found.")
        exit(1)
    except PermissionError:
        logging.error(f"Could not open {full_path} for reading.")
        exit(1)

    out_lines = list()
    for i, line in enumerate(raw_lines):
        out_lines.append([file_name, i, line.split("//")[0].strip(" \n\t")])
    return SourceFile(file_name, out_lines)



def main():
    default_opcode_table_file: str = "microcode.json"
    parser = argparse.ArgumentParser(description=f"TCPU816-v1.1 assembler v{__version__}")
    parser.add_argument("-x", "--hex", action="store_true", help="Output HEX machine code to console.")
    parser.add_argument("-d", "--dec", action="store_true", help="Output DEC machine code to console.")
    parser.add_argument("-n", "--no-output", action="store_true", help="Do not output machine code to file.")
    parser.add_argument("-o", "--output", type=str, help="Output file name.")
    parser.add_argument("input", type=str, help="Input file name.")
    parser.add_argument('-t', '--op-table', nargs='?', type=str, help=f"Override opcode table with JSON file. Otherwise, will default to {default_opcode_table_file}")
    parser.add_argument('-V', '--version', action='version', version=__version__)
    parser.add_argument('-v', '--verbose', action='count', default=0, help="Debug output.")
    args = parser.parse_args()

    log_format = "%(levelname)s [%(funcName)s]: %(message)s"
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format=log_format)
    else:
        logging.basicConfig(level=logging.INFO, format=log_format)
    logging.info(f"TCPU816-v1.1 assembler v{__version__}")
    logging.info("Parsing file: %s", args.input)

    # TODO: Implement -t option for microcode json file loading.
    if args.op_table:
        raise NotImplementedError("Option -t not implemented yet.")

    # load JSON opcode table
    # TODO: Implement validation of data with pydantic
    microcode_table: dict = dict()
    try:
        with open(default_opcode_table_file, 'r') as f:
            microcode_table = json.load(f)
    except FileNotFoundError:
        logging.error(f"microcode.json opcode table not found.")

    # begin assembly process
    source_file: str = args.input
    source_file: SourceFile = read_file_to_lines(source_file)
    try:
        lines = preprocess(source_file)
        lines = process_line_labels(lines)
        lines = process_virtual_opcodes(lines)
        lines = process_variables(lines)
        lines = tokenize_lines(lines)
        assembled_code = assemble(lines, microcode_table)
    except AssemblyError:
        exit(1)
    logging.info(f"Assembly successful for '{source_file.file_name}'. Binary size: {len(assembled_code)} bytes.")

    # output assembly
    if args.hex:
        logging.info("Output machine code in hex format (base16):")
        for i in assembled_code:
            print('{:02X}'.format(i), end=', ')
        print("")
    if args.dec:
        logging.info("Output machine code in dec format (base10):")
        for i in assembled_code:
            print(i, end=', ')
        print("")
    if not args.no_output:
        output_file_name = args.input.split('.')[0] + ".bin"
        try:
            with open(output_file_name, 'wb') as f:
                f.write(bytes(assembled_code))
            logging.info(f"Binary file written to {output_file_name}")
        except Exception as e:
            logging.error(f"Could not open {output_file_name} for writing. {e}")
            exit(1)
    else:
        logging.info("No output file written (-n/--no-output option enabled.)")


if __name__ == '__main__':
    main()