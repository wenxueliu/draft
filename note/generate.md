
###生成器简介

首先请确信，生成器就是一种迭代器。生成器拥有next方法并且行为与迭代器完全相同，这意味着生成器也可以用于Python的for循环中。另外，对于生成器的特殊语法支持使得编写一个生成器比自定义一个常规的迭代器要简单不少，所以生成器也是最常用到的特性之一。
从Python 2.5开始，[PEP 342：通过增强生成器实现协同程序]的实现为生成器加入了更多的特性，这意味着生成器还可以完成更多的工作。

###生成器函数

####使用生成器函数定义生成器

如何获取一个生成器？首先来看一小段代码：

	>>> def get\_0\_1\_2():
	...yield 0
	...yield 1
	...yield 2
	...
	>>> get_0_1_2
	<function get_0_1_2 at 0x00B2CB70>

我们定义了一个函数get_0_1_2，并且可以查看到这确实是函数类型。但与一般的函数不同的是，get_0_1_2的函数体内使用了关键字yield，这使得get_0_1_2成为了一个生成器函数。生成器函数的特性如下：

调用生成器函数将返回一个生成器；

	>>> generator =get\_0\_1\_2()
	>>> generator
	<generator objectget_0_1_2 at 0x00B1C7D8>

第一次调用生成器的next方法时，生成器才开始执行生成器函数（而不是构建生成器时），直到遇到yield时暂停执行（挂起），并且yield的参数将作为此次next方法的返回值； 

之后每次调用生成器的next方法，生成器将从上次暂停执行的位置恢复执行生成器函数，直到再次遇到yield时暂停，并且同样的，yield的参数将作为next方法的返回值；

	>>> generator.next()
	1
	>>> generator.next()
	2

如果当调用next方法时生成器函数结束（遇到空的return语句或是到达函数体末尾），则这次next方法的调用将抛出StopIteration异常（即for循环的终止条件）；

	>>> generator.next()
	Traceback (most recent call last):
	File"<stdin>", line 1, in<module>
	StopIteration

生成器函数在每次暂停执行时，函数体内的所有变量都将被封存(freeze)在生成器中，并将在恢复执行时还原，并且类似于闭包，即使是同一个生成器函数返回的生成器，封存的变量也是互相独立的。

我们的小例子中并没有用到变量，所以这里另外定义一个生成器来展示这个特点：    

	>>> def  fibonacci():
	...   a = b =1
	...	  yield a
	...   yield b
	...   while True:
	...     a, b = b, a+b
	...   yield b
	...
	>>> for num in fibonacci():
	...    if num > 100: break
	...    print num,
	...
	1123581321345589

看到while True可别太吃惊，因为生成器可以挂起，所以是延迟计算的，无限循环并没有关系。这个例子中我们定义了一个生成器用于获取斐波那契数列。


####生成器函数的FAQ

接下来我们来讨论一些关于生成器的有意思的话题。

1)你的例子里生成器函数都没有参数，那么生成器函数可以带参数吗？
当然可以啊亲，而且它支持函数的所有参数形式。要知道生成器函数也是函数的一种：）

	>>> def counter(start=0):
	...     while True:
	...         yield start
	...         start += 1
	...

这是一个从指定数开始的计数器。

2)既然生成器函数也是函数，那么它可以使用return输出返回值吗？       
不行的亲，是这样的，生成器函数已经有默认的返回值——生成器了，你不能再另外给一个返回值；对，即使是return None也不行。但是它可以使用空的return语句结束。如果你坚持要为它指定返回值，那么Python将在定义的位置赠送一个语法错误异常，就像这样：    

	>>> def i_wanna_return():
	...     yield None
	...     return None
	...
	File"<stdin>", line 3
	SyntaxError: 'return'with argument inside generator

3)好吧，那人家需要确保释放资源，需要在try...finally中yield，这会是神马情况？（我就是想玩你）我在finally中还yield了一次！       
Python会在真正离开try...finally时再执行finally中的代码，而这里遗憾地告诉你，暂停不算哦！所以结局你也能猜到吧！   

	>>> def play_u():
	...		try:
	...			yield 1
	...			yield 2
	...			yield 3
	...		finally:
	...			yield 0
	...
	>>> forval inplay_u(): printval,
	...
	1230

*这与return的情况不同。return是真正的离开代码块，所以会在return时立刻执行finally子句。     
*另外，“在带有finally子句的try块中yield”定义在PEP 342中，这意味着只有Python 2.5以上版本才支持这个语法，在Python 2.4以下版本中会得到语法错误异常。

4) 如果我需要在生成器的迭代过程中接入另一个生成器的迭代怎么办？写成下面这样好傻好天真。。

	>>> def sub_generator():
	...		yield 1
	...		yield 2
	...		for val in counter(10): yield val
	...

这种情况的语法改进已经被定义在[PEP 380：委托至子生成器的语法]中，据说会在Python 3.3中实现，届时也可能回馈到2.x中。实现后，就可以这么写了：  

	>>> def sub_generator():
	...		yield1
	...		yield2
	...		yield from counter(10)

	File"<stdin>", line 4
	yield from counter(10)
	^
	SyntaxError: invalid syntax
