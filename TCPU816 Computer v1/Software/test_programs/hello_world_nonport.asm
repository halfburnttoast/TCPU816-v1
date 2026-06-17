@ 0

MAIN:
        ldx #$0
    MAIN.LOOP:
        lda STRING,X
        jeq MAIN.END
        edo $1
        inx
        jmp MAIN.LOOP
    MAIN.END:
        halt
        


STRING:
.ascii "Hello, World!"
.hex $0


