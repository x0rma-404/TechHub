from copy import copy
from .sast3 import * 
from .register import * 

class TooLongError(BaseException): 

    def __init__(self): 
        pass 

class TruthTableRow:

    def __init__(self,ls,value,literals):
        self.literals = literals # literals (letters)
        self.ls = copy(ls) # booleans
        self.value = value # output of tree.eval()
        self.simplified = [False for i in range(len(self.literals))]

    def get_index_for_tt(self,index,tt_index): 

        if self.ls[index] == True:
            return tt_index - pow(2,len(self.literals) - index -1)
        else:
            return tt_index + pow(2,len(self.literals) - index - 1)
        
    def delete_index(self,index):
        self.simplified[index] = True 
        
    def str(self): 

        result = []
        sym = '*'

        for i in range(len(self.literals)): 
            if not self.simplified[i]: 
                result.append(self.literals[i] if self.ls[i] else ("!"+self.literals[i]))
                
        result = sym.join(result)
        return result


class TruthTable: 

    def __init__(self, headers, list_by_ref,tree):

        self.headers =  headers 
        self.ce_count = len(headers)
        self.objects = list_by_ref
        self.tree = tree 
        self.bool_values = [False for i in range(len(self.headers))]
        self.rows = []
        self.data = [copy(self.bool_values)]
        self.simplified_str = ""
        self._powered = pow(2,self.ce_count)
        self.truth_result = None

    def generate(self): 
        
        reg_global.load_values(self.bool_values)
        self.rows.append(TruthTableRow(self.bool_values,self.tree.eval(),self.headers))

        for i in range(1,pow(2,self.ce_count)):

            for j in range(self.ce_count):
                if i % pow(2,self.ce_count-j-1) == 0:
                    self.bool_values[j] = not self.bool_values[j] 

            reg_global.load_values(self.bool_values)
            self.rows.append(TruthTableRow(self.bool_values,self.tree.eval(),self.headers))

    def simplify(self):

        ls = []
        for i in self.rows:
            ls.append(i.value)

        self.truth_result = ls

        if ls.count(True) == len(ls):
            self.simplified_str = '1'
            return
        elif ls.count(False) == len(ls):
            self.simplified_str = '0'
            return 
        else: 
            ls_for_sast = []
            if len(self.headers) >= 7: 
                raise TooLongError()

            for i in self.rows: 
                if i.value: 
                    ls_for_AE = []
                    for j in range(len(self.headers)): 
                        ls_for_AE.append(CE(self.headers[j],not i.ls[j]))
                    ls_for_sast.append(AndExpr(ls_for_AE))

            sast = ExtendedSast2(SAST(ls_for_sast).simplified)
            self.simplified_str =  sast.simplified            
            return 
        
    def print_table(self): 

        print()

        for i in self.headers: 
            print(" " +i + " |",end='')
        print(" X |")

        for i in range(len(self.headers)+2):
            print("---",end="")
        print()

        for i in self.rows:
            for j in i.ls: 
                if j: 
                    print(" 1 |",end="")
                else:
                    print(" 0 |",end="")
            if i.value: 
                print(' 1 |')
            else: 
                print(' 0 |')
        
