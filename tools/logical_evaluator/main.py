from .algo import * 
from .truth_table import *
import shutil

TERM_WIDTH = shutil.get_terminal_size().columns
LINE_STR = (("").join(['-' for i in range(TERM_WIDTH-1)])).strip()

HEADER_STR = LINE_STR + """
\nCopyright (C) 2025
Logical Evaluator by Hazret Hasanov
Rules: 
    - DO NOT TRY TO HACK THE MACHINE!
    - USE * FOR LOGICAL AND (YOU CAN USE ADJACENT NOTATION BTW)
    - USE + FOR LOGICAL OR
    - USE ^ FOR LOGICAL XOR 
    - USE -> FOR IMPLICATION 
    - USE <=> FOR EQIUVALENCE
    - NOTE: VARIABLES ARE CASE SENSETIVE!
    - NOTE: WRONG USAGE MAY LEAD TO FALSE RESULTS, BE RESPONSIBLE! 
    - NOTE: BE CAREFUL WHEN USING ADJACENT NOTATION
            ABC WILL BE INTERPRETED AS A*B*C BUT AB(C) WILL NOT WORK!
            IT WORKS FOR ONLY EXPRESSIONS LIKE AB OR !AB OR !A!B!C 

ATTENTION: 
    - USE 'r' or 'restart' to enter new expression
    - USE 'e' or 'exit' to exit the program 
    - USE 'p' or 'print' to print truth table of expression
    - USE 'h' or 'help' to get more information 
    - USE 'order on/off' to get sorted truth table output
    
GOOD LUCK!\n
""" + LINE_STR 

MACRO_RED = "\x1b[31m"
MACRO_BOLD = "\x1b[1m"
MACRO_GREEN = "\x1b[32m"
MACRO_BLUE = "\x1b[34m"
MACRO_RESET = "\x1b[0m"
MACRO_YELLOW = "\x1b[33m"

def main():

    print(MACRO_GREEN,MACRO_BOLD)
    print(HEADER_STR,MACRO_RESET)

    running = True
    order = False 
    while running:

        user_in = input("Please enter the logical expression: ")
        if (user_in == 'exit'):
            running = False
            break

        user_in = user_in.replace("->","$")
        user_in = user_in.replace("<=>",'#')

        try: 
            if order: 
                reg_global.order(user_in)
            tokens = lex_and_consider_adjacents(user_in)
            z = create_ast(tokens)           

            a = TruthTable(reg_global.get_headers(),reg_global.objs,z)
            a.generate()
            a.simplify()
        
            print(MACRO_BOLD,MACRO_GREEN)
            print(a.simplified_str,MACRO_RESET)
            print()

        except TooLongError: 
            print(MACRO_RED,MACRO_BOLD)
            print("TOO MANY VARIABLES! VARIABLE LIMIT : 6",MACRO_RESET,'\n')
            reg_global.reset()
            continue

        except Exception as e: 
            print(MACRO_RED,MACRO_BOLD)
            print("INVALID!",MACRO_RESET,'\n')
            continue

        while True: 
            prompt = input("What else can I do for you? ")
            prompt = prompt.strip().split()
            if prompt == ["exit"] or prompt == ['e']: 
                running = False
                break
            elif prompt == ['r'] or prompt == ['restart']: 
                reg_global.reset()
                break
            elif prompt == ['h'] or prompt == ["help"]:
                print(MACRO_GREEN,MACRO_BOLD)
                print(HEADER_STR,MACRO_RESET)

            elif prompt == ['p'] or prompt == ['print']: 
                print(MACRO_BLUE,MACRO_BOLD)
                a.print_table()
                print(MACRO_RESET)
            elif prompt == ['order', 'on']: 
                order = True 
            elif prompt == ['order','off']:
                order = False
            else: 
                print(MACRO_RED,MACRO_BOLD)
                print("INVALID!",MACRO_RESET)
            print()

if __name__ == "__main__":
    main()
