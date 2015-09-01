Linux将所有外部设备看成是一类特殊文件，称之为“设备文件”，如果说系统调用是Linux内核和应用程序之间的接口，那么设备驱动程序则可以看成是 Linux内核与外部设备之间的接口。设备驱动程序向应用程序屏蔽了硬件在实现上的细节，使得应用程序可以像操作普通文件一样来操作外部设备。

1. 字符设备和块设备

Linux抽象了对硬件的处理，所有的硬件设备都可以像普通文件一样来看待：它们可以使用和操作文件相同的、标准的系统调用接口来完成打开、关闭、读写和 I/O控制操作，而驱动程序的主要任务也就是要实现这些系统调用函数。Linux系统中的所有硬件设备都使用一个特殊的设备文件来表示，例如，系统中的第 一个IDE硬盘使用/dev/hda表示。每个设备文件对应有两个设备号：一个是主设备号，标识该设备的种类，也标识了该设备所使用的驱动程序；另一个是 次设备号，标识使用同一设备驱动程序的不同硬件设备。设备文件的主设备号必须与设备驱动程序在登录该设备时申请的主设备号一致，否则用户进程将无法访问到 设备驱动程序。

在Linux操作系统下有两类主要的设备文件：一类是字符设备，另一类则是块设备。字符设备是以字节为单位逐个进行I/O操作的设备，在对字符设备发出读 写请求时，实际的硬件I/O紧接着就发生了，一般来说字符设备中的缓存是可有可无的，而且也不支持随机访问。块设备则是利用一块系统内存作为缓冲区，当用 户进程对设备进行读写请求时，驱动程序先查看缓冲区中的内容，如果缓冲区中的数据能满足用户的要求就返回相应的数据，否则就调用相应的请求函数来进行实际 的I/O操作。块设备主要是针对磁盘等慢速设备设计的，其目的是避免耗费过多的CPU时间来等待操作的完成。一般说来，PCI卡通常都属于字符设备。

2. 设备驱动程序接口

Linux中的I/O子系统向内核中的其他部分提供了一个统一的标准设备接口，这是通过include/linux/fs.h中的数据结构file_operations来完成的：

```
struct file_operations {
     struct module *owner;
     loff_t (*llseek) (struct file *, loff_t, int);
     ssize_t (*read) (struct file *, char __user *, size_t, loff_t *);
     ssize_t (*write) (struct file *, const char __user *, size_t, loff_t *);
     ssize_t (*aio_read) (struct kiocb *, const struct iovec *, unsigned long, loff_t);
     ssize_t (*aio_write) (struct kiocb *, const struct iovec *, unsigned long, loff_t);
     int (*readdir) (struct file *, void *, filldir_t);
     unsigned int (*poll) (struct file *, struct poll_table_struct *);
     long (*unlocked_ioctl) (struct file *, unsigned int, unsigned long);
     long (*compat_ioctl) (struct file *, unsigned int, unsigned long);
     int (*mmap) (struct file *, struct vm_area_struct *);
     int (*open) (struct inode *, struct file *);
     int (*flush) (struct file *, fl_owner_t id);
     int (*release) (struct inode *, struct file *);
     int (*fsync) (struct file *, loff_t, loff_t, int datasync);
     int (*aio_fsync) (struct kiocb *, int datasync);
     int (*fasync) (int, struct file *, int);
     int (*lock) (struct file *, int, struct file_lock *);
     ssize_t (*sendpage) (struct file *, struct page *, int, size_t, loff_t *, int);
     unsigned long (*get_unmapped_area)(struct file *, unsigned long, unsigned long, unsigned long, unsigned long);
     int (*check_flags)(int);
     int (*flock) (struct file *, int, struct file_lock *);
     ssize_t (*splice_write)(struct pipe_inode_info *, struct file *, loff_t *, size_t, unsigned int);
     ssize_t (*splice_read)(struct file *, loff_t *, struct pipe_inode_info *, size_t, unsigned int);
     int (*setlease)(struct file *, long, struct file_lock **);
     long (*fallocate)(struct file *file, int mode, loff_t offset,
                 loff_t len);
};
```

当应用程序对设备文件进行诸如open、close、read、write等操作时，Linux内核将通过file_operations结构访问驱动程 序提供的函数。例如，当应用程序对设备文件执行读操作时，内核将调用file_operations结构中的read函数。
 
3. 设备驱动程序模块 

Linux下的设备驱动程序可以按照两种方式进行编译，一种是直接静态编译成内核的一部分，另一种则是编译成可以动态加载的模块。如果编译进内核的话，会增加内核的大小，还要改动内核的源文件，而且不能动态地卸载，不利于调试，所有推荐使用模块方式。 

从本质上来讲，模块也是内核的一部分，它不同于普通的应用程序，不能调用位于用户态下的C或者C++库函数，而只能调用Linux内核提供的函数，在/proc/ksyms中可以查看到内核提供的所有函数。

在以模块方式编写驱动程序时，要实现两个必不可少的函数init_module( )和cleanup_module( )，而且至少要包含和两 个头文件。一般使用LDD3 例程中使用的makefile 作为基本的版本，稍作改变之后用来编译驱动，编译生成的模块（一般为.ko文件）可以使用命令insmod载入Linux内核，从而成为内核的一个组成部分，此时内核会调用 模块中的函数init_module( )。当不需要该模块时，可以使用rmmod命令进行卸载，此进内核会调用模块中的函数cleanup_module( )。任何时候都可以使用命令来lsmod查看目前已经加载的模块以及正在使用该模块的用户数。

 4. 设备驱动程序结构

了解设备驱动程序的基本结构（或者称为框架），对开发人员而言是非常重要的，Linux的设备驱动程序大致可以分为如下几个部分：驱动程序的注册与注销、设备的打开与释放、设备的读写操作、设备的控制操作、设备的中断和轮询处理。

驱动程序的注册与注销 

向系统增加一个驱动程序意味着要赋予它一个主设备号，这可以通过在驱动程序的初始化过程中调用register_chrdev( )或者register_blkdev( )来完成。而在关闭字符设备或者块设备时，则需要通过调用unregister_chrdev( )或unregister_blkdev( )从内核中注销设备，同时释放占用的主设备号。但是现在
程序员都倾向于动态创建设备号和设备结点，动态创建设备号和设备结点需要几个指定的函数，具体
可以参见“Linux字符驱动中动态分配设备号与动态生成设备节点”。

设备的打开与释放 

打开设备是通过调用file_operations结构中的函数open( )来完成的，它是驱动程序用来为今后的操作完成初始化准备工作的。在大部分驱动程序中，open( )通常需要完成下列工作： 

1.检查设备相关错误，如设备尚未准备好等。 

2.如果是第一次打开，则初始化硬件设备。 

3.识别次设备号，如果有必要则更新读写操作的当前位置指针f_ops。 

4.分配和填写要放在file->private_data里的数据结构。 

5.使用计数增1。 

释放设备是通过调用file_operations结构中的函数release( )来完成的，这个设备方法有时也被称为close( )，它的作用正好与open( )相反，通常要完成下列工作： 

1.使用计数减1。 

2.释放在file->private_data中分配的内存。 

3.如果使用计算为0，则关闭设备。 

设备的读写操作 

字符设备的读写操作相对比较简单，直接使用函数read( )和write( )就可以了。但如果是块设备的话，则需要调用函数block_read( )和block_write( )来进行数据读写，这两个函数将向设备请求表中增加读写请求，以便Linux内核可以对请求顺序进行优化。由于是对内存缓冲区而不是直接对设备进行操作 的，因此能很大程度上加快读写速度。如果内存缓冲区中没有所要读入的数据，或者需要执行写操作将数据写入设备，那么就要执行真正的数据传输，这是通过调用 数据结构blk_dev_struct中的函数request_fn( )来完成的。 

设备的控制操作 

除了读写操作外，应用程序有时还需要对设备进行控制，这可以通过设备驱动程序中的函数ioctl( )来完成，ioctl 系统调用有下面的原型: int ioctl(int fd, unsigned long cmd, ...)，第一个参数是文件描述符，第二个参数是具体的命令，一般使用宏定义来确定，第三个参数一般是传递给驱动中处理设备控制操作函数的参数。ioctl( )的用法与具体设备密切关联，因此需要根据设备的实际情况进行具体分析。 

设备的中断和轮询处理

对于不支持中断的硬件设备，读写时需要轮流查询设备状态，以便决定是否继续进行数据传输。如果设备支持中断，则可以按中断方式进行操作。  
 
 
基本框架

在用模块方式实现PCI设备驱动程序时，通常至少要实现以下几个部分：初始化设备模块、设备打开模块、数据读写和控制模块、中断处理模块、设备释放模块、设备卸载模块。下面给出一个典型的PCI设备驱动程序的基本框架，从中不难体会到这几个关键模块是如何组织起来的。

```
/* 指明该驱动程序适用于哪一些PCI设备 */
static struct pci_device_id my_pci_tbl [] __initdata = {
{PCI_VENDOR_ID, PCI_DEVICE_ID,PCI_ANY_ID, PCI_ANY_ID, 0, 0, 0},
{0,}
};

/* 对特定PCI设备进行描述的数据结构 */
struct device_private {
...
}

/* 中断处理模块 */
static irqreturn_t device_interrupt(int irq, void *dev_id)
{
/* ... */
}

/* 设备文件操作接口 */
static struct file_operations device_fops = {
owner: THIS_MODULE, /* demo_fops所属的设备模块 */
read: device_read, /* 读设备操作*/
write: device_write, /* 写设备操作*/
ioctl: device_ioctl, /* 控制设备操作*/
mmap: device_mmap, /* 内存重映射操作*/
open: device_open, /* 打开设备操作*/
release: device_release /* 释放设备操作*/
/* ... */
};

/* 设备模块信息 */
static struct pci_driver my_pci_driver = {
name: DEVICE_MODULE_NAME, /* 设备模块名称 */
id_table: device_pci_tbl, /* 能够驱动的设备列表 */
probe: device_probe, /* 查找并初始化设备 */
remove: device_remove /* 卸载设备模块 */
/* ... */
};

static int __init init_module (void)
{
/* ... */
}

static void __exit cleanup_module (void)
{
     pci_unregister_driver(&my_pci_driver);
}

/* 加载驱动程序模块入口 */
module_init(init_module);

/* 卸载驱动程序模块入口 */
module_exit(cleanup_module);
```

上面这段代码给出了一个典型的PCI设备驱动程序的框架，是一种相对固定的模式。需要注意的是，同加载和卸载模块相关的函数或数据结构都要在前面加上 __init、__exit等标志符，以使同普通函数区分开来。构造出这样一个框架之后，接下去的工作就是如何完成框架内的各个功能模块了。


针对相应设备定义描述该PCI设备的数据结构：

```
struct device_private
{

     /*注册字符驱动和发现PCI设备的时候使用*/
     struct pci_dev  *my_pdev;//
     struct cdev my_cdev;//

     dev_t my_dev;
     atomic_t created;


      /* 用于获取PCI设备配置空间的基本信息 */
     unsigned long mmio_addr;
     unsigned long regs_len;
     int     irq;//中断号
    
     /*用于保存分配给PCI设备的内存空间的信息*/
     dma_addr_t rx_dma_addrp;
     dma_addr_t tx_dma_addrp;


     /*基本的同步手段*/

     spinlock_t lock_send;
     spinlock_t lock_rev;


     /*保存内存空间转换后的地址信息*/
     void __iomem *ioaddr;
     unsigned long virts_addr;


      int open_flag // 设备打开标记

     .....
    
};

```

###初始化设备模块

```
static struct pci_driver my_pci_driver = {
     name:     DRV_NAME,  // 驱动的名字，一般是一个宏定义
     id_table:     my_pci_tbl, //包含了相关物理PCI设备的基本信息，vendorID，deviceID等
     probe:     pci_probe, //用于发现PCI设备
     remove:     __devexit_p(pci_remove), //PCI设备的移除
};
```

// my_pci_tbl 其实是一个 struct pci_device 结构，该结构可以有很多项，每一项代表一个设备

// 该结构可以包含很多项，每一项表明使用该结构的驱动支持的设备

// 注意：需要以一个空的项结尾，也就是：{0,}


```
static struct pci_device_id my_pci_tbl[] __initdata = {
     { vendor_id, device_id, PCI_ANY_ID, PCI_ANY_ID, 0, 0, 0},
     { 0,}
};

 

static int __init init_module(void) 
{
     int result;

     printk(KERN_INFO "my_pci_driver built on %s, %s\n",__DATE__,__TIME__);

     result = pci_register_driver(&my_pci_driver ); //注册设备驱动
     if(result)
          return result;

     return 0;
}
```

###卸载设备模块


```
static void __devexit my_pci_remove(struct pci_dev *pci_dev)
{
     struct device_private *private;
     private= (struct device_private*)pci_get_drvdata(pci_dev);
    
     printk("FCswitch->irq = %d\n",private->irq);
     

     // register_w32 是封装的宏，便于直接操作

     // #define register_w32 (reg, val32)     iowrite32 ((val32), device_private->ioaddr + (reg))

     // 这里的作用是关中断，硬件复位

     register_w32(IntrMask,0x00000001); 
     register_w32(Reg_reset,0x00000001);
    
     // 移除动态创建的设备号和设备
     device_destroy(device_class, device->my_dev);
     class_destroy(device_class);
     

     cdev_del(&private->my_cdev);
     unregister_chrdev_region(priv->my_dev,1);
    
     //清理用于映射到用户空间的内存页面
     for(private->virts_addr = (unsigned long)private->rx_buf_virts;private->virts_addr < (unsigned long)private->rx_buf_virts + BUF_SIZE;private->virts_addr += PAGE_SIZE)
     {
          ClearPageReserved(virt_to_page(FCswitch->virts_addr));
     }
     ...

     // 释放分配的内存空间
     pci_free_consistent(private->my_pdev, BUF_SIZE, private->rx_buf_virts, private->rx_dma_addrp);
     ...    


     free_irq(private->irq, private);


     iounmap(private->ioaddr);
     pci_release_regions(pci_dev);
     kfree(private);
    
     pci_set_drvdata(pci_dev,NULL);
     pci_disable_device(pci_dev);
}
```


// 总之模块卸载函数的职责就是释放一切分配过的资源，根据自己代码的需要进行具体的操作

###PCI设备的探测（probe）

```
static int __devinit pci_probe(struct pci_dev *pci_dev, const struct pci_device_id *pci_id)
{
     unsigned long mmio_start;
     unsigned long mmio_end;
     unsigned long mmio_flags;
     unsigned long mmio_len;
     void __iomem *ioaddr1=NULL;
     struct device_private *private;
     int result;
     printk("probe function is running\n");

     /* 启动PCI设备 */
     if(pci_enable_device(pci_dev))
     {
          printk(KERN_ERR "%s:cannot enable device\n",pci_name(pci_dev));
          return -ENODEV;
     }
     printk( "enable device\n");
     /* 在内核空间中动态申请内存 */
     if((private= kmalloc(sizeof(struct device_private), GFP_KERNEL)) == NULL)
     {
          printk(KERN_ERR "pci_demo: out of memory\n");
          return -ENOMEM;
     }
     memset(private, 0, sizeof(*private));

     private->my_pdev = pci_dev;

     mmio_start = pci_resource_start(pci_dev, 0);
     mmio_end = pci_resource_end(pci_dev, 0);
     mmio_flags = pci_resource_flags(pci_dev, 0);
     mmio_len = pci_resource_len(pci_dev, 0);
     printk("mmio_start is 0x%0x\n",(unsigned int)mmio_start);
     printk("mmio_len is 0x%0x\n",(unsigned int)mmio_len);
     if(!(mmio_flags & IORESOURCE_MEM))
     {
          printk(KERN_ERR "cannot find proper PCI device base address, aborting.\n");
          result = -ENODEV;
          goto err_out;
     }
    

     /* 对PCI区进行标记 ，标记该区域已经分配出去*/
     result = pci_request_regions(pci_dev, DEVICE_NAME);
     if(result)
          goto err_out;

    
     /* 设置成总线主DMA模式 */
     pci_set_master(pci_dev);
    
     /*ioremap 重映射一个物理地址范围到处理器的虚拟地址空间, 使它对内核可用.*/

     ioaddr1 = ioremap(mmio_start, mmio_len);
     if(ioaddr1 == NULL)
     {
          printk(KERN_ERR "%s:cannot remap mmio, aborting\n",pci_name(pci_dev));
          result = -EIO;
          goto err_out;
     }
     printk("ioaddr1 =  0x%0x\n",(unsigned int)ioaddr1);

    

     private->ioaddr = ioaddr1;
     private->mmio_addr = mmio_start;
     private->regs_len = mmio_len;
     private->irq = pci_dev->irq;
     printk("irq is %d\n",pci_dev->irq);


     /* 初始化自旋锁 */
     spin_lock_init(&private->lock_send);
     spin_lock_init(&private->lock_rev);
    

     if(my_register_chrdev(private)) //注：这里的注册字符设备，类似于前面的文章中介绍过的动态创建设备号和动态生成设备结点
     {
          printk("chrdev register fail\n");
          goto err_out;
     }

     //下面这两个函数根据具体的硬件来处理，主要就是内存分配、对硬件进行初始化设置等
     device_init_buf(xx_device);//这个函数主要进行内存分配，内存映射，获取中断
     device_hw_start(xx_device);//这个函数主要是往寄存器中写一些值，复位硬件，开中断，打开DMA等
    

     //把设备指针地址放入PCI设备中的设备指针中，便于后面调用pci_get_drvdata

     pci_set_drvdata(pci_dev, FCswitch);  
      return 0;
err_out:
     printk("error process\n");
      resource_cleanup_dev(FCswitch); //如果出现任何问题，释放已经分配了的资源
     return result;
}
```

// probe函数的作用就是启动pci设备，读取配置空间信息，进行相应的初始化

 

###中断处理

//中断处理，主要就是读取中断寄存器，然后调用中断处理函数来处理中断的下半部分，一般通过tasklet或者workqueue来实现

注意：由于使用request_irq 获得的中断是共享中断，因此在中断处理函数的上半部需要区分是不是该设备发出的中断，这就需要读取中断状态寄存器的值来判断，如果不是该设备发起的中断则 返回 IRQ_NONE

```
static irqreturn_t device_interrupt(int irq, void *dev_id)

{

     ...

　　 if( READ(IntMask) == 0x00000001)
　　 {
　　　　　　return IRQ_NONE;
　　 }
　　 WRITE(IntMask,0x00000001);
    tasklet_schedule(&my_tasklet);  // 需要先申明tasklet 并关联处理函数

     ... 

     return IRQ_HANDLED;

}

```
// 声明tasklet

static void my_tasklet_process(unsigned long unused);
DECLARE_TASKLET(my_tasklet, my_tasklet_process, (unsigned long)&private);//第三个参数为传递给my_tasklet_process 函数的参数


###设备驱动的接口

```
static struct file_operations device_fops = {

     owner:     THIS_MODULE,
     open:       device_open, //打开设备
     ioctl:        device_ioctl,  //设备控制操作
     mmap:     device_mmap,//内存重映射操作
     release:    device_release,// 释放设备
};
```


###打开设备

open 方法提供给驱动来做任何的初始化来准备后续的操作. open 方法的原型是:

int (*open)(struct inode *inode, struct file *filp);
inode 参数有我们需要的信息,以它的 i_cdev 成员的形式, 里面包含我们之前建立的cdev 结构. 唯一的问题是通常我们不想要 cdev 结构本身, 我们需要的是包含 cdev 结构的 device_private 结构. 


```
static int device_open(struct inode *inode, struct file *filp)
{
     struct device_private *private;
     private= container_of(inode->i_cdev, struct device_private, my_cdev);
     filp->private_data = private;

     private->open_flag++;
     try_module_get(THIS_MODULE);
     ...
     return 0;
}
```

###释放设备

release 方法的角色是 open 的反面，设备方法应当进行下面的任务: 

•  释放 open 分配在 filp->private_data 中的任何东西
•  在最后的 close 关闭设备 

```
static int FCswitch_release(struct inode *inode,struct file *filp)

{
     struct device_private *private= filp->private_data;
     private->open_flag--;
 
     module_put(THIS_MODULE);

     printk("pci device close success\n");

     return 0;
}
```


###设备控制操作

PCI设备驱动程序可以通过device_fops 结构中的函数device_ioctl( )，向应用程序提供对硬件进行控制的接口。例如，通过它可以从I/O寄存器里读取一个数据，并传送到用户空间里。

```
static int device_ioctl(struct inode *inode,struct file *filp,unsigned int cmd,unsigned long arg)
{
     int retval = 0;
     struct device_private *FCswitch = filp->private_data;
     
     switch (cmd)
     {

          case DMA_EN://DMA使能
               device_w32(Dma_wr_en, arg);
               break;

          ...

          default:
               retval = -EINVAL;
     }
     return retval;
}
```

###内存映射

```
static int device_mmap(struct file *filp, struct vm_area_struct *vma)
{
     int ret;
     struct device_private *private = filp->private_data;
     vma->vm_page_prot = PAGE_SHARED;//访问权限
     vma->vm_pgoff = virt_to_phys(FCswitch->rx_buf_virts) >> PAGE_SHIFT;//偏移（页帧号）

     ret = remap_pfn_range(vma, vma->vm_start, vma->vm_pgoff, (unsigned long)(vma->vm_end-vma->vm_start), vma->vm_page_prot);
     if(ret!=0)
          return -EAGAIN;

     return 0;
}
```

对 remap_pfn_range()函数的说明：

remap_pfn_range（）函数的原型:
int remap_pfn_range(struct vm_area_struct *vma, unsigned long virt_addr, unsigned long pfn, unsigned long size, pgprot_t prot);

   该函数的功能是创建页表。其中参数vma是内核根据用户的请求自己填写的，而参数addr表示内存映射开始处的虚拟地址，因此，该函数为addr~addr+size之间的虚拟地址构造页表。

   另外，pfn（Page Fram Number）是虚拟地址应该映射到的物理地址的页面号，实际上就是物理地址右移PAGE_SHIFT位。如果PAGE_SHIFT为4kb，则 PAGE_SHIFT为12，因为PAGE_SHIFT等于1<<PAGE_SHIFT。最后一个参数prot是新页所要求的保护属性。
    在驱动程序中，一般能使用remap_pfn_range（）映射内存中的保留页（如X86系统中的640KB~1MB区域）和设备I/O内存。因此，如 果想把kmalloc()申请的内存映射到用户空间，则可以通过SetPageReserved把相应的内存设置为保留后就可以。



##附录

在编写Linux内核驱动程序的时候，如果不动态生成设备号的话，需要自己手动分配设备号，有可能你分配的设备号会与已有设备号相同而产生冲突。因此推荐自动分配设备号。使用下面的函数：

int alloc_chrdev_region(dev_t *dev,　　unsigned baseminor,　　unsigned count,　　const char *name)

该函数需要传递给它指定的第一个次设备号baseminor(一般为0)和要分配的设备数count，以及设备名，调用该函数后自动分配得到的设备号保存在dev中。

当使用了alloc_chrdev_region()动态分配设备号之后，需要依次使用：

 

cdev_init(struct cdev * cdev,const struct file_operations * fops)

和

cdev_add(struct cdev * p,dev_t dev,unsigned count)

将字符设备注册到内核中。通过上面三个函数就可以动态生成设备号了。

在卸载的时候需要使用：unregister_chrdev_region(dev_t from,unsigned count) 来释放设备编号

 

动态创建设备号之后，将驱动加载到内核，通过 ： cat /proc/devices   命令可以查看设备号

 

如果上层应用程序需要访问驱动程序，则需要为该驱动创建设备节点。

如果手动创建设备结点需要这样做：（这里假设通过 cat /proc/devices 发现字符设备 CDEV_ZHU的设备号为 254）

$mknod  /dev/CDEV_ZHU c 254 0

 

如果我们在驱动里面动态创建的话需要这样做：

cdev_class = class_create(owner,name)         // cdev_class 为 struct class 类型

然后使用：

device_create(_cls,_parent,_devt,_device,_fmt)

当动态创建了设备节点之后，在卸载的时候需要使用：

device_destroy(_cls,_device)  和 class_destroy(struct class * cls)

来销毁设备和类。

下面给出一组测试代码：（该组代码实现了应用程序通过打开驱动访问和修改驱动的一个全局变量 “global_var”）

```
/*驱动部分：globalvar.c */

#include <linux/module.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <asm/uaccess.h>
#include <asm/device.h>  //下面这三个头文件是由于动态创建需要加的
#include <linux/device.h>
#include <linux/cdev.h>

 
MODULE_LICENSE("GPL");
 
#define DEVICE_NAME  "CDEV_ZHU"
static struct class *cdev_class;
 
static ssize_t globalvar_read(struct file *, char *, size_t, loff_t*);
static ssize_t globalvar_write(struct file *, const char *, size_t, loff_t*);
 
//初始化字符设备驱动的 file_operations 结构体
struct file_operations globalvar_fops = 
{
    read: globalvar_read,
    write: globalvar_write,
};

static int global_var = 0;      //CDEV_ZHU设备的全局变量

dev_t dev = 0;                 //这里是动态分配设备号和动态创建设备结点需要用到的
struct cdev  dev_c;
 
static int __init globalvar_init(void)
{
    int ret,err;
 
    //注册设备驱动
 
    ret = alloc_chrdev_region(&dev, 0, 1,DEVICE_NAME); //动态分配设备号
    if (ret)
    {
        printk("globalvar register failure\n"); 
 　　 unregister_chrdev_region(dev,1);
 　　 return ret;
    }
    else
    {
        printk("globalvar register success\n");
    }

   cdev_init(&dev_c, &globalvar_fops);
 
   err = cdev_add(&dev_c, dev, 1);

   if(err)
   {
 　　 printk(KERN_NOTICE "error %d adding FC_dev\n",err);
  　　unregister_chrdev_region(dev, 1);
  　　return err;
   }
 
 cdev_class = class_create(THIS_MODULE, DEVICE_NAME);//动态创建设备结点
 if(IS_ERR(cdev_class))
 { 
        printk("ERR:cannot create a cdev_class\n");  
 　　 unregister_chrdev_region(dev, 1);
 　　 return -1;
    }
 device_create(cdev_class,NULL, dev, 0, DEVICE_NAME);
 
    return ret;
}
 
static void __exit globalvar_exit(void)
{
 
    //注销设备驱动 
    
 device_destroy(cdev_class, dev);
 class_destroy(cdev_class);
 unregister_chrdev_region(dev,1);
 printk("globalvar_exit \n");
}
 
static ssize_t globalvar_read(struct file *filp, char *buf, size_t len, loff_t *off)
{
    //将 global_var 从内核空间复制到用户空间
    if(copy_to_user(buf, &global_var, sizeof(int)))
    {
        return    - EFAULT;    
    }  
    return sizeof(int);
}
 
static ssize_t globalvar_write(struct file *filp, const char *buf, size_t len, loff_t *off)
{
    //将用户空间的数据复制到内核空间的 global_var
    if(copy_from_user(&global_var, buf, sizeof(int)))
    {
        return    - EFAULT;
    }  
    return sizeof(int);
}
 
module_init(globalvar_init);
module_exit(globalvar_exit);

/*应用程序： globalvartest.c  */

#include <sys/types.h>
#include <sys/stat.h>
#include <stdio.h>
#include <fcntl.h>
int main()
{
    int fd, num;
    //打开"/dev/CDEV_ZHU"
    fd = open("/dev/CDEV_ZHU", O_RDWR, S_IRUSR | S_IWUSR);
    if (fd != -1 )
    {
      //初次读 global_var
        read(fd, &num, sizeof(int));
        printf("The globalvar is %d\n", num);
 
      //写 global_var
        printf("Please input the num written to globalvar\n");
        scanf("%d", &num);
        write(fd, &num, sizeof(int));
 
      //再次读 global_var
        read(fd, &num, sizeof(int));
        printf("The globalvar is %d\n", num);
 
        //关闭“/dev/CDEV_ZHU”
        close(fd);
    }
    else
    {
        printf("Device open failure\n");
    }

    return 0;
}
```

说明：这个程序是我修改了“深入浅出Linux设备编程”这本书的代码的来的，在项目中使用动态创建设备节点和动态生成设备号比较方便，于是就在这里分享了。

使用一个简单的makefile将(驱动) globalvar.c  编译过后 使用 insmod globalvar.ko 将驱动加载到内核，然后就将globalvartest.c 生成的可执行文件运行起来就可以操作驱动中的全局变量了。不用像书上一样还要在命令行去创建设备节点。

我使用的内核版本是2.6.33.4 。
