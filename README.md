# The Elements of Computing Systems #
### Building a modern computer from first principles ###

Professors Noam Nisan and Shimon Schocken function as system architects and guide students through a series of hardware and software implementation projects. Together the projects form a general-purpose computer system and modern software hierarchy capable of running programs written in a high-level, object-based language.

The course is colloquially known as "Nand to Tetris" since it begins with an elementary Nand gate, and ends with a computer capable of running a game of Tetris.

I primarily referenced [The Elements of Computing Systems: Building a Modern Computer from First Principles, Second Edition](https://mitpress.mit.edu/9780262539807/the-elements-of-computing-systems/) to complete the projects. This repo contains the [assembler](https://github.com/zachariahy/The-Elements-of-Computing-Systems/tree/main/src/Hack%20assembler), [VM translator](https://github.com/zachariahy/The-Elements-of-Computing-Systems/tree/main/src/VM%20translator), and [compiler](https://github.com/zachariahy/The-Elements-of-Computing-Systems/tree/main/src/Jack%20compiler).

## Overview ##

#### Hardware Platform: ####

- _Boolean logic_: the professors present a simple Hardware Description Language (HDL), with which we build a set of elementary logic gates from primitive Nand gates.
- _Boolean arithmetic_: we use elementary logic gates to build a set of combinational gates, including a family of adder chips, leading to the construction of an Arithmetic-Logic Unit (ALU).
- _Memory_: we build a memory hierarchy, from single-bit cells to registers to RAM units of arbitrary size.
- _Machine language_: the professors introduce an instruction set and abstract computer architecture. We write some low-level interactive programs in assembly language and execute them locally on a supplied CPU emulator.
- _Computer architecture_: we build a CPU and integrate all of the previously built chips into a computer platform named _Hack_, capable of executing binary machine code.
- [_Assembler_](https://github.com/zachariahy/The-Elements-of-Computing-Systems/tree/main/src/Hack%20assembler): We develop an assembler to translate symbolic machine code to binary machine code.

#### Software Hierarchy: ####

- [_Virtual machine_](https://github.com/zachariahy/The-Elements-of-Computing-Systems/tree/main/src/VM%20translator): the professors present a simple VM language modeled after Java's JVM. We write a JRE-like program that translates VM commands into assembly code. Then, we extend the translator into a complete VM translator.
- _High-level language_: Professors introduce _Jack_, a simple, high-level, object-oriented, Java-like language. We implement an interactive program in Jack and run it on the computer platform (using executable versions of the compiler and OS).
- [_Compiler_](https://github.com/zachariahy/The-Elements-of-Computing-Systems/tree/main/src/Jack%20compiler): Students build a syntax analyzer (tokenizer and parser) for the Jack language using a proposed software architecture and API. We then extend the syntax analyzer into a full-scale compiler that translates Jack programs into VM code.
- _Operating system_: Students build the OS in Jack using various memory management, algebraic, and geometric algorithms, to close gaps between the Jack language and the Hack platform.

## Limitations ##

The course pays little attention to optimization except in the Jack OS. In addition, it assumes error-free inputs for the software projects, eliminating the need for exception handling.

The minimal feature set of the Jack language dramatically simplifies compilation and is sufficient for developing simple interactive programs. The language could also be extended beyond the requirements of the course to provide ```for``` statements or ```switch``` statements. That said, Jack lacks many standard features. It is a weakly typed language and does not support inheritance or the distinction between public and private class members, for example.

The Jack OS likewise provides a subset of essential services found in typical operating systems. It functions primarily as an extension of the Jack language, offering mathematical operations, abstract data types, input functions, and textual and graphical output capabilities not implemented in the hardware. The system-oriented services of the OS include memory management and, to some extent, I/O device drivers. The OS does not support concurrency for multi-threading, a file system for permanent storage, a command-line or windows interface, security, or communications.

## About the professors ##

[Shimon Schocken](https://www.runi.ac.il/en/faculty/schocken/) is a professor at and founding dean of the Efi Arazi School of Computer Science at Reichman University. He has taught at Harvard, Stanford, and Princeton University's School of Engineering and Applied Science.

[Noam Nisan](https://www.cs.huji.ac.il/~noam/) is a professor in the School of Computer Science and Engineering of the Hebrew University of Jerusalem.
