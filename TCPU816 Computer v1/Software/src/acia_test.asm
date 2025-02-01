@ 0

.alias ACIA_CTRL $1
.alias ACIA_DATA $3

TEST:
        ldai $3
        edo ACIA_CTRL
        ldai $D5
        edo ACIA_CTRL
        ldxi $0
    TEST.TEST_LOOP:
        edi ACIA_CTRL
        bit $2
        jeq TEST.TEST_LOOP
        ldarx STRING
        jeq TEST.TEST_END
        edo ACIA_DATA
        inx
        jmp TEST.TEST_LOOP
    TEST.TEST_END:
        ldxi $0
        jmp TEST.TEST_LOOP


STRING:
.ascii "FARTS! "
.hex 0
