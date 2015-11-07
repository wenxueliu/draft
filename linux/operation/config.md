
##RedHat OR CentOS

内核参数说明如下:

overcommit_memory 文件指定了内核针对内存分配的策略, 其值可以是0, 1, 2.

0. 表示内核将检查是否有足够的可用内存供应用进程使用;如果有足够的可用内存,内存申请允许;否则,内存申请失败,并把错误返回给应用进程.
1. 表示内核允许分配所有的物理内存,而不管当前的内存状态如何.
2. 表示内核允许分配超过所有物理内存和交换空间总和的内存

###修改方法:

    文件 /etc/sysctl.conf    vm.overcommit_memory=1
    $sysctl vm.overcommit_memory=1
    $echo 1 > /proc/sys/vm/overcommit_memory



Q: Error: Cannot retrieve metalink for repository: epel. Please verify its path and try again

A: 修改文件 "/etc/yum.repos.d/epel.repo"， 将 baseurl 的注释取消， mirrorlist 注释掉

