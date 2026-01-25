from copy import copy

class Register: 

    def __init__(self, objs):
        self.objs = objs 
        self.expressions = {} # map<char,list<int>> 
        self.index_ptr = 0
        
    def get_noc(self):
        return len(self.expressions)
    
    def add_constant_expr(self,expr): 
        if expr in self.expressions: 
            self.expressions[expr].append(self.index_ptr)
        else: 
            self.expressions[expr] = [self.index_ptr]
        self.index_ptr += 1

    def load_values(self, ls): 

        if len(ls) != len(self.expressions): 
            raise ValueError("Not Valid list for the truth table!")
        
        iterate_index = 0

        for list_of_indexes in self.expressions.values():
            for index in list_of_indexes:
                self.objs[index].value = ls[iterate_index]
            iterate_index += 1

    def get_headers(self):
        return list(self.expressions.keys())
    
    def reset(self):
        self.objs = []
        self.expressions = {}
        self.index_ptr = 0

    def order(self, string): 
        
        ls = sorted([i for i in string if i.isalpha()])        
        for i in ls:
                self.expressions[i] = []
        


reg_global = Register([])