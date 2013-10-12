@mov r0, pc
@mov r0, #0x08a00000
@add r0, #1
@bx r0
.thumb
.align 2
@. = 0xa00000
push {lr}
ldr r0, SCRIPT_ADRESS
bl SCRIPT_ROUTINE
pop {pc}

SCRIPT_ROUTINE:
ldr r1, SCRIPT_EXECUTER
Bx r1

.align 2
SCRIPT_ADRESS: .word 0x02f30000
SCRIPT_EXECUTER: .word 0x08098EF9
