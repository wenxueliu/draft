
1. 简介

2.6内核的特性，每个处理器都拥有自己的变量副本。
2. 优势

每个处理器访问自己的副本，无需加锁，可以放入自己的cache中，极大地提高了访问与更新效率。常用于计数器。
3. 使用

相关头文件：<linux/percpu.h>

(1) 编译期间分配

声明：

DEFINE_PER_CPU(type, name);

避免进程在访问一个per-CPU变量时被切换到另外一个处理器上运行或被其它进程抢占：

get_cpu_var(变量)++;

put_cpu_var(变量);

访问其他处理器的变量副本用这个宏：

per_cpu(变量，int cpu_id);

 

(2) 动态分配与释放

动态分配per-CPU变量：

void * alloc_percpu(type);

void * __alloc_percpu(size_t size, size_t align); //可以做特定的内存对齐

释放动态分配的per-CPU变量：

free_percpu();

访问动态分配的per-CPU变量的访问通过per_cpu_ptr完成：

per_cpu_ptr(void * per_cpu_var, int cpu_id);

 要想阻塞抢占，使用get_cpu()与put_cpu()即可：

int cpu = get_cpu();

ptr = per_cpu_ptr(per_cpu_var, cpu);

put_cpu();

 

 

(3) 导出Per-CPU变量给模块

EXPORT_PER_CPU_SYMBOL(per_cpu_var);

EXPORT_PER_CPU_SYMBOL_GPL(per_cpu_var);

要在模块中访问这样一个变量，应该这样做声明：

DECLARE_PER_CPU(type, name);
4. 注意

在某些体系结构上，per-CPU变量可使用的地址空间是受限的，要尽量保持这些变量比较小。
5. Per-CPU变量的实现
每个CPU都有对应的专有的数据区，在start_kernel()中调用setup_per_cpu_areas()进行分配和初始化。通过数据区的首地址与偏移量信息访问Per-CPU变量。	
