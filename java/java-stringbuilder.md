




http://www.stormzhang.com/java/2014/08/08/java-string-stringbuilder-stringbuffer/




我们先要记住三者的特征：

* String 字符串常量
* StringBuffer 字符串变量（线程安全）
* StringBuilder 字符串变量（非线程安全）

##定义

查看API会发现，String、StringBuffer、StringBuilder都实现了 CharSequence接口，虽然它们都与字符串相关，但是其处理机制不同。

* String：是不可改变的量，也就是创建后就不能在修改了。
* StringBuffer：是一个可变字符串序列，它与String一样，在内存中保存的都是一个有序的字符串序列（char类型的数组），不同点是StringBuffer对象的值都是可变的。
* StringBuilder：与StringBuffer类基本相同，都是可变字符换字符串序列，不同点是StringBuffer是线程安全的，StringBuilder是线程不安全的。

在性能方面，由于String类的操作是产生新的String对象，而StringBuilder和StringBuffer只是一个字符数组的扩容而已，所以String类的操作要远慢于StringBuffer和StringBuilder。

##使用场景

    使用String类的场景：在字符串不经常变化的场景中可以使用String类，例如常量的声明、少量的变量运算。
    使用StringBuffer类的场景：在频繁进行字符串运算（如拼接、替换、删除等），并且运行在多线程环境中，则可以考虑使用StringBuffer，例如XML解析、HTTP参数解析和封装。
    使用StringBuilder类的场景：在频繁进行字符串运算（如拼接、替换、和删除等），并且运行在单线程的环境中，则可以考虑使用StringBuilder，如SQL语句的拼装、JSON封装等。

##分析

###可变与不可变

　　String类中使用字符数组保存字符串，如下就是，因为有“final”修饰符，所以可以知道string对象是不可变的。

　　　　private final char value[];

　　StringBuilder与StringBuffer都继承自AbstractStringBuilder类，在AbstractStringBuilder中也是使用字符数组保存字符串，如下就是，可知这两种对象都是可变的。

　　　　char[] value;

###是否多线程安全

String中的对象是不可变的，也就可以理解为常量，显然线程安全。

AbstractStringBuilder是StringBuilder与StringBuffer的公共父类，定义了一些字符串的基本操作，如expandCapacity、append、insert、indexOf等公共方法。

StringBuffer对方法加了同步锁或者对调用的方法加了同步锁，所以是线程安全的。看如下源码：

    public synchronized StringBuffer reverse() {
        super.reverse();
        return this;
    }

    public int indexOf(String str) {
        return indexOf(str, 0);        
        //存在 public synchronized int indexOf(String str, int fromIndex) 方法
    }

StringBuilder并没有对方法进行加同步锁，所以是非线程安全的。



简要的说， String 类型和 StringBuffer 类型的主要性能区别其实在于 String 是不可变的对象, 因此在每次对 String 类型进行改
变的时候其实都等同于生成了一个新的 String 对象，然后将指针指向新的 String 对象。所以经常改变内容的字符串最好不要用 String 
，因为每次生成对象都会对系统性能产生影响，特别当内存中无引用对象多了以后， JVM 的 GC 就会开始工作，那速度是一定会相当慢的。

而如果是使用 StringBuffer 类则结果就不一样了，每次结果都会对 StringBuffer 对象本身进行操作，而不是生成新的对象，再改变对
象引用。所以在一般情况下我们推荐使用 StringBuffer ，特别是字符串对象经常改变的情况下。而在某些特别情况下， String 对象的字
符串拼接其实是被 JVM 解释成了 StringBuffer 对象的拼接，所以这些时候 String 对象的速度并不会比 StringBuffer 对象慢，而特
别是以下的字符串对象生成中， String 效率是远要比 StringBuffer 快的：

    String S1 = “This is only a” + “ simple” + “ test”;
    StringBuffer Sb = new StringBuilder(“This is only a”).append(“ simple”).append(“ test”);

你会很惊讶的发现，生成 String S1 对象的速度简直太快了，而这个时候 StringBuffer 居然速度上根本一点都不占优势。其实这是 JVM 的一个把戏，在 JVM 眼里，这个

    String S1 = “This is only a” + “ simple” + “test”;

其实就是
    
    String S1 = “This is only a simple test”;

所以当然不需要太多的时间了。但大家这里要注意的是，如果你的字符串是来自另外的 String 对象的话，速度就没那么快了，譬如：

    String S2 = “This is only a”;
    String S3 = “ simple”;
    String S4 = “ test”;
    String S1 = S2 +S3 + S4;

这时候 JVM 会规规矩矩的按照原来的方式去做。


##测试

###String
    public class Main {
             
        public static void main(String[] args) {
            String string = "";
            for(int i=0;i<10000;i++){
                string += "hello";
            }
        }
    }

反汇编结果：javap -c


事实上会自动被JVM优化成

   StringBuilder str = new StringBuilder(string);
　　str.append("hello");
　　str.toString();

验证

    public class Main {
        private static int time = 50000;
        public static void main(String[] args) {
            testString();
            testOptimalString();
        }
         
         
        public static void testString () {
            String s="";
            long begin = System.currentTimeMillis();
            for(int i=0; i<time; i++){
                s += "java";
            }
            long over = System.currentTimeMillis();
            System.out.println("操作"+s.getClass().getName()+"类型使用的时间为："+(over-begin)+"毫秒");
        }
         
        public static void testOptimalString () {
            String s="";
            long begin = System.currentTimeMillis();
            for(int i=0; i<time; i++){
                StringBuilder sb = new StringBuilder(s);
                sb.append("java");
                s=sb.toString();
            }
            long over = System.currentTimeMillis();
            System.out.println("模拟JVM优化操作的时间为："+(over-begin)+"毫秒");
        }
         
    }



###StringBuilder

    public class Main {
             
        public static void main(String[] args) {
            StringBuilder stringBuilder = new StringBuilder();
            for(int i=0;i<10000;i++){
                stringBuilder.append("hello");
            }
        }
    }

反汇编结果：





那么有人会问既然有了StringBuilder类，为什么还需要StringBuffer类？查看源代码便一目了然，事实上，StringBuilder和StringBuffer类拥有的成员属性以及成员方法基本相同，区别是StringBuffer类的成员方法前面多了一个关键字：synchronized，不用多说，这个关键字是在多线程访问时起到安全保护作用的,也就是说StringBuffer是线程安全的。



###性能比较

    public class Main {
        private static int time = 50000;
        public static void main(String[] args) {
            testString();
            testStringBuffer();
            testStringBuilder();
            test1String();
            test2String();
        }
         
         
        public static void testString () {
            String s="";
            long begin = System.currentTimeMillis(); 
            for(int i=0; i<time; i++){ 
                s += "java"; 
            } 
            long over = System.currentTimeMillis(); 
            System.out.println("操作"+s.getClass().getName()+"类型使用的时间为："+(over-begin)+"毫秒"); 
        }
         
        public static void testStringBuffer () {
            StringBuffer sb = new StringBuffer();
            long begin = System.currentTimeMillis(); 
            for(int i=0; i<time; i++){ 
                sb.append("java"); 
            } 
            long over = System.currentTimeMillis(); 
            System.out.println("操作"+sb.getClass().getName()+"类型使用的时间为："+(over-begin)+"毫秒"); 
        }
         
        public static void testStringBuilder () {
            StringBuilder sb = new StringBuilder();
            long begin = System.currentTimeMillis(); 
            for(int i=0; i<time; i++){ 
                sb.append("java"); 
            } 
            long over = System.currentTimeMillis(); 
            System.out.println("操作"+sb.getClass().getName()+"类型使用的时间为："+(over-begin)+"毫秒"); 
        }
         
        public static void test1String () {
            long begin = System.currentTimeMillis(); 
            for(int i=0; i<time; i++){ 
                String s = "I"+"love"+"java"; 
            } 
            long over = System.currentTimeMillis(); 
            System.out.println("字符串直接相加操作："+(over-begin)+"毫秒"); 
        }
         
        public static void test2String () {
            String s1 ="I";
            String s2 = "love";
            String s3 = "java";
            long begin = System.currentTimeMillis(); 
            for(int i=0; i<time; i++){ 
                String s = s1+s2+s3; 
            } 
            long over = System.currentTimeMillis(); 
            System.out.println("字符串间接相加操作："+(over-begin)+"毫秒"); 
        }
         
    }

###存储资源比较

    String str = null;

    //------------Using Concatenation operator-------------
    long time1 = System.currentTimeMillis();
    long freeMemory1 = Runtime.getRuntime().freeMemory();
    for(int i=0; i<100000; i++){
    str = "Hi";
    str = str+" Bye";
    }
    long time2 = System.currentTimeMillis();
    long freeMemory2 = Runtime.getRuntime().freeMemory();

    long timetaken1 = time2-time1;
    long memoryTaken1 = freeMemory1 - freeMemory2;
    System.out.println("Concat operator  :" + "Time taken =" + timetaken1 + 
                       " Memory Consumed =" + memoryTaken1);

    //------------Using Concat method-------------
    long time3 = System.currentTimeMillis();
    long freeMemory3 = Runtime.getRuntime().freeMemory();
    for(int j=0; j<100000; j++){
    str = "Hi";
    str = str.concat(" Bye");

    }
    long time4 = System.currentTimeMillis();
    long freeMemory4 = Runtime.getRuntime().freeMemory();
    long timetaken2 = time4-time3;
    long memoryTaken2 = freeMemory3 - freeMemory4;
    System.out.println("Concat method  :" + "Time taken =" + timetaken2 + 
                       " Memory Consumed =" + memoryTaken2);



##结论

###对于直接相加简单字符串，String 效率最高

String str = "hello"+ "world"的效率就比 StringBuilder st  = new StringBuilder().append("hello").append("world")要高。

因为在编译器便确定了它的值，也就是说形如"I"+"love"+"java"; 的字符串相加，在编译期间便被优化成了 "Ilovejava"。
这个可以用javap -c命令反编译生成的class文件进行验证。

对于间接相加（即包含字符串引用），形如s1+s2+s3; 效率要比直接相加低，因为在编译器不会对引用变量进行优化。

###在大部分情况下 StringBuffer > String

Java.lang.StringBuffer 是线程安全的可变字符序列。一个类似于 String 的字符串缓冲区，但不能修改。虽然在任意时间点上它都包含
某种特定的字符序列，但通过某些方法调用可以改变该序列的长度和内容。在程序中可将字符串缓冲区安全地用于多线程。而且在必要时可以对
这些方法进行同步，因此任意特定实例上的所有操作就好像是以串行顺序发生的，该顺序与所涉及的每个线程进行的方法调用顺序一致。

StringBuffer 上的主要操作是 append 和 insert 方法，可重载这些方法，以接受任意类型的数据。每个方法都能有效地将给定的数据转
换成字符串，然后将该字符串的字符追加或插入到字符串缓冲区中。append 方法始终将这些字符添加到缓冲区的末端；而 insert 方法则在
指定的点添加字符。

例如，如果 z 引用一个当前内容是 “start” 的字符串缓冲区对象，则此方法调用 z.append("le") 会使字符串缓冲区包含 “startle” 
(累加);而 z.insert(4, "le") 将更改字符串缓冲区，使之包含“starlet”。

###在大部分情况下 StringBuilder > StringBuffer

java.lang.StringBuilder 一个可变的字符序列是 JAVA 5.0 新增的。此类提供一个与 StringBuffer 兼容的 API，但不保证同步，
所以使用场景是单线程。该类被设计用作 StringBuffer 的一个简易替换，用在字符串缓冲区被单个线程使用的时候（这种情况很普遍）。如
果可能，建议优先采用该类，因为在大多数实现中，它比 StringBuffer 要快。两者的使用方法基本相同。


##参考

http://www.cnblogs.com/dolphin0520/p/3778589.html