@ 3000

.alias ACIA_CTRL $1
.alias ACIA_DATA $3
.alias PORT $0014


MAIN:
        edi PORT
        jsr PRINT_BYTE
        jsr NEWLINE
        jmp MAIN




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
