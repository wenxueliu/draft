
##select

```
	#include<sys/select.h>
	int select(int maxfdp1, fd_set *restrict readfds, fd_set *restrict writefds,fd_set *restrict exceptfds,
            struct timeval* restrict tvptr);

	#include <sys/select.h>

	int FD_ISSET(int fd, fd_set *fdset);

	//Returns: nonzero if fd is in set, 0 otherwise
	void FD_CLR(int fd, fd_set *fdset);
	void FD_SET(int fd, fd_set *fdset);
	void FD_ZERO(fd_set *fdset);

	struct timeval{

	　　long tv_sec;//second

	　　long tv_usec;//microsecond

	}

    超时参数如果设置为 NULL 则无限等待。
    更多见 man select
```


##示例

下面来是一个简单的select Echo server：

```
// simpleEcho.cpp
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <vector>
#include <string.h>
#include <stdlib.h>
#include <fcntl.h>

#define SEVER_PORT 1314
#define MAX_LINE_LEN 1024

using namespace std;

int main()
{
    struct sockaddr_in cli_addr, server_addr;
    socklen_t sock_len;
    vector<int> client(FD_SETSIZE,-1);

    fd_set rset,allset;
    int listenfd, connfd, sockfd, maxfd, nready, ix,maxid, nrcv,one;
    char addr_str[INET_ADDRSTRLEN], buf[MAX_LINE_LEN];

    bzero(&server_addr,sizeof server_addr);
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    server_addr.sin_port = htons(SEVER_PORT);

    listenfd = socket(AF_INET,SOCK_STREAM,0);

    one = 1;
    setsockopt(listenfd, SOL_SOCKET, SO_REUSEADDR,&one, sizeof(one));

    if( bind(listenfd ,(struct sockaddr *)&server_addr ,sizeof server_addr) < 0 )
    {
        printf("socket bind error" );
        return 0;
    }

    listen(listenfd ,10);

    FD_ZERO(&allset);
    FD_SET(listenfd ,&allset);

    maxfd = listenfd;
    maxid = -1;

    while(1)
    {
        rset = allset; //!
        nready = select (maxfd + 1, &rset,NULL,NULL,NULL);

        if ( nready < 0 )
        {
                printf("select error! \n");
                exit(1);
        }

        if(FD_ISSET (listenfd, &rset))
        {
            sock_len = sizeof cli_addr;
            connfd = accept(listenfd, (struct sockaddr *)&cli_addr, &sock_len);

            printf("recieve from : %s at port %d\n",
                    inet_ntop(AF_INET,&cli_addr .sin_addr ,addr_str ,INET_ADDRSTRLEN ),
                    cli_addr.sin_port );

            for(ix = 0 ; ix < static_cast<int>(client.size()); ix++)
            {
                if(client[ix] < 0 )
                {
                    client[ix] = connfd ;
                    break;
                }
            }

            printf("client[%d] = %d\n" ,ix ,connfd );

            if( FD_SETSIZE == ix)
            {
                printf("too many client! \n" );
                exit(1 );
            }

            if( connfd > maxfd )
            {
                maxfd = connfd;
            }

            FD_SET(connfd, &allset );

            if(ix > maxid )
            {
                maxid = ix;
            }

            if(--nready == 0)
            {
                continue;
            }

        }

        for(ix = 0 ; ix <= maxid; ix++)  //<=
        {
            if((sockfd = client [ix ]) < 0)
            {
                continue;
            }

            if(FD_ISSET (sockfd ,&rset ))
            {
                if( 0 == (nrcv = read(sockfd,buf,MAX_LINE_LEN )))
                {
                        close(sockfd);
                        client[ix] = -1 ;
                        FD_CLR(sockfd ,&allset );
                }
                else
                {
                        printf("RECIEVE: %s \n" ,buf );
                        write(sockfd,buf,nrcv);
                }
            }

            if(--nready == 0)
            {
                break;
            }
        }

    }
    return 0;
}
```

在使用select 的时候要注意两点：

第一个参数需要是当前所关心的文件描述符中最大的一个+1

第二需要注意的是 select 的中间3个参数采用了 "value-result"(UNP1的说法)的方式,
设置了关心的文件描述符进行 select, select 返回之后对应描述的 fdset 中只有有事
件发生的对应 fd 会被设置, 其它关心但是没有事件发生的描述符将会从 fdset 中清除掉,
如果不进行重新赋值, 下次 select 就不会关注这些描述符了, 因此上述代码中 allset
每次对 rset 进行复制.


##调试

来看看如果只在 while(1) 之前设置 rset, 在 while(1) 中不在每次 select 之前赋值会
发生什么, 在控制台输入:

    $strace ./simpleEcho

另外打开一个控制台窗口输入:

    $nc localhost 1314

这作为一个连接 Echo server 的 client, 然后输入你想发往 Echo Server 内容.

关键我们来看一下 Echo server 的情况:


可以看到 select 首先关注的文件描述符 fd == 3，该描述符是listenfd，然后有client连过来，select关注了 fd 3 和 4，4是accept函数打开的用于与client通信的描述符，当client向server写数据之后select关注的描述就只剩下 fd 4了，也就是当前处于连接状态的描述符，如果client主动关闭，select返回之后，下次监听就没有关注的描述符了，可见select函数的“value-result” 返回方式是这样工作的：每次只返回监听描述符中处于active的，其它处于监听的但是当前没有事件发生的描述符则会从监听的fdset中清除掉。因此在每次select之前需要给关注的fdset重新赋值。

　　注1：在进行系统调用调试的时候 strace 是一个利器，简单使用方式如上面在运行程序之前加上 strace 即可。在调试代码逻辑的时候当然还是使用gdb了。

　　注2：Netcat 或者叫 nc 是 Linux 下的一个用于调试和检查网络工具包。可用于创建 TCP/IP 连接，最大的用途就是用来处理 TCP/UDP 套接字。

　　

　　select 什么时候会处于准备好并返回呢？ UNPv1 上进行了详细介绍：

　　下面四个条件任何一个满足的时候套件字准备好读：

　　1. 套接口接受缓冲区的数据字节数大于等于套接口接受缓冲区的低潮限度当前值。对这样的套接口读操作将不阻塞并返回一个大于0的值（既准备好读入的数据量）。我们可以用套接口选项SO_RCVLOWAT来设置此低潮限度，对于TCP和UDP套接口，其缺省值为1。

　　2. 连接的读这一半关闭（也就是接收了FIN的TCP连接）。对这样的套接口读操作将不阻塞并返回0（记文件结束符）。

　　3. 套接口是一个监听的套接口且已完成的连接数为非0。正常情况下这样的套接口上的accpet不会被阻塞。

　　4. 有一个套接口错误待处理。对这样的套接口操作将不阻塞并返回一个错误-1，errno设置成明确的错误条件。

 

　　以下三个条件的任何一个满足时，套接口准备好写操作：

　　1. 套接口发送缓冲区中可用空间的字节数大于等于套接口发送缓冲区低潮限度的当前值，且或者（i)套接口已连接，或者（ii）套接口不需要连接（例如UDP套接字）。这意味着，如果我们将这样的套接口设置为非阻塞，写操作将不阻塞且返回一个正值（例如由传输层传入的字节数）。我们可以用套接口选项SO_SNDLOWAT来设置此低潮限度，对于TCP和UDP套接口其缺省值为2048.

　　2. 连接的写这一半关闭，对这样的套接口写操作将产生信号SIGPIPE。

　　3. 有一个套接口错误待处理。对这样的套接口操作写操作将不阻塞且返回一个错误-1，errno设置成明确的错误条件。这些待处理的错误也可通过指定套接口选项SO_ERROR调用getsockopt来取得并清除。

　　

　　如果一个套接口存在带外数据或者仍处于带外标记，那他有异常条件待处理。
