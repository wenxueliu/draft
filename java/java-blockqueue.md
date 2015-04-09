在新增的Concurrent包中，BlockingQueue很好的解决了多线程中，如何高效安全“传输”数据的问题。
通过这些高效并且线程安全的队列类，为我们快速搭建高质量的多线程程序带来极大的便利。本文详细介
绍了BlockingQueue家庭中的所有成员，包括他们各自的功能以及常见使用场景。

###认识BlockingQueue

阻塞队列，顾名思义，首先它是一个队列，通过一个共享的队列，可以使得数据由队列的一端输入，从另外一端输出；

常用的队列主要有以下两种：（当然通过不同的实现方式，还可以延伸出很多不同类型的队列，DelayQueue就是其中的一种）

* 先进先出（FIFO）：先插入的队列的元素也最先出队列，类似于排队的功能。从某种程度上来说这种队列也体现了一种公平性。
* 后进先出（LIFO）：后插入队列的元素最先出队列，这种队列优先处理最近发生的事件。

多线程环境中，通过队列可以很容易实现数据共享，比如经典的“生产者”和“消费者”模型中，通过队列可以很便利地实现两者
之间的数据共享。假设我们有若干生产者线程，另外又有若干个消费者线程。如果生产者线程需要把准备好的数据共享给消费者
线程，利用队列的方式来传递数据，就可以很方便地解决他们之间的数据共享问题。但如果生产者和消费者在某个时间段内，万
一发生数据处理速度不匹配的情况呢？理想情况下，如果生产者产出数据的速度大于消费者消费的速度，并且当生产出来的数据
累积到一定程度的时候，那么生产者必须暂停等待一下（阻塞生产者线程），以便等待消费者线程把累积的数据处理完毕，反之
亦然。然而，在concurrent包发布以前，在多线程环境下，我们每个程序员都必须去自己控制这些细节，尤其还要兼顾效率和
线程安全，而这会给我们的程序带来不小的复杂度。好在此时，强大的concurrent包横空出世了，而他也给我们带来了强大的
BlockingQueue。（在多线程领域：所谓阻塞，在某些情况下会挂起线程（即阻塞），一旦条件满足，被挂起的线程又会自动被唤醒）

##BlockingQueue的两个常见阻塞场景

* 当队列中没有数据的情况下，消费者端的所有线程都会被自动阻塞（挂起），直到有数据放入队列。
* 当队列中填满数据的情况下，生产者端的所有线程都会被自动阻塞（挂起），直到队列中有空的位置，线程被自动唤醒。

这也是我们在多线程环境下，为什么需要BlockingQueue的原因。作为BlockingQueue的使用者，我们再也不需要关心什么
时候需要阻塞线程，什么时候需要唤醒线程，因为这一切BlockingQueue都给你一手包办了。既然BlockingQueue如此神通
广大，[参考官方文档查看常见用法](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/BlockingQueue.html)

##BlockingQueue成员详细介绍

###ArrayBlockingQueue

基于数组的阻塞队列实现，在ArrayBlockingQueue内部，维护了一个定长数组，以便缓存队列中的数据对象，这是一个常用
的阻塞队列，除了一个定长数组外，ArrayBlockingQueue内部还保存着两个整形变量，分别标识着队列的头部和尾部在数组
中的位置。

ArrayBlockingQueue在生产者放入数据和消费者获取数据，都是共用同一个锁对象，由此也意味着两者无法真正并行运行，
这点尤其不同于LinkedBlockingQueue；按照实现原理来分析，ArrayBlockingQueue完全可以采用分离锁，从而实现生产
者和消费者操作的完全并行运行。Doug Lea之所以没这样去做，也许是因为ArrayBlockingQueue的数据写入和获取操作已经
足够轻巧，以至于引入独立的锁机制，除了给代码带来额外的复杂性外，其在性能上完全占不到任何便宜。 ArrayBlockingQueue
和LinkedBlockingQueue间还有一个明显的不同之处在于，前者在插入或删除元素时不会产生或销毁任何额外的对象实例，而
后者则会生成一个额外的Node对象。这在长时间内需要高效并发地处理大批量数据的系统中，其对于GC的影响还是存在一定的区
别。而在创建ArrayBlockingQueue时，我们还可以控制对象的内部锁是否采用公平锁，默认采用非公平锁。


###LinkedBlockingQueue

基于链表的阻塞队列，同ArrayListBlockingQueue类似，其内部也维持着一个数据缓冲队列（该队列由一个链表构成），
当生产者往队列中放入一个数据时，队列会从生产者手中获取数据，并缓存在队列内部，而生产者立即返回；只有当队列缓冲区
达到最大值缓存容量时（LinkedBlockingQueue可以通过构造函数指定该值），才会阻塞生产者队列，直到消费者从队列中
消费掉一份数据，生产者线程会被唤醒，反之对于消费者这端的处理也基于同样的原理。而LinkedBlockingQueue之所以能
够高效的处理并发数据，还因为其对于生产者端和消费者端分别采用了独立的锁来控制数据同步，这也意味着在高并发的情况下
生产者和消费者可以并行地操作队列中的数据，以此来提高整个队列的并发性能。

作为开发者，我们需要注意的是，如果构造一个LinkedBlockingQueue对象，而没有指定其容量大小，LinkedBlockingQueue
会默认一个类似无限大小的容量（Integer.MAX_VALUE），这样的话，如果生产者的速度一旦大于消费者的速度，也许还没有等
到队列满阻塞产生，系统内存就有可能已被消耗殆尽了。

ArrayBlockingQueue和LinkedBlockingQueue是两个最普通也是最常用的阻塞队列，一般情况下，在处理多线程间的生产者
消费者问题，使用这两个类足以。

下面的代码演示了如何使用BlockingQueue：

```java

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.LinkedBlockingQueue;
 
/**
 * @author jackyuj
 */
public class BlockingQueueTest {
 
    public static void main(String[] args) throws InterruptedException {
        // 声明一个容量为10的缓存队列
        BlockingQueue<String> queue = new LinkedBlockingQueue<String>(10);
 
        Producer producer1 = new Producer(queue);
        Producer producer2 = new Producer(queue);
        Producer producer3 = new Producer(queue);
        Consumer consumer = new Consumer(queue);
 
        // 借助Executors
        ExecutorService service = Executors.newCachedThreadPool();
        // 启动线程
        service.execute(producer1);
        service.execute(producer2);
        service.execute(producer3);
        service.execute(consumer);
 
        // 执行10s
        Thread.sleep(10 * 1000);
        producer1.stop();
        producer2.stop();
        producer3.stop();
 
        Thread.sleep(2000);
        // 退出Executor
        service.shutdown();
    }
}

import java.util.Random;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.TimeUnit;
 
/**
 * 消费者线程
 *
 * @author jackyuj
 */
public class Consumer implements Runnable {
 
    public Consumer(BlockingQueue<String> queue) {
        this.queue = queue;
    }
 
    public void run() {
        System.out.println("启动消费者线程！");
        Random r = new Random();
        boolean isRunning = true;
        try {
            while (isRunning) {
                System.out.println("正从队列获取数据...");
                String data = queue.poll(2, TimeUnit.SECONDS);
                if (null != data) {
                    System.out.println("拿到数据：" + data);
                    System.out.println("正在消费数据：" + data);
                    Thread.sleep(r.nextInt(DEFAULT_RANGE_FOR_SLEEP));
                } else {
                    // 超过2s还没数据，认为所有生产线程都已经退出，自动退出消费线程。
                    isRunning = false;
                }
            }
        } catch (InterruptedException e) {
            e.printStackTrace();
            Thread.currentThread().interrupt();
        } finally {
            System.out.println("退出消费者线程！");
        }
    }
 
    private BlockingQueue<String> queue;
    private static final int      DEFAULT_RANGE_FOR_SLEEP = 1000;
}
 
import java.util.Random;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
 
/**
 * 生产者线程
 *
 * @author jackyuj
 */
public class Producer implements Runnable {
 
    public Producer(BlockingQueue queue) {
        this.queue = queue;
    }
 
    public void run() {
        String data = null;
        Random r = new Random();
 
        System.out.println("启动生产者线程！");
        try {
            while (isRunning) {
                System.out.println("正在生产数据...");
                Thread.sleep(r.nextInt(DEFAULT_RANGE_FOR_SLEEP));
 
                data = "data:" + count.incrementAndGet();
                System.out.println("将数据：" + data + "放入队列...");
                if (!queue.offer(data, 2, TimeUnit.SECONDS)) {
                    System.out.println("放入数据失败：" + data);
                }
            }
        } catch (InterruptedException e) {
            e.printStackTrace();
            Thread.currentThread().interrupt();
        } finally {
            System.out.println("退出生产者线程！");
        }
    }
 
    public void stop() {
        isRunning = false;
    }
 
    private volatile boolean      isRunning               = true;
    private BlockingQueue queue;
    private static AtomicInteger  count                   = new AtomicInteger();
    private static final int      DEFAULT_RANGE_FOR_SLEEP = 1000;
}

```

###PriorityBlockingQueue

基于优先级的阻塞队列（优先级的判断通过构造函数传入的Compator对象来决定），但需要注意的是PriorityBlockingQueue
并不会阻塞数据生产者，而只会在没有可消费的数据时，阻塞数据的消费者。因此使用的时候要特别注意，生产者生产数据的速度
绝对不能快于消费者消费数据的速度，否则时间一长，会最终耗尽所有的可用堆内存空间。在实现PriorityBlockingQueue时，
内部控制线程同步的锁采用的是公平锁。


###DelayQueue
DelayQueue是一个支持延时获取元素的无界阻塞队列。队列使用PriorityQueue来实现。队列中的元素必须实现Delayed接口，
在创建元素时可以指定多久才能从队列中获取当前元素。只有在延迟期满时才能从队列中提取元素。此外, DelayQueue是一个没
有大小限制的队列，因此往队列中插入数据的操作（生产者）永远不会被阻塞，而只有获取数据的操作（消费者）才会被阻塞。

使用场景：

* 缓存系统的设计：可以用DelayQueue保存缓存元素的有效期，使用一个线程循环查询DelayQueue，一旦能从DelayQueue中获取元素时，表示缓存有效期到了。
* 定时任务调度。使用DelayQueue保存当天将会执行的任务和执行时间，一旦从DelayQueue中获取到任务就开始执行，从比如TimerQueue就是使用DelayQueue实现的。

队列中的Delayed必须实现compareTo来指定元素的顺序。比如让延时时间最长的放在队列的末尾。实现代码如下：

```java
    public int compareTo(Delayed other) {
               if (other == this) // compare zero ONLY if same object
                    return 0;
                if (other instanceof ScheduledFutureTask) {
                    ScheduledFutureTask x = (ScheduledFutureTask)other;
                    long diff = time - x.time;
                    if (diff < 0)
                        return -1;
                    else if (diff > 0)
                        return 1;
    	   else if (sequenceNumber < x.sequenceNumber)
                        return -1;
                    else
                        return 1;
                }
                long d = (getDelay(TimeUnit.NANOSECONDS) -
                          other.getDelay(TimeUnit.NANOSECONDS));
                return (d == 0) ? 0 : ((d < 0) ? -1 : 1);
            }
```

####如何实现Delayed接口

我们可以参考ScheduledThreadPoolExecutor里ScheduledFutureTask类。这个类实现了Delayed接口。
首先：在对象创建的时候，使用time记录前对象什么时候可以使用，代码如下：

```java

    ScheduledFutureTask(Runnable r, V result, long ns, long period) {
                super(r, result);
                this.time = ns;
                this.period = period;
                this.sequenceNumber = sequencer.getAndIncrement();
    }
```

然后使用getDelay可以查询当前元素还需要延时多久，代码如下：

```java
    public long getDelay(TimeUnit unit) {
                return unit.convert(time - now(), TimeUnit.NANOSECONDS);
            }
```

通过构造函数可以看出延迟时间参数ns的单位是纳秒，自己设计的时候最好使用纳秒，因为getDelay时可以指定
任意单位，一旦以纳秒作为单位，而延时的时间又精确不到纳秒就麻烦了。使用时请注意当time小于当前时间时，
getDelay会返回负数。

####如何实现延时队列

延时队列的实现很简单，当消费者从队列里获取元素时，如果元素没有达到延时时间，就阻塞当前线程。

```java

long delay = first.getDelay(TimeUnit.NANOSECONDS);
                    if (delay <= 0)
                        return q.poll();
                    else if (leader != null)
                        available.await();
```



###SynchronousQueue

一种无缓冲的等待队列，类似于无中介的直接交易，有点像原始社会中的生产者和消费者，生产者拿着产品去集市销售给产品的最
终消费者，而消费者必须亲自去集市找到所要商品的直接生产者，如果一方没有找到合适的目标，那么对不起，大家都在集市等待。
相对于有缓冲的BlockingQueue来说，少了一个中间经销商的环节（缓冲区），如果有经销商，生产者直接把产品批发给经销商，
而无需在意经销商最终会将这些产品卖给那些消费者，由于经销商可以库存一部分商品，因此相对于直接交易模式，总体来说采用中
间经销商的模式会吞吐量高一些（可以批量买卖）；但另一方面，又因为经销商的引入，使得产品从生产者到消费者中间增加了额外
的交易环节，单个产品的及时响应性能可能会降低。
　　
声明一个SynchronousQueue有两种不同的方式，它们之间有着不太一样的行为。公平模式和非公平模式的区别:

如果采用公平模式：SynchronousQueue会采用公平锁，并配合一个FIFO队列来阻塞多余的生产者和消费者，从而体系整体的公平策略；

但如果是非公平模式（SynchronousQueue默认）：SynchronousQueue采用非公平锁，同时配合一个LIFO队列来管理多余的生
产者和消费者，而后一种模式，如果生产者和消费者的处理速度有差距，则很容易出现饥渴的情况，即可能有某些生产者或者是消费
者的数据永远都得不到处理。


###LinkedTransferQueue

LinkedTransferQueue是一个由链表结构组成的无界阻塞TransferQueue队列。相对于其他阻塞队列，LinkedTransferQueue
多了tryTransfer和transfer方法。

transfer方法。如果当前有消费者正在等待接收元素（消费者使用take()方法或带时间限制的poll()方法时），transfer方法
可以把生产者传入的元素立刻transfer（传输）给消费者。如果没有消费者在等待接收元素，transfer方法会将元素存放在队列
的tail节点，并等到该元素被消费者消费了才返回。transfer方法的关键代码如下：


    Node pred = tryAppend(s, haveData);
    return awaitMatch(s, pred, e, (how == TIMED), nanos);

第一行代码是试图把存放当前元素的s节点作为tail节点。第二行代码是让CPU自旋等待消费者消费元素。因为自旋会消耗CPU，所以
自旋一定的次数后使用 Thread.yield() 方法来暂停当前正在执行的线程，并执行其他线程。

tryTransfer方法。则是用来试探下生产者传入的元素是否能直接传给消费者。如果没有消费者等待接收元素，则返回false。
和transfer方法的区别是 tryTransfer 方法无论消费者是否接收，方法立即返回。而transfer方法是必须等到消费者消费了才返回。

对于带有时间限制的tryTransfer(E e, long timeout, TimeUnit unit)方法，则是试图把生产者传入的元素直接传给消费者，
但是如果没有消费者消费该元素则等待指定的时间再返回，如果超时还没消费元素，则返回false，如果在超时时间内消费了元素，
则返回true。


##阻塞队列的实现原理

如果队列是空的，消费者会一直等待，当生产者添加元素时候，消费者是如何知道当前队列有元素的呢？如果让你来设计阻塞队列
你会如何设计，让生产者和消费者能够高效率的进行通讯呢？让我们先来看看JDK是如何实现的。

使用通知模式实现。所谓通知模式，就是当生产者往满的队列里添加元素时会阻塞住生产者，当消费者消费了一个队列中的元素后，
会通知生产者当前队列可用。通过查看JDK源码发现ArrayBlockingQueue使用了Condition来实现，代码如下：

```
    private final Condition notFull;
    private final Condition notEmpty;

    public ArrayBlockingQueue(int capacity, boolean fair) {
            //省略其他代码
            notEmpty = lock.newCondition();
            notFull =  lock.newCondition();
        }

    public void put(E e) throws InterruptedException {
            checkNotNull(e);
            final ReentrantLock lock = this.lock;
            lock.lockInterruptibly();
            try {
                while (count == items.length)
                    notFull.await();
                insert(e);
            } finally {
                lock.unlock();
            }
    }

    public E take() throws InterruptedException {
            final ReentrantLock lock = this.lock;
            lock.lockInterruptibly();
            try {
                while (count == 0)
                    notEmpty.await();
                return extract();
      } finally {
                lock.unlock();
            }
    }

    private void insert(E x) {
            items[putIndex] = x;
            putIndex = inc(putIndex);
            ++count;
            notEmpty.signal();
        }
```

当我们往队列里插入一个元素时，如果队列不可用，阻塞生产者主要通过LockSupport.park(this);来实现

```
public final void await() throws InterruptedException {
            if (Thread.interrupted())
                throw new InterruptedException();
            Node node = addConditionWaiter();
            int savedState = fullyRelease(node);
            int interruptMode = 0;
            while (!isOnSyncQueue(node)) {
                LockSupport.park(this);
                if ((interruptMode = checkInterruptWhileWaiting(node)) != 0)
                    break;
            }
            if (acquireQueued(node, savedState) && interruptMode != THROW_IE)
                interruptMode = REINTERRUPT;
            if (node.nextWaiter != null) // clean up if cancelled
                unlinkCancelledWaiters();
            if (interruptMode != 0)
                reportInterruptAfterWait(interruptMode);
        }
```
继续进入源码，发现调用setBlocker先保存下将要阻塞的线程，然后调用unsafe.park阻塞当前线程。

```
public static void park(Object blocker) {
        Thread t = Thread.currentThread();
        setBlocker(t, blocker);
        unsafe.park(false, 0L);
        setBlocker(t, null);
    }
```
unsafe.park是个native方法，代码如下：

park这个方法会阻塞当前线程，只有以下四种情况中的一种发生时，该方法才会返回。

* 与park对应的unpark执行或已经执行时。注意：已经执行是指unpark先执行，然后再执行的park。
* 线程被中断时。
* 如果参数中的time不是零，等待了指定的毫秒数时。
* 发生异常现象时。这些异常事先无法确定。

我们继续看一下JVM是如何实现park方法的，park在不同的操作系统使用不同的方式实现，在linux下是使用的是系统方法
pthread_cond_wait实现。实现代码在JVM源码路径src/os/linux/vm/os_linux.cpp里的 os::PlatformEvent::park
方法，代码如下：

```cpp
    void os::PlatformEvent::park() {      
     	     int v ;
	     for (;;) {
		v = _Event ;
	     if (Atomic::cmpxchg (v-1, &_Event, v) == v) break ;
	     }
	     guarantee (v >= 0, "invariant") ;
	     if (v == 0) {
	     // Do this the hard way by blocking ...
	     int status = pthread_mutex_lock(_mutex);
	     assert_status(status == 0, status, "mutex_lock");
	     guarantee (_nParked == 0, "invariant") ;
	     ++ _nParked ;
	     while (_Event < 0) {
	     status = pthread_cond_wait(_cond, _mutex);
	     // for some reason, under 2.7 lwp_cond_wait() may return ETIME ...
	     // Treat this the same as if the wait was interrupted
	     if (status == ETIME) { status = EINTR; }
	     assert_status(status == 0 || status == EINTR, status, "cond_wait");
	     }
	     -- _nParked ;
	     
	     // In theory we could move the ST of 0 into _Event past the unlock(),
	     // but then we'd need a MEMBAR after the ST.
	     _Event = 0 ;
	     status = pthread_mutex_unlock(_mutex);
	     assert_status(status == 0, status, "mutex_unlock");
	     }
	     guarantee (_Event >= 0, "invariant") ;
	     }

     }
```

当队列满时，生产者往阻塞队列里插入一个元素，生产者线程会进入WAITING (parking)状态。我们可以使用
jstack dump阻塞的生产者线程看到这点：

```
    "main" prio=5 tid=0x00007fc83c000000 nid=0x10164e000 waiting on condition [0x000000010164d000]
       java.lang.Thread.State: WAITING (parking)
            at sun.misc.Unsafe.park(Native Method)
            - parking to wait for  <0x0000000140559fe8> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)
            at java.util.concurrent.locks.LockSupport.park(LockSupport.java:186)
            at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2043)
            at java.util.concurrent.ArrayBlockingQueue.put(ArrayBlockingQueue.java:324)
            at blockingqueue.ArrayBlockingQueueTest.main(ArrayBlockingQueueTest.java:11)
```

###小结

BlockingQueue不光实现了一个完整队列所具有的基本功能，同时在多线程环境下，他还自动管理了多线间的自动等待于唤醒功能，
从而使得程序员可以忽略这些细节，关注更高级的功能。 



##参考

http://www.cnblogs.com/jackyuj/archive/2010/11/24/1886553.html
http://www.infoq.com/cn/articles/java-blocking-queue