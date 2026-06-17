@ 0

.alias TTYO $1
.alias PRL $FE00
.alias PRH $FE01

MAIN:
        rsp
        
        ; Print STRING1
        phi #>STRING1
        phi #<STRING1
        jsr PRINTS
        spa #$2
        
        ; Print STRING2
        phi #>STRING2
        phi #<STRING2
        jsr PRINTS
        spa #$2
        
        ; infinite loop
        halt

PRINTS:
        phx
        ldx #$0
        lsa #$3
        sta PRL
        lsa #$4
        sta PRH
    PRINTS.LOOP:
        lda (PRL),X
        jeq PRINTS.END
        edo TTYO
        inx
        jmp PRINTS.LOOP
    PRINTS.END:
        plx
        rts

STRING1:
.ascii "Hello, World!"
.hex $0A, $0D, 0
STRING2:
.ascii "I'm the second string!"
.hex $0A, $0D, 0



