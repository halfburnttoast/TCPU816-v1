.alias ACIA_CTRL $20
.alias ACIA_DATA $30

SETUP:
        rsp
        ldai $3
        edo ACIA_CTRL
        ldai $15
        edo ACIA_CTRL
        ldxi $0

LOOP:
        edi ACIA_CTRL
        bit $1
        jeq LOOP
        edi ACIA_DATA
        tax
    LOOP.WRITE_WAIT:
        edi ACIA_CTRL
        bit $2
        jeq LOOP.WRITE_WAIT
        txa
        edo ACIA_DATA
        jmp LOOP
