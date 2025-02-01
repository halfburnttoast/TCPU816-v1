.alias PRL $FE00
.alias PRH $FE01
.alias TTYO $1
.alias TTYI $2

.alias IN_BUFFER $FD00

    ldxi <IN_BUFFER
    ldyi >IN_BUFFER
    rsp
MAIN:
    ldxi <TEXT
    ldyi >TEXT
    jsr PRINTS
    ldxi $0
GET_STR:
    edi TTYI
    jeq GET_STR
    pha
    sec
    subi $0D
    jeq END
    pla
    pha
    sec
    subi $0A
    jeq END
    pla
    starx IN_BUFFER
    inx
    edo TTYO
    jmp GET_STR
END:
    ldai $0
    starx IN_BUFFER
    pla
    ldxi <RESPONSE
    ldyi >RESPONSE
    jsr PRINTS
    ldxi <IN_BUFFER
    ldyi >IN_BUFFER
    jsr PRINTS
    ldai $21
    edo TTYO
    jsr NEWLINE
    halt


PRINTS:
    stxr PRL
    styr PRH
PRINTS.LOOP:
    ldari PRL
    jeq PRINTS.RETURN
    edo TTYO
    ldar PRL
    ina
    star PRL
    jcc PRINTS.LOOP
    ldar PRH
    ina
    star PRH
    jmp PRINTS.LOOP
PRINTS.RETURN:
    rts


NEWLINE:
    ldai $0A
    edo TTYO
    ldai $0D
    edo TTYO
    rts


TEXT:
.ascii "Enter your name: "
.hex 0
RESPONSE:
.hex 0A 0D
.ascii "Hello, "
.hex 0