#!/usr/bin/env python

import tomllib
import sys

class Definition():
    def __init__(self, name, parameters):
        self.name       = name
        self.invocation = parameters['invocation'].split(' ')
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

class CallTree():
    pass

class CallTreeValue(CallTree):
    def __init__(self,value):
        self.value = str(value)

    def __repr__(self):
        return self.value

class CallTreeFunction(CallTree):
    def __init__(self,f):
        self.name = f['function']
        self.args = {name:toCallTree(a) for name,a in f.items() if name != 'function'}

    def __repr__(self):
        return f'{self.name}( {str(self.args)} )'

class CallTreeMap(CallTree):
    def __init__(self,m):
        fname = m['function']
        
        var, values = [(k,v) for k,v in m.items() if k != 'function'][0]
        self.subExprs = [toCallTree({"function":fname, var:{"value":value}}) for value in values['value']]

    def __repr__(self):
        return '[' + " ".join([str(x) for x in self.subExprs]) + ']'

def toCallTree(o):
    if isinstance(o,str):
        return CallTreeValue(o)
    if isinstance(o,int):
        return CallTreeValue(str(o))
    if isinstance(o,list):
        return [toCallTree(x) for x in o]
    if isinstance(o,dict):
        if 'function' in o:
            return CallTreeFunction(o)
        if 'value' in o:
            return CallTreeValue(o['value'])
        if 'map' in o:
            return CallTreeMap(o['map'])



class Dag():
    def __init__(self,name,prefix,constants,dependancies):
        self.sub = f"{name}.sub"
        self.id  = f"{name}-{prefix}"
        
        self.arguments  = []
        self.parents    = []

        self.arguments += [f'{arg[0]}="{arg[1]}"' for arg in constants]
        self.arguments.append(f'outname="{self.id}"')

        for n,v in dependancies:
            if isinstance(v,list):
                values = " ".join([d.id + ".out" for d in v])
                self.arguments.append(f'{n}="{values}"')
                self.parents += [d.id for d in v]
            else:
                self.arguments.append(f'{n} = "{v.id}.out"')
                self.parents.append(v.id)

        print(f'JOB  {self.id} {self.sub}')
        print(f'VARS {self.id} {" ".join(self.arguments)}')
        
        if self.parents:
            print(f"PARENT {" ".join(self.parents)} CHILD {self.id}")

def toDag(callTree, prefix):
    if not isinstance(callTree,CallTreeFunction):
        raise Exception()
    
    name = callTree.name
    args = callTree.args

    dependancies = []
    constants    = []

    for k,v in args.items():
        if isinstance(v,CallTreeFunction):
            dependancies.append( (k,toDag(v,f'{prefix}-{k}')) )
        elif isinstance(v,CallTreeMap):
            dependancies.append( (k,[toDag(v1,f'{prefix}-{k}-{i}') for i,v1 in enumerate(v.subExprs)]) )
        else:
            constants.append((k,v))

        
    return Dag(name, prefix, constants, dependancies)

    



with open(sys.argv[1],'rb') as f_in:
    data = tomllib.load(f_in)

functions = {key:Definition(key,value) for key,value in data.items() if key != "main"}

for name,func in functions.items():
    with open(name + ".sub","w") as f_out:
        print(func.toSub(), file=f_out)


call = toCallTree(data['main'])
# dag  = Dag(call,"")


dag = toDag(call, "JOB")
print(dag)

