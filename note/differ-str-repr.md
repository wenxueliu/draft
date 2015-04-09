
The one place where you use them both a lot is in an interactive session. If you print an object then its __str__ method will get called, whereas if you just use an object by itself then its __repr__ is shown:

>>> from decimal import Decimal
>>> a = Decimal(1.25)
>>> print(a)1.25            <---- this is from __str__
>>> aDecimal('1.25')       <---- this is from __repr__

The __str__ is intended to be as human-readable as possible, whereas the __repr__ should aim to be something that could be used to recreate the object, although it often won't be exactly how it was created, as in this case.

It's also not unusual for both __str__ and __repr__ to return the same value (certainly for built-in types).


##Purpose of __str__ and __repr__ in Python

The official Python documentation says:

>	object.__repr__(self): called by the repr() built-in function and by string conversions (reverse quotes) to compute the “official” string representation of an object.
>	object.__str__(self): called by the str() build-in function and by the print statement to compute the “informal” string representation of an object.

From the official documentation, we know that both __repr__ and __str__ are used to “represent” an object. __repr__ should be the “official” representation while __str__ is the “informal” representation.

So, what does Python’s default __repr__ and __str__ implementation of any object look like?

>>> x = 1
>>> repr(x)
'1'
>>> str(x)
'1'
>>> y = 'a string'
>>> repr(y)
"'a string'"
>>> str(y)
'a string'


While the return of repr() and str() are identical for int x, you should notice the difference between the return values for str y. It is important to realize the default implementation of __repr__ for a str object can be called as an argument to eval and the return value would be a valid str object:

>>> repr(y)
"'a string'"
>>> y2 = eval(repr(y))
>>> y == y2
True


While the return value of __str__ is not even a valid statement that can be executed by eval:

	
>>> str(y)
'a string'
>>> eval(str(y))
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<string>", line 1
    a string
           ^
SyntaxError: unexpected EOF while parsing


Therefore, a “formal” representation of an object should be callable by eval() and return the same object, if possible. If not possible, such as in the case where the object’s members are referring itself that leads to infinite circular reference, then __repr__ should be unambiguous and contain as much information as possible.


The print statement and str() built-in function uses __str__ to display the string representation of the object while the repr() built-in function uses __repr__ to display the object. Using this definition let us take an example to understand what the two methods actually do.

>>> class ClassA(object):
...     def __init__(self, b=None):
...         self.b = b
...
...     def __repr__(self):
...         return '%s(%r)' % (self.__class__, self.b)
...
>>>
>>> class ClassB(object):
...     def __init__(self, a=None):
...         self.a = a
...
...     def __repr__(self):
...         return "%s(%r)" % (self.__class__, self.a)
...
>>> a = ClassA()
>>> b = ClassB(a=a)
>>> a.b = b
>>> repr(b)
RuntimeError: maximum recursion depth exceeded while calling a Python object

Instead of literally following the requirement of __repr__ for ClassB which causes an infinite recursion problem where a.__repr__ calls b.__repr__ which calls a.__repr__ which calls b.__repr__, on and on forever, you could define ClassB.__repr__ in a different way. A way that shows as much information about an object as possible would be just as good as a valid eval-confined __repr__.

>>> class ClassB(object):
...     def __init__(self, a=None):
...         self.a = a
...
...     def __repr__(self):
...         return '%s(a=a)' % (self.__class__)
...
 
>>> a = ClassA()
>>> b = ClassB(a=a)
>>> a.b = b
>>> repr(a)
"<class '__main__.ClassA'>(<class '__main__.ClassB'>(a=a))"
>>> repr(b)
"<class '__main__.ClassB'>(a=a)"


Since __repr__ is the official representation for an object, you always want to call "repr(an_object)" to get the most comprehensive information about an object. However, sometimes __str__ is useful as well. Because __repr__ could be too complicated to inspect if the object in question is complex (imagine an object with a dozen attributes), __str__ is helpful to serve as a quick overview of complicated objects. For example, suppose you want to inspect a datetime object in the middle of a lengthy log file to find out why the datetime of a user’s photo is not correct:


>>> from datetime import datetime
>>> now = datetime.now()
>>> repr(now)
'datetime.datetime(2013, 2, 5, 4, 43, 11, 673075)'
>>> str(now)
'2013-02-05 04:43:11.673075'

The __str__ representation of now looks cleaner and easier to read than the formal representation generated from __repr__. Sometimes, being able to quickly grasp what’s stored in an object is valuable to grab the “big” picture of a complex program.
Gotchas between __str__ and __repr__ in Python

One important catch to keep in mind is that container’s __str__ uses contained objects’ __repr__.

>>> from datetime import datetime
>>> from decimal import Decimal
>>> print((Decimal('42'), datetime.now()))
(Decimal('42'), datetime.datetime(2013, 2, 5, 4, 53, 32, 646185))
>>> str((Decimal('42'), datetime.now()))
"(Decimal('42'), datetime.datetime(2013, 2, 5, 4, 57, 2, 459596))"

Since Python favours unambiguity over readability, the __str__ call of a tuple calls the contained objects’ __repr__, the “formal” representation of an object. Although the formal representation is harder to read than an informal one, it is unambiguous and more robust against bugs.
Tips and Suggestions between __str__ and __repr__ in Python

Implement __repr__ for every class you implement. There should be no excuse.
Implement __str__ for classes which you think readability is more important of non-ambiguity.



-------------------------------------------------	

In short __repr__ goal is to be unambigous and __str__ is to be readable.
The official Python documentation says __repr__ is used to compute the “official” string representation of an object and __str__ is used to compute the “informal” string representation of an object. The print statement and str() built-in function uses __str__ to display the string representation of the object while the repr() built-in function uses __repr__ to display the object. Using this definition let us take an example to understand what the two methods actually do.
Lets create a datetime object:
>>> import datetime
>>> today = datetime.datetime.now()
When I use the built-in function str() to display today:
>>> str(today)
'2012-03-14 09:21:58.130922'
You can see that the date was displayed as a string in a way that the user can understand the date and time. Now lets see when I use the  built-in function repr():
>>> repr(today)
'datetime.datetime(2012, 3, 14, 9, 21, 58, 130922)'
You can see that this also returned a string but the string was the “official” representation of a datetime object. What does official mean? Using the “official” string representation I can reconstruct the object:
>>> eval('datetime.datetime(2012, 3, 14, 9, 21, 58, 130922)')
datetime.datetime(2012, 3, 14, 9, 21, 58, 130922)
The eval() built-in function accepts a string and converts it to a datetime object.
Most functions while trying to get the string representation use the __str__ function, if missing uses __repr__. Thus in a general every class you code must have a __repr__ and if you think it would be useful to have a string version of the object, as in the case of datetime create a __str__ function.
A few references:
Stackoverflow: http://stackoverflow.com/a/2626364/504262
Python reference for __repr__
Python reference for __str__




The next example exercises the __init__ constructor and the __add__ overload method, both of which we’ve already seen, as well as defining a __repr__ method that returns a string representation for instances. String formatting is used to convert the managed self.data object to a string. If defined, __repr__ (or its sibling, __str__) is called automatically when class instances are printed or converted to strings. These methods allow you to define a better display format for your objects than the default instance display.

The default display of instance objects is neither useful nor pretty:

>>> class adder:
...     def __init__(self, value=0):
...         self.data = value                    # Initialize data
...     def __add__(self, other):
...         self.data += other                   # Add other in-place (bad!)
...
>>> x = adder()                                  # Default displays
>>> print(x)
<__main__.adder object at 0x025D66B0>
>>> x
<__main__.adder object at 0x025D66B0>

But coding or inheriting string representation methods allows us to customize the display:

>>> class addrepr(adder):                        # Inherit __init__, __add__
...     def __repr__(self):                      # Add string representation
...         return 'addrepr(%s)' % self.data     # Convert to as-code string
...
>>> x = addrepr(2)                               # Runs __init__
>>> x + 1                                        # Runs __add__
>>> x                                            # Runs __repr__
addrepr(3)
>>> print(x)                                     # Runs __repr__
addrepr(3)
>>> str(x), repr(x)                              # Runs __repr__ for both
('addrepr(3)', 'addrepr(3)')

So why two display methods? Mostly, to support different audiences. In full detail:

    __str__ is tried first for the print operation and the str built-in function (the internal equivalent of which print runs). It generally should return a user-friendly display.

    __repr__ is used in all other contexts: for interactive echoes, the repr function, and nested appearances, as well as by print and str if no __str__ is present. It should generally return an as-code string that could be used to re-create the object, or a detailed display for developers.

In a nutshell, __repr__ is used everywhere, except by print and str when a __str__ is defined. Note, however, that while printing falls back on __repr__ if no __str__ is defined, the inverse is not true—other contexts, such as interactive echoes, use __repr__ only and don’t try __str__ at all:

>>> class addstr(adder):
...     def __str__(self):                       # __str__ but no __repr__
...         return '[Value: %s]' % self.data     # Convert to nice string
...
>>> x = addstr(3)
>>> x + 1
>>> x                                            # Default __repr__
<__main__.addstr object at 0x00B35EF0>
>>> print(x)                                     # Runs __str__
[Value: 4]
>>> str(x), repr(x)
('[Value: 4]', '<__main__.addstr object at 0x00B35EF0>')

Because of this, __repr__ may be best if you want a single display for all contexts. By defining both methods, though, you can support different displays in different contexts—for example, an end-user display with __str__, and a low-level display for programmers to use during development with __repr__. In effect, __str__ simply overrides __repr__ for user-friendly display contexts:

>>> class addboth(adder):
...     def __str__(self):
...         return '[Value: %s]' % self.data     # User-friendly string
...     def __repr__(self):
...         return 'addboth(%s)' % self.data     # As-code string
...
>>> x = addboth(4)
>>> x + 1
>>> x                                            # Runs __repr__
addboth(5)
>>> print(x)                                     # Runs __str__
[Value: 5]
>>> str(x), repr(x)
('[Value: 5]', 'addboth(5)')

I should mention two usage notes here. First, keep in mind that __str__ and __repr__ must both return strings; other result types are not converted and raise errors, so be sure to run them through a converter if needed. Second, depending on a container’s string-conversion logic, the user-friendly display of __str__ might only apply when objects appear at the top level of a print operation; objects nested in larger objects might still print with their __repr__ or its default. The following illustrates both of these points:

>>> class Printer:
...     def __init__(self, val):
...         self.val = val
...     def __str__(self):                  # Used for instance itself
...         return str(self.val)            # Convert to a string result
...
>>> objs = [Printer(2), Printer(3)]
>>> for x in objs: print(x)                 # __str__ run when instance printed
...                                         # But not when instance in a list!
2
3
>>> print(objs)
[<__main__.Printer object at 0x025D06F0>, <__main__.Printer object at ...more...
>>> objs
[<__main__.Printer object at 0x025D06F0>, <__main__.Printer object at ...more...

To ensure that a custom display is run in all contexts regardless of the container, code __repr__, not __str__; the former is run in all cases if the latter doesn’t apply:

>>> class Printer:
...     def __init__(self, val):
...         self.val = val
...     def __repr__(self):                 # __repr__ used by print if no __str__
...         return str(self.val)            # __repr__ used if echoed or nested
...
>>> objs = [Printer(2), Printer(3)]
>>> for x in objs: print(x)                 # No __str__: runs __repr__
...
2
3
>>> print(objs)                             # Runs __repr__, not ___str__
[2, 3]
>>> objs
[2, 3]

In practice, __str__ (or its low-level relative, __repr__) seems to be the second most commonly used operator overloading method in Python scripts, behind __init__. Any time you can print an object and see a custom display, one of these two tools is probably in use.

http://satyajit.ranjeev.in/2012/03/14/python-repr-str.html



First, let me reiterate the main points in Alex’s post:

    The default implementation is useless (it’s hard to think of one which wouldn’t be, but yeah)
    __repr__ goal is to be unambiguous
    __str__ goal is to be readable
    Container’s __str__ uses contained objects’ __repr__

Default implementation is useless

This is mostly a surprise because Python’s defaults tend to be fairly useful. However, in this case, having a default for __repr__ which would act like:

return "%s(%r)" % (self.__class__, self.__dict__)

would have been too dangerous (for example, too easy to get into infinite recursion if objects reference each other). So Python cops out. Note that there is one default which is true: if __repr__ is defined, and __str__ is not, the object will behave as though __str__=__repr__.

This means, in simple terms: almost every object you implement should have a functional __repr__ that’s usable for understanding the object. Implementing __str__ is optional: do that if you need a “pretty print” functionality (for example, used by a report generator).

The goal of __repr__ is to be unambiguous

Let me come right out and say it — I do not believe in debuggers. I don’t really know how to use any debugger, and have never used one seriously. Furthermore, I believe that the big fault in debuggers is their basic nature — most failures I debug happened a long long time ago, in a galaxy far far away. This means that I do believe, with religious fervor, in logging. Logging is the lifeblood of any decent fire-and-forget server system. Python makes it easy to log: with maybe some project specific wrappers, all you need is a

log(INFO, "I am in the weird function and a is", a, "and", b, "is", b, "but I got a null C — using default", default_c)

But you have to do the last step — make sure every object you implement has a useful repr, so code like that can just work. This is why the “eval” thing comes up: if you have enough information so eval(repr(c))==c, that means you know everything there is to know about c. If that’s easy enough, at least in a fuzzy way, do it. If not, make sure you have enough information about c anyway. I usually use an eval-like format: "MyClass(this=%r,that=%r)" % (self.this,self.that). It does not mean that you can actually construct MyClass, or that those are the right constructor arguments — but it is a useful form to express “this is everything you need to know about this instance”.

Note: I used %r above, not %s. You always want to use repr() [or %r formatting character, equivalently] inside __repr__ implementation, or you’re defeating the goal of repr. You want to be able to differentiate MyClass(3) and MyClass("3").

The goal of __str__ is to be readable

Specifically, it is not intended to be unambiguous — notice that str(3)==str(“3″). Likewise, if you implement an IP abstraction, having the str of it look like 192.168.1.1 is just fine. When implementing a date/time abstraction, the str can be “2010/4/12 15:35:22″, etc. The goal is to represent it in a way that a user, not a programmer, would want to read it. Chop off useless digits, pretend to be some other class — as long is it supports readability, it is an improvement.

Container’s __str__ uses contained objects’ __repr__

This seems surprising, doesn’t it? It is a little, but how readable would

[moshe is, 3, hello
world, this is a list, oh I don't know, containing just 4 elements]

be? Not very. Specifically, the strings in a container would find it way too easy to disturb its string representation. In the face of ambiguity, remember, Python resists the temptation to guess. If you want the above behavior when you’re printing a list, just

print "["+", ".join(l)+"]"

(you can probably also figure out what to do about dictionaries.

Summary

Implement __repr__ for any class you implement. This should be second nature. Implement __str__ if you think it would be useful to have a string version which errs on the side of more readability in favor of more ambiguity.




Unless you specifically act to ensure otherwise, most classes don't have helpful results for either:

>>> class Sic(object): pass
... 
>>> print str(Sic())
<__main__.Sic object at 0x8b7d0>
>>> print repr(Sic())
<__main__.Sic object at 0x8b7d0>
>>>

As you see -- no difference, and no info beyond the class and object's id. If you only override one of the two...:

>>> class Sic(object): 
...   def __repr__(object): return 'foo'
... 
>>> print str(Sic())
foo
>>> print repr(Sic())
foo
>>> class Sic(object):
...   def __str__(object): return 'foo'
... 
>>> print str(Sic())
foo
>>> print repr(Sic())
<__main__.Sic object at 0x2617f0>
>>>

as you see, if you override __repr__, that's ALSO used for __str__, but not vice versa.

Other crucial tidbits to know: __str__ on a built-on container uses the __repr__, NOT the __str__, for the items it contains. And, despite the words on the subject found in typical docs, hardly anybody bothers making the __repr__ of objects be a string that eval may use to build an equal object (it's just too hard, AND not knowing how the relevant module was actually imported makes it actually flat out impossible).

So, my advice: focus on making __str__ reasonably human-readable, and __repr__ as unambiguous as you possibly can, even if that interferes with the fuzzy unattainable goal of making __repr__'s returned value acceptable as input to __eval__!




__repr__: representation of python object usually eval will convert it back to that object

__str__: is whatever you think is that object in text form

e.g.

>>> s="""w'o"w"""
>>> repr(s)
'\'w\\\'o"w\''
>>> str(s)
'w\'o"w'
>>> eval(str(s))==s
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<string>", line 1
    w'o"w
       ^
SyntaxError: EOL while scanning single-quoted string
>>> eval(repr(s))==s
True



In all honesty, eval(repr(obj)) is never used. If you find yourself using it, you should stop, because eval is dangerous, and strings are a very inefficient way to serialize your objects (use pickle instead).

Therefore, I would recommend setting __repr__ = __str__. The reason is that str(list) calls repr on the elements (I consider this to be one of the biggest design flaws of Python that was not addressed by Python 3). An actual repr will probably not be very helpful as the output of print [your, objects].

To qualify this, in my experience, the most useful use case of the repr function is to put a string inside another string (using string formatting). This way, you don't have to worry about escaping quotes or anything. But note that there is no eval happening here.





    In short, the goal of __repr__ is to be unambiguous and __str__ is to be readable.

Here is a good example:

>>> import datetime
>>> today = datetime.datetime.now()
>>> str(today)
'2012-03-14 09:21:58.130922'
>>> repr(today)
'datetime.datetime(2012, 3, 14, 9, 21, 58, 130922)'

Read this documentation for repr:

    repr(object)

    Return a string containing a printable representation of an object. This is the same value yielded by conversions (reverse quotes). It is sometimes useful to be able to access this operation as an ordinary function. For many types, this function makes an attempt to return a string that would yield an object with the same value when passed to eval(), otherwise the representation is a string enclosed in angle brackets that contains the name of the type of the object together with additional information often including the name and address of the object. A class can control what this function returns for its instances by defining a __repr__() method.

Here is the documentation for str:

    str(object='')

    Return a string containing a nicely printable representation of an object. For strings, this returns the string itself. The difference with repr(object) is that str(object) does not always attempt to return a string that is acceptable to eval(); its goal is to return a printable string. If no argument is given, returns the empty string, ''.

[1]http://stackoverflow.com/questions/1436703/difference-between-str-and-repr-in-python
[2]https://www.inkling.com/read/learning-python-mark-lutz-4th/chapter-29/string-representation---repr--

[python doc repr](http://docs.python.org/2/reference/datamodel.html#object.__repr__)
[python doc str](http://docs.python.org/2/reference/datamodel.html#object.__str__)
