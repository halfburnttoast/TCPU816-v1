@ 0

.alias ACIA_CTRL $1
.alias ACIA_DATA $3


.alias PRL $FE00
.alias PRH $FE01 
.alias IN_BUFFER $FD00
.alias EXMS_L $FE02
.alias EXMS_H $FE03
.alias EXME_L $FE04
.alias EXME_H $FE05
.alias CUR_L $FE06
.alias CUR_H $FE07
.alias PORT_H $FE08
.alias PORT_L $FE09

.alias cCURSOR '>'
.alias cSPACE $20
.alias cNL $0A
.alias cCR $0D
.alias cBS $08
.alias cUS '_'
.alias cESC $1B
.alias cW 'W'
.alias cX 'X'
.alias cR 'R'
.alias cP 'P'
.alias cERR '?'
.alias cCOL ':'



MAIN:
        rsp
        jsr ACIA_SETUP

        ldxi <TITLE_TEXT
        ldyi >TITLE_TEXT
        jsr PRINTS

    ; fetch a new instruction line from user
    MAIN.NEW_INST:
        jsr GET_LINE
        jsr NEWLINE
        
        ; get instruction
        ldxi $0

    ; get the first character and lookup control code
    MAIN.GET_INST_LOOP:
        ldarx IN_BUFFER
        inx
        cpai cSPACE
        jeq MAIN.GET_INST_LOOP

        ; is EXAM command?
        cpai cX
        jeq MAIN.EXAM_JMP

        ; is RUN command?
        cpai cR
        jeq MAIN.RUN

        ; is WRITE command?
        cpai cW
        jeq MAIN.WRITE

        ; is PORT command?
        cpai cP
        jeq MAIN.PORT

        ; no match
        ldai cERR
        jsr SEND_CHR
        jsr NEWLINE
        jmp MAIN.NEW_INST

    ; command jump table
    MAIN.EXAM_JMP:
        jsr EXAM
        jmp MAIN.NEW_INST
    MAIN.RUN:
        jmpr CUR_L
    MAIN.WRITE:
        jsr WRITE
        jmp MAIN.NEW_INST
    MAIN.PORT:
        jsr PORT
        jmp MAIN.NEW_INST



; Reads or writes a value to an external port
; Syntax:
; > P <address>              : read
; > P <address> <value>      : write
PORT:

        ; get port address
        jsr GET_ARG
        cpyi $0
        jeq PORT.END
        ldar PRH
        star PORT_H
        ldar PRL
        star PORT_L

        ; get value
        jsr GET_ARG
        cpyi $0
        jeq PORT.READ
        ldar PRL

        ; write value to port
        edor PORT_L
        jmp PORT.END

    PORT.READ:
        edir PORT_L
        jsr PRINT_BYTE

    PORT.END:
        rts



; Write memory subroutine
WRITE:

    ; begin fetching arguments and writing them to CUR
    WRITE.LOOP:
        jsr GET_ARG
        cpyi $0
        jeq WRITE.END       ; if we reached EOL
        ldar PRL
        stari CUR_L
        incr CUR_L
        jcc WRITE.LOOP
        incr CUR_H
        jmp WRITE.LOOP
    WRITE.END:
        rts




; Examine memory subroutine
EXAM:
        ; copy CUR address pointer to EXMS/E
        ldar CUR_L
        star EXMS_L
        star EXME_L
        ldar CUR_H
        star EXMS_H
        star EXME_H

        ; get first argument
        jsr GET_ARG
        cpyi $0
        jeq EXAM.EXAM_LOOP_OUTER    ; if no arguments, output current byte and exit
        ldar PRL        ; otherwise, store first arg in EXMS and CUR
        star EXMS_L
        star CUR_L
        star EXME_L     ; store EXMS_L in EXME_L so it always outputs at least one byte
        ldar PRH
        star EXMS_H
        star EXME_H
        star CUR_H

        ; get second argument. if none, start exam process
        jsr GET_ARG
        cpyi $0         ; otherwise store end address
        jeq EXAM.EXAM_LOOP_OUTER
        ldar PRL
        star EXME_L
        ldar PRH
        star EXME_H

    EXAM.EXAM_LOOP_OUTER:

        ; print current address on new line
        jsr NEWLINE
        ldar EXMS_H
        jsr PRINT_BYTE
        ldar EXMS_L
        jsr PRINT_BYTE
        ldai cCOL
        jsr SEND_CHR
        ldai cSPACE
        jsr SEND_CHR

    EXAM.EXAM_LOOP_INNER:

        ; fetch and print current byte
        ldari EXMS_L
        jsr PRINT_BYTE
        ldai cSPACE
        jsr SEND_CHR

        ; check if EXMS is equal to EXME
        ldar EXMS_H
        cpar EXME_H
        jne EXAM.NOT_END
        ldar EXMS_L
        cpar EXME_L
        jne EXAM.NOT_END
        jsr NEWLINE         ; we've reached the end
        rts

    EXAM.NOT_END:

        ; increment EXMS_L/H
        incr EXMS_L
        jcc EXAM.EXAM_LOOP_SKIPH
        incr EXMS_H

    EXAM.EXAM_LOOP_SKIPH:

        ; check if we should start a new line
        ldar EXMS_L
        andi $07
        jeq EXAM.EXAM_LOOP_OUTER
        jmp EXAM.EXAM_LOOP_INNER












; fetches an argument from IN_BUFFER + X. Space or null terminated.
; Argument is rolled onto PRL,PRH
; Returns 1 in REG Y if argument was found, 0 if none was found
; Returns new index for IN_BUFFER in REG X
GET_ARG:
        ldai $0
        star PRL
        star PRH
        ;stz PRL
        ;stz PRH
        ldyi $0

    ; skip forward until we find the next character or string ends
    GET_ARG.SEEK:
        ldarx IN_BUFFER

        ; is null?
        jeq GET_ARG.END

        ; is space?
        cpai cSPACE
        jeq GET_ARG.SEEK_SKIP

        ; otherwise we have the first character
        ldyi $1
        jmp GET_ARG.ARG_LOOP

    GET_ARG.SEEK_SKIP:
        inx
        jmp GET_ARG.SEEK

    GET_ARG.ARG_LOOP:
        ldarx IN_BUFFER

        ; is null?
        jeq GET_ARG.END

        ; is space?
        cpai cSPACE
        jeq GET_ARG.END

        ; convert character to binary
        jsr CTON
        jsr BSHIFT              ; shift onto PRL/H
        inx
        jmp GET_ARG.ARG_LOOP

    GET_ARG.END:
        rts
    






; shifts nibble in A onto PRL,PRH
BSHIFT:
        pha
        phx
        pha
        ldar PRH
        andi $0F
        asr4
        star PRH
        ldar PRL
        asr4
        tax
        andi $F0
        star PRL
        pla
        orr PRL
        star PRL
        txa
        andi $0F
        orr PRH
        star PRH
        plx
        pla
        rts



    
; print byte in A as ASCII
PRINT_BYTE:
        pha
        asr4
        jsr PRINT_NIBBLE
        pla
        jsr PRINT_NIBBLE
        rts



; print nibble in A as ASCII
PRINT_NIBBLE:
        pha
        andi $0F
        clc
        addi $30
        cpai $3A
        jlt PRINT_NIBBLE.PRINT
        addi $06
    PRINT_NIBBLE.PRINT:
        jsr SEND_CHR
        pla
        rts




; converts ascii character in A to nibble, returns in A
CTON:
        sec
        subi $30
        cpai $0A
        jlt CTON.END
        sec
        subi $07
    CTON.END:
        rts





; gets a input string from the user. Stores in IN_BUFFER.
; Max string length 254 bytes.
GET_LINE:
        jsr NEWLINE
        ldai cCURSOR
        jsr SEND_CHR
        ldai cSPACE
        jsr SEND_CHR
        ldxi $0         ; index of character buffer

    GET_LINE.GET_C_LOOP:
        jsr GET_CHR
        cpai $0
        jeq GET_LINE.GET_C_LOOP

        ; check if command character
        cpai cNL         ; on newline
        jeq GET_LINE.END_LINE
        cpai cCR         ; on return
        jeq GET_LINE.END_LINE
        cpai cESC        ; on escape, scrap entire line
        jeq GET_LINE

        ; if backspace
        cpai cBS
        jne GET_LINE.ADD_CHR
        jsr SEND_CHR
        ldai cSPACE     ; visually clear the character from screen
        jsr SEND_CHR
        ldai $cBS
        jsr SEND_CHR
        dex
        jcc GET_LINE    ; on underflow, scrap line
        jmp GET_LINE.GET_C_LOOP

    GET_LINE.ADD_CHR:
        jsr SEND_CHR
        starx IN_BUFFER
        inx
        jcs GET_LINE        ; on overflow, scrap line
        jmp GET_LINE.GET_C_LOOP

    GET_LINE.END_LINE:
        ldai $0         ; insert null terminator
        starx IN_BUFFER
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



; output newline
NEWLINE:
        ldai $0A
        jsr SEND_CHR
        ldai $0D
        jsr SEND_CHR
        rts


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



TITLE_TEXT:
.ascii "MiniMON 0.3v (ACIA Version) - JUL 31 2024"
.hex 0A 0D 0