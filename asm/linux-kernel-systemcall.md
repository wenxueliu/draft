##预备知识

* 内核态
* 用户态
* 为什么要划分系统级别?
* 如何区分内核和用户态? cs:eip
* 寄存器上下文
* 上下文切换
* 系统调用号
* 中断向量
* 调度时机


现代计算机机中都有几种不同的指令级别，在高执行级别下，代码可以执行特权指令，
访问任意的物理地址，这种CPU执行级别就对应着内核态，而在相应的低级别执行状态下，
代码的掌控范围会受到限制，只能在对应级别允许的范围内活动。举例：Intrel x86 CPU
有四种不同的执行级别0-3，Linux只使用了其中的0级和3级来分别表示内核态和用户态。
操作系统让系统本身更为稳定的方式，这样程序员自己写的用户态代码很难把整个系统都
给搞崩溃，内核的代码经过仔细的分析有专业的人员写的代码会更加健壮一些，整个程序
会更加稳定一些，注意：这里所说的地址空间是逻辑地址而不是物理地址。


用户态和内核态的很显著的区分就是：CS和EIP， CS寄存器的最低两位表明了当前代码的
特权级别；CPU每条指令的读取都是通过CS:EIP这两个寄存器：其中CS是代码段选择寄存器，
EIP是偏移量寄存器，上述判断由硬件完成。一般来说在Linux中，地址空间是一个显著的
标志：0xc0000000以上的地址空间只能在内核态下访问，0xc00000000-0xbfffffff的地址
空间在两种状态下都可以访问。

系统调用过程中一定发生中断, 在系统调用执行过程中可能有进程的切换.

##系统调用分类

###进程控制

    load
    execute
    end, abort
    create process (for example, fork on Unix-like systems, or NtCreateProcess in the Windows NT Native API)
    terminate process
    get/set process attributes
    wait for time, wait event, signal event
    allocate, free memory

###文件管理

    create file, delete file
    open, close
    read, write, reposition
    get/set file attributes

###设备管理

    request device, release device
    read, write, reposition
    get/set device attributes
    logically attach or detach devices

###信息管理

    get/set time or date
    get/set system data
    get/set process, file, or device attributes

###通信

    create, delete communication connection
    send, receive messages
    transfer status information
    attach or detach remote devices

##什么是 system-call

linux 系统[64 位系统调用表](https://github.com/torvalds/linux/blob/master/arch/x86/entry/syscalls/syscall_64.tbl)

[32 位系统调用表](https://github.com/torvalds/linux/blob/master/arch/x86/entry/syscalls/syscall_32.tbl)

上面的系统调用并不需要完全掌握, 可以慢慢来, 当需要记住的 64 位系统有 326 个系统调用.


##系统调用原理分析

1. int 0x80 中断与系统调用是在什么时候, 如何建立起关联的, 具体相关代码在哪里?

在内核初始化(start_kernel) 过程中通过中断向量建立关联, 在系统初始化已经建立了
中断 int 0x80 与系统调用的关联, 在后续, 一旦用户态出现 int 0x80 的指令, CPU 就
立即跳转到系统调用对应的地址.

2. 系统调用处理过程如何与具体的系统调用函数关联起来的, 代码在哪里, 整个系统调用具体做了哪些工作?

通过系统调用号关联起来, 在 arch/x86/entry/entry_64.S, 现场保存, 执行系统调用, 现场恢复.

3. 在系统调用过程中还会存在其他中断么?

会

4. 在系统调用过程中可能发生其他系统相关导致进程切换吗?

会, 如果发生调度或有一些信号需要处理, 具体参考 int_ret_from_sys_call_irqs_off 及 int_ret_from_sys_call
此外, 进程的切换也会导致进程上下文的切换

###系统调用入口

从内核初始化在 init/main.c 中的 start_kernel 函数. 其中一个初始化是 setup_arch,
对于 x86 来说, 实际调用的是 arch/x86/kernel/setup.c 中的 setup_arch 函数. 而
setup_arch 又调用了 early_trap_init 函数. 这部分与系统开启相关. 这里不详细讨论.


###初始化

syscall 的初始化 syscall_init 在 arch/x86/kernel/cpu/common.c 的 cpu_init 函数中.

```
linux/arch/x86/kernel/cpu/common.c

    void syscall_init(void)
    {
    	/*
    	 * LSTAR and STAR live in a bit strange symbiosis.
    	 * They both write to the same internal register. STAR allows to
    	 * set CS/DS but only a 32bit target. LSTAR sets the 64bit rip.
    	 */
    	wrmsr(MSR_STAR, 0, (__USER32_CS << 16) | __KERNEL_CS);
    	wrmsrl(MSR_LSTAR, (unsigned long)entry_SYSCALL_64);

    #ifdef CONFIG_IA32_EMULATION //允许 64 位系统运行 32 位程序
    	wrmsrl(MSR_CSTAR, (unsigned long)entry_SYSCALL_compat);
    	/*
    	 * This only works on Intel CPUs.
    	 * On AMD CPUs these MSRs are 32-bit, CPU truncates MSR_IA32_SYSENTER_EIP.
    	 * This does not cause SYSENTER to jump to the wrong location, because
    	 * AMD doesn't allow SYSENTER in long mode (either 32- or 64-bit).
    	 */
    	wrmsrl_safe(MSR_IA32_SYSENTER_CS, (u64)__KERNEL_CS);
    	wrmsrl_safe(MSR_IA32_SYSENTER_ESP, 0ULL);
    	wrmsrl_safe(MSR_IA32_SYSENTER_EIP, (u64)entry_SYSENTER_compat);
    #else //不允许 64 位系统运行 32 程序
    	wrmsrl(MSR_CSTAR, (unsigned long)ignore_sysret);
        //[GDT](https://en.wikipedia.org/wiki/Global_Descriptor_Table)
    	wrmsrl_safe(MSR_IA32_SYSENTER_CS, (u64)GDT_ENTRY_INVALID_SEG);
    	wrmsrl_safe(MSR_IA32_SYSENTER_ESP, 0ULL);
    	wrmsrl_safe(MSR_IA32_SYSENTER_EIP, 0ULL);
    #endif

    	/* Flags to clear on syscall */
    	wrmsrl(MSR_SYSCALL_MASK,
    	       X86_EFLAGS_TF|X86_EFLAGS_DF|X86_EFLAGS_IF|
    	       X86_EFLAGS_IOPL|X86_EFLAGS_AC|X86_EFLAGS_NT);
    }


linux/arch/x86/include/asm/segment.h

    #define __KERNEL_CS			(GDT_ENTRY_KERNEL_CS*8)
    #define __USER32_CS			(GDT_ENTRY_DEFAULT_USER32_CS*8 + 3)

linux/arch/x86/include/uapi/asm/processor-flags.h

    #define X86_EFLAGS_TF		_BITUL(X86_EFLAGS_TF_BIT)
    #define X86_EFLAGS_DF		_BITUL(X86_EFLAGS_DF_BIT)
    #define X86_EFLAGS_IF		_BITUL(X86_EFLAGS_IF_BIT)
    #define X86_EFLAGS_AC		_BITUL(X86_EFLAGS_AC_BIT)
    #define X86_EFLAGS_IOPL		(_AC(3,UL) << X86_EFLAGS_IOPL_BIT)

linux/arch/x86/kernel/cpu/msr.h


    static inline void native_write_msr(unsigned int msr,
    				    unsigned low, unsigned high)
    {
        //Write the value in EDX:EAX to MSR specified by ECX. MSR[ECX] = EDX:EAX;
    	asm volatile(""wrmsr"" : : ""c"" (msr), ""a""(low), ""d"" (high) : ""memory"");
    	if (msr_tracepoint_active(__tracepoint_read_msr))
    		do_trace_write_msr(msr, ((u64)high << 32 | low), 0);
    }

    /* Can be uninlined because referenced by paravirt */
    notrace static inline int native_write_msr_safe(unsigned int msr,
    					unsigned low, unsigned high)
    {
    	int err;
    	asm volatile(""2: wrmsr ; xor %[err],%[err]\n""
    		     ""1:\n\t""
    		     "".section .fixup,\"ax\"\n\t""
    		     ""3:  mov %[fault],%[err] ; jmp 1b\n\t""
    		     "".previous\n\t""
    		     _ASM_EXTABLE(2b, 3b)
    		     : [err] ""=a"" (err)
    		     : ""c"" (msr), ""0"" (low), ""d"" (high),
    		       [fault] ""i"" (-EIO)
    		     : ""memory"");
    	if (msr_tracepoint_active(__tracepoint_read_msr))
    		do_trace_write_msr(msr, ((u64)high << 32 | low), err);
    	return err;
    }

    static inline void wrmsr(unsigned msr, unsigned low, unsigned high)
    {
    	native_write_msr(msr, low, high);
    }

    static inline void wrmsrl(unsigned msr, u64 val)
    {
    	native_write_msr(msr, (u32)(val & 0xffffffffULL), (u32)(val >> 32));
    }

    /* wrmsr with exception handling */
    static inline int wrmsr_safe(unsigned msr, unsigned low, unsigned high)
    {
    	return native_write_msr_safe(msr, low, high);
    }

    #define wrmsrl_safe(msr, val) wrmsr_safe((msr), (u32)(val),		\
    					     (u32)((val) >> 32))

linux/arch/x86/entry/entry_64.S 1485 行

    ENTRY(ignore_sysret)
    	mov	$-ENOSYS, %eax
    	sysret
    END(ignore_sysret)

```

wrmsr(MSR_STAR, 0, (__USER32_CS << 16) | __KERNEL_CS);


    MSR_STAR contains 63:48 bits of the user code segment. These bits
    will be loaded to the CS and SS segment registers for the sysret
    instruction which provides functionality to return from a system
    call to user code with the related privilege. Also the MSR_STAR
    contains 47:32 bits from the kernel code that will be used as the
    base selector for CS and SS segment registers when user space
    applications execute a system call.

wrmsrl(MSR_LSTAR, (unsigned long)entry_SYSCALL_64);

    加载 entry_SYSCALL_64 到 MSR_LSTAR 中, 其中 entry_SYSCALL_64 的定义
    在[这里](http://code.woboq.org/linux/linux/arch/x86/entry/entry_64.S.html)

wrmsrl(MSR_CSTAR, (unsigned long)entry_SYSCALL_compat);

    加载 entry_SYSCALL_compat 到 MSR_LSTAR 中, 其中 entry_SYSCALL_64 的定义
    在[这里](http://code.woboq.org/linux/linux/arch/x86/entry/entry_64.S.html)

wrmsrl_safe(MSR_IA32_SYSENTER_CS, (u64)__KERNEL_CS);

    保存 __KERNEL_CS 到 MSR_IA32_SYSENTER_CS

wrmsrl_safe(MSR_IA32_SYSENTER_ESP, 0ULL);

    MSR_IA32_SYSENTER_ESP 清零

wrmsrl_safe(MSR_IA32_SYSENTER_EIP, (u64)entry_SYSENTER_compat);

    MSR_IA32_SYSENTER_EIP 指向 entry_SYSCALL_compat

wrmsrl(MSR_SYSCALL_MASK, X86_EFLAGS_TF|X86_EFLAGS_DF|X86_EFLAGS_IF| X86_EFLAGS_IOPL|X86_EFLAGS_AC|X86_EFLAGS_NT);

    标志位保存到 MSR_SYSCALL_MASK 之后, 被清零.


以上代码主要工作是将系统调用入口放入 MSR(model specific register)

###系统调用准备

在 Linux 内核处理系统调用中断之前, 在一个异常被处理之前, idtentry 宏执行准备工作;
在中断被处理之前, interrupt 宏执行准备工作; 在系统调用被处理之前, entry_SYSCALL_64
将做准备工作.

在控制器由用户态转到内核态后, 并不是立即就执行内核态系统调用表中的内核函数,
原因是在系统调用完成之后还要返回用户态, 因此在调用内核系统调用函数之前, 必须
做一些准备工作, 保持用户态的信息(堆栈, 寄存器)待系统调用完之后恢复现场.
初始化内核, 寄存器,堆栈 等等.


```
/*
 * 64-bit SYSCALL instruction entry. Up to 6 arguments in registers.
 *
 * 64-bit SYSCALL saves rip to rcx, clears rflags.RF, then saves rflags to r11,
 * then loads new ss, cs, and rip from previously programmed MSRs.
 * rflags gets masked by a value from another MSR (so CLD and CLAC
 * are not needed). SYSCALL does not save anything on the stack
 * and does not change rsp.
 *
 * Registers on entry:
 * rax  system call number
 * rcx  return address
 * r11  saved rflags (note: r11 is callee-clobbered register in C ABI)
 * rdi  arg0
 * rsi  arg1
 * rdx  arg2
 * r10  arg3 (needs to be moved to rcx to conform to C ABI)
 * r8   arg4
 * r9   arg5
 * (note: r12-r15, rbp, rbx are callee-preserved in C ABI)
 *
 * Only called from user space.
 *
 * When user can change pt_regs->foo always force IRET. That is because
 * it deals with uncanonical addresses better. SYSRET has trouble
 * with them due to bugs in both AMD and Intel CPUs.
 */

ENTRY(entry_SYSCALL_64)
	/*
	 * Interrupts are off on entry.
	 * We do not frame this tiny irq-off block with TRACE_IRQS_OFF/ON,
	 * it is too small to ever cause noticeable irq latency.
	 */
	SWAPGS_UNSAFE_STACK
	/*
	 * A hypervisor implementation might want to use a label
	 * after the swapgs, so that it can do the swapgs
	 * for the guest and jump here on syscall.
	 */
GLOBAL(entry_SYSCALL_64_after_swapgs)

    //将旧的 rsp 保存到 rsp_scratch
	movq	%rsp, PER_CPU_VAR(rsp_scratch)

    //rsp 指向 cpu_current_top_of_stack, 后续指令执行从 cpu_current_top_of_stack 地址开始
	movq	PER_CPU_VAR(cpu_current_top_of_stack), %rsp

	/* Construct struct pt_regs on stack */
    //将 $__USER_DS 压栈
	pushq	$__USER_DS			/* pt_regs->ss */

    //将 rsp_scratch 压栈, 实际为旧的 rsp
	pushq	PER_CPU_VAR(rsp_scratch)	/* pt_regs->sp */

	/*
	 * Re-enable interrupts.
	 * We use 'rsp_scratch' as a scratch space, hence irq-off block above
	 * must execute atomically in the face of possible interrupt-driven
	 * task preemption. We must enable interrupts only after we're done
	 * with using rsp_scratch:
	 */
    //重新开启中断
	ENABLE_INTERRUPTS(CLBR_NONE)

    //保存通用寄存器, -ENOSYS, flags, 主要原因是系统调用会用到.
    //rax - contains system call number;
    //rcx - contains return address to the user space;
    //r11 - contains register flags;
    //rdi - contains first argument of a system call handler;
    //rsi - contains second argument of a system call handler;
    //rdx - contains third argument of a system call handler;
    //r10 - contains fourth argument of a system call handler;
    //r8 - contains fifth argument of a system call handler;
    //r9 - contains sixth argument of a system call handler;
    //其他寄存器 rbp, rbx, r12~r15 在 C-ABI 作为 callee-preserved
    //其中 ENOSYS 是没有实现系统调用的错误代码
	pushq	%r11				/* pt_regs->flags */
	pushq	$__USER_CS			/* pt_regs->cs */
	pushq	%rcx				/* pt_regs->ip */
	pushq	%rax				/* pt_regs->orig_ax */
	pushq	%rdi				/* pt_regs->di */
	pushq	%rsi				/* pt_regs->si */
	pushq	%rdx				/* pt_regs->dx */
	pushq	%rcx				/* pt_regs->cx */
	pushq	$-ENOSYS			/* pt_regs->ax */
	pushq	%r8				    /* pt_regs->r8 */
	pushq	%r9				    /* pt_regs->r9 */
	pushq	%r10				/* pt_regs->r10 */
	pushq	%r11				/* pt_regs->r11 */
	sub	$(6*8), %rsp			/* pt_regs->bp, bx, r12-15 not saved */

    //测试是否进入系统跟踪
	testl	$_TIF_WORK_SYSCALL_ENTRY, ASM_THREAD_INFO(TI_flags, %rsp, SIZEOF_PTREGS)
	jnz	tracesys

entry_SYSCALL_64_fastpath:

#if __SYSCALL_MASK == ~0
    //__NR_syscall_max 为最大系统调用号
	cmpq	$__NR_syscall_max, %rax
#else
	andl	$__SYSCALL_MASK, %eax
	cmpl	$__NR_syscall_max, %eax
#endif
    //CF, ZF 标志是否清零, 如果是跳到 1:
	ja	1f				/* return -ENOSYS (already in pt_regs->ax) */

    //如果有正确的系统调用, 第四个参数赋值给给 rcx.
	movq	%r10, %rcx
    //调用系统调用表中的函数, 系统调用表见前面分析.
	call	*sys_call_table(, %rax, 8)

    //#define RAX		10*8
    //将 rax(系统调用返回结果)保存到 rsp
	movq	%rax, RAX(%rsp)

1:
/*
 * Syscall return path ending with SYSRET (fast path).
 * Has incompletely filled pt_regs.
 */
    //见后面附注
	LOCKDEP_SYS_EXIT
	/*
	 * We do not frame this tiny irq-off block with TRACE_IRQS_OFF/ON,
	 * it is too small to ever cause noticeable irq latency.
	 */
	DISABLE_INTERRUPTS(CLBR_NONE)
	/*
	 * We must check ti flags with interrupts (or at least preemption)
	 * off because we must *never* return to userspace without
	 * processing exit work that is enqueued if we're preempted here.
	 * In particular, returning to userspace with any of the one-shot
	 * flags (TIF_NOTIFY_RESUME, TIF_USER_RETURN_NOTIFY, etc) set is
	 * very bad.
	 */
	testl	$_TIF_ALLWORK_MASK, ASM_THREAD_INFO(TI_flags, %rsp, SIZEOF_PTREGS)

    //TODO
	jnz	int_ret_from_sys_call_irqs_off	/* Go to the slow path */

    //TODO
	RESTORE_C_REGS_EXCEPT_RCX_R11

    //不恢复 rcx, r11, rsp
	movq	RIP(%rsp), %rcx
	movq	EFLAGS(%rsp), %r11
	movq	RSP(%rsp), %rsp
	/*
	 * 64-bit SYSRET restores rip from rcx,
	 * rflags from r11 (but RF and VM bits are forced to 0),
	 * cs and ss are loaded from MSRs.
	 * Restoration of rflags re-enables interrupts.
	 *
	 * NB: On AMD CPUs with the X86_BUG_SYSRET_SS_ATTRS bug, the ss
	 * descriptor is not reinitialized.  This means that we should
	 * avoid SYSRET with SS == NULL, which could happen if we schedule,
	 * exit the kernel, and re-enter using an interrupt vector.  (All
	 * interrupt entries on x86_64 set SS to NULL.)  We prevent that
	 * from happening by reloading SS in __switch_to.  (Actually
	 * detecting the failure in 64-bit userspace is tricky but can be
	 * done.)
	 */
	USERGS_SYSRET64
GLOBAL(int_ret_from_sys_call_irqs_off)
	TRACE_IRQS_ON
	ENABLE_INTERRUPTS(CLBR_NONE)
	jmp int_ret_from_sys_call
	/* Do syscall entry tracing */
tracesys:
	movq	%rsp, %rdi
	movl	$AUDIT_ARCH_X86_64, %esi
	call	syscall_trace_enter_phase1
	test	%rax, %rax
	jnz	tracesys_phase2			/* if needed, run the slow path */
	RESTORE_C_REGS_EXCEPT_RAX		/* else restore clobbered regs */
	movq	ORIG_RAX(%rsp), %rax
	jmp	entry_SYSCALL_64_fastpath	/* and return to the fast path */
tracesys_phase2:
	SAVE_EXTRA_REGS
	movq	%rsp, %rdi
	movl	$AUDIT_ARCH_X86_64, %esi
	movq	%rax, %rdx
	call	syscall_trace_enter_phase2
	/*
	 * Reload registers from stack in case ptrace changed them.
	 * We don't reload %rax because syscall_trace_entry_phase2() returned
	 * the value it wants us to use in the table lookup.
	 */
	RESTORE_C_REGS_EXCEPT_RAX
	RESTORE_EXTRA_REGS
#if __SYSCALL_MASK == ~0
	cmpq	$__NR_syscall_max, %rax
#else
	andl	$__SYSCALL_MASK, %eax
	cmpl	$__NR_syscall_max, %eax
#endif
	ja	1f				/* return -ENOSYS (already in pt_regs->ax) */
	movq	%r10, %rcx			/* fixup for C */
	call	*sys_call_table(, %rax, 8)
	movq	%rax, RAX(%rsp)
1:
	/* Use IRET because user could have changed pt_regs->foo */
/*
 * Syscall return path ending with IRET.
 * Has correct iret frame.
 */
GLOBAL(int_ret_from_sys_call)
	SAVE_EXTRA_REGS
	movq	%rsp, %rdi
	call	syscall_return_slowpath	/* returns with IRQs disabled */
	RESTORE_EXTRA_REGS
	TRACE_IRQS_IRETQ		/* we're about to change IF */
	/*
	 * Try to use SYSRET instead of IRET if we're returning to
	 * a completely clean 64-bit userspace context.
	 */
	movq	RCX(%rsp), %rcx
	movq	RIP(%rsp), %r11
	cmpq	%rcx, %r11			/* RCX == RIP */
	jne	opportunistic_sysret_failed
	/*
	 * On Intel CPUs, SYSRET with non-canonical RCX/RIP will #GP
	 * in kernel space.  This essentially lets the user take over
	 * the kernel, since userspace controls RSP.
	 *
	 * If width of "canonical tail" ever becomes variable, this will need
	 * to be updated to remain correct on both old and new CPUs.
	 */
	.ifne __VIRTUAL_MASK_SHIFT - 47
	.error ""virtual address width changed -- SYSRET checks need update""
	.endif
	/* Change top 16 bits to be the sign-extension of 47th bit */
	shl	$(64 - (__VIRTUAL_MASK_SHIFT+1)), %rcx
	sar	$(64 - (__VIRTUAL_MASK_SHIFT+1)), %rcx
	/* If this changed %rcx, it was not canonical */
	cmpq	%rcx, %r11
	jne	opportunistic_sysret_failed
	cmpq	$__USER_CS, CS(%rsp)		/* CS must match SYSRET */
	jne	opportunistic_sysret_failed
	movq	R11(%rsp), %r11
	cmpq	%r11, EFLAGS(%rsp)		/* R11 == RFLAGS */
	jne	opportunistic_sysret_failed
	/*
	 * SYSRET can't restore RF.  SYSRET can restore TF, but unlike IRET,
	 * restoring TF results in a trap from userspace immediately after
	 * SYSRET.  This would cause an infinite loop whenever #DB happens
	 * with register state that satisfies the opportunistic SYSRET
	 * conditions.  For example, single-stepping this user code:
	 *
	 *           movq	$stuck_here, %rcx
	 *           pushfq
	 *           popq %r11
	 *   stuck_here:
	 *
	 * would never get past 'stuck_here'.
	 */
	testq	$(X86_EFLAGS_RF|X86_EFLAGS_TF), %r11
	jnz	opportunistic_sysret_failed
	/* nothing to check for RSP */
	cmpq	$__USER_DS, SS(%rsp)		/* SS must match SYSRET */
	jne	opportunistic_sysret_failed
	/*
	 * We win! This label is here just for ease of understanding
	 * perf profiles. Nothing jumps here.
	 */
syscall_return_via_sysret:
	/* rcx and r11 are already restored (see code above) */
	RESTORE_C_REGS_EXCEPT_RCX_R11
	movq	RSP(%rsp), %rsp
	USERGS_SYSRET64
opportunistic_sysret_failed:
	SWAPGS
	jmp	restore_c_regs_and_iret
END(entry_SYSCALL_64)


linux/arch/x86/include/asm/irqflags.h

    /*
     * Currently paravirt can't handle swapgs nicely when we
     * don't have a stack we can rely on (such as a user space
     * stack).  So we either find a way around these or just fault
     * and emulate if a guest tries to call swapgs directly.
     *
     * Either way, this is a good way to document that we don't
     * have a reliable stack. x86_64 only.
     */
    #define SWAPGS_UNSAFE_STACK	swapgs

   [swapgs](http://www.felixcloutier.com/x86/SWAPGS.html)

    SWAPGS exchanges the current GS base register value with the
    value contained in MSR address C0000102H (IA32_KERNEL_GS_BASE).
    The SWAPGS instruction is a privileged instruction intended
    for use by system soft-ware.

    When using SYSCALL to implement system calls, there is no kernel
    stack at the OS entry point. Neither is there a straightforward
    method to obtain a pointer to kernel structures from which the
    kernel stack pointer could be read. Thus, the kernel cannot
    save general purpose registers or reference memory.

    By design, SWAPGS does not require any general purpose registers
    or memory operands. No registers need to be saved before using
    the instruction. SWAPGS exchanges the CPL 0 data pointer from
    the IA32_KERNEL_GS_BASE MSR with the GS base register. The kernel
    can then use the GS prefix on normal memory references to access
    kernel data structures. Similarly, when the OS kernel is entered
    using an interrupt or exception (where the kernel stack is already
    set up), SWAPGS can be used to quickly get a pointer to the kernel
    data structures.

    The IA32_KERNEL_GS_BASE MSR itself is only accessible using
    RDMSR/WRMSR instructions. Those instructions are only accessible
    at privilege level 0. The WRMSR instruction ensures that the
    IA32_KERNEL_GS_BASE MSR contains a canonical address.

linux/arch/x86/include/asm/thread_info.h

    /* work to do in syscall_trace_enter() */
    #define _TIF_WORK_SYSCALL_ENTRY	\
    	(_TIF_SYSCALL_TRACE | _TIF_SYSCALL_EMU | _TIF_SYSCALL_AUDIT |	\
    	 _TIF_SECCOMP | _TIF_SINGLESTEP | _TIF_SYSCALL_TRACEPOINT |	\
    	 _TIF_NOHZ)

    /*
     * ASM operand which evaluates to a 'thread_info' address of
     * the current task, if it is known that "reg" is exactly "off"
     * bytes below the top of the stack currently.
     *
     * ( The kernel stack's size is known at build time, it is usually
     *   2 or 4 pages, and the bottom  of the kernel stack contains
     *   the thread_info structure. So to access the thread_info very
     *   quickly from assembly code we can calculate down from the
     *   top of the kernel stack to the bottom, using constant,
     *   build-time calculations only. )
     *
     * For example, to fetch the current thread_info->flags value into %eax
     * on x86-64 defconfig kernels, in syscall entry code where RSP is
     * currently at exactly SIZEOF_PTREGS bytes away from the top of the
     * stack:
     *
     *      mov ASM_THREAD_INFO(TI_flags, %rsp, SIZEOF_PTREGS), %eax
     *
     * will translate to:
     *
     *      8b 84 24 b8 c0 ff ff      mov    -0x3f48(%rsp), %eax
     *
     * which is below the current RSP by almost 16K.
     */
    #define ASM_THREAD_INFO(field, reg, off) ((field)+(off)-THREAD_SIZE)(reg)

linux/arch/x86/include/asm/thread_info.h

    #define TI_flags 8 /* offsetof(struct thread_info, flags)	# */

linux/arch/x86/entry/calling.h

    #define SIZEOF_PTREGS	21*8

linux/include/generated/asm-offsets.h

    #define __NR_syscall_max 545 /* sizeof(syscalls_64) - 1	# */

linux/arch/x86/include/asm/unistd.h

    # ifdef CONFIG_X86_X32_ABI
    #  define __SYSCALL_MASK (~(__X32_SYSCALL_BIT))
    # else
    #  define __SYSCALL_MASK (~0)
    # endif

    #define __X32_SYSCALL_BIT    0x40000000

linux/arch/x86/include/asm/irqflags.h

    #ifdef CONFIG_DEBUG_LOCK_ALLOC
        #    define LOCKDEP_SYS_EXIT		call lockdep_sys_exit_thunk
    #else
        #    define LOCKDEP_SYS_EXIT
    #endif

    #define USERGS_SYSRET64                \
        swapgs;                               \
        sysretq;
```

以上包含了系统调用整个生命周期的管理. 包括系统调用前的运行环境保存,
执行系统调用, 系统调用之后的恢复等等.


###系统调用表

当程序从用户态调用系统调用时, 这个指令导致一个异常, 由于异常都是在内核中处理的,
因此就会导致从用户态到内核态的转换, 系统调用权限也随之由用户态转换到内核态.

但转到内核态执行什么指令, 从哪开始呢?  从前面的分析可知, 实际的系统调用是
`call    *sys_call_table(, %rax, 8)`, 那么 sys_call_table 具体是什么, 保存在哪里,
有哪些内容? 这是本部分要解决的问题.

```
[linux/arch/x86/entry/syscall_64.c](http://code.woboq.org/linux/linux/arch/x86/entry/syscall_64.c.html)

    #define __SYSCALL_COMMON(nr, sym, compat) __SYSCALL_64(nr, sym, compat)

    #ifdef CONFIG_X86_X32_ABI
    # define __SYSCALL_X32(nr, sym, compat) __SYSCALL_64(nr, sym, compat)
    #else
    # define __SYSCALL_X32(nr, sym, compat) /* nothing */
    #endif

    #define __SYSCALL_64(nr, sym, compat) extern asmlinkage long sym(unsigned long, unsigned long, unsigned long, unsigned long, unsigned long, unsigned long) ;
    #include <asm/syscalls_64.h>
    #undef __SYSCALL_64

    #define __SYSCALL_64(nr, sym, compat) [nr] = sym,

    asmlinkage const sys_call_ptr_t sys_call_table[__NR_syscall_max+1] = {
    	/*
    	 * Smells like a compiler bug -- it doesn't work
    	 * when the & below is removed.
    	 */
    	[0 ... __NR_syscall_max] = &sys_ni_syscall,
    #include <asm/syscalls_64.h>
    };


[linux/include/generated/asm-offsets.h]

    #define __NR_syscall_max 545 /* sizeof(syscalls_64) - 1	# */
    #define NR_syscalls 546 /* sizeof(syscalls_64)	# */

    linux/arch/x86/include/asm/syscall.h
    typedef asmlinkage long (*sys_call_ptr_t)(unsigned long, unsigned long,
    					  unsigned long, unsigned long,
    unsigned long, unsigned long);


[linux/kernel/sys_ni.c](http://code.woboq.org/linux/linux/kernel/sys_ni.c.html#sys_ni_syscall)

    /*  we can't #include <linux/syscalls.h> here,
        but tell gcc to not warn with -Wmissing-prototypes  */
    asmlinkage long sys_ni_syscall(void);
    /*
     * Non-implemented system calls get redirected here.
     */
    asmlinkage long sys_ni_syscall(void)
    {
    	return -ENOSYS;
    }
```

其中 [0 ... __NR_syscall_max] = &sys_ni_syscall 是
[gcc 扩展](https://gcc.gnu.org/onlinedocs/gcc/Designated-Inits.html).

sys_ni_syscall 只是初始化 sys_call_table, 真正的初始化由
[脚本](https://github.com/torvalds/linux/blob/master/arch/x86/entry/syscalls/syscalltbl.sh)
以[文件](https://github.com/torvalds/linux/blob/master/arch/x86/entry/syscalls/syscall_64.tbl)
为输入, 输出头文件[asm/syscalls_64.h](http://code.woboq.org/linux/linux/arch/x86/include/generated/asm/syscalls_64.h.html)

最后, sys_call_table 变成了这样:

```
asmlinkage const sys_call_ptr_t sys_call_table[__NR_syscall_max+1] = {
    [0 ... __NR_syscall_max] = &sys_ni_syscall,
    [0] = sys_read,
    [1] = sys_write,
    [2] = sys_open,
    ...
    ...
    ...
};
```

NOTE: 如何找到一个系统调用的具体实现代码?

实际内核中并没有 sys 开头的系统调用实现函数,
而是以 SYSCALL_DEFINEx 开头的函数实现. 其中
x 是该系统调用的参数个数. 如 write 系统调用
有三个参数, 实际函数为 SYSCALL_DEFINE3(write
这样的函数.

###一个系统调用实现的分析


系统调用从 syscall_init 开始, 之后定位系统调用到 entry_SYSCALL_64,
entry_SYSCALL_64 包括了保存现场, 执行系统调用, 恢复现场的工作.
而实际系统调用是通过定位 sys_call_table 中的元素完成的. 至此, 系统
调用整个流程已经走完, 那么就以一个具体的系统调用为例. 解释 wirte
系统调用做了哪些工作.

```
https://github.com/torvalds/linux/blob/master/fs/read_write.c

SYSCALL_DEFINE3(read, unsigned int, fd, char __user *, buf, size_t, count)
{
	struct fd f = fdget_pos(fd);
	ssize_t ret = -EBADF;

	if (f.file) {
		loff_t pos = file_pos_read(f.file);
		ret = vfs_read(f.file, buf, count, &pos);
		if (ret >= 0)
			file_pos_write(f.file, pos);
		fdput_pos(f);
	}
	return ret;
}

SYSCALL_DEFINE3(write, unsigned int, fd, const char __user *, buf,
		size_t, count)
{
	struct fd f = fdget_pos(fd);
	ssize_t ret = -EBADF;

	if (f.file) {
		loff_t pos = file_pos_read(f.file);
		ret = vfs_write(f.file, buf, count, &pos);
		if (ret >= 0)
			file_pos_write(f.file, pos);
		fdput_pos(f);
	}

	return ret;
}

```

```
http://code.woboq.org/linux/linux/include/linux/syscalls.h.html

/*
 * __MAP - apply a macro to syscall arguments
 * __MAP(n, m, t1, a1, t2, a2, ..., tn, an) will expand to
 *    m(t1, a1), m(t2, a2), ..., m(tn, an)
 * The first argument must be equal to the amount of type/name
 * pairs given.  Note that this list of pairs (i.e. the arguments
 * of __MAP starting at the third one) is in the same format as
 * for SYSCALL_DEFINE<n>/COMPAT_SYSCALL_DEFINE<n>
 */
#define __MAP0(m,...)
#define __MAP1(m,t,a) m(t,a)
#define __MAP2(m,t,a,...) m(t,a), __MAP1(m,__VA_ARGS__)
#define __MAP3(m,t,a,...) m(t,a), __MAP2(m,__VA_ARGS__)
#define __MAP4(m,t,a,...) m(t,a), __MAP3(m,__VA_ARGS__)
#define __MAP5(m,t,a,...) m(t,a), __MAP4(m,__VA_ARGS__)
#define __MAP6(m,t,a,...) m(t,a), __MAP5(m,__VA_ARGS__)
#define __MAP(n,...) __MAP##n(__VA_ARGS__)

#define __SC_DECL(t, a)	t a
#define __TYPE_IS_L(t)	(__same_type((t)0, 0L))
#define __TYPE_IS_UL(t)	(__same_type((t)0, 0UL))
#define __TYPE_IS_LL(t) (__same_type((t)0, 0LL) || __same_type((t)0, 0ULL))
#define __SC_LONG(t, a) __typeof(__builtin_choose_expr(__TYPE_IS_LL(t), 0LL, 0L)) a
#define __SC_CAST(t, a)	(t) a
#define __SC_ARGS(t, a)	a
#define __SC_TEST(t, a) (void)BUILD_BUG_ON_ZERO(!__TYPE_IS_LL(t) && sizeof(t) > sizeof(long))

#define SYSCALL_DEFINE1(name, ...) SYSCALL_DEFINEx(1, _##name, __VA_ARGS__)
#define SYSCALL_DEFINE2(name, ...) SYSCALL_DEFINEx(2, _##name, __VA_ARGS__)
#define SYSCALL_DEFINE3(name, ...) SYSCALL_DEFINEx(3, _##name, __VA_ARGS__)
#define SYSCALL_DEFINE4(name, ...) SYSCALL_DEFINEx(4, _##name, __VA_ARGS__)
#define SYSCALL_DEFINE5(name, ...) SYSCALL_DEFINEx(5, _##name, __VA_ARGS__)
#define SYSCALL_DEFINE6(name, ...) SYSCALL_DEFINEx(6, _##name, __VA_ARGS__)
#define SYSCALL_DEFINEx(x, sname, ...)				\
	SYSCALL_METADATA(sname, x, __VA_ARGS__)			\
	__SYSCALL_DEFINEx(x, sname, __VA_ARGS__)
#define __PROTECT(...) asmlinkage_protect(__VA_ARGS__)
#define __SYSCALL_DEFINEx(x, name, ...)					\
	asmlinkage long sys##name(__MAP(x,__SC_DECL,__VA_ARGS__))	\
		__attribute__((alias(__stringify(SyS##name))));		\
	static inline long SYSC##name(__MAP(x,__SC_DECL,__VA_ARGS__));	\
	asmlinkage long SyS##name(__MAP(x,__SC_LONG,__VA_ARGS__));	\
	asmlinkage long SyS##name(__MAP(x,__SC_LONG,__VA_ARGS__))	\
	{								\
		long ret = SYSC##name(__MAP(x,__SC_CAST,__VA_ARGS__));	\
		__MAP(x,__SC_TEST,__VA_ARGS__);				\
		__PROTECT(x, ret,__MAP(x,__SC_ARGS,__VA_ARGS__));	\
		return ret;						\
	}								\
	static inline long SYSC##name(__MAP(x,__SC_DECL,__VA_ARGS__))

#ifdef CONFIG_FTRACE_SYSCALLS //跟踪系统调用
#define SYSCALL_METADATA(sname, nb, ...)			\
	static const char *types_##sname[] = {			\
		__MAP(nb,__SC_STR_TDECL,__VA_ARGS__)		\
	};							\
	static const char *args_##sname[] = {			\
		__MAP(nb,__SC_STR_ADECL,__VA_ARGS__)		\
	};							\
	SYSCALL_TRACE_ENTER_EVENT(sname);			\
	SYSCALL_TRACE_EXIT_EVENT(sname);			\
	static struct syscall_metadata __used			\
	  __syscall_meta_##sname = {				\
		.name 		= "sys"#sname,			\
		.syscall_nr	= -1,	/* Filled in at boot */	\
		.nb_args 	= nb,				\
		.types		= nb ? types_##sname : NULL,	\
		.args		= nb ? args_##sname : NULL,	\
		.enter_event	= &event_enter_##sname,		\
		.exit_event	= &event_exit_##sname,		\
		.enter_fields	= LIST_HEAD_INIT(__syscall_meta_##sname.enter_fields), \
	};							\
	static struct syscall_metadata __used			\
	  __attribute__((section("__syscalls_metadata")))	\
	 *__p_syscall_meta_##sname = &__syscall_meta_##sname;
#else
#define SYSCALL_METADATA(sname, nb, ...)
#endif


http://code.woboq.org/linux/linux/include/linux/compiler.h.html

# define __user	__attribute__((noderef, address_space(1))) //主要供 sparse 工具使用
```

由于 SYSCALL_DEFINEx 调用了 SYSCALL_METADATA 和 __SYSCALL_DEFINEx

由于 SYSCALL_METADATA 是跟踪系统调用的, 因此我们注意关注 __SYSCALL_DEFINEx

对于 __MAP 宏变化过程

其中 __MAP(3,__SC_DECL, unsigned int, fd, const char __user *, buf, size_t, count) 翻译为

    unsigned int fd, const char __user * buf, size_t, count


其中 __MAP(3,__SC_LONG, unsigned int, fd, const char __user *, buf, size_t, count) 翻译为

    __typeof(__builtin_choose_expr(__TYPE_IS_LL(unsigned int), 0LL, 0L)) fd \
            __builtin_choose_expr(__TYPE_IS_LL(const char __user *), 0LL, 0L)) buf \
            __builtin_choose_expr(__TYPE_IS_LL(size_t), 0LL, 0L)) count

因此, wirte 系统调用编译之后变为:

```
	asmlinkage long sys_write(unsigned int fd, const char __user * buf, size_t, count)
		__attribute__((alias(__stringify(SyS_write))));
	static inline long SYSC_write(unsigned int fd, const char __user * buf, size_t, count);

    //SyS_write 函数定义
	asmlinkage long SyS_write(
            __typeof(__builtin_choose_expr((__same_type((unsigned int)0, 0LL)
                        || __same_type((unsigned int)0, 0ULL)),
                0LL, 0L))
            fd,

            __typeof(__builtin_choose_expr((__same_type((const char __user *)0, 0LL)
                        || __same_type((const char __user *)0, 0ULL)),
                0LL, 0L))
            buf,

            __typeof(__builtin_choose_expr((__same_type((size_t)0, 0LL)
                        || __same_type((size_t)0, 0ULL)),
                0LL, 0L))
            count
    );

    //SyS_write 函数定义
	asmlinkage long SyS_write(
            __typeof(__builtin_choose_expr((__same_type((unsigned int)0, 0LL)
                        || __same_type((unsigned int)0, 0ULL)),
                0LL, 0L))
            fd,

            __typeof(__builtin_choose_expr((__same_type((const char __user *)0, 0LL)
                        || __same_type((const char __user *)0, 0ULL)),
                0LL, 0L))
            buf,

            __typeof(__builtin_choose_expr((__same_type((size_t)0, 0LL)
                        || __same_type((size_t)0, 0ULL)),
                0LL, 0L))
            count
    )
	{
		long ret = SYSC_write(
                (unsigned int) fd,
                (const char __user *) buf,
                (size_t) count
        );

        (void)BUILD_BUG_ON_ZERO(
                !(__same_type((unsigned int)0, 0LL) || __same_type((unsigned int)0, 0ULL))
                && sizeof(unsigned int) > sizeof(long)),

        (void)BUILD_BUG_ON_ZERO(
                !__same_type((const char __user *)0, 0LL) || __same_type((const char __user *)0, 0ULL))
                && sizeof(const char __user *) > sizeof(long)),

        (void)BUILD_BUG_ON_ZERO(
                !__same_type((size_t)0, 0LL) || __same_type((size_t)0, 0ULL))
                && sizeof(size_t) > sizeof(long)),

        asmlinkage_protect(3, ret, fd, buf, count)
		return ret;
	}
	static inline long SYSC_write(unsigned int fd, const char __user * buf, size_t, count)
    //之前是函数头的解析后的结果, 下面是函数体
    {
        /*
         * struct files_struct files;
         * v = (unsigned long) files ->fdt->fd[fd]
         * struct fd f = (struct fd){(struct file *)v &~3, v&3 }
         *
         * struct fd {
         *      struct file *file;
         *      unsigned int flags;
         * };
         */

        struct fd f = fdget_pos(fd);
        ssize_t ret = -EBADF;

        if (f.file) {
            //获取当前文件的位置 : pos = file->f_pos;
            loff_t pos = file_pos_read(f.file);

            //将 buf 内容 count 个 byte 从 pos 开始写入 f.file. 详细待后续文件系统部分分析.
            ret = vfs_write(f.file, buf, count, &pos);

            //如果写入文件字节数大于等于 0
            if (ret >= 0)
                //更改当前文件的 pos:  file->f_pos = pos;
                file_pos_write(f.file, pos);
            //解锁, 实际调用 fput, 待后续文件系统部分分析.
            fdput_pos(f);
        }

        return ret;
    }
```

至此, write 系统调用分析完成, 细节见注释.

当然你也可以根据自己的偏好分析其中一个系统调用的具体实现, 相信付出是高回报的.

##系统调用的例子

注: 当一个函数多余 6 个参数, 其余参数将被放在栈

``` test.c

#include <stdio.h>
#include <string.h>
#include <fcntl.h>

int main(int argc, char **argv)
{

    const char *str = "hello systemcall";
    size_t len = strlen(str) + 1;
    ssize_t ret = 1;

    int fd = open("tmp1", O_WRONLY | O_CREAT | O_APPEND);

    printf("write %d return %lu\n", fd, ret);
    //write(fd, str, len);
    asm volatile (
        "mov  %1,%%edi\n\t"  //fd 传递给第一个参数
        "movq %2,%%rsi\n\t"  //str 地址传递给第二个参数
        "movq %3,%%rdx\n\t"  //len 传递给第三个参数
        "movq $1,%%rax\n\t"  //系统调用号 1
        "syscall\n\t"
        "movq %%rax, %0\n\t" //将write 返回结果给 ret
        :"=p"(ret)
        :"b"(fd), "p"(str), "d"(len)
        );
    printf("write return %lu\n", ret);
    return 0;
}
```
$ gcc -o test test.c

$ ./test

    write 3 return 4195536
    write return 17

$ ltrace ./test

    __libc_start_main(0x4005bd, 1, 0x7fff40ba1148, 0x400650 <unfinished ...>
    strlen("hello systemcall")                                                             = 16
    open("tmp", 1024, 04200000)                                                            = 3
    +++ exited (status 0) +++

$ ltrace ./test

    ...
    __libc_start_main(0x4005bd, 1, 0x7fff15fa4358, 0x400650 <unfinished ...>
    strlen("hello systemcall")                                                             = 16
    open("tmp", 1024, 04200000 <unfinished ...>
    SYS_open("tmp", 1024, 04200000)                                                        = 3
    <... open resumed> )                                                                   = 3
    SYS_write(3, "hello systemcall", 17 <no return ...>
    +++ exited (status 0) +++

$ strace ./test

    open("tmp1", O_WRONLY|O_CREAT|O_APPEND, 0200000020400000) = 3
    fstat(1, {st_mode=S_IFCHR|0620, st_rdev=makedev(136, 10), ...}) = 0
    mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0x7f34c0174000
    write(1, "write 3 return 4195536\n", 23write 3 return 4195536
    ) = 23
    write(3, "hello systemcall\n", 17)      = 17
    write(1, "write return 17\n", 16write return 17
    )       = 16
    exit_group(0)                           = ?
    +++ exited with 0 +++

##如何查看一个进程的系统调用

strace 是查看系统调用的利器, 既可以查看正在调用的进程的系统调用, 也可以看正在运行的程序
正在执行的系统调用.

$ ltrace -S param    //查看即将执行的程序 param 涉及的系统调用
$ ltrace -p -S param    //查看即将执行的程序 param 涉及的系统调用
$ strace param    //查看即将执行的程序 param 涉及的系统调用
$ strace -p PID   //查看进程号 PID 正在执行的系统调用

更多参考 man strace man lstrace

###proc 文件系统

系统调用在系统中无处不在, 我们知道在 /proc 文件系统保持了进程信息.

比如 /proc/1 代表进程号 1 的进程信息.

$ cat /proc/1/comm
init

$ sudo cat /proc/1/syscall
23 0x1d 0x7fff4930fa40 0x7fff4930fac0 0x7fff4930fb40 0x0 0x7fbeb3e03420 0x7fff4930f7e8 0x7fbeb2093d83

其中 23 就是系统调用号. 想知道其他进程正在执行的系统调用, 是不是很容易了:)


###调试系统调用

$sudo qemu-system-x86_64 -kernel linux-3.18.6/arch/x86/boot/bzImage -initrd rootfs.img -s -S

$ gdb
(gdb) file linux-3.18.6/vmlinux
(gdb) target remote:1234
(gdb) set arch i386:x86-64:intel
(gdb) b sys_time
(gdb) c
(gdb) layout asm
(gdb) stepi   //单步汇编指令
(gdb) stepi 2 //两步汇编指令
(gdb) nexti   //execute next instruction, stepping over function calls



###系统调用的意义

操作系统为用户态进程与硬件设备进行交互提供了一组接口——系统调用

* 把用户从底层的硬件编程中解放出来
* 极大的提高了系统的安全性
* 使用户程序具有可移植性

##API 与系统调用的关系

应用编程接口 (application program interface, API) 和系统调用是不同的

* API只是一个函数定义
* 系统调用通过软中断向内核发出一个明确的请求

Libc库定义的一些API引用了封装例程(wrapper routine,唯一目的就是发布系统调用)

* 一般每个系统调用对应一个封装例程
* 库再用这些封装例程定义出给用户的API

不是每个API都对应一个特定的系统调用

* API可能直接提供用户态的服务 如,一些数学函数
* 一个单独的API可能调用几个系统调用
* 不同的API可能调用了同一个系统调用

返回值

* 大部分封装例程返回一个整数,其值的含义依赖于相应的系统调用
* -1在多数情况下表示内核不能满足进程的请求
* Libc中定义的errno变量包含特定的出错码

此外, 系统调用必须尽量快, 因此必须尽量小, 而标准库负责参数校验等工作.

##遗留问题

1.用户代码是如何进入 syscall_init 的? 当然是触发中断, 需要对中断进一步理解

2.系统调用中发生调度, 对调度的影响, 如调度策略, 时机等等?

3.超过6个怎么办？做一个把某个寄存器作为指针，指向一块内存，这样进入内核态
之后可以访问所有内存空间，这就是系统调用的参数传递方式。以具体的实例说明

##总结

当用户态进程调用一个系统调用时,CPU切换到内核态并开始执行一个内核函数。
在Linux中是通过执行int $0x80来执行系统调用的, 这条汇编指令产生向量为
128的编程异常

整个系统调用过程如下:

1. 用户应用程序填充系统调用的寄存器
2. 进程从用户态切换到内核态, 并执行系统调用 entry_SYSCALL_64
3. entry_SYSCALL_64 切换到内核栈, 保存现场(通用寄存器, 旧的栈. flags)
4. entry_SYSCALL_64 调用 sys_call_table 中的函数, 如果正确调用对应的函数, 如果错误退出.
5. 系统调用完成, 恢复现场(通用寄存器, 旧的栈. flags).

##参考

https://0xax.gitbooks.io/linux-insides/content/SysCall/syscall-1.html
https://en.wikipedia.org/wiki/System_call
[Intel 指令参考](http://x86.renejeschke.de/)
[GDT](https://en.wikipedia.org/wiki/Global_Descriptor_Table)

##附录

###系统调用表

    0	common	read			sys_read
    1	common	write			sys_write
    2	common	open			sys_open
    3	common	close			sys_close
    4	common	stat			sys_newstat
    5	common	fstat			sys_newfstat
    6	common	lstat			sys_newlstat
    7	common	poll			sys_poll
    8	common	lseek			sys_lseek
    9	common	mmap			sys_mmap
    10	common	mprotect		sys_mprotect
    11	common	munmap			sys_munmap
    12	common	brk			    sys_brk
    13	64	    rt_sigaction	sys_rt_sigaction
    14	common	rt_sigprocmask	sys_rt_sigprocmask
    15	64	    rt_sigreturn	sys_rt_sigreturn/ptregs
    16	64	    ioctl			sys_ioctl
    17	common	pread64			sys_pread64
    18	common	pwrite64		sys_pwrite64
    19	64	    readv			sys_readv
    20	64	    writev			sys_writev
    21	common	access			sys_access
    22	common	pipe			sys_pipe
    23	common	select			sys_select
    24	common	sched_yield		sys_sched_yield
    25	common	mremap			sys_mremap
    26	common	msync			sys_msync
    27	common	mincore			sys_mincore
    28	common	madvise			sys_madvise
    29	common	shmget			sys_shmget
    30	common	shmat			sys_shmat
    31	common	shmctl			sys_shmctl
    32	common	dup			    sys_dup
    33	common	dup2			sys_dup2
    34	common	pause			sys_pause
    35	common	nanosleep		sys_nanosleep
    36	common	getitimer		sys_getitimer
    37	common	alarm			sys_alarm
    38	common	setitimer		sys_setitimer
    39	common	getpid			sys_getpid
    40	common	sendfile		sys_sendfile64
    41	common	socket			sys_socket
    42	common	connect			sys_connect
    43	common	accept			sys_accept
    44	common	sendto			sys_sendto
    45	64	    recvfrom		sys_recvfrom
    46	64	    sendmsg			sys_sendmsg
    47	64	    recvmsg			sys_recvmsg
    48	common	shutdown		sys_shutdown
    49	common	bind			sys_bind
    50	common	listen			sys_listen
    51	common	getsockname		sys_getsockname
    52	common	getpeername		sys_getpeername
    53	common	socketpair		sys_socketpair
    54	64	    setsockopt		sys_setsockopt
    55	64	    getsockopt		sys_getsockopt
    56	common	clone			sys_clone/ptregs
    57	common	fork			sys_fork/ptregs
    58	common	vfork			sys_vfork/ptregs
    59	64	    execve			sys_execve/ptregs
    60	common	exit			sys_exit
    61	common	wait4			sys_wait4
    62	common	kill			sys_kill
    63	common	uname			sys_newuname
    64	common	semget			sys_semget
    65	common	semop			sys_semop
    66	common	semctl			sys_semctl
    67	common	shmdt			sys_shmdt
    68	common	msgget			sys_msgget
    69	common	msgsnd			sys_msgsnd
    70	common	msgrcv			sys_msgrcv
    71	common	msgctl			sys_msgctl
    72	common	fcntl			sys_fcntl
    73	common	flock			sys_flock
    74	common	fsync			sys_fsync
    75	common	fdatasync		sys_fdatasync
    76	common	truncate		sys_truncate
    77	common	ftruncate		sys_ftruncate
    78	common	getdents		sys_getdents
    79	common	getcwd			sys_getcwd
    80	common	chdir			sys_chdir
    81	common	fchdir			sys_fchdir
    82	common	rename			sys_rename
    83	common	mkdir			sys_mkdir
    84	common	rmdir			sys_rmdir
    85	common	creat			sys_creat
    86	common	link			sys_link
    87	common	unlink			sys_unlink
    88	common	symlink			sys_symlink
    89	common	readlink		sys_readlink
    90	common	chmod			sys_chmod
    91	common	fchmod			sys_fchmod
    92	common	chown			sys_chown
    93	common	fchown			sys_fchown
    94	common	lchown			sys_lchown
    95	common	umask			sys_umask
    96	common	gettimeofday		sys_gettimeofday
    97	common	getrlimit		sys_getrlimit
    98	common	getrusage		sys_getrusage
    99	common	sysinfo			sys_sysinfo
    100	common	times			sys_times
    101	64	    ptrace			sys_ptrace
    102	common	getuid			sys_getuid
    103	common	syslog			sys_syslog
    104	common	getgid			sys_getgid
    105	common	setuid			sys_setuid
    106	common	setgid			sys_setgid
    107	common	geteuid			sys_geteuid
    108	common	getegid			sys_getegid
    109	common	setpgid			sys_setpgid
    110	common	getppid			sys_getppid
    111	common	getpgrp			sys_getpgrp
    112	common	setsid			sys_setsid
    113	common	setreuid		sys_setreuid
    114	common	setregid		sys_setregid
    115	common	getgroups		sys_getgroups
    116	common	setgroups		sys_setgroups
    117	common	setresuid		sys_setresuid
    118	common	getresuid		sys_getresuid
    119	common	setresgid		sys_setresgid
    120	common	getresgid		sys_getresgid
    121	common	getpgid			sys_getpgid
    122	common	setfsuid		sys_setfsuid
    123	common	setfsgid		sys_setfsgid
    124	common	getsid			sys_getsid
    125	common	capget			sys_capget
    126	common	capset			sys_capset
    127	64	    rt_sigpending		sys_rt_sigpending
    128	64	    rt_sigtimedwait		sys_rt_sigtimedwait
    129	64	    rt_sigqueueinfo		sys_rt_sigqueueinfo
    130	common	rt_sigsuspend		sys_rt_sigsuspend
    131	64	    sigaltstack		sys_sigaltstack
    132	common	utime			sys_utime
    133	common	mknod			sys_mknod
    134	64	    uselib
    135	common	personality		sys_personality
    136	common	ustat			sys_ustat
    137	common	statfs			sys_statfs
    138	common	fstatfs			sys_fstatfs
    139	common	sysfs			sys_sysfs
    140	common	getpriority		sys_getpriority
    141	common	setpriority		sys_setpriority
    142	common	sched_setparam		sys_sched_setparam
    143	common	sched_getparam		sys_sched_getparam
    144	common	sched_setscheduler	sys_sched_setscheduler
    145	common	sched_getscheduler	sys_sched_getscheduler
    146	common	sched_get_priority_max	sys_sched_get_priority_max
    147	common	sched_get_priority_min	sys_sched_get_priority_min
    148	common	sched_rr_get_interval	sys_sched_rr_get_interval
    149	common	mlock			sys_mlock
    150	common	munlock			sys_munlock
    151	common	mlockall		sys_mlockall
    152	common	munlockall		sys_munlockall
    153	common	vhangup			sys_vhangup
    154	common	modify_ldt		sys_modify_ldt
    155	common	pivot_root		sys_pivot_root
    156	64	    _sysctl			sys_sysctl
    157	common	prctl			sys_prctl
    158	common	arch_prctl		sys_arch_prctl
    159	common	adjtimex		sys_adjtimex
    160	common	setrlimit		sys_setrlimit
    161	common	chroot			sys_chroot
    162	common	sync			sys_sync
    163	common	acct			sys_acct
    164	common	settimeofday		sys_settimeofday
    165	common	mount			sys_mount
    166	common	umount2			sys_umount
    167	common	swapon			sys_swapon
    168	common	swapoff			sys_swapoff
    169	common	reboot			sys_reboot
    170	common	sethostname		sys_sethostname
    171	common	setdomainname		sys_setdomainname
    172	common	iopl			sys_iopl/ptregs
    173	common	ioperm			sys_ioperm
    174	64	    create_module
    175	common	init_module		sys_init_module
    176	common	delete_module		sys_delete_module
    177	64	    get_kernel_syms
    178	64	    query_module
    179	common	quotactl		sys_quotactl
    180	64	    nfsservctl
    181	common	getpmsg
    182	common	putpmsg
    183	common	afs_syscall
    184	common	tuxcall
    185	common	security
    186	common	gettid			sys_gettid
    187	common	readahead		sys_readahead
    188	common	setxattr		sys_setxattr
    189	common	lsetxattr		sys_lsetxattr
    190	common	fsetxattr		sys_fsetxattr
    191	common	getxattr		sys_getxattr
    192	common	lgetxattr		sys_lgetxattr
    193	common	fgetxattr		sys_fgetxattr
    194	common	listxattr		sys_listxattr
    195	common	llistxattr		sys_llistxattr
    196	common	flistxattr		sys_flistxattr
    197	common	removexattr		sys_removexattr
    198	common	lremovexattr	sys_lremovexattr
    199	common	fremovexattr	sys_fremovexattr
    200	common	tkill			sys_tkill
    201	common	time			sys_time
    202	common	futex			sys_futex
    203	common	sched_setaffinity	sys_sched_setaffinity
    204	common	sched_getaffinity	sys_sched_getaffinity
    205	64	    set_thread_area
    206	64	    io_setup		sys_io_setup
    207	common	io_destroy		sys_io_destroy
    208	common	io_getevents		sys_io_getevents
    209	64	    io_submit		sys_io_submit
    210	common	io_cancel		sys_io_cancel
    211	64	    get_thread_area
    212	common	lookup_dcookie		sys_lookup_dcookie
    213	common	epoll_create		sys_epoll_create
    214	64	    epoll_ctl_old
    215	64	    epoll_wait_old
    216	common	remap_file_pages	sys_remap_file_pages
    217	common	getdents64		sys_getdents64
    218	common	set_tid_address		sys_set_tid_address
    219	common	restart_syscall		sys_restart_syscall
    220	common	semtimedop		sys_semtimedop
    221	common	fadvise64		sys_fadvise64
    222	64	    timer_create		sys_timer_create
    223	common	timer_settime		sys_timer_settime
    224	common	timer_gettime		sys_timer_gettime
    225	common	timer_getoverrun	sys_timer_getoverrun
    226	common	timer_delete		sys_timer_delete
    227	common	clock_settime		sys_clock_settime
    228	common	clock_gettime		sys_clock_gettime
    229	common	clock_getres		sys_clock_getres
    230	common	clock_nanosleep		sys_clock_nanosleep
    231	common	exit_group		sys_exit_group
    232	common	epoll_wait		sys_epoll_wait
    233	common	epoll_ctl		sys_epoll_ctl
    234	common	tgkill			sys_tgkill
    235	common	utimes			sys_utimes
    236	64	    vserver
    237	common	mbind			sys_mbind
    238	common	set_mempolicy		sys_set_mempolicy
    239	common	get_mempolicy		sys_get_mempolicy
    240	common	mq_open			sys_mq_open
    241	common	mq_unlink		sys_mq_unlink
    242	common	mq_timedsend		sys_mq_timedsend
    243	common	mq_timedreceive		sys_mq_timedreceive
    244	64	    mq_notify		sys_mq_notify
    245	common	mq_getsetattr		sys_mq_getsetattr
    246	64	    kexec_load		sys_kexec_load
    247	64	    waitid			sys_waitid
    248	common	add_key			sys_add_key
    249	common	request_key		sys_request_key
    250	common	keyctl			sys_keyctl
    251	common	ioprio_set		sys_ioprio_set
    252	common	ioprio_get		sys_ioprio_get
    253	common	inotify_init		sys_inotify_init
    254	common	inotify_add_watch	sys_inotify_add_watch
    255	common	inotify_rm_watch	sys_inotify_rm_watch
    256	common	migrate_pages		sys_migrate_pages
    257	common	openat			sys_openat
    258	common	mkdirat			sys_mkdirat
    259	common	mknodat			sys_mknodat
    260	common	fchownat		sys_fchownat
    261	common	futimesat		sys_futimesat
    262	common	newfstatat		sys_newfstatat
    263	common	unlinkat		sys_unlinkat
    264	common	renameat		sys_renameat
    265	common	linkat			sys_linkat
    266	common	symlinkat		sys_symlinkat
    267	common	readlinkat		sys_readlinkat
    268	common	fchmodat		sys_fchmodat
    269	common	faccessat		sys_faccessat
    270	common	pselect6		sys_pselect6
    271	common	ppoll			sys_ppoll
    272	common	unshare			sys_unshare
    273	64	    set_robust_list		sys_set_robust_list
    274	64	    get_robust_list		sys_get_robust_list
    275	common	splice			sys_splice
    276	common	tee			sys_tee
    277	common	sync_file_range		sys_sync_file_range
    278	64	    vmsplice		sys_vmsplice
    279	64	    move_pages		sys_move_pages
    280	common	utimensat		sys_utimensat
    281	common	epoll_pwait		sys_epoll_pwait
    282	common	signalfd		sys_signalfd
    283	common	timerfd_create		sys_timerfd_create
    284	common	eventfd			sys_eventfd
    285	common	fallocate		sys_fallocate
    286	common	timerfd_settime		sys_timerfd_settime
    287	common	timerfd_gettime		sys_timerfd_gettime
    288	common	accept4			sys_accept4
    289	common	signalfd4		sys_signalfd4
    290	common	eventfd2		sys_eventfd2
    291	common	epoll_create1		sys_epoll_create1
    292	common	dup3			sys_dup3
    293	common	pipe2			sys_pipe2
    294	common	inotify_init1		sys_inotify_init1
    295	64	    preadv			sys_preadv
    296	64	    pwritev			sys_pwritev
    297	64	    rt_tgsigqueueinfo	sys_rt_tgsigqueueinfo
    298	common	perf_event_open		sys_perf_event_open
    299	64	    recvmmsg		sys_recvmmsg
    300	common	fanotify_init		sys_fanotify_init
    301	common	fanotify_mark		sys_fanotify_mark
    302	common	prlimit64		sys_prlimit64
    303	common	name_to_handle_at	sys_name_to_handle_at
    304	common	open_by_handle_at	sys_open_by_handle_at
    305	common	clock_adjtime		sys_clock_adjtime
    306	common	syncfs			sys_syncfs
    307	64	    sendmmsg		sys_sendmmsg
    308	common	setns			sys_setns
    309	common	getcpu			sys_getcpu
    310	64	    process_vm_readv	sys_process_vm_readv
    311	64	    process_vm_writev	sys_process_vm_writev
    312	common	kcmp			sys_kcmp
    313	common	finit_module		sys_finit_module
    314	common	sched_setattr		sys_sched_setattr
    315	common	sched_getattr		sys_sched_getattr
    316	common	renameat2		sys_renameat2
    317	common	seccomp			sys_seccomp
    318	common	getrandom		sys_getrandom
    319	common	memfd_create		sys_memfd_create
    320	common	kexec_file_load		sys_kexec_file_load
    321	common	bpf			sys_bpf
    322	64	    execveat		sys_execveat/ptregs
    323	common	userfaultfd		sys_userfaultfd
    324	common	membarrier		sys_membarrier
    325	common	mlock2			sys_mlock2
    326	common	copy_file_range		sys_copy_file_range

    #
    # x32-specific system call numbers start at 512 to avoid cache impact
    # for native 64-bit operation.
    #
    512	x32	rt_sigaction		compat_sys_rt_sigaction
    513	x32	rt_sigreturn		sys32_x32_rt_sigreturn
    514	x32	ioctl			compat_sys_ioctl
    515	x32	readv			compat_sys_readv
    516	x32	writev			compat_sys_writev
    517	x32	recvfrom		compat_sys_recvfrom
    518	x32	sendmsg			compat_sys_sendmsg
    519	x32	recvmsg			compat_sys_recvmsg
    520	x32	execve			compat_sys_execve/ptregs
    521	x32	ptrace			compat_sys_ptrace
    522	x32	rt_sigpending		compat_sys_rt_sigpending
    523	x32	rt_sigtimedwait		compat_sys_rt_sigtimedwait
    524	x32	rt_sigqueueinfo		compat_sys_rt_sigqueueinfo
    525	x32	sigaltstack		compat_sys_sigaltstack
    526	x32	timer_create		compat_sys_timer_create
    527	x32	mq_notify		compat_sys_mq_notify
    528	x32	kexec_load		compat_sys_kexec_load
    529	x32	waitid			compat_sys_waitid
    530	x32	set_robust_list		compat_sys_set_robust_list
    531	x32	get_robust_list		compat_sys_get_robust_list
    532	x32	vmsplice		compat_sys_vmsplice
    533	x32	move_pages		compat_sys_move_pages
    534	x32	preadv			compat_sys_preadv64
    535	x32	pwritev			compat_sys_pwritev64
    536	x32	rt_tgsigqueueinfo	compat_sys_rt_tgsigqueueinfo
    537	x32	recvmmsg		compat_sys_recvmmsg
    538	x32	sendmmsg		compat_sys_sendmmsg
    539	x32	process_vm_readv	compat_sys_process_vm_readv
    540	x32	process_vm_writev	compat_sys_process_vm_writev
    541	x32	setsockopt		compat_sys_setsockopt
    542	x32	getsockopt		compat_sys_getsockopt
    543	x32	io_setup		compat_sys_io_setup
    544	x32	io_submit		compat_sys_io_submit
    545	x32	execveat		compat_sys_execveat/ptregs


