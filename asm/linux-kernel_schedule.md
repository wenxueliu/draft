#内核分析 第二周

##基本数据结构

/* CPU-specific state of this task */
struct Thread {
    unsigned long		ip;
    unsigned long		sp;
};

typedef struct PCB{
    int pid;
    volatile long state;	/* -1 unrunnable, 0 runnable, >0 stopped */
    char stack[KERNEL_STACK_SIZE];
    /* CPU-specific state of this task */
    struct Thread thread;
    unsigned long	task_entry;
    struct PCB *next;
}tPCB;

##内核启动

1. 在 linux-3.9.4/include/linux/start_kernel.h 增加外部声明 void __init my_start_kernel(void)
2. 在 linux-3.9.4/init/main.c 中的 start_kernel 函数中调用 my_start_kernel

由此可见, start_kernel 函数担任了内核初始化工作.

my_start_kernel 函数具体实现是在 mymain.c 进行初始化工作.

```
void __init my_start_kernel(void)
{
    int pid = 0;
    //初始j进程 pid 为 0
    task[pid].pid = pid;
    //状态为 runnable
    task[pid].state = 0;/* -1 unrunnable, 0 runnable, >0 stopped */
    //进程处理函数
    task[pid].task_entry = task[pid].thread.ip = (unsigned long)my_process;
    //堆栈指向该进程栈的栈顶
    task[pid].thread.sp = (unsigned long)&task[pid].stack[KERNEL_STACK_SIZE-1];
    //该进程的下一个进程为本身
    task[pid].next = &task[pid];

    //类似上面初始化工作. 用 task[0] 初始化 task[1] task[2] ..
    //task[MAX_TASK_NUM-1]. 但修改进程 pid, state, stack, next
    int i;
    for(i=1;i<MAX_TASK_NUM;i++)
    {
        memcpy(&task[i],&task[0],sizeof(tPCB));
        task[i].pid = i;
        task[i].state = -1;
        task[i].thread.sp = (unsigned long)&task[i].stack[KERNEL_STACK_SIZE-1];
        /*
           task[1].next = task[0].next; task[0].next = task[1]
           task[2].next = task[1].next; task[1].next = task[2]
           ...
           将所有进程通过有环链表连接起来.
        */
        task[i].next = task[i-1].next;
        task[i-1].next = &task[i];
    }
    /* start process 0 by task[0] */
    pid = 0;
    //初始化 my_current_task 为 task[0]
    my_current_task = &task[pid];
	asm volatile(
    	"movl %1,%%esp\n\t" 	/* 栈的 esp 指向 task[0].thread.sp 的地址 */
    	"pushl %1\n\t" 	        /* task[0].thread.sp 压栈 */
    	"pushl %0\n\t" 	        /* task[0].thread.ip 压栈 */
    	"ret\n\t" 	            /* 将 task[0].thread.ip 保存到 cs:eip 下一条指令执行就从
                                   task[0].thread.ip 处开始执行, 即执行 my_process 函数*/
    	"popl %%ebp\n\t"        /* 将 task[0].thread.sp 保存到 ebp */
    	:
    	: "c" (task[pid].thread.ip),"d" (task[pid].thread.sp)	/* input c or d mean %ecx/%edx*/
	);
}
```

执行完 my_start_kernel 及其他系统启动函数, 最终系统启动.

问题: start_kernel 如何与 mymain.c 中的 my_start_kernel 关联的?

###进程运行

目前每个 task 的入口都是 my_process.

```
void my_process(void) {
    int i = 0;
    while(1) {
        //i 会溢出. 需要在一定大小进行清零
        i++;

        //该值越大, 进程切换越不及时.
        int sched_check_feq = 10000000;

        //每执行 sched_check_feq 检查一次是否进行内核切换.
        if(i%sched_check_feq == 0) {
            printk(KERN_NOTICE "this is process %d -\n",my_current_task->pid);
            if(my_need_sched == 1)
            {
                my_need_sched = 0;
        	    my_schedule();
        	}
        	printk(KERN_NOTICE "this is process %d +\n",my_current_task->pid);
        }
        if (i == sched_check_feq * 1000) {
            i = 0;
        }
    }
}
```

###中断

在 arch/x86/kernel/time.c 中 setup_default_timer_irq 调用 setup_irq(0, &irq0),
而 irq0.handler = timer_interrupt. timer_interrupt 中调用了 my_timer_handler

因此, 每次时钟中断都会调用 my_timer_handler 函数.

```
/*
 * Called by timer interrupt.
 * it runs in the name of current running process,
 * so it use kernel stack of current running process
 */
void my_timer_handler(void)
{
#if 1
    //该值越大, 进程切换速度越慢. 越小, 进程切换越快.
    int sched_feq = 1000.
    //每次时钟中断, time_count 加 1, 当 time_count 整除 1000 时, 重置 my_need_sched 为 1,
    //my_need_sched = 1 表明下次要进行进程切换. 注意这里 time_count
    //在制定数量时要重置为 0, 否则 int 类型溢出
    if(time_count%sched_feq == 0 && my_need_sched != 1) {
        printk(KERN_NOTICE ">>>my_timer_handler here<<<\n");
        my_need_sched = 1;
    }
    time_count ++ ;
    if (time_count == 1000000) {
        time_count = 0;
    }
#endif
    return;
}
```

###进程调度

以下以 task[0] 切换到 task[1] 为例.

```
void my_schedule(void)
{
    tPCB * next;
    tPCB * prev;

    //由于 my_current_task 已经在 my_start_kernel 初始化了, 因此, 这里条件不成立.
    if(my_current_task == NULL
        || my_current_task->next == NULL)
    {
    	return;
    }
    printk(KERN_NOTICE ">>>my_schedule<<<\n");

    //next 指向 task[1]
    next = my_current_task->next;
    //prev 指向 task[0]
    prev = my_current_task;
    //显然条件成立, 因为 task[1].[state] = 0
    if(next->state == 0)/* -1 unrunnable, 0 runnable, >0 stopped */
    {
    	/* switch to next process */
    	asm volatile(
            //保持现场
        	"pushl %%ebp\n\t" 	    /* ebp 压栈, 保存 task[0] 的栈基址 */
        	"movl %%esp,%0\n\t" 	/* 保持 esp 到内存变量 task[0]->thread.sp */
            //切换到 task[1] 的栈
        	"movl %2,%%esp\n\t"     /* 将内存变量 task[1]->thread.sp 赋值给 esp,
                                     此时完成了进程栈的切换*/
            //task 下次执行开始地址.
        	"movl $1f,%1\n\t"       /* 将 1: 的地址保存到 task[0]->thread.ip */
            //进行进程切换
        	"pushl %3\n\t"          /* task[1]->thread.ip 压栈.
        	"ret\n\t" 	            /* 将 task[1]->thread.ip 从栈弹出放入 cs:eip,
                                       调用 task[1] 的 my_process 函数 */
            //下次 切换到 task[0] 从此处开始执行
        	"1:\t"                  /*  */
            //如果切换到 task[0], 先将 ebp 出栈, 恢复 task[0] 的栈
        	"popl %%ebp\n\t"
        	: "=m" (prev->thread.sp),"=m" (prev->thread.ip)
        	: "m" (next->thread.sp),"m" (next->thread.ip)
    	);
        //已经执行完 task[1] 的 entry 函数. my_current_task 指向 task[1]
    	my_current_task = next;
    	printk(KERN_NOTICE ">>>switch %d to %d<<<\n",prev->pid,next->pid);
    }
    else
    {
        //标记 task[1]->state = 0 可以执行
        next->state = 0;
        //my_current_task 指向 task[1]
        my_current_task = next;
        printk(KERN_NOTICE ">>>switch %d to %d<<<\n",prev->pid,next->pid);
    	/* switch to new process */
    	asm volatile(
        	"pushl %%ebp\n\t" 	    /* 保存 task[0] 栈的 ebp, 压栈, 是否可以保存在内存? */
        	"movl %%esp,%0\n\t" 	/* task[0] 的 esp 保存在 task[0]->thread.sp */
        	"movl %2,%%esp\n\t"     /* task[1] 的 esp 保持在 esp */
        	"movl %2,%%ebp\n\t"     /* 将 task[1]->thread.sp 保持在 ebp*/
        	"movl $1f,%1\n\t"       /* 将 1: 地址保存在 task[0]->thread.ip, 下次
                                     task[0] 从 1: 处开始执行 */
        	"pushl %3\n\t"          /* task[1]->thread.ip 压栈*/
        	"ret\n\t" 	            /* cs:eip = task[1]->thread.ip, 从 task[1]->thread.ip
                                       处开始执行, 即调用 my_process */
        	: "=m" (prev->thread.sp),"=m" (prev->thread.ip)
        	: "m" (next->thread.sp),"m" (next->thread.ip)
    	);
    }
    return;
}
```

##总结

内核启动后, 调用 start_kernel, 其中调用了 my_start_kernel 函数. 而
my_start_kernel 的内联汇编部分将系统的 cs:eip 指向 task[0].task_entry
(my_process 的地址), 系统栈指向 task[0].thread.sp. cpu 于是开始执行
my_process. 而 my_process 是死循环while(1), 因此一直执行.

此外, 系统每过一段时间会发生一次时钟中断, time_count 加 1. 当
time_count % 1000 == 1 且 my_need_sched != 1 时, 重置 my_need_sched 为 1.
这样, my_process 中的下次执行 while(1) 发现 my_need_sched == 1, 于是根据
my_schedule 调度算法进行进程切换.  将系统当前栈指向 task[1] 的 esp, 将 cs:eip 指向
task[1].task_entry(my_process 地址). 于是系统从 my_process 开始执行. (注意
我们可以为每个 task 分配不同的处理函数). 即通过时钟中断进行进程切换.

如此往复, 进程从 task[0] -> task[1] -> task[2] -> task[3] -> task[0] 这样进行
无限循环. 当然, 我们可以增加 task 个数, 对 task 进行优先级调整, 权重调整, 需要
改变的仅仅是 my_schedule 部分.

至此, 整个系统就运行起来了.

####进程调度算法(my_schedule):

开始先执行 task[0] 第一次调度执行 my_schedule 的 else 部分, 然后切换到 task[1]
执行它的 my_process 函数. 执行完之后, 再次调度, 执行 my_schedule 的 else 部分. 然后切换到
task[2] 执行它的 my_process 函数. 之后执行 task[0]. 执行 my_schedule 的 if 部分,
切换到 task[1], 执行 my_schedule 的 if 部分; 切换到 task[1], 执行 my_schedule 的 if 部分,
如此往复.
