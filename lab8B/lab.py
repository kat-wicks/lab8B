"""6.009 Lab 8A: carlae Interpreter"""

import sys


class EvaluationError(Exception):
    """Exception to be raised if there is an error during evaluation."""
    pass



def tokenize(source):
    """
    Splits an input string into meaningful tokens (left parens, right parens,
    other whitespace-separated values).  Returns a list of strings.
    Arguments:
        source (str): a string containing the source code of a carlae
                      expression
    """
    string_list = []
    s = ""
    comment = False
    for i in source:
        #go through characters
        if comment:
            if i =='\n': #break comment
                comment = False
        else:
            if (i == ' ' or i=='\n')and s:
                string_list.append(s)
                s = ""
            elif i in "()" and (s == "" or s[-1] not in "()+-*/;<>=!"):
                if s:
                    string_list.append(s)
                    s = ""
                string_list.append(i)
            elif i ==';': #enter comment mode
                comment = True
                if s:
                    string_list.append(s)
                    s = ""
                
            elif i and i != ' ' and i!= '\n':
                s+= (i)
    if s:            
        string_list.append(s)
    return string_list

def parse(tokens):
    """
    Parses a list of tokens, constructing a representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-expressions are represented as Python lists
    Arguments:
        tokens (list): a list of strings representing tokens
    """
    s = [[]]
    inner = ""
    paren = 0 #keeps track of # of parens
    try:
        for token in tokens:
            if token == '(':
                s.append([]) #go down into lower level
                paren +=1
            elif token == ')':
                if inner:
                    s[-1].append(inner)
                    inner = ""
                sub = s.pop()
                s[-1].append(sub)
                paren -= 1
                
            else:
                try:
                    token = float(token)
                except:
                    pass
                finally:
                    s[-1].append(token)

    except:
        raise SyntaxError
    if [] in s or (paren == 0 and len(s[0]) >1): #if mismatched
        raise SyntaxError
    return s[0] if len(s[0]) >1 else s[0][0]

def mul(args):
    i = 1
    for atom in args:
        i *= atom
    return i
def div(args):
    i = args[0]
    for atom in args[1:]:
        i = i/atom
    return i
def check_order(op, args, env=None):
    if env == None:
        env = Environment()
    if op == 0:
        for i in range(1,len(args)):
            if evaluate(args[i-1],env) <= evaluate(args[i],env):
                return False
        return True
    elif op == 1:
        for i in range(1,len(args)):
            if evaluate(args[i-1],env) >= evaluate(args[i],env):
                return False
        return True
    elif op == 2:
        for i in range(1,len(args)):
            if evaluate(args[i-1],env) < evaluate(args[i],env):
                return False
        return True
    elif op == 3:
        for i in range(1,len(args)):
            if evaluate(args[i-1],env) > evaluate(args[i],env):
                return False
        return True
def check_gt(args, env=None):
    return check_order(0, args,env)
def check_ls(args, env= None):
    return check_order(1,args,env)
def check_geq(args, env= None):
    return check_order(2, args, env)
def check_leq(args, env= None):
    return check_order(3, args, env)
def check_equal(args, env= None):
    return all([args[0]==i for i in args[1:]])

def define(args, env):
    try:
        ##print(args[0], args[1:])

        if isinstance(args[0], list): #handles short definition - list = S-Exps
            print(args[0][1:], args[1])
            env[args[0][0]] = Function(args[0][1:], args[1], env)
            return env[args[0][0]]
        else:
            env[args[0]] = evaluate(args[1], env) #traditional define
            return evaluate(args[1],env)
    except:
        raise EvaluationError

def check_any(args, env):
    for i in args:
        if evaluate(i, env):
            return True
    return False

def check_all(args, env):
    for i in args:
        if not evaluate(i, env):
            return False
    return True

def check_not(arg, env):
    if evaluate(arg, env):
        return False
    return True

def check_if(tri,env):
    
    if evaluate(tri[0]) == True:
        print('tri[1] is: ', tri[1])
        return evaluate(tri[1],env)
    elif evaluate(tri[0]) == False:
        print('tri[2] is: ', tri[2])
        return evaluate(tri[2],env)
    else:
        print('lol what')
        print(evaluate(tri[0],env))

carlae_builtins = {
    '+' : sum,
    '-' : lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    '*' : mul,
    '/' : div,
    'define' : define,
    'lambda' : 'lambda', #define and lambda are utility funcs
    '#t' : True,
    '#f' : False,
    '?=' : check_equal,
    '>' : check_gt,
    '<' : check_ls,
    '>=' : check_geq,
    '<='  : check_leq,
    'and' : check_all,
    'or'  : check_any,
    'not' : check_not,
    'if' : check_if

}




class Environment():
    def __init__(self, bindings = None, parent = None):
        if not bindings: #saves mappings
            bindings = dict()
        self.bindings= bindings
        self.parent = parent
        
        
    def __getitem__(self,key):
        if key in self.bindings:
            return self.bindings[key] #go through superclasses until actual value is found
        try:
            if not self.parent:
                raise KeyError
            return self.parent[key]
        except:
            raise KeyError
    def __setitem__(self, key, value):
        
        self.bindings[key] = value
        return value
    def __contains__(self,key): #let's be cute and use in
        flag = True
        try:
            self.__getitem__(key)
        except:
            flag = False
        finally:
            return flag

class Function():   
    def __init__(self, params = None, expr = None, parent = None): #saves relevant info
        d = dict()
        if params:
            for i in range(len(params)):
                d[i] = params[i]
        else:
            params = []
        self.params = params
        self.keys = d
        self.expr = expr
        ##print("parent is", parent.bindings)
        self.environ =  parent
        ##print('BINDINGS',self.keys, self.params, self.expr,self.environ.bindings)

    def eval(self, args,  parent_env = None):
        ##print(args, self.keys, self.params)
        evaluator = Environment(parent = self.environ)
        try:
            for i in range(len(args)):
                evaluator[self.keys[i]] = evaluate(args[i], parent_env) #adds values from function call
        except:
            raise EvaluationError
        print(self.expr, evaluator.bindings)
        return evaluate(self.expr, evaluator)


def evaluate(tree, env = None):
    """
    Evaluate the given syntax tree according to the rules of the carlae
    language.
    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """

    if not env:
        env = Environment()
    if tree == []:
        raise EvaluationError
    # print("ENV MAP::::", env.bindings)
    # print("COMMAND::::", tree)
    if not isinstance(tree, list):                #check for atoms
        ##print('NOT A LIST')
        #reorder to allow for renaming builtins! 
        if tree == '#t' or tree == '#f':
            return True if tree == '#t' else False
        if tree in carlae_builtins:
            print('RETURNING BUILTIN', tree)
            return tree
        if isinstance(tree,float) or isinstance(tree,int):
            ##print('RETURNING NUMBER')
            return tree

        try:
            ##print('IN ENV, IS..', env[tree])
            return env[tree]
        except:
            raise EvaluationError
            return

    else:
        if evaluate(tree[0],env) not in carlae_builtins: #check for correct leading entry (must be evaluate-able)
            if tree[0] in env:
                if not isinstance(env[tree[0]], Function):
                    raise EvaluationError

        ##print('MADE IT PAST EVALS. TREE IS: ', tree)
        f = tree[0]
        ##print('F IS...', tree[0])
        if not isinstance(evaluate(tree[0],env), Function): #how to handle lead? built-in, define, lambda, named, unnamed (in that order)
            ##print('IS BUILTIN')
            try:
                f= carlae_builtins[evaluate(tree[0],env)]
            except:
                raise EvaluationError
        if f == define:
            print('IS DEFINE')
            return define(tree[1:], env)
        if f == "lambda":
            ##print('LAMBDA')
            ##print(tree[1], tree[2])
            return Function(tree[1], tree[2], env)
        if f == check_if:
            print(tree)
            return check_if(tree[1:], env)
        # if f == check_all:
        #     return check_all(tree[1:])
        # if f == check_any:
        #     return check_any(tree[1:])

        if f == True or f == False:
            print('F IS TRUTH value', f)
            return f
        if tree[0] in env:  #checks if function has already been defined
            ##print("attempting to eval")

            #can combine cases using evaluate !!!

            if isinstance(env[tree[0]], Function):
                ##print("Got Here")
                return env[tree[0]].eval(tree[1:], env)



        # if tree[0] in env:
        #     if isinstance(env[tree[0]], Function):
        #         return env[tree[0]].eval(tree[1:], env)

        if f == check_not or f == check_any or f == check_all or f == check_leq or f == check_geq or f ==check_ls or f == check_gt:
            return f(tree[1:], env)
        args = [] #if function hasn't been defined, eval it inline
        for i in tree[1:]:
            if isinstance(i, float) or isinstance(i, int):
                args.append(i)
            else:
                print(i, env.bindings)
                args.append(evaluate(i,env))
        print('f is',f, 'args are', args)

        if isinstance(f, list):
            f = evaluate(f, env)
            return f.eval(tree[1:], env)
        
        to_ret = f(args)
        return to_ret

def result_and_env(tree, env = None):
    if env == None:
        env = Environment()
    evald = evaluate(tree, env)
    return(evald, env)
def repl():
    inp = ""
    e = Environment()
    while inp != "QUIT":
        inp = input("enter >>")
        i = parse(tokenize(str(inp)))
        #print(i)
        try:
            print(evaluate(i, e))
        except:
            print("code error, diagnostic info: env =", e.bindings, " i =", i)

if __name__ == '__main__':
    # code in this block will only be executed if lab.py is the main file being
    # run (not when this module is imported)
    repl()