@ 3000

.alias TTYO $1
.alias TTYI $2
.alias PRL $FE00
.alias PRH $FE01 
.alias DIV_TMP $FE02
.alias IN_BUFFER $FD00
.alias cV 'V'
.alias cSPACE $20



        rsp
        ldai $0
        pha
MAIN:

    ; If a character was pressed, enter string test routine
    ;    edi TTYI
    ;    jeq MAIN.SKIP_NAME
    ;    jsr HELLO_NAME
    MAIN.SKIP_NAME:

        ; print number of runs
        pla
        ina
        pha
        tax
        jsr PRINT_BYTE

        ; Print division test
        ldai cSPACE
        edo TTYO
        ldxi $43
        ldyi $03
        jsr DIV
        jsr PRINT_BYTE
        ldai cSPACE
        edo TTYO
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
        jmp MAIN


; print string at pointer passed through X and Y
; X = low
; Y = high
PRINTS:
        stxr PRL
        styr PRH
    PRINTS.LOOP:
        ldari PRL
        jeq PRINTS.RETURN
        edo TTYO
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
        edo TTYO
        ina
        tax
        subi $7F
        jeq ASCDUMP.END
        txa
        jmp ASCDUMP.LOOP
    ASCDUMP.END:
        ldai $0A
        edo TTYO
        ldai $0D
        edo TTYO
        plx
        rts


; output newline
NEWLINE:
        ldai $0A
        edo TTYO
        ldai $0D
        edo TTYO
        rts


; draw horizontal line 
HLINE:
        phx
        ldxi $28
    HLINE.LOOP:
        ldai $2D
        edo TTYO
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
        edo TTYO
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
        edo TTYO
        ldai $20
        edo TTYO
    RAMDUMP.LINE:
        ldary $0
        tax
        jsr PRINT_BYTE
        ldai $20
        edo TTYO
        iny
        tya
        sec
        subi $40
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
        edi TTYI
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
        edo TTYO
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
        edo TTYO
        jsr NEWLINE
        ldxi <CONTINUE_TEXT
        ldyi >CONTINUE_TEXT
        jsr PRINTS
    HELLO_NAME.CONTINUE:
        edi TTYI
        jeq HELLO_NAME.CONTINUE
        ply
        plx
        rts


HELLO_TEXT:
.ascii "Hello, World! I'm an 8-bit CPU with a 16-bit address bus!"
.hex 0A 0D 
.ascii "I was designed, built, and programmed by Kevin Williams in the summer of 2024."
.hex 0A 0D 
.ascii "I'll now run through some demo routines!"
.hex 0A 0D 0
DUMP_TEXT:
.ascii "RAM contents from 0x0000 to 0x0040:"
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




    