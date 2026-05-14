#!/usr/bin/env python


class Expression():
    def __init__(self):
        pass

    def eval(self,env):
        pass

class Constant(Expression):
    def __init__(self,value):
        self.value = value

    def eval(self,env):
        return self.value
    
class Symbol(Expression):
    def __init__(self,symbol):
        self.symbol = symbol

    def eval(self,env):
        return env(self.symbol)
    
class Lambda(Expression):
    def __init__(self,variables,body):
        self.variables = variables
        self.body      = body

    def eval(self,env):
        return self

class Apply(Expression):
    def __init__(self,function,arguments):
        self.function  = function
        self.arguments = arguments
        

    def eval(self,env):
        # Better be a lambda!
        evaled_function = self.function.eval(env)
        variables       = evaled_function.variables
        evaled_args     = [exp.eval(env) for exp in self.arguments]
        new_env         = create_new_env(env, variables, evaled_args)

        return evaled_function.body.eval(new_env)

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
    
