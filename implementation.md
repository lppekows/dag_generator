Consider a simple expression like

```python
f(g(1), h(2, i(3)))
```

This has a call graph which can be derived from a static analysis, that is, the
structure of the dag is completely specified by (and parallels) the structure of
the calls.

(TODO: make these pretty...)

```
       i
       |
g      h
|      |
+---+--+
    |
	f
```

However the situation is immediately more complicated when using map

```python
f(map(g, [1,2,3])))
```
The call structure is even simpler

```
map
|
|
f
```

but this is not the dag structure we want since it fails to take advantage of the
inherent parallelism of map.

```
g(1)   g(2)   g(3)
 |      |      |
 +------+------+
        |
		f
```

In order to derive the correct dag it is not enough to statically analyze the
code, it must be evaluated/run[^1].  This then requires that the code be
compiled into some form that can be executed or interpreted.  There are many
ways this could be done, translate to Python, literally compile to machine code,
implement a stack machine such as the
[G-machine](https://amelia.how/posts/the-gmachine-in-detail.html), etc.  Given
the simple functional nature of the dag language and the lack of importance of
performance a natural approach is to compile down to a simple version of Lisp
or, equivilently a kind of [lambda
calculus](https://en.wikipedia.org/wiki/Lambda_calculus).  The interpreter for
the basic case is in [interpreter.py](interpreter.py).

Two advantages of this approach are (1) after translation interpreting the
resulting code is very simple, needing less than a page of Python and (2)
modifying this basic core is easy, which will play a key role in what follows.
For a lovely talk discussing both these features, see William Byrd's talk on
[The Most Beautiful Program in the
World](https://www.youtube.com/watch?v=OyfBQmvr2Hc).

The next question to ask is, if we are going to treat these expressions as real
functions what are the input and output types?  Consider a sample definition and
call

```python
f(x,y) = "f.py --x $x $y" => "a=$y/in/out"

f(1,"hello.in")
```

"1" here is a standard integer, in general arguments to a function may be any
primitive type including ints, floats, strings, etc.  The only thing this kind
of function, which will result in a dag entry, can produce is a collection of
files, in this case "hello.out" and the implicit stdout and stderr files created
by HTCondor.  Specifically, the output of any such function is some sort of
association between keys ("a") and filenames ("hello.out").  A hashtable is the
obvious way to implement such an association, but the specifics aren't
important.

This now allows for a clear semantics of dotted function calls.  Moving to
Scheme syntax

```scheme
(g.x 1)
```

becomes syntactic sugar for

```scheme
(select 'x (g 1))
```

However the cost of this transformation is to introduce a second kind of
function since `select` should not result in a dag node.  This doesn't represent
a particular problem, but it does require that functions (lambda terms) carry
some sort of information regarding which type of function they are.

The next issue is closely related to the previous one.  For function calls that
result in a dag entry the call not only returns a value but adds the `JOB` and
`VARS` line to the global dag, as well as creates a mapping between the job and
its parents.  While the evaluator could track and manage these additional values
I suspect that it will be far more elegant, as well as well as simpler to
implement, if the functions themselves return *enhanced* or *decorated* results,
that is, both the resulting value and the necessary data to construct the dag.

As a side note, this is closely related to the idea of a 
[kleisli category](https://www.youtube.com/watch?v=i9CU4CuHADQ), which
is also related to *monads*.  The classic example of which is is to enhance
the returned value of a function with a logging message.  This is described
in many places, but a good reference starts
[here](https://brian-candler.medium.com/function-composition-with-bind-4f6e3fdc0e7)
and the sense in which this is a monad
[here](https://brian-candler.medium.com/function-programming-illustrated-in-python-part-4-bc8948ec6433).

The interpreter for this enhanced lambda calculus is in [dag_eval](dag_eval.py)
but it is very much a work in progress.


[^1]: In principle map could be treated as a special form rather than a function
    which would allow a static analysis, but this would likely just kick the
    problem down the road until another complex construct was encountered.
    Plus, as the rest of the document discusess, doing a full evaluation has
    other advantages.
