# Translates Hack assembly code into Hack binary code.

import sys
import os


class Parser:
    # Provides convenient means for advancing through source code, skipping comments and white space, and breaking
    # each symbolic instruction into its underlying components.
    def __init__(self, arg):
        self.hack_file = open(arg)
        self.hack_line = None
        self.advance()

    def has_more_lines(self):
        # Returns 'True' if there are more instructions in the .asm input file.
        if self.hack_line:
            return True
        self.hack_file.close()
        return False

    def advance(self):
        # Reads the next instruction from the input and makes it the current instruction, ignoring comments and
        # whitespace.
        line = self.hack_file.readline()

        if line.startswith("//") or line == "\n":   # '//comment' or '\n'
            self.advance()
            return
        elif "//" in line:  # 'code // comment'
            self.hack_line = line.split('//')[0].strip()
        elif line:   # 'code'
            self.hack_line = line.strip()
        else:   # '' (EOF)
            self.hack_line = None

    def instruction_type(self):
        # Returns the type of the current instruction.
        if self.hack_line.startswith("@"):
            return "A-Instruction"
        elif "=" in self.hack_line or ";" in self.hack_line:
            return "C-Instruction"
        elif self.hack_line.startswith("("):
            return "L-Instruction"

    def symbol(self):
        # Returns the symbol from an A- or L-Instruction in the form '@symbol' or '(symbol)'.
        if self.hack_line.startswith("@"):
            return self.hack_line[1:]
        elif self.hack_line.startswith("("):
            return self.hack_line[1:-1]

    def comp(self):
        # Returns the 'comp' mnemonic from a C-Instruction in the form 'dest=comp' or 'comp;jump'.
        if "=" in self.hack_line:
            return self.hack_line.split("=")[1]
        return self.hack_line.split(";")[0]  # elif ";" in self.hack_line:

    def dest(self):
        # Returns the 'dest' mnemonic from a C-Instruction in the form 'dest=comp'.
        if "=" in self.hack_line:
            return self.hack_line.split("=")[0]
        return "null"

    def jump(self):
        # Returns the 'jump' mnemonic from a C-Instruction in the form 'comp;jump'.
        if ";" in self.hack_line:
            return self.hack_line.split(";")[1]
        return "null"


class Assembler:
    # Drives the assembly process using Parser, CODE, and symbols. (CODE and symbols dictionaries eliminate need for
    # specified Code and Symbol Table classes.) Gets the name of the input file Prog.asm and creates an output file,
    # Prog.hack, into which it will write the translated binary instructions. Then enters a loop that iterates
    # through the lines in the input file and processes them.
    #
    # For each C-instruction, parse into its fields and translate each field into its corresponding binary code. Then
    # concatenate the translated binary codes into a string consisting of 16 '0' and '1' characters and write this
    # string as the next line in the output .hack file.
    #
    # For each A-instruction of type @xxx, translate xxx into its binary representation, create a string of 16 '0'
    # and '1' characters, and write it as the next line in the output .hack file.
    CODE = {'comp': {'0': '0101010',
                     '1': '0111111',
                     '-1': '0111010',
                     'D': '0001100',
                     'A': '0110000',
                     '!D': '0001101',
                     '!A': '0110001',
                     '-D': '0001111',
                     '-A': '0110011',
                     'D+1': '0011111',
                     'A+1': '0110111',
                     'D-1': '0001110',
                     'A-1': '0110010',
                     'D+A': '0000010',
                     'D-A': '0010011',
                     'A-D': '0000111',
                     'D&A': '0000000',
                     'D|A': '0010101',
                     'M': '1110000',
                     '!M': '1110001',
                     '-M': '1110011',
                     'M+1': '1110111',
                     'M-1': '1110010',
                     'D+M': '1000010',
                     'D-M': '1010011',
                     'M-D': '1000111',
                     'D&M': '1000000',
                     'D|M': '1010101'
                     },
            'dest': {'null': '000',
                     'M': '001',
                     'D': '010',
                     'MD': '011',
                     'A': '100',
                     'AM': '101',
                     'AD': '110',
                     'AMD': '111'
                     },
            'jump': {'null': '000',
                     'JGT': '001',
                     'JEQ': '010',
                     'JGE': '011',
                     'JLT': '100',
                     'JNE': '101',
                     'JLE': '110',
                     'JMP': '111'
                     }
            }
    symbols = {'SP': '000000000000000',
               'LCL': '000000000000001',
               'ARG': '000000000000010',
               'THIS': '000000000000011',
               'THAT': '000000000000100',
               'R0': '000000000000000',
               'R1': '000000000000001',
               'R2': '000000000000010',
               'R3': '000000000000011',
               'R4': '000000000000100',
               'R5': '000000000000101',
               'R6': '000000000000110',
               'R7': '000000000000111',
               'R8': '000000000001000',
               'R9': '000000000001001',
               'R10': '000000000001010',
               'R11': '000000000001011',
               'R12': '000000000001100',
               'R13': '000000000001101',
               'R14': '000000000001110',
               'R15': '000000000001111',
               'SCREEN': '100000000000000',
               'KBD': '110000000000000'
               }

    def __init__(self):
        # Gets the .asm and .hack \path\filenames. Executes the first and second passes over the assembly code.
        if len(sys.argv) == 2:
            self.asm = sys.argv[1]
            hack = sys.argv[1][:-3] + 'hack'
        else:
            self.asm = os.getcwd()
            hack = os.getcwd()[:-3] + 'hack'

        self.first_pass()

        with open(hack, 'w') as self.hack_file:
            self.second_pass()

    def first_pass(self):
        # In the first pass, the assembler adds every label with its binary address to the symbol dictionary. The
        # binary address is determined by adding one to the current line number.
        #
        # The assembler constructs a parser and initializes the line count. For every instruction in the .asm input
        # file, if the instruction is an L-Instruction and the label is not in the symbols dictionary,
        # then the assembler adds the label with its binary address to the dictionary. If the instruction is not an
        # L-Instruction (i.e., it is an A- or C-Instruction), the assembler increments the line count.
        parser = Parser(self.asm)
        line_count = 0

        while parser.has_more_lines():
            if parser.instruction_type() == "L-Instruction" and parser.symbol() not in self.symbols:
                self.symbols[parser.symbol()] = to_binary(line_count)
            else:  # A- or C-Instruction
                line_count += 1

            parser.advance()

    def second_pass(self):
        # In the second pass, the assembler fully parses the assembly code, converts the assembly code to hack binary
        # code, and writes the hack binary code to the .hack output file. With every label having been added to the
        # symbol dictionary in the first pass, any symbol not in the dictionary must be a new variable. The assembler
        # adds every new variable with its binary address to the symbol dictionary. The binary address is determined
        # by adding 16 to the number of variables.
        #
        # The assembler constructs a parser and initializes the variable count. For every instruction in the .asm
        # input file, if the instruction is an A-Instruction, the assembler parses out the symbol or integer. If the
        # address is an integer ( numeric), then the assembler converts the address to binary. If the address is
        # symbolic (not numeric, containing letters, underscore (_), period (.), dollar sign ($), or colon (:)) and
        # not in the symbol dictionary, then it is a new variable. The assembler adds the variable with its binary
        # address to the symbol dictionary and increments the variable count. Finally, the assembler converts the
        # symbol to binary and writes the hack (binary) code to the .hack file.
        #
        # If the instruction is a C-Instruction, the assembler parses out the comp, dest, and jump symbolic
        # mnemonics, converts them to binary, and writes the hack (binary) code to the .hack output file.
        parser = Parser(self.asm)
        variable_count = 0

        while parser.has_more_lines():

            if parser.instruction_type() == "A-Instruction":
                symbol = parser.symbol()

                if symbol.isnumeric():
                    address = to_binary(symbol)

                else:  # if address is symbol
                    if symbol not in self.symbols:
                        self.symbols[symbol] = to_binary(variable_count + 16)
                        variable_count += 1

                    address = self.symbols[symbol]

                self.hack_file.write('0' + address + '\n')

            elif parser.instruction_type() == "C-Instruction":

                comp = self.CODE['comp'][parser.comp()]
                dest = self.CODE['dest'][parser.dest()]
                jump = self.CODE['jump'][parser.jump()]

                self.hack_file.write('111' + comp + dest + jump + '\n')

            parser.advance()


def to_binary(string):
    # Returns a 15-bit word from a numeric string.
    binary = bin(int(string)).replace("0b", "")
    binary = binary[::-1]  # reverse array
    while len(binary) < 15:  # make word proper bit length
        binary += '0'
    binary = binary[::-1]  # re-reverse array
    return binary


Assembler()
