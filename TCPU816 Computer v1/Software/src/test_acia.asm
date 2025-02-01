@ 800
.alias ACIA_CTRL $1
.alias ACIA_DATA $3
.alias TTYO $1
.alias TTYI $2
.alias PRL $FE00
.alias PRH $FE01 
.alias DIV_TMP $FE02
.alias FIBA_H $FE23
.alias FIBA_L $FE24
.alias FIBB_H $FE25
.alias FIBB_L $FE26
.alias FIBC_H $FE27
.alias FIBC_L $FE28
.alias IN_BUFFER $FD00
.alias cV 'V'
.alias cSPACE $20



        rsp
        ldai $0
        pha
        jsr ACIA_SETUP
MAIN:

    ; If a character was pressed, enter string test routine
        jsr GET_CHR
        bit $0
        jeq MAIN.SKIP_NAME
        jsr HELLO_NAME
    MAIN.SKIP_NAME:

        ; print number of runs
        pla
        ina
        pha
        tax
        jsr PRINT_BYTE

        ; Print division test
        ldai cSPACE
        jsr SEND_CHR
        ldxi $43
        ldyi $03
        jsr DIV
        jsr PRINT_BYTE
        ldai cSPACE
        jsr SEND_CHR
        tyx
        jsr PRINT_BYTE

        ; print hello text
        jsr NEWLINE
        jsr HLINE
        jsr NEWLINE
        ldxi <HELLO_TEXT
        ldyi >HELLO_TEXT
        jsr PRINTS
        jsr NEWLINE

        ; run ascdump
        jsr ASCDUMP_LOOP_TEST
        jsr NEWLINE

        ; print first X bytes of RAM
        jsr RAMDUMP
        jsr NEWLINE

        ; draw raccoon logo image
        ldxi <RACCOON_IMG
        ldyi >RACCOON_IMG
        jsr PRINTS
        nop
        
        ; fibonacci
        jsr NEWLINE
        ldxi <FIBONACCI_TEXT
        ldyi >FIBONACCI_TEXT
        jsr PRINTS
        jsr FIBONACCI
        jsr NEWLINE     

        ; extended stack test
        ldxi <STACK_TEXT
        ldyi >STACK_TEXT
        jsr PRINTS
        ldai $42
        pha
        ldai $FA
        pha
        jsr ESTACK
        pla
        ldxi <STACK_TEXT.3
        ldyi >STACK_TEXT.3
        jsr PRINTS
        pla
        tax
        jsr PRINT_BYTE
        jsr NEWLINE

        cpai $05
        jne MAIN.ST_PASS
        ldxi <FAIL_TEXT
        ldyi >FAIL_TEXT
        jsr PRINTS
    MAIN.ST_PASS:
        ldxi <PASS_TEXT
        ldyi >PASS_TEXT
        jsr PRINTS

        jmp MAIN



; Fibonacci
FIBONACCI:
        ldyi $20
        ldai $0
        star FIBA_H
        star FIBA_L
        star FIBB_H
        star FIBB_L
        star FIBC_H
        star FIBC_L
        incr FIBA_L
    FIBONACCI.LOOP:

        ; C = A + B
        jsr FIBONACCI.ADD_16
        ldar FIBC_H
        tax
        jsr PRINT_BYTE
        ldar FIBC_L
        tax
        jsr PRINT_BYTE
        jsr NEWLINE
        jsr DELAY

        ; A = C
        ldar FIBC_L
        star FIBA_L
        ldar FIBC_H
        star FIBA_H

        ; C = A + B
        jsr FIBONACCI.ADD_16
        ldar FIBC_H
        tax
        jsr PRINT_BYTE
        ldar FIBC_L
        tax
        jsr PRINT_BYTE
        jsr NEWLINE
        jsr DELAY

        ; B = C
        ldar FIBC_L
        star FIBB_L
        ldar FIBC_H
        star FIBB_H

        dey
        jne FIBONACCI.LOOP
        rts

    FIBONACCI.ADD_16:
        ldar FIBA_L
        addr FIBB_L
        star FIBC_L
        jcs FIBONACCI.ADD_16.CARRY
        ldar FIBA_H
        addr FIBB_H
        star FIBC_H
        rts
    FIBONACCI.ADD_16.CARRY:
        ldar FIBA_H
        addr FIBB_H
        ina 
        star FIBC_H
        rts





; print string at pointer passed through X and Y
; X = low
; Y = high
PRINTS:
        stxr PRL
        styr PRH
    PRINTS.LOOP:
        ldari PRL
        jeq PRINTS.RETURN
        jsr SEND_CHR
        incr PRL
        jcc PRINTS.LOOP
        incr PRH
        jmp PRINTS.LOOP
    PRINTS.RETURN:
        rts
    

; run through ASCDUMP multiple times
ASCDUMP_LOOP_TEST:
        phx
        phy
        ldxi <ASC_TEXT
        ldyi >ASC_TEXT
        jsr PRINTS
        ldai $8
    ASCDUMP_LOOP_TEST.ASC_LOOP:
        pha
        jsr ASCDUMP
        pla
        dea
        jne ASCDUMP_LOOP_TEST.ASC_LOOP
        ply
        plx
        rts


; Output printable ascii characters (0x20 - 0x7F)
ASCDUMP:
        clc
        phx
        ldai $20
    ASCDUMP.LOOP:
        jsr SEND_CHR
        ina
        tax
        subi $7F
        jeq ASCDUMP.END
        txa
        jmp ASCDUMP.LOOP
    ASCDUMP.END:
        ldai $0A
        jsr SEND_CHR
        ldai $0D
        jsr SEND_CHR
        plx
        rts


; output newline
NEWLINE:
        ldai $0A
        jsr SEND_CHR
        ldai $0D
        jsr SEND_CHR
        rts


; draw horizontal line 
HLINE:
        phx
        ldxi $28
    HLINE.LOOP:
        ldai $2D
        jsr SEND_CHR
        dex
        txa
        jne HLINE.LOOP
        plx
        rts


; print byte in X as ASCII hex
; does not retain X register contents on RTS
PRINT_BYTE:
        txa
        pha
        asr4
        tax
        jsr PRINT_NIBBLE
        plx
        jsr PRINT_NIBBLE
        rts


; print nibble in X as ASCII
PRINT_NIBBLE:
        txa
        andi $0F
        clc
        addi $30
        tax
        sec
        subi $3A
        jcc PRINT_NIBBLE.PRINT
        txa
        addi $07
        tax
    PRINT_NIBBLE.PRINT:
        txa
        jsr SEND_CHR
        rts


; does not retain X or Y register contents
RAMDUMP:
        ldai $0
        pha
        ldxi <DUMP_TEXT
        ldyi >DUMP_TEXT
        jsr PRINTS
    RAMDUMP.LOOP:
        pla
        tay
        andi $07
        jne RAMDUMP.LINE
        jsr NEWLINE
        tyx
        jsr PRINT_BYTE
        ldai $3A
        jsr SEND_CHR
        ldai $20
        jsr SEND_CHR
    RAMDUMP.LINE:
        ldary $FF00
        tax
        jsr PRINT_BYTE
        ldai $20
        jsr SEND_CHR
        iny
        tya
        sec
        subi $FE
        jeq RAMDUMP.END
        tya
        pha
        jmp RAMDUMP.LOOP
    RAMDUMP.END:
        rts


; divide X by Y
; returns X (quot), Y (remainder)
DIV:
        styr DIV_TMP
        ldyi $0
        txa
        ldxi $0
        sec
    DIV.LOOP:
        tay
        subr DIV_TMP
        jcc DIV.END
        tya
        inx
        sec
        subr DIV_TMP
        jmp DIV.LOOP
    DIV.END:
        rts


HELLO_NAME:
        phx
        phy
        ldxi <NAME_TEXT
        ldyi >NAME_TEXT
        jsr PRINTS
        ldxi $0
    HELLO_NAME.GET_STR:
        jsr GET_CHR
        jeq HELLO_NAME.GET_STR
        pha
        sec
        subi $0D
        jeq HELLO_NAME.END
        pla
        pha
        sec
        subi $0A
        jeq HELLO_NAME.END
        pla
        starx IN_BUFFER
        inx
        jsr SEND_CHR
        jmp HELLO_NAME.GET_STR
    HELLO_NAME.END:
        ldai $0
        starx IN_BUFFER
        pla
        ldxi <NAME_RESPONSE
        ldyi >NAME_RESPONSE
        jsr PRINTS
        ldxi <IN_BUFFER
        ldyi >IN_BUFFER
        jsr PRINTS
        ldai $21
        jsr SEND_CHR
        jsr NEWLINE
        ldxi <CONTINUE_TEXT
        ldyi >CONTINUE_TEXT
        jsr PRINTS
    HELLO_NAME.CONTINUE:
        jmp GET_CHR
        jeq HELLO_NAME.CONTINUE
        ply
        plx
        rts




; Setup ACIA
ACIA_SETUP:
        ldai $3
        edo ACIA_CTRL
        ldai $D5
        edo ACIA_CTRL
        rts

; sends the character in register A to ACIA
SEND_CHR:
        pha
    SEND_CHR.WAIT:
        edi ACIA_CTRL
        bit $2
        jeq SEND_CHR.WAIT
        pla
        edo ACIA_DATA
        rts


; gets character from ACIA, non-blocking. Returns in A. Returns
; 0 if no character.
GET_CHR:
        edi ACIA_CTRL
        bit $1
        jeq GET_CHR.NO_CHR
        edi ACIA_DATA
        rts
    GET_CHR.NO_CHR:
        ldai $0
        rts


DELAY:
        phx 
        ldxi $FF
    DELAY.LOOP:
        dex
        jne DELAY.LOOP
        plx
        rts


ESTACK:
        ldxi <STACK_TEXT.1
        ldyi >STACK_TEXT.1
        jsr PRINTS
        ldsa $2
        tax
        jsr PRINT_BYTE
        jsr NEWLINE

        ldxi <STACK_TEXT.2
        ldyi >STACK_TEXT.2
        jsr PRINTS
        ldsa $3
        tax
        jsr PRINT_BYTE
        jsr NEWLINE

        ldai $05
        stsa $3

        rts




STACK_TEXT:
.ascii "Extended stack test."
.hex 0A 0D 0
STACK_TEXT.1:
.ascii "ARG1: "
.hex 0
STACK_TEXT.2:
.ascii "ARG2: "
.hex 0
STACK_TEXT.3:
.ascii "CHANGED ARG 2: "
.hex 0
PASS_TEXT:
.ascii "PASS"
.hex 0A 0D 0
FAIL_TEXT:
.ascii "FAIL"
.hex 0A 0D 0
HELLO_TEXT:
.ascii "Hello, World! I'm an 8-bit CPU with a 16-bit address bus!"
.hex 0A 0D 
.ascii "I was designed, built, and programmed by HalfBurntToast in the summer of 2024."
.hex 0A 0D 
.ascii "I'll now run through some demo routines!"
.hex 0A 0D 0
DUMP_TEXT:
.ascii "RAM contents from 0xFF00 to 0xFFFF:"
.hex 0
ASC_TEXT:
.ascii "Printable ASCII characters:"
.hex 0A 0D 0
NAME_TEXT:
.ascii "Enter your name: "
.hex 0
NAME_RESPONSE:
.hex 0A 0D
.ascii "Hello, "
.hex 0
CONTINUE_TEXT:
.ascii "Press any key to continue."
.hex 0A 0D 0
FIBONACCI_TEXT:
.ascii "16-bit Fibonacci Sequence (in hex)"
.hex 0A 0D 0
RACCOON_IMG:
.hex 0A 0D
.ascii "== TCPU816 - ALPHA 1 - JUNE, 19, 2024 =="
.hex 0A 0D
.ascii "Raccoon picture!"
.hex 0A 0D
.hex 20 20 20 20 20 20 20 20 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 2E 20 20 20 20 20 20 20 20 
.hex 0A 0D
.hex 20 20 20 20 20 2E 63 4F 30 6B 6F 3B 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 2E 27 63 64 4F 30 78 2C 20 20 20 20 20 20 
.hex 0A 0D
.hex 20 20 20 20 20 63 4E 4E 57 4D 4D 57 58 6B 6C 2C 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 2E 3B 6F 30 4E 4D 4D 4D 57 57 30 27 20 20 20 20 20 
.hex 0A 0D
.hex 20 20 20 20 27 30 58 63 3B 6B 4E 4D 4D 4D 4D 4E 4F 6C 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 2C 64 4B 57 4D 4D 4D 4D 58 6F 3B 78 57 78 2E 20 20 20 20 
.hex 0A 0D
.hex 20 20 20 20 64 57 64 2E 20 20 3B 6B 57 4D 4D 4D 4D 4D 58 64 27 20 20 20 20 20 2E 2E 2E 2E 2E 2E 2E 2E 20 20 20 20 2E 3B 6B 4E 4D 4D 4D 4D 4D 58 64 2E 20 20 2C 30 58 3A 20 20 20 20 
.hex 0A 0D
.hex 20 20 20 27 30 58 3B 20 20 20 20 2E 63 4B 4D 4D 4D 4D 4D 4D 58 78 6F 78 6B 4F 4F 30 30 4F 4F 30 30 4F 4F 6B 64 6F 6B 4E 4D 4D 4D 4D 4D 57 6B 2C 20 20 20 20 20 6F 57 78 2E 20 20 20 
.hex 0A 0D
.hex 20 20 20 63 4E 6B 2E 20 20 20 20 20 20 2C 30 4D 4D 4D 57 58 30 78 6F 6C 3A 3B 2C 27 27 27 27 27 2C 3B 3A 63 6C 64 6B 4B 4E 57 4D 4D 57 64 2E 20 20 20 20 20 20 3B 58 30 27 20 20 20 
.hex 0A 0D
.hex 20 20 20 64 57 64 20 20 20 20 20 20 20 3A 4B 4B 78 6C 3B 2E 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 2E 27 3A 6F 6B 4B 6B 27 20 20 20 20 20 20 27 30 58 3A 20 20 20 
.hex 0A 0D
.hex 20 20 2E 78 57 6C 20 20 20 20 20 20 20 2E 27 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 2E 27 2E 20 20 20 20 20 20 2E 6B 57 63 20 20 20 
.hex 0A 0D
.hex 20 20 2E 6B 57 63 20 27 3B 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 27 3B 2E 2E 6B 57 6C 20 20 20 
.hex 0A 0D
.hex 20 20 2E 78 57 78 6F 58 30 27 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 63 58 4F 6C 4F 57 63 20 20 20 
.hex 0A 0D
.hex 20 20 20 64 57 57 4E 78 2E 20 2E 2E 2C 3A 6C 6F 78 6B 4F 4F 4F 4F 78 6F 3A 2E 20 20 20 20 20 20 20 20 27 63 64 6B 4F 4F 4F 6B 78 64 6C 63 3B 27 2E 20 20 3B 30 57 57 58 3A 20 20 20 
.hex 0A 0D
.hex 20 20 20 6C 57 4E 78 3A 6C 78 30 58 57 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 58 6F 2E 20 20 20 20 27 78 4E 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 57 4E 4B 6B 6F 3A 63 30 57 4B 2C 20 20 20 
.hex 0A 0D
.hex 20 20 2E 6B 57 57 58 57 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 57 64 2E 20 20 27 4F 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4E 58 57 4E 6F 2E 20 20 
.hex 0A 0D
.hex 20 2E 6F 57 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 57 4F 20 20 20 30 4D 4D 4D 4D 4D 4D 78 2E 20 20 2C 4B 4D 4D 4D 4D 4D 57 6B 20 20 6C 4B 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 58 3A 20 20 
.hex 0A 0D
.hex 20 3B 4B 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4E 3A 20 20 20 6F 57 4D 4D 4D 57 4F 27 20 20 20 20 63 58 4D 4D 4D 4D 4B 3B 20 20 2E 64 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 6B 2E 20 
.hex 0A 0D
.hex 20 64 57 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4B 64 6C 78 58 4D 4D 57 30 6C 2C 27 27 27 27 27 27 3A 78 58 4D 4D 57 30 6F 6C 6B 4E 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 58 3A 20 
.hex 0A 0D
.hex 2E 4F 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4E 4F 63 3A 78 4B 4E 4E 4E 4E 4E 58 4B 64 63 6F 4B 57 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 64 20 
.hex 0A 0D
.hex 2C 4B 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 57 30 6F 2C 2E 20 2C 4B 4D 4D 4D 4D 4D 4D 4D 57 4F 27 20 2E 3A 78 58 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 6B 2E 
.hex 0A 0D
.hex 3A 58 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 58 64 3B 2E 20 20 20 20 20 2E 6C 4F 4E 4D 4D 4E 6B 63 2E 20 20 20 20 20 2E 63 4F 4E 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4F 2E 
.hex 0A 0D
.hex 2C 4B 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 4E 4F 63 2E 20 2E 3B 2E 20 20 20 20 20 20 2E 6B 4D 57 64 2E 20 20 20 20 20 20 2E 3B 2E 20 2C 64 4B 57 4D 4D 4D 4D 4D 4D 4D 4D 4D 4D 57 6B 2E 
.hex 0A 0D
.hex 20 2C 78 4E 4D 4D 4D 4D 4D 4D 4D 57 4F 3B 2E 20 20 20 64 57 78 27 2E 2C 3B 63 6F 78 58 4D 4D 4B 64 6C 3A 3B 27 2E 3B 30 58 3B 20 20 20 2E 6C 4B 4D 4D 4D 4D 4D 4D 4D 57 4B 6C 2E 20 
.hex 0A 0D
.hex 20 20 20 27 64 4B 57 4D 4D 4D 57 64 2E 20 20 20 20 20 2E 64 30 30 4F 30 4F 6B 64 6C 63 3A 3A 63 6F 78 6B 4F 30 4F 30 4F 63 2E 20 20 20 20 20 2C 30 4D 4D 4D 4D 57 4F 63 2E 20 20 20 
.hex 0A 0D
.hex 20 20 20 20 20 2E 63 4F 4E 4D 58 63 20 20 20 20 20 20 20 20 2E 2E 2E 2E 20 20 20 20 20 20 20 20 20 20 20 2E 2E 2E 2E 2E 20 20 20 20 20 20 20 2E 78 4D 4D 58 78 3B 2E 20 20 20 20 20 
.hex 0A 0D
.hex 20 20 20 20 20 20 20 2E 2C 6F 30 4B 6B 6C 2C 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 2E 3B 6F 30 4B 6B 63 2E 20 20 20 20 20 20 20 20 
.hex 0A 0D
.hex 20 20 20 20 20 20 20 20 20 20 2E 2C 6C 6B 4B 30 64 63 2C 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 2E 3B 6C 78 30 30 78 63 27 20 20 20 20 20 20 20 20 20 20 20 
.hex 0A 0D
.hex 20 20 20 20 20 20 20 20 20 20 20 20 20 20 2E 3A 6F 4F 30 30 6B 64 63 3A 2C 27 2E 2E 2E 2E 2E 2E 2E 2E 27 2C 3A 6C 64 4F 30 30 6B 6C 3B 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 
.hex 0A 0D
.hex 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 2E 2C 63 6F 78 4F 4F 4F 4F 4F 4F 4F 4F 4F 4F 4F 4F 4F 6B 64 6C 3A 27 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 
.hex 0A 0D
.hex 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 2E 2E 2E 27 27 27 27 27 27 2E 2E 2E 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20
.hex 0A 0D 0A 0D 0




    
