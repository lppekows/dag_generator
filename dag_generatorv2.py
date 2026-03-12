#!/usr/bin/env python3

import sys
from lark import Lark, Transformer

class Definition():
    def __init__(self, name, parameters, invocation, output_expression = None):
        self.name       = name
        self.invocation = invocation.replace('"','').split(' ')
        self.output_expression = output_expression
        self.executable = self.invocation[0]
        self.parameters = parameters
        self.arguments  = [a[0] == '$' and f'$({a[1:]})' or a for a in self.invocation[1:]]
        self.argLine    = self.arguments and f"arguments = {' '.join(self.arguments)}" or ""

    def eval(self, arguments, environment):
        id      = self.name in environment and environment[self.name] + 1 or 0
        new_env = {k:v for k,v in environment.items() if k != self.name}
        new_env[self.name] = id

        return (self.name, zip(self.parameters,arguments), new_environment) 

    def write_submit_file(self):
        subfile_text = f"""
executable = {self.executable}
{self.argLine}

output = $(outname).out
error  = $(outname).err
log    = $(outname).log

queue
"""
        with open(f'{self.name}.sub','w') as f_out:
            print(subfile_text,file=f_out)

    def __str__(self):
        return f'{self.name} ( {self.parameters} ) = {self.output_expression}'

class Program():
    def __init__(self,definitions,expression):
        self.definitions = definitions
        self.expression  = expression

    def compile(self):
        functions = {d.name:d for d in self.definitions}
        dag       = Dag(self.expression,functions)
        dag.label(0)

        return dag

class Dag():
    def __init__(self,expression,functions):
        self.functions = functions
        self.function  = functions[expression.fname]
        self.args      = []
        self.id        = 0
    
        for arg in expression.args:
            if isinstance(arg,Expression):
                self.args.append(Dag(arg,functions))
            else:
                self.args.append(arg[0])
                
    def label(self,id): 
        for arg in self.args:
            if isinstance(arg,Dag):
                id = arg.label(id)
        self.id = id
        return id+1

    def render(self):
        for f in self.functions.values():
            f.write_submit_file()

        my_parents = []
        parameters = []

        for arg in self.args:
            if isinstance(arg,Dag):
                arg.render()
                my_parents.append(str(arg.id))
                parameters.append(f"{arg.id}.out")
            else:
                parameters.append(f"{arg}")

            
        assignments = " ".join([f'{var}="{val}"' for var,val in zip(self.function.parameters,parameters)])
        assignments = f'outname="{self.id}" ' + assignments
        print(f"JOB {self.id} {self.function.name}.dag")
        print(f"VARS {self.id} {assignments}")
        if len(my_parents):
            print(f"PARENT {' '.join(my_parents)} CHILD {self.id}") 
        print()


    def __repr__(self):
        return f"{self.function.name}:{self.id} ( {self.args} )"

class Expression():
    def __init__(self,fname,args):
        self.fname = fname
        self.args  = args

    def __repr__(self):
        return f"{self.fname}( {self.args} )"

class DagTransformer(Transformer):
    def value(self, items):
        definitions = items[:-1]
        expression  = items[-1]
        return Program(definitions, expression)

    def definition(self, items):
        if len(items) == 3:
            name, params, invocation = items
            return Definition(name, params, invocation)  
        else:
            name, params, invocation, output = items
            return Definition(name, params, invocation, output)
    def arglist(self, items):
        return list(items)
    def expression(self, expr):
        if len(expr) > 1:
            return Expression(expr[0],expr[1:])
        else:
            return expr
    def string(self, s):
        (s,) = s
        return s[1:-1]
    def SIGNED_NUMBER(self, n):
        return int(n)

    def var(self, s):
        (s,) = s
        return s

    def CNAME(self, s):
        return str(s)



bnf_filename  = sys.argv[1]
text_filename = sys.argv[2]

with open(bnf_filename) as f_in:
   bnf = ''.join([line for line in f_in])

with open(text_filename) as f_in:
   text = ''.join([line for line in f_in])

parser  = Lark(bnf, start='value')
tree    = parser.parse(text)
program = DagTransformer().transform(tree)



#print(dag)
#print( dag.pretty() )

dag = program.compile()

dag.render()


