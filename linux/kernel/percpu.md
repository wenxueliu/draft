
1. 简介

2.6 内核的特性, 每个处理器都拥有自己的变量副本。

2. 优势

每个处理器访问自己的副本, 无需加锁, 可以放入自己的 cache 中, 极大地提高了访问与更新效率. 常用于计数器.

3. 使用

相关头文件：<linux/percpu.h>

(1) 编译期间分配

声明：

    DEFINE_PER_CPU(type, name);

避免进程在访问一个 per-CPU 变量时被切换到另外一个处理器上运行或被其它进程抢占：

    get_cpu_var(变量)++;

    put_cpu_var(变量);

访问其他处理器的变量副本用这个宏：

    per_cpu(变量，int cpu_id);


(2) 动态分配与释放

动态分配 per-CPU 变量:

    void * alloc_percpu(type);
    void * __alloc_percpu(size_t size, size_t align); //可以做特定的内存对齐

释放动态分配的 per-CPU 变量：

    free_percpu();

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

每个 CPU 都有对应的专有的数据区, 在 start_kernel() 中调用 setup_per_cpu_areas() 进行分配和初始化.
通过数据区的首地址与偏移量信息访问 Per-CPU 变量.




    //based on Linux V3.14 source code
    一、概述
    每cpu变量是最简单也是最重要的同步技术。每cpu变量主要是数据结构数组，系统的每个cpu对应数组的一个元素。一个cpu不应该访问与其它cpu对应的数组元素，另外，它可以随意读或修改它自己的元素而不用担心出现竞争条件，因为它是唯一有资格这么做的cpu。这也意味着每cpu变量基本上只能在特殊情况下使用，也就是当它确定在系统的cpu上的数据在逻辑上是独立的时候。

    每个处理器访问自己的副本，无需加锁，可以放入自己的cache中，极大地提高了访问与更新效率。常用于计数器。

    二、相关结构体：
    1.整体的percpu内存管理信息被收集在struct pcpu_alloc_info结构中
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

    2.对于处理器的分组信息，内核使用struct pcpu_group_info结构表示
    struct pcpu_group_info {
        int nr_units; //该组的处理器数目
        //组的percpu内存地址起始地址，即组内处理器数目×处理器percpu虚拟内存递进基本单位
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

    三、per-cpu初始化
    在系统初始化期间，start_kernel()函数中调用setup_per_cpu_areas()函数，用于为每个cpu的per-cpu变量副本分配空间，注意这时alloc内存分配器还没建立起来，该函数调用alloc_bootmem函数为初始化期间的这些变量副本分配物理空间。

    在建立percpu内存管理机制之前要整理出该架构下的处理器信息，包括处理器如何分组、每组对应的处理器位图、静态定义的percpu变量占用内存区域、每颗处理器percpu虚拟内存递进基本单位等信息。

    1.setup_per_cpu_areas()函数，用于为每个cpu的per-cpu变量副本分配空间
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

http://blog.chinaunix.net/uid-27717694-id-4252214.html 
