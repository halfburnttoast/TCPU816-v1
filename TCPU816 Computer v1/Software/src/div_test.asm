.alias DIV_TMP $FE00

MAIN:
    ldxi $38
    ldyi $0A
    jsr DIV
    halt


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
    ; X now contains the quotient
    ; y has the remainder
    rts