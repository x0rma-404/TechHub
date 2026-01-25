from .logic import * 


def get_prev_is_letter(index, input, size): 
    index -= 1 
    if index >= 0 and index < size-1: 
        return input[index].isalpha() 
    return False 

def find_braces(ls):

    for i in range(len(ls)-1,-1,-1):
        if ls[i] == '(':
            for j in range(i+1,len(ls)):
                if ls[j] == ')':
                    return (i,j)

def replace_with(ls,begin,end,value): # note : it replaces a range with just one variable
    
    insert_index = begin 

    for i in range(begin,end):
        del ls[insert_index]
    
    ls.insert(insert_index, value)

def single_replace(ls, index, new_value):

    ls.pop(index)
    ls.insert(index,new_value)

def lex_input(input):

    input = input.strip()

    tokens = []
    prev_is_ce = False 
    for i in input: 
        if i.isalpha(): 
            tokens.append(ConstExpr(i,False))
        elif i == '1':
            tokens.append(true())
        elif i == '0':
            tokens.append(false())
        else :
            tokens.append(i)

    return tokens

def lex_and_consider_adjacents(input):

    # This input does the same as 
    # the function above, but it actually considers
    # AB as A*B automatically

    input = input.strip()
    tokens = []
    size_of_input = len(input)
    for i in range(len(input)): 
        if input[i].isalpha(): 
            if get_prev_is_letter(i,input,size_of_input):
                tokens.append('*')
            tokens.append(ConstExpr(input[i],False))
        elif input[i] == '1':
            tokens.append(true())
        elif input[i] == '0':
            tokens.append(false())
        else:
            if input[i] == '!':
                if get_prev_is_letter(i,input,size_of_input):
                    tokens.append('*')
                tokens.append('!')
            else:
                tokens.append(input[i])

    return tokens

def create_ast(tokens):

    tree = AbstractSyntaxTree(None)

    if len(tokens) == 0:
        return 

    # eval paranthesises first
    # ATTENTION : USAGE WITHOUT ATTENTION MAY CAUSE RECURSIVE FAULTS!!!
    while tokens.count('(') > 0: 
        res = find_braces(tokens)
        lparstart, rparstart = res[0], res[1]
        result = create_ast(tokens[lparstart+1:rparstart])
        replace_with(tokens,lparstart,rparstart+1,result)

    # this part of function assumes that 
    # there is no paranthesis 
    # means there is just one for after and (no paranthesis ^__^)

    # chaining !!!!!

    # eval NOTs first 
    count_not  = tokens.count('!')
    for i in range(len(tokens) - count_not):
        if tokens[i] == '!':
            not_obj = Not(tokens[i+1])
            replace_with(tokens,i,i+2,not_obj)

    i = 0
    and_count = tokens.count('*')
    and_limit = len(tokens) - 2*and_count 
    while i <= and_limit:
        if tokens.count('*') == 0:
            break
        if tokens[i] == '*':
            and_obj = And(tokens[i-1], tokens[i+1])
            replace_with(tokens,i-1, i+2, and_obj)
            i -= 1
        i+=1

    # eval ORs then 
    i = 0
    or_count = tokens.count('+')
    or_limit = len(tokens) - 2*or_count 
    while i <= or_limit:
        if tokens.count('+') == 0:
            break
        if tokens[i] == '+':
            or_obj = Or(tokens[i-1], tokens[i+1])
            replace_with(tokens,i-1, i+2, or_obj)
            i -= 1
        i+=1

    # eval XORs
    i = 0
    xor_count = tokens.count('^')
    xor_limit = len(tokens) - 2*xor_count 
    while i <= xor_limit:
        if tokens.count('^') == 0:
            break
        if tokens[i] == '^':
            xor_obj = Xor(tokens[i-1], tokens[i+1])
            replace_with(tokens,i-1, i+2, xor_obj)
            i -= 1
        i+=1 

    # eval IMPLICATIONs
    # i = 0
    # implication_count = tokens.count('$')
    # implication_limit = len(tokens) - 2*implication_count 
    # while i <= implication_limit:
    #     if tokens.count('$') == 0:
    #         break
    #     if tokens[i] == '$':
    #         impl_obj = Implication(tokens[i-1], tokens[i+1])
    #         replace_with(tokens,i-1, i+2, impl_obj)
    #         i -= 1
    #     i+=1

    # FOR IMPLICATIONS, ITERATION HAPPENS IN REVERSE ORDER BECAUSE, IN LOGIC
    # A->B->C IS INTERPRETED AS A->(B->C)

    start = len(tokens) - 1
    for i in range(start, -1, -1): 
        if tokens.count('$') == 0: 
            break
        
        if tokens[i] == '$': 
            impl_obj = Implication(tokens[i-1], tokens[i+1])
            replace_with(tokens, i-1, i+2, impl_obj)
            i += 1

    # eval EQUIVALENCEs
    i = 0
    eq_count = tokens.count('#')
    eq_limit = len(tokens) - 2*eq_count 
    while i <= eq_limit:
        if tokens.count('#') == 0:
            break
        if tokens[i] == '#':
            eq_obj = Equivalence(tokens[i-1], tokens[i+1])
            replace_with(tokens,i-1, i+2, eq_obj)
            i -= 1
        i+=1

    tree.set_expr(tokens[0])

    return tree     

