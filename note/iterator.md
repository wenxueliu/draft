
###迭代器(Iterator)概述

迭代器是访问集合内元素的一种方式。迭代器对象从集合的第一个元素开始访问，直到所有的元素都被访问一遍后结束。
迭代器不能回退，只能往前进行迭代。这并不是什么很大的缺点，因为人们几乎不需要在迭代途中进行回退操作。
迭代器也不是线程安全的，在多线程环境中对可变集合使用迭代器是一个危险的操作。但如果小心谨慎，或者干脆贯彻函数式思想坚持使用不可变的集合，那这也不是什么大问题。
对于原生支持随机访问的数据结构（如tuple、list），迭代器和经典for循环的索引访问相比并无优势，反而丢失了索引值（可以使用内建函数enumerate()找回这个索引值，这是后话）。但对于无法随机访问的数据结构（比如set）而言，迭代器是唯一的访问元素的方式。
迭代器的另一个优点就是它不要求你事先准备好整个迭代过程中所有的元素。迭代器仅仅在迭代至某个元素时才计算该元素，而在这之前或之后，元素可以不存在或者被销毁。这个特点使得它特别适合用于遍历一些巨大的或是无限的集合，比如几个G的文件，或是斐波那契数列等等。这个特点被称为延迟计算或惰性求值(Lazy evaluation)。
迭代器更大的功劳是提供了一个统一的访问集合的接口。只要是实现了__iter__()方法的对象，就可以使用迭代器进行访问。


###使用内建的工厂函数iter(iterable)可以获取迭代器对象：

	>>> lst =range(2)
	>>> it =iter(lst)
	>>> it
	<listiterator objectat 0x00BB62F0>


使用迭代器的next()方法可以访问下一个元素：

	>>> it.next()
	0

如果是Python 2.6+，还有内建函数next(iterator)可以完成这一功能：

	>>> next(it)
	1

如何判断迭代器还有更多的元素可以访问呢？Python里的迭代器并没有提供类似has_next()这样的方法。
那么在这个例子中，我们已经访问到了最后一个元素1，再使用next()方法会怎样呢？

	>>> it.next()
	Traceback (most recent call last):
	File"<stdin>", line 1, in<module>
	StopIteration

Python遇到这样的情况时将会抛出StopIteration异常。事实上，Python正是根据是否检查到这个异常来决定是否停止迭代的。   
这种做法与迭代前手动检查是否越界相比各有优点。但Python的做法总有一些利用异常进行流程控制的嫌疑。
了解了这些情况以后，我们就能使用迭代器进行遍历了。

	it =iter(lst)
	try:
		while True:
			val =it.next()
			print val
	except StopIteration:
		pass

实际上，因为迭代操作如此普遍，Python专门将关键字for用作了迭代器的语法糖。在for循环中，Python将自动调用工厂函数iter()获得迭代器，自动调用next()获取元素，还完成了检查StopIteration异常的工作。上述代码可以写成如下的形式，你一定非常熟悉：

	for val in lst:
		print val

首先Python将对关键字in后的对象调用iter函数获取迭代器，然后调用迭代器的next方法获取元素，直到抛出StopIteration异常。对迭代器调用iter函数时将返回迭代器自身，所以迭代器也可以用于for语句中，不需要特殊处理。
常用的几个内建数据结构tuple、list、set、dict都支持迭代器，字符串也可以使用迭代操作。你也可以自己实现一个迭代器，如上所述，只需要在类的__iter__方法中返回一个对象，这个对象拥有一个next()方法，这个方法能在恰当的时候抛出StopIteration异常即可。但是需要自己实现迭代器的时候不多，即使需要，使用生成器会更轻松。

*异常并不是非抛出不可的，不抛出该异常的迭代器将进行无限迭代，某些情况下这样的迭代器很有用。这种情况下，你需要自己判断元素并中止，否则就死循环了！
使用迭代器的循环可以避开索引，但有时候我们还是需要索引来进行一些操作的。这时候内建函数enumerate就派上用场咯，它能在 iter 函数的结果前加上索引，以元组返回，用起来就像这样：

	for idx, ele in enumerate(lst):
		print idx, ele

###生成器表达式(Generator expression)和列表解析(List Comprehension)

绝大多数情况下，遍历一个集合都是为了对元素应用某个动作或是进行筛选。如果看过本文的第二部分，你应该还记得有内建函数map和filter提供了这些功能，但Python仍然为这些操作提供了语言级的支持。

	(x+1 for x in lst) #生成器表达式，返回迭代器。外部的括号可在用于参数时省略。
	[x+1 for x in lst] #列表解析，返回list

如你所见，生成器表达式和列表解析（注：这里的翻译有很多种，比如列表展开、列表推导等等，指的是同一个意思）的区别很小，所以人们提到这个特性时，简单起见往往只描述成列表解析。然而由于返回迭代器时，并不是在一开始就计算所有的元素，这样能得到更多的灵活性并且可以避开很多不必要的计算，所以除非你明确希望返回列表，否则应该始终使用生成器表达式。接下来的文字里我就不区分这两种形式了：）
你也可以为列表解析提供if子句进行筛选：

​	(x+1 for x in lst if x != 0)

或者提供多条for子句进行嵌套循环，嵌套次序就是for子句的顺序：

	((x, y) forx inrange(3) fory inrange(x))

列表解析就是鲜明的Pythonic。我常遇到两个使用列表解析的问题，本应归属于最佳实践，但这两个问题非常典型，所以不妨在这里提一下：

第一个问题是，因为对元素应用的动作太复杂，不能用一个表达式写出来，所以不使用列表解析。这是典型的思想没有转变的例子，如果我们将动作封装成函数，那不就是一个表达式了么？
第二个问题是，因为if子句里的条件需要计算，同时结果也需要进行同样的计算，不希望计算两遍，就像这样：

	( x.doSomething() for x in lst if x.doSomething() > 0 )	

这样写确实很糟糕，但组合一下列表解析即可解决：

	(x for x in (y.doSomething() for y in lst) if x>0)

内部的列表解析变量其实也可以用x，但为清晰起见我们改成了y。或者更清楚的，可以写成两个表达式：

	tmp =(x.doSomething() forx inlst)
	(x forx intmp ifx > 0)

列表解析可以替代绝大多数需要用到map和filter的场合，可能正因为此，著名的静态检查工具pylint将map和filter的使用列为了警告。

###相关的库

Python内置了一个模块itertools，包含了很多函数用于creating iterators for efficient looping（创建更有效率的循环迭代器），这说明很是霸气，这一小节就来浏览一遍这些函数并留下印象吧，需要这些功能的时候隐约记得这里面有就好。这一小节的内容翻译自itertools模块官方文档。

####无限迭代

count(start, [step])
	从start开始，以后每个元素都加上step。step默认值为1。     
	count(10) --> 10 11 12 13 14 ...
	cycle(p)

迭代至序列p的最后一个元素后，从p的第一个元素重新开始。

	cycle('ABCD') --> A B C D A B C D ...
	repeat(elem [,n])

将elem重复n次。如果不指定n，则无限重复。     

	repeat(10, 3) --> 10 10 10

####在最短的序列参数终止时停止迭代

* chain(p, q, ...)    迭代至序列p的最后一个元素后，从q的第一个元素开始，直到所有序列终止。

chain('ABC', 'DEF') --> A B C D E F
	
* compress(data, selectors)    如果bool(selectors[n])为True，则next()返回data[n]，否则跳过data[n]。

compress('ABCDEF', [1,0,1,0,1,1]) --> A C E F

* dropwhile(pred, seq)   当pred对seq[n]的调用返回False时才开始迭代。

dropwhile(lambda x: x<5, [1,4,6,4,1]) --> 6 4 1

* takewhile(pred, seq)   dropwhile的相反版本。

takewhile(lambda x: x<5, [1,4,6,4,1]) --> 1 4

* ifilter(pred, seq)  内建函数filter的迭代器版本。

ifilter(lambda x: x%2, range(10)) --> 1 3 5 7 9
ifilterfalse(pred, seq)       
ifilter的相反版本。
ifilterfalse(lambda x: x%2, range(10)) --> 0 2 4 6 8

* imap(func, p, q, ...)   内建函数map的迭代器版本。     

imap(pow, (2,3,10), (5,2,3)) --> 32 9 1000

* starmap(func, seq)   将seq的每个元素以变长参数(*args)的形式调用func。
starmap(pow, [(2,5), (3,2), (10,3)]) --> 32 9 1000

* izip(p, q, ...)    内建函数zip的迭代器版本。

izip('ABCD', 'xy') --> Ax By
izip_longest(p, q, ..., fillvalue=None)
izip的取最长序列的版本，短序列将填入fillvalue。
izip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-

* tee(it, n)   返回n个迭代器it的复制迭代器。

* groupby(iterable[, keyfunc])       

这个函数功能类似于SQL的分组。使用groupby前，首先需要使用相同的keyfunc对iterable进行排序，比如调用内建的sorted函数。然后，groupby返回迭代器，每次迭代的元素是元组(key值, iterable中具有相同key值的元素的集合的子迭代器)。或许看看Python的排序指南对理解这个函数有帮助。     
groupby([0, 0, 0, 1, 1, 1, 2, 2, 2]) --> (0, (0 0 0)) (1, (1 1 1)) (2, (2 2 2))
​
####组合迭代器

* product(p, q, ... [repeat=1])     笛卡尔积。
product('ABCD', repeat=2) --> AA AB AC AD BA BB BC BD CA CB CC CD DA DB DC DD

* permutations(p[, r])    去除重复的元素。
permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC

* combinations(p, r)  排序后去除重复的元素。
combinations('ABCD', 2) --> AB AC AD BC BD CD

* combinations_with_replacement()    排序后，包含重复元素。
combinations_with_replacement('ABCD', 2) --> AA AB AC AD BB BC BD CC CD DD


