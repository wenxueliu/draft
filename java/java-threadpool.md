


##Executors

位于[这里](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Executors.html)
这里对其主要接口做一说明

其实它主要用来创建线程池，代理了线程池的创建，使得你的创建入口参数变得简单，通过方法名便知道了
你要创建的线程池是什么样一个线程池，功能大概是什么样的，其实线程池内部都是统一的方法来实现，通
过构造方法重载，使得实现不同的功能，但是往往这种方式很多时候不知道具体入口参数的改变有什么意思，
除非读了源码才知道，此时 builder 模式的方式来完成，builder 什么样的东西它告诉你就可以。

常见的方法有(都是静态方法)：

###Executors.newFixedThreadPool(int) 

创建一个指定大小的线程池，如果超过大小，放入 blocken 队列中，默认是 LinkedBlockingQueue，默认的 ThreadFactory 为：Executors.defaultThreadFactory()，是一个 Executors 的一个内部类。

内部实现是：

    public static ExecutorService newFixedThreadPool(int nThreads) {
        return new ThreadPoolExecutor(nThreads, nThreads,
                                      0L, TimeUnit.MILLISECONDS,
                                      new LinkedBlockingQueue<Runnable>());
    }

###Executors.newFixedThreadPool(int,ThreadFactory) 

创建一个指定大小的线程池，如果超过大小，放入 blocken 队列中,默认是 LinkedBlockingQueue，
自己指定 ThreadFactory，自己写的 ThreadFactory，必须 implements ThreadFactory，实现
方法： newThread(Runnable)。

内部实现是：

    public static ExecutorService newFixedThreadPool(int nThreads, ThreadFactory threadFactory) {
        return new ThreadPoolExecutor(nThreads, nThreads,
                                      0L, TimeUnit.MILLISECONDS,
                                      new LinkedBlockingQueue<Runnable>(),
                                      threadFactory);
    }

###Executors.newSingleThreadExecutor() 

创建线程池长度为 1 的，也就是只有一个长度的线程池，多余的必须等待，它和调用 Executors.newFixedThreadPool(1) 
得到的结果一样：

内部实现是：

    public static ExecutorService newSingleThreadExecutor() {
        return new FinalizableDelegatedExecutorService
            (new ThreadPoolExecutor(1, 1,
                                    0L, TimeUnit.MILLISECONDS,
                                    new LinkedBlockingQueue<Runnable>()));
    }

是不是蛮简单的，就是在变参数，你自己也可以new的。 

###Executors.newCachedThreadPool()

创建可以进行缓存的线程池，默认缓存 60s，数据会放在一个 SynchronousQueue 上，而不会进入 blocken 队列中，
也就是只要有线程进来就直接进入调度，这个不推荐使用，因为容易出问题，除非用来模拟一些并发的测试：

###Executors.newSingleThreadScheduledExecutor()

添加一个Schedule的调度器的线程池，默认只有一个调度：

内部实现为(这里可以看到不是用 ThreadPoolExector 了，schedule 换了一个类，内部实现通过 ScheduledThreadPoolExecutor 类里面的内部类 ScheduledFutureTask 来实现的，这个内部类是 private，默认是引用不到的哦)：

    public static ScheduledExecutorService newSingleThreadScheduledExecutor() {
        return new DelegatedScheduledExecutorService
            (new ScheduledThreadPoolExecutor(1));
    }

###Executors.newScheduledThreadPool();

添加一个schedule的线程池调度器，和newFixedThreadPool有点类似：

内部代码为：

    public static ScheduledExecutorService newScheduledThreadPool(int corePoolSize) {
        return new ScheduledThreadPoolExecutor(corePoolSize);
    }

其实内部 Exectors 里面还有一些其他的方法，我们就不多说明了，另外通过这里，大家先可以了解一个大概，
知道 Exectors 其实是一个工具类，提供一系列的静态方法，来完成对对应线程池的形象化创建，所以不用觉得很神奇，
神奇的是内部是如何实现的，本文我们不阐述文章中各种线程池的实现，只是大概上有个认识，等到我们专门将 Exector
系列的时候，我们会详细描述这些细节。 


##Semaphor

```java

    import java.util.Random;
    import java.util.concurrent.Semaphore;


      public class SemaphoreTest {
          private final static Semaphore MAX_SEMA_PHORE = new Semaphore(10);
          public static void main(String []args) {
               for(int i = 0 ; i < 100 ; i++) {
                    final int num = i;
                    final Random radom = new Random();
                    new Thread() {
                         public void run() {
                             boolean acquired = false;
                             try {
                                  MAX_SEMA_PHORE.acquire();
                                  acquired = true;
                                  System.out.println("我是线程：" + num + " 我获得了使用权！" + DateTimeUtil.getDateTime());
                                  long time = 1000 * Math.max(1, Math.abs(radom.nextInt() % 10));
                                  Thread.sleep(time);
                                  System.out.println("我是线程：" + num + " 我执行完了！" + DateTimeUtil.getDateTime());
                             }catch(Exception e) {
                                  e.printStackTrace();
                             }finally {
                                  if(acquired) {
                                     MAX_SEMA_PHORE.release();
                                  }
                             }
                          }
                    }.start();
               }
          }
      }
```


###Exchanger

线程之间交互数据，且在并发时候使用，两两交换，交换中不会因为线程多而混乱，发送出去没接收到会一直等，由交互器完成交互过程。

```
    import java.util.concurrent.Exchanger;

    public class ExchangerTest {
    	
    	public static void main(String []args) {
    		final Exchanger <Integer>exchanger = new Exchanger<Integer>();
    		for(int i = 0 ; i < 10 ; i++) {
    			final Integer num = i;
    			new Thread() {
    				public void run() {
    					System.out.println("我是线程：Thread_" + this.getName() + "我的数据是：" + num);
    					try {
    						Integer exchangeNum = exchanger.exchange(num);
    						Thread.sleep(1000);
    						System.out.println("我是线程：Thread_" + this.getName() + "我原先的数据为：" + num + " , 交换后的数据为：" + exchangeNum);
    					} catch (InterruptedException e) {
    						e.printStackTrace();
    					}
    				}
    			}.start();
    		}
    	}
    }
```

##CyclicBarrier

当你在很多环节需要卡住，要多个线程同时在这里都达到后，再向下走，很有用途。举个例子: 团队出去旅行，
大家一起先达到酒店住宿，然后一起达到游乐的地方游玩，然后一起坐车回家，每次需要点名后确认相关人员均
达到，然后LZ一声令下，触发，大伙就疯子般的出发了

```java

import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CyclicBarrier;

public class BarrierTest {
	
	private static final int THREAD_COUNT = 10;
	
	private final static CyclicBarrier CYCLIC_BARRIER = new CyclicBarrier(THREAD_COUNT  ,
		new Runnable() {
			public void run() {
				System.out.println("======>我是导游，本次点名结束，准备走下一个环节!");
			}
		}
	);
	
	public static void main(String []args) 
			throws InterruptedException, BrokenBarrierException {
		for(int i = 0 ; i < 10 ; i++) {
			new Thread(String.valueOf(i)) {
				public void run() {
					try {
						System.out.println("我是线程：" + this.getName() + " 我们达到旅游地点！");
						CYCLIC_BARRIER.await();
						System.out.println("我是线程：" + this.getName() + " 我开始骑车！");
						CYCLIC_BARRIER.await();
						System.out.println("我是线程：" + this.getName() + " 我们开始爬山！");
						CYCLIC_BARRIER.await();
						System.out.println("我是线程：" + this.getName() + " 我们回宾馆休息！");
						CYCLIC_BARRIER.await();
						System.out.println("我是线程：" + this.getName() + " 我们开始乘车回家！");
						CYCLIC_BARRIER.await();
						System.out.println("我是线程：" + this.getName() + " 我们到家了！");
					} catch (InterruptedException e) {
						e.printStackTrace();
					} catch (BrokenBarrierException e) {
						e.printStackTrace();
					}
				}
			}.start();
		}
	}
}
```

测试结果中可以发现，大家一起走到某个步骤后，导游说：“我是导游，本次点名结束，准备走下一个环节!”，然后才会进入下一个步骤，OK，这个有点意思吧，其实赛马也是这个道理，只是赛马通常只有一个步骤，所以我们还有一个方式是： 

CountDownLatch 的方式来完成赛马操作，CountDownLatch 是用计数器来做的，所以它不可以被复用，如果要多次使用，就要从新 new一个出来才可以。我们下面的代码中，用两组赛马，每组5个参与者来，做一个简单测试：

```java

import java.util.concurrent.CountDownLatch;

public class CountDownLatchTest {
	
	private final static int GROUP_SIZE = 5;
	
	public static void main(String []args) {
		processOneGroup("分组1");
		processOneGroup("分组2");
	}
	
	private static void processOneGroup(final String groupName) {
		final CountDownLatch start_count_down = new CountDownLatch(1);
		final CountDownLatch end_count_down = new CountDownLatch(GROUP_SIZE);
		System.out.println("==========================>\n分组：" + groupName + "比赛开始：");
		for(int i = 0 ; i < GROUP_SIZE ; i++) {
			new Thread(String.valueOf(i)) {
				public void run() {
					System.out.println("我是线程组：【" + groupName + "】,第：" + this.getName() + " 号线程,我已经准备就绪！");
					try {
						start_count_down.await();//等待开始指令发出即：start_count_down.countDown();
					} catch (InterruptedException e) {
						e.printStackTrace();
					}
					System.out.println("我是线程组：【" + groupName + "】,第：" + this.getName() + " 号线程,我已执行完成！");
					end_count_down.countDown();
				}
			}.start();
		}
		try {
			Thread.sleep(1000);
		} catch (InterruptedException e) {
			e.printStackTrace();
		}
		System.out.println("各就各位，预备！");
		start_count_down.countDown();//开始赛跑
		try {
			end_count_down.await();//等待多个赛跑者逐个结束
		} catch (InterruptedException e) {
			e.printStackTrace();
		}
		System.out.println("分组：" + groupName + "比赛结束！");
	}
}
```

有点意思哈，如果你自己用多线程实现是不是有点麻烦，不过你可以用 Thread 的 join 方法来实现，也就是线程的发生
join 的时候，当前线程（一般是主线程）要等到对应线程执行完 run 方法后才会进入下一步，为了模拟下，我们也来玩玩： 

```
public class ThreadJoinTest {
	
	private final static int GROUP_SIZE = 5;

	public static void main(String []args) throws InterruptedException {
		Thread []threadGroup1 = new Thread[5];
		Thread []threadGroup2 = new Thread[5];
		for(int i = 0 ; i < GROUP_SIZE ; i++) {
			final int num = i;
			threadGroup1[i] = new Thread() {
				public void run() {
					int j = 0;
					while(j++ < 10) {
						System.out.println("我是1号组线程：" + num + " 这个是我第：" + j + " 次运行！");
					}
				}
			};
			threadGroup2[i] = new Thread() {
				public void run() {
					int j = 0;
					while(j++ < 10) {
						System.out.println("我是2号组线程：" + num + " 这个是我第：" + j + " 次运行！");
					}
				}
			};
			threadGroup1[i].start();
		}
		for(int i = 0 ; i < GROUP_SIZE ; i++) {
			threadGroup1[i].join();
		}
		System.out.println("-==================>线程组1执行完了，该轮到俺了！");
		for(int i = 0 ; i < GROUP_SIZE ; i++) {
			threadGroup2[i].start();
		}
		for(int i = 0 ; i < GROUP_SIZE ; i++) {
			threadGroup2[i].join();
		}
		System.out.println("全部结束啦！哈哈，回家喝稀饭！");
	}
}
```

代码是不是繁杂了不少，呵呵，我们再看看上面的信号量，如果不用工具，自己写会咋写，我们模拟 CAS 锁，
使用 Atomic 配合完成咋来做呢。也来玩玩，呵呵：

```
import java.util.concurrent.atomic.AtomicInteger;

public class ThreadWaitNotify {
	
	private final static int THREAD_COUNT = 100;
	
	private final static int QUERY_MAX_LENGTH = 2;
	
	private final static AtomicInteger NOW_CALL_COUNT = new AtomicInteger(0);

	public static void main(String []args) throws InterruptedException {
		Thread []threads = new Thread[THREAD_COUNT];
		for(int i = 0 ; i < THREAD_COUNT ; i++) {
			threads[i] = new Thread(String.valueOf(i)) {
				synchronized public void run() {
					int nowValue = NOW_CALL_COUNT.get();
					while(true) {
						if(nowValue < QUERY_MAX_LENGTH && NOW_CALL_COUNT.compareAndSet(nowValue, nowValue + 1)) {
							break;//获取到了
						}
						try {
							this.wait(1000);
						} catch (InterruptedException e) {
							e.printStackTrace();
						}
						nowValue = NOW_CALL_COUNT.get();//获取一个数据，用于对比
					}
					System.out.println(this.getName() + "======我开始做操作了！");
					try {
						Thread.sleep(1000);
					} catch (InterruptedException e) {
						e.printStackTrace();
					}
					System.out.println(this.getName() + "======操作结束了！");
					NOW_CALL_COUNT.getAndDecrement();
					this.notify();
				}
			};
		}
		for(int i = 0 ; i < THREAD_COUNT ; i++) {
			threads[i].start();
		}
	}
}
```


还是有点意思哈，这样写就是大部分人对 while 循环那部分会写晕掉，主要是要不断去判定和尝试，wait() 默认是长期等待，但是我们不想让他长期等待，就等 1s 然后再尝试，其实例子还可以改成 wait 一个随机的时间范围，这样模拟的效果会更加好一些；另外实际的代码中，如果获取到锁后，notify 方法应当放在 finally 中，才能保证他肯定会执行 notify 这个方法。 
