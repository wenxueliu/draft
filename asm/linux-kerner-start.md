
##前提

本文只讨论 x86 下的 Linux 系统.

##预备知识

[实模式 real mode](https://en.wikipedia.org/wiki/Real_mode): CPU
访问的是实际物理地址. 只有 20 位地址总线. 在 80286 之前采用该模式.

[保护模式 protected mode](https://en.wikipedia.org/wiki/Protected_mode) :
支持虚拟地址, 分页，安全多任务等等, 从 80286 开始出现该模式.

[reset vector](https://en.wikipedia.org/wiki/Reset_vector): CPU 开始运行
取的第一个地址. (该文档非常易懂, 建议读)

[BIOS]() 保存了启动顺序


##系统启动

当我们按下电脑的开关键, 母板发送一个信号给电源, 电源发现自己供电能力正常, 就会
发送一个[power good singal](https://en.wikipedia.org/wiki/Power_good_signal)给
母板, 母板收到该信号启动 CPU. CPU 从寄存器开始取址-执行的循环.

那么寄存器存储的第一个值(即 CS:IP 的值)是什么呢? , 在 x86 系统中该值为:

    IP          0xfff0
    CS selector 0xf000
    CS base     0xffff0000

因此, 地址值为 0xfffffff0, 这个地址被称为 [reset vector](https://en.wikipedia.org/wiki/Reset_vector)

这个地址包含一个 jump 指令, 指向 BIOS 的入口地址.

###BIOS

BIOS(位于 ROM 而不是 RAM) 启动, 1)初始化和检查硬件 2)根据配置的启动顺序从对应设备读取启动扇区(boot
sector). 在有 MBR 分区的硬盘, 启动扇区为第一扇区的前 446 byte. 该扇区的最后两
个字节是 0x55, 0xaa 通知 BIOS 该设备是可启动的.

BIOS 完全启动之后将控制器交给 bootloader

###Bootloader

Bootloader (如 grub2, syslinux)

Bootloader 保存在哪里?

BIOS 将控制权转交给启动扇区, 从 boot.img 开始执行, 之后跳转到 Grub2 的 core
image. 这个 core image 从 diskboot.img(位于第一个扇区之后, 第一分区之前)

将 core image 剩余部分(GRUB2 的核和处理文件系统的驱动)加载到内存, 加载完剩余
的 core image 之后, 开始执行 [grub_main](http://git.savannah.gnu.org/gitweb/?p=grub.git;a=blob;f=grub-core/kern/main.c)

grub_main 初始化 console, 获取模块基地址, 设置 root 设备, 加载和解析 grub 配置,
加载模块等等, 执行完之后, grub_main 转移 grub 到 normal 模块, grub_normal_execute
完成最后的准备阶段, 之后显示可选的操作系统菜单. 当我们选择对应的的选项, 调用
grub_menu_execute_entry 调用 boot 命令启动对应的操作系统.


Bootloader 转换控制权给 kernel, 此时 bootloader 已经将内核加载到内存.


###Kernel 启动

首先进入 arch/x86/boot/head.S 的 292 行

```
    	.globl	_start
    _start:
    		# Explicitly enter this as bytes, or the assembler
    		# tries to generate a 3-byte jump here, which causes
    		# everything else to push off to the wrong offset.
    		.byte	0xeb		# short (2-byte) jump
    		.byte	start_of_setup-1f
```

其中 0xeb 是 jump 指令, 跳转到 start_of_setup-1f 处.

```
    	.section ".entrytext", "ax"
    start_of_setup:
    # Force %es = %ds
    	movw	%ds, %ax
    	movw	%ax, %es     //%es 存储 %ds 相同的地址
    	cld                  //将 DF(Direct Flag) 清零

    # 建立 Stack
    # Apparently some ancient versions of LILO invoked the kernel with %ss != %ds,
    # which happened to work by accident for the old code.  Recalculate the stack
    # pointer if %ss is invalid.  Otherwise leave it alone, LOADLIN sets up the
    # stack behind its own code, so we can't blindly put it directly past the heap.

    	movw	%ss, %dx    # 将 %ss 地址保存到 %dx
    	cmpw	%ax, %dx	# %ds - %ss 设置对应的标志位 ZF, SF, CF, OF.
    	movw	%sp, %dx    # 保持 %sp 到 %ds

    	je	2f		# -> assume %sp is reasonably set //ZF = 1 即 %ds == %ss 跳转到 2:

    	# Invalid %ss, make up a new stack
    	movw	$_end, %dx
    	testb	$CAN_USE_HEAP, loadflags
    	jz	1f
    	movw	heap_end_ptr, %dx
    1:	addw	$STACK_SIZE, %dx
    	jnc	2f
    	xorw	%dx, %dx	# Prevent wraparound

    2:	# Now %dx should point to the end of our stack space 此时 %ds = %es = %ss
    	andw	$~3, %dx	# dword align (might as well...)
    	jnz	3f              # ZF = 0, 跳转到 3:
    	movw	$0xfffc, %dx	# Make sure we're not zero
    3:	movw	%ax, %ss    #   
    	movzwl	%dx, %esp	# Clear upper half of %esp
    	sti			# Now we should have a working stack 允许中断

    # We will have entered with %cs = %ds+0x20, normalize %cs so
    # it is on par with the other segments.
    	pushw	%ds         #ds 压栈
    	pushw	$6f         #6f 压栈
    	lretw               #取出 %ds 给 %cs, 6:处地址给 ip, 从该地址开始执行程序.
    6:

    # Check signature at end of setup
    	cmpl	$0x5a5aaa55, setup_sig
    	jne	setup_bad

    # BSS 初始化, 将 $__bss_start 到 $end+3 区域清零
    # Zero the bss
    	movw	$__bss_start, %di
    	movw	$_end+3, %cx
    	xorl	%eax, %eax
    	subw	%di, %cx
    	shrw	$2, %cx

        #repeat %cx times for stosl which store %eax(0) from $__bss_start to $_end+3
    	rep; stosl

    # Jump to C code (should not return)
	calll	main
```

其中 start_of_setup 部分做了如下几件事:

1. 确保所有分段寄存器的值是相同的
2. 如果需要, 建立正确的栈
3. 建立 BSS
4. 跳到 C 代码的 arch/x86/boot/main.c 的 main 函数

系统启动首先进入实模式(注意是为了向下兼容), 之后进入保护模式


感觉有点乱, 后续修正. 不过要真正理解启动过程, 分析 coreboot 和 grub 的源代码
应该能够建立比较清晰的认识.

###从实模式到保护模式

[long mode](https://en.wikipedia.org/wiki/Long_mode)

```
    void main(void)
    {
    	/* First, copy the boot header into the "zeropage" */
    	copy_boot_params();

    	/* Initialize the early-boot console */
    	console_init();
    	if (cmdline_find_option_bool("debug"))
    		puts("early console in setup code\n");

    	/* End of heap check */
    	init_heap();

    	/* Make sure we have all the proper CPU support */
    	if (validate_cpu()) {
    		puts("Unable to boot - please use a kernel appropriate "
    		     "for your CPU.\n");
    		die();
    	}

    	/* Tell the BIOS what CPU mode we intend to run in. */
    	set_bios_mode();

    	/* Detect memory layout */
    	detect_memory();

    	/* Set keyboard repeat rate (why?) and query the lock flags */
    	keyboard_init();

    	/* Query MCA information */
    	query_mca();

    	/* Query Intel SpeedStep (IST) information */
    	query_ist();

    	/* Query APM information */
    #if defined(CONFIG_APM) || defined(CONFIG_APM_MODULE)
    	query_apm_bios();
    #endif

    	/* Query EDD information */
    #if defined(CONFIG_EDD) || defined(CONFIG_EDD_MODULE)
    	query_edd();
    #endif

    	/* Set the video mode */
    	set_video();

    	/* Do the last things and invoke protected mode */
    	go_to_protected_mode();
    }
```

###[copy_boot_params](http://code.woboq.org/linux/linux/arch/x86/boot/main.c.html#copy_boot_params)

    将 head.S 中的 hdr 拷贝到 struct boot_params.hdr, 这里 boot_params 被称为 zeropage

###[console_init](http://code.woboq.org/linux/linux/arch/x86/boot/early_serial_console.c.html#console_init)

    略过

###[init_heap]()

```
    static void init_heap(void)
    {
    	char *stack_end;

    	if (boot_params.hdr.loadflags & CAN_USE_HEAP) {
    		asm("leal %P1(%%esp),%0"
    		    : "=r" (stack_end) : "i" (-STACK_SIZE));

    		heap_end = (char *)
    			((size_t)boot_params.hdr.heap_end_ptr + 0x200);
    		if (heap_end > stack_end)
    			heap_end = stack_end;
    	} else {
    		/* Boot protocol 2.00 only, no heap available */
    		puts("WARNING: Ancient bootloader, some functionality "
    		     "may be limited!\n");
    	}
    }
```

    stack_end = esp - STACK_SIZE
    heap_end = boot_params.hdr.heap_end_ptr + 0x200

###[validate_cpu](http://code.woboq.org/linux/linux/arch/x86/boot/cpu.c.html#validate_cpu)

```
    int validate_cpu(void)
    {
    	u32 *err_flags;
    	int cpu_level, req_level;
    	check_cpu(&cpu_level, &req_level, &err_flags);
    	if (cpu_level < req_level) {
    		printf(""This kernel requires an %s CPU, "",
    		       cpu_name(req_level));
    		printf(""but only detected an %s CPU.\n"",
    		       cpu_name(cpu_level));
    		return -1;
    	}
    	if (err_flags) {
    		puts(""This kernel requires the following features ""
    		     ""not present on the CPU:\n"");
    		show_cap_strs(err_flags);
    		putchar('\n');
    		return -1;
    	} else {
    		return 0;
    	}
    }

    int check_cpu(int *cpu_level_ptr, int *req_level_ptr, u32 **err_flags_ptr)
    {
    	int err;
    	memset(&cpu.flags, 0, sizeof cpu.flags);
    	cpu.level = 3;
    	if (has_eflag(X86_EFLAGS_AC)) // EFLAGS ^ (EFLAGS ^ X86_EFLAGS_AC) & X86_EFLAGS_AC
    		cpu.level = 4;
    	get_cpuflags();
    	err = check_cpuflags();
    	if (test_bit(X86_FEATURE_LM, cpu.flags))
    		cpu.level = 64;
    	if (err == 0x01 &&
    	    !(err_flags[0] &
    	      ~((1 << X86_FEATURE_XMM)|(1 << X86_FEATURE_XMM2))) &&
    	    is_amd()) {
    		/* If this is an AMD and we're only missing SSE+SSE2, try to
    		   turn them on */
    		u32 ecx = MSR_K7_HWCR;
    		u32 eax, edx;
    		asm(""rdmsr"" : ""=a"" (eax), ""=d"" (edx) : ""c"" (ecx));
    		eax &= ~(1 << 15);
    		asm(""wrmsr"" : : ""a"" (eax), ""d"" (edx), ""c"" (ecx));
    		get_cpuflags();	/* Make sure it really did something */
    		err = check_cpuflags();
    	} else if (err == 0x01 &&
    		   !(err_flags[0] & ~(1 << X86_FEATURE_CX8)) &&
    		   is_centaur() && cpu.model >= 6) {
    		/* If this is a VIA C3, we might have to enable CX8
    		   explicitly */
    		u32 ecx = MSR_VIA_FCR;
    		u32 eax, edx;
    		asm(""rdmsr"" : ""=a"" (eax), ""=d"" (edx) : ""c"" (ecx));
    		eax |= (1<<1)|(1<<7);
    		asm(""wrmsr"" : : ""a"" (eax), ""d"" (edx), ""c"" (ecx));
    		set_bit(X86_FEATURE_CX8, cpu.flags);
    		err = check_cpuflags();
    	} else if (err == 0x01 && is_transmeta()) {
    		/* Transmeta might have masked feature bits in word 0 */
    		u32 ecx = 0x80860004;
    		u32 eax, edx;
    		u32 level = 1;
    		asm(""rdmsr"" : ""=a"" (eax), ""=d"" (edx) : ""c"" (ecx));
    		asm(""wrmsr"" : : ""a"" (~0), ""d"" (edx), ""c"" (ecx));
    		asm(""cpuid""
    		    : ""+a"" (level), ""=d"" (cpu.flags[0])
    		    : : ""ecx"", ""ebx"");
    		asm(""wrmsr"" : : ""a"" (eax), ""d"" (edx), ""c"" (ecx));
    		err = check_cpuflags();
    	} else if (err == 0x01 &&
    		   !(err_flags[0] & ~(1 << X86_FEATURE_PAE)) &&
    		   is_intel() && cpu.level == 6 &&
    		   (cpu.model == 9 || cpu.model == 13)) {
    		/* PAE is disabled on this Pentium M but can be forced */
    		if (cmdline_find_option_bool(""forcepae"")) {
    			puts(""WARNING: Forcing PAE in CPU flags\n"");
    			set_bit(X86_FEATURE_PAE, cpu.flags);
    			err = check_cpuflags();
    		}
    		else {
    			puts(""WARNING: PAE disabled. Use parameter 'forcepae' to enable at your own risk!\n"");
    		}
    	}
    	if (err_flags_ptr)
    		*err_flags_ptr = err ? err_flags : NULL;
    	if (cpu_level_ptr)
    		*cpu_level_ptr = cpu.level;
    	if (req_level_ptr)
    		*req_level_ptr = req_level;
    	return (cpu.level < req_level || err) ? -1 : 0;
    }


    struct cpu_features {
    	int level;		/* Family, or 64 for x86-64 */
    	int model;
    	u32 flags[NCAPINTS]; //具体的 flags 参考[这里](http://code.woboq.org/linux/linux/arch/x86/include/asm/cpufeature.h.html#15)
    };
```

检查 CPU 支持特性, 并设置对应特性. 具体的特性参考[这里](http://code.woboq.org/linux/linux/arch/x86/include/asm/cpufeature.h.html#15)

###set_bios_mode();

调用 15 号中断,

###[detect_memory](http://code.woboq.org/linux/linux/arch/x86/boot/memory.c.html#detect_memory_e820)


```
    int detect_memory(void)
    {
    	int err = -1;
    	if (detect_memory_e820() > 0)
    		err = 0;
    	if (!detect_memory_e801())
    		err = 0;
    	if (!detect_memory_88())
    		err = 0;
    	return err;
    }

    struct e820entry {
    	__u64 addr;	/* start of memory segment */
    	__u64 size;	/* size of memory segment */
    	__u32 type;	/* type of memory segment */
    } __attribute__((packed));
```

核心都是初始化 biosreg 之后调用 15 号中断


###[keyboard_init](http://code.woboq.org/linux/linux/arch/x86/boot/main.c.html#keyboard_init)

调用 16 号中断


###[query_ist](http://code.woboq.org/linux/linux/arch/x86/boot/main.c.html#query_ist)

调用 15 号中断

###[set_video](http://code.woboq.org/linux/linux/arch/x86/boot/video.c.html#set_video)

TODO

###

```
void go_to_protected_mode(void)
{
	/* Hook before leaving real mode, also disables interrupts */
	realmode_switch_hook();
	/* Enable the A20 gate */
	if (enable_a20()) {
		puts(""A20 gate not responding, unable to boot...\n"");
		die();
	}
	/* Reset coprocessor (IGNNE#) */
	reset_coprocessor();
	/* Mask all interrupts in the PIC */
	mask_all_interrupts();
	/* Actual transition to protected mode... */
	setup_idt();
	setup_gdt();
	protected_mode_jump(boot_params.hdr.code32_start,
			    (u32)&boot_params + (ds() << 4));
}
```



* 分段　保存在 GDTR 寄存器, 由 GDT 的结构描述, 在内存中的位置不固定.
* 分页

[中断跳表](http://www.ctyme.com/intr/int.htm)


If the system has just been powered up or the reset button was pressed ("cold boot"), the full power-on self-test (POST) is run. If Ctrl+Alt+Delete was pressed ("warm boot"), a special flag value is stored in nonvolatile BIOS memory ("CMOS") before the processor is reset, and after the reset the BIOS startup code detects this flag and does not run the POST. This saves the time otherwise used to detect and test all memory.

The POST checks, identifies, and initializes system devices such as the CPU, RAM, interrupt and DMA controllers and other parts of the chipset, video display card, keyboard, hard disk drive, optical disc drive and other basic hardware.

[系统启动过程](https://en.wikipedia.org/wiki/Booting#Boot_sequence)

[coreboot][]

[母板](https://en.wikipedia.org/wiki/Motherboard#Design)

##参考

[](https://www.coreboot.org/Payloads#Linux)
[BIOS](https://en.wikipedia.org/wiki/BIOS#System_startup)
[Gate-A20](https://en.wikipedia.org/wiki/A20_line)

[内核启动](https://0xax.gitbooks.io/linux-insides/content/Booting/linux-bootstrap-2.html)

the BIOS first enables Gate-A20 when counting and testing all of the system's
memory, and disables it before transferring control to the operating system.

##附录


### cmp 指令

```
        /*
           unsigned compare

           %ds == %ss, ZF=1
           %ds != %ss, ZF=0
           %ds >= %ss, CF=0
           %ds >  %ss, ZF=0, CF=0
           %ds <= %ss, ZF=1 | CF=1
           %ds <  %ss, ZF=0, CF=1

           singed compare
           %ds >  %ss, SF = 0, OF = 0
           %ds <  %ss, SF = 1, OF = 0
           %ds <  %ss, SF = 0, OF = 1
           %ds >  %ss, SF = 1, OF = 1
           两数同为正，相加，值为负，则说明溢出
           两数同为负，相加，值为正，则说明溢出
           故有，正正得负则溢出，负负得正则溢出

            两数相减，同号，则不溢出
            两数为异号，结果与减数符号相同，则溢出。
         */
```

###rep 指令

将 rep 后面的指令执行 cx 次

###stosl 指令

将寄存器 %eax 内容存储到内存单元 es:di, 同时修改 di, 指向下一个元素.

###lretw 指令

弹出第一个 word 给 ip, 第二个 word 给 cs; 之后执行 cs:ip 指定的地址

###内核中的魔数

arch/x86/include/asm/setup.h

#define OLD_CL_ADDRESS		0x020	/* Relative to real mode data */

###pushf

EFLAGS
