#!/usr/bin/env python


class Expression():
    def __init__(self):
        pass

    def eval(self,env,id):
        pass

class Constant(Expression):
    def __init__(self,value):
        self.value = value

    def eval(self,env,id):
        # Any one invocation produces a result, a JOB line for the dag file
        # (or the data needed to construct it), a VAR line for the dag file
        # (or the data needed to construct it) and a list of jobs this job
        # depend on.  However, we need to return a list of these so that results
        # are composable (in other words the return type needs to be a monoid for
        # the Kleisli category!).  We also need to return the next id available,
        # since any expression may have an arbitrary depth and use up an unknown
        # number of ids.
        
        # (value, [(id, JOB line, VAR line, [dependancies])], next available id)
        return (self.value, [], id)
    
class Symbol(Expression):
    def __init__(self,symbol):
        self.symbol = symbol

    def eval(self,env,id):
        return (env(self.symbol), [], id)
    
class Lambda(Expression):
    def __init__(self,variables,body):
        self.variables = variables
        self.body      = body

    def eval(self,env,id):
        return (self, [], id)

class Apply(Expression):
    def __init__(self,function,arguments):
        self.function  = function
        self.arguments = arguments
        
    def eval(self,env,id):
        # Better be a lambda!
        evaled_function = self.function.eval(env)
        variables       = evaled_function.variables

        # Here's the fun part
        value       = None
        evaled_args = []
        dag_entries = []
        next_id     = id

        for exp in self.arguments:
            value, dag_entry, next_id = exp.eval(env, next_id)
            evaled_args.append(value)
            dag_entries.append(dag_entry)
            
        new_env = create_new_env(env, variables, evaled_args)

        return (next_id, evaled_function.body.eval(new_env), dag_entries, next_id+1)

def create_new_env(env,vars,expressions):
    if not vars:
        return env

    inner = create_new_env(env,vars[1:],expressions[1:])

    return lambda s: s == vars[0] and expressions[0] or inner(s)



class BuiltinBody(Expression):
    def __init__(self, func):
        self.func = func

    def eval(self,env):
        return self.func(env)

class Builtin(Lambda):
    def __init__(self, vars, func):
        self.variables = vars
        self.body      = BuiltinBody(func)

    def eval(self,env):
        return self

add1 = Builtin(['x','y'],lambda env: env('x') + env('y'))
mul1 = Builtin(['x','y'],lambda env: env('x') * env('y'))

base_env = create_new_env(lambda x:99,['+','*'],[add1,mul1])

if __name__ == '__main__':
    # (+ 1 (* 2 3))
    test = Apply(Symbol('+'),
                 [Constant(1),
                  Apply(Symbol('*'),
                        [Constant(2),Constant(3)])])
    
    print(test.eval(base_env))
    
