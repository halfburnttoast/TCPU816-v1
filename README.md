# TCPU816 - Version 1

This is the official repository for my TCPU816, 8-bit, homebrew computer. The computer is a completely custom architecture using 74-series logic gates and EEPROMs. 

The overall goals of this project were to:
* Minimize the chip count.
* Use the fewest EEPROM's possible.
* Avoid using PLAs, CPLDs, and microcontrollers. 
* Maximize stability and operating speed.
* Leave the most amount of RAM possible to the user.
* Make the project fully open-source for others to tinker with and learn from.

## To Do (in no particular order)

* Create standalone emulator for this computer (in C/Rust/Python/etc...)
* Improve the assembler to allow for a more 6502-style syntax (rather than relying on opcode names to define the variants).
* Research adding interrupts to the computer and what kinds of changes would need to happen.
* See the TODO.docx for bugs and improvements. This can be found in 'TCPU816 Computer v1/Hardware/TODO.docx'.

## Purpose

I've had a strong interest in computer design since I was a teenager and had developed multiple CPU implementations in software. But, I've always had a dream of making my own computer from scratch on real hardware. 

The project has been a great learning experience and challenge. In several ways, it let me break away from traditional CPU architecture and test out experimental designs (specifically, minimizing buffer registers and repurposing the MAR to increase efficiency).

## Features and shortcomings
I've tried to keep this computer streamlined and minimalist, focusing on balancing a low chip count and efficiency. But, focusing on one design philosophy usually excludes the other. So, after careful design, the computer has taken the following form:

* Rich, complex instruction set comparable to the 65C02 (but not binary compatible).
* Heavy optimization of the sequencing logic to allow the microcode to fit onto just two EEPROMs.
* Internal memory and IO separation. The external IO exists on a separate address space from the internal memory. This preserves the usable RAM space while allowing the IO cards to make use of the full 16-bit address bus. This also helps reduce address decoding logic. 
* Minimal ROM space. In order to maximize the available RAM, the ROM is limited t a 2Kb block at the beginning of the memory address space. The intention is that this 2Kb block will contain a small monitor and/or bootloader. The actual program storage will be from an SD card on the external bus. 
* Multi-phase clock generation. The phases allow for proper timing between events on the board to eliminate race conditions. It also allows for faster operating speeds overall because it allows multiple conflicting microinstructions to happen during the same CPU cycle without threatening the stability.

There are some pitfalls with this design, however:

* Due to the minimalist ALU design, logic operations take a lot longer to run.
* The computer does not support interrupts at all. This may be something that can be addressed later on. But, for now, there is no clean solution for adding interrupt support. For now, IO is done through polling.
* The design of the address controller limits the possible operating frequency to the maximum response time of the RAM and ROM. This is okay for me because I don't expect (or need) this computer to run any faster than around 3.3MHz. But, the design decisions for this computer make the architecture difficult to scale upwards.

## Licensing 

Licensing hardware is notoriously difficult. Ideally, I'd like the software to be under the GPLv2 license and the hardware to be under the CERN-OHL-S-2.0 license. 

I wouldn't be able to do all this without the vast open-source resources available for electrical engineering and computer design, a lot of which is open source. So, this is my contribution back to that. Hopefully this computer can serve as a learning tool. But, even if the design just gives you an idea or a different way to look at computer design, that's good enough for me!

I'd appreciate a reference if you build off of this design and encourage you to share your improvements back with the community. 

