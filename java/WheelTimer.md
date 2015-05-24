
[AtomicIntegerFieldUpdater](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/atomic/AtomicIntegerFieldUpdater.html)


wheel       : 双向队列(HashedWheelBucket) 的数组
bucket      : 一个双向队列(HashedWheelBucket)
timeout     : 每个元素(HashedWheelTimeout))
timeouts    : 保持所有的 timeout
tick        : wheel 包含很多 tick

###调用过程

* createWheel()
* newTimeout()


##HashedWheelTimer

####关键变量####

long tickDuration;
HashedWheelBucket[] wheel : 数组, 每个元素为 HashedWheelBucket
workerStateUpdater = AtomicIntegerFieldUpdater.newUpdater(HashedWheelTimer.class, "workerState");
WORKER_STATE_UPDATER = workerStateUpdater
Worker worker = new Worker()
Thread workerThread = threadFactory.newThread(worker)
volatile long startTime

int workerState = WORKER_STATE_INIT; // 0 - init, 1 - started, 2 - shut down
int WORKER_STATE_INIT = 0;
int WORKER_STATE_STARTED = 1;
int WORKER_STATE_SHUTDOWN = 2;

int mask  : wheel.length - 1, wheel 掩码
long tickDuration: 单位纳秒

CountDownLatch startTimeInitialized : 栅栏, 默认 1
Queue<HashedWheelTimeout> timeouts : HashedWheelTimeout 队列
Queue<Runnable> cancelledTimeouts  :

####关键方法####

* HashedWheelTimer(ThreadFactory threadFactory, long tickDuration, TimeUnit unit)
* int normalizeTicksPerWheel(int ticksPerWheel)
* HashedWheelBucket[] createWheel(int ticksPerWheel) 创建 wheel 对象
* start() 返回 boolen 貌似更合适
* stop() 返回没有处理的timeout
* Timeout newTimeout(TimerTask task, long delay, TimeUnit unit) : 构造 timeout 对象加入 timeouts





###HashedWheelBucket

维护了一个双向队列, 用于对每个 wheel 中元素的增删



####关键变量####

* HashedWheelTimeout head
* HashedWheelTimeout tail


####关键方法####

* void addTimeout(HashedWheelTimeout timeout) : 增加 timeout 元素到当前队列
* void expireTimeouts(long deadline) : 遍历所有元素, 从当前队列删除过期的和取消的元素, 或者递减元素的计数器
* void remove(HashedWheelTimeout timeout) : 删除 timeout 元素到当前队列
* void clearTimeouts(Set<Timeout> set) : 增加所有没有过期和取消的元素到 set 中
* HashedWheelTimeout pollTimeout() : 删除队列头元素


###HashedWheelTimeout

继承 MpscLinkedQueueNode<Timeout> 实现 Timeout 接口, 维护了一个 wheel 中一个元素的状态

####关键变量####

HashedWheelBucket bucket : 当前元素所属的 bucket

updater = AtomicIntegerFieldUpdater.newUpdater(HashedWheelTimeout.class, "state")
AtomicIntegerFieldUpdater<HashedWheelTimeout> STATE_UPDATER = updater
volatile int state ; ST_INIT(0), ST_CANCELLED(1), ST_EXPIRED(2)

HashedWheelTimer timer
TimerTask task
long deadline

long remainingRounds : 注意与 deadline 的关系! 剩余的循环次数
    (deadline/ tickDuration - tick)/wheel.Duration

####关键方法####

HashedWheelTimeout(HashedWheelTimer timer, TimerTask task, long deadline)

timer       :
task        :
deadline    :

* Timer timer()
* TimerTask task()
* int state()
* HashedWheelTimeout value()
* boolean isCancelled()
* boolean isExpired()
* boolean cancel() : 设置当前元素状态为 ST_INIT, 将当前元素加入 timer.cancelledTimeouts中, 增加一个线程,专门做把当前对象从所属 bucket 中删除的工作
* void expire()    : 设置当前元素状态为 ST_EXPIRED, 调用 task.run(this)


###Worker

实现 Runnable 接口的线程对象


####关键变量####

Set<Timeout> unprocessedTimeouts = new HashSet<Timeout>()
long tick


####关键方法####
* long waitForNextTick() : 计算下一个 ticket 的时间, 并计算当前时间到下一个 tick 需要休眠 sleepTimeMs 毫秒
* void processCancelledTasks() : 从 cancelledTimeouts 中取出一个任务, 调用其 run() , 与 HashedWheelTimeout.cancle() 对应
* void transferTimeoutsToBuckets() : 将 timeouts 中的每个元素加入合适它所属的 bucket
* Set<Timeout> unprocessedTimeouts() : 返回 unprocessedTimeouts
* void run() : 遍历 

核心算法: 将 timeout 放入 bucket

    long calculated = timeout.deadline / tickDuration;
    timeout.remainingRounds = (calculated - tick) / wheel.length;
    ticks = Math.max(calculated, tick)
    HashedWheelBucket bucket = wheel[stopIndex];
    bucket.addTimeout(timeout);
