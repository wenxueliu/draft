单例模式算是设计模式中最容易理解，也是最容易手写代码的模式了吧。但是其中的坑却不少，所以也常作为面试题来考。
本文主要对几种单例写法的整理，并分析其优缺点。很多都是一些老生常谈的问题，但如果你不知道如何创建一个线程安全
的单例，不知道什么是双检锁，那这篇文章可能会帮助到你。

从速度和反应时间角度来讲，非延迟加载（又称饿汉式）好；从资源利用效率上说，延迟加载（又称懒汉式）好。

##懒汉式，线程不安全(同步延迟加载)

```java
    public class Singleton {
    	private static Singleton instance;
    	private Singleton (){}
    	public static Singleton getInstance() {
    		if (instance == null) {
    		    instance = new Singleton();
    		}
    		return instance;
    	}
    }
```

这段代码简单明了，而且使用了懒加载模式，但是却存在致命的问题。当有多个线程并行调用 getInstance() 
的时候，就会创建多个实例。也就是说在多线程下不能正常工作。

##懒汉式，线程安全

为了解决上面的问题，最简单的方法是将整个 getInstance() 方法设为同步（synchronized）。

```java
    public class Singleton {
    	private static Singleton instance;
    	private Singleton (){}
    	public static synchronized Singleton getInstance() {
    		if (instance == null) {
    		    instance = new Singleton();
    		}
    		return instance;
    	}
    }
```

虽然做到了线程安全，并且解决了多实例的问题，但是它并不高效。假设有多个同时调用 getInstance()
,在任何时候只能有一个线程调用 getInstance() 方法,除了创建实例的线程,其他线程等待只是判断 
instance != null 后直接返回, 如果在 synchronized 外加 if(instance == null), 那么,
如果实例已经创建,后续现场可以并发判断 if(instance == null), 这就是双重检验锁。

##双重检验锁

双重检验锁模式（double checked locking pattern），是一种使用同步块加锁的方法。程序员称其为
双重检查锁，因为会有两次检查 instance == null，一次是在同步块外，一次是在同步块内。为什么在同
步块内还要再检验一次？因为可能会有多个线程一起进入同步块外的 if，如果在同步块内不进行二次检验的话
就会生成多个实例了。

```
    public static Singleton getSingleton() {
    	if (instance == null) {               
    		synchronized (Singleton.class) {         //1
    			if (instance == null) {           //2
    				instance = new Singleton();//3
    			}
    		}
    	}
    	return instance ;
    }
```

这段代码看起来很完美，很可惜，它是有问题。主要在于 instance = new Singleton()这句，这并非是一个
原子操作，事实上在 JVM 中这句话大概做了下面 3 件事情。


* 给 instance 分配内存
* 调用 Singleton 的构造函数来初始化成员变量
* 将 instance 对象指向分配的内存空间（执行完这步 instance 就为非 null 了）


但是在 JVM 的即时编译器中存在指令重排序的优化。也就是说上面的第二步和第三步的顺序是不能保证的，最终的
执行顺序可能是 1-2-3 也可能是 1-3-2。如果是后者，则在 3 执行完毕、2 未执行之前，被线程二抢占了，这时
 instance 已经是非 null 了（但却没有初始化），所以线程二会直接返回 instance，然后使用，然后顺理成章地报错。

如果你还是有疑问,那么, 假设代码执行以下事件序列：

* 线程 1 进入 getInstance() 方法。
* 由于 instance 为 null，线程 1 在 //1 处进入 synchronized 块。 
* 线程 1 前进到 //3 处，但在构造函数执行之前，使实例成为非 null。 
* 线程 1 被线程 2 预占。
* 线程 2 检查实例是否为 null。因为实例不为 null，线程 2 将 instance 引用返回给一个构造完整但部分初始化了的 Singleton 对象。 
* 线程 2 被线程 1 预占。
* 线程 1 通过运行 Singleton 对象的构造函数并将引用返回给它，来完成对该对象的初始化。

为展示此事件的发生情况，假设代码行 instance =new Singleton(); 执行了下列伪代码：

    mem = allocate();             //为单例对象分配内存空间.
    instance = mem;               //注意，instance 引用现在是非空，但还未初始化
    ctorSingleton(instance);    //为单例对象通过instance调用构造函数

这段伪代码不仅是可能的，而且是一些 JIT 编译器上真实发生的。执行的顺序是颠倒的，但鉴于当前的内存模型，
这也是允许发生的。JIT 编译器的这一行为使双重检查锁定的问题只不过是一次学术实践而已。


我们只需要将 instance 变量声明成 volatile 就可以了。

```
    public class Singleton {
    	private volatile static Singleton instance; //声明成 volatile
    	private Singleton (){}
    	public static Singleton getSingleton() {
    		if (instance == null) {
    			synchronized (Singleton.class) {
    				if (instance == null) {
    				    instance = new Singleton();
    				}
    			} 
    		}
    		return instance;
    	}
    }
```

有些人认为使用 volatile 的原因是可见性，也就是可以保证线程在本地不会存有 instance 的副本，
每次都是去主内存中读取。但其实是不对的。使用 volatile 的主要原因是其另一个特性：禁止指令重排
序优化。也就是说，在 volatile 变量的赋值操作后面会有一个内存屏障（生成的汇编代码上），读操作
不会被重排序到内存屏障之前。比如上面的例子，取操作必须在执行完 1-2-3 之后或者 1-3-2 之后，不
存在执行到 1-3 然后取到值的情况。从「先行发生原则」的角度理解的话，就是对于一个 volatile 变
量的写操作都先行发生于后面对这个变量的读操作（这里的“后面”是时间上的先后顺序）。

但是特别注意在 Java 5 以前的版本使用了 volatile 的双检锁还是有问题的。其原因是 Java 5 以前的
 JMM （Java 内存模型）是存在缺陷的，即时将变量声明成 volatile 也不能完全避免重排序，主要是 
volatile 变量前后的代码仍然存在重排序问题。这个 volatile 屏蔽重排序的问题在 Java 5 中才得以
修复，所以在这之后才可以放心使用 volatile。

相信你不会喜欢这种复杂又隐含问题的方式，当然我们有更好的实现线程安全的单例模式的办法。

##饿汉式 static final field

这种方法非常简单，因为单例的实例被声明成 static 和 final 变量了，在第一次加载类到内存中时就会初始化，
所以创建实例本身是线程安全的。

```java

    public class Singleton{
        //类加载时就初始化
        private static final Singleton instance = new Singleton();
        private Singleton(){}
        public static Singleton getInstance(){
            return instance;
        }
    }
```

这种写法如果完美的话，就没必要在啰嗦那么多双检锁的问题了。缺点是它不是一种懒加载模式（lazy initialization），
单例会在加载类后一开始就被初始化，即使客户端没有调用 getInstance()方法。饿汉式的创建方式在一些场景中将无法使用：
譬如 Singleton 实例的创建是依赖参数或者配置文件的，在 getInstance() 之前必须调用某个方法设置参数给它，那样这
种单例写法就无法使用了。 

##静态内部类 static nested class

我比较倾向于使用静态内部类的方法，这种方法也是《Effective Java》上所推荐的。也叫 Initialization on Demand 
Holder (IODH) 方法

```java

    public class Singleton {
        private static class SingletonHolder {
            private static final Singleton INSTANCE = new Singleton();
        }
        private Singleton (){}
        public static final Singleton getInstance() {
            return SingletonHolder.INSTANCE;
        }
    }
```

依靠JVM对内部静态类&静态成员初始化的顺序机制来实现的。 这种实现方法虽然有一定的局限性，比如，只能用于静态成员，
ClassLoader要确定等等，但是这种实现方法已经足够好了。 

##枚举 Enum

用枚举写单例实在太简单了！这也是它最大的优点。下面这段代码就是声明枚举实例的通常做法。

```java
    public enum EasySingleton{
        INSTANCE;
    }
```

我们可以通过EasySingleton.INSTANCE来访问实例，这比调用getInstance()方法简单多了。创建枚举默认就是线
程安全的，所以不需要担心double checked locking，而且还能防止反序列化导致重新创建新的对象。但是还是很少
看到有人这样写，可能是因为不太熟悉吧。


## ThreadLocal修复双重检测

借助于ThreadLocal，将临界资源（需要同步的资源）线程局部化，具体到本例就是将双重检测的第一层检测条件 
if (instance == null) 转换为了线程局部范围内来作。这里的ThreadLocal也只是用作标示而已，用来标示每个
线程是否已访问过，如果访问过，则不再需要走同步块，这样就提高了一定的效率。但是ThreadLocal在1.4以前的版本
都较慢，但这与 volatile 相比却是安全的。

```
    public class Singleton {  
         private static final ThreadLocal perThreadInstance = new ThreadLocal();  
         private static Singleton singleton ;  
         private Singleton() {}  
       
         public static Singleton  getInstance() {  
              if (perThreadInstance.get() == null){  
               // 每个线程第一次都会调用  
                   createInstance();  
              }  
              return singleton;  
         }  
      
         private static  final void createInstance() {  
              synchronized (Singleton.class) {  
                   if (singleton == null){  
                        singleton = new Singleton();  
                   }  
             }  
             perThreadInstance.set(perThreadInstance);  
         }  
    }  
```

多线程要点:

线程切换: CPU 时间片到达, 线程直接切换
原子性: 语句的原子性
有序性: 语句的有序性
可见性: 变量的可见性
同步原理: 将多线程强制对该同步块的访问变成单线程



##单例测试

下面是测试单例的框架，采用了类加载器与反射。
注，为了测试单便是否为真真的单例，我自己写了一个类加载器，且其父加载器设置为根加载器，这样确保Singleton由MyClassLoader加载，如果不设置为根加载器为父加载器，则默认为系统加载器，则Singleton会由系统加载器去加载，但这样我们无法卸载类加载器，如果加载Singleton的类加载器卸载不掉的话，那么第二次就不能重新加载Singleton的Class了，这样Class不能得加载则最终导致Singleton类中的静态变量重新初始化，这样就无法测试了。
下面测试类延迟加载的结果是可行的，同样也可用于其他单例的测试：


```
    public class Singleton {  
         private Singleton() {}  
      
         public static class Holder {  
              // 这里的私有没有什么意义  
              /* private */
              static Singleton instance = new Singleton();  
         }  
      
         public static Singleton getInstance() {  
              // 外围类能直接访问内部类（不管是否是静态的）的私有变量  
              return Holder.instance;  
         }  
    }  
      
    class CreateThread extends Thread {  
         Object singleton;  
         ClassLoader cl;  
      
         public CreateThread(ClassLoader cl) {  
              this.cl = cl;  
         }  
      
         public void run() {  
              Class c;  
              try {  
                   c = cl.loadClass("Singleton");  
                   // 当两个不同命名空间内的类相互不可见时，可采用反射机制来访问对方实例的属性和方法  
                   Method m = c.getMethod("getInstance", new Class[] {});  
                   // 调用静态方法时，传递的第一个参数为class对象  
                   singleton = m.invoke(c, new Object[] {});  
                   c = null;  
                   cl = null;  
              } catch (Exception e) {  
                   e.printStackTrace();  
              }  
         }  
    }  
      
    class MyClassLoader extends ClassLoader {  
         private String loadPath;  
         MyClassLoader(ClassLoader cl) {  
              super(cl);  
         }  
         public void setPath(String path) {  
              this.loadPath = path;  
         }  
         protected Class findClass(String className) throws ClassNotFoundException {  
              FileInputStream fis = null;  
              byte[] data = null;  
              ByteArrayOutputStream baos = null;  
      
              try {  
                   fis = new FileInputStream(new File(loadPath  
                         + className.replaceAll("\\.", "\\\\") + ".class"));  
                   baos = new ByteArrayOutputStream();  
                   int tmpByte = 0;  
                   while ((tmpByte = fis.read()) != -1) {  
                        baos.write(tmpByte);  
                   }  
                   data = baos.toByteArray();  
              } catch (IOException e) {  
                   throw new ClassNotFoundException("class is not found:" + className, e);  
              } finally {  
                   try {  
                    if (fis != null) {  
                         fis.close();  
                    }  
                    if (fis != null) {  
                         baos.close();  
                    }  
      
                   } catch (Exception e) {  
                        e.printStackTrace();  
                   }  
              }  
              return defineClass(className, data, 0, data.length);  
         }  
    }  
      
    class SingleTest {  
         public static void main(String[] args) throws Exception {  
              while (true) {  
                   // 不能让系统加载器直接或间接的成为父加载器  
                   MyClassLoader loader = new MyClassLoader(null);  
                   loader.setPath("/");  
                   CreateThread ct1 = new CreateThread(loader);  
                   CreateThread ct2 = new CreateThread(loader);  
                   ct1.start();  
                   ct2.start();  
                   ct1.join();  
                   ct2.join();  
                   if (ct1.singleton != ct2.singleton) {  
                        System.out.println(ct1.singleton + " " + ct2.singleton);  
                   }  
                   // System.out.println(ct1.singleton + " " + ct2.singleton);  
                   ct1.singleton = null;  
                   ct2.singleton = null;  
                   Thread.yield();  
              }  
         }  
    }  
```


http://www.iteye.com/topic/652440