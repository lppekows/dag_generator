#!/usr/bin/env python3

import sys
from lark import Lark, Transformer

class Definition():
    def __init__(self, name, parameters, invocation, output_expression = None):
        self.name       = name
        self.invocation = invocation.split(' ')
        self.executable = self.invocation[0]
        self.arguments  = [a[0] == '$' and f'$({a[1:]})' or a for a in self.invocation[1:]]
        self.argLine    = self.arguments and f"arguments = {' '.join(self.arguments)}" or ""

    def toSub(self):
        return f"""
executable = {self.executable}
{self.argLine}

output = $(outname).out
error  = $(outname).err
log    = $(outname).log

queue
"""


class DagTransformer(Transformer):
    def definition(self, items):
        if len(items) == 3:
            name, args, value = items
            return f'{name} ( {args} ) = {value}'
        else:
            return "HOT HAMS:" + str(items)
    def arglist(self, items):
        return list(items)
    def expression(self, expr):
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

parser = Lark(bnf, start='value')
tree   = parser.parse(text)
dag    = DagTransformer().transform(tree)



print(dag)
print( dag.pretty() )

