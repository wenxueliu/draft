
1. 简介

2.6内核上一个新的特性就是per-CPU变量。顾名思义，就是每个处理器上有此变量的一个副本。
per-CPU的最大优点就是，对它的访问几乎不需要锁，因为每个CPU都在自己的副本上工作。
tasklet、timer_list等机制都使用了per-CPU技术。

2. 优势

每个处理器访问自己的副本, 无需加锁, 可以放入自己的 cache 中, 极大地提高了访问与更新效率. 常用于计数器.

当创建一个per-cpu变量时，系统中的每一个处理器都会拥有该变量的独有副本。由于每个处理器都是在自己的副本上工作，所以对per-cpu变量的访问几乎不需要加锁。   

per-cpu变量只为来自不同处理器的并发访问提供保护，对来自异步函数（中断处理程序和可延迟函数）的访问，以及内核抢

并不提供保护，因此在这些情况下还需要另外的同步原语


3. 使用

注意，2.6内核是抢占式的。所以在访问per-CPU变量时，应使用特定的API来避免抢占，即避免它被切换到另一个CPU上被处理。

per-CPU变量可以在编译时声明，也可以在系统运行时动态生成

相关头文件：<linux/percpu.h>

(1) 编译期间分配

声明：

    DEFINE_PER_CPU(type, name);

这语句为系统的每个CPU都创建了一个类型为type，名字为name的变量。如果需要在别处声明此变量，以防编译时的警告，可使用下面的宏：

	DECLARE_PER_CPU(type, name);  


例如

	DEFINE_PER_CPU(int,my_percpu); //声明一个变量
    DEFINE_PER_CPU(int[3],my_percpu_array); //声明一个数组

操作每个CPU的变量和指针

	get_cpu_var(name);  //返回当前处理器上的指定变量name的值, 同时将他禁止抢占；
	put_cpu_var(name); //与get_cpu_var(name)相对应，重新激活抢占；


避免进程在访问一个 per-CPU 变量时被切换到另外一个处理器上运行或被其它进程抢占:

    ptr = get_cpu_var(my_percpu); 

    put_cpu_var(my_percpu);

访问其他处理器的变量副本用这个宏：

获得别的处理器上的name变量的值

    per_cpu(var，int cpu_id); //返回别的处理器cpu_id 上变量 var 	的值；	


通过指针来操作每个CPU的数据：

	get_cpu_ptr(var); --- 返回一个void类型的指针，指向CPU ptr处的数据
	put_cpu_ptr(var); --- 操作完成后，重新激活内核抢占。
	
	#define get_cpu()       ({ preempt_disable(); smp_processor_id(); })  
    #define put_cpu()       preempt_enable()  


per-CPU变量导出，供模块使用：

    EXPORT_PER_CPU_SYMBOL(per_cpu_var);
    EXPORT_PER_CPU_SYMBOL_GPL(per_cpu_var);


(2) 动态分配与释放

动态分配 per-CPU 变量:

    void * alloc_percpu(type);
    void * __alloc_percpu(size_t size, size_t align); //可以做特定的内存对齐

    #define alloc_percpu(type)  \  
        (typeof(type) __percpu *)__alloc_percpu(sizeof(type), __alignof__(type))  
      
    /** 
     * __alloc_percpu - allocate dynamic percpu area 
     * @size: size of area to allocate in bytes 
     * @align: alignment of area (max PAGE_SIZE) 
     * 
     * Allocate zero-filled percpu area of @size bytes aligned at @align. 
     * Might sleep.  Might trigger writeouts. 
     * 
     * CONTEXT: 
     * Does GFP_KERNEL allocation. 
     * 
     * RETURNS: 
     * Percpu pointer to the allocated area on success, NULL on failure. 
     */  
    void __percpu *__alloc_percpu(size_t size, size_t align)  
    {  
        return pcpu_alloc(size, align, false);  
    }  
    EXPORT_SYMBOL_GPL(__alloc_percpu);  

参数为type, 就是指定的需要分配的类型，通过类型，可以得出__alloc_percpu（）的两个参数：

	size =  sizeof(type);

	align = __alignof__(type);

	__alignof__()是gcc的一个功能，它会返回指定类型或lvalue所需的对齐字节数。



释放动态分配的 per-CPU 变量：

    free_percpu();

	    /** 
     * free_percpu - free percpu area 
     * @ptr: pointer to area to free 
     * 
     * Free percpu area @ptr. 
     * 
     * CONTEXT: 
     * Can be called from atomic context. 
     */  
    void free_percpu(void __percpu *ptr)  
    {  
        void *addr;  
        struct pcpu_chunk *chunk;  
        unsigned long flags;  
        int off;  
      
        if (!ptr)  
            return;  
      
        addr = __pcpu_ptr_to_addr(ptr);  
      
        spin_lock_irqsave(&pcpu_lock, flags);  
      
        chunk = pcpu_chunk_addr_search(addr);  
        off = addr - chunk->base_addr;  
      
        pcpu_free_area(chunk, off);  
      
        /* if there are more than one fully free chunks, wake up grim reaper */  
        if (chunk->free_size == pcpu_unit_size) {  
            struct pcpu_chunk *pos;  
      
            list_for_each_entry(pos, &pcpu_slot[pcpu_nr_slots - 1], list)  
                if (pos != chunk) {  
                    schedule_work(&pcpu_reclaim_work);  
                    break;  
                }  
        }  
      
        spin_unlock_irqrestore(&pcpu_lock, flags);  
    }  
    EXPORT_SYMBOL_GPL(free_percpu);  

访问动态分配的 per-CPU 变量的访问通过 per_cpu_ptr 完成：

    per_cpu_ptr(void * per_cpu_var, int cpu_id);

要想阻塞抢占, 使用 get_cpu() 与 put_cpu() 即可:

    int cpu = get_cpu();
    ptr = per_cpu_ptr(per_cpu_var, cpu);
    put_cpu();

(3) 导出 Per-CPU 变量给模块

    EXPORT_PER_CPU_SYMBOL(per_cpu_var);

    EXPORT_PER_CPU_SYMBOL_GPL(per_cpu_var);

要在模块中访问这样一个变量，应该这样做声明：

    DECLARE_PER_CPU(type, name);

4. 注意

在某些体系结构上，per-CPU 变量可使用的地址空间是受限的, 要尽量保持这些变量比较小.

5. Per-CPU 变量的实现


定义

    #define DEFINE_PER_CPU(type, name) \
    __attribute__((__section__(".data.percpu"))) __typeof__(type) per_cpu__##name

从上面的代码我们可以看出，手工定义的所有per-cpu变量都是放在.data.percpu段的。注意上面的宏只是在SMP体系结构下才如此定义。
如果不是SMP结构的计算机那么只是简单的把所有的per-cpu变量放到全局变量应该放到的地方。



单CPU的per-cpu变量定义：

      27 #else /* ! SMP */
      28 
      29 #define DEFINE_PER_CPU(type, name) \
      30 __typeof__(type) per_cpu__##name

 在了解了上述代码后，我们还必须弄清楚一点：单CPU的计算机中使用的per-cpu变量就是通过上述宏定义的放在全局数据区的per-cpu变 量。而在SMP体系结构中，我们使用却不是放在.data.percpu段的变量，设想一下如果使用这个变量，那么应该哪个CPU使用呢？事实上，SMP 下，每个cpu使用的都是在.data.percpu段中的这些per-cpu变量的副本，有几个cpu就创建几个这样的副本。


使用上面的API为什么就能避免抢占问题呢，看看代码实现就知道了


	    /* 
     * Must be an lvalue. Since @var must be a simple identifier, 
     * we force a syntax error here if it isn't. 
     */  
    #define get_cpu_var(var) (*({               \  
        preempt_disable();              \  
        &__get_cpu_var(var); }))  
      
    /* 
     * The weird & is necessary because sparse considers (void)(var) to be 
     * a direct dereference of percpu variable (var). 
     */  
    #define put_cpu_var(var) do {               \  
        (void)&(var);                   \  
        preempt_enable();               \  
    } while (0)  

	#define get_cpu_ptr(var) ({             \  
        preempt_disable();              \  
        this_cpu_ptr(var); })  
      
    #define put_cpu_ptr(var) do {               \  
        (void)(var);                    \  
        preempt_enable();               \  
    } while (0)  


    #define get_cpu() ({ preempt_disable(); smp_processor_id(); })
    #define put_cpu() preempt_enable()

关键就在于 preempt_disable 和 preempt_enable 两个调用，分别是禁止抢占和开启抢占
抢占相关的东东以后再看


在系统初始化期 间，start_kernel()函数中调用setup_per_cpu_areas（）函数，用于为每个cpu的per-cpu变量副本分配空间，注意 这时alloc内存分配器还没建立起来，该函数调用alloc_bootmem函数为初始化期间的这些变量副本分配物理空间。



    332 static void __init setup_per_cpu_areas(void)
         /* */
     333 {
     334 unsigned long size, i;
     335 char *ptr;
     336 
     337 /* Copy section for each CPU (we discard the original) */
     338 size = ALIGN(__per_cpu_end - __per_cpu_start, SMP_CACHE_BYTES);
     339 #ifdef CONFIG_MODULES
     340 if (size < PERCPU_ENOUGH_ROOM)
     341 size = PERCPU_ENOUGH_ROOM;
     342 #endif
     343 
     344 ptr = alloc_bootmem(size * NR_CPUS);
     345 
     346 for (i = 0; i < NR_CPUS; i++, ptr += size) {
     347 __per_cpu_offset[i] = ptr - __per_cpu_start;
     348 memcpy(ptr, __per_cpu_start, __per_cpu_end - __per_cpu_start);
     349 }
     350 }
     351 #endif /* !__GENERIC_PER_CPU */

上述函数，在分配好每个cpu的per-cpu变量副本所占用的物理空间的同时，也对__per_cpu_offset[NR_CPUS]数组进行了初始化用于以后找到指定CPU的这些per-cpu变量副本。

![per_cpu_offset](per_cpu_offset.png)



    15 #define per_cpu(var, cpu) (*RELOC_HIDE(&per_cpu__##var, __per_cpu_offset[cpu]))
    16 #define __get_cpu_var(var) per_cpu(var, smp_processor_id())

这两个宏一个用于获得指定cpu的per-cpu变量，另一个用于获的本地cpu的per-cpu变量，可以自己分析一下。



##多核中percpu的数据分配



















//based on Linux V3.14 source code
##概述

每 CPU 变量是最简单也是最重要的同步技术. 每 CPU 变量主要是数据结构数组, 系统的每个 CPU 对应数组的一个元素.
一个 CPU 不应该访问与其它 CPU 对应的数组元素, 另外, 它可以随意读或修改它自己的元素而不用担心出现竞争条件,
因为它是唯一有资格这么做的 CPU. 这也意味着每 CPU 变量基本上只能在特殊情况下使用, 也就是当它确定在系统的
CPU 上的数据在逻辑上是独立的时候.

每个处理器访问自己的副本, 无需加锁, 可以放入自己的 cache 中, 极大地提高了访问与更新效率. 常用于计数器.

##相关结构体：

1.整体的 percpu 内存管理信息被收集在 struct pcpu_alloc_info 结构中

    struct pcpu_alloc_info {
        size_t static_size;    //静态定义的percpu变量占用内存区域长度
        size_t reserved_size;    //预留区域，在percpu内存分配指定为预留区域分配时，将使用该区域
        size_t dyn_size;        //动态分配的percpu变量占用内存区域长度
        //每个cpu的percpu空间所占得内存空间为一个unit, 每个unit的大小记为unit_size
        size_t unit_size;        //每颗处理器的percpu虚拟内存递进基本单位
        size_t atom_size;        //PAGE_SIZE
        size_t alloc_size;        //要分配的percpu内存空间
        size_t __ai_size;        //整个pcpu_alloc_info结构体的大小
        int nr_groups;        //该架构下的处理器分组数目
        struct pcpu_group_info groups[];        //该架构下的处理器分组信息
    };

2. 对于处理器的分组信息, 内核使用 struct pcpu_group_info 结构表示

    struct pcpu_group_info {
        int nr_units; //该组的处理器数目
        //组的percpu内存地址起始地址, 即组内处理器数目*处理器percpu虚拟内存递进基本单位
        unsigned long base_offset;
        unsigned int *cpu_map; //组内cpu对应数组，保存cpu id号
    };

3.内核使用pcpu_chunk结构管理percpu内存

    struct pcpu_chunk {
        //用来把chunk链接起来形成链表。每一个链表又都放到pcpu_slot数组中，根据chunk中空闲空间的大小决定放到数组的哪个元素中。
        struct list_head list;
        int free_size; //chunk中的空闲大小
        int contig_hint; //该chunk中最大的可用空间的map项的size
        void *base_addr; //percpu内存开始基地值
        int map_used; //该chunk中使用了多少个map项
        int map_alloc; //记录map数组的项数，为PERCPU_DYNAMIC_EARLY_SLOTS=128
        //若map项>0,表示该map中记录的size是可以用来分配percpu空间的。
        //若map项<0,表示该map项中的size已经被分配使用。
        int *map; //map数组，记录该chunk的空间使用情况
        void *data; //chunk data
        bool immutable; /* no [de]population allowed */
        unsigned long populated[]; /* populated bitmap */
    };

##per-cpu初始化

在系统初始化期间, start_kernel() 函数中调用 setup_per_cpu_areas() 函数, 用于为每个 cpu 的 per-cpu 变量副本分配空间,
注意这时 alloc 内存分配器还没建立起来, 该函数调用 alloc_bootmem 函数为初始化期间的这些变量副本分配物理空间.

在建立 percpu 内存管理机制之前要整理出该架构下的处理器信息, 包括处理器如何分组, 每组对应的处理器位图, 静态定义的
percpu 变量占用内存区域, 每颗处理器 percpu 虚拟内存递进基本单位等信息.

1. setup_per_cpu_areas() 函数, 用于为每个 cpu 的 per-cpu 变量副本分配空间

    void __init setup_per_cpu_areas(void)
    {
        unsigned long delta;
        unsigned int cpu;
        int rc;

        //为percpu建立第一个chunk
        rc = pcpu_embed_first_chunk(PERCPU_MODULE_RESERVE,
                                    PERCPU_DYNAMIC_RESERVE, PAGE_SIZE, NULL,
                                    pcpu_dfl_fc_alloc, pcpu_dfl_fc_free);
        if (rc < 0)
            panic("Failed to initialize percpu areas.");

        //内核为percpu分配了一大段空间，在整个percpu空间中根据cpu个数将percpu的空间分为不同的unit。
        //而pcpu_base_addr表示整个系统中percpu的起始内存地址.
        //__per_cpu_start表示静态分配的percpu起始地址。即节区".data..percpu"中起始地址。
        //函数首先算出副本空间首地址(pcpu_base_addr)与".data..percpu"section首地址(__per_cpu_start)之间的偏移量delta
        delta = (unsigned long)pcpu_base_addr - (unsigned long)__per_cpu_start;

        //遍历系统中的cpu，设置每个cpu的__per_cpu_offset指针
        //pcpu_unit_offsets[cpu]保存对应cpu所在副本空间相对于pcpu_base_addr的偏移量
        //加上delta，这样就可以得到每个cpu的per-cpu变量副本的偏移量, 放在__per_cpu_offset数组中.
        for_each_possible_cpu(cpu)
            __per_cpu_offset[cpu] = delta + pcpu_unit_offsets[cpu];
    }

1.1 为percpu建立第一个chunk

    int __init pcpu_embed_first_chunk(size_t reserved_size, size_t dyn_size,
                                        size_t atom_size,
                                        pcpu_fc_cpu_distance_fn_t cpu_distance_fn,
                                        pcpu_fc_alloc_fn_t alloc_fn,
                                        pcpu_fc_free_fn_t free_fn)
    {
        void *base = (void *)ULONG_MAX;
        void **areas = NULL;
        struct pcpu_alloc_info *ai;
        size_t size_sum, areas_size, max_distance;
        int group, i, rc;

        //收集整理该架构下的percpu信息，结果放在struct pcpu_alloc_info结构中
        ai = pcpu_build_alloc_info(reserved_size, dyn_size, atom_size,cpu_distance_fn);
        if (IS_ERR(ai))
            return PTR_ERR(ai);

        //计算每个cpu占用的percpu内存空间大小，包括静态定义变量占用空间+reserved空间+动态分配空间
        size_sum = ai->static_size + ai->reserved_size + ai->dyn_size;

        //areas用来保存每个group的percpu内存起始地址，为其分配空间，做临时存储使用，用完释放掉
        areas_size = PFN_ALIGN(ai->nr_groups * sizeof(void *));    
        areas = memblock_virt_alloc_nopanic(areas_size, 0);
        if (!areas) {
            rc = -ENOMEM;
            goto out_free;
        }

        //针对该系统下的每个group操作，为每个group分配percpu内存区域，前边只是计算出percpu信息，并没有分配percpu的内存空间。
        for (group = 0; group < ai->nr_groups; group++) {
            struct pcpu_group_info *gi = &ai->groups[group];//取出该group下的组信息
            unsigned int cpu = NR_CPUS;
            void *ptr;

            //检查cpu_map数组
            for (i = 0; i < gi->nr_units && cpu == NR_CPUS; i++)
                cpu = gi->cpu_map[i];
            BUG_ON(cpu == NR_CPUS);

            //为该group分配percpu内存区域。长度为该group里的cpu数目X每颗处理器的percpu递进单位。
            //函数pcpu_dfl_fc_alloc是从bootmem里取得内存，得到的是物理内存，返回物理地址的内存虚拟地址ptr
            ptr = alloc_fn(cpu, gi->nr_units * ai->unit_size, atom_size);
            if (!ptr) {
                rc = -ENOMEM;
                goto out_free_areas;
            }
            /* kmemleak tracks the percpu allocations separately */
            kmemleak_free(ptr);
            //将分配到的改组percpu内存虚拟起始地址保存在areas数组中
            areas[group] = ptr;

            //比较每个group的percpu内存地址，保存最小的内存地址，即percpu内存的起始地址
            //为后边计算group的percpu内存地址的偏移量
            base = min(ptr, base);
        }

        //为每个group中的每个cpu建立其percpu区域
        for (group = 0; group < ai->nr_groups; group++) {
            //取出该group下的组信息
            struct pcpu_group_info *gi = &ai->groups[group];
            void *ptr = areas[group];//得到该group的percpu内存起始地址

            //遍历该组中的cpu，并得到每个cpu对应的percpu内存地址
            for (i = 0; i < gi->nr_units; i++, ptr += ai->unit_size) {
                if (gi->cpu_map[i] == NR_CPUS) {
                    free_fn(ptr, ai->unit_size);//释放掉未使用的unit
                    continue;
                }

                //将静态定义的percpu变量拷贝到每个cpu的percpu内存起始地址
                memcpy(ptr, __per_cpu_load, ai->static_size);
                //为每个cpu释放掉多余的空间，多余的空间是指ai->unit_size减去静态定义变量占用空间+reserved空间+动态分配空间
                free_fn(ptr + size_sum, ai->unit_size - size_sum);
            }
        }

        //计算group的percpu内存地址的偏移量
        max_distance = 0;
        for (group = 0; group < ai->nr_groups; group++) {
            ai->groups[group].base_offset = areas[group] - base;
            max_distance = max_t(size_t, max_distance,ai->groups[group].base_offset);
        }

        //检查最大偏移量是否超过vmalloc空间的75%
        max_distance += ai->unit_size;    
        if (max_distance > VMALLOC_TOTAL * 3 / 4) {
            pr_warning("PERCPU: max_distance=0x%zx too large for vmalloc "
                        "space 0x%lx\n", max_distance,VMALLOC_TOTAL);
        }

        pr_info("PERCPU: Embedded %zu pages/cpu @%p s%zu r%zu d%zu u%zu\n",
                PFN_DOWN(size_sum), base, ai->static_size, ai->reserved_size,
                ai->dyn_size, ai->unit_size);

        //为percpu建立第一个chunk
        rc = pcpu_setup_first_chunk(ai, base);
        goto out_free;

    out_free_areas:
        for (group = 0; group < ai->nr_groups; group++)
            if (areas[group])
                free_fn(areas[group],ai->groups[group].nr_units * ai->unit_size);
    out_free:
        pcpu_free_alloc_info(ai);
        if (areas)
            memblock_free_early(__pa(areas), areas_size);
        return rc;
    }

1.1.1 收集整理该架构下的percpu信息

    static struct pcpu_alloc_info * __init pcpu_build_alloc_info(size_t reserved_size, size_t dyn_size,
                                        size_t atom_size,pcpu_fc_cpu_distance_fn_t cpu_distance_fn)
    {
        static int group_map[NR_CPUS] __initdata;
        static int group_cnt[NR_CPUS] __initdata;
        const size_t static_size = __per_cpu_end - __per_cpu_start;
        int nr_groups = 1, nr_units = 0;
        size_t size_sum, min_unit_size, alloc_size;
        int upa, max_upa, uninitialized_var(best_upa); /* units_per_alloc */
        int last_allocs, group, unit;
        unsigned int cpu, tcpu;
        struct pcpu_alloc_info *ai;
        unsigned int *cpu_map;

        /* this function may be called multiple times */
        memset(group_map, 0, sizeof(group_map));
        memset(group_cnt, 0, sizeof(group_cnt));

        //计算每个cpu所占有的percpu空间大小，包括静态空间+保留空间+动态空间
        size_sum = PFN_ALIGN(static_size + reserved_size +
                            max_t(size_t, dyn_size, PERCPU_DYNAMIC_EARLY_SIZE));
        //重新计算动态分配的percpu空间大小
        dyn_size = size_sum - static_size - reserved_size;

        //计算每个unit的大小，即每个group中的每个cpu占用的percpu内存大小为一个unit
        min_unit_size = max_t(size_t, size_sum, PCPU_MIN_UNIT_SIZE);
        //atom_size为PAGE_SIZE，即4K.将min_unit_size按4K向上舍入，例如min_unit_size=5k，则alloc_size为两个页面大小即8K，若min_unit_size=9k，则alloc_size为三个页面大小即12K
        alloc_size = roundup(min_unit_size, atom_size);
        upa = alloc_size / min_unit_size;
        while (alloc_size % upa || ((alloc_size / upa) & ~PAGE_MASK))
            upa--;
        max_upa = upa;

        //为cpu分组，将接近的cpu分到一组中，因为没有定义cpu_distance_fn函数体，所以所有的cpu分到一个组中。
        //可以得到所有的cpu都是group=0，group_cnt[0]即是该组中的cpu个数
        for_each_possible_cpu(cpu) {
            group = 0;
    next_group:
            for_each_possible_cpu(tcpu) {
                if (cpu == tcpu)
                    break;
                //cpu_distance_fn=NULL
                if (group_map[tcpu] == group && cpu_distance_fn &&
                    (cpu_distance_fn(cpu, tcpu) > LOCAL_DISTANCE ||
                    cpu_distance_fn(tcpu, cpu) > LOCAL_DISTANCE)) {
                        group++;
                        nr_groups = max(nr_groups, group + 1);
                        goto next_group;
                    }
            }
            group_map[cpu] = group;
            group_cnt[group]++;
        }

        /*
        * Expand unit size until address space usage goes over 75%
        * and then as much as possible without using more address
        * space.
        */
        last_allocs = INT_MAX;
        for (upa = max_upa; upa; upa--) {
            int allocs = 0, wasted = 0;

            if (alloc_size % upa || ((alloc_size / upa) & ~PAGE_MASK))
                continue;

            for (group = 0; group < nr_groups; group++) {
                int this_allocs = DIV_ROUND_UP(group_cnt[group], upa);
                allocs += this_allocs;
                wasted += this_allocs * upa - group_cnt[group];
            }

            /*
                * Don't accept if wastage is over 1/3. The
                * greater-than comparison ensures upa==1 always
                * passes the following check.
            */
            if (wasted > num_possible_cpus() / 3)
                continue;

            /* and then don't consume more memory */
            if (allocs > last_allocs)
                break;
            last_allocs = allocs;
            best_upa = upa;
        }
        upa = best_upa;

        //计算每个group中的cpu个数
        for (group = 0; group < nr_groups; group++)
            nr_units += roundup(group_cnt[group], upa);

        //分配pcpu_alloc_info结构空间，并初始化
        ai = pcpu_alloc_alloc_info(nr_groups, nr_units);
        if (!ai)
            return ERR_PTR(-ENOMEM);

        //为每个group的cpu_map指针赋值为group[0]，group[0]中的cpu_map中的值初始化为NR_CPUS
        cpu_map = ai->groups[0].cpu_map;
        for (group = 0; group < nr_groups; group++) {
            ai->groups[group].cpu_map = cpu_map;
            cpu_map += roundup(group_cnt[group], upa);
        }

        ai->static_size = static_size; //静态percpu变量空间
        ai->reserved_size = reserved_size;//保留percpu变量空间
        ai->dyn_size = dyn_size; //动态分配的percpu变量空间
        ai->unit_size = alloc_size / upa; //每个cpu占用的percpu变量空间
        ai->atom_size = atom_size; //PAGE_SIZE
        ai->alloc_size = alloc_size; //实际分配的空间

        for (group = 0, unit = 0; group_cnt[group]; group++) {
            struct pcpu_group_info *gi = &ai->groups[group];
            //设置组内的相对于0地址偏移量，后边会设置真正的对于percpu起始地址的偏移量
            gi->base_offset = unit * ai->unit_size;
             //设置cpu_map数组，数组保存该组中的cpu id号。以及设置组中的cpu个数gi->nr_units
            //gi->nr_units=0,cpu=0
            //gi->nr_units=1,cpu=1
            //gi->nr_units=2,cpu=2
            //gi->nr_units=3,cpu=3
            for_each_possible_cpu(cpu)
                if (group_map[cpu] == group)
                    gi->cpu_map[gi->nr_units++] = cpu;
            gi->nr_units = roundup(gi->nr_units, upa);
            unit += gi->nr_units;
        }
        BUG_ON(unit != nr_units);

        return ai;
    }

    1.1.1.1 分配pcpu_alloc_info结构，并初始化
    struct pcpu_alloc_info * __init pcpu_alloc_alloc_info(int nr_groups,int nr_units)
    {
        struct pcpu_alloc_info *ai;
        size_t base_size, ai_size;
        void *ptr;
        int unit;
        
        //根据group数以及，group[0]中cpu个数确定pcpu_alloc_info结构体大小ai_size
        base_size = ALIGN(sizeof(*ai) + nr_groups * sizeof(ai->groups[0]),
                    __alignof__(ai->groups[0].cpu_map[0]));

        ai_size = base_size + nr_units * sizeof(ai->groups[0].cpu_map[0]);
        
        //分配空间
        ptr = memblock_virt_alloc_nopanic(PFN_ALIGN(ai_size), 0);
        if (!ptr)
            return NULL;
        ai = ptr;
        ptr += base_size;//指针指向group的cpu_map数组地址处
        
        ai->groups[0].cpu_map = ptr;
        
        //初始化group[0]的cpu_map数组值为NR_CPUS
        for (unit = 0; unit < nr_units; unit++)
            ai->groups[0].cpu_map[unit] = NR_CPUS;
        
        ai->nr_groups = nr_groups;//group个数
        ai->__ai_size = PFN_ALIGN(ai_size);//整个pcpu_alloc_info结构体的大小
        
        return ai;
    }

    1.1.2 为percpu建立第一个chunk
    int __init pcpu_setup_first_chunk(const struct pcpu_alloc_info *ai,void *base_addr)
    {
        static char cpus_buf[4096] __initdata;
        static int smap[PERCPU_DYNAMIC_EARLY_SLOTS] __initdata;
        static int dmap[PERCPU_DYNAMIC_EARLY_SLOTS] __initdata;
        size_t dyn_size = ai->dyn_size;
        size_t size_sum = ai->static_size + ai->reserved_size + dyn_size;
        struct pcpu_chunk *schunk, *dchunk = NULL;
        unsigned long *group_offsets;
        size_t *group_sizes;
        unsigned long *unit_off;
        unsigned int cpu;
        int *unit_map;
        int group, unit, i;
        
        cpumask_scnprintf(cpus_buf, sizeof(cpus_buf), cpu_possible_mask);
        
    #define PCPU_SETUP_BUG_ON(cond) do { \
            if (unlikely(cond)) { \
                pr_emerg("PERCPU: failed to initialize, %s", #cond); \
                pr_emerg("PERCPU: cpu_possible_mask=%s\n", cpus_buf); \
                pcpu_dump_alloc_info(KERN_EMERG, ai); \
                BUG(); \
            } \
        } while (0)
        
        //健康检查
        PCPU_SETUP_BUG_ON(ai->nr_groups <= 0);
    #ifdef CONFIG_SMP
        PCPU_SETUP_BUG_ON(!ai->static_size);
        PCPU_SETUP_BUG_ON((unsigned long)__per_cpu_start & ~PAGE_MASK);
    #endif
        PCPU_SETUP_BUG_ON(!base_addr);
        PCPU_SETUP_BUG_ON((unsigned long)base_addr & ~PAGE_MASK);
        PCPU_SETUP_BUG_ON(ai->unit_size < size_sum);
        PCPU_SETUP_BUG_ON(ai->unit_size & ~PAGE_MASK);
        PCPU_SETUP_BUG_ON(ai->unit_size < PCPU_MIN_UNIT_SIZE);
        PCPU_SETUP_BUG_ON(ai->dyn_size < PERCPU_DYNAMIC_EARLY_SIZE);
        PCPU_SETUP_BUG_ON(pcpu_verify_alloc_info(ai) < 0);
        
        //为group相关percpu信息保存数组分配空间
        group_offsets = memblock_virt_alloc(ai->nr_groups *sizeof(group_offsets[0]), 0);
        group_sizes = memblock_virt_alloc(ai->nr_groups *sizeof(group_sizes[0]), 0);
        //为每个cpu相关percpu信息保存数组分配空间
        unit_map = memblock_virt_alloc(nr_cpu_ids * sizeof(unit_map[0]), 0);
        unit_off = memblock_virt_alloc(nr_cpu_ids * sizeof(unit_off[0]), 0);
        
        //对unit_map、pcpu_low_unit_cpu和pcpu_high_unit_cpu变量初始化
        for (cpu = 0; cpu < nr_cpu_ids; cpu++)
            unit_map[cpu] = UINT_MAX;    
        pcpu_low_unit_cpu = NR_CPUS;
        pcpu_high_unit_cpu = NR_CPUS;
        
        //遍历每一group的每一个cpu
        for (group = 0, unit = 0; group < ai->nr_groups; group++, unit += i) {
            const struct pcpu_group_info *gi = &ai->groups[group];
            //取得该组处理器的percpu内存空间的偏移量
            group_offsets[group] = gi->base_offset;
            //取得该组处理器的percpu内存空间占用的虚拟地址空间大小，即包含改组中每个cpu所占的percpu空间
            group_sizes[group] = gi->nr_units * ai->unit_size;
            //遍历该group中的cpu
            for (i = 0; i < gi->nr_units; i++) {
                cpu = gi->cpu_map[i];//得到该group中的cpu id号
                if (cpu == NR_CPUS)
                    continue;
        
                PCPU_SETUP_BUG_ON(cpu > nr_cpu_ids);
                PCPU_SETUP_BUG_ON(!cpu_possible(cpu));
                PCPU_SETUP_BUG_ON(unit_map[cpu] != UINT_MAX);
                 
                //计算每个cpu的跨group的编号，保存在unit_map数组中
                unit_map[cpu] = unit + i;
                //计算每个cpu的在整个系统percpu内存空间中的偏移量，保存到数组unit_off中
                unit_off[cpu] = gi->base_offset + i * ai->unit_size;
        
                /* determine low/high unit_cpu */
                if (pcpu_low_unit_cpu == NR_CPUS || unit_off[cpu] < unit_off[pcpu_low_unit_cpu])
                    pcpu_low_unit_cpu = cpu;
                if (pcpu_high_unit_cpu == NR_CPUS || unit_off[cpu] > unit_off[pcpu_high_unit_cpu])
                    pcpu_high_unit_cpu = cpu;
            }
        }
        //pcpu_nr_units变量保存系统中有多少个cpu的percpu内存空间
        pcpu_nr_units = unit;
        
        for_each_possible_cpu(cpu)
            PCPU_SETUP_BUG_ON(unit_map[cpu] == UINT_MAX);
        
    #undef PCPU_SETUP_BUG_ON
        pcpu_dump_alloc_info(KERN_DEBUG, ai);

        //记录下全局参数，留在pcpu_alloc时使用
        pcpu_nr_groups = ai->nr_groups;//系统中group数量
        pcpu_group_offsets = group_offsets;//记录每个group的percpu内存偏移量数组
        pcpu_group_sizes = group_sizes;//记录每个group的percpu内存空间大小数组
        pcpu_unit_map = unit_map;//整个系统中cpu(跨group)的编号数组
        pcpu_unit_offsets = unit_off;//每个cpu的percpu内存空间偏移量
        pcpu_unit_pages = ai->unit_size >> PAGE_SHIFT;//每个cpu的percpu内存虚拟空间所占的页面数量
        pcpu_unit_size = pcpu_unit_pages << PAGE_SHIFT;//每个cpu的percpu内存虚拟空间大小
        pcpu_atom_size = ai->atom_size;//PAGE_SIZE

        //计算pcpu_chunk结构的大小，加上populated域的大小
        pcpu_chunk_struct_size = sizeof(struct pcpu_chunk) +
                                BITS_TO_LONGS(pcpu_unit_pages) * sizeof(unsigned long);
        
        //计算pcpu_nr_slots，即pcpu_slot数组的组项数量
        pcpu_nr_slots = __pcpu_size_to_slot(pcpu_unit_size) + 2;
        //为pcpu_slot数组分配空间，不同size的chunck挂在不同“pcpu_slot”项目中
        pcpu_slot = memblock_virt_alloc(pcpu_nr_slots * sizeof(pcpu_slot[0]), 0);
        for (i = 0; i < pcpu_nr_slots; i++)
            INIT_LIST_HEAD(&pcpu_slot[i]);
        
        //构建静态chunck,即pcpu_reserved_chunk
        schunk = memblock_virt_alloc(pcpu_chunk_struct_size, 0);
        INIT_LIST_HEAD(&schunk->list);
        schunk->base_addr = base_addr;//整个系统中percpu内存的起始地址
        schunk->map = smap;//初始化为一个静态数组
        schunk->map_alloc = ARRAY_SIZE(smap);//PERCPU_DYNAMIC_EARLY_SLOTS=128
        schunk->immutable = true;
        //物理内存已经分配这里标志之
        //若pcpu_unit_pages=8即每个cpu占用的percpu空间为8页的空间，则populated域被设置为0xff
        bitmap_fill(schunk->populated, pcpu_unit_pages);
        
        if (ai->reserved_size) {
            //如果存在percpu保留空间，在指定reserved分配时作为空闲空间使用
            schunk->free_size = ai->reserved_size;            
            pcpu_reserved_chunk = schunk;
            //静态chunk的大小限制包括，定义的静态变量的空间+保留的空间
            pcpu_reserved_chunk_limit = ai->static_size + ai->reserved_size;
        } else {
            //若不存在保留空间，则将动态分配空间作为空闲空间使用
            schunk->free_size = dyn_size;
            dyn_size = 0;//覆盖掉动态分配空间
        }

        //记录静态chunk中空闲可使用的percpu空间大小
        schunk->contig_hint = schunk->free_size;
        //map数组保存空间的使用情况，负数为已使用的空间，正数表示为以后可以分配的空间
        //map_used记录chunk中存在几个map项
        schunk->map[schunk->map_used++] = -ai->static_size;
        if (schunk->free_size)
            schunk->map[schunk->map_used++] = schunk->free_size;
        
        //构建动态chunk分配空间
        if (dyn_size) {
            dchunk = memblock_virt_alloc(pcpu_chunk_struct_size, 0);
            INIT_LIST_HEAD(&dchunk->list);
            dchunk->base_addr = base_addr;//整个系统中percpu内存的起始地址
            dchunk->map = dmap;//初始化为一个静态数组
            dchunk->map_alloc = ARRAY_SIZE(dmap);//PERCPU_DYNAMIC_EARLY_SLOTS=128
            dchunk->immutable = true;
            //记录下来分配的物理页
            bitmap_fill(dchunk->populated, pcpu_unit_pages);
             //设置动态chunk中的空闲可分配空间大小
            dchunk->contig_hint = dchunk->free_size = dyn_size;
            //map数组保存空间的使用情况，负数为已使用的空间（静态变量空间和reserved空间），正数表示为以后可以分配的空间
            dchunk->map[dchunk->map_used++] = -pcpu_reserved_chunk_limit;
            dchunk->map[dchunk->map_used++] = dchunk->free_size;
        }
        
        //把第一个chunk链接进对应的slot链表，reserverd的空间有自己单独的chunk：pcpu_reserved_chunk
        pcpu_first_chunk = dchunk ?: schunk;
        pcpu_chunk_relocate(pcpu_first_chunk, -1);
     
        //pcpu_base_addr记录整个系统中percpu内存的起始地址
        pcpu_base_addr = base_addr;
        return 0;
    }

    //fls找到size中最高的置1的位，返回该位号
    //例：fls(0) = 0, fls(1) = 1, fls(0x80000000) = 32.
    //若size=32768=0x8000，则fls(32768)=16
    //若highbit=0-4，则slot个数均为1
    #define PCPU_SLOT_BASE_SHIFT    5
    static int __pcpu_size_to_slot(int size)
    {
        int highbit = fls(size);
        return max(highbit - PCPU_SLOT_BASE_SHIFT + 2, 1);
    }

    static void pcpu_chunk_relocate(struct pcpu_chunk *chunk, int oslot)
    {
        //返回该chunk对应的要挂入的slot数组的下标
        int nslot = pcpu_chunk_slot(chunk);
            
        //静态chunk不需挂入pcpu_slot数组中
        if (chunk != pcpu_reserved_chunk && oslot != nslot) {
            if (oslot < nslot)
                list_move(&chunk->list, &pcpu_slot[nslot]);
            else
                list_move_tail(&chunk->list, &pcpu_slot[nslot]);
        }
    }

    static int pcpu_chunk_slot(const struct pcpu_chunk *chunk)
    {
        //该chunk中的空闲空间小于sizeof(int)，或者最大的空闲空间块小于sizeof(int)，返回0
        if (chunk->free_size < sizeof(int) || chunk->contig_hint < sizeof(int))
            return 0;
     
        return pcpu_size_to_slot(chunk->free_size);
    }

    static int pcpu_size_to_slot(int size)
    {
        //若size等于每个cpu占用的percpu内存空间大小，返回最后一项pcpu_slot数组下标
        if (size == pcpu_unit_size)
            return pcpu_nr_slots - 1;
        
        //否则根据size返回在pcpu_slot数组中的下标
        return __pcpu_size_to_slot(size);
    }


    四、每CPU变量提供的函数和宏
    1.编译期间分配percpu，即分配静态percpu，函数原型:
    DEFINE_PER_CPU(type, name)

    #define DEFINE_PER_CPU(type, name) DEFINE_PER_CPU_SECTION(type, name, "")

    #define DEFINE_PER_CPU_SECTION(type, name, sec) \
            __PCPU_ATTRS(sec) PER_CPU_DEF_ATTRIBUTES \
            __typeof__(type) name

    #define __PCPU_ATTRS(sec) \
            __percpu __attribute__((section(PER_CPU_BASE_SECTION sec))) \
            PER_CPU_ATTRIBUTES

    #define PER_CPU_BASE_SECTION ".data..percpu"
    #define PER_CPU_ATTRIBUTES
    #define PER_CPU_DEF_ATTRIBUTES

    根据以上宏定义展开之，可以得到
    __attribute__((section(.data..percpu))) __typeof__(type) name
    可见宏“DEFINE_PER_CPU(type, name)”的作用就是将类型为“type”的“name”变量放到“.data..percpu”数据段。
    而在/include/asm-generic/vmlinux.lds.h中定义：
    链接器会把所有静态定义的per-cpu变量统一放到".data..percpu" section中, 链接器生成__per_cpu_start和__per_cpu_end两个变量来表示该section的起始和结束地址, 为了配合链接器的行为, linux内核源码中针对以上链接脚本声明了外部变量 extern char __per_cpu_load[], __per_cpu_start[], __per_cpu_end[];
    #define PERCPU_INPUT(cacheline)                                        \
        VMLINUX_SYMBOL(__per_cpu_start) = .; \
        *(.data..percpu..first) \
        . = ALIGN(PAGE_SIZE); \
        *(.data..percpu..page_aligned) \
        . = ALIGN(cacheline); \
        *(.data..percpu..readmostly) \
        . = ALIGN(cacheline); \
        *(.data..percpu) \
        *(.data..percpu..shared_aligned) \
        VMLINUX_SYMBOL(__per_cpu_end) = .;

    #define PERCPU_VADDR(cacheline, vaddr, phdr) \
            VMLINUX_SYMBOL(__per_cpu_load) = .; \
            .data..percpu vaddr : AT(VMLINUX_SYMBOL(__per_cpu_load) \
                                    - LOAD_OFFSET) { \
                    PERCPU_INPUT(cacheline) \
            } phdr \
            . = VMLINUX_SYMBOL(__per_cpu_load) + SIZEOF(.data..percpu);

    我们知道在系统对percpu初始化的时候，会将静态定义的percpu变量(内核映射".data.percpu"section中的变量数据)拷贝到每个cpu的percpu内存空间中，静态定义的percpu变量的起始地址为__per_cpu_load，即
    memcpy(ptr, __per_cpu_load, ai->static_size);

    2. 访问percpu变量
    (1) per_cpu(var, cpu)获取编号cpu的处理器上面的变量var的副本
    (2) get_cpu_var(var)获取本处理器上面的变量var的副本，该函数关闭进程抢占，主要由__get_cpu_var来完成具体的访问
    (3) get_cpu_ptr(var) 获取本处理器上面的变量var的副本的指针，该函数关闭进程抢占，主要由__get_cpu_var来完成具体的访问
    (4) put_cpu_var(var) & put_cpu_ptr(var)表示每CPU变量的访问结束，恢复进程抢占
    (5) __get_cpu_var(var) 获取本处理器上面的变量var的副本，该函数不关闭进程抢占

    注意：关闭内核抢占可确保在对per-cpu变量操作的临界区中, 当前进程不会被换出处理器, 在put_cpu_var中恢复内核调度器的可抢占性.

    //详细代码解析：
    (1) per_cpu
    #define per_cpu(var, cpu) (*SHIFT_PERCPU_PTR(&(var), per_cpu_offset(cpu)))

    #define per_cpu_offset(x) (__per_cpu_offset[x])

    #define SHIFT_PERCPU_PTR(__p, __offset) ({ \
            __verify_pcpu_ptr((__p)); \
            RELOC_HIDE((typeof(*(__p)) __kernel __force *)(__p), (__offset)); \
            })

    #define RELOC_HIDE(ptr, off)             \
            ({ unsigned long __ptr;                                            \
            __ptr = (unsigned long) (ptr);                                    \
            (typeof(ptr)) (__ptr + (off)); })

    per_cpu(var, cpu)通过以上的宏展开，就是返回*(__per_cpu_offset[cpu]+&(var))的值。__per_cpu_offset数组记录每个cpu的percpu内存空间距离内核静态percpu内存区起始地址(即".data..percpu"段的起始地址__per_cpu_start)的偏移量，加上var在内核中的内存地址(因为是静态percpu变量，所以地址肯定在".data..percpu"段中)，就得到var在该cpu下的percpu内存区的地址，取地址下的值即可得到该var变量的值。

    (2) get_cpu_var/__get_cpu_var
    #define get_cpu_var(var) (*({ \
            preempt_disable(); \ //关闭进程抢占
            &__get_cpu_var(var); }))

    #define __get_cpu_var(var) (*this_cpu_ptr(&(var)))
    #define this_cpu_ptr(ptr) __this_cpu_ptr(ptr)
    #define __this_cpu_ptr(ptr) SHIFT_PERCPU_PTR(ptr, __my_cpu_offset)
    #define my_cpu_offset __my_cpu_offset
    #define __my_cpu_offset per_cpu_offset(raw_smp_processor_id())
    #define per_cpu_offset(x) (__per_cpu_offset[x])
    通过一系列宏调用，最终函数还是通过*(__per_cpu_offset[raw_smp_processor_id()]+&(var))来获得本地处理器上的var变量的值。

    (3) get_cpu_ptr
    #define get_cpu_ptr(var) ({ \
            preempt_disable(); \
            this_cpu_ptr(var); })
    获取本处理器上面的变量var的副本的指针，该函数关闭进程抢占.

    (4)put_cpu_ptr/put_cpu_var,恢复进程抢占
    #define put_cpu_var(var) do { \
            (void)&(var); \
            preempt_enable(); \
            } while (0)
             
    #define put_cpu_ptr(var) do { \
            (void)(var); \
            preempt_enable(); \
            } while (0)

    3.动态分配percpu空间：void * alloc_percpu(type)
    #define alloc_percpu(type) \
            (typeof(type) __percpu *)__alloc_percpu(sizeof(type), __alignof__(type))

    void __percpu *__alloc_percpu(size_t size, size_t align)
    {
        return pcpu_alloc(size, align, false);
    }

    3.1 动态分配percpu
    static void __percpu *pcpu_alloc(size_t size, size_t align, bool reserved)
    {
        static int warn_limit = 10;
        struct pcpu_chunk *chunk;
        const char *err;
        int slot, off, new_alloc;
        unsigned long flags;
        void __percpu *ptr;
            
        if (unlikely(!size || size > PCPU_MIN_UNIT_SIZE || align > PAGE_SIZE)) {
            WARN(true, "illegal size (%zu) or align (%zu) for "
                "percpu allocation\n", size, align);
            return NULL;
        }
        
        mutex_lock(&pcpu_alloc_mutex);
        spin_lock_irqsave(&pcpu_lock, flags);
            
        //若指定reserved分配，则从pcpu_reserved_chunk进行
        if (reserved && pcpu_reserved_chunk) {
            chunk = pcpu_reserved_chunk;//找到静态percpu的chunk
            
            //检查要分配的空间size是否超出该chunk的所具有的最大的空闲size
            if (size > chunk->contig_hint) {
                err = "alloc from reserved chunk failed";
                goto fail_unlock;
            }
        
            //检查是否要扩展chunk的的map数组，map数组默认设置为128项
            while ((new_alloc = pcpu_need_to_extend(chunk))) {
                spin_unlock_irqrestore(&pcpu_lock, flags);
                //对map数组进行扩展
                if (pcpu_extend_area_map(chunk, new_alloc) < 0) {
                    err = "failed to extend area map of reserved chunk";
                    goto fail_unlock_mutex;
                }
                spin_lock_irqsave(&pcpu_lock, flags);
            }
        
            //从该chunk分配出size大小的空间，返回该size空间在chunk中的偏移量off
            //然后重新将该chunk挂到slot数组对应链表中
            off = pcpu_alloc_area(chunk, size, align);
            if (off >= 0)
                goto area_found;
        
            err = "alloc from reserved chunk failed";
            goto fail_unlock;
        }
            
    restart:
        //根据需要分配内存块的大小索引slot数组找到对应链表
        for (slot = pcpu_size_to_slot(size); slot < pcpu_nr_slots; slot++) {
            list_for_each_entry(chunk, &pcpu_slot[slot], list) {
                if (size > chunk->contig_hint) //在该链表中进一步寻找符合尺寸要求的chunk
                    continue;
                 //chunck用数组map记录每次分配的内存块，若该数组项数用完(默认为128项)，
                //但是若该chunk仍然还有空闲空间可分配，则需要增长该map数组项数来记录可分配的空间
                new_alloc = pcpu_need_to_extend(chunk);
                if (new_alloc) {
                    spin_unlock_irqrestore(&pcpu_lock, flags);
                    //扩展map数组
                    if (pcpu_extend_area_map(chunk,new_alloc) < 0) {
                        err = "failed to extend area map";
                        goto fail_unlock_mutex;
                    }
                    spin_lock_irqsave(&pcpu_lock, flags);

                    goto restart;
                }
                 //从该chunk分配出size大小的空间，返回该size空间在chunk中的偏移量off
                //然后重新将该chunk挂到slot数组对应链表中
                off = pcpu_alloc_area(chunk, size, align);
                if (off >= 0)
                    goto area_found;
            }
        }
        
        //到这里表示没有找到合适的chunk，需要重新创建一个新的chunk
        spin_unlock_irqrestore(&pcpu_lock, flags);
        //创建一个新的chunk，这里进行的是虚拟地址空间的分配
        chunk = pcpu_create_chunk();
        if (!chunk) {
            err = "failed to allocate new chunk";
            goto fail_unlock_mutex;
        }
        
        spin_lock_irqsave(&pcpu_lock, flags);
        //把一个全新的chunk挂到slot数组对应链表中
        pcpu_chunk_relocate(chunk, -1);
        goto restart;
        
    area_found:
        spin_unlock_irqrestore(&pcpu_lock, flags);
        
        //这里要检查该段区域对应物理页是否已经分配
        if (pcpu_populate_chunk(chunk, off, size)) {
            spin_lock_irqsave(&pcpu_lock, flags);
            pcpu_free_area(chunk, off);
            err = "failed to populate";
            goto fail_unlock;
        }
        
        mutex_unlock(&pcpu_alloc_mutex);
        
        /*
        #define __addr_to_pcpu_ptr(addr)     \
            (void __percpu *)((unsigned long)(addr) - \
            (unsigned long)pcpu_base_addr +                     \
            (unsigned long)__per_cpu_start)
        */
        //chunk->base_addr + off表示分配该size空间的起始percpu内存地址
        //最终返回的地址即__per_cpu_start+off，即得到该动态分配percpu变量在内核镜像中的一个虚拟内存地址。
        //实际上该动态分配percpu变量并不在此地址上，只是为了以后通过per_cpu(var, cpu)引用该变量时，
        //与静态percpu变量一致，因为静态percpu变量在内核镜像中是有分配内存虚拟地址的(在.data..percpu段中)。
        //使用per_cpu(var, cpu)时，该动态分配percpu变量的内核镜像中的虚拟地址(假的地址，为了跟静态percpu变量一致)，加上本cpu所在percpu空间与.data..percpu段的偏移量，
        //即得到该动态分配percpu变量在本cpu副本中的内存地址
        ptr = __addr_to_pcpu_ptr(chunk->base_addr + off);
        kmemleak_alloc_percpu(ptr, size);
        return ptr;
        
    fail_unlock:
        spin_unlock_irqrestore(&pcpu_lock, flags);
    fail_unlock_mutex:
        mutex_unlock(&pcpu_alloc_mutex);
        if (warn_limit) {
            pr_warning("PERCPU: allocation failed, size=%zu align=%zu, ""%s\n", size, align, err);
            dump_stack();
            if (!--warn_limit)
                pr_info("PERCPU: limit reached, disable warning\n");
        }
        return NULL;
    }

    3.1.1 检查chunk的map数组是否需要扩展
    //#define PCPU_DFL_MAP_ALLOC    16
    static int pcpu_need_to_extend(struct pcpu_chunk *chunk)
    {
        int new_alloc;
        
        //map_alloc默认设置为128，只有map_used记录超过126时才会进行map数组扩展
        if (chunk->map_alloc >= chunk->map_used + 2)
            return 0;
            
        new_alloc = PCPU_DFL_MAP_ALLOC;//16

        //计算该chunk的map数组新的大小，并返回
        while (new_alloc < chunk->map_used + 2)
            new_alloc *= 2;
            
        return new_alloc;
    }

    3.1.2 对map数组的大小进行扩展
    static int pcpu_extend_area_map(struct pcpu_chunk *chunk, int new_alloc)
    {
        int *old = NULL, *new = NULL;
        size_t old_size = 0, new_size = new_alloc * sizeof(new[0]);
        unsigned long flags;
        
        //为新的map数组大小分配内存空间    
        new = pcpu_mem_zalloc(new_size);
        if (!new)
            return -ENOMEM;
            
        /* acquire pcpu_lock and switch to new area map */
        spin_lock_irqsave(&pcpu_lock, flags);
            
        if (new_alloc <= chunk->map_alloc)
            goto out_unlock;
            
        old_size = chunk->map_alloc * sizeof(chunk->map[0]);
        old = chunk->map;
        
        //复制老的map数组信息到new
        memcpy(new, old, old_size);
        
        //重新设置map数组，完成map数组的扩展
        chunk->map_alloc = new_alloc;
        chunk->map = new;
        new = NULL;
        
    out_unlock:
        spin_unlock_irqrestore(&pcpu_lock, flags);
        
        pcpu_mem_free(old, old_size);
        pcpu_mem_free(new, new_size);
            
        return 0;
    }

    3.1.3 从chunk的map数组中分配size大小空间，返回该size的偏移值
    static int pcpu_alloc_area(struct pcpu_chunk *chunk, int size, int align)
    {
        int oslot = pcpu_chunk_slot(chunk);
        int max_contig = 0;
        int i, off;
        
        //遍历该chunk的map中记录的空间，map中负数为已经使用的空间，正数为可以分配使用的空间
        for (i = 0, off = 0; i < chunk->map_used; off += abs(chunk->map[i++])) {
            //is_last为1表示已经扫描了chunk中所有记录的空间，并且是最后一个map组项
            bool is_last = i + 1 == chunk->map_used;
            int head, tail;
            
            //对map项中记录的percpu空间大小进行对齐，可能会产生的一个偏移量head
            head = ALIGN(off, align) - off;
            BUG_ON(i == 0 && head != 0);
             
             //map中记录的负数表示已经使用的percpu空间，继续下一个
            if (chunk->map[i] < 0)
                continue;
                
            //若map中的空间大小小于要分配的空间大小，继续下一个
            if (chunk->map[i] < head + size) {
                //更新该chunk中可使用的空间大小
                max_contig = max(chunk->map[i], max_contig);
                continue;
            }
        
            //如果head不为0，并且head很小(小于sizeof(int))，或者前一个map的可用空间大于0(但是chunk->map[i - 1] < head+size)
            //如果前一个map项>0，则将head合并到前一个map中
            //如果前一个map项<0,则将head合并到前一个map，并且是负数，不可用空间，当前chunk空闲size减去这head大小的空间
            if (head && (head < sizeof(int) || chunk->map[i - 1] > 0)) {
                if (chunk->map[i - 1] > 0)
                    chunk->map[i - 1] += head;
                else {
                    chunk->map[i - 1] -= head;
                    chunk->free_size -= head;
                }
                //当前map减去已经与前一个map合并的head大小的空间
                chunk->map[i] -= head;
                off += head;//偏移要加上head
                head = 0;//合并之后，head清零
            }
        
            //计算要分配空间的尾部
            tail = chunk->map[i] - head - size;
            if (tail < sizeof(int))
                tail = 0;
        
            //如果head不为0，或者tail不为0，则要将当前map分割
            if (head || tail) {
                pcpu_split_block(chunk, i, head, tail);
                //如果head不为0，tail不为0，经过split之后，map[i]记录head，map[i+1]记录要分配的size，map[i+2]记录tail。
                if (head) {
                    i++; //移到记录要分配size空间的map项
                    off += head;//偏移要加上head，表示从head之后开始
                    //i-1表示head所在的那个map项，与max_contig比较大小，为下边更新chunk的最大空闲空间
                    max_contig = max(chunk->map[i - 1], max_contig);
                }
                //i+1表示tail所在的那个map项，比较与max_contig的大小，为下边更新chunk的最大空闲空间
                if (tail)
                    max_contig = max(chunk->map[i + 1], max_contig);
            }
        
            //更新chunk的最大空闲空间
            if (is_last)
                chunk->contig_hint = max_contig; /* fully scanned */
            else
                chunk->contig_hint = max(chunk->contig_hint,max_contig);
        
            chunk->free_size -= chunk->map[i];//chunk中的空闲空间大小递减
            chunk->map[i] = -chunk->map[i];//变成负数表示该map中的size大小已分配
            
            //重新计算chunk在slot中的位置
            pcpu_chunk_relocate(chunk, oslot);
            return off;
        }
        
        chunk->contig_hint = max_contig; /* fully scanned */
        pcpu_chunk_relocate(chunk, oslot);
        
        /* tell the upper layer that this chunk has no matching area */
        return -1;
    }

    3.1.4 将map数组进行分割
    static void pcpu_split_block(struct pcpu_chunk *chunk, int i,int head, int tail)
    {
        //若head、tail都不为0，则要添加两个map，有一个不为0则添加一个map
        int nr_extra = !!head + !!tail;
        
        BUG_ON(chunk->map_alloc < chunk->map_used + nr_extra);
        
        //首先将该当前要分割的map后边的数据拷贝
        memmove(&chunk->map[i + nr_extra], &chunk->map[i],sizeof(chunk->map[0]) * (chunk->map_used - i));
        chunk->map_used += nr_extra;//map数组的使用个数更新
        
        //如果head不为0，则i+1的map项保存chunk->map[i] - head的大小，当前的map保存head的大小
        if (head) {
            chunk->map[i + 1] = chunk->map[i] - head;
            chunk->map[i++] = head;
        }

        //如果tail不为0，将记录(chunk->map[i] - head)大小的map项减去tail，即得到要分配size空间
        //最后一个map保存剩余的tail大小
        if (tail) {
            chunk->map[i++] -= tail;//得到size空间大小的map项
            chunk->map[i] = tail;
        }
    }

    五、结构图
    参见附件

##参考

* 深入linux 设备驱动程序内核机制
* http://blog.chinaunix.net/uid-27717694-id-4252214.html 

##附录
```
/* Linux/include/linux/percpu-defs.h 	*/
/*
 * linux/percpu-defs.h - basic definitions for percpu areas
 *
 * DO NOT INCLUDE DIRECTLY OUTSIDE PERCPU IMPLEMENTATION PROPER.
 *
 * This file is separate from linux/percpu.h to avoid cyclic inclusion
 * dependency from arch header files.  Only to be included from
 * asm/percpu.h.
 *
 * This file includes macros necessary to declare percpu sections and
 * variables, and definitions of percpu accessors and operations.  It
 * should provide enough percpu features to arch header files even when
 * they can only include asm/percpu.h to avoid cyclic inclusion dependency.
 */

#ifndef _LINUX_PERCPU_DEFS_H
#define _LINUX_PERCPU_DEFS_H

#ifdef CONFIG_SMP

#ifdef MODULE
#define PER_CPU_SHARED_ALIGNED_SECTION ""
#define PER_CPU_ALIGNED_SECTION ""
#else
#define PER_CPU_SHARED_ALIGNED_SECTION "..shared_aligned"
#define PER_CPU_ALIGNED_SECTION "..shared_aligned"
#endif
#define PER_CPU_FIRST_SECTION "..first"

#else

#define PER_CPU_SHARED_ALIGNED_SECTION ""
#define PER_CPU_ALIGNED_SECTION "..shared_aligned"
#define PER_CPU_FIRST_SECTION ""

#endif

/*
 * Base implementations of per-CPU variable declarations and definitions, where
 * the section in which the variable is to be placed is provided by the
 * 'sec' argument.  This may be used to affect the parameters governing the
 * variable's storage.
 *
 * NOTE!  The sections for the DECLARE and for the DEFINE must match, lest
 * linkage errors occur due the compiler generating the wrong code to access
 * that section.
 */
#define __PCPU_ATTRS(sec)                                               \
        __percpu __attribute__((section(PER_CPU_BASE_SECTION sec)))     \
        PER_CPU_ATTRIBUTES

#define __PCPU_DUMMY_ATTRS                                              \
        __attribute__((section(".discard"), unused))

/*
 * s390 and alpha modules require percpu variables to be defined as
 * weak to force the compiler to generate GOT based external
 * references for them.  This is necessary because percpu sections
 * will be located outside of the usually addressable area.
 *
 * This definition puts the following two extra restrictions when
 * defining percpu variables.
 *
 * 1. The symbol must be globally unique, even the static ones.
 * 2. Static percpu variables cannot be defined inside a function.
 *
 * Archs which need weak percpu definitions should define
 * ARCH_NEEDS_WEAK_PER_CPU in asm/percpu.h when necessary.
 *
 * To ensure that the generic code observes the above two
 * restrictions, if CONFIG_DEBUG_FORCE_WEAK_PER_CPU is set weak
 * definition is used for all cases.
 */
#if defined(ARCH_NEEDS_WEAK_PER_CPU) || defined(CONFIG_DEBUG_FORCE_WEAK_PER_CPU)
/*
 * __pcpu_scope_* dummy variable is used to enforce scope.  It
 * receives the static modifier when it's used in front of
 * DEFINE_PER_CPU() and will trigger build failure if
 * DECLARE_PER_CPU() is used for the same variable.
 *
 * __pcpu_unique_* dummy variable is used to enforce symbol uniqueness
 * such that hidden weak symbol collision, which will cause unrelated
 * variables to share the same address, can be detected during build.
 */
#define DECLARE_PER_CPU_SECTION(type, name, sec)                        \
        extern __PCPU_DUMMY_ATTRS char __pcpu_scope_##name;             \
        extern __PCPU_ATTRS(sec) __typeof__(type) name

#define DEFINE_PER_CPU_SECTION(type, name, sec)                         \
        __PCPU_DUMMY_ATTRS char __pcpu_scope_##name;                    \
        extern __PCPU_DUMMY_ATTRS char __pcpu_unique_##name;            \
        __PCPU_DUMMY_ATTRS char __pcpu_unique_##name;                   \
        extern __PCPU_ATTRS(sec) __typeof__(type) name;                 \
        __PCPU_ATTRS(sec) PER_CPU_DEF_ATTRIBUTES __weak                 \
        __typeof__(type) name
#else
/*
 * Normal declaration and definition macros.
 */
#define DECLARE_PER_CPU_SECTION(type, name, sec)                        \
        extern __PCPU_ATTRS(sec) __typeof__(type) name

#define DEFINE_PER_CPU_SECTION(type, name, sec)                         \
        __PCPU_ATTRS(sec) PER_CPU_DEF_ATTRIBUTES                        \
        __typeof__(type) name
#endif

/*
 * Variant on the per-CPU variable declaration/definition theme used for
 * ordinary per-CPU variables.
 */
#define DECLARE_PER_CPU(type, name)                                     \
        DECLARE_PER_CPU_SECTION(type, name, "")

#define DEFINE_PER_CPU(type, name)                                      \
        DEFINE_PER_CPU_SECTION(type, name, "")

/*
 * Declaration/definition used for per-CPU variables that must come first in
 * the set of variables.
 */
#define DECLARE_PER_CPU_FIRST(type, name)                               \
        DECLARE_PER_CPU_SECTION(type, name, PER_CPU_FIRST_SECTION)

#define DEFINE_PER_CPU_FIRST(type, name)                                \
        DEFINE_PER_CPU_SECTION(type, name, PER_CPU_FIRST_SECTION)

/*
 * Declaration/definition used for per-CPU variables that must be cacheline
 * aligned under SMP conditions so that, whilst a particular instance of the
 * data corresponds to a particular CPU, inefficiencies due to direct access by
 * other CPUs are reduced by preventing the data from unnecessarily spanning
 * cachelines.
 *
 * An example of this would be statistical data, where each CPU's set of data
 * is updated by that CPU alone, but the data from across all CPUs is collated
 * by a CPU processing a read from a proc file.
 */
#define DECLARE_PER_CPU_SHARED_ALIGNED(type, name)                      \
        DECLARE_PER_CPU_SECTION(type, name, PER_CPU_SHARED_ALIGNED_SECTION) \
        ____cacheline_aligned_in_smp

#define DEFINE_PER_CPU_SHARED_ALIGNED(type, name)                       \
        DEFINE_PER_CPU_SECTION(type, name, PER_CPU_SHARED_ALIGNED_SECTION) \
        ____cacheline_aligned_in_smp

#define DECLARE_PER_CPU_ALIGNED(type, name)                             \
        DECLARE_PER_CPU_SECTION(type, name, PER_CPU_ALIGNED_SECTION)    \
        ____cacheline_aligned

#define DEFINE_PER_CPU_ALIGNED(type, name)                              \
        DEFINE_PER_CPU_SECTION(type, name, PER_CPU_ALIGNED_SECTION)     \
        ____cacheline_aligned

/*
 * Declaration/definition used for per-CPU variables that must be page aligned.
 */
#define DECLARE_PER_CPU_PAGE_ALIGNED(type, name)                        \
        DECLARE_PER_CPU_SECTION(type, name, "..page_aligned")           \
        __aligned(PAGE_SIZE)

#define DEFINE_PER_CPU_PAGE_ALIGNED(type, name)                         \
        DEFINE_PER_CPU_SECTION(type, name, "..page_aligned")            \
        __aligned(PAGE_SIZE)

/*
 * Declaration/definition used for per-CPU variables that must be read mostly.
 */
#define DECLARE_PER_CPU_READ_MOSTLY(type, name)                 \
        DECLARE_PER_CPU_SECTION(type, name, "..read_mostly")

#define DEFINE_PER_CPU_READ_MOSTLY(type, name)                          \
        DEFINE_PER_CPU_SECTION(type, name, "..read_mostly")

/*
 * Intermodule exports for per-CPU variables.  sparse forgets about
 * address space across EXPORT_SYMBOL(), change EXPORT_SYMBOL() to
 * noop if __CHECKER__.
 */
#ifndef __CHECKER__
#define EXPORT_PER_CPU_SYMBOL(var) EXPORT_SYMBOL(var)
#define EXPORT_PER_CPU_SYMBOL_GPL(var) EXPORT_SYMBOL_GPL(var)
#else
#define EXPORT_PER_CPU_SYMBOL(var)
#define EXPORT_PER_CPU_SYMBOL_GPL(var)
#endif

/*
 * Accessors and operations.
 */
#ifndef __ASSEMBLY__

/*
 * __verify_pcpu_ptr() verifies @ptr is a percpu pointer without evaluating
 * @ptr and is invoked once before a percpu area is accessed by all
 * accessors and operations.  This is performed in the generic part of
 * percpu and arch overrides don't need to worry about it; however, if an
 * arch wants to implement an arch-specific percpu accessor or operation,
 * it may use __verify_pcpu_ptr() to verify the parameters.
 *
 * + 0 is required in order to convert the pointer type from a
 * potential array type to a pointer to a single item of the array.
 */
#define __verify_pcpu_ptr(ptr)                                          \
do {                                                                    \
        const void __percpu *__vpp_verify = (typeof((ptr) + 0))NULL;    \
        (void)__vpp_verify;                                             \
} while (0)

#ifdef CONFIG_SMP

/*
 * Add an offset to a pointer but keep the pointer as-is.  Use RELOC_HIDE()
 * to prevent the compiler from making incorrect assumptions about the
 * pointer value.  The weird cast keeps both GCC and sparse happy.
 */
#define SHIFT_PERCPU_PTR(__p, __offset)                                 \
        RELOC_HIDE((typeof(*(__p)) __kernel __force *)(__p), (__offset))

#define per_cpu_ptr(ptr, cpu)                                           \
({                                                                      \
        __verify_pcpu_ptr(ptr);                                         \
        SHIFT_PERCPU_PTR((ptr), per_cpu_offset((cpu)));                 \
})

#define raw_cpu_ptr(ptr)                                                \
({                                                                      \
        __verify_pcpu_ptr(ptr);                                         \
        arch_raw_cpu_ptr(ptr);                                          \
})

#ifdef CONFIG_DEBUG_PREEMPT
#define this_cpu_ptr(ptr)                                               \
({                                                                      \
        __verify_pcpu_ptr(ptr);                                         \
        SHIFT_PERCPU_PTR(ptr, my_cpu_offset);                           \
})
#else
#define this_cpu_ptr(ptr) raw_cpu_ptr(ptr)
#endif

#else   /* CONFIG_SMP */

#define VERIFY_PERCPU_PTR(__p)                                          \
({                                                                      \
        __verify_pcpu_ptr(__p);                                         \
        (typeof(*(__p)) __kernel __force *)(__p);                       \
})

#define per_cpu_ptr(ptr, cpu)   ({ (void)(cpu); VERIFY_PERCPU_PTR(ptr); })
#define raw_cpu_ptr(ptr)        per_cpu_ptr(ptr, 0)
#define this_cpu_ptr(ptr)       raw_cpu_ptr(ptr)

#endif  /* CONFIG_SMP */

#define per_cpu(var, cpu)       (*per_cpu_ptr(&(var), cpu))

/*
 * Must be an lvalue. Since @var must be a simple identifier,
 * we force a syntax error here if it isn't.
 */
#define get_cpu_var(var)                                                \
(*({                                                                    \
        preempt_disable();                                              \
        this_cpu_ptr(&var);                                             \
}))

/*
 * The weird & is necessary because sparse considers (void)(var) to be
 * a direct dereference of percpu variable (var).
 */
#define put_cpu_var(var)                                                \
do {                                                                    \
        (void)&(var);                                                   \
        preempt_enable();                                               \
} while (0)

#define get_cpu_ptr(var)                                                \
({                                                                      \
        preempt_disable();                                              \
        this_cpu_ptr(var);                                              \
})

#define put_cpu_ptr(var)                                                \
do {                                                                    \
        (void)(var);                                                    \
        preempt_enable();                                               \
} while (0)

/*
 * Branching function to split up a function into a set of functions that
 * are called for different scalar sizes of the objects handled.
 */

extern void __bad_size_call_parameter(void);

#ifdef CONFIG_DEBUG_PREEMPT
extern void __this_cpu_preempt_check(const char *op);
#else
static inline void __this_cpu_preempt_check(const char *op) { }
#endif

#define __pcpu_size_call_return(stem, variable)                         \
({                                                                      \
        typeof(variable) pscr_ret__;                                    \
        __verify_pcpu_ptr(&(variable));                                 \
        switch(sizeof(variable)) {                                      \
        case 1: pscr_ret__ = stem##1(variable); break;                  \
        case 2: pscr_ret__ = stem##2(variable); break;                  \
        case 4: pscr_ret__ = stem##4(variable); break;                  \
        case 8: pscr_ret__ = stem##8(variable); break;                  \
        default:                                                        \
                __bad_size_call_parameter(); break;                     \
        }                                                               \
        pscr_ret__;                                                     \
})

#define __pcpu_size_call_return2(stem, variable, ...)                   \
({                                                                      \
        typeof(variable) pscr2_ret__;                                   \
        __verify_pcpu_ptr(&(variable));                                 \
        switch(sizeof(variable)) {                                      \
        case 1: pscr2_ret__ = stem##1(variable, __VA_ARGS__); break;    \
        case 2: pscr2_ret__ = stem##2(variable, __VA_ARGS__); break;    \
        case 4: pscr2_ret__ = stem##4(variable, __VA_ARGS__); break;    \
        case 8: pscr2_ret__ = stem##8(variable, __VA_ARGS__); break;    \
        default:                                                        \
                __bad_size_call_parameter(); break;                     \
        }                                                               \
        pscr2_ret__;                                                    \
})

/*
 * Special handling for cmpxchg_double.  cmpxchg_double is passed two
 * percpu variables.  The first has to be aligned to a double word
 * boundary and the second has to follow directly thereafter.
 * We enforce this on all architectures even if they don't support
 * a double cmpxchg instruction, since it's a cheap requirement, and it
 * avoids breaking the requirement for architectures with the instruction.
 */
#define __pcpu_double_call_return_bool(stem, pcp1, pcp2, ...)           \
({                                                                      \
        bool pdcrb_ret__;                                               \
        __verify_pcpu_ptr(&(pcp1));                                     \
        BUILD_BUG_ON(sizeof(pcp1) != sizeof(pcp2));                     \
        VM_BUG_ON((unsigned long)(&(pcp1)) % (2 * sizeof(pcp1)));       \
        VM_BUG_ON((unsigned long)(&(pcp2)) !=                           \
                  (unsigned long)(&(pcp1)) + sizeof(pcp1));             \
        switch(sizeof(pcp1)) {                                          \
        case 1: pdcrb_ret__ = stem##1(pcp1, pcp2, __VA_ARGS__); break;  \
        case 2: pdcrb_ret__ = stem##2(pcp1, pcp2, __VA_ARGS__); break;  \
        case 4: pdcrb_ret__ = stem##4(pcp1, pcp2, __VA_ARGS__); break;  \
        case 8: pdcrb_ret__ = stem##8(pcp1, pcp2, __VA_ARGS__); break;  \
        default:                                                        \
                __bad_size_call_parameter(); break;                     \
        }                                                               \
        pdcrb_ret__;                                                    \
})

#define __pcpu_size_call(stem, variable, ...)                           \
do {                                                                    \
        __verify_pcpu_ptr(&(variable));                                 \
        switch(sizeof(variable)) {                                      \
                case 1: stem##1(variable, __VA_ARGS__);break;           \
                case 2: stem##2(variable, __VA_ARGS__);break;           \
                case 4: stem##4(variable, __VA_ARGS__);break;           \
                case 8: stem##8(variable, __VA_ARGS__);break;           \
                default:                                                \
                        __bad_size_call_parameter();break;              \
        }                                                               \
} while (0)

/*
 * this_cpu operations (C) 2008-2013 Christoph Lameter <cl@linux.com>
 *
 * Optimized manipulation for memory allocated through the per cpu
 * allocator or for addresses of per cpu variables.
 *
 * These operation guarantee exclusivity of access for other operations
 * on the *same* processor. The assumption is that per cpu data is only
 * accessed by a single processor instance (the current one).
 *
 * The arch code can provide optimized implementation by defining macros
 * for certain scalar sizes. F.e. provide this_cpu_add_2() to provide per
 * cpu atomic operations for 2 byte sized RMW actions. If arch code does
 * not provide operations for a scalar size then the fallback in the
 * generic code will be used.
 *
 * cmpxchg_double replaces two adjacent scalars at once.  The first two
 * parameters are per cpu variables which have to be of the same size.  A
 * truth value is returned to indicate success or failure (since a double
 * register result is difficult to handle).  There is very limited hardware
 * support for these operations, so only certain sizes may work.
 */

/*
 * Operations for contexts where we do not want to do any checks for
 * preemptions.  Unless strictly necessary, always use [__]this_cpu_*()
 * instead.
 *
 * If there is no other protection through preempt disable and/or disabling
 * interupts then one of these RMW operations can show unexpected behavior
 * because the execution thread was rescheduled on another processor or an
 * interrupt occurred and the same percpu variable was modified from the
 * interrupt context.
 */
#define raw_cpu_read(pcp)               __pcpu_size_call_return(raw_cpu_read_, pcp)
#define raw_cpu_write(pcp, val)         __pcpu_size_call(raw_cpu_write_, pcp, val)
#define raw_cpu_add(pcp, val)           __pcpu_size_call(raw_cpu_add_, pcp, val)
#define raw_cpu_and(pcp, val)           __pcpu_size_call(raw_cpu_and_, pcp, val)
#define raw_cpu_or(pcp, val)            __pcpu_size_call(raw_cpu_or_, pcp, val)
#define raw_cpu_add_return(pcp, val)    __pcpu_size_call_return2(raw_cpu_add_return_, pcp, val)
#define raw_cpu_xchg(pcp, nval)         __pcpu_size_call_return2(raw_cpu_xchg_, pcp, nval)
#define raw_cpu_cmpxchg(pcp, oval, nval) \
        __pcpu_size_call_return2(raw_cpu_cmpxchg_, pcp, oval, nval)
#define raw_cpu_cmpxchg_double(pcp1, pcp2, oval1, oval2, nval1, nval2) \
        __pcpu_double_call_return_bool(raw_cpu_cmpxchg_double_, pcp1, pcp2, oval1, oval2, nval1, nval2)

#define raw_cpu_sub(pcp, val)           raw_cpu_add(pcp, -(val))
#define raw_cpu_inc(pcp)                raw_cpu_add(pcp, 1)
#define raw_cpu_dec(pcp)                raw_cpu_sub(pcp, 1)
#define raw_cpu_sub_return(pcp, val)    raw_cpu_add_return(pcp, -(typeof(pcp))(val))
#define raw_cpu_inc_return(pcp)         raw_cpu_add_return(pcp, 1)
#define raw_cpu_dec_return(pcp)         raw_cpu_add_return(pcp, -1)

/*
 * Operations for contexts that are safe from preemption/interrupts.  These
 * operations verify that preemption is disabled.
 */
#define __this_cpu_read(pcp)                                            \
({                                                                      \
        __this_cpu_preempt_check("read");                               \
        raw_cpu_read(pcp);                                              \
})

#define __this_cpu_write(pcp, val)                                      \
({                                                                      \
        __this_cpu_preempt_check("write");                              \
        raw_cpu_write(pcp, val);                                        \
})

#define __this_cpu_add(pcp, val)                                        \
({                                                                      \
        __this_cpu_preempt_check("add");                                \
        raw_cpu_add(pcp, val);                                          \
})

#define __this_cpu_and(pcp, val)                                        \
({                                                                      \
        __this_cpu_preempt_check("and");                                \
        raw_cpu_and(pcp, val);                                          \
})

#define __this_cpu_or(pcp, val)                                         \
({                                                                      \
        __this_cpu_preempt_check("or");                                 \
        raw_cpu_or(pcp, val);                                           \
})

#define __this_cpu_add_return(pcp, val)                                 \
({                                                                      \
        __this_cpu_preempt_check("add_return");                         \
        raw_cpu_add_return(pcp, val);                                   \
})

#define __this_cpu_xchg(pcp, nval)                                      \
({                                                                      \
        __this_cpu_preempt_check("xchg");                               \
        raw_cpu_xchg(pcp, nval);                                        \
})

#define __this_cpu_cmpxchg(pcp, oval, nval)                             \
({                                                                      \
        __this_cpu_preempt_check("cmpxchg");                            \
        raw_cpu_cmpxchg(pcp, oval, nval);                               \
})

#define __this_cpu_cmpxchg_double(pcp1, pcp2, oval1, oval2, nval1, nval2) \
({      __this_cpu_preempt_check("cmpxchg_double");                     \
        raw_cpu_cmpxchg_double(pcp1, pcp2, oval1, oval2, nval1, nval2); \
})

#define __this_cpu_sub(pcp, val)        __this_cpu_add(pcp, -(typeof(pcp))(val))
#define __this_cpu_inc(pcp)             __this_cpu_add(pcp, 1)
#define __this_cpu_dec(pcp)             __this_cpu_sub(pcp, 1)
#define __this_cpu_sub_return(pcp, val) __this_cpu_add_return(pcp, -(typeof(pcp))(val))
#define __this_cpu_inc_return(pcp)      __this_cpu_add_return(pcp, 1)
#define __this_cpu_dec_return(pcp)      __this_cpu_add_return(pcp, -1)

/*
 * Operations with implied preemption protection.  These operations can be
 * used without worrying about preemption.  Note that interrupts may still
 * occur while an operation is in progress and if the interrupt modifies
 * the variable too then RMW actions may not be reliable.
 */
#define this_cpu_read(pcp)              __pcpu_size_call_return(this_cpu_read_, pcp)
#define this_cpu_write(pcp, val)        __pcpu_size_call(this_cpu_write_, pcp, val)
#define this_cpu_add(pcp, val)          __pcpu_size_call(this_cpu_add_, pcp, val)
#define this_cpu_and(pcp, val)          __pcpu_size_call(this_cpu_and_, pcp, val)
#define this_cpu_or(pcp, val)           __pcpu_size_call(this_cpu_or_, pcp, val)
#define this_cpu_add_return(pcp, val)   __pcpu_size_call_return2(this_cpu_add_return_, pcp, val)
#define this_cpu_xchg(pcp, nval)        __pcpu_size_call_return2(this_cpu_xchg_, pcp, nval)
#define this_cpu_cmpxchg(pcp, oval, nval) \
        __pcpu_size_call_return2(this_cpu_cmpxchg_, pcp, oval, nval)
#define this_cpu_cmpxchg_double(pcp1, pcp2, oval1, oval2, nval1, nval2) \
        __pcpu_double_call_return_bool(this_cpu_cmpxchg_double_, pcp1, pcp2, oval1, oval2, nval1, nval2)

#define this_cpu_sub(pcp, val)          this_cpu_add(pcp, -(typeof(pcp))(val))
#define this_cpu_inc(pcp)               this_cpu_add(pcp, 1)
#define this_cpu_dec(pcp)               this_cpu_sub(pcp, 1)
#define this_cpu_sub_return(pcp, val)   this_cpu_add_return(pcp, -(typeof(pcp))(val))
#define this_cpu_inc_return(pcp)        this_cpu_add_return(pcp, 1)
#define this_cpu_dec_return(pcp)        this_cpu_add_return(pcp, -1)

#endif /* __ASSEMBLY__ */
#endif /* _LINUX_PERCPU_DEFS_H */

```

```
  1 #ifndef __LINUX_CPUMASK_H
  2 #define __LINUX_CPUMASK_H
  3 
  4 /*
  5  * Cpumasks provide a bitmap suitable for representing the
  6  * set of CPU's in a system, one bit position per CPU number.  In general,
  7  * only nr_cpu_ids (<= NR_CPUS) bits are valid.
  8  */
  9 #include <linux/kernel.h>
 10 #include <linux/threads.h>
 11 #include <linux/bitmap.h>
 12 #include <linux/bug.h>
 13 
 14 /* Don't assign or return these: may not be this big! */
 15 typedef struct cpumask { DECLARE_BITMAP(bits, NR_CPUS); } cpumask_t;
 16 
 17 /**
 18  * cpumask_bits - get the bits in a cpumask
 19  * @maskp: the struct cpumask *
 20  *
 21  * You should only assume nr_cpu_ids bits of this mask are valid.  This is
 22  * a macro so it's const-correct.
 23  */
 24 #define cpumask_bits(maskp) ((maskp)->bits)
 25 
 26 /**
 27  * cpumask_pr_args - printf args to output a cpumask
 28  * @maskp: cpumask to be printed
 29  *
 30  * Can be used to provide arguments for '%*pb[l]' when printing a cpumask.
 31  */
 32 #define cpumask_pr_args(maskp)          nr_cpu_ids, cpumask_bits(maskp)
 33 
 34 #if NR_CPUS == 1
 35 #define nr_cpu_ids              1
 36 #else
 37 extern int nr_cpu_ids;
 38 #endif
 39 
 40 #ifdef CONFIG_CPUMASK_OFFSTACK
 41 /* Assuming NR_CPUS is huge, a runtime limit is more efficient.  Also,
 42  * not all bits may be allocated. */
 43 #define nr_cpumask_bits nr_cpu_ids
 44 #else
 45 #define nr_cpumask_bits NR_CPUS
 46 #endif
 47 
 48 /*
 49  * The following particular system cpumasks and operations manage
 50  * possible, present, active and online cpus.
 51  *
 52  *     cpu_possible_mask- has bit 'cpu' set iff cpu is populatable
 53  *     cpu_present_mask - has bit 'cpu' set iff cpu is populated
 54  *     cpu_online_mask  - has bit 'cpu' set iff cpu available to scheduler
 55  *     cpu_active_mask  - has bit 'cpu' set iff cpu available to migration
 56  *
 57  *  If !CONFIG_HOTPLUG_CPU, present == possible, and active == online.
 58  *
 59  *  The cpu_possible_mask is fixed at boot time, as the set of CPU id's
 60  *  that it is possible might ever be plugged in at anytime during the
 61  *  life of that system boot.  The cpu_present_mask is dynamic(*),
 62  *  representing which CPUs are currently plugged in.  And
 63  *  cpu_online_mask is the dynamic subset of cpu_present_mask,
 64  *  indicating those CPUs available for scheduling.
 65  *
 66  *  If HOTPLUG is enabled, then cpu_possible_mask is forced to have
 67  *  all NR_CPUS bits set, otherwise it is just the set of CPUs that
 68  *  ACPI reports present at boot.
 69  *
 70  *  If HOTPLUG is enabled, then cpu_present_mask varies dynamically,
 71  *  depending on what ACPI reports as currently plugged in, otherwise
 72  *  cpu_present_mask is just a copy of cpu_possible_mask.
 73  *
 74  *  (*) Well, cpu_present_mask is dynamic in the hotplug case.  If not
 75  *      hotplug, it's a copy of cpu_possible_mask, hence fixed at boot.
 76  *
 77  * Subtleties:
 78  * 1) UP arch's (NR_CPUS == 1, CONFIG_SMP not defined) hardcode
 79  *    assumption that their single CPU is online.  The UP
 80  *    cpu_{online,possible,present}_masks are placebos.  Changing them
 81  *    will have no useful affect on the following num_*_cpus()
 82  *    and cpu_*() macros in the UP case.  This ugliness is a UP
 83  *    optimization - don't waste any instructions or memory references
 84  *    asking if you're online or how many CPUs there are if there is
 85  *    only one CPU.
 86  */
 87 
 88 extern const struct cpumask *const cpu_possible_mask;
 89 extern const struct cpumask *const cpu_online_mask;
 90 extern const struct cpumask *const cpu_present_mask;
 91 extern const struct cpumask *const cpu_active_mask;
 92 
 93 #if NR_CPUS > 1
 94 #define num_online_cpus()       cpumask_weight(cpu_online_mask)
 95 #define num_possible_cpus()     cpumask_weight(cpu_possible_mask)
 96 #define num_present_cpus()      cpumask_weight(cpu_present_mask)
 97 #define num_active_cpus()       cpumask_weight(cpu_active_mask)
 98 #define cpu_online(cpu)         cpumask_test_cpu((cpu), cpu_online_mask)
 99 #define cpu_possible(cpu)       cpumask_test_cpu((cpu), cpu_possible_mask)
100 #define cpu_present(cpu)        cpumask_test_cpu((cpu), cpu_present_mask)
101 #define cpu_active(cpu)         cpumask_test_cpu((cpu), cpu_active_mask)
102 #else
103 #define num_online_cpus()       1U
104 #define num_possible_cpus()     1U
105 #define num_present_cpus()      1U
106 #define num_active_cpus()       1U
107 #define cpu_online(cpu)         ((cpu) == 0)
108 #define cpu_possible(cpu)       ((cpu) == 0)
109 #define cpu_present(cpu)        ((cpu) == 0)
110 #define cpu_active(cpu)         ((cpu) == 0)
111 #endif
112 
113 /* verify cpu argument to cpumask_* operators */
114 static inline unsigned int cpumask_check(unsigned int cpu)
115 {
116 #ifdef CONFIG_DEBUG_PER_CPU_MAPS
117         WARN_ON_ONCE(cpu >= nr_cpumask_bits);
118 #endif /* CONFIG_DEBUG_PER_CPU_MAPS */
119         return cpu;
120 }
121 
122 #if NR_CPUS == 1
123 /* Uniprocessor.  Assume all masks are "1". */
124 static inline unsigned int cpumask_first(const struct cpumask *srcp)
125 {
126         return 0;
127 }
128 
129 /* Valid inputs for n are -1 and 0. */
130 static inline unsigned int cpumask_next(int n, const struct cpumask *srcp)
131 {
132         return n+1;
133 }
134 
135 static inline unsigned int cpumask_next_zero(int n, const struct cpumask *srcp)
136 {
137         return n+1;
138 }
139 
140 static inline unsigned int cpumask_next_and(int n,
141                                             const struct cpumask *srcp,
142                                             const struct cpumask *andp)
143 {
144         return n+1;
145 }
146 
147 /* cpu must be a valid cpu, ie 0, so there's no other choice. */
148 static inline unsigned int cpumask_any_but(const struct cpumask *mask,
149                                            unsigned int cpu)
150 {
151         return 1;
152 }
153 
154 static inline unsigned int cpumask_local_spread(unsigned int i, int node)
155 {
156         return 0;
157 }
158 
159 #define for_each_cpu(cpu, mask)                 \
160         for ((cpu) = 0; (cpu) < 1; (cpu)++, (void)mask)
161 #define for_each_cpu_not(cpu, mask)             \
162         for ((cpu) = 0; (cpu) < 1; (cpu)++, (void)mask)
163 #define for_each_cpu_and(cpu, mask, and)        \
164         for ((cpu) = 0; (cpu) < 1; (cpu)++, (void)mask, (void)and)
165 #else
166 /**
167  * cpumask_first - get the first cpu in a cpumask
168  * @srcp: the cpumask pointer
169  *
170  * Returns >= nr_cpu_ids if no cpus set.
171  */
172 static inline unsigned int cpumask_first(const struct cpumask *srcp)
173 {
174         return find_first_bit(cpumask_bits(srcp), nr_cpumask_bits);
175 }
176 
177 /**
178  * cpumask_next - get the next cpu in a cpumask
179  * @n: the cpu prior to the place to search (ie. return will be > @n)
180  * @srcp: the cpumask pointer
181  *
182  * Returns >= nr_cpu_ids if no further cpus set.
183  */
184 static inline unsigned int cpumask_next(int n, const struct cpumask *srcp)
185 {
186         /* -1 is a legal arg here. */
187         if (n != -1)
188                 cpumask_check(n);
189         return find_next_bit(cpumask_bits(srcp), nr_cpumask_bits, n+1);
190 }
191 
192 /**
193  * cpumask_next_zero - get the next unset cpu in a cpumask
194  * @n: the cpu prior to the place to search (ie. return will be > @n)
195  * @srcp: the cpumask pointer
196  *
197  * Returns >= nr_cpu_ids if no further cpus unset.
198  */
199 static inline unsigned int cpumask_next_zero(int n, const struct cpumask *srcp)
200 {
201         /* -1 is a legal arg here. */
202         if (n != -1)
203                 cpumask_check(n);
204         return find_next_zero_bit(cpumask_bits(srcp), nr_cpumask_bits, n+1);
205 }
206 
207 int cpumask_next_and(int n, const struct cpumask *, const struct cpumask *);
208 int cpumask_any_but(const struct cpumask *mask, unsigned int cpu);
209 unsigned int cpumask_local_spread(unsigned int i, int node);
210 
211 /**
212  * for_each_cpu - iterate over every cpu in a mask
213  * @cpu: the (optionally unsigned) integer iterator
214  * @mask: the cpumask pointer
215  *
216  * After the loop, cpu is >= nr_cpu_ids.
217  */
218 #define for_each_cpu(cpu, mask)                         \
219         for ((cpu) = -1;                                \
220                 (cpu) = cpumask_next((cpu), (mask)),    \
221                 (cpu) < nr_cpu_ids;)
222 
223 /**
224  * for_each_cpu_not - iterate over every cpu in a complemented mask
225  * @cpu: the (optionally unsigned) integer iterator
226  * @mask: the cpumask pointer
227  *
228  * After the loop, cpu is >= nr_cpu_ids.
229  */
230 #define for_each_cpu_not(cpu, mask)                             \
231         for ((cpu) = -1;                                        \
232                 (cpu) = cpumask_next_zero((cpu), (mask)),       \
233                 (cpu) < nr_cpu_ids;)
234 
235 /**
236  * for_each_cpu_and - iterate over every cpu in both masks
237  * @cpu: the (optionally unsigned) integer iterator
238  * @mask: the first cpumask pointer
239  * @and: the second cpumask pointer
240  *
241  * This saves a temporary CPU mask in many places.  It is equivalent to:
242  *      struct cpumask tmp;
243  *      cpumask_and(&tmp, &mask, &and);
244  *      for_each_cpu(cpu, &tmp)
245  *              ...
246  *
247  * After the loop, cpu is >= nr_cpu_ids.
248  */
249 #define for_each_cpu_and(cpu, mask, and)                                \
250         for ((cpu) = -1;                                                \
251                 (cpu) = cpumask_next_and((cpu), (mask), (and)),         \
252                 (cpu) < nr_cpu_ids;)
253 #endif /* SMP */
254 
255 #define CPU_BITS_NONE                                           \
256 {                                                               \
257         [0 ... BITS_TO_LONGS(NR_CPUS)-1] = 0UL                  \
258 }
259 
260 #define CPU_BITS_CPU0                                           \
261 {                                                               \
262         [0] =  1UL                                              \
263 }
264 
265 /**
266  * cpumask_set_cpu - set a cpu in a cpumask
267  * @cpu: cpu number (< nr_cpu_ids)
268  * @dstp: the cpumask pointer
269  */
270 static inline void cpumask_set_cpu(unsigned int cpu, struct cpumask *dstp)
271 {
272         set_bit(cpumask_check(cpu), cpumask_bits(dstp));
273 }
274 
275 /**
276  * cpumask_clear_cpu - clear a cpu in a cpumask
277  * @cpu: cpu number (< nr_cpu_ids)
278  * @dstp: the cpumask pointer
279  */
280 static inline void cpumask_clear_cpu(int cpu, struct cpumask *dstp)
281 {
282         clear_bit(cpumask_check(cpu), cpumask_bits(dstp));
283 }
284 
285 /**
286  * cpumask_test_cpu - test for a cpu in a cpumask
287  * @cpu: cpu number (< nr_cpu_ids)
288  * @cpumask: the cpumask pointer
289  *
290  * Returns 1 if @cpu is set in @cpumask, else returns 0
291  */
292 static inline int cpumask_test_cpu(int cpu, const struct cpumask *cpumask)
293 {
294         return test_bit(cpumask_check(cpu), cpumask_bits((cpumask)));
295 }
296 
297 /**
298  * cpumask_test_and_set_cpu - atomically test and set a cpu in a cpumask
299  * @cpu: cpu number (< nr_cpu_ids)
300  * @cpumask: the cpumask pointer
301  *
302  * Returns 1 if @cpu is set in old bitmap of @cpumask, else returns 0
303  *
304  * test_and_set_bit wrapper for cpumasks.
305  */
306 static inline int cpumask_test_and_set_cpu(int cpu, struct cpumask *cpumask)
307 {
308         return test_and_set_bit(cpumask_check(cpu), cpumask_bits(cpumask));
309 }
310 
311 /**
312  * cpumask_test_and_clear_cpu - atomically test and clear a cpu in a cpumask
313  * @cpu: cpu number (< nr_cpu_ids)
314  * @cpumask: the cpumask pointer
315  *
316  * Returns 1 if @cpu is set in old bitmap of @cpumask, else returns 0
317  *
318  * test_and_clear_bit wrapper for cpumasks.
319  */
320 static inline int cpumask_test_and_clear_cpu(int cpu, struct cpumask *cpumask)
321 {
322         return test_and_clear_bit(cpumask_check(cpu), cpumask_bits(cpumask));
323 }
324 
325 /**
326  * cpumask_setall - set all cpus (< nr_cpu_ids) in a cpumask
327  * @dstp: the cpumask pointer
328  */
329 static inline void cpumask_setall(struct cpumask *dstp)
330 {
331         bitmap_fill(cpumask_bits(dstp), nr_cpumask_bits);
332 }
333 
334 /**
335  * cpumask_clear - clear all cpus (< nr_cpu_ids) in a cpumask
336  * @dstp: the cpumask pointer
337  */
338 static inline void cpumask_clear(struct cpumask *dstp)
339 {
340         bitmap_zero(cpumask_bits(dstp), nr_cpumask_bits);
341 }
342 
343 /**
344  * cpumask_and - *dstp = *src1p & *src2p
345  * @dstp: the cpumask result
346  * @src1p: the first input
347  * @src2p: the second input
348  *
349  * If *@dstp is empty, returns 0, else returns 1
350  */
351 static inline int cpumask_and(struct cpumask *dstp,
352                                const struct cpumask *src1p,
353                                const struct cpumask *src2p)
354 {
355         return bitmap_and(cpumask_bits(dstp), cpumask_bits(src1p),
356                                        cpumask_bits(src2p), nr_cpumask_bits);
357 }
358 
359 /**
360  * cpumask_or - *dstp = *src1p | *src2p
361  * @dstp: the cpumask result
362  * @src1p: the first input
363  * @src2p: the second input
364  */
365 static inline void cpumask_or(struct cpumask *dstp, const struct cpumask *src1p,
366                               const struct cpumask *src2p)
367 {
368         bitmap_or(cpumask_bits(dstp), cpumask_bits(src1p),
369                                       cpumask_bits(src2p), nr_cpumask_bits);
370 }
371 
372 /**
373  * cpumask_xor - *dstp = *src1p ^ *src2p
374  * @dstp: the cpumask result
375  * @src1p: the first input
376  * @src2p: the second input
377  */
378 static inline void cpumask_xor(struct cpumask *dstp,
379                                const struct cpumask *src1p,
380                                const struct cpumask *src2p)
381 {
382         bitmap_xor(cpumask_bits(dstp), cpumask_bits(src1p),
383                                        cpumask_bits(src2p), nr_cpumask_bits);
384 }
385 
386 /**
387  * cpumask_andnot - *dstp = *src1p & ~*src2p
388  * @dstp: the cpumask result
389  * @src1p: the first input
390  * @src2p: the second input
391  *
392  * If *@dstp is empty, returns 0, else returns 1
393  */
394 static inline int cpumask_andnot(struct cpumask *dstp,
395                                   const struct cpumask *src1p,
396                                   const struct cpumask *src2p)
397 {
398         return bitmap_andnot(cpumask_bits(dstp), cpumask_bits(src1p),
399                                           cpumask_bits(src2p), nr_cpumask_bits);
400 }
401 
402 /**
403  * cpumask_complement - *dstp = ~*srcp
404  * @dstp: the cpumask result
405  * @srcp: the input to invert
406  */
407 static inline void cpumask_complement(struct cpumask *dstp,
408                                       const struct cpumask *srcp)
409 {
410         bitmap_complement(cpumask_bits(dstp), cpumask_bits(srcp),
411                                               nr_cpumask_bits);
412 }
413 
414 /**
415  * cpumask_equal - *src1p == *src2p
416  * @src1p: the first input
417  * @src2p: the second input
418  */
419 static inline bool cpumask_equal(const struct cpumask *src1p,
420                                 const struct cpumask *src2p)
421 {
422         return bitmap_equal(cpumask_bits(src1p), cpumask_bits(src2p),
423                                                  nr_cpumask_bits);
424 }
425 
426 /**
427  * cpumask_intersects - (*src1p & *src2p) != 0
428  * @src1p: the first input
429  * @src2p: the second input
430  */
431 static inline bool cpumask_intersects(const struct cpumask *src1p,
432                                      const struct cpumask *src2p)
433 {
434         return bitmap_intersects(cpumask_bits(src1p), cpumask_bits(src2p),
435                                                       nr_cpumask_bits);
436 }
437 
438 /**
439  * cpumask_subset - (*src1p & ~*src2p) == 0
440  * @src1p: the first input
441  * @src2p: the second input
442  *
443  * Returns 1 if *@src1p is a subset of *@src2p, else returns 0
444  */
445 static inline int cpumask_subset(const struct cpumask *src1p,
446                                  const struct cpumask *src2p)
447 {
448         return bitmap_subset(cpumask_bits(src1p), cpumask_bits(src2p),
449                                                   nr_cpumask_bits);
450 }
451 
452 /**
453  * cpumask_empty - *srcp == 0
454  * @srcp: the cpumask to that all cpus < nr_cpu_ids are clear.
455  */
456 static inline bool cpumask_empty(const struct cpumask *srcp)
457 {
458         return bitmap_empty(cpumask_bits(srcp), nr_cpumask_bits);
459 }
460 
461 /**
462  * cpumask_full - *srcp == 0xFFFFFFFF...
463  * @srcp: the cpumask to that all cpus < nr_cpu_ids are set.
464  */
465 static inline bool cpumask_full(const struct cpumask *srcp)
466 {
467         return bitmap_full(cpumask_bits(srcp), nr_cpumask_bits);
468 }
469 
470 /**
471  * cpumask_weight - Count of bits in *srcp
472  * @srcp: the cpumask to count bits (< nr_cpu_ids) in.
473  */
474 static inline unsigned int cpumask_weight(const struct cpumask *srcp)
475 {
476         return bitmap_weight(cpumask_bits(srcp), nr_cpumask_bits);
477 }
478 
479 /**
480  * cpumask_shift_right - *dstp = *srcp >> n
481  * @dstp: the cpumask result
482  * @srcp: the input to shift
483  * @n: the number of bits to shift by
484  */
485 static inline void cpumask_shift_right(struct cpumask *dstp,
486                                        const struct cpumask *srcp, int n)
487 {
488         bitmap_shift_right(cpumask_bits(dstp), cpumask_bits(srcp), n,
489                                                nr_cpumask_bits);
490 }
491 
492 /**
493  * cpumask_shift_left - *dstp = *srcp << n
494  * @dstp: the cpumask result
495  * @srcp: the input to shift
496  * @n: the number of bits to shift by
497  */
498 static inline void cpumask_shift_left(struct cpumask *dstp,
499                                       const struct cpumask *srcp, int n)
500 {
501         bitmap_shift_left(cpumask_bits(dstp), cpumask_bits(srcp), n,
502                                               nr_cpumask_bits);
503 }
504 
505 /**
506  * cpumask_copy - *dstp = *srcp
507  * @dstp: the result
508  * @srcp: the input cpumask
509  */
510 static inline void cpumask_copy(struct cpumask *dstp,
511                                 const struct cpumask *srcp)
512 {
513         bitmap_copy(cpumask_bits(dstp), cpumask_bits(srcp), nr_cpumask_bits);
514 }
515 
516 /**
517  * cpumask_any - pick a "random" cpu from *srcp
518  * @srcp: the input cpumask
519  *
520  * Returns >= nr_cpu_ids if no cpus set.
521  */
522 #define cpumask_any(srcp) cpumask_first(srcp)
523 
524 /**
525  * cpumask_first_and - return the first cpu from *srcp1 & *srcp2
526  * @src1p: the first input
527  * @src2p: the second input
528  *
529  * Returns >= nr_cpu_ids if no cpus set in both.  See also cpumask_next_and().
530  */
531 #define cpumask_first_and(src1p, src2p) cpumask_next_and(-1, (src1p), (src2p))
532 
533 /**
534  * cpumask_any_and - pick a "random" cpu from *mask1 & *mask2
535  * @mask1: the first input cpumask
536  * @mask2: the second input cpumask
537  *
538  * Returns >= nr_cpu_ids if no cpus set.
539  */
540 #define cpumask_any_and(mask1, mask2) cpumask_first_and((mask1), (mask2))
541 
542 /**
543  * cpumask_of - the cpumask containing just a given cpu
544  * @cpu: the cpu (<= nr_cpu_ids)
545  */
546 #define cpumask_of(cpu) (get_cpu_mask(cpu))
547 
548 /**
549  * cpumask_parse_user - extract a cpumask from a user string
550  * @buf: the buffer to extract from
551  * @len: the length of the buffer
552  * @dstp: the cpumask to set.
553  *
554  * Returns -errno, or 0 for success.
555  */
556 static inline int cpumask_parse_user(const char __user *buf, int len,
557                                      struct cpumask *dstp)
558 {
559         return bitmap_parse_user(buf, len, cpumask_bits(dstp), nr_cpu_ids);
560 }
561 
562 /**
563  * cpumask_parselist_user - extract a cpumask from a user string
564  * @buf: the buffer to extract from
565  * @len: the length of the buffer
566  * @dstp: the cpumask to set.
567  *
568  * Returns -errno, or 0 for success.
569  */
570 static inline int cpumask_parselist_user(const char __user *buf, int len,
571                                      struct cpumask *dstp)
572 {
573         return bitmap_parselist_user(buf, len, cpumask_bits(dstp),
574                                      nr_cpu_ids);
575 }
576 
577 /**
578  * cpumask_parse - extract a cpumask from from a string
579  * @buf: the buffer to extract from
580  * @dstp: the cpumask to set.
581  *
582  * Returns -errno, or 0 for success.
583  */
584 static inline int cpumask_parse(const char *buf, struct cpumask *dstp)
585 {
586         char *nl = strchr(buf, '\n');
587         unsigned int len = nl ? (unsigned int)(nl - buf) : strlen(buf);
588 
589         return bitmap_parse(buf, len, cpumask_bits(dstp), nr_cpu_ids);
590 }
591 
592 /**
593  * cpulist_parse - extract a cpumask from a user string of ranges
594  * @buf: the buffer to extract from
595  * @dstp: the cpumask to set.
596  *
597  * Returns -errno, or 0 for success.
598  */
599 static inline int cpulist_parse(const char *buf, struct cpumask *dstp)
600 {
601         return bitmap_parselist(buf, cpumask_bits(dstp), nr_cpu_ids);
602 }
603 
604 /**
605  * cpumask_size - size to allocate for a 'struct cpumask' in bytes
606  *
607  * This will eventually be a runtime variable, depending on nr_cpu_ids.
608  */
609 static inline size_t cpumask_size(void)
610 {
611         return BITS_TO_LONGS(nr_cpumask_bits) * sizeof(long);
612 }
613 
614 /*
615  * cpumask_var_t: struct cpumask for stack usage.
616  *
617  * Oh, the wicked games we play!  In order to make kernel coding a
618  * little more difficult, we typedef cpumask_var_t to an array or a
619  * pointer: doing &mask on an array is a noop, so it still works.
620  *
621  * ie.
622  *      cpumask_var_t tmpmask;
623  *      if (!alloc_cpumask_var(&tmpmask, GFP_KERNEL))
624  *              return -ENOMEM;
625  *
626  *        ... use 'tmpmask' like a normal struct cpumask * ...
627  *
628  *      free_cpumask_var(tmpmask);
629  *
630  *
631  * However, one notable exception is there. alloc_cpumask_var() allocates
632  * only nr_cpumask_bits bits (in the other hand, real cpumask_t always has
633  * NR_CPUS bits). Therefore you don't have to dereference cpumask_var_t.
634  *
635  *      cpumask_var_t tmpmask;
636  *      if (!alloc_cpumask_var(&tmpmask, GFP_KERNEL))
637  *              return -ENOMEM;
638  *
639  *      var = *tmpmask;
640  *
641  * This code makes NR_CPUS length memcopy and brings to a memory corruption.
642  * cpumask_copy() provide safe copy functionality.
643  *
644  * Note that there is another evil here: If you define a cpumask_var_t
645  * as a percpu variable then the way to obtain the address of the cpumask
646  * structure differently influences what this_cpu_* operation needs to be
647  * used. Please use this_cpu_cpumask_var_t in those cases. The direct use
648  * of this_cpu_ptr() or this_cpu_read() will lead to failures when the
649  * other type of cpumask_var_t implementation is configured.
650  */
651 #ifdef CONFIG_CPUMASK_OFFSTACK
652 typedef struct cpumask *cpumask_var_t;
653 
654 #define this_cpu_cpumask_var_ptr(x) this_cpu_read(x)
655 
656 bool alloc_cpumask_var_node(cpumask_var_t *mask, gfp_t flags, int node);
657 bool alloc_cpumask_var(cpumask_var_t *mask, gfp_t flags);
658 bool zalloc_cpumask_var_node(cpumask_var_t *mask, gfp_t flags, int node);
659 bool zalloc_cpumask_var(cpumask_var_t *mask, gfp_t flags);
660 void alloc_bootmem_cpumask_var(cpumask_var_t *mask);
661 void free_cpumask_var(cpumask_var_t mask);
662 void free_bootmem_cpumask_var(cpumask_var_t mask);
663 
664 #else
665 typedef struct cpumask cpumask_var_t[1];
666 
667 #define this_cpu_cpumask_var_ptr(x) this_cpu_ptr(x)
668 
669 static inline bool alloc_cpumask_var(cpumask_var_t *mask, gfp_t flags)
670 {
671         return true;
672 }
673 
674 static inline bool alloc_cpumask_var_node(cpumask_var_t *mask, gfp_t flags,
675                                           int node)
676 {
677         return true;
678 }
679 
680 static inline bool zalloc_cpumask_var(cpumask_var_t *mask, gfp_t flags)
681 {
682         cpumask_clear(*mask);
683         return true;
684 }
685 
686 static inline bool zalloc_cpumask_var_node(cpumask_var_t *mask, gfp_t flags,
687                                           int node)
688 {
689         cpumask_clear(*mask);
690         return true;
691 }
692 
693 static inline void alloc_bootmem_cpumask_var(cpumask_var_t *mask)
694 {
695 }
696 
697 static inline void free_cpumask_var(cpumask_var_t mask)
698 {
699 }
700 
701 static inline void free_bootmem_cpumask_var(cpumask_var_t mask)
702 {
703 }
704 #endif /* CONFIG_CPUMASK_OFFSTACK */
705 
706 /* It's common to want to use cpu_all_mask in struct member initializers,
707  * so it has to refer to an address rather than a pointer. */
708 extern const DECLARE_BITMAP(cpu_all_bits, NR_CPUS);
709 #define cpu_all_mask to_cpumask(cpu_all_bits)
710 
711 /* First bits of cpu_bit_bitmap are in fact unset. */
712 #define cpu_none_mask to_cpumask(cpu_bit_bitmap[0])
713 
714 #define for_each_possible_cpu(cpu) for_each_cpu((cpu), cpu_possible_mask)
715 #define for_each_online_cpu(cpu)   for_each_cpu((cpu), cpu_online_mask)
716 #define for_each_present_cpu(cpu)  for_each_cpu((cpu), cpu_present_mask)
717 
718 /* Wrappers for arch boot code to manipulate normally-constant masks */
719 void set_cpu_possible(unsigned int cpu, bool possible);
720 void set_cpu_present(unsigned int cpu, bool present);
721 void set_cpu_online(unsigned int cpu, bool online);
722 void set_cpu_active(unsigned int cpu, bool active);
723 void init_cpu_present(const struct cpumask *src);
724 void init_cpu_possible(const struct cpumask *src);
725 void init_cpu_online(const struct cpumask *src);
726 
727 /**
728  * to_cpumask - convert an NR_CPUS bitmap to a struct cpumask *
729  * @bitmap: the bitmap
730  *
731  * There are a few places where cpumask_var_t isn't appropriate and
732  * static cpumasks must be used (eg. very early boot), yet we don't
733  * expose the definition of 'struct cpumask'.
734  *
735  * This does the conversion, and can be used as a constant initializer.
736  */
737 #define to_cpumask(bitmap)                                              \
738         ((struct cpumask *)(1 ? (bitmap)                                \
739                             : (void *)sizeof(__check_is_bitmap(bitmap))))
740 
741 static inline int __check_is_bitmap(const unsigned long *bitmap)
742 {
743         return 1;
744 }
745 
746 /*
747  * Special-case data structure for "single bit set only" constant CPU masks.
748  *
749  * We pre-generate all the 64 (or 32) possible bit positions, with enough
750  * padding to the left and the right, and return the constant pointer
751  * appropriately offset.
752  */
753 extern const unsigned long
754         cpu_bit_bitmap[BITS_PER_LONG+1][BITS_TO_LONGS(NR_CPUS)];
755 
756 static inline const struct cpumask *get_cpu_mask(unsigned int cpu)
757 {
758         const unsigned long *p = cpu_bit_bitmap[1 + cpu % BITS_PER_LONG];
759         p -= cpu / BITS_PER_LONG;
760         return to_cpumask(p);
761 }
762 
763 #define cpu_is_offline(cpu)     unlikely(!cpu_online(cpu))
764 
765 #if NR_CPUS <= BITS_PER_LONG
766 #define CPU_BITS_ALL                                            \
767 {                                                               \
768         [BITS_TO_LONGS(NR_CPUS)-1] = BITMAP_LAST_WORD_MASK(NR_CPUS)     \
769 }
770 
771 #else /* NR_CPUS > BITS_PER_LONG */
772 
773 #define CPU_BITS_ALL                                            \
774 {                                                               \
775         [0 ... BITS_TO_LONGS(NR_CPUS)-2] = ~0UL,                \
776         [BITS_TO_LONGS(NR_CPUS)-1] = BITMAP_LAST_WORD_MASK(NR_CPUS)     \
777 }
778 #endif /* NR_CPUS > BITS_PER_LONG */
779 
780 /**
781  * cpumap_print_to_pagebuf  - copies the cpumask into the buffer either
782  *      as comma-separated list of cpus or hex values of cpumask
783  * @list: indicates whether the cpumap must be list
784  * @mask: the cpumask to copy
785  * @buf: the buffer to copy into
786  *
787  * Returns the length of the (null-terminated) @buf string, zero if
788  * nothing is copied.
789  */
790 static inline ssize_t
791 cpumap_print_to_pagebuf(bool list, char *buf, const struct cpumask *mask)
792 {
793         return bitmap_print_to_pagebuf(list, buf, cpumask_bits(mask),
794                                       nr_cpu_ids);
795 }
796 
797 #if NR_CPUS <= BITS_PER_LONG
798 #define CPU_MASK_ALL                                                    \
799 (cpumask_t) { {                                                         \
800         [BITS_TO_LONGS(NR_CPUS)-1] = BITMAP_LAST_WORD_MASK(NR_CPUS)     \
801 } }
802 #else
803 #define CPU_MASK_ALL                                                    \
804 (cpumask_t) { {                                                         \
805         [0 ... BITS_TO_LONGS(NR_CPUS)-2] = ~0UL,                        \
806         [BITS_TO_LONGS(NR_CPUS)-1] = BITMAP_LAST_WORD_MASK(NR_CPUS)     \
807 } }
808 #endif /* NR_CPUS > BITS_PER_LONG */
809 
810 #define CPU_MASK_NONE                                                   \
811 (cpumask_t) { {                                                         \
812         [0 ... BITS_TO_LONGS(NR_CPUS)-1] =  0UL                         \
813 } }
814 
815 #define CPU_MASK_CPU0                                                   \
816 (cpumask_t) { {                                                         \
817         [0] =  1UL                                                      \
818 } }
819 
820 #endif /* __LINUX_CPUMASK_H */
821 
```

```
  1 /* CPU control.
  2  * (C) 2001, 2002, 2003, 2004 Rusty Russell
  3  *
  4  * This code is licenced under the GPL.
  5  */
  6 #include <linux/proc_fs.h>
  7 #include <linux/smp.h>
  8 #include <linux/init.h>
  9 #include <linux/notifier.h>
 10 #include <linux/sched.h>
 11 #include <linux/unistd.h>
 12 #include <linux/cpu.h>
 13 #include <linux/oom.h>
 14 #include <linux/rcupdate.h>
 15 #include <linux/export.h>
 16 #include <linux/bug.h>
 17 #include <linux/kthread.h>
 18 #include <linux/stop_machine.h>
 19 #include <linux/mutex.h>
 20 #include <linux/gfp.h>
 21 #include <linux/suspend.h>
 22 #include <linux/lockdep.h>
 23 #include <linux/tick.h>
 24 #include <trace/events/power.h>
 25 
 26 #include "smpboot.h"
 27 
 28 #ifdef CONFIG_SMP
 29 /* Serializes the updates to cpu_online_mask, cpu_present_mask */
 30 static DEFINE_MUTEX(cpu_add_remove_lock);
 31 
 32 /*
 33  * The following two APIs (cpu_maps_update_begin/done) must be used when
 34  * attempting to serialize the updates to cpu_online_mask & cpu_present_mask.
 35  * The APIs cpu_notifier_register_begin/done() must be used to protect CPU
 36  * hotplug callback (un)registration performed using __register_cpu_notifier()
 37  * or __unregister_cpu_notifier().
 38  */
 39 void cpu_maps_update_begin(void)
 40 {
 41         mutex_lock(&cpu_add_remove_lock);
 42 }
 43 EXPORT_SYMBOL(cpu_notifier_register_begin);
 44 
 45 void cpu_maps_update_done(void)
 46 {
 47         mutex_unlock(&cpu_add_remove_lock);
 48 }
 49 EXPORT_SYMBOL(cpu_notifier_register_done);
 50 
 51 static RAW_NOTIFIER_HEAD(cpu_chain);
 52 
 53 /* If set, cpu_up and cpu_down will return -EBUSY and do nothing.
 54  * Should always be manipulated under cpu_add_remove_lock
 55  */
 56 static int cpu_hotplug_disabled;
 57 
 58 #ifdef CONFIG_HOTPLUG_CPU
 59 
 60 static struct {
 61         struct task_struct *active_writer;
 62         /* wait queue to wake up the active_writer */
 63         wait_queue_head_t wq;
 64         /* verifies that no writer will get active while readers are active */
 65         struct mutex lock;
 66         /*
 67          * Also blocks the new readers during
 68          * an ongoing cpu hotplug operation.
 69          */
 70         atomic_t refcount;
 71 
 72 #ifdef CONFIG_DEBUG_LOCK_ALLOC
 73         struct lockdep_map dep_map;
 74 #endif
 75 } cpu_hotplug = {
 76         .active_writer = NULL,
 77         .wq = __WAIT_QUEUE_HEAD_INITIALIZER(cpu_hotplug.wq),
 78         .lock = __MUTEX_INITIALIZER(cpu_hotplug.lock),
 79 #ifdef CONFIG_DEBUG_LOCK_ALLOC
 80         .dep_map = {.name = "cpu_hotplug.lock" },
 81 #endif
 82 };
 83 
 84 /* Lockdep annotations for get/put_online_cpus() and cpu_hotplug_begin/end() */
 85 #define cpuhp_lock_acquire_read() lock_map_acquire_read(&cpu_hotplug.dep_map)
 86 #define cpuhp_lock_acquire_tryread() \
 87                                   lock_map_acquire_tryread(&cpu_hotplug.dep_map)
 88 #define cpuhp_lock_acquire()      lock_map_acquire(&cpu_hotplug.dep_map)
 89 #define cpuhp_lock_release()      lock_map_release(&cpu_hotplug.dep_map)
 90 
 91 
 92 void get_online_cpus(void)
 93 {
 94         might_sleep();
 95         if (cpu_hotplug.active_writer == current)
 96                 return;
 97         cpuhp_lock_acquire_read();
 98         mutex_lock(&cpu_hotplug.lock);
 99         atomic_inc(&cpu_hotplug.refcount);
100         mutex_unlock(&cpu_hotplug.lock);
101 }
102 EXPORT_SYMBOL_GPL(get_online_cpus);
103 
104 bool try_get_online_cpus(void)
105 {
106         if (cpu_hotplug.active_writer == current)
107                 return true;
108         if (!mutex_trylock(&cpu_hotplug.lock))
109                 return false;
110         cpuhp_lock_acquire_tryread();
111         atomic_inc(&cpu_hotplug.refcount);
112         mutex_unlock(&cpu_hotplug.lock);
113         return true;
114 }
115 EXPORT_SYMBOL_GPL(try_get_online_cpus);
116 
117 void put_online_cpus(void)
118 {
119         int refcount;
120 
121         if (cpu_hotplug.active_writer == current)
122                 return;
123 
124         refcount = atomic_dec_return(&cpu_hotplug.refcount);
125         if (WARN_ON(refcount < 0)) /* try to fix things up */
126                 atomic_inc(&cpu_hotplug.refcount);
127 
128         if (refcount <= 0 && waitqueue_active(&cpu_hotplug.wq))
129                 wake_up(&cpu_hotplug.wq);
130 
131         cpuhp_lock_release();
132 
133 }
134 EXPORT_SYMBOL_GPL(put_online_cpus);
135 
136 /*
137  * This ensures that the hotplug operation can begin only when the
138  * refcount goes to zero.
139  *
140  * Note that during a cpu-hotplug operation, the new readers, if any,
141  * will be blocked by the cpu_hotplug.lock
142  *
143  * Since cpu_hotplug_begin() is always called after invoking
144  * cpu_maps_update_begin(), we can be sure that only one writer is active.
145  *
146  * Note that theoretically, there is a possibility of a livelock:
147  * - Refcount goes to zero, last reader wakes up the sleeping
148  *   writer.
149  * - Last reader unlocks the cpu_hotplug.lock.
150  * - A new reader arrives at this moment, bumps up the refcount.
151  * - The writer acquires the cpu_hotplug.lock finds the refcount
152  *   non zero and goes to sleep again.
153  *
154  * However, this is very difficult to achieve in practice since
155  * get_online_cpus() not an api which is called all that often.
156  *
157  */
158 void cpu_hotplug_begin(void)
159 {
160         DEFINE_WAIT(wait);
161 
162         cpu_hotplug.active_writer = current;
163         cpuhp_lock_acquire();
164 
165         for (;;) {
166                 mutex_lock(&cpu_hotplug.lock);
167                 prepare_to_wait(&cpu_hotplug.wq, &wait, TASK_UNINTERRUPTIBLE);
168                 if (likely(!atomic_read(&cpu_hotplug.refcount)))
169                                 break;
170                 mutex_unlock(&cpu_hotplug.lock);
171                 schedule();
172         }
173         finish_wait(&cpu_hotplug.wq, &wait);
174 }
175 
176 void cpu_hotplug_done(void)
177 {
178         cpu_hotplug.active_writer = NULL;
179         mutex_unlock(&cpu_hotplug.lock);
180         cpuhp_lock_release();
181 }
182 
183 /*
184  * Wait for currently running CPU hotplug operations to complete (if any) and
185  * disable future CPU hotplug (from sysfs). The 'cpu_add_remove_lock' protects
186  * the 'cpu_hotplug_disabled' flag. The same lock is also acquired by the
187  * hotplug path before performing hotplug operations. So acquiring that lock
188  * guarantees mutual exclusion from any currently running hotplug operations.
189  */
190 void cpu_hotplug_disable(void)
191 {
192         cpu_maps_update_begin();
193         cpu_hotplug_disabled = 1;
194         cpu_maps_update_done();
195 }
196 
197 void cpu_hotplug_enable(void)
198 {
199         cpu_maps_update_begin();
200         cpu_hotplug_disabled = 0;
201         cpu_maps_update_done();
202 }
203 
204 #endif  /* CONFIG_HOTPLUG_CPU */
205 
206 /* Need to know about CPUs going up/down? */
207 int __ref register_cpu_notifier(struct notifier_block *nb)
208 {
209         int ret;
210         cpu_maps_update_begin();
211         ret = raw_notifier_chain_register(&cpu_chain, nb);
212         cpu_maps_update_done();
213         return ret;
214 }
215 
216 int __ref __register_cpu_notifier(struct notifier_block *nb)
217 {
218         return raw_notifier_chain_register(&cpu_chain, nb);
219 }
220 
221 static int __cpu_notify(unsigned long val, void *v, int nr_to_call,
222                         int *nr_calls)
223 {
224         int ret;
225 
226         ret = __raw_notifier_call_chain(&cpu_chain, val, v, nr_to_call,
227                                         nr_calls);
228 
229         return notifier_to_errno(ret);
230 }
231 
232 static int cpu_notify(unsigned long val, void *v)
233 {
234         return __cpu_notify(val, v, -1, NULL);
235 }
236 
237 #ifdef CONFIG_HOTPLUG_CPU
238 
239 static void cpu_notify_nofail(unsigned long val, void *v)
240 {
241         BUG_ON(cpu_notify(val, v));
242 }
243 EXPORT_SYMBOL(register_cpu_notifier);
244 EXPORT_SYMBOL(__register_cpu_notifier);
245 
246 void __ref unregister_cpu_notifier(struct notifier_block *nb)
247 {
248         cpu_maps_update_begin();
249         raw_notifier_chain_unregister(&cpu_chain, nb);
250         cpu_maps_update_done();
251 }
252 EXPORT_SYMBOL(unregister_cpu_notifier);
253 
254 void __ref __unregister_cpu_notifier(struct notifier_block *nb)
255 {
256         raw_notifier_chain_unregister(&cpu_chain, nb);
257 }
258 EXPORT_SYMBOL(__unregister_cpu_notifier);
259 
260 /**
261  * clear_tasks_mm_cpumask - Safely clear tasks' mm_cpumask for a CPU
262  * @cpu: a CPU id
263  *
264  * This function walks all processes, finds a valid mm struct for each one and
265  * then clears a corresponding bit in mm's cpumask.  While this all sounds
266  * trivial, there are various non-obvious corner cases, which this function
267  * tries to solve in a safe manner.
268  *
269  * Also note that the function uses a somewhat relaxed locking scheme, so it may
270  * be called only for an already offlined CPU.
271  */
272 void clear_tasks_mm_cpumask(int cpu)
273 {
274         struct task_struct *p;
275 
276         /*
277          * This function is called after the cpu is taken down and marked
278          * offline, so its not like new tasks will ever get this cpu set in
279          * their mm mask. -- Peter Zijlstra
280          * Thus, we may use rcu_read_lock() here, instead of grabbing
281          * full-fledged tasklist_lock.
282          */
283         WARN_ON(cpu_online(cpu));
284         rcu_read_lock();
285         for_each_process(p) {
286                 struct task_struct *t;
287 
288                 /*
289                  * Main thread might exit, but other threads may still have
290                  * a valid mm. Find one.
291                  */
292                 t = find_lock_task_mm(p);
293                 if (!t)
294                         continue;
295                 cpumask_clear_cpu(cpu, mm_cpumask(t->mm));
296                 task_unlock(t);
297         }
298         rcu_read_unlock();
299 }
300 
301 static inline void check_for_tasks(int dead_cpu)
302 {
303         struct task_struct *g, *p;
304 
305         read_lock_irq(&tasklist_lock);
306         do_each_thread(g, p) {
307                 if (!p->on_rq)
308                         continue;
309                 /*
310                  * We do the check with unlocked task_rq(p)->lock.
311                  * Order the reading to do not warn about a task,
312                  * which was running on this cpu in the past, and
313                  * it's just been woken on another cpu.
314                  */
315                 rmb();
316                 if (task_cpu(p) != dead_cpu)
317                         continue;
318 
319                 pr_warn("Task %s (pid=%d) is on cpu %d (state=%ld, flags=%x)\n",
320                         p->comm, task_pid_nr(p), dead_cpu, p->state, p->flags);
321         } while_each_thread(g, p);
322         read_unlock_irq(&tasklist_lock);
323 }
324 
325 struct take_cpu_down_param {
326         unsigned long mod;
327         void *hcpu;
328 };
329 
330 /* Take this CPU down. */
331 static int __ref take_cpu_down(void *_param)
332 {
333         struct take_cpu_down_param *param = _param;
334         int err;
335 
336         /* Ensure this CPU doesn't handle any more interrupts. */
337         err = __cpu_disable();
338         if (err < 0)
339                 return err;
340 
341         cpu_notify(CPU_DYING | param->mod, param->hcpu);
342         /* Give up timekeeping duties */
343         tick_handover_do_timer();
344         /* Park the stopper thread */
345         kthread_park(current);
346         return 0;
347 }
348 
349 /* Requires cpu_add_remove_lock to be held */
350 static int __ref _cpu_down(unsigned int cpu, int tasks_frozen)
351 {
352         int err, nr_calls = 0;
353         void *hcpu = (void *)(long)cpu;
354         unsigned long mod = tasks_frozen ? CPU_TASKS_FROZEN : 0;
355         struct take_cpu_down_param tcd_param = {
356                 .mod = mod,
357                 .hcpu = hcpu,
358         };
359 
360         if (num_online_cpus() == 1)
361                 return -EBUSY;
362 
363         if (!cpu_online(cpu))
364                 return -EINVAL;
365 
366         cpu_hotplug_begin();
367 
368         err = __cpu_notify(CPU_DOWN_PREPARE | mod, hcpu, -1, &nr_calls);
369         if (err) {
370                 nr_calls--;
371                 __cpu_notify(CPU_DOWN_FAILED | mod, hcpu, nr_calls, NULL);
372                 pr_warn("%s: attempt to take down CPU %u failed\n",
373                         __func__, cpu);
374                 goto out_release;
375         }
376 
377         /*
378          * By now we've cleared cpu_active_mask, wait for all preempt-disabled
379          * and RCU users of this state to go away such that all new such users
380          * will observe it.
381          *
382          * For CONFIG_PREEMPT we have preemptible RCU and its sync_rcu() might
383          * not imply sync_sched(), so explicitly call both.
384          *
385          * Do sync before park smpboot threads to take care the rcu boost case.
386          */
387 #ifdef CONFIG_PREEMPT
388         synchronize_sched();
389 #endif
390         synchronize_rcu();
391 
392         smpboot_park_threads(cpu);
393 
394         /*
395          * So now all preempt/rcu users must observe !cpu_active().
396          */
397 
398         err = __stop_machine(take_cpu_down, &tcd_param, cpumask_of(cpu));
399         if (err) {
400                 /* CPU didn't die: tell everyone.  Can't complain. */
401                 smpboot_unpark_threads(cpu);
402                 cpu_notify_nofail(CPU_DOWN_FAILED | mod, hcpu);
403                 goto out_release;
404         }
405         BUG_ON(cpu_online(cpu));
406 
407         /*
408          * The migration_call() CPU_DYING callback will have removed all
409          * runnable tasks from the cpu, there's only the idle task left now
410          * that the migration thread is done doing the stop_machine thing.
411          *
412          * Wait for the stop thread to go away.
413          */
414         while (!per_cpu(cpu_dead_idle, cpu))
415                 cpu_relax();
416         smp_mb(); /* Read from cpu_dead_idle before __cpu_die(). */
417         per_cpu(cpu_dead_idle, cpu) = false;
418 
419         hotplug_cpu__broadcast_tick_pull(cpu);
420         /* This actually kills the CPU. */
421         __cpu_die(cpu);
422 
423         /* CPU is completely dead: tell everyone.  Too late to complain. */
424         tick_cleanup_dead_cpu(cpu);
425         cpu_notify_nofail(CPU_DEAD | mod, hcpu);
426 
427         check_for_tasks(cpu);
428 
429 out_release:
430         cpu_hotplug_done();
431         if (!err)
432                 cpu_notify_nofail(CPU_POST_DEAD | mod, hcpu);
433         return err;
434 }
435 
436 int __ref cpu_down(unsigned int cpu)
437 {
438         int err;
439 
440         cpu_maps_update_begin();
441 
442         if (cpu_hotplug_disabled) {
443                 err = -EBUSY;
444                 goto out;
445         }
446 
447         err = _cpu_down(cpu, 0);
448 
449 out:
450         cpu_maps_update_done();
451         return err;
452 }
453 EXPORT_SYMBOL(cpu_down);
454 #endif /*CONFIG_HOTPLUG_CPU*/
455 
456 /*
457  * Unpark per-CPU smpboot kthreads at CPU-online time.
458  */
459 static int smpboot_thread_call(struct notifier_block *nfb,
460                                unsigned long action, void *hcpu)
461 {
462         int cpu = (long)hcpu;
463 
464         switch (action & ~CPU_TASKS_FROZEN) {
465 
466         case CPU_ONLINE:
467                 smpboot_unpark_threads(cpu);
468                 break;
469 
470         default:
471                 break;
472         }
473 
474         return NOTIFY_OK;
475 }
476 
477 static struct notifier_block smpboot_thread_notifier = {
478         .notifier_call = smpboot_thread_call,
479         .priority = CPU_PRI_SMPBOOT,
480 };
481 
482 void __cpuinit smpboot_thread_init(void)
483 {
484         register_cpu_notifier(&smpboot_thread_notifier);
485 }
486 
487 /* Requires cpu_add_remove_lock to be held */
488 static int _cpu_up(unsigned int cpu, int tasks_frozen)
489 {
490         int ret, nr_calls = 0;
491         void *hcpu = (void *)(long)cpu;
492         unsigned long mod = tasks_frozen ? CPU_TASKS_FROZEN : 0;
493         struct task_struct *idle;
494 
495         cpu_hotplug_begin();
496 
497         if (cpu_online(cpu) || !cpu_present(cpu)) {
498                 ret = -EINVAL;
499                 goto out;
500         }
501 
502         idle = idle_thread_get(cpu);
503         if (IS_ERR(idle)) {
504                 ret = PTR_ERR(idle);
505                 goto out;
506         }
507 
508         ret = smpboot_create_threads(cpu);
509         if (ret)
510                 goto out;
511 
512         ret = __cpu_notify(CPU_UP_PREPARE | mod, hcpu, -1, &nr_calls);
513         if (ret) {
514                 nr_calls--;
515                 pr_warn("%s: attempt to bring up CPU %u failed\n",
516                         __func__, cpu);
517                 goto out_notify;
518         }
519 
520         /* Arch-specific enabling code. */
521         ret = __cpu_up(cpu, idle);
522         if (ret != 0)
523                 goto out_notify;
524         BUG_ON(!cpu_online(cpu));
525 
526         /* Now call notifier in preparation. */
527         cpu_notify(CPU_ONLINE | mod, hcpu);
528 
529 out_notify:
530         if (ret != 0)
531                 __cpu_notify(CPU_UP_CANCELED | mod, hcpu, nr_calls, NULL);
532 out:
533         cpu_hotplug_done();
534 
535         return ret;
536 }
537 
538 int cpu_up(unsigned int cpu)
539 {
540         int err = 0;
541 
542         if (!cpu_possible(cpu)) {
543                 pr_err("can't online cpu %d because it is not configured as may-hotadd at boot time\n",
544                        cpu);
545 #if defined(CONFIG_IA64)
546                 pr_err("please check additional_cpus= boot parameter\n");
547 #endif
548                 return -EINVAL;
549         }
550 
551         err = try_online_node(cpu_to_node(cpu));
552         if (err)
553                 return err;
554 
555         cpu_maps_update_begin();
556 
557         if (cpu_hotplug_disabled) {
558                 err = -EBUSY;
559                 goto out;
560         }
561 
562         err = _cpu_up(cpu, 0);
563 
564 out:
565         cpu_maps_update_done();
566         return err;
567 }
568 EXPORT_SYMBOL_GPL(cpu_up);
569 
570 #ifdef CONFIG_PM_SLEEP_SMP
571 static cpumask_var_t frozen_cpus;
572 
573 int disable_nonboot_cpus(void)
574 {
575         int cpu, first_cpu, error = 0;
576 
577         cpu_maps_update_begin();
578         first_cpu = cpumask_first(cpu_online_mask);
579         /*
580          * We take down all of the non-boot CPUs in one shot to avoid races
581          * with the userspace trying to use the CPU hotplug at the same time
582          */
583         cpumask_clear(frozen_cpus);
584 
585         pr_info("Disabling non-boot CPUs ...\n");
586         for_each_online_cpu(cpu) {
587                 if (cpu == first_cpu)
588                         continue;
589                 trace_suspend_resume(TPS("CPU_OFF"), cpu, true);
590                 error = _cpu_down(cpu, 1);
591                 trace_suspend_resume(TPS("CPU_OFF"), cpu, false);
592                 if (!error)
593                         cpumask_set_cpu(cpu, frozen_cpus);
594                 else {
595                         pr_err("Error taking CPU%d down: %d\n", cpu, error);
596                         break;
597                 }
598         }
599 
600         if (!error) {
601                 BUG_ON(num_online_cpus() > 1);
602                 /* Make sure the CPUs won't be enabled by someone else */
603                 cpu_hotplug_disabled = 1;
604         } else {
605                 pr_err("Non-boot CPUs are not disabled\n");
606         }
607         cpu_maps_update_done();
608         return error;
609 }
610 
611 void __weak arch_enable_nonboot_cpus_begin(void)
612 {
613 }
614 
615 void __weak arch_enable_nonboot_cpus_end(void)
616 {
617 }
618 
619 void __ref enable_nonboot_cpus(void)
620 {
621         int cpu, error;
622 
623         /* Allow everyone to use the CPU hotplug again */
624         cpu_maps_update_begin();
625         cpu_hotplug_disabled = 0;
626         if (cpumask_empty(frozen_cpus))
627                 goto out;
628 
629         pr_info("Enabling non-boot CPUs ...\n");
630 
631         arch_enable_nonboot_cpus_begin();
632 
633         for_each_cpu(cpu, frozen_cpus) {
634                 trace_suspend_resume(TPS("CPU_ON"), cpu, true);
635                 error = _cpu_up(cpu, 1);
636                 trace_suspend_resume(TPS("CPU_ON"), cpu, false);
637                 if (!error) {
638                         pr_info("CPU%d is up\n", cpu);
639                         continue;
640                 }
641                 pr_warn("Error taking CPU%d up: %d\n", cpu, error);
642         }
643 
644         arch_enable_nonboot_cpus_end();
645 
646         cpumask_clear(frozen_cpus);
647 out:
648         cpu_maps_update_done();
649 }
650 
651 static int __init alloc_frozen_cpus(void)
652 {
653         if (!alloc_cpumask_var(&frozen_cpus, GFP_KERNEL|__GFP_ZERO))
654                 return -ENOMEM;
655         return 0;
656 }
657 core_initcall(alloc_frozen_cpus);
658 
659 /*
660  * When callbacks for CPU hotplug notifications are being executed, we must
661  * ensure that the state of the system with respect to the tasks being frozen
662  * or not, as reported by the notification, remains unchanged *throughout the
663  * duration* of the execution of the callbacks.
664  * Hence we need to prevent the freezer from racing with regular CPU hotplug.
665  *
666  * This synchronization is implemented by mutually excluding regular CPU
667  * hotplug and Suspend/Hibernate call paths by hooking onto the Suspend/
668  * Hibernate notifications.
669  */
670 static int
671 cpu_hotplug_pm_callback(struct notifier_block *nb,
672                         unsigned long action, void *ptr)
673 {
674         switch (action) {
675 
676         case PM_SUSPEND_PREPARE:
677         case PM_HIBERNATION_PREPARE:
678                 cpu_hotplug_disable();
679                 break;
680 
681         case PM_POST_SUSPEND:
682         case PM_POST_HIBERNATION:
683                 cpu_hotplug_enable();
684                 break;
685 
686         default:
687                 return NOTIFY_DONE;
688         }
689 
690         return NOTIFY_OK;
691 }
692 
693 
694 static int __init cpu_hotplug_pm_sync_init(void)
695 {
696         /*
697          * cpu_hotplug_pm_callback has higher priority than x86
698          * bsp_pm_callback which depends on cpu_hotplug_pm_callback
699          * to disable cpu hotplug to avoid cpu hotplug race.
700          */
701         pm_notifier(cpu_hotplug_pm_callback, 0);
702         return 0;
703 }
704 core_initcall(cpu_hotplug_pm_sync_init);
705 
706 #endif /* CONFIG_PM_SLEEP_SMP */
707 
708 /**
709  * notify_cpu_starting(cpu) - call the CPU_STARTING notifiers
710  * @cpu: cpu that just started
711  *
712  * This function calls the cpu_chain notifiers with CPU_STARTING.
713  * It must be called by the arch code on the new cpu, before the new cpu
714  * enables interrupts and before the "boot" cpu returns from __cpu_up().
715  */
716 void notify_cpu_starting(unsigned int cpu)
717 {
718         unsigned long val = CPU_STARTING;
719 
720 #ifdef CONFIG_PM_SLEEP_SMP
721         if (frozen_cpus != NULL && cpumask_test_cpu(cpu, frozen_cpus))
722                 val = CPU_STARTING_FROZEN;
723 #endif /* CONFIG_PM_SLEEP_SMP */
724         cpu_notify(val, (void *)(long)cpu);
725 }
726 
727 #endif /* CONFIG_SMP */
728 
729 /*
730  * cpu_bit_bitmap[] is a special, "compressed" data structure that
731  * represents all NR_CPUS bits binary values of 1<<nr.
732  *
733  * It is used by cpumask_of() to get a constant address to a CPU
734  * mask value that has a single bit set only.
735  */
736 
737 /* cpu_bit_bitmap[0] is empty - so we can back into it */
738 #define MASK_DECLARE_1(x)       [x+1][0] = (1UL << (x))
739 #define MASK_DECLARE_2(x)       MASK_DECLARE_1(x), MASK_DECLARE_1(x+1)
740 #define MASK_DECLARE_4(x)       MASK_DECLARE_2(x), MASK_DECLARE_2(x+2)
741 #define MASK_DECLARE_8(x)       MASK_DECLARE_4(x), MASK_DECLARE_4(x+4)
742 
743 const unsigned long cpu_bit_bitmap[BITS_PER_LONG+1][BITS_TO_LONGS(NR_CPUS)] = {
744 
745         MASK_DECLARE_8(0),      MASK_DECLARE_8(8),
746         MASK_DECLARE_8(16),     MASK_DECLARE_8(24),
747 #if BITS_PER_LONG > 32
748         MASK_DECLARE_8(32),     MASK_DECLARE_8(40),
749         MASK_DECLARE_8(48),     MASK_DECLARE_8(56),
750 #endif
751 };
752 EXPORT_SYMBOL_GPL(cpu_bit_bitmap);
753 
754 const DECLARE_BITMAP(cpu_all_bits, NR_CPUS) = CPU_BITS_ALL;
755 EXPORT_SYMBOL(cpu_all_bits);
756 
757 #ifdef CONFIG_INIT_ALL_POSSIBLE
758 static DECLARE_BITMAP(cpu_possible_bits, CONFIG_NR_CPUS) __read_mostly
759         = CPU_BITS_ALL;
760 #else
761 static DECLARE_BITMAP(cpu_possible_bits, CONFIG_NR_CPUS) __read_mostly;
762 #endif
763 const struct cpumask *const cpu_possible_mask = to_cpumask(cpu_possible_bits);
764 EXPORT_SYMBOL(cpu_possible_mask);
765 
766 static DECLARE_BITMAP(cpu_online_bits, CONFIG_NR_CPUS) __read_mostly;
767 const struct cpumask *const cpu_online_mask = to_cpumask(cpu_online_bits);
768 EXPORT_SYMBOL(cpu_online_mask);
769 
770 static DECLARE_BITMAP(cpu_present_bits, CONFIG_NR_CPUS) __read_mostly;
771 const struct cpumask *const cpu_present_mask = to_cpumask(cpu_present_bits);
772 EXPORT_SYMBOL(cpu_present_mask);
773 
774 static DECLARE_BITMAP(cpu_active_bits, CONFIG_NR_CPUS) __read_mostly;
775 const struct cpumask *const cpu_active_mask = to_cpumask(cpu_active_bits);
776 EXPORT_SYMBOL(cpu_active_mask);
777 
778 void set_cpu_possible(unsigned int cpu, bool possible)
779 {
780         if (possible)
781                 cpumask_set_cpu(cpu, to_cpumask(cpu_possible_bits));
782         else
783                 cpumask_clear_cpu(cpu, to_cpumask(cpu_possible_bits));
784 }
785 
786 void set_cpu_present(unsigned int cpu, bool present)
787 {
788         if (present)
789                 cpumask_set_cpu(cpu, to_cpumask(cpu_present_bits));
790         else
791                 cpumask_clear_cpu(cpu, to_cpumask(cpu_present_bits));
792 }
793 
794 void set_cpu_online(unsigned int cpu, bool online)
795 {
796         if (online) {
797                 cpumask_set_cpu(cpu, to_cpumask(cpu_online_bits));
798                 cpumask_set_cpu(cpu, to_cpumask(cpu_active_bits));
799         } else {
800                 cpumask_clear_cpu(cpu, to_cpumask(cpu_online_bits));
801         }
802 }
803 
804 void set_cpu_active(unsigned int cpu, bool active)
805 {
806         if (active)
807                 cpumask_set_cpu(cpu, to_cpumask(cpu_active_bits));
808         else
809                 cpumask_clear_cpu(cpu, to_cpumask(cpu_active_bits));
810 }
811 
812 void init_cpu_present(const struct cpumask *src)
813 {
814         cpumask_copy(to_cpumask(cpu_present_bits), src);
815 }
816 
817 void init_cpu_possible(const struct cpumask *src)
818 {
819         cpumask_copy(to_cpumask(cpu_possible_bits), src);
820 }
821 
822 void init_cpu_online(const struct cpumask *src)
823 {
824         cpumask_copy(to_cpumask(cpu_online_bits), src);
825 }
826 
```
