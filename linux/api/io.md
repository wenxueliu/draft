

###EINTR 信号对 IO 的影响

[参考](http://willko.iteye.com/blog/1691741)
 
对于socket接口(指connect/send/recv/accept..等等后面不重复，不包括不能设置非阻塞的如select)，在阻塞模式下有可能因为发生信号，返回EINTR错误，由用户做重试或终止。

但是，在非阻塞模式下，是否出现这种错误呢？
对此，重温了系统调用、信号、socket相关知识，得出结论是：不会出现。

首先，
1.信号的处理是在用户态下进行的，也就是必须等待一个系统调用执行完了才会执行进程的信号函数，所以就有了信号队列保存未执行的信号
2.用户态下被信号中断时，内核会记录中断地址，信号处理完后，如果进程没有退出则重回这个地址继续执行

socket接口是一个系统调用，也就是即使发生了信号也不会中断，必须等socket接口返回了，进程才能处理信号。
也就是，EINTR错误是socket接口主动抛出来的，不是内核抛的。socket接口也可以选择不返回，自己内部重试之类的..

那阻塞的时候socket接口是怎么处理发生信号的?

举例
socket接口，例如recv接口会做2件事情，
1.检查buffer是否有数据，有则复制清除返回
2.没有数据，则进入睡眠模式，当超时、数据到达、发生错误则唤醒进程处理

socket接口的实现都差不了太多，抽象说
1.资源是否立即可用，有则返回
2.没有，就等...

对于
1.这个时候不管有没信号，也不返回EINTR，只管执行自己的就可以了
2.采用睡眠来等待，发生信号的时候进程会被唤醒，socket接口唤醒后检查有无未处理的信号(signal_pending)会返回EINTR错误。

所以
socket接口并不是被信号中断，只是调用了睡眠，发生信号睡眠会被唤醒通知进程，然后socket接口选择主动退出，这样做可以避免一直阻塞在那里，有退出的机会。非阻塞时不会调用睡眠。


###实例

一些IO系统调用执行时, 如 read 等待输入期间, 如果收到一个信号,系统将中断read, 转而执行信号处理函数. 当信号处理返回后, 系统遇到了一个问题: 是重新开始这个系统调用, 还是让系统调用失败?早期UNIX系统的做法是, 中断系统调用, 并让系统调用失败, 比如read返回 -1, 同时设置 errno 为 EINTR中断了的系统调用是没有完成的调用, 它的失败是临时性的, 如果再次调用则可能成功, 这并不是真正的失败, 所以要对这种情况进行处理, 典型的方式为:



while (1) {

    n = read(fd, buf, BUFSIZ);

    if (n == -1 && errno != EINTR) {

        printf("read error\n");

        break;

    }

    if (n == 0) {

        printf("read done\n");

        break;

    }

}



这样做逻辑比较繁琐, 事实上, 我们可以从信号的角度来解决这个问题,  安装信号的时候, 设置 SA_RESTART属性, 那么当信号处理函数返回后, 被该信号中断的系统调用将自动恢复.

示例程序：

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <error.h>
#include <string.h>
#include <unistd.h>

void sig_handler(int signum)
{
    printf("in handler\n");
    sleep(1);
    printf("handler return\n");
}

int main(int argc, char **argv)
{
    char buf[100];
    int ret;
    struct sigaction action, old_action;

    action.sa_handler = sig_handler;
    sigemptyset(&action.sa_mask);
    action.sa_flags = 0;
    /* 版本1:不设置SA_RESTART属性
     * 版本2:设置SA_RESTART属性 */
    //action.sa_flags |= SA_RESTART;

    sigaction(SIGINT, NULL, &old_action);
    if (old_action.sa_handler != SIG_IGN) {
        sigaction(SIGINT, &action, NULL);
    }

    bzero(buf, 100);

    ret = read(0, buf, 100);
    if (ret == -1) {
        perror("read");
    }

    printf("read %d bytes:\n", ret);
    printf("%s\n", buf);

    return 0;
}
