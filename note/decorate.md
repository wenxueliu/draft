---
layout: post
category : lessons
tagline: "Supporting tagline"
tags : [python, learning, advance]
---
{% include JB/setup %}

一 装饰器decorator
decorator设计模式允许动态地对现有的对象或函数包装以至于修改现有的职责和行为，简单地讲用来动态地扩展现有的功能。其实也就是其他语言中的AOP的概念，将对象或函数的真正功能也其他辅助的功能的分离。
二Python中的decorator
python中的decorator通常为输入一个函数，经过装饰后返回另一个函数。  比较常用的功能一般使用decorator来实现，例如python自带的staticmethod和classmethod。

装饰器有两种形式：

    @A
    def foo():
        pass

相当于：

    def foo():
        pass
    foo = A(foo)

第二种为带参数的：

    @A(arg)
    def foo():
        pass

则相当于：

    def foo():
        pass
    foo = A(arg)(foo)

可以看出第一种的装饰器是个返回函数的函数，第二种的装饰器是个返回函数的函数的函数。

python中的decorator可以多个同时使用，如下：

    @A
    @B
    @C
    def f (): pass

    # it is same as below
    def f(): pass
    f = A(B(C(f)))

三 Python中常用的decorator实例
decorator通常用来在执行前进行权限认证，日志记录，甚至修改传入参数，或者在执行后对返回结果进行预处理，甚至可以截断函数的执行等等。

http://www.cnblogs.com/Lifehacker/archive/2011/12/20/3_useful_python_decorator.html#2277951
﻿http://www.cnblogs.com/rhcad/archive/2011/12/21/2295507.html﻿


示例1: 最简单的函数,表示调用了两次

    def myfunc():
        print("myfunc() called.")

    myfunc()
    myfunc()


示例2: 替换函数(装饰)

装饰函数的参数是被装饰的函数对象，返回原函数对象
装饰的实质语句: myfunc = deco(myfunc)

    def deco(func):
        print("before myfunc() called.")
        func()
        print("after myfunc() called.")
        ​return func

    def myfunc():
        print(" myfunc() called.")

    myfunc = deco(myfunc)

    myfunc()
    myfunc()


示例3: 使用语法糖@来装饰函数，相当于“myfunc = deco(myfunc)”
但发现新函数只在第一次被调用，且原函数多调用了一次

    def deco(func):
        print("before myfunc() called.")
        func()
        print("  after myfunc() called.")
        return func

    @deco
    def myfunc():
        print("myfunc() called.")

    myfunc()
    myfunc()



示例4: 使用内嵌包装函数来确保每次新函数都被调用，
内嵌包装函数的形参和返回值与原函数相同，装饰函数返回内嵌包装函数对象

    def deco(func):
        def deco():
            print("before myfunc() called.")
            func()
            print(" after myfunc() called.")
          
        return deco

    @deco
    def myfunc():
        print(" myfunc() called.")
        return  'ok'

    myfunc()
    myfunc()


示例5: 对带参数的函数进行装饰，
内嵌包装函数的形参和返回值与原函数相同，装饰函数返回内嵌包装函数对象

{% highlight python linenos %}
    def deco(func):
        def deco(a, b):
            print("before myfunc() called.")
            ret =func(a, b)
            print("  after myfunc() called. result: %s"% ret)
            return ret
        return deco

    @deco
    def myfunc(a, b):
        print(" myfunc(%s,%s) called."%(a, b))
        return  a +b

    myfunc(1, 2)
    myfunc(3, 4)

{% endhighlight %}



示例6: 对参数数量不确定的函数进行装饰，
参数用`(\*args, \*\*kwargs)`，自动适应变参和命名参数

{% highlight python linenos %}

    def deco(func):
        def deco(\*args, \*\*kwargs):
            print("before %s called."%func.__name__)
            ret =func(\*args, \*\*kwargs)
            print("  after %s called. result: %s"%(func.__name__, ret))
            return ret
        return deco

    @deco
    def myfunc(a, b):
        print(" myfunc(%s,%s) called."%(a, b))
        return a+b

    @deco
    def myfunc2(a, b, c):
        print(" myfunc2(%s,%s,%s) called."%(a, b, c))
        return a+b+c

    myfunc(1, 2)
    myfunc(3, 4)
    myfunc2(1, 2, 3)
    myfunc2(3, 4, 5)

{% endhighlight %}


示例7: 在示例4的基础上，让装饰器带参数，
和上一示例相比在外层多了一层包装。
装饰函数名实际上应更有意义些
    def deco(arg):
    def deco(func):
    def __deco():
        print("before %s called [%s]."%(func.__name__, arg))
        func()
        print("  after %s called [%s]."%(func.__name__, arg))
        return__deco
    return_deco

    @deco("mymodule")
    def myfunc():
        print(" myfunc() called.")

    @deco("module2")
    def myfunc2():
        print(" myfunc2() called.")

    myfunc()
    myfunc2()

示例8: 装饰器带类参数
classlocker:
def__init__(self):
print("locker.__init__() should be not called.")
@staticmethod
defacquire():
print("locker.acquire() called.（这是静态方法）")
@staticmethod
defrelease():
print("  locker.release() called.（不需要对象实例）")
defdeco(cls):
'''cls 必须实现acquire和release静态方法'''
def_deco(func):
def__deco():
print("before %s called [%s]."%(func.__name__, cls))
cls.acquire()
try:
returnfunc()
finally:
cls.release()
return__deco
return_deco
@deco(locker)
defmyfunc():
print(" myfunc() called.")
myfunc()
myfunc()




'''mylocker.py: 公共类 for 示例9.py'''
classmylocker:
def__init__(self):
print("mylocker.__init__() called.")
@staticmethod
defacquire():
print("mylocker.acquire() called.")
@staticmethod
defunlock():
print("  mylocker.unlock() called.")
classlockerex(mylocker):
@staticmethod
defacquire():
print("lockerex.acquire() called.")
@staticmethod
defunlock():
print("  lockerex.unlock() called.")
deflockhelper(cls):
'''cls 必须实现acquire和release静态方法'''
def_deco(func):
def__deco(*args, **kwargs):
print("before %s called."%func.__name__)
cls.acquire()
try:
returnfunc(*args, **kwargs)
finally:
cls.unlock()
return__deco
return_deco



'''示例9: 装饰器带类参数，并分拆公共类到其他py文件中
同时演示了对一个函数应用多个装饰器'''
frommylocker import*
classexample:
@lockhelper(mylocker)
defmyfunc(self):
print(" myfunc() called.")
@lockhelper(mylocker)
@lockhelper(lockerex)
defmyfunc2(self, a, b):
print(" myfunc2() called.")
returna +b
if__name__=="__main__":
a =example()
a.myfunc()
print(a.myfunc())
print(a.myfunc2(1, 2))
print(a.myfunc2(3, 4))



1. Python装饰器学习 http://blog.csdn.net/thy38/article/details/4471421
2. Python装饰器与面向切面编程 http://www.cnblogs.com/huxi/archive/2011/03/01/1967600.html
3. Python装饰器的理解 http://apps.hi.baidu.com/share/detail/17572338
