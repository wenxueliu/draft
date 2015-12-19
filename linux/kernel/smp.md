

    一、前言
    SMP（Symmetric Multi-Processing），对称多处理结构的简称，是指在一个计算机上汇集了一组处理器(多CPU),各CPU之间共享内存子系统以及总线结构。在这种技术的支持下，一个服务器系统可以同时运行多个处理器，并共享内存和其他的主机资源。像双至强，也就是我们所说的二路，这是在对称处理器系统中最常见的一种（至强MP可以支持到四路，AMD Opteron可以支持1-8 路）。也有少数是16路的。但是一般来讲，SMP结构的机器可扩展性较差，很难做到100个以上多处理器，常规的一般是8个到16 个，不过这对于多数的用户来说已经够用了。在高性能服务器和工作站级主板架构中最为常见，像UNIX服务器可支持最多256个CPU的系统。

    二、smp_processor_id()函数解析
    1.含义
    smp_processor_id()其意义在于SMP的情况下，获得当前CPU的ID。如果不是SMP，那么就返回0。在CONFIG_X86_32_SMP的情况下，是一个宏，调用raw_smp_processor_id()宏：

    2.代码
    #define smp_processor_id() raw_smp_processor_id()
    #define raw_smp_processor_id() (this_cpu_read(cpu_number))
    #define this_cpu_read(pcp) __pcpu_size_call_return(this_cpu_read_, (pcp))

    //通过以上宏调用，即最后调用__pcpu_size_call_return(this_cpu_read_,cpu_number)
    这里cpu_number来自arch/x86/kernel/setup_percpu.c的24行：
    DEFINE_PER_CPU(int, cpu_number);
    EXPORT_PER_CPU_SYMBOL(cpu_number);
    这个东西不像是c语言全局变量，而是通过两个宏来定义的。要读懂这两个宏，必须对每CPU变量这个概念非常了解，如果还不是很清楚的同学请查阅一下博客“每CPU变量”http://blog.csdn.net/yunsongice/archive/2010/05/18/5605239.aspx。

    其中DEFINE_PER_CPU来自文件include/linux/percpu-defs.h：
    #define DEFINE_PER_CPU(type, name) /
           DEFINE_PER_CPU_SECTION(type, name, "")

    该宏静态分配一个每CPU数组，数组名为name，结构类型为type。由于我们没有设置CONFIG_DEBUG_FORCE_WEAK_PER_CPU编译选项，所以DEFINE_PER_CPU_SECTION又被定义为：
    #define DEFINE_PER_CPU_SECTION(type, name, sec) /
           __PCPU_ATTRS(sec) PER_CPU_DEF_ATTRIBUTES /
           __typeof__(type) name

    其中，__PCPU_ATTRS(sec)在include/linux/percpu-defs.h中定义：
    #define __PCPU_ATTRS(sec) /
           __percpu __attribute__((section(PER_CPU_BASE_SECTION sec))) /
           PER_CPU_ATTRIBUTES

    __percpu是个编译扩展类型，大家可以去看看include/linux/compile.h这个文件，里面的__percpu是空的。而传进来的sec也是空的，PER_CPU_ATTRIBUTES也是空的，而上面PER_CPU_DEF_ATTRIBUTES还是空代码，可能都是留给将来内核代码扩展之用的吧，所以DEFINE_PER_CPU(int, cpu_number)展开就是：
    __attribute__((section(PER_CPU_BASE_SECTION))) /
    __typeof__(int) cpu_number
     
    所以现在只关注PER_CPU_BASE_SECTION，来自include/asm-generic/percpu.h
    #ifdef CONFIG_SMP
    #define PER_CPU_BASE_SECTION ".data.percpu"
    #else
    #define PER_CPU_BASE_SECTION ".data"
    #endif

    gcc支持一种叫做类型识别的技术，通过typeof(x)关键字，获得x的数据类型。而如果是在一个要被一些c文件包含的头文件中获得变量的数据类型，就需要用__typeof__而不是typeof关键字了，比如说我们这里。最后，这里就是声明一个int类型的cpu_number变量，编译的时候把他指向.data.percpu段的开始位置。

    #define __pcpu_size_call_return(stem, variable) \
    ({     
        //声明变量int pscr_ret__                                                                                \
        typeof(variable) pscr_ret__;
        //验证cpu_number是否为一个percpu变量 \
        __verify_pcpu_ptr(&(variable));
        
        //根据cpu_number的size，调用相应的函数，即调用this_cpu_read_4 \
        switch(sizeof(variable)) { \
        case 1: pscr_ret__ = stem##1(variable);break; \
        case 2: pscr_ret__ = stem##2(variable);break; \
        case 4: pscr_ret__ = stem##4(variable);break; \
        case 8: pscr_ret__ = stem##8(variable);break; \
        default: \
            __bad_size_call_parameter();break;             \
        } \
        pscr_ret__; \
    })

    //用来验证指针是per-cpu类型
    #define __verify_pcpu_ptr(ptr) do { \
        const void __percpu *__vpp_verify = (typeof((ptr) + 0))NULL; \
        (void)__vpp_verify; \
    }

    #define this_cpu_read_1(pcp) percpu_from_op("mov", (pcp), "m"(pcp))
    #define this_cpu_read_2(pcp) percpu_from_op("mov", (pcp), "m"(pcp))
    #define this_cpu_read_4(pcp) percpu_from_op("mov", (pcp), "m"(pcp))

    //调用percpu_from_op("mov", cpu_number, "m" (cpu_number))
    #define percpu_from_op(op, var, constraint) \
    ({ \
        typeof(var) pfo_ret__; \
        switch (sizeof(var)) { \
        case 1: \
            asm(op "b "__percpu_arg(1)",%0" \
            : "=q" (pfo_ret__) \
            : constraint); \
            break; \
        case 2: \
            asm(op "w "__percpu_arg(1)",%0" \
            : "=r" (pfo_ret__) \
            : constraint); \
            break; \
        case 4: \
            asm(op "l "__percpu_arg(1)",%0" \
            : "=r" (pfo_ret__) \
            : constraint); \
            break; \
        case 8: \
            asm(op "q "__percpu_arg(1)",%0" \
            : "=r" (pfo_ret__) \
            : constraint); \
            break; \
        default: __bad_percpu_size(); \
        } \
        pfo_ret__; \
    })

    #define __percpu_arg(x) __percpu_prefix "%P" #x
    #define __percpu_prefix "%%"__stringify(__percpu_seg)":"
    #define __percpu_seg fs

    所以__percpu_arg(x)翻译过来就是："%%"__stringify(fs)":%P" #x

    #define __stringify_1(x...) #x
    #define __stringify(x...) __stringify_1(x)

    所以__percpu_arg(1)最终翻译过来就是：
    "%%" "fs:%P" "1"

    因此上边的汇编代码翻译过来就是：
    asm("movl %%fs:%P1, %0" /
         : "=q" (pfo_ret__) /
         : "m" (var));

    其中pfo_ret__是输出部%0，q，表示寄存器eax、ebx、ecx或edx中的一个，并且变量pfo_ret__存放在这个寄存器中。var就是刚才我们建立的那个临时的汇编变量cpu_number，作为输入部%1。

    还记得“加载全局/中断描述符表”中把__KERNEL_PERCPU段选择子赋给了fs了吗，每个 cpu 的 fs 的内容都不同，fs:cpu_number就获得了当前存放在__KERNEL_PERCPU段中cpu_number偏移的内存中，最后把结果返回给pfo_ret__。所以这个宏最后的结果就是pfo_ret__的值，其返回的是CPU的编号.

    参考：
    http://blog.csdn.net/yunsongice/article/details/6130032
    http://bbs.chinaunix.net/thread-3767460-1-1.html


    //////////////////////////////////////////////////////////////////////////////////////
    三、for_each_online_cpu()内核函数解析
    1.含义
    for_each_online_cpu来枚举系统中所有core的id值，也就是常说的cpuid。

    2.代码
    #define for_each_online_cpu(cpu) for_each_cpu((cpu), cpu_online_mask)
    #define for_each_cpu(cpu, mask) \
        for ((cpu) = -1;(cpu) = cpumask_next((cpu), (mask)),(cpu) < nr_cpu_ids;)

    从以上代码可以看出依此根据掩码cpu_online_mask和系统core个数nr_cpu_ids来循环取出真正在工作的处理器序号。

    const struct cpumask *const cpu_online_mask = to_cpumask(cpu_online_bits);

    2.1 to_cpumask
    //把cpu_online_bits强制转换成cpumask类型
    #define to_cpumask(bitmap) \
        ((struct cpumask *)(1 ? (bitmap):(void *)sizeof(__check_is_bitmap(bitmap))))

    typedef struct cpumask { DECLARE_BITMAP(bits, NR_CPUS); } cpumask_t;
    #define DECLARE_BITMAP(name,bits) unsigned long name[BITS_TO_LONGS(bits)]

    //BITS_TO_LONGS宏根据处理器个数分配数组大小
    #define BITS_PER_BYTE 8
    #define BITS_TO_LONGS(nr) DIV_ROUND_UP(nr, BITS_PER_BYTE * sizeof(long))
    #define DIV_ROUND_UP(n,d) (((n) + (d) - 1) / (d))

    所以以上宏调用生成的cpu_online_mask结构是:
    struct cpumask
    {
        unsigned long bits[1];
    }*cpu_online_mask;

    2.2 cpu_online_bits
    cpu_online_bits, 用以表示系统真正在工作的处理器个数/状态。当内核管理处理器时主要是通过这个来进行的.
    static DECLARE_BITMAP(cpu_online_bits, CONFIG_NR_CPUS) __read_mostly;

    //通过这个函数可以设置当前cpu是有效的还是无效的，即
    void set_cpu_online(unsigned int cpu, bool online)
    {
        if (online)
            cpumask_set_cpu(cpu, to_cpumask(cpu_online_bits));
        else
            cpumask_clear_cpu(cpu, to_cpumask(cpu_online_bits));
    }

    static inline void cpumask_set_cpu(unsigned int cpu, struct cpumask *dstp)
    {
        //#define cpumask_bits(maskp) ((maskp)->bits)
        set_bit(cpumask_check(cpu), cpumask_bits(dstp));
    }

    static inline void set_bit(int nr, void *addr)
    {
        //把addr地址下的内容的第nr位置为1
        asm("btsl %1,%0" : "+m" (*(u32 *)addr) : "Ir" (nr));
    }

    2.3 cpumask_next
    static inline unsigned int cpumask_next(int n, const struct cpumask *srcp)
    {
        /* -1 is a legal arg here. */
        if (n != -1)
            cpumask_check(n);//检查cpu位图
        
        //取下一位数值    
        return find_next_bit(cpumask_bits(srcp), nr_cpumask_bits, n+1);
    }

    #define cpumask_bits(maskp) ((maskp)->bits)
    //系统内核数量
    #define nr_cpumask_bits NR_CPUS

    unsigned long find_next_bit(const unsigned long *addr, unsigned long size,unsigned long offset)
    {
        //#define BITS_PER_LONG 32
        //#define BITOP_WORD(nr) ((nr) / BITS_PER_LONG)
        //当前要查找的cpu号在baddr地址处的偏移地址
        const unsigned long *p = addr + BITOP_WORD(offset);
        unsigned long result = offset & ~(BITS_PER_LONG-1);//offset & 0xE0
        unsigned long tmp;
        
        if (offset >= size)
            return size;
            
        size -= result;
        //offset整除得到在p地址处的偏移
        offset %= BITS_PER_LONG;
        if (offset) {
            tmp = *(p++);//取得p地址开始处保存的数据，即数组bits数据
            //tmp最低的offset为清零
            tmp &= (~0UL << offset);
            //cpu个数小于32
            if (size < BITS_PER_LONG)
                goto found_first;
            if (tmp)
                goto found_middle;
            size -= BITS_PER_LONG;
            result += BITS_PER_LONG;
        }
        
        //若cpu个数超过32个时
        while (size & ~(BITS_PER_LONG-1)) {
            if ((tmp = *(p++)))
                goto found_middle;
            result += BITS_PER_LONG;
            size -= BITS_PER_LONG;
        }
        if (!size)
            return result;
        tmp = *p;
        
    found_first:
        //清楚无效的cpu所占位数
        tmp &= (~0UL >> (BITS_PER_LONG - size));
        if (tmp == 0UL) /* Are any bits set? */
            return result + size; /* Nope. */
    found_middle:
        //__ffs找到tmp中第一个不为0的位的序号，加上result就是cpu号
        return result + __ffs(tmp);
    }

    for_each_cpu () 函数内核实现了两个版本，一个是单处理器版本，一个是多处理器版本，其中他还用到了cpu_present_mask 宏。
    系统中有四种这类的变量分别叫，cpu_present_mask,cpu_online_mask,cpu_active_mask , cpu_possible_mask;
    在Linux内核中默认的SMP是最大支持8CPU，当然你可以加大这个数值。这可以在make menuconfig 中找到相关设置 "CPUS".这四个变量来源于四个属性：
    cpu_all_bits ,用以表示在 menuconfig 中设置的NR_CPUS的值是多少。
    cpu_possible_bits,表示实际在运行时处理器的CPU个数是多少？
    cpu_online_bits, 用以表示系统真正在工作的处理器个数/状态。当内核管理处理器时主要是通过这个来进行的。
    cpu_present_bits:用以表示系统中present的处理器数量，不一定所有都是Online的，在支持处理器热插拔的系统中，possible与present的关系为“cpu_possible_map = cpu_present_map + additional_cpus” ,present处理器是指系统固有的处理器个数不是外部插入的。
    cpu_active_bits, 表示目前处于可工作状态的处理器个数。

    setup_max_cpus
    nr_cpu_ids
    在默认情况下都表示CPUS数量。
    const struct cpumask *const cpu_possible_mask = to_cpumask(cpu_possible_bits);

    /* An arch may set nr_cpu_ids earlier if needed, so this would be redundant */
    void __init setup_nr_cpu_ids(void)
    {
        nr_cpu_ids = find_last_bit(cpumask_bits(cpu_possible_mask),NR_CPUS) + 1;
     }

     /* this is hard limit */
    static int __init nrcpus(char *str)
    {
        int nr_cpus;
        
        get_option(&str, &nr_cpus);
        if (nr_cpus > 0 && nr_cpus < nr_cpu_ids)
            nr_cpu_ids = nr_cpus;
        
        return 0;
    }
    early_param("nr_cpus", nrcpus);

    int nr_cpu_ids __read_mostly = NR_CPUS;

    #define NR_CPUS CONFIG_NR_CPUS
    NR_CPUS是个宏定义，可以在config中配置（CONFIG_NR_CPUS），表示系统中CPU的最大数量

    //////////////////////////////////////////////////////////////////////////////////////
    三、smp_call_function_single()内核函数解析
    1.含义
    系统中每个cpu都还拥有各自的一个类型为struct call_single_queue的队列dst（list)，smp_call_function_single（）会根据目标cpu来获得该队列，把前述的csd作为跨cpu参数传递的方法。不管怎么说吧，跨cpu调用的参数传递方法是用了，然后如果队列dst为空，就调用arch_send_call_function_single_ipi(cpu)给参数所指定的cpu发ipi消息，目标cpu收到该消息进入中断处理函数，那么就调用csd_data->func函数了(其实应该是ipi的中断处理函数处理dst队列中的每个结点，调用每个结点上的func函数指针，所以队列不为空时就没必要再发ipi消息了。

    2.代码
    int smp_call_function_single(int cpu, smp_call_func_t func, void *info,int wait)
    {
        struct call_single_data d = {
            .flags = 0,
        };
        unsigned long flags;
        int this_cpu;
        int err = 0;
        
        this_cpu = get_cpu();//获得当前cpu号,并且禁止抢占

        /*
        * Can deadlock when called with interrupts disabled.
        * We allow cpu's that are not yet online though, as no one else can
        * send smp call function interrupt to this cpu and as such deadlocks
        * can't happen.
        */
        WARN_ON_ONCE(cpu_online(this_cpu) && irqs_disabled() && !oops_in_progress);
        
        //要指定运行的cpu id和当前cpu id一致的话，就调用func函数运行
        if (cpu == this_cpu) {
            local_irq_save(flags);
            func(info);
            local_irq_restore(flags);
        } else {//不一致，发送ipi中断
            //要运行该func的cpu号必须小于系统中cpu个数，且该cpu online
            if ((unsigned)cpu < nr_cpu_ids && cpu_online(cpu)) {
                /*
                struct call_single_data {
                    struct list_head list;
                    smp_call_func_t func;
                    void *info;
                    u16 flags;
                };
                */
                struct call_single_data *csd = &d;
        
                if (!wait)
                    csd = &__get_cpu_var(csd_data);
                
                //设置csd结构
                csd_lock(csd);
                csd->func = func;
                csd->info = info;//函数参数
                //挂到每cpu队列call_single_queue中，并向指定cpu发送IPI中断
                generic_exec_single(cpu, csd, wait);
            } else {
                err = -ENXIO; /* CPU not online */
            }
        }
        
        put_cpu();
        
        return err;
    }

    void generic_exec_single(int cpu, struct call_single_data *csd, int wait)
    {
        //找到要运行该func的cpu的每cpu变量call_single_queue队列
        struct call_single_queue *dst = &per_cpu(call_single_queue, cpu);
        unsigned long flags;
        int ipi;
        
        raw_spin_lock_irqsave(&dst->lock, flags);
        ipi = list_empty(&dst->list);//if empty return 1
        //把该csd结构挂入每cpu变量call_single_queue队列尾部
        list_add_tail(&csd->list, &dst->list);
        raw_spin_unlock_irqrestore(&dst->lock, flags);
        
        //队列为空，就向该cpu发送IPI中断，让其读取其每cpu队列call_single_queue上的csd结构，进而去执行func函数
        if (ipi)
            arch_send_call_function_single_ipi(cpu);
        
        //若设置了等待标志，则进行等待
        if (wait)
            csd_lock_wait(csd);
    }

    static void csd_lock_wait(struct call_single_data *csd)
    {
        //若csd标志设置了CSD_FLAG_LOCK位，则在这里循环等待。前边并没有设置该标志
        while (csd->flags & CSD_FLAG_LOCK)
            cpu_relax();
    }

    //全局变量smp_ops也是一个smp_ops结构，在代码arch/x86/kernel/smp.c中被初始化成：
    struct smp_ops smp_ops = {
        .smp_prepare_boot_cpu = native_smp_prepare_boot_cpu,
        .smp_prepare_cpus = native_smp_prepare_cpus,
        .smp_cpus_done = native_smp_cpus_done,
        .stop_other_cpus = native_stop_other_cpus,
        .smp_send_reschedule = native_smp_send_reschedule,
        .cpu_up = native_cpu_up,
        .cpu_die = native_cpu_die,
        .cpu_disable = native_cpu_disable,
        .play_dead = native_play_dead,
        .send_call_func_ipi = native_send_call_func_ipi,
        .send_call_func_single_ipi = native_send_call_func_single_ipi,
    };

    static inline void arch_send_call_function_single_ipi(int cpu)
    {
        //调用native_send_call_func_single_ipi
        smp_ops.send_call_func_single_ipi(cpu);
    }

    void native_send_call_func_single_ipi(int cpu)
    {
        apic->send_IPI_mask(cpumask_of(cpu), CALL_FUNCTION_SINGLE_VECTOR);
    }

    #define cpumask_of(cpu) (get_cpu_mask(cpu))
    static inline const struct cpumask *get_cpu_mask(unsigned int cpu)
    {
        //cpu是指目标cpu，即要将该IPI中断传给此cpu，通过下面得到通知IPI中断的cpu掩码
        const unsigned long *p = cpu_bit_bitmap[1 + cpu % BITS_PER_LONG];
        p -= cpu / BITS_PER_LONG;
        return to_cpumask(p);
    }

    const unsigned long cpu_bit_bitmap[BITS_PER_LONG+1][BITS_TO_LONGS(NR_CPUS)] = {
        MASK_DECLARE_8(0), MASK_DECLARE_8(8),
        MASK_DECLARE_8(16), MASK_DECLARE_8(24),
    #if BITS_PER_LONG > 32
        MASK_DECLARE_8(32), MASK_DECLARE_8(40),
        MASK_DECLARE_8(48), MASK_DECLARE_8(56),
    #endif
    };

    #define MASK_DECLARE_1(x) [x+1][0] = (1UL << (x))
    #define MASK_DECLARE_2(x) MASK_DECLARE_1(x), MASK_DECLARE_1(x+1)
    #define MASK_DECLARE_4(x) MASK_DECLARE_2(x), MASK_DECLARE_2(x+2)
    #define MASK_DECLARE_8(x) MASK_DECLARE_4(x), MASK_DECLARE_4(x+4)

    //通过以上宏计算得到：
    cpu_bit_bitmap[][] = {
        [1][0]=1,
        [2][0]=1<<1,
        [3][0]=1<<2,
        [4][0]=1<<3,
        ......
    }

    //x86 32位下，apic定义为
    struct apic *apic = &apic_default;
    static struct apic apic_default = {
     77 .name = "default",
     78 .probe = probe_default,
     79 .acpi_madt_oem_check = NULL,
     80 .apic_id_valid = default_apic_id_valid,
     81 .apic_id_registered = default_apic_id_registered,
     82
     83 .irq_delivery_mode = dest_LowestPrio,
     84 /* logical delivery broadcast to all CPUs: */
     85 .irq_dest_mode = 1,
     86
     87 .target_cpus = default_target_cpus,
     88 .disable_esr = 0,
     89 .dest_logical = APIC_DEST_LOGICAL,
     90 .check_apicid_used = default_check_apicid_used,
     91 .check_apicid_present = default_check_apicid_present,
     92
     93 .vector_allocation_domain = flat_vector_allocation_domain,
     94 .init_apic_ldr = default_init_apic_ldr,
     95
     96 .ioapic_phys_id_map = default_ioapic_phys_id_map,
     97 .setup_apic_routing = setup_apic_flat_routing,
     98 .multi_timer_check = NULL,
     99 .cpu_present_to_apicid = default_cpu_present_to_apicid,
    100 .apicid_to_cpu_present = physid_set_mask_of_physid,
    101 .setup_portio_remap = NULL,
    102 .check_phys_apicid_present = default_check_phys_apicid_present,
    103 .enable_apic_mode = NULL,
    104 .phys_pkg_id = default_phys_pkg_id,
    105 .mps_oem_check = NULL,
    106
    107 .get_apic_id = default_get_apic_id,
    108 .set_apic_id = NULL,
    109 .apic_id_mask = 0x0F << 24,
    110
    111 .cpu_mask_to_apicid_and = flat_cpu_mask_to_apicid_and,
    112
    113 .send_IPI_mask = default_send_IPI_mask_logical,
    114 .send_IPI_mask_allbutself = default_send_IPI_mask_allbutself_logical,
    115 .send_IPI_allbutself = default_send_IPI_allbutself,
    116 .send_IPI_all = default_send_IPI_all,
    117 .send_IPI_self = default_send_IPI_self,
    118
    119 .trampoline_phys_low = DEFAULT_TRAMPOLINE_PHYS_LOW,
    120 .trampoline_phys_high = DEFAULT_TRAMPOLINE_PHYS_HIGH,
    121
    122 .wait_for_init_deassert = default_wait_for_init_deassert,
    123
    124 .smp_callin_clear_local_apic = NULL,
    125 .inquire_remote_apic = default_inquire_remote_apic,
    126
    127 .read = native_apic_mem_read,
    128 .write = native_apic_mem_write,
    129 .eoi_write = native_apic_mem_write,
    130 .icr_read = native_apic_icr_read,
    131 .icr_write = native_apic_icr_write,
    132 .wait_icr_idle = native_apic_wait_icr_idle,
    133 .safe_wait_icr_idle = native_safe_apic_wait_icr_idle,
    134
    135 .x86_32_early_logical_apicid = default_x86_32_early_logical_apicid,
    };

    void default_send_IPI_mask_logical(const struct cpumask *cpumask, int vector)
    {
        //得到相应cpu的掩码，若是cpu1的话，此值应为0x0000 0002
        unsigned long mask = cpumask_bits(cpumask)[0];
        unsigned long flags;
        
        if (!mask)
            return;
        
        local_irq_save(flags);
        WARN_ON(mask & ~cpumask_bits(cpu_online_mask)[0]);
        //#define APIC_DEST_LOGICAL 0x00800
        __default_send_IPI_dest_field(mask, vector, apic->dest_logical);
        local_irq_restore(flags);
    }

    static inline void __default_send_IPI_dest_field(unsigned int mask, int vector, unsigned int dest)
    {
        unsigned long cfg;
        
        //CPU内部APIC有一些控制寄存器，APIC_ICR和APIC_ICR2是其中的两个。要向系统中的一个CPU发出中断请求时，首先要通过apic_wait_icr_idle(),确认或等待APIC_ICR处于空闲状态.
        if (unlikely(vector == NMI_VECTOR))
            safe_apic_wait_icr_idle();
        else
            __xapic_wait_icr_idle();
        
        //prepare target chip field
        cfg = __prepare_ICR2(mask);
        //APIC_ICR2主要用来说明要发送的中断请求的目标
        native_apic_mem_write(APIC_ICR2, cfg);
        
        //program the ICR
        cfg = __prepare_ICR(0, vector, dest);
        
        //Send the IPI. The write to APIC_ICR fires this off.
        native_apic_mem_write(APIC_ICR, cfg);
    }
    在SMP系统上，当一个CPU想对另一个CPU发送中断信号时，就在自己的本地APIC的ICR寄存器（Interrupt Command Register，中断命令寄存器）中存放其中断向量，和目标CPU拥有的本地APIC的标识，触发中断。IPI中断信号经由APIC总线传递到目标APIC，那个收到中断的APIC就向自己所属的CPU发送一个中断。

    Linux针对IA32的SMP系统定义了五种IPI：
    1, CALL_FUNCTION_VECTOR：发往自己除外的所有CPU，强制它们执行指定的函数；
    2, RESCHEDULE_VECTOR：使被中断的CPU重新调度；
    3, INVLIDATE_TLB_VECTOR：使被中断的CPU废弃自己的TLB缓存内容。
    4, ERROR_APIC_VECTOR：错误中断。
    5, SPUROUS_APIC_VECTOR：假中断


