
在Linux socket关闭连接的方法有两种分别是shutdown和close，
首先看一下shutdown的定义:
#include
int shutdown(int sockfd,int how);

how的方式有三种分别是
SHUT_RD（0）：关闭sockfd上的读功能，此选项将不允许sockfd进行读操作。
SHUT_WR（1）：关闭sockfd的写功能，此选项将不允许sockfd进行写操作。
SHUT_RDWR（2）：关闭sockfd的读写功能。
成功则返回0，错误返回-1，错误码errno：EBADF表示sockfd不是一个有效描述符；
ENOTCONN表示sockfd未连接；ENOTSOCK表示sockfd是一个文件描述符而不是socket描述符。

close的定义如下：

#include
int close(int fd);
关闭读写。
成功则返回0，错误返回-1，错误码errno：EBADF表示fd不是一个有效描述符；EINTR表示close函数被信号中断；EIO表示一个IO错误。

下面摘用网上的一段话来说明二者的区别：

close-----关闭本进程的socket id，但链接还是开着的，用这个socket id的其它进程还能用这个链接，能读或写这个socket id shutdown--则破坏了socket 链接，读的时候可能侦探到EOF结束符，写的时候可能会收到一个SIGPIPE信号，这个信号可能直到socket buffer被填充了才收到，shutdown还有一个关闭方式的参数，0 不能再读，1不能再写，2 读写都不能。socket 多进程中的shutdown, close使用

当所有的数据操作结束以后，你可以调用close()函数来释放该socket，从而停止在该socket上的任何数据操作：
close(sockfd);

你也可以调用shutdown()函数来关闭该socket。该函数允许你只停止在某个方向上的数据传输，
而一个方向上的数据传输继续进行。如你可以关闭某socket的写操作而允许继续在该socket上接受数据，
直至读入所有数据。

int shutdown(int sockfd,int how);

Sockfd是需要关闭的socket的描述符。参数 how允许为shutdown操作选择以下几种方式：
SHUT_RD：关闭连接的读端。也就是该套接字不再接受数据，任何当前在套接字接受缓冲区的数据将被丢弃。进程将不能对该套接字发出任何读操作。对TCP套接字该调用之后接受到的任何数据将被确认然后无声的丢弃掉。

SHUT_WR:关闭连接的写端，进程不能在对此套接字发出写操作SHUT_RDWR:相当于调用shutdown两次：首先是以SHUT_RD,然后以SHUT_WR使用close中止一个连接，但它只是减少描述符的参考数，并不直接关闭连接，只有当描述符的参考数为0时才关闭连接。shutdown可直接关闭描述符，不考虑描述符的参考数，可选择中止一个方向的连接。

注意:
1>.
如果有多个进程共享一个套接字，close每被调用一次，计数减1，直到计数为0时，
也就是所用进程都调用了close，套接字将被释放。
2>. 
在多进程中如果一个进程中shutdown(sfd, SHUT_RDWR)后其它的进程将无法进行通信.
如果一个进程close(sfd)将不会影响到其它进程. 得自己理解引用计数的用法了. 


更多关于close和shutdown的说明
1，只要TCP栈的读缓冲里还有未读取（read）数据，则调用close时会直接向对端发送RST。
2，shutdown与socket描述符没有关系，即使调用shutdown(fd, SHUT_RDWR)也不会关闭fd，最终还需close(fd)。
3，可以认为shutdown(fd, SHUT_RD)是空操作，因为shutdown后还可以继续从该socket读取数据，这点也许还需要进一步证实。
4，在已发送FIN包后write该socket描述符会引发EPIPE/SIGPIPE。
5，当有多个socket描述符指向同一socket对象时，调用close时首先会递减该对象的引用计数，计数为0时才会发送FIN包结束TCP连接。shutdown不同，只要以SHUT_WR/SHUT_RDWR方式调用即发送FIN包。
6，SO_LINGER与close，当SO_LINGER选项开启但超时值为0时，调用close直接发送RST（这样可以避免进入TIME_WAIT状态，但破坏了TCP协议的正常工作方式），SO_LINGER对shutdown无影响。
7，TCP连接上出现RST与随后可能的TIME_WAIT状态没有直接关系，主动发FIN包方必然会进入TIME_WAIT状态，除非不发送FIN而直接以发送RST结束连接。

http://blog.chinaunix.net/uid-25203957-id-2689372.html
