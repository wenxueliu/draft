##异常分类

　在Java中异常被当做对象来处理，根类是java.lang.Throwable类，在Java中定义了很多异常类（如OutOfMemoryError、NullPointerException、IndexOutOfBoundsException等），这些异常类分为两大类：Error和Exception。

　　Error是无法处理的异常，比如OutOfMemoryError，一般发生这种异常，JVM会选择终止程序。因此我们编写程序时不需要关心这类异常。

　　Exception，也就是我们经常见到的一些异常情况，比如NullPointerException、IndexOutOfBoundsException，这些异常是我们可以处理的异常。

　　Exception类的异常包括checked exception和unchecked exception（unchecked exception也称运行时异常RuntimeException，当然这里的运行时异常并不是前面我所说的运行期间的异常，只是Java中用运行时异常这个术语来表示，Exception类的异常都是在运行期间发生的）。

　　unchecked exception（非检查异常），也称运行时异常（RuntimeException），比如常见的NullPointerException、IndexOutOfBoundsException。对于运行时异常，java编译器不要求必须进行异常捕获处理或者抛出声明，由程序员自行决定。

　　checked exception（检查异常），也称非运行时异常（运行时异常以外的异常就是非运行时异常），java编译器强制程序员必须进行捕获处理，比如常见的IOExeption和SQLException。对于非运行时异常如果不进行捕获或者抛出声明处理，编译都不会通过。



##Checked异常和Runtime异常体系

java异常被分为两大类：Checked异常和Runtime异常（运行时异常）。

所有RuntimeException类及其子类的实例被称为unChecked异常，不是RuntimeException类及其子类的异常实例则被称为Checked异常。

只有java语言提供了Checked异常，其他语言都没有提供，java认为Checked异常都是可以被处理（修复）的异常，所以 java 程序无须显式的处理 Checked 异常。如果程序没有处理 Checked 异常，该程序在编译时就会发生错误，无法通过编译。

Checked异常的处理方式：

* 当方法明确知道如何处理异常，程序应该使用try...catch块来捕获该异常，然后在对应的catch块中修补该异常。
* 当方法不知道如何处理异常，应该在定义该方法时声明抛出该异常。

Runtime 异常无须显式声明抛出，如果程序需要捕捉 Runtime 异常，也可以使用try...catch块来捕获 Runtime 异常。

问题是：大部分的方法总是不能明确知道如何处理异常，这就只能声明抛出异常了。


也就说在Java中进行异常处理的话，对于可能会发生异常的代码，可以选择三种方法来进行异常处理：

1）对代码块用try..catch进行异常捕获处理；

2）在 该代码的方法体外用throws进行抛出声明，告知此方法的调用者这段代码可能会出现这些异常，你需要谨慎处理。此时有两种情况：

如果声明抛出的异常是非运行时异常，此方法的调用者必须显示地用try..catch块进行捕获或者继续向上层抛出异常。

如果声明抛出的异常是运行时异常，此方法的调用者可以选择地进行异常捕获处理。

3）在代码块用throw手动抛出一个异常对象，此时也有两种情况，跟2）中的类似：

如果抛出的异常对象是非运行时异常，此方法的调用者必须显示地用try..catch块进行捕获或者继续向上层抛出异常。

如果抛出的异常对象是运行时异常，此方法的调用者可以选择地进行异常捕获处理。

（如果最终将异常抛给main方法，则相当于交给jvm自动处理，此时jvm会简单地打印异常信息）


##在类继承的时候，方法覆盖时如何进行异常抛出声明

1）父类的方法没有声明异常，子类在重写该方法的时候不能声明异常；

2）如果父类的方法声明一个异常exception1，则子类在重写该方法的时候声明的异常不能是exception1的父类；

3）如果父类的方法声明的异常类型只有非运行时异常（运行时异常），则子类在重写该方法的时候声明的异常也只能有非运行时异常（运行时异常），不能含有运行时异常（非运行时异常）。



##注意事项

* 注意catch块的顺序,不要把上层类的异常放在最前面的catch块。

* 异常处理尽量放在高层进行

* finally中释放资源

##声明异常和未声明异常的区别

Java可以在方法签名上显式地声明可能抛出的异常，但也允许抛出某些未声明的异常。那么，二者有何区别呢？

我们自己在设计一个方法时如何决定是否在方法上声明某个异常呢？本质上讲，在方法签名上声明的异常属于
方法接口的一部分，**它和方法的返回值处于同一抽象层次，不随具体实现的变化而改变**。比如，Integer类用于
解析一个字符串到Integer型整数的valueOf方法：

    public static Integer valueOf(String s) throws NumberFormatException

它声明抛出的 NumberFormatException 属于这个方法接口层面的一种失败情况，不管内部实现采用什么解析方法，
都必然存在输入字符串不是合法整数这种情况，所以这时把这个异常声明出来就非常合理。

相反，下面这个从帐户 a 向帐户 b 转账的 transfer 方法：

    public boolean transfer(Account a, Account b, Money money) throws SQLException

它抛出 SQLException 就不对了，因为 SQLException 不属于这个 transfer 接口层面的概念，而属于具体实现，
很有可能未来某个实现不用 SQL 了那么这个异常也就不存在了。这种情况下，就应该捕获 SQLException，然后
抛出自定义异常 TransferException，其中 TransferException 可以定义几种和业务相关的典型错误情况，比如
金额不足，帐户失效，通信故障，同时它还可以引用 SQLException 作为触发原因(Cause)。

    public boolean transfer(Account a, Account b, Money money) throws TransferException {
        try {
            ...
            executeSQL(...);
        } catch (SQLException e) {
            throw new TransferException("...", e);
        }
    }


##什么情况下方法应该抛出未声明的异常？

前面谈到在编写一个方法时，声明异常属于接口的一部分，不随着具体实现而改变，但是我们知道 Java 允许抛出
未声明的 RuntimeException，那么什么情况下会这样做呢？ 比如，下面的例子中方法 f 声明了 FException，但
是它的实现中可能抛出 RuntimeException，这是什么意思呢？

    void f() throws FException {
        if (...) {
            throw new RuntimeException("...");
        }
    }

根据上面提到的原理，未声明异常是和实现相关的，有可能随着不同实现而出现或消失，同时它又对应不到 FException。
比如，f 方法依赖于对象 a，结果在运行时 a 居然是 null，导致本方法无法完成相应功能，这就可以成为一种未声明的
RuntimeException了（当然，更常见的是直接调用 a 的方法，然后触发 NullPointerException）。

其实，很多情况下抛出未声明的 RuntimeException 的语义和 Error 非常接近，只是没有 Error 那么强烈，方法的使用
者可以根据情况来处理，不是一定要停止整个程序。我们最常见的 RuntimeException 可能要算 NullPointerException了，
通常都是程序 Bug 引起的，如果是 C/C++ 就已经 crash 了，Java 给了你一个选择如何处理的机会。

所以，抛出未声明异常表示遇到了和具体实现相关的运行时错误，它不是在设计时就考虑到的方法接口的一部分，所以又
被称为是不可恢复的异常。有些Java程序员为了简便不声明异常而直接抛出RuntimeException的做法从设计上是不可取的。


##如何捕获和处理其他方法抛出的异常？

下面例子中方法g声明了GException，方法f声明了FException，而f在调用g的时候不管三七二十一通过catch (Exception e)捕获了所有的异常。

    void g() throws GException
    void f() throws FException {
        try {
            g();
        } catch (Exception e) {
            ...
        }
        ....
    }

这种做法是很多人的习惯性写法，它的问题在哪里呢？问题就在于g明明已经告诉你除了GException外，如果抛出未声明的
RuntimeException 就表示遇到了错误，很可能是程序有 Bug，这时f还不顾一切继续带着Bug跑。所以，除非有特殊理由，
对具体情况做了分析判断，一般不捕获未声明异常，让它直接抛出就行。

    void g() throws GException
    void f() throws FException {
        try {
            g();
        } catch (GException e) {
            ...
        }
        ....
    }

但是，很遗憾有一种很典型的情况是g()是不受自己控制的代码，它虽然只声明了抛出GException，实际上在实现的时候抛出
了未声明的但属于接口层面而应该声明的异常。如果遇到这种情况最好的做法是应该告诉g()的作者修改程序声明出这些异常，
如果实在不行也只能全部捕获了。但是，对于自己写的程序来讲，一定要严格区别声明异常和未声明异常的处理，这样做的
目的是理清Exception和Bug的界限。


##自定义异常应继承Exception还是RuntimeException?

Java 中区分 Checked Exception 和 Unchecked Exception，前者继承于 Exception，后者继承于 RuntimeException。
Unchecked Exception和Runtime Exception在Java中常常是指同一个意思。

    public boolean createNewFile() throws IOException

上面的 IOException 就是一个著名的 Checked Exception。Java 编译器对 Checked Exception 的约束包括两方面：对于方法
编写者来讲，Checked Exception 必须在方法签名上声明；对于方法调用者来讲，调用抛出 Checked Exception的方法必须用
try-catch捕获异常或者继续声明抛出。相反，Unchecked Exception则不需要显式声明，也不强制捕获。

Checked Exception 的用意在于明确地提醒调用者去处理它，防止遗漏。但是 Checked Exception 同时也给调用者带来了负担，
通常会导致层层的 try-catch，降低代码的可读性，前面例子中的 Integer.valueOf 方法虽然声明了 NumberFormatException，
但是它是一个RuntimeException，所以使用者不是必须用 try-catch 去捕获它。

实际上，对于自己编写的异常类来讲，推荐默认的是继承 RuntimeException，除非有特殊理由才继承 Exception。C# 中没有
Checked Exception的概念，这种推荐的做法等于是采用了C#的设计理念：把是否捕获和何时捕获这个问题交给使用者决定，
不强制使用者。当然，如果某些情况下明确提醒捕获更加重要还是可以采用 Checked Exception的。对于编写一个方法来讲，
"是否在方法上声明一个异常"这个问题比“是否采用Checked Exception”更加重要。

##总结

本文介绍了自己总结的Java异常处理的主要原理和原则，主要回答了这几个主要的问题：1)Exception和Error的区别；2)声明异常和未声明异常的区别；3)什么情况下应抛出未声明异常；4)理解如何捕获和处理其他方法抛出的异常；5)自定义异常应继承Exception还是RuntimeException。最后需要说的是，虽然有这些原理和原则可以指导，但是异常处理本质上还是一个需要根据具体情况仔细推敲的问题，这样才能作出最合适的设计。




