@ 3000


.alias ACIA_CTRL $1
.alias ACIA_DATA $3
.alias RBD $4
.alias RAD $14
.alias DDRB $24
.alias DDRA $34


START:
        ldai $FF
        edo DDRA
        ldai $14
        star $0
        ldai $0
        star $1
        ldai $40
        edo $RAD
LOOP:        
        edir $0
        nota
        edor $0

WAIT:
        dex
        jne WAIT
        jmp LOOP

