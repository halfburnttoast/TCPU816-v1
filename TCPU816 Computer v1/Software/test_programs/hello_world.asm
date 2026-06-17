@ 0

.alias TTYO $1

MAIN:   rsp
        
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
    PRINTS.LOOP:
        lsa *($3),X
        jeq PRINTS.END
        edo TTYO
        inx
        jmp PRINTS.LOOP
    PRINTS.END:
        plx
        rts

STRING1: .byte "Hello, World!", $0A, $0D, 0
STRING2: .byte "I'm the second string!", $0A, $0D, 0



