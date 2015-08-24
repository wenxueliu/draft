
###同 select 比较

对于select, linux/posix_types.h 头文件有这样的宏: #define __FD_SETSIZE 1024;

select 能监听的最大 fd 数量, 在内核编译的时候就确定了的. 若想加大 fd 的数量, 需要调整编译参数, 重新编译内核.

epoll_wait 直接返回被触发的 fd 或对应的一块 buffer, 不需要遍历所有的 fd. epoll的实现中, 用户空间跟内核空间共享内存(mmap), 避免拷贝.

##epoll

###LT 模式下的读和写

既可以为阻塞也可以为非阻塞

###ET模式下的读和写

只能是非阻塞的

读一定要到 EWOULDBLOCK　才能停止
