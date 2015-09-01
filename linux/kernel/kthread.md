Linux内核可以看作一个服务进程(管理软硬件资源，响应用户进程的种种合理以及不合理的请求)。内核需要多个执行流并行，为了防止可能的阻塞，支持多线程是必要的。内核线程就是内核的分身，一个分身可以处理一件特定事情。内核线程的调度由内核负责，一个内核线程处于阻塞状态时不影响其他的内核线程，因为其是调度的基本单位。这与用户线程是不一样的。因为内核线程只运行在内核态，因此，它只能使用大于PAGE_OFFSET（3G）的地址空间。内核线程和普通的进程间的区别在于内核线程没有独立的地址空间，mm指针被设置为NULL；它只在 内核空间运行，从来不切换到用户空间去；并且和普通进程一样，可以被调度，也可以被抢占。

内核线程（thread）或叫守护进程(daemon)，在操作系统中占据相当大的比例，当Linux操作系统启动以后，你可以用”ps -ef”命令查看系统中的进程，这时会发现很多以”d”结尾的进程名，确切说名称显示里面加 "[]"的，这些进程就是内核线程。

创建内核线程最基本的两个接口函数是：

kthread_run(threadfn, data, namefmt, ...)    

和

kernel_thread(int(* fn)(void *),void * arg,unsigned long flags)

这里我们主要介绍kthread_run，后面会专门分析这两个函数的异同。

 

kthread_run 事实上是一个宏定义：

```
/**

 * kthread_run - create and wake a thread.

 * @threadfn: the function to run until signal_pending(current).

 * @data: data ptr for @threadfn.

 * @namefmt: printf-style name for the thread.

 *

 * Description: Convenient wrapper for kthread_create() followed by

 * wake_up_process().  Returns the kthread or ERR_PTR(-ENOMEM).

 */

#define kthread_run(threadfn, data, namefmt, ...)                   \
({                                                  \

      struct task_struct *__k                                    \

           = kthread_create(threadfn, data, namefmt, ## __VA_ARGS__); \

      if (!IS_ERR(__k))                                \

           wake_up_process(__k);                              \

      __k;                                               \

})
```

 kthread_run()负责内核线程的创建，它由kthread_create()和wake_up_process()两部分组成，这样的好处是用kthread_run()创建的线程可以直接运行。外界调用kthread_run创建运行线程。kthread_run是个宏定义，首先调用kthread_create()创建线程，如果创建成功，再调用wake_up_process()唤醒新创建的线程。kthread_create()根据参数向kthread_create_list中发送一个请求，并唤醒kthreadd，之后会调用wait_for_completion(&create.done)等待线程创建完成。新创建的线程开始运行后，入口在kthread()，kthread()调用complete(&create->done)唤醒阻塞的模块进程，并使用schedule()调度出去。kthread_create()被唤醒后，设置新线程的名称，并返回到kthread_run中。kthread_run调用wake_up_process()重新唤醒新创建线程，此时新线程才开始运行kthread_run参数中的入口函数。

在介绍完如何创建线程之后，下面来介绍另外两个基本的函数：

int kthread_stop(struct task_struct *k);

 

int kthread_should_stop(void);

 

 kthread_stop()负责结束创建的线程，参数是创建时返回的task_struct指针。kthread设置标志should_stop，并等待线程主动结束，返回线程的返回值。在调用 kthread_stop()结束线程之前一定要检查该线程是否还在运行（通过 kthread_run 返回的 task_stuct 是否有效），否则会造成灾难性的后果。kthread_run的返回值tsk。不能用tsk是否为NULL进行检查，而要用IS_ERR()宏定义检查，这是因为返回的是错误码，大致从0xfffff000~0xffffffff。

 kthread_should_stop()返回should_stop标志（参见 struct kthread ）。它用于创建的线程检查结束标志，并决定是否退出。

kthread() (注：原型为：static int kthread(void *_create) )的实现在kernel/kthread.c中，头文件是include/linux/kthread.h。内核中一直运行一个线程kthreadd，它运行kthread.c中的kthreadd函数。在kthreadd()中，不断检查一个kthread_create_list链表。kthread_create_list中的每个节点都是一个创建内核线程的请求，kthreadd()发现链表不为空，就将其第一个节点退出链表，并调用create_kthread()创建相应的线程。create_kthread()则进一步调用更深层的kernel_thread()创建线程，入口函数设在kthread()中。

      外界调用kthread_stop()删除线程。kthread_stop首先设置结束标志should_stop，然后调用wake_for_completion(&kthread->exited)上，这个其实是新线程task_struct上的vfork_done，会在线程结束调用do_exit()时设置。

附：

```
struct kthread {

       int should_stop;

       struct completion exited;

};

int kthreadd(void *unused)
{

       struct task_struct *tsk = current;


       /* Setup a clean context for our children to inherit. */

       set_task_comm(tsk, "kthreadd");

       ignore_signals(tsk);

       set_cpus_allowed_ptr(tsk, cpu_all_mask);

       set_mems_allowed(node_states[N_HIGH_MEMORY]);


       current->flags |= PF_NOFREEZE | PF_FREEZER_NOSIG;

 
       for (;;) {

              set_current_state(TASK_INTERRUPTIBLE);

              if (list_empty(&kthread_create_list))

                     schedule();

              __set_current_state(TASK_RUNNING);

 
              spin_lock(&kthread_create_lock);

              while (!list_empty(&kthread_create_list)) {

                     struct kthread_create_info *create;

                     create = list_entry(kthread_create_list.next,

                                       struct kthread_create_info, list);

                     list_del_init(&create->list);

                     spin_unlock(&kthread_create_lock);

 

                     create_kthread(create);

 

                     spin_lock(&kthread_create_lock);

              }

              spin_unlock(&kthread_create_lock);

       }

       return 0;
}

/**

 * kthread_stop - stop a thread created by kthread_create().

 * @k: thread created by kthread_create().

 *

 * Sets kthread_should_stop() for @k to return true, wakes it, and

 * waits for it to exit. This can also be called after kthread_create()

 * instead of calling wake_up_process(): the thread will exit without

 * calling threadfn().

 *

 * If threadfn() may call do_exit() itself, the caller must ensure

 * task_struct can't go away.

 *

 * Returns the result of threadfn(), or %-EINTR if wake_up_process()

 * was never called.

 */

int kthread_stop(struct task_struct *k)
{

       struct kthread *kthread;

       int ret;

 
       trace_sched_kthread_stop(k);

       get_task_struct(k);

 
       kthread = to_kthread(k);

       barrier(); /* it might have exited */

       if (k->vfork_done != NULL) {

              kthread->should_stop = 1;

              wake_up_process(k);

              wait_for_completion(&kthread->exited);

       }

       ret = k->exit_code;

       put_task_struct(k);

       trace_sched_kthread_stop_ret(ret);

       return ret;

}
```


内核多线程是在项目中使用到，自己也不熟悉，遇到一个很囧的问题，导致cpu运行100%。

这是写的第一个内核线程程序，通过全局变量来实现两个内核线程之间的通信。但是这里遇到致命错误，就是：每当 wait_event_interruptible()被wake_up_interruptible 唤醒之后线程就进入死循环。后面发现是线程不会主动的自己调度，需要显式的通过schedule 或者 schedule_timeout()来调度。如果不加tc = 0 这一行，wait_event_intrruptible()就一直不会睡眠（参见前面的文章“等待队列”），不会被调度放弃CPU，因此进入死循环。这个过程可以通过分析wait_event_intrruptible()的源代码来看出。


```
#include <linux/init.h>   

#include <linux/module.h>   

#include <linux/kthread.h>   

#include <linux/wait.h>

  
MODULE_LICENSE("Dual BSD/GPL");  

  
static struct task_struct * _tsk;  

static struct task_struct * _tsk1;

static int tc = 0;

static wait_queue_head_t log_wait_queue;

  

static int thread_function(void *data)  
{  

    do {  

       　    　　　 printk(KERN_INFO "IN thread_function thread_function: %d times \n", tc);    

        
                   wait_event_interruptible(log_wait_queue,tc == 10);

                   tc = 0;  ///必须加这一行，内核才会进行调度。内核线程不像应用程序会主动调度，我们需要显式的使用调度函数，想要在thread_function_1中去重置tc的值是不可能的，因为线程不会被调度，该线程会一直占用CPU

                           
                   printk(KERN_INFO "has been woke up !\n");

    }while(!kthread_should_stop());  

    return tc;  
}  


static int thread_function_1(void *data)  
{  

    do {  

       　　　　　　 printk(KERN_INFO "IN thread_function_1 thread_function: %d times\n", ++tc);  

       

                   if(tc == 10 && waitqueue_active(&log_wait_queue))

                   {

                            wake_up_interruptible(&log_wait_queue);

                   }

                   msleep_interruptible(1000);

                  
    }while(!kthread_should_stop());  

    return tc;  

}  

  
static int hello_init(void)  

{  

    printk(KERN_INFO "Hello, world!\n");  

    init_waitqueue_head(&log_wait_queue);

    _tsk = kthread_run(thread_function, NULL, "mythread"); 

    if (IS_ERR(_tsk)) {  //需要使用IS_ERR()来判断线程是否有效，后面会有文章介绍IS_ERR()

        printk(KERN_INFO "first create kthread failed!\n");  

    }  

    else {  

        printk(KERN_INFO "first create ktrhead ok!\n");  

    }  

          _tsk1 = kthread_run(thread_function_1,NULL, "mythread2");

    if (IS_ERR(_tsk1)) {  

        printk(KERN_INFO "second create kthread failed!\n");  

    }  

    else {  

        printk(KERN_INFO "second create ktrhead ok!\n");  

    }  

    return 0;  

}  

  
static void hello_exit(void)  
{  

    printk(KERN_INFO "Hello, exit!\n");  

    if (!IS_ERR(_tsk)){  

        int ret = kthread_stop(_tsk);  

        printk(KERN_INFO "First thread function has stopped ,return %d\n", ret);  

    }  

    if(!IS_ERR(_tsk1))

         {

                   int ret = kthread_stop(_tsk1);

                   printk(KERN_INFO "Second thread function_1 has stopped ,return %d\n",ret);

         }

}  

  
module_init(hello_init);  

module_exit(hello_exit);

```

说明：这个程序的目的就是，使用一个线程（thread_function_1）通知另外一个线程（thread_function）某个条件（tc == 10）满足（比如接收线程收到10帧然后通知处理线程处理接收到的数据）

运行结果：

程序加载并运行（tc 的值等于10 之后 就会唤醒另外一个线程，之后tc又从10开始计数）：

一种线程间通信的方式：completion机制。Completion机制是线程间通信的一种轻量级机制：允许一个线程告诉另一个线程工作已经完成。为使用 completion, 需要包含头文件 <linux/completion.h>。

可以通过以下方式来创建一个 completion :

DECLARE_COMPLETION(my_completion);

或者, 动态创建和初始化:

struct completion my_completion;

init_completion(&my_completion);

等待 completion 是一个简单事来调用: void wait_for_completion(struct completion *c); 

注意：这个函数进行一个不可打断的等待. 如果你的代码调用 wait_for_completion 并且

没有人完成这个任务, 结果会是一个不可杀死的进程。

completion 事件可能通过调用下列之一来发出：

void complete(struct completion *c);

void complete_all(struct completion *c);

如果多于一个线程在等待同一个 completion 事件, 这 2 个函数做法不同. complete 只

唤醒一个等待的线程, 而 complete_all 允许它们所有都继续。

下面来看使用completion机制的实现代码：

```
#include <linux/init.h>   

#include <linux/module.h>   

#include <linux/kthread.h>   

#include <linux/wait.h>

#include <linux/completion.h>

  
MODULE_LICENSE("Dual BSD/GPL");  
  

static struct completion  comp;  

static struct task_struct * _tsk;  

static struct task_struct * _tsk1;

static int tc = 0;
 

static int thread_function(void *data)  
{  

    do {  

        　　　　　　printk(KERN_INFO "IN thread_function thread_function: %d times \n", tc);    

   
                   wait_for_completion(&comp);

                   //tc = 0;  ///在哪里都行
                   

                   printk(KERN_INFO "has been woke up !\n");

    }while(!kthread_should_stop());  

    return tc;  

}   

 

static int thread_function_1(void *data)  
{  

    do {  

       　　　　　　　printk(KERN_INFO "IN thread_function_1 thread_function: %d times\n", ++tc);  

       

                   if(tc == 10)
                   {

                            complete(&comp);

                            tc = 0;

                   }

                   msleep_interruptible(1000);
                  

    }while(!kthread_should_stop());  

    return tc;  

}  

  

static int hello_init(void)  
{  

    printk(KERN_INFO "Hello, world!\n");  

    init_completion(&comp);

    _tsk = kthread_run(thread_function, NULL, "mythread"); 

    if (IS_ERR(_tsk)) {  

        printk(KERN_INFO "first create kthread failed!\n");  

    }  

    else {  

        printk(KERN_INFO "first create ktrhead ok!\n");  

    }  

          _tsk1 = kthread_run(thread_function_1,NULL, "mythread2");

    if (IS_ERR(_tsk1)) {  

        printk(KERN_INFO "second create kthread failed!\n");  

    }  

    else {  

        printk(KERN_INFO "second create ktrhead ok!\n");  

    }  

    return 0;  

}  

  

static void hello_exit(void)  
{  

    printk(KERN_INFO "Hello, exit!\n");  

    if (!IS_ERR(_tsk)){  

        int ret = kthread_stop(_tsk);  

        printk(KERN_INFO "First thread function has stopped ,return %d\n", ret);  

    }  

    if(!IS_ERR(_tsk1))

         {

                   int ret = kthread_stop(_tsk1);

                   printk(KERN_INFO "Second thread function_1 has stopped ,return %d\n",ret);

         }

}   

module_init(hello_init);  

module_exit(hello_exit);
```


自己创建的内核线程，当把模块加载到内核之后，可以通过：ps –ef 命令来查看线程运行的情况。通过该命令可以看到该线程的pid和ppid等。也可以通过使用kill –s 9 pid 来杀死对应pid的线程。如果要支持kill命令自己创建的线程里面需要能接受kill信号。这里我们就来举一个例，支持kill命令，同时rmmod的时候也能杀死线程。


```
#include <linux/kernel.h>

#include <linux/module.h>

#include <linux/init.h>

#include <linux/param.h>

#include <linux/jiffies.h>

#include <asm/system.h>

#include <asm/processor.h>

#include <asm/signal.h>

#include <linux/completion.h>       // for DECLARE_COMPLETION()

#include <linux/sched.h>            

#include <linux/delay.h>            // mdelay()

#include <linux/kthread.h> 

 

MODULE_LICENSE("GPL");

 
static DECLARE_COMPLETION(my_completion);

 
static struct task_struct *task;

 
int flag = 0;

 
int my_fuction(void *arg)
{

    printk(" in %s()\n", __FUNCTION__);

    allow_signal(SIGKILL); //使得线程可以接收SIGKILL信号

    mdelay(2000);

    printk(" my_function complete()\n");

    printk("should stop: %d\n",kthread_should_stop());

    while (!signal_pending(current) && !kthread_should_stop()) {//使得线程可以可以被杀死，也可以再rmmod的时候结束

        printk(" jiffies is %lu\n", jiffies);

        set_current_state(TASK_INTERRUPTIBLE);

        schedule_timeout(HZ * 5);   

         printk("should stop: %d\n",kthread_should_stop());

    }

    printk("Leaving my_function\n");

    flag = 1; //flag很关键！

    return 0;

}

 

static int __init init(void)
{

    task = kthread_run(my_fuction,NULL,"my_function");

    printk("<1> init wait_for_completion()\n");

    return 0;

}

 

static void __exit finish(void)
{        

        int ret;

        if(!flag)
        {

                 if (!IS_ERR(task))
                 {  

                      int ret = kthread_stop(task);  

                      printk(KERN_INFO "First thread function has stopped ,return %d\n", ret);  

                 }                  

       }

    

    printk("task_struct: 0x%x",task);

    printk(" Goodbye\n");

}

 

module_init(init);

module_exit(finish);
```

运行结果（执行kill之后）：
运行结果（rmmod之后）：


说明：程序运行后线程循环执行每隔5个内核 ticks 就答应一次当前的jiffies值。可以通过kthread_stop()来结束，也可以通过kill命令来结束。

程序中使用了flag 变量来控制是否使用 kthread_stop()函数有两个原因：首先，当线程创建成功之后IS_ERR()不能检测出线程是否还在运行，因为此时task是一个正常的地址而不是错误码（后面会说明IS_ERR的原理）；其次，线程不能被杀次两次，如果使用kill命令之后线程已经被杀死，但是在此使用kthread_stop()函数就会出严重问题，因为此时线程已经被杀死，task指向的地址已经无效，struct kthread 也已经不存在，操作此时使用kthread_stop()设置should_stop是没有意义的。同样可以得出结论，当线程结束之后使用kthread_should_stop()来查看线程运行状态也会造成内核异常。

 

IS_ERR()函数的原理：

#define IS_ERR_VALUE(x) unlikely((x) >= (unsigned long)-MAX_ERRNO)

static inline long IS_ERR(const void *ptr)
{
　　return IS_ERR_VALUE((unsigned long)ptr);
}

内核中的函数常常返回指针，问题是如果出错，也希望能够通过返回的指针体现出来。
所幸的是，内核返回的指针一般是指向页面的边界(4K边界)，即

ptr & 0xfff == 0

这样ptr的值不可能落在（0xfffff000，0xffffffff）之间，而一般内核的出错代码也是一个小负数，在-1000到0之间，转变成unsigned long，正好在（0xfffff000，0xffffffff)之间。因此可以用

(unsigned long)ptr > (unsigned long)-1000L

也就等效于(x) >= (unsigned long)-MAX_ERRNO
其中MAX_ERRNO 为4095

来判断内核函数的返回值是一个有效的指针，还是一个出错代码。

涉及到的任何一个指针,必然有三种情况,一种是有效指针,一种是NULL,空指针,一种是错误指针,或者说无效指针.而所谓的错误指针就是指其已经到达了 最后一个page.比如对于32bit的系统来说,内核空间最高地址0xffffffff,那么最后一个page就是指的 0xfffff000~0xffffffff(假设4k一个page).这段地址是被保留的，如果超过这个地址，则肯定是错误的。

 
这里主要实现两个线程间通信，当flag = 10 之后通知另外一个线程（也就是“Linux内核多线程(二)”中的程序的各种平台实现）。


###首先是C++ 11 的方式：

```
#include <thread>
#include <iostream>
#include <mutex>
#include <queue>
#include <condition_variable>
#include <atomic>

using namespace std;
const int M = 10;

int main()
{
    mutex lockBuffer; 
     
    int flag = 0;
    bool stop = false;
    int count = 0;

    condition_variable_any recv_task_cond;

    condition_variable_any RecieveTask_cond;   

    thread recv_task([&]()
    { 
        while(true)
        {

                std::this_thread::sleep_for (chrono::milliseconds (1000));
                lockBuffer.lock ();

                if(stop)
                {
                    lockBuffer.unlock();
                    RecieveTask_cond.notify_one();
                    break;
                }

                if (flag == M)

                {

                    cout<< "recv task try to wake up RecieveTask! "<<endl;
                    count++;
                    lockBuffer.unlock ();
                    RecieveTask_cond.notify_one ();
                    
                }

                else
                {
                    flag++;
                    lockBuffer.unlock ();
                }

        }
        cout<< "recv_task exit"<<endl;

    } );


    thread RecieveTask([&]()

    {

        while(true)
            {
                std::this_thread::sleep_for (chrono::milliseconds (15));   

                cout<<"In Recieve Task !" <<endl;
                lockBuffer.lock ();

                if(flag != M)
                {

                    RecieveTask_cond.wait(lockBuffer);
                }

                if(stop)
                {
                    lockBuffer.unlock();
                    recv_task_cond.notify_one();
                    break;
                }

                cout<<"WAKE UP  "<< count <<" times \t"<<" FLAG = " << flag <<endl;
                cout<<endl;

                flag = 0;
                
                lockBuffer.unlock ();
                recv_task_cond.notify_one ();
            }
        cout<< "Recieve Task exit "<<endl;

    } );

    cout<< "Press Enter to stop "<<endl;
    getchar();
    stop = true;

    recv_task.join();
    RecieveTask.join();

    cout<<"Main Thread"<<endl;

    return 0;

}
```

###posix 线程库实现的方式


```
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

enum bool{FALSE = 0, TRUE = !FALSE};
int stop;

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;/*初始化互斥锁*/
pthread_cond_t cond = PTHREAD_COND_INITIALIZER;/*初始化条件变量*/

void *RecieveTask(void *);
void *recv_task(void *);

int i = 0;

int main()
{
    pthread_t RT;
    pthread_t r_t;
    stop = TRUE;

    pthread_create(&RT,NULL,RecieveTask,(void *)NULL);/*创建进程RecieveTask*/
    pthread_create(&r_t,NULL,recv_task,(void *)NULL); /*创建进程recv_task*/
    
    getchar();
    stop = FALSE;
    //printf("STOP\n");
    
    pthread_join(RT, NULL);/*等待进程recv_task结束*/
    
    printf("BACK IN MAIN \n");

    pthread_mutex_destroy(&mutex);
    pthread_cond_destroy(&cond);

    
    return 0;
}

void *recv_task(void *junk)
{

    while(stop)
    {
        pthread_mutex_lock(&mutex);/*锁住互斥量*/
/*
        if(stop)
        {
            pthread_cond_signal(&cond);
            printf("END recv_task\n");
            break;
        }
*/

        if(i == 10)
            {
                pthread_cond_signal(&cond);/*条件改变，发送信号，通知t_b进程*/
                pthread_cond_wait(&cond,&mutex);
            }    
        else
            printf("recv_task: %d \n",i++);

        pthread_mutex_unlock(&mutex);/*解锁互斥量*/

        sleep(1);

    }
    pthread_cond_signal(&cond);
    printf("recv_task exit \n");
}

void *RecieveTask(void *junk)
{

    while(stop)
    {

        pthread_mutex_lock(&mutex);

        if(i != 10)
            pthread_cond_wait(&cond,&mutex);/*等待*/
        if(!stop)
        {    
            printf("END RecieveTask \n");
            break;
        }

        printf("wake up RecieveTask: %d \n",i);
        i = 0;
        pthread_cond_signal(&cond);
        pthread_mutex_unlock(&mutex);

        sleep(1);

    }
    printf("RecieveTask exit \n");
}
```


http://www.cnblogs.com/zhuyp1015/archive/2012/06/13/2548494.html
http://www.cnblogs.com/zhuyp1015/archive/2012/06/11/2545702.html
http://www.cnblogs.com/zhuyp1015/archive/2012/06/13/2548458.html
http://www.cnblogs.com/zhuyp1015/archive/2012/06/14/2549973.html
