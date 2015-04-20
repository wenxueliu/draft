Date: 上次更新 15-04-01

##ThreadLocal的定义

它是一个线程级别变量，在并发模式下是绝对安全的变量，也是线程封闭的一种标准用法（除了局部变量外），
即使你将它定义为 static，它也是线程安全的。

ThreadLocal 中有一个ThreadLocalMap类，每个Thread对象都会有自己的ThreadLocalMap对象，
Thread本身不能调用ThreadLocalMap对象的get set remove方法。只能通过ThreadLocal 这个对象去
调用。那么ThreadLocal 是怎么调用的呢？通过获取当前线程，然后进而得到当前线程的ThreadLocalMap
对象，然后调用Map的get set remove 方法。既然是Map，那么map的key是什么呢？map的key是 ThreadLocal 
这个对象。 ok 。实现了数据只能是线程的局部变量要求。

##使用场景

So what is a thread-local variable? A thread-local variable is one whose value at any one time is
linked to which thread it is being accessed from. In other words, it has a separate value per thread.
Each thread maintains its own, separate map of thread-local variable values. (Many operating systems
actually have native support for thread-local variables, but in Sun's implementation at least, native
support is not used, and thread-local variables are instead held in a specialised type of hash table
attached to the Thread.)

Thread-local variables are used via the ThreadLocal class in Java. We declare an instance of ThreadLocal, 
which has a get() and set() method. A call to these methods will read and set the calling thread's own value.

##实例

So when in practice would we use ThreadLocal? A typical example of using ThreadLocal would be as an alternative 
to an object or resource pool, when we don't mind creating one object per thread. Let's consider the example of 
a pool of Calendar instances. In an application that does a lot of date manipulation, Calendar classes may be a 
good candidates for pooling because: 

* Creating a Calendar is non-trivial (various calculations and accesses to localisation resources need to be made 
each time one is created); 
* There's no actual requirement to share Calendars between threads or have fewer calendars than threads. 

One (inefficient) way to re-use Calendars would be to create a 'calendar pool' class such as this:

```java
    package org.test.Calendar
    import java.util.Calendar
    import java.util.GregorianCalendar

    public class CalendarFactory {
      private List calendars = new ArrayList();
      private static CalendarFactory instance = new CalendarFactory();

      public static CalendarFactory getFactory() { return instance; }

      public Calendar getCalendar() {
        synchronized (calendars) {
          if (calendars.isEmpty()) {
            return new GregorianCalendar();
          } else {
            return calendars.remove(calendars.size()-1);
          }
        }
      }
      public void returnCalendar(Calendar cal) {
        synchronized (calendars) {
          calendars.add(cal);
        }
      }
      // Don't let outsiders create new factories directly
      private CalendarFactory() {}
    }
```

Then a client could call: 

```java

    Calendar cal = CalendarFactory.getFactory().getCalendar();
    try {
      // perform some calculation using cal
    } finally {
      CalendarFactory.getFactory().returnCalendar(cal);
    }
```


This would allow us to re-use Calendar objects but it's a bit inefficient because 
in each case it makes two synchronized calls when we're actually not that bothered
 about sharing the calendars across the threads. We wouldn't care, for example, if
 Thread 1 created and finished with a calendar and then Thread 2 created another, 
even though Thread 1 had finished with its. The number of threads will typically be 
small-ish (maybe in the hundreds at the very most), and so having as many calendars
 knocking around as there are threads is an OK compromise. (This would not be the 
case, for example, with database connections: if possible, we generally would want 
Thread 2 to use the connection that Thread 1 had just finished with rather than 
creating another; in such cases, thread-local variables aren't the right solution.) 
Now let's see how we can improve CalendarFactory using ThreadLocal:

当后续的线程不依赖与前面线程完成操作，这时候可以通过　ThreadLocal　来增强并发性能。对于数据库并
发写操作，只有当前面的线程已经写完，后面的线程才可以写的情况，并不适合用　ThreadLocal。

    package org.test.Calendar
    import java.util.Calendar
    import java.util.GregorianCalendar

    public class CalendarFactory {
      private ThreadLocal<Calendar> calendarRef = new ThreadLocal<Calendar>() {
        protected Calendar initialValue() {
          return new GregorianCalendar();
        }
      };
      private static CalendarFactory instance = new CalendarFactory();

      public static CalendarFactory getFactory() { return instance; }

      public Calendar getCalendar() {
        return calendarRef.get();
      }

      // Don't let outsiders create new factories directly
      private CalendarFactory() {}
    }


Note that there is still a single, static instance of CalendarFactory shared by 
all threads. But that single instance uses the ThreadLocal variable calendarRef, 
which has a per-thread value. Inside getCalendar(), the call to calendarRef.get()
will always operate on our thread-private "instance" of the variable, and we don't
need any synchronization.

This example uses the Java 5 generics feature: we declare ThreadLocal as 'containing'
 Calendar objects, so that the subsequent get() method doesn't need an explicit cast. 
(That is, the cast is inserted automatically by the compiler.) Another feature of this
 example is the initialValue() method. We actually subclass ThreadLocal and override 
initialValue() to provide an appropriate object each time a new one is required (i.e. 
when get() is called for the first time on a particular thread). We could of course 
have simply checked for null inside the getCalendar() method (the first time get() is 
called on a ThreadLocal for a particular thread, it returns null) and set the value if
it was null: 

    public Calendar getCalendar() {
      Calendar cal = calendarRef.get();
        if (cal == null) {
          calendarRef.set(cal = new GregorianCalendar());
        }
        return cal;
      }

However, overriding ThreadLocal.initialValue() automatically handles this logic and makes
 our code a bit neater– especially if we're calling get() in multiple places.

Note that we don't have a "return to pool" method. Once created, we let the calendar hang
around for as long as the thread is alive. If we really wanted to remove these instances
at a particular moment, then as of Java 5, we can call calendarRef.remove(), which removes
the calling thread's value; it would be set to the initial value again on the next call to calendarRef.get(). 

**Notes**

All values set on a ThreadLocal also become garbage collectable if the ThreadLocal becomes
 no longer reachable outside of the Thread class. In other words, a thread's map of ThreadLocal
 to value holds on to the ThreadLocal only via a weak reference. 

###When to use ThreadLocal?

So what are other good candidates for object re-use via ThreadLocal? Basically, objects where: 

* The objects are non-trivial to construct; 
* An instance of the object is frequently needed by a given thread; 
* The application pools threads, such as in a typical server (if every time the thread-local is used it is from a new thread, then a new object will still be created on each call!); 
* It doesn't matter that Thread A will never share an instance with Thread B; 
* It's not convenient to subclass Thread. If you can subclass Thread, you could add extra instance variables to your subclass instead of using ThreadLocal. But for example, if you are writing a servlet running in an off-the-shelf servlet runner such as Tomcat, you generally have no control over the class of created threads. Of course, even if you can subclass Thread, you may simply prefer the cleaner syntax of ThreadLocal. 

That means that typical objects to use with ThreadLocal could be:

* Random number generators (provided a per-thread sequence was acceptable); 
* Collators; 
* native ByteBuffers (which in some environments cannot be destroyed once they're created); 
* XML parsers or other cases where creating an instance involves going through slightly non-trival code to 'choose a registered service provider'; 
* Per-thread information such as profiling data which will be periodically collated. 


Note that it is generally better not to re-use objects that are trivial to construct and finalize.
 (By "trivial to finalize", we mean objects that don't override finalize.) This is because recent 
garbage collector implementations are optimised for "temporary" objects that are constructed, 
trivially used and then fall out of scope without needing to be added to the finalizer queue. 
Pooling something trivial like a StringBuffer, Integer or small byte array can actually degrade
 performance on modern JVMs. 


##应用场景之多参数传递

在系统中任意一个适合的位置定义个 ThreadLocal 变量，可以定义为 public static 类型（直接new出来一个 ThreadLocal 
对象），要向里面放入数据就使用 set(Object)，要获取数据就用 get() 操作，删除元素就用 remove()，其余的方法是非 
public 的方法，不推荐使用。

```java
public class ThreadLocalTest2 {
	
	public final static ThreadLocal <String>TEST_THREAD_NAME_LOCAL = new ThreadLocal<String>();

	public final static ThreadLocal <String>TEST_THREAD_VALUE_LOCAL = new ThreadLocal<String>();
	
	public static void main(String[]args) {
		for(int i = 0 ; i < 100 ; i++) {
			final String name = "线程-【" + i + "】";
			final String value =  String.valueOf(i);
			new Thread() {
				public void run() {
					try {
						TEST_THREAD_NAME_LOCAL.set(name);
						TEST_THREAD_VALUE_LOCAL.set(value);
						callA();
					}finally {
						TEST_THREAD_NAME_LOCAL.remove();
						TEST_THREAD_VALUE_LOCAL.remove();
					}
				}
			}.start();
		}
	}
	
	public static void callA() {
		callB();
	}
	
	public static void callB() {
		new ThreadLocalTest2().callC();
	}
	
	public void callC() {
		callD();
	}
	
	public void callD() {
		System.out.println(TEST_THREAD_NAME_LOCAL.get() + "\t=\t" + TEST_THREAD_VALUE_LOCAL.get());
	}
}
```

这里模拟了 100 个线程去访问分别设置 name 和 value，中间故意将 name 和 value 的值设置成一样，
看是否会存在并发的问题，通过输出可以看出，线程输出并不是按照顺序输出，说明是并行执行的，而线程 
name 和 value 是可以对应起来的，中间通过多个方法的调用，以模实际的调用中参数不传递，如何获取到
对应的变量的过程，不过实际的系统中往往会跨类，这里仅仅在一个类中模拟，其实跨类也是一样的结果，大家
可以自己去模拟就可以。

##应用场景之数据库连接

```java
class ConnectionManager {

    private static Connection connect = null;

    public static Connection openConnection() {
            if(connect == null){
                        connect = DriverManager.getConnection();
                    }
            return connect;
        }
    public static void closeConnection() {
            if(connect!=null)
                connect.close();
        }
}
```
假设有这样一个数据库链接管理类，这段代码在单线程中使用是没有任何问题的，但是如果在多线程中使用呢？
很显然，在多线程中使用会存在线程安全问题：

第一，这里面的2个方法都没有进行同步，很可能在 openConnection 方法中会多次创建 connect；

第二，由于 connect 是共享变量，那么必然在调用 connect 的地方需要使用到同步来保障线程安全，因为很可能
一个线程在使用 connect 进行数据库操作，而另外一个线程调用 closeConnection 关闭链接。

所以出于线程安全的考虑，必须将这段代码的两个方法进行同步处理，并且在调用connect的地方需要进行同步处理。

这样将会大大影响程序执行效率，因为一个线程在使用 connect 进行数据库操作的时候，其他线程只有等待。

那么大家来仔细分析一下这个问题，这地方到底需不需要将 connect 变量进行共享？事实上，是不需要的。假如每个线程
中都有一个 connect 变量，各个线程之间对 connect 变量的访问实际上是没有依赖关系的，即一个线程不需要关心其他线
程是否对这个 connect 进行了修改的。

到这里，可能会有朋友想到，既然不需要在线程之间共享这个变量，可以直接这样处理，在每个需要使用数据库连接的方法
中具体使用时才创建数据库链接，然后在方法调用完毕再释放这个连接。比如下面这样：

```java
class ConnectionManager {

    private  Connection connect = null;

    public Connection openConnection() {
            if(connect == null){
                        connect = DriverManager.getConnection();
                    }
            return connect;
        }

    public void closeConnection() {
            if(connect!=null)
                connect.close();
        }
}

class Dao{
    public void insert() {
            ConnectionManager connectionManager = new ConnectionManager();
            Connection connection = connectionManager.openConnection();

            //使用connection进行操作
            connectionManager.closeConnection();
        }
}
```
这样处理确实也没有任何问题，由于每次都是在方法内部创建的连接，那么线程之间自然不存在线程安全问题。
但是这样会有一个致命的影响：导致服务器压力非常大，并且严重影响程序执行性能。由于在方法中需要频繁地
开启和关闭数据库连接，这样不尽严重影响程序执行效率，还可能导致服务器压力巨大。

那么这种情况下使用 ThreadLocal 是再适合不过的了，因为 ThreadLocal 在每个线程中对该变量会创建一个副本，
即每个线程内部都会有一个该变量，且在线程内部任何地方都可以使用，线程之间互不影响，这样一来就不存在线
程安全问题，也不会严重影响程序执行性能。

但是要注意，虽然 ThreadLocal 能够解决上面说的问题，但是由于在每个线程中都创建了副本，所以要考虑它对资
源的消耗，比如内存的占用会比不使用 ThreadLocal 要大。

##应用场景之 session 管理

``` java
private static final ThreadLocal threadSession = new ThreadLocal();

public static Session getSession() throws InfrastructureException {
    Session s = (Session) threadSession.get();
    try {
            if (s == null) {
                        s = getSessionFactory().openSession();
                        threadSession.set(s);
                    }
        } catch (HibernateException ex) {
                throw new InfrastructureException(ex);
            }
    return s;
}
```

##ThreadLocal 原理

###set(T obj)

```java
public void set(T value) {
        Thread t = Thread.currentThread();
        ThreadLocalMap map = getMap(t);
        if (map != null)
            map.set(this, value);
        else
            createMap(t, value);
    }
```

首先获取了当前的线程，和猜测一样，然后有个 getMap 方法，传入了当前线程，我们先可以理解这个 map 是和线程相关的
map，接下来如果不为空，就做 set 操作，你跟踪进去会发现，这个和 HashMap 的 put 操作类似，也就是向 map 中写入
了一条数据，如果为空，则调用 createMap 方法，进去后，看看：

```java
void createMap(Thread t, T firstValue) {
        t.threadLocals = new ThreadLocalMap(this, firstValue);
    }
```

返回创建了一个ThreadLocalMap，并且将传入的参数和当前ThreadLocal作为K-V结构写入进去

```java
ThreadLocalMap(ThreadLocal firstKey, Object firstValue) {
    table = new Entry[INITIAL_CAPACITY];
    int i = firstKey.threadLocalHashCode & (INITIAL_CAPACITY - 1);
    table[i] = new Entry(firstKey, firstValue);
    size = 1;
    setThreshold(INITIAL_CAPACITY);
}
```

这里就不说明 ThreadLocalMap 的结构细节，只需要知道它的实现和 HashMap 类似，只是很多方法没有，
也没有 implements Map，因为它并不想让你通过某些方式（例如反射）获取到一个 Map 对他进一步操作，
它是一个 ThreadLocal 里面的一个 static 内部类，default 类型，仅仅在 java.lang 下面的类可以
引用到它，所以你可以想到 Thread 可以引用到它。

我们再回过头来看看 getMap 方法，因为上面我仅仅知道获取的 Map 是和线程相关的，有一个
t.threadLocalMap = new ThreadLocalMap(this, firstValue)的时候，相信你应该大概有点明白，
这个变量应该来自 Thread 里面，我们根据 getMap 方法进去看看：

```java

    ThreadLocalMap getMap(Thread t) {
            return t.threadLocals;
        }
```

是的，是来自于Thread，而这个Thread正好又是当前线程，那么进去看看定义就是：

```java

    ThreadLocal.ThreadLocalMap threadLocals = null;
```

这个属性就是在 Thread 类中，也就是每个 Thread 默认都有一个 ThreadLocalMap，用于存放线程级别的局部变量，
通常你无法为他赋值，因为这样的赋值通常是不安全的。

通过上面的分析, get() 和 remove 就简单多了

###get()

```java
    public T get() {
            Thread t = Thread.currentThread();
            ThreadLocalMap map = getMap(t);
            if (map != null) {
                ThreadLocalMap.Entry e = map.getEntry(this);
                if (e != null)
                    return (T)e.value;
            }
            return setInitialValue();
        }
```

通过根据当前线程调用 getMap 方法，也就是调用了 t.threadLocalMap，然后在 map 中查找，注意 Map 中找到的是
Entry，也就是 K-V 基本结构，因为你 set 写入的仅仅有值，所以，它会设置一个 e.value 来返回你写入的值，因为
Key 就是 ThreadLocal 本身。你可以看到 map.getEntry 也是通过 this 来获取的。

```java
    private T setInitialValue() {
        value = initialValue();
        Thread t = Thread.currentThread();
        ThreadLocalMap map = getMap(t);
        if (map != null)
            return map.set(this, value);
        else
            createMap(t, value)
        return value;
    }
```

因为在上面的代码分析过程中，我们发现如果没有先 set 的话，即在 map 中查找不到对应的存储，则会通过调用 setInitialValue
方法返回 i，而在 setInitialValue 方法中，有一个语句是 T value = initialValue()， 而默认情况下，initialValue 方法返回
的是 null, 因此, 在进行get之前，必须先set，否则会报空指针异常。


###remove()

```java
    public void remove() {
             ThreadLocalMap m = getMap(Thread.currentThread());
             if (m != null)
                 m.remove(this);
         }
```

同样根据当前线程获取 map，如果不为空，则 remove，通过this来remove。

##总结

Thread 里面有个属性是一个类似于 HashMap 一样的东西，只是它的名字叫 ThreadLocalMap，这个属性是 default
类型的，因此同一个 package 下面所有的类都可以引用到，因为是 Thread 的局部变量，所以每个线程都有一个自己单
独的 Map，相互之间是不冲突的，所以即使将 ThreadLocal 定义为 static 线程之间也不会冲突。

ThreadLocal 和 Thread 是在同一个 package 下面，可以引用到这个类，可以对他做操作，此时 ThreadLocal 每
定义一个，用 this 作为Key，你传入的值作为 value，而 this 就是你定义的 ThreadLocal，所以不同的 ThreadLocal
变量，都使用set，相互之间的数据不会冲突，因为他们的 Key 是不同的，当然同一个 ThreadLocal 做两次set操作后，
会以最后一次为准。

综上所述，在线程之间并行，ThreadLocal可以像局部变量一样使用，且线程安全，且不同的ThreadLocal变量之间的数据毫无冲突。

###要点


1. 每个 thread 下可以定义多个 ThreadLocal 变量.
2. 每个 thread 下有一个变量 threadLocals, 它的类型是 ThreadLocalMap(ThreadLocal key, T value) 用于维护所有的ThreadLocal 变量, threadLocals 的 key 是定义的 ThreadLocal 变量, 值是 ThreadLocal 变量调用 set() 的设置的值
3. 仔细体会代码中 this 和 t 的区别

###注意点:

不能放置全局变量，只能放置线程私有的对象
ThreadLocal 主要还是线程封闭的一种用法，而且跨类和方法传递参数很好用（不是主要目的），且线程安全。
ThreadLocal 首先要 set 才可以 get 否则会抛出 NullPointerException 异常


这个 ThreadLocal 有啥坑呢，大家从前面应该可以看出来，这个 ThreadLocal 相关的对象是被绑定到一个 Map 中的，
而这个 Map 是 Thread 线程的中的一个属性，那么就有一个问题是，如果你不自己 remove 的话或者说如果你自己的程序
中不知道什么时候去 remove 的话，那么线程不注销，这些被 set 进去的数据也不会被注销。

反过来说，写代码中除非你清晰的认识到这个对象应该在哪里 set，哪里 remove，如果是模糊的，很可能你的代码中不会走
remove 的位置去，或导致一些逻辑问题，另外，如果不 remove 的话，就要等线程注销，我们在很多应用服务器中，线程是
被复用的，因为在内核分配线程还是有开销的，因此在这些应用中线程很难会被注销掉，那么向 ThreadLocal 写入的数据自
然很不容易被注销掉，这些可能在我们使用某些开源框架的时候无意中被隐藏用到，都有可能会导致问题，最后发现 OOM 得时
候数据竟然来自 ThreadLocalMap 中，还不知道这些数据是从哪里设置进去的，所以你应当注意这个坑，可能不止一个人掉
进这个坑里去过

##参考

http://blog.csdn.net/xieyuooo/article/details/8599266
http://www.cnblogs.com/dolphin0520/p/3920407.html
