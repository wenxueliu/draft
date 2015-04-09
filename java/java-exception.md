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