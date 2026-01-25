from .register import * 

class Not: 

    def __init__(self, expr):
        self.expr = expr

        if isinstance(self.expr,ConstExpr):
            reg_global.objs.append(self.expr)
            reg_global.add_constant_expr(self.expr.symbol)

    def eval(self):
        return not self.expr.eval()
    
    def __str__(self):

        return "Not Expression"
    
class And:
    
    def __init__(self, lval, rval):
        self.lval = lval
        self.rval = rval 

        if isinstance(self.lval,ConstExpr):
            reg_global.objs.append(self.lval)
            reg_global.add_constant_expr(self.lval.symbol)

        if isinstance(self.rval,ConstExpr):
            reg_global.objs.append(self.rval)
            reg_global.add_constant_expr(self.rval.symbol)

    def eval(self):
        return self.lval.eval() and self.rval.eval()
    
    def __str__(self):
        return "And expression "
    
class Xor:

    def __init__(self,lval,rval):
        self.lval = lval
        self.rval = rval

        if isinstance(self.lval,ConstExpr):
            reg_global.objs.append(self.lval)
            reg_global.add_constant_expr(self.lval.symbol) 

        if isinstance(self.rval,ConstExpr):
            reg_global.objs.append(self.rval)
            reg_global.add_constant_expr(self.rval.symbol)

    def eval(self):
        return (not self.lval.eval() and self.rval.eval()) or (not self.rval.eval() and self.lval.eval()) 
    
class Or:

    def __init__(self,lval, rval):
        self.lval = lval 
        self.rval = rval 

        if isinstance(self.lval,ConstExpr):
            reg_global.objs.append(self.lval)
            reg_global.add_constant_expr(self.lval.symbol)

        if isinstance(self.rval,ConstExpr):
            reg_global.objs.append(self.rval)
            reg_global.add_constant_expr(self.rval.symbol)

    def eval(self): 
        return self.lval.eval() or self.rval.eval()
    
    def __str__(self):
        return "Or expression "
    
class Implication: 

    def __init__(self, lval, rval):
        self.lval = lval 
        self.rval = rval 

        if isinstance(self.lval,ConstExpr):
            reg_global.objs.append(self.lval)
            reg_global.add_constant_expr(self.lval.symbol)

        if isinstance(self.rval,ConstExpr):
            reg_global.objs.append(self.rval)
            reg_global.add_constant_expr(self.rval.symbol)

    def eval(self):
        return (not self.lval.eval()) or self.rval.eval()
    
    def __str__(self):
        return "Implication expression "
    
class ConstExpr: 

    def __init__(self,symbol,value = False ):
        self.symbol = symbol 
        self.value = value
    
    def eval(self):
        return self.value 

    def __str__(self):
        return ("Constant Expression with symbol " + self.symbol)
    

class true: 

    def __init__(self):
        pass 

    def eval(self):
        return True
    
class false: 

    def __init__(self):
        pass 


    def eval(self):
        return False 

class Equivalence:
    
    def __init__(self, lval, rval):
        self.lval = lval 
        self.rval = rval 

        if isinstance(self.lval,ConstExpr):
            reg_global.objs.append(self.lval)
            reg_global.add_constant_expr(self.lval.symbol)

        if isinstance(self.rval,ConstExpr):
            reg_global.objs.append(self.rval)
            reg_global.add_constant_expr(self.rval.symbol)

    def eval(self):
        return (not self.lval.eval() and not self.rval.eval()) or (self.lval.eval() and self.rval.eval())
    
    def __str__(self):
        return "Equivalence obj"


class AbstractSyntaxTree: 

    def __init__(self,expr):
        self.ls = []
        self.expr =  expr

        if isinstance(self.expr,ConstExpr):
            reg_global.objs.append(self.expr)
            reg_global.add_constant_expr(self.expr.symbol)

    def eval(self): 
        return self.expr.eval()
    
    def set_expr(self,expr):
        self.expr = expr
        if isinstance(self.expr,ConstExpr):
            reg_global.objs.append(self.expr)
            reg_global.add_constant_expr(self.expr.symbol)
        

    def __str__(self):
        return "Abstract syntax tree expression "
    
