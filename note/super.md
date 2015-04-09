###问题的发现与提出

在Python类的方法（method）中，要调用父类的某个方法，在Python 2.2以前，通常的写法如代码段1：

 代码段1：
	class A:
	  def __init__(self):
	   print "enter A"
	   print "leave A"

	 class B(A):
	  def __init__(self):
	   print "enter B"
	   A.__init__(self)
	   print "leave B"

	 >>> b = B()
	 enter B
	 enter A
	 leave A
	 leave B

即，使用非绑定的类方法（用类名来引用的方法），并在参数列表中，引入待绑定的对象（self），从而达到调用父类的目的。

这样做的缺点是，当一个子类的父类发生变化时（如类B的父类由A变为C时），必须遍历整个类定义，把所有的通过非绑定的方法的类名全部替换过来，例如代码段2，

代码段2：

	class B(C):    # A --> C
	  def __init__(self):
	   print "enter B"
	   C.__init__(self) # A --> C
	   print "leave B"

如果代码简单，这样的改动或许还可以接受。但如果代码量庞大，这样的修改可能是灾难性的。

因此，自Python 2.2开始，Python添加了一个关键字super，来解决这个问题。下面是Python 2.3的官方文档说明：

	 super(type[, object-or-type])

	  Return the superclass of type. If the second argument is omitted the super object
	  returned is unbound. If the second argument is an object, isinstance(obj, type) 
	  must be true. If the second argument is a type, issubclass(type2, type) must be 
	  true. super() only works for new-style classes.

	  A typical use for calling a cooperative superclass method is:

	   class C(B):
		   def meth(self, arg):
		       super(C, self).meth(arg)

	  New in version 2.2.

从说明来看，可以把类B改写如代码段3：

代码段3：

	class A(object):    # A must be new-style class
	  def __init__(self):
	   print "enter A"
	   print "leave A"

	class B(C):     # A --> C
	  def __init__(self):
	   print "enter B"
	   super(B, self).__init__()
	   print "leave B"

尝试执行上面同样的代码，结果一致，但修改的代码只有一处，把代码的维护量降到最低，是一个不错的用法。因此在我们的开发过程中，super关键字被大量使用，而且一直表现良好。

在我们的印象中，对于super(B, self).__init__()是这样理解的：super(B, self)首先找到B的父类（就是类A），然后把类B的对象self转换为类A的对象（通过某种方式，一直没有考究是什么方式，惭愧），然后“被转换”的类A对象调用自己的__init__函数。考虑到super中只有指明子类的机制，因此，在多继承的类定义中，通常我们保留使用类似代码段1的方法。

有一天某同事设计了一个相对复杂的类体系结构（我们先不要管这个类体系设计得是否合理，仅把这个例子作为一个题目来研究就好），代码如代码段4：

代码段4：

	class A(object):
	  def __init__(self):
	   print "enter A"
	   print "leave A"

	 class B(object):
	  def __init__(self):
	   print "enter B"
	   print "leave B"

	 class C(A):
	  def __init__(self):
	   print "enter C"
	   super(C, self).__init__()
	   print "leave C"

	 class D(A):
	  def __init__(self):
	   print "enter D"
	   super(D, self).__init__()
	   print "leave D"

	 class E(B, C):
	  def __init__(self):
	   print "enter E"
	   B.__init__(self)
	   C.__init__(self)
	   print "leave E"

	 class F(E, D):
	  def __init__(self):
	   print "enter F"
	   E.__init__(self)
	   D.__init__(self)
	   print "leave F"

  	 f = F() 

输出：

	 enter F
	 enter E
	 enter B
	 leave B
	 enter C
	 enter D
	 enter A
	 leave A
	 leave D
	 leave C
	 leave E
	 enter D
	 enter A
	 leave A
	 leave D
	 leave F


明显地，类A和类D的初始化函数被重复调用了2次，这并不是我们所期望的结果！我们所期望的结果是最多只有类A的初始化函数被调用2次——其实这是多继承的类体系必须面对的问题。我们把代码段4的类体系画出来，如下图：

		object
	   |       \
	   |        A
	   |      / |
	   B     C  D
		\   /   |
		  E     |
		    \   |
		      F

按我们对super的理解，从图中可以看出，在调用类C的初始化函数时，应该是调用类A的初始化函数，但事实上却调用了类D的初始化函数。好一个诡异的问题！

也就是说，mro中记录了一个类的所有基类的类类型序列。查看mro的记录，发觉包含7个元素，7个类名分别为：

 	F E B C D A object

从而说明了为什么在C.__init__中使用super(C, self).__init__()会调用类D的初始化函数了。 

我们把代码段4改写为：

代码段9：

	class A(object):
	  	def __init__(self):
	   		print "enter A"
	   		super(A, self).__init__()  # new
	   		print "leave A"

	class B(object):
	  	def __init__(self):
	   		print "enter B"
	   		super(B, self).__init__()  # new
	   		print "leave B"

	class C(A):
	  	def __init__(self):
	  		print "enter C"
	   		super(C, self).__init__()
	   		print "leave C"

	class D(A):
	  	def __init__(self):
	   		print "enter D"
	   		super(D, self).__init__()
	   		print "leave D"

	class E(B, C):
		def __init__(self):
	   		print "enter E"
	   		super(E, self).__init__()  # change
	   		print "leave E"

	class F(E, D):
	  	def __init__(self):
	   		print "enter F"
	   		super(F, self).__init__()  # change
	   		print "leave F"


	f = F() 

结果:

	 enter F
	 enter E
	 enter B
	 enter C
	 enter D
	 enter A
	 leave A
	 leave D
	 leave C
	 leave B
	 leave E
	 leave F



　　明显地，F的初始化不仅完成了所有的父类的调用，而且保证了每一个父类的初始化函数只调用一次。

　　再看类结构：


    object
     /   \
    /      A
   |     /   \
  B-1  C-2   D-2
    \   /    /
     E-1    /
        \  /
          F


E-1,D-2是F的父类，其中表示E类在前，即F（E，D）。

所以初始化顺序可以从类结构图来看出 ： F --> E --> B -->C --> D --> A

由于C，D有同一个父类，因此会先初始化D再是A。

###延续的讨论

我们再重新看上面的类体系图，如果把每一个类看作图的一个节点，每一个从子类到父类的直接继承关系看作一条有向边，那么该体系图将变为一个有向图。不难发现mro的顺序正好是该有向图的一个拓扑排序序列。

从而，我们得到了另一个结果——Python是如何去处理多继承。支持多继承的传统的面向对象程序语言（如C++）是通过虚拟继承的方式去实现多继承中父类的构造函数被多次调用的问题，而Python则通过MRO的方式去处理。

但这给我们一个难题：对于提供类体系的编写者来说，他不知道使用者会怎么使用他的类体系，也就是说，不正确的后续类，可能会导致原有类体系的错误，而且这样的错误非常隐蔽的，也难于发现。

####MRO

Method resolution order是python用来解析方法调用顺序的。MRO对于多重继承中方法调用异常重要。python中有一个内建函数和MRO密切相关——super。顾名思义，super看上去应该是调用父类的方法，通常情况下也是如此。来看一段代码：

    class A(object):  
        def __init__(self):  
            print 'A.__init__'  
    class B(A):  
        def __init__(self):  
            print 'B.__init__'  
            # try to call parent's __init__ without explicitly reference class A  
            super(B, self).__init__()  

    >>> x = B()  
    B.__init__  
    A.__init__  

如前所述，这里我们通过super来调用父类的__init__，super(B, self)返回一个bounded对象（因为我们传入了self)。

从输出可以看到，调用正确。就像我们直接调用A.__init__(self)一样。

这样做的好处是，可以不用直接引用基类的名称就可以调用基类的方法。如果我们改变了基类的名称，那么所有子类的调用将不用改变。

但是super其实并不是我们想的那么简单，super不是简单地调用所谓基类的方法，而是调用MRO中的下一个类的方法，也就是类似于next的方法。

    class A(object):  
        def __init__(self):  
            print "A"  
            super(A, self).__init__()  
    class B(object):  
        def __init__(self):  
            print "B"  
            super(B, self).__init__()  
    class C(A):  
        def __init__(self, arg):  
            print "C","arg=",arg  
            super(C, self).__init__()  
    class D(B):  
        def __init__(self, arg):  
            print "D", "arg=",arg  
            super(D, self).__init__()  
    class E(C,D):  
        def __init__(self, arg):  
            print "E", "arg=",arg  
            super(E, self).__init__(arg)  
    #print "MRO:", [x.__name__ for x in E.__mro__]  
    E(10)  

对于这段代码，我们可能期望输出像这样：

    E arg= 10  
    C arg= 10  
    A  
    D arg= 10  
    B  

但事实上，这段代码会引发错误，因为python没有像我们想的那样调用正确的函数。

    E arg= 10  
    C arg= 10  
    A  
    Traceback (most recent call last):  
      File "C:/Users/Administrator/Desktop/example1-2.py", line 27, in <module>  
        E(10)  
      File "C:/Users/Administrator/Desktop/example1-2.py", line 24, in __init__  
        super(E, self).__init__(arg)  
      File "C:/Users/Administrator/Desktop/example1-2.py", line 14, in __init__  
        super(C, self).__init__()  
      File "C:/Users/Administrator/Desktop/example1-2.py", line 4, in __init__  
        super(A, self).__init__()  
    TypeError: __init__() takes exactly 2 arguments (1 given)  

我们先给出上面的代码中注释掉的输出mro的语句的输出：

    MRO: ['E', 'C', 'A', 'D', 'B', 'object']  

出错的原因是因为调用继续到A.__init__时，我们调用了super(A,self).__init__。记得上面我们说过super类似于next函数，是调用mro中下一个类型的方法。

这里我们给出的类型是A，那么mro中下一个类型就是D，很显然，super将会调用D.__init__(self)。可是，D.__init__却接受一个额外的参数arg，所以调用错误。

super并不像它的名字那样，只调用父类的方法，而是调用MRO中，下一个类型的方法。

一个常见的错误是，如果基类的父类是object，一般会忽略super()的调用。比如上面改为如下

    class A(object):  
        def __init__(self):  
            print "A"  
            #super(A, self).__init__()  
    class B(object):  
        def __init__(self):  
            print "B"  
            #super(B, self).__init__()  
    class C(A):  
        def __init__(self, arg):  
            print "C","arg=",arg  
            super(C, self).__init__()  
    class D(B):  
        def __init__(self, arg):  
            print "D", "arg=",arg  
            super(D, self).__init__()  
    class E(C,D):  
        def __init__(self, arg):  
            print "E", "arg=",arg  
            super(E, self).__init__(arg)  
    #print "MRO:", [x.__name__ for x in E.__mro__]  
    E(10)  

输出为：

	MRO: ['E', 'C', 'A', 'D', 'B', 'object']
	E arg= 10
	C arg= 10
	A
显然不是我们所期望的。

[reference](https://fuhm.net/super-harmful/)中的链接中给出了使用super的建议，可以作为参考。

 
####小结

1. super并不是一个函数，是一个类名，形如super(B, self)事实上调用了super类的初始化函数，产生了一个super对象；
2. super类的初始化函数并没有做什么特殊的操作，只是简单记录了类类型和具体实例；
3. super(B, self).func的调用并不是用于调用当前类的父类的func函数；
4. Python的多继承类是通过mro的方式来保证各个父类的函数被逐一调用，而且保证每个父类函数只调用一次（如果每个类都使用super）；
5. 混用super类和非绑定的函数是一个危险行为，这可能导致应该调用的父类函数没有调用或者一个父类函数被调用多次。
6. 如果类被设计成使用了super，那么所有子类也必须要调用super，否则直接调用会出现重复调用的问题,super调用的目标函数通常是用 *args, **kwargs 作为参数，这样可以解决目标函数参数匹配的问题


参考文献：
[Python's Super Considered Harmful]()
http://www.cnblogs.com/lovemo1314/archive/2011/05/03/2035005.html 
http://blog.csdn.net/seizef/article/details/5310107
book:Core python programming

####MRO Implementation

这个mro是根据The Python 2.3 Method Resolution Order中的描述，自己写出来的。该paper中也有相关的实现，而且更加精巧。

[python] view plaincopyprint?

    import inspect  
    def compute_linearization(kls):  
        """ 
        Given a class object, calculate the mro of the class 
        A linerization is defined as the class plus the merge of the linerization of all bases and the list of bases 
        """  
        if inspect.isclass(kls):  
            mro = [kls]  
            # for each base class, we need to compute the linerization  
            merge_list = []  
            for basekls in kls.__bases__:  
                merge_list.append(compute_linearization(basekls))  
            # add all bases to the merge list  
            merge_list.append([])  
            for basekls in kls.__bases__:  
                merge_list[-1].append(basekls)  
            return mro + merge(merge_list)  
        else:  
            raise TypeError("argument must a class object")  
    """ 
    take the head of the first list, i.e L[B1][0]; if this head is not in the tail of any of the other lists, then add it to the linearization of C and remove it from the lists in the merge, otherwise look at the head of the next list and take it, if it is a good head. Then repeat the operation until all the class are removed or it is impossible to find good heads. In this case, it is impossible to construct the merge, Python 2.3 will refuse to create the class C and will raise an exception. 
    """  
    def merge(merge_list):  
        res = []  
        while True:  
            processed = False  
            has_good_head = False  
            for i, l in enumerate(merge_list):  
                if len(l):  
                    # mark for processing  
                    processed = True  
                    head = l[0]  
                    is_good_head = True  
                    other_lists = merge_list[0:i] + merge_list[i+1:]  
                    # check if the head is in the tail of other lists   
                    for rest in other_lists:  
                        if head in rest[1:]:  
                            is_good_head = False  
                            break  
                    # if is a good head, then need to remove it from other lists  
                    if is_good_head:  
                        # save the head to the result list  
                        has_good_head = True  
                        res.append(head)  
                        for al in merge_list:  
                            if len(al) and al[0] == head:  
                                del al[0]  
                        break  
                    # else skip to the next list  
            if not has_good_head:  
                raise TypeError("MRO error")  
            if not processed:  
                break  
        return res  

