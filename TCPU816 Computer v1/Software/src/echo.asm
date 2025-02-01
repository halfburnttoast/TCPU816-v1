.alias TTYO $1
.alias TTYI $2



LOOP:
    edi TTYI
    jeq LOOP
    edo TTYO
    jmp LOOP