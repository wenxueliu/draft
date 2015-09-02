##环境
Ubuntu 14.04

##预备知识

makefile 基本用法, 参见 [跟我学 makefile]


##实例

$ cat hello.c

```
	/*
	 * main.c
	 */
	#include<linux/module.h>
	#include<linux/init.h>

	static int __init hello_init(void)
	{
		printk("Hi module!\n");
		return 0;
	}

	static void __exit hello_exit(void)
	{
		printk("Bye module!\n");
	}

	module_init(hello_init);
	module_exit(hello_exit);
```

$ cat Makefile

```
	obj-m += hello.o
	#generate the path
	CURRENT_PATH:=$(shell pwd)
	#the current kernel version number
	LINUX_KERNEL:=$(shell uname -r)
	#the absolute path
	LINUX_KERNEL_PATH:=/usr/src/linux-headers-$(LINUX_KERNEL)
	#complie object
	all:
		make -C $(LINUX_KERNEL_PATH) M=$(CURRENT_PATH) modules
	#clean
	clean:
		make -C $(LINUX_KERNEL_PATH) M=$(CURRENT_PATH) clean
```

$ make

```
	make -C /lib/modules/3.13.0-24-generic/build M=/home/mininet/kernel_test modules
	make[1]: Entering directory `/usr/src/linux-headers-3.13.0-24-generic'
	  CC [M]  /home/mininet/kernel_test/hello.o
	  Building modules, stage 2.
	  MODPOST 1 modules
	  CC      /home/mininet/kernel_test/hello.mod.o
	  LD [M]  /home/mininet/kernel_test/hello.ko
	make[1]: Leaving directory `/usr/src/linux-headers-3.13.0-24-generic'

```

$ cat Makefile

```
	ifneq ($(KERNELRELEASE),)
	mymodule-objs:=hello.c
	obj-m := hello.o
	else
	#generate the path
	CURRENT_PATH:=$(shell pwd)
	#the current kernel version number
	LINUX_KERNEL:=$(shell uname -r)
	#the absolute path
	#LINUX_KERNEL_PATH:=/usr/src/linux-headers-$(LINUX_KERNEL)
	LINUX_KERNEL_PATH:=/lib/modules/$(LINUX_KERNEL)/build
	#complie object
	all:
		make -C $(LINUX_KERNEL_PATH) M=$(CURRENT_PATH) modules
	#clean
	clean:
		make -C $(LINUX_KERNEL_PATH) M=$(CURRENT_PATH) clean
	endif
```

$ make

```
	make -C /lib/modules/3.13.0-24-generic/build M=/home/mininet/kernel_test modules
	make[1]: Entering directory `/usr/src/linux-headers-3.13.0-24-generic'
	  CC [M]  /home/mininet/kernel_test/hello.o
	  Building modules, stage 2.
	  MODPOST 1 modules
	  CC      /home/mininet/kernel_test/hello.mod.o
	  LD [M]  /home/mininet/kernel_test/hello.ko
	make[1]: Leaving directory `/usr/src/linux-headers-3.13.0-24-generic'
```

$ ls

    hello.c  hello.ko  hello.mod.c  hello.mod.o  hello.o  Makefile  modules.order Module.symvers

$ sudo insmod hello.ko; dmesg | tail -1

    [ 8231.779340] Hi module!

$ sudo rmmod hello; dmesg | tail -1

    [ 8317.344809] Bye module!



##原理分析

当我们写完一个 hello 模块, 只要使用以上的 makefile. 然后 make 一下就行. 假设我们把 hello 模块的源代码放在
/home/mininet/kernel_test/ 下. 当我们在这个目录运行 make 时, make 是怎么执行的呢?

首先, 由于 make 后面没有目标, 进入 Makefile, 在第一次读取执行此 Makefile 时, 变量 $(KERNELRELEASE) 并没有
被设置, 因此第一行 ifneq 的条件失败, 从 else 后面的开始执行(make 会在 Makefile 中的第一个不是以 "." 开头的
目标作为默认的目标执行.), 设置PWD、KVER、KDIR等变量, 当 make 遇到标号 all 时, all 成为 make 的目标. 

make 会执行

    $(MAKE) -C $(LINUX_KERNEL_PATH) M=$(CURRENT_PATH) modules

实际上是运行

    make -C /lib/modules/3.13.0-24-generic/build M=/home/mininet/kernel_test modules

/lib/modules/3.13.0-24-generic/build 是一个指向内核源代码 /usr/src/linux-headers-(uname -r) 的符号链接.

$ ls -ld /lib/modules/3.13.0-24-generic/build

    lrwxrwxrwx 1 root root 40 Apr 10  2014 /lib/modules/3.13.0-24-generic/build -> /usr/src/linux-headers-3.13.0-24-generic

这句是 Makefile 的规则: 这里 -C 跳转到 $(LINUX_KERNEL_PATH) 目录下读取那里的 Makefile. "M=" 选项的作用是, 当用户
需要以某个内核为基础编译一个外部模块的话, 需要在 make modules 命令中加入"M=dir", 于是 make 返回到 $(CURRENT_PATH)
目录进行继续读入, 执行当前的 Makefile, 也就是第二次调用 make, 这时的变量 $(KERNELRELEASE) 已经被定义，因此 ifneq 成功,
make 将继续读取紧接在 ifneq 后面的内容:

     mymodule-objs:= hello.c    : 表示 mymodule.o 由 hello.c 生成.
     obj-m += hello.o           : 表示链接后将生成 hello.ko 模块, 这个文件就是要插入内核的模块文件.

可见, make 执行了两次. 第一次执行时是执行 /usr/src/linux-headers-3.13.0-24/ 下的 Makefile; 第二次执行时是读 hello 模块的源代码所在目录
/home/mininet/kernel_test/ 下的 Makefile.


但是还是有不少令人困惑的问题:

1. 这个 KERNELRELEASE 也很令人困惑, 它是什么呢? 在 /home/mininet/kernel_test/Makefile 中是没有定义这个变量的, 所以起作用的是
else...endif 这一段.

在 /usr/src/linux-headers-3.13.0-24/Makefile 中有

    KERNELRELEASE = $(shell cat include/config/kernel.release 2> /dev/null)

$ cat /lib/modules/3.13.0-24-generic/build/include/config/kernel.release

    3.13.0-24-generic

这时候, hello 模块也不再是单独用 make 编译, 而是在内核中用 make modules 进行编译. 用这种方式, 该 Makefile 在单独编译和作为内
核一部分编译时都能正常工作.

###这个 `obj-m := hello.o` 什么时候会执行到呢?

在执行:

    make -C /lib/modules/3.13.0-24-generic/build M=/home/mininet/kernel_test modules

时, make 去 /usr/src/linux-headers-3.13.0-24/Makefile 中寻找目标 modules:

    981 modules: $(vmlinux-dirs) $(if $(KBUILD_BUILTIN),vmlinux) modules.builtin
    982         $(Q)$(AWK) '!x[$$0]++' $(vmlinux-dirs:%=$(objtree)/%/modules.order) > $(objtree)/modules.order
    983         @$(kecho) '  Building modules, stage 2.';
    984         $(Q)$(MAKE) -f $(srctree)/scripts/Makefile.modpost
    985         $(Q)$(MAKE) -f $(srctree)/scripts/Makefile.fwinst obj=firmware __fw_modbuild


    1258 module-dirs := $(addprefix _module_,$(KBUILD_EXTMOD))
    1259 PHONY += $(module-dirs) modules
    1260 $(module-dirs): crmodverdir $(objtree)/Module.symvers
    1261         $(Q)$(MAKE) $(build)=$(patsubst _module_%,%,$@)
    1262
    1263 modules: $(module-dirs)
    1264         @$(kecho) '  Building modules, stage 2.';
    1265         $(Q)$(MAKE) -f $(srctree)/scripts/Makefile.modpost


可以看出, 分两个 stage:

1 编译出 hello.o 文件.
2 生成 hello.mod.o hello.ko

在这过程中, 会调用 make -f scripts/Makefile.build obj=/home/mininet/kernel_test 而在 scripts/Makefile.build 会包含很多文件:

    42 kbuild-dir := $(if $(filter /%,$(src)),$(src),$(srctree)/$(src))
    43 kbuild-file := $(if $(wildcard $(kbuild-dir)/Kbuild),$(kbuild-dir)/Kbuild,$(kbuild-dir)/Makefile)
    44 include $(kbuild-file)

其中就有 /Makefile 这时 KERNELRELEASE 已经存在. 所以执行的是: obj-m:=hello.o

关于 make modules 的更详细的过程可以在 scripts/Makefile.modpost 文件的注释中找到. 如果想查看 make 的整个执行过程, 可以运行make -n.


##模块文件

使用readelf命令查看一下模块文件main.ko的信息。

$ readelf -h hello.o


	ELF Header:
	  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
	  Class:                             ELF64
	  Data:                              2's complement, little endian
	  Version:                           1 (current)
	  OS/ABI:                            UNIX - System V
	  ABI Version:                       0
	  Type:                              REL (Relocatable file)
	  Machine:                           Advanced Micro Devices X86-64
	  Version:                           0x1
	  Entry point address:               0x0
	  Start of program headers:          0 (bytes into file)
	  Start of section headers:          368 (bytes into file)
	  Flags:                             0x0
	  Size of this header:               64 (bytes)
	  Size of program headers:           0 (bytes)
	  Number of program headers:         0
	  Size of section headers:           64 (bytes)
	  Number of section headers:         15
	  Section header string table index: 12

$ readelf -h hello.ko 

	ELF Header:
	  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
	  Class:                             ELF64
	  Data:                              2's complement, little endian
	  Version:                           1 (current)
	  OS/ABI:                            UNIX - System V
	  ABI Version:                       0
	  Type:                              REL (Relocatable file)
	  Machine:                           Advanced Micro Devices X86-64
	  Version:                           0x1
	  Entry point address:               0x0
	  Start of program headers:          0 (bytes into file)
	  Start of section headers:          1344 (bytes into file)
	  Flags:                             0x0
	  Size of this header:               64 (bytes)
	  Size of program headers:           0 (bytes)
	  Number of program headers:         0
	  Size of section headers:           64 (bytes)
	  Number of section headers:         19
	  Section header string table index: 16


##模块数据结构

首先，我们了解一下模块的内核数据结构。

linux3.5.2/kernel/module.h:220

struct module

{

    ……

    /* Startup function. */

    int (*init)(void);

    ……

    /* Destruction function. */

    void (*exit)(void);

    ……

};


模块数据结构的init和exit函数指针记录了我们定义的模块入口函数和出口函数。

###模块加载

模块加载由内核的系统调用init_module完成。

linux3.5.2/kernel/module.c:3009

/* This is where the real work happens */

SYSCALL_DEFINE3(init_module, void __user *, umod,

       unsigned long, len, const char __user *, uargs)

{

    struct module *mod;

    int ret = 0;

    ……

    /* Do all the hard work */

    mod = load_module(umod, len, uargs);//模块加载

    ……

    /* Start the module */

    if (mod->init != NULL)

       ret = do_one_initcall(mod->init);//模块init函数调用

    ……

    return 0;

}

系统调用init_module由SYSCALL_DEFINE3(init_module...)实现，其中有两个关键的函数调用。load_module用于模块加载，do_one_initcall用于回调模块的init函数。

函数load_module的实现为。

linux3.5.2/kernel/module.c:2864

/* Allocate and load the module: note that size of section 0 is always

   zero, and we rely on this for optional sections. */

static struct module *load_module(void __user *umod,

                unsigned long len,

                const char __user *uargs)

{

    struct load_info info = { NULL, };

    struct module *mod;

    long err;

    ……

    /* Copy in the blobs from userspace, check they are vaguely sane. */

    err = copy_and_check(&info, umod, len, uargs);//拷贝到内核

    if (err)

       return ERR_PTR(err);

    /* Figure out module layout, and allocate all the memory. */

    mod = layout_and_allocate(&info);//地址空间分配

    if (IS_ERR(mod)) {

       err = PTR_ERR(mod);

       goto free_copy;

    }

    ……

    /* Fix up syms, so that st_value is a pointer to location. */

    err = simplify_symbols(mod, &info);//符号解析

    if (err < 0)

       goto free_modinfo;

    err = apply_relocations(mod, &info);//重定位

    if (err < 0)

       goto free_modinfo;

    ……

}

函数load_module内有四个关键的函数调用。copy_and_check将模块从用户空间拷贝到内核空间，layout_and_allocate为模块进行地址空间分配，simplify_symbols为模块进行符号解析，apply_relocations为模块进行重定位。

由此可见，模块加载时，内核为模块文件main.ko进行了链接的过程！

至于函数do_one_initcall的实现就比较简单了。

linux3.5.2/kernel/init.c:673

int __init_or_module do_one_initcall(initcall_t fn)

{

    int count = preempt_count();

    int ret;

    if (initcall_debug)

       ret = do_one_initcall_debug(fn);

    else

       ret = fn();//调用init module

    ……

    return ret;

}

即调用了模块的入口函数init。


###模块卸载

模块卸载由内核的系统调用delete_module完成。

linux3.5.2/kernel/module.c:768

SYSCALL_DEFINE2(delete_module, const char __user *, name_user,

        unsigned int, flags)

{

    struct module *mod;

    char name[MODULE_NAME_LEN];

    int ret, forced = 0;

    ……

    /* Final destruction now no one is using it. */

    if (mod->exit != NULL)

       mod->exit();//调用exit module

    ……

    free_module(mod);//卸载模块

    ……

}

通过回调exit完成模块的出口函数功能，最后调用free_module将模块卸载。

##总结

Makefiel要做两件事

1 如果内核没有被编译, 先编译内核.
2 然后编译内核完后, 编译模块.

内核模块其实并不神秘. 传统的用户程序需要编译为可执行程序才能执行, 而模块程序只需要编译为目标文件的形式
便可以加载到内核, 有内核实现模块的链接, 将之转化为可执行代码. 同时, 在内核加载和卸载的过程中, 会通过函
数回调用户定义的模块入口函数和模块出口函数, 实现相应的功能.

##参考

http://yijiuzai.blog.163.com/blog/static/1037567272010101885922998/
http://www.cnblogs.com/fanzhidongyzby/p/3730131.html
http://blog.chinaunix.net/uid-26009923-id-3840337.html
