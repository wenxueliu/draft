

自进程虽然与父进程执行的代码一样, 但是, 实际的 IP,CS 肯定是不一样的.
通过汇编代码验证之

进程的创建与人类的繁衍非常相似, 我们身上留着父母的血, 遗传了他们的基因.


 Linux中，1号进程是所有用户态进程的祖先，0号进程是所有内核线程的祖先

Linux中，fork、vfork和clone三个系统调用都是通过调用do_fork来实现进程的创建。

Linux中，fork()系统调用产生的子进程在系统调用处理过程中从 ret_from_fork 处开始执行。

fork()系统调用具有“一次调用，两次返回”的特点


本文目的, 跟踪 fork 从用户态到内核态之后返回用户态的整个流程. 最后通过
调试验证该流程.

##进程描述块

谈论Linux 进程, 不能绕过 task_struct 数据结构. 该结构定义在
[linux/include/linux/sched.h](http://code.woboq.org/linux/linux/include/linux/sched.h.html#task_struct)

由于数量代码量非常庞大, 事实上对此, 只需要大概了解即可. 下面只列出我自己感觉有用的成员

* volatile long state; /* -1 unrunnable, 0 runnable, >0 stopped */
* void *stack;
* atomic_t usage;
* unsigned int flags; /* per process flags, defined below */
* struct sched_info sched_info
* struct list_head tasks;
* struct mm_struct *mm, *active_mm;
* int exit_state;
* int exit_code, exit_signal;
* unsigned long atomic_flags; /* Flags needing atomic access. */
* struct restart_block restart_block;
* struct task_struct __rcu *real_parent; /* real parent process */
* struct task_struct __rcu *parent;
* struct list_head children; /* list of my children */
* struct list_head sibling; /* linkage in my parent's children list */
* struct task_struct *group_leader; /* threadgroup leader */

* struct sched_class *sched_class;
* struct sched_entity se;
* struct pid_link pids[PIDTYPE_MAX];
* struct list_head thread_group;
* struct list_head thread_node;
* pid_t pid;
* pid_t tgid;
* struct sysv_sem sysvsem; //IPC
* struct sysv_shm sysvshm;
* struct nameidata *nameidata;
* struct fs_struct *fs;
* struct files_struct *files;
* void *journal_info;
* struct list_head tasks;
* struct mm_struct *mm, *active_mm;
* struct thread_struct thread;


还有一些 pstrace, numa, smp, perf_event, cgroup, 中断跟踪, 信号处理等并不是目前关注的问题.

##进程创建

从系统调用部分, 我们已经对系统调用有了基本的了解. 因此, 这里通过对 fork
这个系统调用的学习, 一方面加深对系统调用的理解, 一方面理解进程创建的原理.

首先当用户通过 fork 这个系统调用创建一个新的进程的时候, 首先触发中断 0x80,
系统由用户态跳转到内核态. 内核态首先保存现场, 根据用户态传递的系统调用号,
在[这里](http://code.woboq.org/linux/linux/arch/x86/include/generated/asm/syscalls_64.h.html)
查找 sys_call_table 找到 fork 对应的系统处理函数 sys_fork(实际上为
SYSCALL_DEFINE0(fork))

fork 的代码具体实现在[这里](http://code.woboq.org/linux/linux/kernel/fork.c.html)

首先, 调用 _do_fork(SIGCHLD, 0, 0, NULL, NULL, 0)

而 _do_fork 对 fork 主要有用的两个函数

```
p = copy_process(clone_flags, stack_start, stack_size,
child_tidptr, NULL, trace, tls);

```
当 copy_process 执行成功:
1. pid = get_task_pid(p, PIDTYPE_PID); 获取进程 pid
2. wake_up_new_task(p);

至此, 系统调用 fork 返回. 其余部分与系统参照系统调用部分. 下面着重分析
copy_process 和 wake_up_new_task

###copy_process

```
http://code.woboq.org/linux/linux/kernel/fork.c.html#copy_process

static struct task_struct *copy_process(unsigned long clone_flags,
					unsigned long stack_start,
					unsigned long stack_size,
					int __user *child_tidptr,
					struct pid *pid,
					int trace,
					unsigned long tls)
{
	int retval;
	struct task_struct *p;
    //调用 security_hook_heads.task_create 中每一个元素 P 的 P->hook.task_create(clone_flags)
	retval = security_task_create(clone_flags);
	if (retval)
		goto fork_out;
	retval = -ENOMEM;
    //为新的进程分配内核空间, 新进程分配内核堆栈. 之后将 current 拷贝给
    //新创建进程 p, 设置相关属性. 并返回 p. 至此, 新进程的空间及内容已经
    //就绪.
	p = dup_task_struct(current);
	if (!p)
		goto fork_out;

    //初始化 p->pi_lock
	rt_mutex_init_task(p);

	retval = -EAGAIN;
	current->flags &= ~PF_NPROC_EXCEEDED;
    //为 p 分配内核空间, 并将 current->cred 拷贝给 p, 并更新 p->cred 相关成员
	retval = copy_creds(p, clone_flags);
	if (retval < 0)
		goto bad_fork_free;
	/*
	 * If multiple threads are within copy_process(), then this check
	 * triggers too late. This doesn't hurt, the check is only there
	 * to stop root fork bombs.
	 */
	retval = -EAGAIN;
	if (nr_threads >= max_threads)
		goto bad_fork_cleanup_count;
    //为 p->delays 分配内核空间并加锁
	delayacct_tsk_init(p);	/* Must remain after dup_task_struct() */

    //下面初始化 p 相关数据成员
	p->flags &= ~(PF_SUPERPRIV | PF_WQ_WORKER);
	p->flags |= PF_FORKNOEXEC;
	INIT_LIST_HEAD(&p->children);
	INIT_LIST_HEAD(&p->sibling);
	rcu_copy_process(p);
	p->vfork_done = NULL;
	spin_lock_init(&p->alloc_lock);
	init_sigpending(&p->pending);
	p->utime = p->stime = p->gtime = 0;
	p->utimescaled = p->stimescaled = 0;
	prev_cputime_init(&p->prev_cputime);

#ifdef CONFIG_VIRT_CPU_ACCOUNTING_GEN
	seqcount_init(&p->vtime_seqcount);
	p->vtime_snap = 0;
	p->vtime_snap_whence = VTIME_INACTIVE;
#endif
#if defined(SPLIT_RSS_COUNTING)
	memset(&p->rss_stat, 0, sizeof(p->rss_stat));
#endif
	p->default_timer_slack_ns = current->timer_slack_ns;
    //p->ioac 置零
	task_io_accounting_init(&p->ioac);
	acct_clear_integrals(p);
	posix_cpu_timers_init(p);
	p->start_time = ktime_get_ns();
	p->real_start_time = ktime_get_boot_ns();
	p->io_context = NULL;
	p->audit_context = NULL;
	threadgroup_change_begin(current);
	cgroup_fork(p);
#ifdef CONFIG_NUMA
	p->mempolicy = mpol_dup(p->mempolicy);
	if (IS_ERR(p->mempolicy)) {
		retval = PTR_ERR(p->mempolicy);
		p->mempolicy = NULL;
		goto bad_fork_cleanup_threadgroup_lock;
	}
#endif
#ifdef CONFIG_CPUSETS
	p->cpuset_mem_spread_rotor = NUMA_NO_NODE;
	p->cpuset_slab_spread_rotor = NUMA_NO_NODE;
	seqcount_init(&p->mems_allowed_seq);
#endif
#ifdef CONFIG_TRACE_IRQFLAGS
	p->irq_events = 0;
	p->hardirqs_enabled = 0;
	p->hardirq_enable_ip = 0;
	p->hardirq_enable_event = 0;
	p->hardirq_disable_ip = _THIS_IP_;
	p->hardirq_disable_event = 0;
	p->softirqs_enabled = 1;
	p->softirq_enable_ip = _THIS_IP_;
	p->softirq_enable_event = 0;
	p->softirq_disable_ip = 0;
	p->softirq_disable_event = 0;
	p->hardirq_context = 0;
	p->softirq_context = 0;
#endif
	p->pagefault_disabled = 0;
#ifdef CONFIG_LOCKDEP
	p->lockdep_depth = 0; /* no locks held yet */
	p->curr_chain_key = 0;
	p->lockdep_recursion = 0;
#endif
#ifdef CONFIG_DEBUG_MUTEXES
	p->blocked_on = NULL; /* not blocked yet */
#endif
#ifdef CONFIG_BCACHE
	p->sequential_io	= 0;
	p->sequential_io_avg	= 0;
#endif



	/* Perform scheduler related setup. Assign this task to a CPU. */
    //初始化 sched, numa 相关成员, TODO
	retval = sched_fork(clone_flags, p);
	if (retval)
		goto bad_fork_cleanup_policy;
    //初始化 CONFIG_PERF_EVENTS 条件编译中的成员
	retval = perf_event_init_task(p);
	if (retval)
		goto bad_fork_cleanup_policy;
    //为成员 audit_context 分配内存并初始化, 并设置 TIF_SYSCALL_AUDIT 标志
	retval = audit_alloc(p);
	if (retval)
		goto bad_fork_cleanup_perf;
	/* copy all the process information */
    //初始化 p->sysvshm
	shm_init_task(p);
	retval = copy_semundo(clone_flags, p);
	if (retval)
		goto bad_fork_cleanup_audit;
    //拷贝父进程的 files
	retval = copy_files(clone_flags, p);
	if (retval)
		goto bad_fork_cleanup_semundo;
    //拷贝父进程的 fs
	retval = copy_fs(clone_flags, p);
	if (retval)
		goto bad_fork_cleanup_files;
    //拷贝父进程的 sighand
	retval = copy_sighand(clone_flags, p);
	if (retval)
		goto bad_fork_cleanup_fs;

    //拷贝父进程的 signal
	retval = copy_signal(clone_flags, p);
	if (retval)
		goto bad_fork_cleanup_sighand;

    //关键, 拷贝父进程的 mm, TODO 详细分析
	retval = copy_mm(clone_flags, p);
	if (retval)
		goto bad_fork_cleanup_signal;
    //创建自己的命名空间
	retval = copy_namespaces(clone_flags, p);
	if (retval)
		goto bad_fork_cleanup_mm;
    //拷贝父进程的 io_context
	retval = copy_io(clone_flags, p);
	if (retval)
		goto bad_fork_cleanup_namespaces;
    //拷贝父进程的 thread
	retval = copy_thread_tls(clone_flags, stack_start, stack_size, p, tls);
	if (retval)
		goto bad_fork_cleanup_io;
	if (pid != &init_struct_pid) {
		pid = alloc_pid(p->nsproxy->pid_ns_for_children);
		if (IS_ERR(pid)) {
			retval = PTR_ERR(pid);
			goto bad_fork_cleanup_io;
		}
	}
	p->set_child_tid = (clone_flags & CLONE_CHILD_SETTID) ? child_tidptr : NULL;
	/*
	 * Clear TID on mm_release()?
	 */
	p->clear_child_tid = (clone_flags & CLONE_CHILD_CLEARTID) ? child_tidptr : NULL;
#ifdef CONFIG_BLOCK
	p->plug = NULL;
#endif
#ifdef CONFIG_FUTEX
	p->robust_list = NULL;
#ifdef CONFIG_COMPAT
	p->compat_robust_list = NULL;
#endif
	INIT_LIST_HEAD(&p->pi_state_list);
	p->pi_state_cache = NULL;
#endif
	/*
	 * sigaltstack should be cleared when sharing the same VM
	 */
	if ((clone_flags & (CLONE_VM|CLONE_VFORK)) == CLONE_VM)
		p->sas_ss_sp = p->sas_ss_size = 0;
	/*
	 * Syscall tracing and stepping should be turned off in the
	 * child regardless of CLONE_PTRACE.
	 */
	user_disable_single_step(p);
	clear_tsk_thread_flag(p, TIF_SYSCALL_TRACE);
#ifdef TIF_SYSCALL_EMU
	clear_tsk_thread_flag(p, TIF_SYSCALL_EMU);
#endif
	clear_all_latency_tracing(p);
	/* ok, now we should be set up.. */
	p->pid = pid_nr(pid);
	if (clone_flags & CLONE_THREAD) {
		p->exit_signal = -1;
		p->group_leader = current->group_leader;
		p->tgid = current->tgid;
	} else {
		if (clone_flags & CLONE_PARENT)
			p->exit_signal = current->group_leader->exit_signal;
		else
			p->exit_signal = (clone_flags & CSIGNAL);
		p->group_leader = p;
		p->tgid = p->pid;
	}
	p->nr_dirtied = 0;
	p->nr_dirtied_pause = 128 >> (PAGE_SHIFT - 10);
	p->dirty_paused_when = 0;
	p->pdeath_signal = 0;
	INIT_LIST_HEAD(&p->thread_group);
	p->task_works = NULL;

    //后续 TODO
	/*
	 * Ensure that the cgroup subsystem policies allow the new process to be
	 * forked. It should be noted the the new process's css_set can be changed
	 * between here and cgroup_post_fork() if an organisation operation is in
	 * progress.
	 */
	retval = cgroup_can_fork(p);
	if (retval)
		goto bad_fork_free_pid;
	/*
	 * Make it visible to the rest of the system, but dont wake it up yet.
	 * Need tasklist lock for parent etc handling!
	 */
	write_lock_irq(&tasklist_lock);
	/* CLONE_PARENT re-uses the old parent */
	if (clone_flags & (CLONE_PARENT|CLONE_THREAD)) {
		p->real_parent = current->real_parent;
		p->parent_exec_id = current->parent_exec_id;
	} else {
		p->real_parent = current;
		p->parent_exec_id = current->self_exec_id;
	}
	spin_lock(&current->sighand->siglock);
	/*
	 * Copy seccomp details explicitly here, in case they were changed
	 * before holding sighand lock.
	 */
	copy_seccomp(p);
	/*
	 * Process group and session signals need to be delivered to just the
	 * parent before the fork or both the parent and the child after the
	 * fork. Restart if a signal comes in before we add the new process to
	 * it's process group.
	 * A fatal signal pending means that current will exit, so the new
	 * thread can't slip out of an OOM kill (or normal SIGKILL).
	*/
	recalc_sigpending();
	if (signal_pending(current)) {
		spin_unlock(&current->sighand->siglock);
		write_unlock_irq(&tasklist_lock);
		retval = -ERESTARTNOINTR;
		goto bad_fork_cancel_cgroup;
	}
	if (likely(p->pid)) {
		ptrace_init_task(p, (clone_flags & CLONE_PTRACE) || trace);
		init_task_pid(p, PIDTYPE_PID, pid);
		if (thread_group_leader(p)) {
			init_task_pid(p, PIDTYPE_PGID, task_pgrp(current));
			init_task_pid(p, PIDTYPE_SID, task_session(current));
			if (is_child_reaper(pid)) {
				ns_of_pid(pid)->child_reaper = p;
				p->signal->flags |= SIGNAL_UNKILLABLE;
			}
			p->signal->leader_pid = pid;
			p->signal->tty = tty_kref_get(current->signal->tty);
			list_add_tail(&p->sibling, &p->real_parent->children);
			list_add_tail_rcu(&p->tasks, &init_task.tasks);
			attach_pid(p, PIDTYPE_PGID);
			attach_pid(p, PIDTYPE_SID);
			__this_cpu_inc(process_counts);
		} else {
			current->signal->nr_threads++;
			atomic_inc(&current->signal->live);
			atomic_inc(&current->signal->sigcnt);
			list_add_tail_rcu(&p->thread_group,
					  &p->group_leader->thread_group);
			list_add_tail_rcu(&p->thread_node,
					  &p->signal->thread_head);
		}
		attach_pid(p, PIDTYPE_PID);
		nr_threads++;
	}
	total_forks++;
	spin_unlock(&current->sighand->siglock);
	syscall_tracepoint_update(p);
	write_unlock_irq(&tasklist_lock);
	proc_fork_connector(p);
	cgroup_post_fork(p);
	threadgroup_change_end(current);
	perf_event_fork(p);
	trace_task_newtask(p, clone_flags);
	uprobe_copy_process(p, clone_flags);
	return p;
bad_fork_cancel_cgroup:
	cgroup_cancel_fork(p);
bad_fork_free_pid:
	if (pid != &init_struct_pid)
		free_pid(pid);
bad_fork_cleanup_io:
	if (p->io_context)
		exit_io_context(p);
bad_fork_cleanup_namespaces:
	exit_task_namespaces(p);
bad_fork_cleanup_mm:
	if (p->mm)
		mmput(p->mm);
bad_fork_cleanup_signal:
	if (!(clone_flags & CLONE_THREAD))
		free_signal_struct(p->signal);
bad_fork_cleanup_sighand:
	__cleanup_sighand(p->sighand);
bad_fork_cleanup_fs:
	exit_fs(p); /* blocking */
bad_fork_cleanup_files:
	exit_files(p); /* blocking */
bad_fork_cleanup_semundo:
	exit_sem(p);
bad_fork_cleanup_audit:
	audit_free(p);
bad_fork_cleanup_perf:
	perf_event_free_task(p);
bad_fork_cleanup_policy:
#ifdef CONFIG_NUMA
	mpol_put(p->mempolicy);
bad_fork_cleanup_threadgroup_lock:
#endif
	threadgroup_change_end(current);
	delayacct_tsk_free(p);
bad_fork_cleanup_count:
	atomic_dec(&p->cred->user->processes);
	exit_creds(p);
bad_fork_free:
	free_task(p);
fork_out:
	return ERR_PTR(retval);
}
```

dup_task_struct 分析

```
http://code.woboq.org/linux/linux/kernel/fork.c.html#dup_task_struct

static struct task_struct *dup_task_struct(struct task_struct *orig)
{
	struct task_struct *tsk;
	struct thread_info *ti;
    //对于非 NUMA 架构, 返回 -1
	int node = tsk_fork_get_node(orig);
	int err;
    //为新进程分配内核空间:
    //  kmem_cache_alloc_node(task_struct_cachep, GFP_KERNEL, node);
    //  slab_alloc_node(s, gfpflags, node, _RET_IP_);
    //
	tsk = alloc_task_struct_node(node);
	if (!tsk)
		return NULL;
    //为新进程分配线程页信息:
    //  struct page *page = alloc_kmem_pages_node(node, THREADINFO_GFP, THREAD_SIZE_ORDER);
    //  return page ? page_address(page) : NULL;
	ti = alloc_thread_info_node(tsk, node);
	if (!ti)
		goto free_tsk;
    //将 tsk 指向 org 的内存地址
    //  *tsk = *org
	err = arch_dup_task_struct(tsk, orig);
	if (err)
		goto free_ti;
    //注意这里 tsk 的 stack 是自己重新分配的, 而不是共享.
	tsk->stack = ti;
#ifdef CONFIG_SECCOMP
	/*
	 * We must handle setting up seccomp filters once we're under
	 * the sighand lock in case orig has changed between now and
	 * then. Until then, filter must be NULL to avoid messing up
	 * the usage counts on the error path calling free_task.
	 */
	tsk->seccomp.filter = NULL;
#endif
    //初始化 task 的栈为 origin 的栈
    //  tsk->stack = orig->stack
    //  tsk->stack->task = tsk
	setup_thread_stack(tsk, orig);
    //置零 tsk->stack->flags 中的 TIF_USER_RETURN_NOTIFY 标志
	clear_user_return_notifier(tsk);
    //置零 tsk->stack->flags 中的 TIF_NEED_RESCHED 标志
	clear_tsk_need_resched(tsk);
    //溢出检查
    //将 tsk->stack 最后一个自己设置为 STACK_END_MAGIC, 标记 stack 结束
	set_task_stack_end_magic(tsk);
#ifdef CONFIG_CC_STACKPROTECTOR
	tsk->stack_canary = get_random_int();
#endif
	/*
	 * One for us, one for whoever does the "release_task()" (usually
	 * parent)
	 */
	atomic_set(&tsk->usage, 2);
#ifdef CONFIG_BLK_DEV_IO_TRACE
	tsk->btrace_seq = 0;
#endif
    //设置 task_struct 一些属性
	tsk->splice_pipe = NULL;
	tsk->task_frag.page = NULL;
	tsk->wake_q.next = NULL;
	account_kernel_stack(ti, 1);
	return tsk;
free_ti:
	free_thread_info(ti);
free_tsk:
	free_task_struct(tsk);
	return NULL;
}
```





###wake_up_new_task

```
/*
 * wake_up_new_task - wake up a newly created task for the first time.
 *
 * This function will do some initial scheduler statistics housekeeping
 * that must be done for every newly created context, then puts the task
 * on the runqueue and wakes it.
 */
void wake_up_new_task(struct task_struct *p)
{
	unsigned long flags;
	struct rq *rq;
	raw_spin_lock_irqsave(&p->pi_lock, flags);
	/* Initialize new task's runnable average */
	init_entity_runnable_average(&p->se);
#ifdef CONFIG_SMP
	/*
	 * Fork balancing, do it here and not earlier because:
	 *  - cpus_allowed can change in the fork path
	 *  - any previously selected cpu might disappear through hotplug
	 */
	set_task_cpu(p, select_task_rq(p, task_cpu(p), SD_BALANCE_FORK, 0));
#endif
	rq = __task_rq_lock(p);
	activate_task(rq, p, 0);
	p->on_rq = TASK_ON_RQ_QUEUED;
	trace_sched_wakeup_new(p);
	check_preempt_curr(rq, p, WF_FORK);
#ifdef CONFIG_SMP
	if (p->sched_class->task_woken) {
		/*
		 * Nothing relies on rq->lock after this, so its fine to
		 * drop it.
		 */
		lockdep_unpin_lock(&rq->lock);
		p->sched_class->task_woken(rq, p);
		lockdep_pin_lock(&rq->lock);
	}
#endif
	task_rq_unlock(rq, p, &flags);
}
```

附录


task_struct 中会保留父进程信息的数据成员. 未完待续
```
struct task_struct {
	volatile long state;	/* -1 unrunnable, 0 runnable, >0 stopped */
	void *stack;
	atomic_t usage;
	unsigned int flags;	/* per process flags, defined below */
	unsigned int ptrace;
#ifdef CONFIG_SMP
	struct llist_node wake_entry;
	int on_cpu;
	unsigned int wakee_flips;
	unsigned long wakee_flip_decay_ts;
	struct task_struct *last_wakee;
	int wake_cpu;
#endif
    //prio 父进程的 normal_prio
	int prio, static_prio, normal_prio;
	unsigned int rt_priority;
	const struct sched_class *sched_class;
    //重要结构, 非克隆
	struct sched_rt_entity rt;
#ifdef CONFIG_CGROUP_SCHED
	struct task_group *sched_task_group;
#endif
    //重要结构, 非克隆
	struct sched_dl_entity dl;
#ifdef CONFIG_BLK_DEV_IO_TRACE
	unsigned int btrace_seq;
#endif
	unsigned int policy;
	int nr_cpus_allowed;
	cpumask_t cpus_allowed;
#ifdef CONFIG_TASKS_RCU
	unsigned long rcu_tasks_nvcsw;
#endif /* #ifdef CONFIG_TASKS_RCU */
#ifdef CONFIG_SCHED_INFO
	struct sched_info sched_info;
#endif
	struct list_head tasks;
#ifdef CONFIG_SMP
	struct plist_node pushable_tasks;
	struct rb_node pushable_dl_tasks;
#endif
	struct mm_struct *mm, *active_mm;
	/* per-thread vma caching */
	u32 vmacache_seqnum;
	struct vm_area_struct *vmacache[VMACACHE_SIZE];
/* task state */
	int exit_state;
	int exit_code, exit_signal;
	unsigned long jobctl;	/* JOBCTL_*, siglock protected */
	/* Used for emulating ABI behavior of previous Linux versions */
	unsigned int personality;
	/* scheduler bits, serialized by scheduler locks */
	unsigned sched_reset_on_fork:1;
	unsigned sched_contributes_to_load:1;
	unsigned sched_migrated:1;
	unsigned :0; /* force alignment to the next boundary */
	/* unserialized, strictly 'current' */
	unsigned in_execve:1; /* bit to tell LSMs we're in execve */
	unsigned in_iowait:1;
#ifdef CONFIG_MEMCG
	unsigned memcg_may_oom:1;
#ifndef CONFIG_SLOB
	unsigned memcg_kmem_skip_account:1;
#endif
#endif
#ifdef CONFIG_COMPAT_BRK
	unsigned brk_randomized:1;
#endif
	unsigned long atomic_flags; /* Flags needing atomic access. */
	struct restart_block restart_block;
	pid_t pid;
	pid_t tgid;
#ifdef CONFIG_CC_STACKPROTECTOR
	/* Canary value for the -fstack-protector gcc feature */
	unsigned long stack_canary;
#endif
	/*
	 * pointers to (original) parent process, youngest child, younger sibling,
	 * older sibling, respectively.  (p->father can be replaced with
	 * p->real_parent->pid)
	 */
	struct task_struct __rcu *real_parent; /* real parent process */
	struct task_struct __rcu *parent; /* recipient of SIGCHLD, wait4() reports */
	struct task_struct *group_leader;	/* threadgroup leader */
	/*
	 * ptraced is the list of tasks this task is using ptrace on.
	 * This includes both natural children and PTRACE_ATTACH targets.
	 * p->ptrace_entry is p's link on the p->parent->ptraced list.
	 */
	struct list_head ptraced;
	struct list_head ptrace_entry;
	/* PID/PID hash table linkage. */
	struct pid_link pids[PIDTYPE_MAX];
	struct list_head thread_node;
	unsigned long nvcsw, nivcsw; /* context switch counts */
/* mm fault and swap info: this can arguably be seen as either mm-specific or thread-specific */
	unsigned long min_flt, maj_flt;
/* process credentials */
	const struct cred __rcu *real_cred; /* objective and real subjective task
					 * credentials (COW) */
	char comm[TASK_COMM_LEN]; /* executable name excluding path
				     - access with [gs]et_task_comm (which lock
				       it with task_lock())
				     - initialized normally by setup_new_exec */
/* file system info */
	struct nameidata *nameidata;
#ifdef CONFIG_SYSVIPC
/* ipc stuff */
	struct sysv_sem sysvsem;
#endif
#ifdef CONFIG_DETECT_HUNG_TASK
/* hung task detection */
	unsigned long last_switch_count;
#endif
/* filesystem information */
	struct fs_struct *fs;       //拷贝父进程
/* open file information */
	struct files_struct *files; //拷贝父进程
/* signal handlers */
    //仅拷贝父进程的 signal->rlim, oom_score_adj, oom_score_adj_min, has_child_subreaper  而不是内存.
	struct signal_struct *signal;
	struct sighand_struct *sighand; //仅拷贝父进程的 sighand->action, 而不是内存.
	sigset_t blocked, real_blocked;
	sigset_t saved_sigmask;	/* restored if set_restore_sigmask() was used */
	unsigned long sas_ss_sp;
	size_t sas_ss_size;
#ifdef CONFIG_AUDITSYSCALL
	kuid_t loginuid;
	unsigned int sessionid;
#endif
	struct seccomp seccomp;
/* Thread group tracking */
   	u32 parent_exec_id;
   	u32 self_exec_id;
/* Protection of (de-)allocation: mm, files, fs, tty, keyrings, mems_allowed,
 * mempolicy */
	struct wake_q_node wake_q;
#ifdef CONFIG_LOCKDEP
# define MAX_LOCK_DEPTH 48UL
	struct held_lock held_locks[MAX_LOCK_DEPTH];
	gfp_t lockdep_reclaim_gfp;
#endif
#ifdef CONFIG_UBSAN
	unsigned int in_ubsan;
#endif
/* journalling filesystem info */
	void *journal_info;
/* stacked block device info */
	struct bio_list *bio_list;
/* VM state */
	struct reclaim_state *reclaim_state;
	struct backing_dev_info *backing_dev_info;
	unsigned long ptrace_message;
	siginfo_t *last_siginfo; /* For ptrace use.  */
#ifdef CONFIG_CPUSETS
	nodemask_t mems_allowed;	/* Protected by alloc_lock */
#endif
#endif
#ifdef CONFIG_DEBUG_PREEMPT
	unsigned long preempt_disable_ip;
#endif
#ifdef CONFIG_NUMA
	short il_next;
	short pref_node_fork;
#endif
#ifdef CONFIG_NUMA_BALANCING
	int numa_scan_seq;
	unsigned int numa_scan_period_max;
	unsigned long numa_migrate_retry;
	struct list_head numa_entry;
	/*
	 * numa_faults is an array split into four regions:
	 * faults_memory, faults_cpu, faults_memory_buffer, faults_cpu_buffer
	 * in this precise order.
	 *
	 * faults_memory: Exponential decaying average of faults on a per-node
	 * basis. Scheduling placement decisions are made based on these
	 * counts. The values remain static for the duration of a PTE scan.
	 * faults_cpu: Track the nodes the process was running on when a NUMA
	 * hinting fault was incurred.
	 * faults_memory_buffer and faults_cpu_buffer: Record faults per node
	 * during the current scan window. When the scan completes, the counts
	 * in faults_memory and faults_cpu decay and these values are copied.
	 */
	unsigned long total_numa_faults;
	/*
	 * numa_faults_locality tracks if faults recorded during the last
	 * scan window were remote/local or failed to migrate. The task scan
	 * period is adapted based on the locality of the faults with different
	 * weights depending on whether they were shared or private faults
	 */
	unsigned long numa_faults_locality[3];
	unsigned long numa_pages_migrated;
#endif /* CONFIG_NUMA_BALANCING */
#ifdef CONFIG_ARCH_WANT_BATCHED_UNMAP_TLB_FLUSH
	struct tlbflush_unmap_batch tlb_ubc;
#endif
	struct rcu_head rcu;
	/*
	 * cache last used pipe for splice
	 */
	struct pipe_inode_info *splice_pipe;
	struct page_frag task_frag;
#ifdef CONFIG_FAULT_INJECTION
	int make_it_fail;
#endif
#ifdef CONFIG_LATENCYTOP
	int latency_record_count;
	struct latency_record latency_record[LT_SAVECOUNT];
#endif
	/*
	 * time slack values; these are used to round up poll() and
	 * select() etc timeout values. These are in nanoseconds.
	 */
	unsigned long timer_slack_ns;
	unsigned long default_timer_slack_ns; //父进程的 timer_slack_ns
#ifdef CONFIG_KASAN
	unsigned int kasan_depth;
#endif
#ifdef CONFIG_FUNCTION_GRAPH_TRACER
	/* Index of current stored address in ret_stack */
	int curr_ret_stack;
	/* Stack of return addresses for return function tracing */
	struct ftrace_ret_stack	*ret_stack;
	/* time stamp for last schedule */
	unsigned long long ftrace_timestamp;
	/*
	 * Number of functions that haven't been traced
	 * because of depth overrun.
	 */
	atomic_t trace_overrun;
	/* Pause for the tracing */
	atomic_t tracing_graph_pause;
#endif
#ifdef CONFIG_TRACING
	/* state flags for use by tracers */
	unsigned long trace;
	/* bitmask and counter of trace recursion */
	unsigned long trace_recursion;
#endif /* CONFIG_TRACING */
#ifdef CONFIG_MEMCG
	struct mem_cgroup *memcg_in_oom;
	gfp_t memcg_oom_gfp_mask;
	int memcg_oom_order;
	/* number of pages to reclaim on returning to userland */
	unsigned int memcg_nr_pages_over_high;
#endif
#ifdef CONFIG_UPROBES
	struct uprobe_task *utask;
#endif
#ifdef CONFIG_DEBUG_ATOMIC_SLEEP
	unsigned long	task_state_change;
#endif
/* CPU-specific state of this task */
	struct thread_struct thread;  //克隆父进程
/*
 * WARNING: on x86, 'thread_struct' contains a variable-sized
 * structure.  It *MUST* be at the end of 'task_struct'.
 *
 * Do not put anything below here!
 */
};
```
