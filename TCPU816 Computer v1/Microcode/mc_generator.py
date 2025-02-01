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



import struct

g_instruction_size = 32


g_set_mem = ['RAM_WE', 'PC_COUNT', 'RF_WE']

g_set_a = [
    'CONST_OE_00'
    'RAM_OE',
    'ALU_OE',
    'PCOUT_L',
    'PCOUT_H',
    'ASR_OE',
    'RF_OE',
    'ED_OE',
]

g_set_b = [
    'JMP',
    'JEQ',
    'JCS',
    'IRX_CLR',
    'CARRY_SET',
    'CARRY_CLR',
    'CONST_OE_FF',
]

g_set_c = [
    'IR_WE',
    'RAM_WE',
    'RF_WE',
    'ALU_EN',
    'MARL_L',
    'MARL_H',
]

g_inst_const = {

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
    
    # free
    'ALU_CLR'       :   0x80,
    'ALU_NAND'      :   0x100,
    'ALU_SUB'       :   0x200,
    'RF_IN_A'       :   0x400,
    'RF_IN_B'       :   0x800,
    'RF_OUT_A'      :   0x1000,
    'RF_OUT_B'      :   0x2000,
    'MAR_SEL'       :   0x4000,
    'PC_COUNT'      :   0x8000,


    # aliases
    'RF_IN_X'       :   0x0,
    'RF_IN_Y'       :   0x400,
    'RF_IN_TMP'     :   0x800,
    'RF_IN_A'       :   0xC00,
    'RF_OUT_X'      :   0x0,
    'RF_OUT_Y'      :   0x1000,
    'RF_OUT_TMP'    :   0x2000,
    'RF_OUT_A'      :   0x3000,
}




def main():
    f = open('microcode.des', 'r')
    lines = f.readlines()
    f.close()
    lines = [x.strip(' \n\t') for x in lines]
    
    main_out = list()
    code_out = list([0] * g_instruction_size)
    index = 0
    for line in lines:
        line = line.replace(' ', '')
        line = line.split(';')[0]
        if line == '':
            continue
        tokens = line.split('|')

        # Check if more than one signal from set is used at once
        #   This won't work due to how the decoders are set up
        if len(set(tokens) & set(g_set_a)) > 1:
            print("ERROR: Line contains multiple signals from same set.")
            print(line)
            exit()
        if len(set(tokens) & set(g_set_b)) > 1:
            print("ERROR: Line contains multiple signals from same set.")
            print(line)
            exit()
        if len(set(tokens) & set(g_set_c)) > 1:
            print("ERROR: Line contains multiple signals from same set.")
            print(line)
            exit()
        
        # prevent PC_COUNT from incrementing when RAM is being written to
        if len(set(tokens) & set(g_set_mem)) > 1:
            print("ERROR: Cannot use PC_COUNT, RF_WE, or RAM_WE at the same time. Will cause memory corruption.")
            exit()
    
        # Check if signals conflict between sets A and B
        if bool(set(tokens) & set(g_set_a)) and bool(set(tokens) & set(g_set_b)):
            print("ERROR: Line contains instructions in conflicting sets!")
            print(line)
            exit()
        if(tokens[0] == '.end'):
            main_out = main_out + code_out
            code_out = list([0] * g_instruction_size)
            index = 0
            continue
        temp = 0
        for t in tokens:
            try:
                if(t[0] == ';'):
                    break
            except Exception as e:
                print(e)
                print(line)
            temp = temp | g_inst_const[t]
        code_out[index] = temp
        index = index + 1

    # write single output file
    f = open('temp.bin', 'wb')
    for b in main_out:
        f.write(bytes(struct.pack('>H', b)))

    # write individual high and low rom images
    fl = open('rom_L.bin', 'wb')
    fh = open('rom_H.bin', 'wb')
    bytepack = bytes()
    for b in main_out:
        bytepack = bytepack + struct.pack('>H', b)
    mem_view = memoryview(bytepack)
    for i in range(0, len(bytepack), 2):
        fh.write(bytepack[i].to_bytes(1, 'little'))
        fl.write(bytepack[i + 1].to_bytes(1, 'little'))
    
    fl.flush()
    fh.flush()
    fl.close()
    fh.close()
    f.flush()
    f.close()



if __name__ == '__main__':
    main()
