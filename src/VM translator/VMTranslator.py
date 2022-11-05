# Translates VM commands into Hack assembly code.

import os
import sys


class Parser:
    # Handles the parsing of a single .vm file and provides services for reading a VM command, unpacking the command
    # into its various components, and providing convenient access to these components.
    COMMAND_TYPE = {'add': 'C_ARITHMETIC',
                    'sub': 'C_ARITHMETIC',
                    'neg': 'C_ARITHMETIC',
                    'eq': 'C_ARITHMETIC',
                    'gt': 'C_ARITHMETIC',
                    'lt': 'C_ARITHMETIC',
                    'and': 'C_ARITHMETIC',
                    'or': 'C_ARITHMETIC',
                    'not': 'C_ARITHMETIC',
                    'push': 'C_PUSH',
                    'pop': 'C_POP',
                    'label': 'C_LABEL',
                    'goto': 'C_GOTO',
                    'if-goto': 'C_IF',
                    'function': 'C_FUNCTION',
                    'return': 'C_RETURN',
                    'call': 'C_CALL'
                    }

    def __init__(self, arg):
        # Opens the input file and prepares to parse it.
        self.vm_file = open(arg)
        self.vm_line = None
        self.advance()

    def has_more_lines(self):
        # Returns 'True' if there are more instructions in the .asm input file.
        if self.vm_line:
            return True
        self.vm_file.close()
        return False

    def advance(self):
        # Reads the next instruction from the input and makes it the current instruction, ignoring comments and
        # whitespace.
        line = self.vm_file.readline()

        if line.startswith("//") or line == "\n":  # '// comment' or '\n'
            self.advance()
            return
        elif line:  # 'code'
            self.vm_line = line.strip()
        else:  # '' (EOF)
            self.vm_line = None

    def command_type(self):
        # Returns a constant representing the type of the current command.
        vm_command = self.vm_line.split()[0]
        return Parser.COMMAND_TYPE[vm_command]

    def arg1(self):
        # Returns the first argument of the current command.
        if self.command_type() == "C_ARITHMETIC":
            return self.vm_line.split()[0]
        return self.vm_line.split()[1]

    def arg2(self):
        # Returns the second argument of the current command.
        return self.vm_line.split()[2]


class CodeWriter:
    # Translates a parsed VM command into Hack assembly code.
    #
    # command_groups, math_logic_template, and insert_dict used by arithmetic and logic commands. segment_groups,
    # push_pop_template, base_address, and pointer_address used by push/pop commands. end_loop used by close() when
    # argument is single file
    COMMAND_GROUP = {'add': 'add_sub_and_or',
                     'sub': 'add_sub_and_or',
                     'and': 'add_sub_and_or',
                     'or': 'add_sub_and_or',
                     'neg': 'neg_not',
                     'not': 'neg_not',
                     'eq': 'eq_gt_lt',
                     'gt': 'eq_gt_lt',
                     'lt': 'eq_gt_lt'
                     }
    MATH_LOGIC_TEMPLATE = {'add_sub_and_or': ('@SP\n'
                                              'AM=M-1\n'
                                              'D=M\n'
                                              'A=A-1\n'
                                              'M=insert\n'
                                              ),
                           'neg_not': ('@SP\n'
                                       'A=M-1\n'
                                       'M=insert\n'
                                       ),
                           'eq_gt_lt': ('@SP\n'
                                        'AM=M-1\n'
                                        'D=M\n'
                                        'A=A-1\n'
                                        'D=M-D\n'
                                        '@TRUE.index\n'
                                        'D;insert\n'
                                        'D=0\n'
                                        '@CONT.index\n'
                                        '0;JMP\n'
                                        '(TRUE.index)\n'
                                        'D=-1\n'
                                        '(CONT.index)\n'
                                        '@SP\n'
                                        'A=M-1\n'
                                        'M=D\n'
                                        )
                           }
    ASM_INSERT = {'add': 'D+M',
                  'sub': 'M-D',
                  'and': 'D&M',
                  'or': 'D|M',
                  'neg': '-M',
                  'not': '!M',
                  'eq': 'JEQ',
                  'gt': 'JGT',
                  'lt': 'JLT'
                  }
    SEGMENT_GROUPS = {'argument': 'argument_local_this_that_temp',
                      'local': 'argument_local_this_that_temp',
                      'this': 'argument_local_this_that_temp',
                      'that': 'argument_local_this_that_temp',
                      'temp': 'argument_local_this_that_temp',
                      'static': 'static_pointer',
                      'constant': 'constant',
                      'pointer': 'static_pointer'
                      }
    PUSH_POP_TEMPLATE = {('C_PUSH', 'argument_local_this_that_temp'): ('@address\n'
                                                                       'D=computation\n'
                                                                       '@index\n'
                                                                       'A=D+A\n'
                                                                       'D=M\n'
                                                                       '@SP\n'
                                                                       'M=M+1\n'
                                                                       'A=M-1\n'
                                                                       'M=D\n'
                                                                       ),
                         ('C_POP', 'argument_local_this_that_temp'): ('@address\n'
                                                                      'D=computation\n'
                                                                      '@index\n'
                                                                      'D=D+A\n'
                                                                      '@SP\n'
                                                                      'AM=M-1\n'
                                                                      'D=D+M\n'
                                                                      'A=D-M\n'
                                                                      'M=D-A\n'
                                                                      ),
                         ('C_PUSH', 'static_pointer'): ('@address\n'
                                                        'D=M\n'
                                                        '@SP\n'
                                                        'M=M+1\n'
                                                        'A=M-1\n'
                                                        'M=D\n'
                                                        ),
                         ('C_POP', 'static_pointer'): ('@SP\n'
                                                       'AM=M-1\n'
                                                       'D=M\n'
                                                       '@address\n'
                                                       'M=D\n'
                                                       ),
                         ('C_PUSH', 'constant'): ('@index\n'
                                                  'D=A\n'
                                                  '@SP\n'
                                                  'M=M+1\n'
                                                  'A=M-1\n'
                                                  'M=D\n'
                                                  )
                         }
    BASE_ADDRESS = {'argument': 'ARG',
                    'local': 'LCL',
                    'this': 'THIS',
                    'that': 'THAT',
                    'temp': '5'
                    }
    POINTER_ADDRESS = {'0': 'THIS',
                       '1': 'THAT'
                       }
    END_LOOP = ('(END_LOOP)\n'
                '@END_LOOP\n'
                '0;JMP\n'
                )

    def __init__(self, argument):
        # Opens an output file and prepares to write into it.
        #
        # Determine full path of output file whether argument is file path (ends with '.vm') or directory path. If
        # argument is directory ('\Directory'), then filename is 'Directory.asm', and full path is
        # '\Directory\Directory.asm'.
        #
        # Single file bool used by close() to determine need for asm loop and before
        # bootstrap() to determine need for bootstrap code. (Only add end loop when single file, and bootstrap when
        # directory.)
        #
        # Filename is used by push/pop commands for static variable names. Symbol index is used by arithmetic commands
        # and is set by comparison commands (eq, gt, lt). Function name is used by branching commands (label, goto,
        # if) and is set by function command. Call index dictionary is used by call command for return address.
        if argument.endswith('.vm'):
            full_path = argument[:-2] + "asm"
            self.is_single_file = True
        else:
            filename = os.path.basename(argument) + '.asm'
            full_path = os.path.join(argument, filename)
            self.is_single_file = False

        self.asm_file = open(full_path, "w")
        self.filename, self.function_name = None, None
        self.symbol_index = 0
        self.call_index = {}

        if not self.is_single_file:
            self.write_bootstrap()

    def set_filename(self, full_path):
        # Informs that the translation of a new VM file has started. Removes path and extension:
        # '\Directory\Filename.vm' --> 'Filename'.
        self.filename = os.path.basename(full_path)[:-3]

    def write_bootstrap(self):
        # Writes the bootstrap code to the output file.
        asm_code = ('@256\n'
                    'D=A\n'
                    '@SP\n'
                    'M=D\n'
                    )
        self.asm_file.write(asm_code)

        self.write_call('Sys.init', '0')

    def write_arithmetic(self, command):
        # Writes to the output file the assembly code that implements the given arithmetic-logical command.
        #
        # 1) Get command group using command; 2) get asm code template using command group; 3) get asm insert (comp or
        # jump) using command; 4) insert comp or jump into asm code template.
        #
        # If the command is a comparison command (eq, gt, lt), then insert the symbol index into asm code template and
        # increment the symbol index.
        command_group = CodeWriter.COMMAND_GROUP[command]
        template = CodeWriter.MATH_LOGIC_TEMPLATE[command_group]
        insert = CodeWriter.ASM_INSERT[command]
        asm_code = template.replace('insert', insert)

        if command_group == 'eq_gt_lt':
            asm_code = asm_code.replace("index", str(self.symbol_index))
            self.symbol_index += 1

        self.asm_file.write(asm_code)

    def write_push_pop(self, command, segment, index):
        # Writes to the output file the assembly code that implements the given push or pop command.
        #
        # 1) Get the segment group using the segment argument variable. 2) Get the asm code template using the command
        # argument variable and the segment group. 3) If the segment group is 'argument_local_this_that_temp,'
        # then get the address and computation and replace 'address', 'computation', and 'index' in the template.
        # If the segment is 'static' or 'pointer', then get the address and replace 'address' in the template. If the
        # segment is 'constant,' then replace 'index' in the template.
        segment_group = CodeWriter.SEGMENT_GROUPS[segment]
        template = CodeWriter.PUSH_POP_TEMPLATE[(command, segment_group)]

        if segment_group == 'argument_local_this_that_temp':
            address = CodeWriter.BASE_ADDRESS[segment]
            computation = 'A' if segment == 'temp' else 'M'
            asm_code = template.replace('address', address).replace('computation', computation).replace('index', index)

        elif segment == 'static':
            address = f'{self.filename}.{index}'
            asm_code = template.replace('address', address)

        elif segment == 'constant':
            asm_code = template.replace('index', index)

        else:   # elif segment == 'pointer':
            address = CodeWriter.POINTER_ADDRESS[index]
            asm_code = template.replace('address', address)

        self.asm_file.write(asm_code)

    def write_label(self, label):
        # Writes to the output file the assembly code that affects the label command, labelling the current location
        # in the function's code.
        goto_label = f'{self.function_name}${label}'
        asm_code = f'({goto_label})\n'

        self.asm_file.write(asm_code)

    def write_goto(self, label):
        # Writes to the output file the assembly code that affects the goto command, causing execution to continue
        # from the location marked by the label.
        goto_label = f'{self.function_name}${label}'
        asm_code = (f'@{goto_label}\n'
                    '0;JMP\n'
                    )
        self.asm_file.write(asm_code)

    def write_if(self, label):
        # Writes to the output file the assembly code that affects the if-goto command, causing execution to continue
        # from the location marked by the label if the condition 'popped value != 0' is met.
        goto_label = f'{self.function_name}${label}'
        asm_code = ('@SP\n'
                    'AM=M-1\n'
                    'D=M\n'
                    f'@{goto_label}\n'
                    'D;JNE\n'
                    )
        self.asm_file.write(asm_code)

    def write_function(self, function_name, n_vars):
        # Writes to the output file the assembly code that affects the function command, initializing the local
        # variables of the callee.
        asm_code = f'({function_name})\n'

        for i in range(int(n_vars)):
            asm_code += self.PUSH_POP_TEMPLATE[('C_PUSH', 'constant')].replace('index', '0')

        self.asm_file.write(asm_code)
        self.function_name = function_name

    def write_call(self, function_name, n_args):
        # Writes to the output file the assembly code that affects the call command, saving the frame of the caller
        # on the stack and jumping to execute the callee.
        if function_name in self.call_index:
            self.call_index[function_name] += 1
        else:
            self.call_index[function_name] = 0

        return_address = f'{function_name}$ret.{self.call_index[function_name]}'

        asm_code = (f'@{return_address}\n'  # push return_address
                    'D=A\n'
                    '@SP\n'
                    'M=M+1\n'
                    'A=M-1\n'
                    'M=D\n'
                    '@LCL\n'  # push LCL
                    'D=M\n'
                    '@SP\n'
                    'M=M+1\n'
                    'A=M-1\n'
                    'M=D\n'
                    '@ARG\n'  # push ARG
                    'D=M\n'
                    '@SP\n'
                    'M=M+1\n'
                    'A=M-1\n'
                    'M=D\n'
                    '@THIS\n'  # push THIS
                    'D=M\n'
                    '@SP\n'
                    'M=M+1\n'
                    'A=M-1\n'
                    'M=D\n'
                    '@THAT\n'  # push THAT
                    'D=M\n'
                    '@SP\n'
                    'M=M+1\n'
                    'A=M-1\n'
                    'M=D\n'
                    '@SP\n'  # ARG = SP-5-nArgs
                    'D=M\n'
                    '@5\n'
                    'D=D-A\n'
                    f'@{n_args}\n'
                    'D=D-A\n'
                    '@ARG\n'
                    'M=D\n'
                    '@SP\n'  # LCL = SP
                    'D=M\n'
                    '@LCL\n'
                    'M=D\n'
                    f'@{function_name}\n'  # goto entry_label of function
                    '0;JMP\n'
                    f'({return_address})\n'  # return_address label
                    )
        self.asm_file.write(asm_code)

    def write_return(self):
        # Writes to the output file the assembly code that affects the return command, copying the return value to
        # the top of hte caller's working stack, reinstating the segment pointers of the caller, and jumping to
        # execute the latter from the return address onward.
        asm_code = ('@LCL\n'  # R13 (frame) = LCL
                    'D=M\n'
                    '@R13\n'
                    'M=D\n'
                    '@5\n'  # R14 (return_address) = *(R13-5)
                    'A=D-A\n'
                    'D=M\n'
                    '@R14\n'
                    'M=D\n'
                    '@SP\n'  # *ARG = pop()
                    'AM=M-1\n'
                    'D=M\n'
                    '@ARG\n'
                    'A=M\n'
                    'M=D\n'
                    'D=A\n'  # SP = ARG+1
                    '@SP\n'
                    'M=D+1\n'
                    '@R13\n'  # THAT = *(frame-1)
                    'AM=M-1\n'
                    'D=M\n'
                    '@THAT\n'
                    'M=D\n'
                    '@R13\n'  # THIS = *(frame-2)
                    'AM=M-1\n'
                    'D=M\n'
                    '@THIS\n'
                    'M=D\n'
                    '@R13\n'  # ARG = *(frame-3)
                    'AM=M-1\n'
                    'D=M\n'
                    '@ARG\n'
                    'M=D\n'
                    '@R13\n'  # LCL = *(frame-4)
                    'AM=M-1\n'
                    'D=M\n'
                    '@LCL\n'
                    'M=D\n'
                    '@R14\n'  # goto return_address
                    'A=M\n'
                    '0;JMP\n'
                    )
        self.asm_file.write(asm_code)

    def close(self):
        # Closes output file.
        if self.is_single_file:
            self.asm_file.write(CodeWriter.END_LOOP)
        self.asm_file.close()


class VMTranslator:
    # Drives translation process using Parser and CodeWriter.
    def __init__(self):
        # Argument is either command line argument (if specified) or current working directory (if not). If argument
        # is .vm file, initialize code_writer and translate .vm file. If argument is directory with .vm files in it,
        # initialize code_writer, and translate each .vm file in directory. Lastly, close output file.
        if len(sys.argv) == 2:
            arg = sys.argv[1]
        else:
            arg = os.getcwd()

        self.code_writer = CodeWriter(arg)

        if arg.endswith('.vm'):
            self.translate(arg)
        else:
            for file in os.listdir(arg):
                if not file.endswith('.vm'):
                    continue

                full_path = os.path.join(arg, file)
                self.translate(full_path)

        self.code_writer.close()

    def translate(self, full_path):
        # Set filename, initialize parser, and translate .vm file.
        self.code_writer.set_filename(full_path)
        parser = Parser(full_path)

        while parser.has_more_lines():

            command_type = parser.command_type()

            if command_type == 'C_PUSH' or command_type == 'C_POP':
                segment = parser.arg1()
                index = parser.arg2()
                self.code_writer.write_push_pop(command_type, segment, index)

            elif command_type == 'C_ARITHMETIC':
                command = parser.arg1()
                self.code_writer.write_arithmetic(command)

            elif command_type == 'C_LABEL':
                label = parser.arg1()
                self.code_writer.write_label(label)

            elif command_type == 'C_GOTO':
                label = parser.arg1()
                self.code_writer.write_goto(label)

            elif command_type == 'C_IF':
                label = parser.arg1()
                self.code_writer.write_if(label)

            elif command_type == 'C_FUNCTION':
                function_name = parser.arg1()
                n_vars = parser.arg2()
                self.code_writer.write_function(function_name, n_vars)

            elif command_type == 'C_CALL':
                function_name = parser.arg1()
                n_args = parser.arg2()
                self.code_writer.write_call(function_name, n_args)

            elif command_type == 'C_RETURN':
                self.code_writer.write_return()

            parser.advance()


VMTranslator()
