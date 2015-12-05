
###Why write memory which is mmaped from file can be blocked?

最近在调试一个应用层程序的时候发现, 尝试修改一个内存变量居然可能会耗时几百ms.
这个变量对应的内存是 mmap 的一个文件, 并且这个文件确定已经在 pagecache 中.

###mmap syscall

这里以 SLES11 SP2 3.0.80 内核, ext4 文件系统为例. ext4 文件系统 file_operations=ext4_file_operations,
对应的 mmap 函数为 ext4_file_mmap.

    mm/mmap.c mmap_pgoff---->do_mmap_pgoff---->mmap_region---->file->f_op->mmap---->ext4_file_mmap---->vma->vm_ops = &ext4_file_mmap.

设置vm_ops.fault=filemap_fault; vm_ops.page_mkwrite=ext4_page_mkwrite

###write for first time

第一次写相应的页面的使用, 由于页面还没有到内存中, 所有会触发缺页异常

    do_page_fault-->handle_mm_fault-->handle_pte_offset

因为vma->vm_ops不为空, 所以进入 do_linear_fault

    do_linear_fault---->__do_fault---->vma->vm_ops->fault---->filemap_fault

这里等待从磁盘读取页面到 pagecache. 处理完成后, 由于使用 SHARED 模式 mmap, 所以会进入

    vma->vm_ops->page_mkwrite

    vma->vm_ops->page_mkwrite---->ext4_page_mkwrite

这里会 lock_page() 和 wait_on_page_writeback(), 如果恰好页面被其他进程锁定或者正在写回,
那么会 block, 由于是第一次读取页面, 所以一般不会在这里 block.

###page writeback

    write_cache_pages---->clear_page_dirty_for_io---->page_mkclean---->page_mkclean_file---->page_mkclean_one---->pte_wrprotect

这里会将正在写回的页置为写保护, 当页面回写完成后清除标志.

###write page which is writebacking

由于页面被回写线程置为写保护, 对页面的写操作同样会触发 do_page_fault, 从而走到上面的流程.

    do_page_fault---->handle_mm_fault--->handle_pte_fault

在handle_pte_fault中有如下代码:

    if （flags & FAULT_FLAG_WRITE） {
        if(!pte_write(entry))
            return do_wp_page(mm, …)
        entry = pte_mkdirty(entry);
    }

如果用户尝试写页面(FLAULT_FLAG_WRITE), 并且 pte 是写保护的, 那么就会调用 do_wp_page, 而
do_wp_page 里面会对写且共享的 vma 的页面调用 page_mkwrite.

page_mkwrite 里面会调用 lock_page 和 wait_on_page_writeback(), 从而导致等待页面写回后才可以完成写操作.

###mmap manual

如果使用 SHARE 共享模式 mmap 文件, 那么对这块内存的操作是无法保证实时性的. 如果磁盘IO比较大, 可能导致
回写页面耗费几百ms, 对应的内存操作也就会被 block 几百ms.

##参考

http://blog.chinaunix.net/uid-20662820-id-3873318.html
