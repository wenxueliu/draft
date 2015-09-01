
1) EXPORT_SYMBOL(),这个宏也是将函数导出让所有模块都可以使用, 而EXPORT_SYMBOL_GPL() 使用此函数的模块需要 MODULE_LICENSE("GPL") 来声明, 这个宏主要是给有 GPL 认证的模块使用.
2) EXPORT_SYMBOL 标签内定义的函数对全部内核代码公开, 不用修改内核代码就可以在您的内核模块中直接调用.
3) EXPORT_SYMBOL(符号名);  EXPORT_SYMBOL_GPL(符号名)


主要作之一:内核"导出"的符号表,这个表在 insmod 时候会用到.

###打印内核当前的符号表

$ head /proc/kallsyms
    ...
    d8834a24 t snd_free_sgbuf_pages [snd_page_alloc]
    d8834ab5 t snd_malloc_sgbuf_pages [snd_page_alloc]
    c014f906 U kmem_cache_alloc [snd_page_alloc]
    c0106dcd U dma_alloc_coherent [snd_page_alloc]
    ...

其中

第一列是该符号在内核地址空间中的地址;
第二列是符号属性,小写表示局部符号,大写表示全局符号,具体含义参考man nm;
第三列表示符号字符串.

这里只能显示EXPORT_SYMBOL,EXPROT_SYMBOL_GPL处理过的符号.

####System.map内核符号文件

通过 more /boot/System.map 可以查看内核符号列表.

可以显示编译好内核后所有在内核中的符号, 模块中的要另行查看.

####通过nm vmlinux也可以查看内核符号列表

可以显示编译好内核后所有在内核中的符号, 模块中的要另行查看.

####通过nm module_name可以查看模块的符号列表

但是得到是相对地址, 只有加载后才会分配绝对地址. 比如: e1000 模块, 如果 e1000 中的符号经过 EXPORT_SYMBOL 处理,
等加载后, 我们可以通过 more /boot/System.map 和 nm vmlinux 命令查看到, 但是没有 EXPORT_SYMBOL 的, 不能查看.
代码如:

```
    int __gpio_cansleep(unsigned gpio)
    {
        struct gpio_chip *chip; /* only call this on GPIOs that are valid! */
        chip = gpio_to_chip(gpio);
        return chip->can_sleep;
    }
    EXPORT_SYMBOL_GPL(__gpio_cansleep);

    /**
    * __gpio_to_irq() - return the IRQ corresponding to a GPIO
    * @gpio: gpio whose IRQ will be returned (already requested)
    * Context: any
    *
    * This is used directly or indirectly to implement gpio_to_irq().
    * It returns the number of the IRQ signaled by this (input) GPIO,
    * or a negative errno.
    */
    int __gpio_to_irq(unsigned gpio)
    {
    struct gpio_chip *chip;
    chip = gpio_to_chip(gpio);
    return chip->to_irq ? chip->to_irq(chip, gpio - chip->base) : -ENXIO;
    }
    EXPORT_SYMBOL_GPL(__gpio_to_irq);
```

##EXPORT_SYMBOL_GPL导出函数


如果要用 EXPORT_SYMBOL_GPL 导出函数, 使用此函数的模块需要 MODULE_LICENSE("GPL") 或 MODULE_LICENSE("Dual  BSD/GPL") 之后才能在模块中引用来声明

##EXPORT_SYMBOL 导出函数

```
    include/module.h:

    struct kernel_symbol
    {
        unsigned long value;
        const char *name;
    };
    /* For every exported symbol, place a struct in the __ksymtab section */
    #define __EXPORT_SYMBOL(sym, sec)               \
        __CRC_SYMBOL(sym, sec)                  \
        static const char __kstrtab_##sym[]         \
        __attribute__((section("__ksymtab_strings")))       \
        = MODULE_SYMBOL_PREFIX #sym;                        \
        static const struct kernel_symbol __ksymtab_##sym   \
        __attribute_used__                  \
        __attribute__((section("__ksymtab" sec), unused))   \
        = { (unsigned long)&sym, __kstrtab_##sym }
    #define EXPORT_SYMBOL(sym)                  \
        __EXPORT_SYMBOL(sym, "")
    #define EXPORT_SYMBOL_GPL(sym)                  \
        __EXPORT_SYMBOL(sym, "_gpl")
    #endif
```

Analysis:

1. kernel_symbol: 内核函数符号结构体

value:  记录使用 EXPORT_SYMBOL(fun), 函数 fun 的地址
name:  记录函数名称("fun"), 在静态内存中

2. EXPORT_SYMBOL(sym) : 导出函数符号, 保存函数地址和名称

宏等价于: (去掉gcc的一些附加属性, MODULE_SYMBOL_PREFIX该宏一般是"")

```
static const char __kstrtab_sym[] = "sym";
static const struct kernel_symbol __ksymtab_sym =
    {(unsigned long)&sym, __kstrtab_sym }
```

3. gcc 附加属性

1>. __atrribute__ 指定变量或者函数属性. 

__attribute((section("section-name")) var : 编译器将变量 var 放在 section-name 所指定的 data 或者 bssw 段里面.

很容易看出: EXPORT_SYMBOL(sym) 将 sym 函数的名称 __kstrtab_sym 记录在, 段名为 "__kstrtab_strings" 数据段中.
将 sym 所对应的 kernel_symbol 记录在名为 __ksymtab 段中.

EXPORT_SYMBOL_GPL(sym) 和 EXPORT_SYMBOL 不同之处在于 sym 对应的 kenel_symbol 记录在 __ksymtab_gpl 段中.

