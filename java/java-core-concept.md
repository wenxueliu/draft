

现在感觉学习一门语言最重要的是模型，比如 Netty 如何建立一个连接，如何处理连接流程是怎么样的，非常重要。


* Enum 使用
* Netty 库
* concurrent Thread 
* 参数是传值，但当为对象时，是对象的引用，这点非常重要，要仔细理解
* 没有显示的 new 一个对象，都是对前面对象的引用。
* 接口
* 泛型






单继承特性

类调用顺序

1 成员变量
2 构造函数
3 方法


初始化基类，必会先初始化父类，如果没有显示地调用父类的构造函数，将调用父类的默认构造函数

关键字 super 可被用来引用该类的父类，它被用来引用父类的成员变量或方法。

super.method()格式的调用，如果对象已经具有父类类型，那么它的方法的整个行为都将被调用，也包括其所有负面效果。该方法不必在父类中定义，它也可以从某些祖先类中继承。也就是说可以从父类的父类去获取，具有追溯性，一直向上去找，直到找到为止，这是一个很重要的特点。


重载的规则：

    方法名称必须相同
    参数列表必须不同（个数不同，或类型不同，或参数排列顺序不同）。
    方法的返回类型可以相同也可以不相同。仅仅返回类型不同不足以成为方法的重载。



覆盖

    覆盖方法的返回类型、方法名称、参数列表必须与它所覆盖的方法的相同。
    覆盖方法不能比它所覆盖的方法访问性差（即访问权限不允许缩小）。
    覆盖方法不能比它所覆盖的方法抛出更多的异常。

方法覆盖称为动态多态，是一个运行时问题；方法重载称为静态多态， 是一个编译时问题。

instanceof 运算符功能：用来判断某个实例变量是否属于某种类的类型。


static 

    一个类的静态方法只能访问静态属性；
    一个类的静态方法不能够直接调用非静态方法；
    如访问控制权限允许，static 属性和方法可以使用对象名加“.”方式调用；当然也可以使用实例加“.”方式调用；
    静态方法中不存在当前对象，因而不能使用“this”，当然也不能使用”super”；
    静态方法不能被非静态方法覆盖；
    构造方法不允许声明为 static 的；
    局部变量不能使用static修饰。

final 

    final 标记的类不能被继承。
    final 标记的方法不能被子类重写。
    final 标记的变量（成员变量或局部变量）即成为常量，只能赋值一次。
    final 标记的成员变量必须在声明的同时赋值，如果在声明的时候没有赋值，那么只有 一次赋值的机会，而且只能在构造方法中显式赋值，然后才能使用。
    final 标记的局部变量可以只声明不赋值，然后再进行一次性的赋值。
    final 一般用于标记那些通用性的功能、实现方式或取值不能随意被改变的成分，以避免被误用，例如实现数学三角方法、幂运算等功能的方法，以及数学常量π=3.141593、e=2.71828 等。
	被标记为 static 或 private 的方法被自动地 final，因为动态联编在上述两种情况下都不能应用。
	
接口（interface）

	接口必须通过类来实现它的抽象方法，类实现接口的关键字为implements。
	一个类只能继承一个父类，但却可以实现多个接口。
	如果一个类不能实现该接口的所有抽象方法，那么这个类必须被定义为抽象方法。
	接口可以作为一个类型来使用，把接口作为方法的参数和返回类型。

抽象类

	抽象类可以为部分方法提供实现，避免了在子类中重复实现这些方法，提高了代码的可重用性，这是抽象类的优势；而接口中只能包含抽象方法，不能包含任何实现。
	一个类只能继承一个直接的父类（可能是抽象类），但一个类可以实现多个接口，这个就是接口的优势。
	
	
接口和抽象的选择


    行为模型应该总是通过接口而不是抽象类定义。所以通常是：优先选用接口，尽量少用抽象类。
    选择抽象类的时候通常是如下情况：需要定义子类的行为，又要为子类提供共性的功能。

override

Use it every time you override a method for two benefits. Do it so that you can take advantage of the compiler checking to make sure you actually are overriding a method when you think you are. This way, if you make a common mistake of misspelling a method name or not correctly matching the parameters, you will be warned that you method does not actually override as you think it does. Secondly, it makes your code easier to understand because it is more obvious when methods are overwritten.


##路径

###类加载目录(即当运行某一类时获得其装载目录)

不论是一般的java项目还是web项目,先定位到能看到包路径的第一级目录
   
        InputStream is=ReadWrite.class.getClassLoader().getResourceAsStream("DeviceNO");
        
   	其中，DeviceNO文件的路径为 项目名\src\DeviceNO;类ReadWrite所在包的第一级目录位于src目录下。
   
与1相似，不同的是此方法必须以'/'开头

    	InputStream is=ReadWrite.class.getResourceAsStream("DeviceNO");
    
    其中，DeviceNO文件的路径为 项目名\src\DeviceNO;类ReadWrite所在包的第一级目录位于src目录下。 

###类路径（ classpath）的获取

    Thread.currentThread().getContextClassLoader().getResource("").getPath()
     例如：
     String path=Thread.currentThread().getContextClassLoader().getResource("").getPath();
     System.out.println(path);
     打印:“/D:/windpower/WebRoot/WEB-INF/classes/” 






[微学苑4,5,6章](http://www.weixueyuan.net/java/rumen/)
[w3cschool java](http://www.w3cschool.cc/java/java-tutorial.html)
