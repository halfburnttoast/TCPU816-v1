.alias TTYO $1
.alias TTYI $2
.alias PRL $FE00
.alias PRH $FE01 
.alias IN_BUFFER $FD00
.alias EXMS_L $FE02
.alias EXMS_H $FE03
.alias EXME_L $FE04
.alias EXME_H $FE05
.alias CUR_L $FE06
.alias CUR_H $FE07

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
.alias cERR '?'
.alias cCOL ':'



MAIN:
        rsp
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

        ; no match
        ldai cERR
        edo TTYO
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
        edo TTYO
        ldai cSPACE
        edo TTYO

    EXAM.EXAM_LOOP_INNER:

        ; fetch and print current byte
        ldari EXMS_L
        jsr PRINT_BYTE
        ldai cSPACE
        edo TTYO

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
        stz PRL
        stz PRH
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
        edo TTYO
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
        edo TTYO
        ldai cSPACE
        edo TTYO
        ldxi $0         ; index of character buffer

    GET_LINE.GET_C_LOOP:
        edi TTYI
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
        edo TTYO
        ldai cSPACE     ; visually clear the character from screen
        edo TTYO
        ldai $cBS
        edo TTYO
        dex
        jcc GET_LINE    ; on underflow, scrap line
        jmp GET_LINE.GET_C_LOOP

    GET_LINE.ADD_CHR:
        edo TTYO
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
        edo TTYO
        incr PRL
        jcc PRINTS.LOOP
        incr PRH
        jmp PRINTS.LOOP
    PRINTS.RETURN:
        rts



; output newline
NEWLINE:
        ldai $0A
        edo TTYO
        ldai $0D
        edo TTYO
        rts



TITLE_TEXT:
.ascii "MiniMON 0.2v - JUN 28 2024"
.hex 0A 0D 0