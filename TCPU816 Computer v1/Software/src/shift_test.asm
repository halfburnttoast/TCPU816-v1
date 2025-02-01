.alias PRL $0100
.alias PRH $0101

    rsp
    ldai $5
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
    halt