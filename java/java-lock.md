[](http://ifeve.com/java_lock_see3/)
[](http://ifeve.com/java_lock_see2/)
http://ifeve.com/java_lock_see4/

JAVA中, 能够进入\退出, 阻塞状态或包含阻塞锁的方法有, synchronized
关键字(其中的重量锁)，ReentrantLock, Object.wait()\notify(),LockSupport.park()/unpart()(j.u.c经常使用)

```java
package lock;

import java.util.concurrent.atomic.AtomicReferenceFieldUpdater;
import java.util.concurrent.locks.LockSupport;

public class CLHLock1 {
    public static class CLHNode {
            private volatile Thread isLocked;
        }

    @SuppressWarnings("unused")
    private volatile CLHNode     tail;
    private static final ThreadLocal<CLHNode>     LOCAL = new ThreadLocal<CLHNode>();
    private static final AtomicReferenceFieldUpdater<CLHLock1, CLHNode> UPDATER
        = AtomicReferenceFieldUpdater.newUpdater(CLHLock1.class, CLHNode.class, "tail");

    public void lock() {
        CLHNode node = new CLHNode();
        LOCAL.set(node);
        CLHNode preNode = UPDATER.getAndSet(this, node);
        if (preNode != null) {
                    preNode.isLocked = Thread.currentThread();
                    LockSupport.park(this);
                    preNode = null;
                    LOCAL.set(node);
                }
    }

    public void unlock() {
        CLHNode node = LOCAL.get();
        if (!UPDATER.compareAndSet(this, node, null)) {
                    System.out.println("unlock\t" +
                            node.isLocked.getName());
                    LockSupport.unpark(node.isLocked);
                }
        node = null;
    }
}

```

阻塞锁的优势在于，阻塞的线程不会占用cpu时间， 不会导致
CPu占用率过高，但进入时间以及恢复时间都要比自旋锁略慢。

在竞争激烈的情况下 阻塞锁的性能要明显高于 自旋锁。

理想的情况则是; 在线程竞争不激烈的情况下，使用自旋锁，竞争激烈的情况下使用，阻塞锁。 


###自旋锁

TicketLock ，CLHlock 和MCSlock

Ticket锁主要解决的是访问顺序的问题，主要的问题是在多核cpu上

```java
package com.alipay.titan.dcc.dal.entity;

import java.util.concurrent.atomic.AtomicInteger;

public class TicketLock {
    private AtomicInteger                     serviceNum = new AtomicInteger();
    private AtomicInteger                     ticketNum  = new AtomicInteger();
    private static final ThreadLocal<Integer> LOCAL      = new ThreadLocal<Integer>();

    public void lock() {
        int myticket = ticketNum.getAndIncrement();
        LOCAL.set(myticket);
        while (myticket != serviceNum.get()) {
        }
    }

    public void unlock() {
        int myticket = LOCAL.get();
        serviceNum.compareAndSet(myticket, myticket + 1);
    }
}
```

每次都要查询一个 serviceNum 服务号, 影响性能(必须要到主内存读取, 并阻止其他cpu修改).



import java.util.concurrent.atomic.AtomicReferenceFieldUpdater;

public class CLHLock {
    public static class CLHNode {
        private volatile boolean isLocked = true;
    }

    @SuppressWarnings("unused")
    private volatile CLHNode                                           tail;
    private static final ThreadLocal<CLHNode>                          LOCAL   = new ThreadLocal<CLHNode>();
    private static final AtomicReferenceFieldUpdater<CLHLock, CLHNode> UPDATER
        = AtomicReferenceFieldUpdater.newUpdater(CLHLock.class, CLHNode.class, "tail");

    public void lock() {
        CLHNode node = new CLHNode();
        LOCAL.set(node);
        CLHNode preNode = UPDATER.getAndSet(this, node);
        if (preNode != null) {
            while (preNode.isLocked) {
            }
            preNode = null;
            LOCAL.set(node);
        }
    }

    public void unlock() {
        CLHNode node = LOCAL.get();
        if (!UPDATER.compareAndSet(this, node, null)) {
            node.isLocked = false;
        }
        node = null;
    }
}


