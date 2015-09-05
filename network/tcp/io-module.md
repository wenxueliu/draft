
术语:

用户态 :
内核态 :
应用程序: 线程或进程


要点:

多线程 VS IO复用

* 内存资源
* CPU 资源

线程池　VS IO　复用

* 长连接
* 短连接


线程池　连接池


##Linux I/O 模型

##IO 矩阵

![IO 模型矩阵](io_module.gif)

同步:
异步:
阻塞:
非阻塞:

POSIX把这两个术语定义如下:

同步: I/O操作导致请求进程阻塞, 直至操作完成
异步: I/O操作不导致请求进程阻塞.

###同步阻塞 I/O

最常用的一个模型是同步阻塞 I/O 模型: 用户空间的应用程序执行一个系统调用, 陷入内核,
系统调用完成, 数据从内核拷贝到用户空间的缓存, 用户空间取数据.

在这个模型中, 除非系统调用完成为止(数据传输完成或发生错误), 否则应用程序会一直阻塞, 调用期间应用程序
处于一种不再消费 CPU 而只是简单等待响应的状态, 因此从处理的角度来看, 这是非常有效的. 

![同步阻塞 I/O 模型典型流程](io_syn_block.gif)

这也是目前应用程序中最为常用的一种模型. 其行为非常容易理解, 其用法对于典型的应用程序来说都非常有效.

以读操作为例:

1. 当用户态的应用程序调用 recvfrom() 或 recv(), 用户态切换到内核态后进行上下文切换 
2. 内核调用 sys_rec() 会一直**阻塞**, 直到响应数据返回
3. 返回的数据首先拷贝到内核的缓冲区, sys_rec() 发现对应内核缓冲区不为空, 系统调用返回
4. 拷贝该数据到用户空间应用程序对应的缓冲区中, 应用程序由于一直在**阻塞**, 当发现缓冲区不为空, 就会解除阻塞.
5. 将缓冲区的数据拷贝到对应的地址.

从上面的描述发现总共有两次阻塞, 用户态阻塞, 内核态阻塞.

我们很容易发现, 进程一旦调用同步阻塞的接口, 该进程就一直等待, 直到完成处理. 在整个过程中, 该进程无法
进行任何其他操作. 在互联网的草莽时代, 每一个新的连接, 就新建立一个进程来处理该连接, 如果存在大量的短连接,
系统由于建立过多的进程, 导致 cpu 上下文切换非常频繁, 严重影响系统的整体性能. 因此 C10K 就是当时那个年代的瓶颈.


缺点:

CPU 利用率不高: 在等待应答期间, 应用程序阻塞不能进行任何操作, 造成CPU 资源浪费.

####服务端

```c server_syn_block.c
    #include <stdio.h>
    #include <stdlib.h>
    #include <errno.h>
    #include <string.h>
    #include <netinet/in.h>
    #include <sys/socket.h>
    #include <unistd.h>

    int main() {
        if (argc != 2) {
            printf("Usage: %s PORT \n",argv[0]);
            return 1;
        }
        int sockfd, new_fd;
        int sin_size, numbytes;
        struct sockaddr_in addr, cliaddr;
        int listen_port = atoi(argv[1]);
        int backlog = 10;

        //创建socket
        if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
            perror("createSocket");
            return -1;
        }

        //初始化socket结构
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(listen_port);
        addr.sin_addr.s_addr = htonl(INADDR_ANY);

        //绑定套接口
        if (bind(sockfd, (struct sockaddr *)&addr, sizeof(struct sockaddr)) == -1) {
            perror("bind");
            return -1;
        }

        //创建监听套接口
        if (listen(sockfd, backlog) == -1) {
            perror("listen");
            return -1;
        }

        printf("server is running!\n");

        char buff[1024];
        //等待连接
        while (1) {
            sin_size = sizeof(struct sockaddr_in);

            //接受连接
            if ((new_fd = accept(sockfd, (struct sockaddr *)&cliaddr, (socklen_t*)&sin_size)) == -1) {
                perror("accept");
                return -1;
            }

            //生成一个子进程来完成和客户端的会话, 父进程继续监听, 也可以通过
            //pthread_creat 通过新线程来完成客户端请求

            if (!fork()) {
                //读取客户端发来的信息
                memset(buff,0,sizeof(buff));
                if ((numbytes = recv(new_fd, buff, sizeof(buff), 0)) == -1) {
                    perror("recv");
                    return -1;
                }
                printf("buff=%s\n",buff);

                //将从客户端接收到的信息再发回客户端
                if (send(new_fd, buff, strlen(buff), 0) == -1) {
                    perror("send");
                }
                close(new_fd);
                return 0;
            }
            //父进程关闭new_fd
            close(new_fd);
        }
        close(sockfd);
    }
```

####客户端

```c client_syn_block.c
    #include <stdio.h>
    #include <stdlib.h>
    #include <errno.h>
    #include <string.h>
    #include <netdb.h>
    #include <sys/types.h>
    #include <netinet/in.h>
    #include <sys/socket.h>
    #include <unistd.h>

    int main(int argc,char *argv[]) {
        if (argc != 3) {
            printf("Usage: %s IP PORT\n",argv[0]);
            return 1;
        }

        int sockfd,numbytes;
        char buf[100] = "hello world";
        struct hostent *host;
        struct sockaddr_in their_addr;

        //将基本名字和地址转换
        host = gethostbyname(argv[1]);

        //建立一个TCP套接口
        if ((sockfd = socket(AF_INET,SOCK_STREAM,0)) == -1) {
            perror("socket");
            exit(1);
        }

        //初始化结构体
        their_addr.sin_family = AF_INET;
        their_addr.sin_port = htons(atoi(argv[2]));
        their_addr.sin_addr = *((struct in_addr *)host->h_addr);
        bzero(&(their_addr.sin_zero),8);

        //和服务器建立连接
        if (connect(sockfd, (struct sockaddr *)&their_addr, sizeof(struct sockaddr)) == -1) {
            perror("connect");
            exit(1);
        }

        //向服务器发送字符串
        if (send(sockfd,buf,strlen(buf),0) == -1) {
            perror("send");
            exit(1);
        }
        memset(buf,0,sizeof(buf));

        //接受从服务器返回的信息
        if ((numbytes = recv(sockfd, buf, 100, 0))==-1) {
            perror("recv");
            exit(1);
        }

        close(sockfd);
        return 0;
    }
```

$ gcc server_syn_block.c -o server_syn_block
$ gcc client_syn_block.c -o client_syn_block
$ sudo strace -e trace=network ./server_syn_block 8001

    socket(PF_INET, SOCK_STREAM, IPPROTO_IP) = 3
    bind(3, {sa_family=AF_INET, sin_port=htons(8001), sin_addr=inet_addr("0.0.0.0")}, 16) = 0
    listen(3, 10)                           = 0
    server is running!
    accept(3, {sa_family=AF_INET, sin_port=htons(40278), sin_addr=inet_addr("127.0.0.1")}, [16]) = 4
    accept(3, buff=hello world 0x7fffcd25f1a0, [16])         = ? ERESTARTSYS (To be restarted if SA_RESTART is set)
    --- SIGCHLD {si_signo=SIGCHLD, si_code=CLD_EXITED, si_pid=19375, si_status=0, si_utime=0, si_stime=0} ---
    accept(3, ^CProcess 19348 detached <detached ...> )

$ sudo strace ./client_syn_block 127.0.0.1 8001

    socket(PF_INET, SOCK_STREAM, IPPROTO_IP) = 3
    connect(3, {sa_family=AF_INET, sin_port=htons(8001), sin_addr=inet_addr("127.0.0.1")}, 16) = 0
    sendto(3, "hello world", 11, 0, NULL, 0) = 11
    recvfrom(3, "hello world", 100, 0, NULL, NULL) = 11
    +++ exited with 0 +++


###同步非阻塞 I/O

同步阻塞 I/O 的一种效率稍低的变种是同步非阻塞 I/O. 在这种模型中, 设备是以非阻塞的形式打开的. 这意味
着 I/O 操作不会立即完成, 操作可能会返回一个错误代码, 说明这个命令不能立即满足(EAGAIN 或 EWOULDBLOCK)

![同步非阻塞 I/O 模型典型流程](io_syn_unblock.gif)


以读操作为例:

1. 当用户态的应用程序调用 recvfrom() 或 recv(), 用户态切换到内核态后进行上下文切换 
2. 内核调用 sys_rec() 没有读到数据, 立即返回给用户态错误码 EWOULDBLOCK, 到步骤3. 如果读到数据, 到步骤4.
3. 用户态从 1 开始, 或放弃, 或做其他事情过会再调用.
4. 返回的数据首先拷贝到内核的缓冲区, sys_rec() 发现对应内核缓冲区不为空, 拷贝内核缓冲区数据到对应地址, 系统调用返回
4. 拷贝该数据到用户空间应用程序对应的缓冲区中
5. 用户态应用程序当发现缓冲区不为空, 将缓冲区的数据拷贝到对应的地址, 就会解除阻塞.

非阻塞的实现是 I/O 命令可能并不会立即满足, 需要应用程序调用许多次来等待操作完成. 这样我们的I/O操作函数
将不断的测试数据是否已经准备好, 如果没有准备好, 继续测试, 直到数据准备好为止. 在这个不断测试的过程中,
会发生大量的系统调用, 占用大量的 CPU 的时间.

如果遇到网络不好的情况, 会极大消耗　CPU, 而网络好的情况下, 同步阻塞也工作得很好, 那就没有存在的价值了么？　
事实是当前辈们发现同步阻塞的问题后, 首先想到的是把阻塞变为非阻塞的, 的确非阻塞在大量请求下,　较同步阻塞还是
有很大的提升, 至少可以极大提高系统的响应性能. 但是很快发现, 如果网络不是很稳定, 系统开销太大, 是否可以在
内核态来做, 至此, IO 复用登山历史舞台.

在现代的 IO 模型中, 一般很少直接使用这种模型, 而是在其他 IO 模型中使用非阻塞 IO 这一特性. 

可以通过 fcntl 控制 socket 描述符属性.

    int flags;
    flag=fcntl(sockfd,F_GETFL,0);
    fcntl(sockfd,F_SETFL,flag|O_NONBLOCK)

非阻塞式I/O模型对4种I/O操作返回的错误
读操作: 接收缓冲区无数据时返回 EWOULDBLOCK
写操作: 发送缓冲区无空间时返回 EWOULDBLOCK; 空间不够时部分拷贝, 返回实际拷贝字节数
建立连接: 启动 3 次握手, 立刻返回错误 EINPROGRESS; 服务器客户端在同一主机上 connect 立即返回成功
接受连接: 没有新连接返回 EWOULDBLOCK


###服务端

```c server_syn_unblock.c

    #include <stdio.h>
    #include <stdlib.h>
    #include <errno.h>
    #include <string.h>
    #include <netinet/in.h>
    #include <sys/socket.h>
    #include <unistd.h>
    #include <fcntl.h>

    int main(int argc, char **argv) {
    	int sockfd, new_fd;
    	int sin_size;
    	struct sockaddr_in addr, cliaddr;
        int listen_port = atoi(argv[1]);
        int backlog = 10;

    	//创建socket
    	if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
    		perror("create socket error");
    		return -1;
    	}

    	//初始化socket结构
    	memset(&addr, 0, sizeof(addr));
    	addr.sin_family = AF_INET;
    	addr.sin_port = htons(listen_port);
    	addr.sin_addr.s_addr = htonl(INADDR_ANY);

    	//绑定套接口
    	if (bind(sockfd, (struct sockaddr *)&addr, sizeof(struct sockaddr)) == -1) {
    		perror("bind");
    		return -1;
    	}

    	//创建监听套接口
    	if (listen(sockfd, backlog) == -1) {
    		perror("listen");
    		return -1;
    	}

    	printf("server is running!\n");

    	char buff[1024];
    	//等待连接
    	while(1) {
    		sin_size = sizeof(struct sockaddr_in);
    		//接受连接
    		if((new_fd = accept(sockfd, (struct sockaddr *)&cliaddr, (socklen_t*)&sin_size))==-1) {
    			perror("accept");
    			return -1;
    		}

    		//生成一个子进程来完成和客户端的会话, 父进程继续监听
    		if(!fork()) {

    			//设置new_fd无阻塞属性
    			int flags;
    			if ((flags = fcntl(new_fd, F_GETFL, 0)) < 0) {
                	perror("fcntl F_GETFL");
                }
        	    flags |= O_NONBLOCK;
          		if(fcntl(new_fd, F_SETFL, flags)<0) {
                	perror("fcntl F_SETFL");
    			}

    			//读取客户端发来的信息
    			memset(buff,0,sizeof(buff));
    			while(1) {
    				if ((recv(new_fd, buff, sizeof(buff),0)) < 0) {
    					if (errno == EWOULDBLOCK) {
    						perror("recv error, wait....");
    						sleep(1);
    						continue;
    					}
    				} else {
    					printf("buff=%s\n",buff);
    				}
    				break;
    			}

    			//发送数据
    			while(1) {
    				if (send(new_fd, buff, strlen(buff), 0) < 0) {
    					if (errno == EWOULDBLOCK) {
                            //这里不能做什么有用的事情, 如果要有很好的响应特性, 唯一的选择就是继续．
    						perror("send error, wait....");
    						sleep(1);
    						continue;
    					}
    				} else {
    					printf("buff=%s\n",buff);
    				}
    				break;
    			}
    			close(new_fd);
    			return 0;
    		}
    		//父进程关闭new_fd
    		close(new_fd);
    	}
    	close(sockfd);
    }
```

TODO: 上面实现并不是非阻塞的正确用法, 事实上可以将所有的 new_fd 添加到一个 recv 和
send 循环链表中, 由两个线程分别不断地遍历这个链表, 如果数据准备好了, 就进行
recv() 或 send(); 如果数据没有准备好, 就遍历下一个节点. 如果 recv 完成, 就
放到 send 的循环链表中. 但该实现仍然较　select 要差很多, 主要在于用户态和内核态
的频繁切换


###客户端

```c client_syn_unblock.c

    #include <stdio.h>
    #include <stdlib.h>
    #include <errno.h>
    #include <string.h>
    #include <netdb.h>
    #include <sys/types.h>
    #include <netinet/in.h>
    #include <sys/socket.h>
    #include <unistd.h>

    int main(int argc,char *argv[]) {
    	if(argc!=3) {
    		printf("Usage: %s IP PORT\n",argv[0]);
    		return 1;
    	}

    	int sockfd,numbytes;
    	char buf[100] = "hello world";
    	struct hostent *host;
    	struct sockaddr_in their_addr;

    	//将基本名字和地址转换
    	host = gethostbyname(argv[1]);

    	//建立一个TCP套接口
    	if ((sockfd = socket(AF_INET, SOCK_STREAM, 0))==-1) {
    		perror("socket");
    		exit(1);
    	}

    	//初始化结构体
    	their_addr.sin_family = AF_INET;
    	their_addr.sin_port = htons(atoi(argv[2]));
    	their_addr.sin_addr = *((struct in_addr *)host->h_addr);
    	bzero(&(their_addr.sin_zero),8);

    	//和服务器建立连接
    	if(connect(sockfd, (struct sockaddr *)&their_addr, sizeof(struct sockaddr)) == -1) {
    		perror("connect");
    		exit(1);
    	}

    	sleep(5);

    	//向服务器发送字符串
    	if (send(sockfd, buf, strlen(buf),0) == -1) {
    		perror("send");
    		exit(1);
    	}

    	memset(buf, 0, sizeof(buf));

    	sleep(5);

    	//接受从服务器返回的信息
    	if ((numbytes = recv(sockfd, buf, 100, 0)) == -1) {
    		perror("recv");
    		exit(1);
    	}

    	close(sockfd);
    	return 0;
    }
```

显然客户端也可以是同步非阻塞的, 但这在绝大多数情况下是非必须的, 除非是构建一个压力测试工具.


$ gcc server_syn_unblock.c -o server_syn_unblock
$ gcc client_syn_unblock.c -o client_syn_unblock
$ sudo strace -e trace=network ./server_syn_unblock 8001

    socket(PF_INET, SOCK_STREAM, IPPROTO_IP) = 3
    bind(3, {sa_family=AF_INET, sin_port=htons(8001),
            sin_addr=inet_addr("0.0.0.0")}, 16) = 0
    listen(3, 10)                           = 0
    server is running!
    accept(3, {sa_family=AF_INET, sin_port=htons(40277),
            sin_addr=inet_addr("127.0.0.1")}, [16]) = 4
    accept(3, recv error, wait....: Resource temporarily unavailable
    recv error, wait....: Resource temporarily unavailable
    recv error, wait....: Resource temporarily unavailable
    recv error, wait....: Resource temporarily unavailable
    recv error, wait....: Resource temporarily unavailable
    buff=hello world
    buff=hello world
    0x7fff61133ce0, [16])         = ? ERESTARTSYS (To be restarted if SA_RESTART is set)
    --- SIGCHLD {si_signo=SIGCHLD, si_code=CLD_EXITED, si_pid=18633, si_status=0, si_utime=0, si_stime=0} ---
    accept(3, ^CProcess 18600 detached
    <detached ...>
    )

$ sudo strace -e trace=network ./client_syn_unblock 127.0.0.1 8001

    socket(PF_INET, SOCK_STREAM, IPPROTO_IP) = 3
    connect(3, {sa_family=AF_INET, sin_port=htons(8001),
            sin_addr=inet_addr("127.0.0.1")}, 16) = 0
    sendto(3, "hello world", 11, 0, NULL, 0) = 11
    recvfrom(3, "hello world", 100, 0, NULL, NULL) = 11
    +++ exited with 0 +++



###异步阻塞 I/O --- Reactor　模式

这个模型也叫 I/O复用模型, 另外一个阻塞解决方案是带有阻塞通知的非阻塞 I/O. 在这种模型中, 配置的是非阻塞 I/O, 然后使用阻塞 select
系统调用来确定一个 I/O 描述符何时有操作. 使 select 调用非常有趣的是它可以用来为多个描述符提供通知, 而
不仅仅为一个描述符提供通知. 对于每个提示符来说, 我们可以请求这个描述符有数据可写, 有数据可读以及是否
发生错误的通知. 

![异步阻塞 I/O 模型典型流程](io_asyn_block.gif)

select 调用的主要问题是它的效率不是非常高. 尽管这是异步通知使用的一种方便模型, 但是对于高性能的 I/O
操作来说不建议使用. 

java 1.4 NIO 提供的 select, 这是一种多路复用 I/O（multiplexed non-blocking I/O）模型, 底层是使用 select
或者 poll. I/O 复用就是阻塞在 select 或者 poll 系统调用的某一个之上, 而不是阻塞在真正的 I/O 系统调用之上.
JDK 5.0 update 9 和 JDK 6.0 在 linux 下支持使用 epoll, 可以提高并发 idle connection 的性能

注 : select 不允许多于一个的线程在同一个描述符集上等待

当用户进程调用了select, 那么整个进程会被block, 而同时, kernel会"监视"所有select负责的socket, 当任何一个
socket中的数据准备好了, select就会返回. 这个时候用户进程再调用read操作, 将数据从kernel拷贝到用户进程. 


因为这里需要使用两个system call (select 和 recvfrom), 而blocking IO只调用了一个system call (recvfrom). 
但是, 用select的优势在于它可以同时处理多个connection. (多说一句. 所以, 如果处理的连接数不是很高的话, 
使用select/epoll的web server不一定比使用multi-threading + blocking IO的web server性能更好, 可能延迟还
更大. select/epoll的优势并不是对于单个连接能处理得更快, 而是在于能处理更多的连接.)

使用 select 最大的优势是用户可以在一个线程内同时处理多个 socket 的 IO 请求. 用户可以注册多个 socket,
然后不断地调用 select 读取被激活的 socket, 即可达到在同一个线程内同时处理多个 IO 请求的目的. 而在同步
阻塞模型中, 必须通过多线程的方式才能达到这个目的.

为了克服传统的同步阻塞模式大量的短连接情况下的缺点, 引入了该模式, 显然不需要开很多进程就可以处理大量
的连接, 因此, 通过该模型, 单机处理能力已经达到 10M, 100M 的能力. 如 java 的 netty, cpp 的 libevent,
clang 的 libev

更为重要的是, epoll 因为采用 mmap 的机制, 使得内核 socket buffer 和用户空间的 buffer 共享, 从面省去了
socket data copy, 这也意味着, 当 epoll 回调上层的 callback 函数来处理 socket 数据时, 数据已经从内核层
"自动" 到了用户空间, 虽然和用 poll 一样, 用户层的代码还必须要调用 read/write, 但这个函数内部实现所触发
的深度不同了.

####服务端

```c server_multiplex_io.c

    #include <stdio.h>
    #include <stdlib.h>
    #include <errno.h>
    #include <string.h>
    #include <netinet/in.h>
    #include <sys/socket.h>
    #include <unistd.h>
    #include <fcntl.h>
    #include <netdb.h>
    #include <sys/epoll.h>

    #define MAXEVENT 1024
    int LISTEN_PORT = 8000;
    int BACK_LOG = 10;

    struct server_socket {
        struct sockaddr_in *addr;
        int                port;
        int                fd;
    }

    struct server_socket* create_server_socket() {
        server_socket *server;
        server = malloc(sizeof(struct server_socket));
        server->addr = malloc(sizeof(struct sockaddr_in));

    	//创建socket
    	if((server->fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
    		perror("create socket");
    		return NULL;
    	}

    	//初始化socket结构
    	memset(server->addr, 0, sizeof(struct sockaddr_in));
    	server->addr.sin_family = AF_INET;
    	server->addr.sin_port = htons(LISTEN_PORT);
    	server->addr.sin_addr.s_addr = htonl(INADDR_ANY);

    	//绑定套接口
    	if (bind(server->fd, (struct sockaddr *)server->addr, sizeof(struct sockaddr)) == -1) {
    		perror("bind");
    		return NULL;
    	}

    	//创建监听套接口
    	if(listen(server->fd, BACK_LOG) == -1) {
    		perror("listen");
    		return NULL;
    	}
    	return server;
    }

    void destory_server_socket(struct server_socket **server) {
        free((*server)->addr);
        free(*server);
    }

    int set_socket_non_blocking(int fd) {
    	int flags, ret;
    	flags = fcntl (fd, F_GETFL, 0);
    	if (flags == -1) {
    		perror ("fcntl F_GETFL failed");
    		return -1;
    	}

    	flags |= O_NONBLOCK;
    	ret = fcntl (fd, F_SETFL, flags);
    	if (ret == -1) {
    		perror ("fcntl F_SETFL failed");
    		return -1;
    	}
    	return 0;
    }

    int main() {
    	int sockfd, efd;
    	struct epoll_event event;
    	struct epoll_event *events;
    	int ret;

        server_socket *server;

    	if (server = create_server_socket() == NULL) {
    		perror("create server sock failed\n");
    		return 1;
    	}
    	set_socket_non_blocking(server->fd);

        sockfd = server->fd;

    	printf("server is running!\n");

    	//创建一个epoll的句柄
    	//int epoll_create(int size)
    	//Since Linux 2.6.8, the size argument is unused. (The kernel dynamically sizes 
        //the required data structures without needing this initial hint.)
    	efd = epoll_create(MAXEVENT);
    	if (efd == -1) {
    		perror ("epoll_create");
    		abort ();
    	}

    	//注册新事件到epoll efd
    	event.data.fd = sockfd;
    	event.events = EPOLLIN | EPOLLET;
    	if ((ret = epoll_ctl(efd, EPOLL_CTL_ADD, sockfd, &event)) == -1) {
    		perror ("epoll_ctl EPOLL_CTL_ADD failed");
    		abort ();
    	}

    	events = (epoll_event*)calloc(MAXEVENT, sizeof(event));

    	while (1) {
    		int poll_num, i;
    		poll_num = epoll_wait(efd, events, MAXEVENT, -1);
            if (poll_num == -1) {
                if (errno == EINTR) {
                    continue;
                }
                perror("epoll_wait");
                exit(EXIT_FAILURE);
            }
    		for (i = 0; i < poll_num; i++) {
        		//fd error
          		if ((events[i].events & EPOLLERR)
                    || (events[i].events & EPOLLHUP)
                    || (!(events[i].events & EPOLLIN))) {

    				perror("epoll error\n");
    				close (events[i].data.fd);
    				continue;
    			} else if (sockfd == events[i].data.fd) {//新连接
    				while (1) {
    					struct sockaddr in_addr;
    					socklen_t in_len;
    					int infd;
    					char hostbuf[NI_MAXHOST], portbuf[NI_MAXSERV];

    					//接受连接
    					in_len = sizeof(in_addr);
    					infd = accept(sockfd, &in_addr, &in_len);
    					if (infd == -1) {
    						if ((errno == EAGAIN)
                               || (errno == EWOULDBLOCK)) {
    							//已接受所有连接
    					      	break;
    					    } else {
    							perror ("accept");
    							break;
    						}
    					}
    					ret = getnameinfo (&in_addr, in_len,
    					               hostbuf, sizeof(hbuf)/sizeof(char),
    					               portbuf, sizeof(portbuf)/sizof(char),
    					               NI_NUMERICHOST | NI_NUMERICSERV);
    					if (ret == 0) {
    					    printf("Accepted connection on descriptor %d "
    					         "(host=%s, port=%s)\n", infd, hostbuf, portbuf);
    					}

    					/* 设置新接受的socket连接无阻塞*/
    					ret = set_socket_non_blocking(infd);
    					if (ret == -1) {
    					    return 1;
    					}

    					//注册新事件到epoll
    					event.data.fd = infd;
    					event.events = EPOLLIN | EPOLLET;
    					ret = epoll_ctl(efd, EPOLL_CTL_ADD, infd, &event);
    					if (ret == -1) {
                            perror ("epoll_ctl");
                            return 1;
    					}
    				}
    				continue;
                } else { //数据可读
                    int done = 0;
                    while (1) {
                        ssize_t count;
                        char buf[512];
                        count = read(events[i].data.fd, buf, sizeof(buf));
                        if (count == -1) {
                            //数据读完
                            if (errno != EAGAIN) {
                                perror ("read");
                                done = 1;
                            }
                            break;
                        } else if(count == 0) {
                            /* End of file. The remote has closed the
                                connection. */
                            done = 1;
                            break;
                        }
                        printf("recv: %s\n", buf);
                    }
                    if (done) {
                        printf ("Closed connection on descriptor %d\n", events[i].data.fd);
                        close (events[i].data.fd);
                    }
                }
            }
        }
        free (events);
        close(sockfd);
        destory_server_socket(&server);
        return 0;
    }
```

####客户端

``` client_multiplex_io.c

    #include <stdio.h>
    #include <stdlib.h>
    #include <errno.h>
    #include <string.h>
    #include <netdb.h>
    #include <sys/types.h>
    #include <netinet/in.h>
    #include <sys/socket.h>
    #include <unistd.h>

    int main(int argc,char *argv[])
    {
    	if(argc!=3)
    	{
    		printf("%s: input IP & port\n",argv[0]);
    		return 1;
    	}
    	int sockfd,numbytes;
    	char buf[100] = "hello world";
    	struct hostent *he;
    	struct sockaddr_in their_addr;

    	//将基本名字和地址转换
    	he = gethostbyname(argv[1]);

    	//建立一个TCP套接口
    	if ((sockfd = socket(AF_INET,SOCK_STREAM,0))==-1) {
    		perror("socket");
    		exit(1);
    	}

    	//初始化结构体
    	their_addr.sin_family = AF_INET;
    	their_addr.sin_port = htons(atoi(argv[2]));
    	their_addr.sin_addr = *((struct in_addr *)he->h_addr);
    	bzero(&(their_addr.sin_zero),8);

    	//和服务器建立连接
    	if (connect(sockfd,(struct sockaddr *)&their_addr,sizeof(struct sockaddr)) == -1) {
    		perror("connect");
    		exit(1);
    	}

    	//向服务器发送字符串
    	while(1) {
    		if (send(sockfd, buf, strlen(buf), 0) == -1) {
    			perror("send");
    			exit(1);
    		}
    		sleep(2);
    	}
    	memset(buf,0,sizeof(buf));
    	close(sockfd);
    	return 0;
    }
```


###信号驱动IO

使用信号驱动I/O时, 当网络套接字可读后, 内核通过发送SIGIO信号通知应用进程, 于是应用可以开始读取数据. 如图：

为了让套接字描述符可以工作于信号驱动I/O模式, 应用进程必须完成如下三步设置：
1.注册SIGIO信号处理程序. (安装信号处理器)
2.使用fcntl的F_SETOWN命令, 设置套接字所有者. （设置套接字的所有者）
3.使用fcntl的F_SETFL命令, 置O_ASYNC标志, 允许套接字信号驱动I/O. （允许这个套接字进行信号输入输出）
注意, 必须保证在设置套接字所有者之前, 向系统注册信号处理程序, 否则就有可能在fcntl调用后, 信号处理程序注册前内核向应用交付SIGIO信号, 导致应用丢失此信号. 

在UDP编程中使用信号驱动I/O, 此时SIGIO信号产生于下面两种情况：
套接字收到一个数据报. 
套接字上发生了异步错误. 
因此, 当应用因为收到一个UDP数据报而产生的SIGIO时, 要么可以调用recvfrom读取该数据报, 要么得到一个异步错误. 
对于TCP编程, 信号驱动I/O就没有太大意义了, 因为对于流式套接字而言, 有很多情况都可以导致SIGIO产生, 而应用又无法区分是什么具体情况导致该信号产生的
信号驱动IO模型在网络编程中极少使用, 这里不写例子了, 有兴趣的同学可以参考：http://blog.csdn.net/yskcg/article/details/6021275


###异步非阻塞 I/O(AIO) --- Proactor　模式

异步非阻塞 I/O 模型是一种处理与 I/O 重叠进行的模型: 首先我们允许套接口进行信号驱动 I/O, 并安装一个信
号处理函数, 进程继续运行并不阻塞. 当数据准备好时, 进程会收到一个 SIGIO 信号, 可以在信号处理函数中调用
I/O 操作函数处理数据.

读请求会立即返回, 说明 read 请求已经成功发起了.
在后台完成读操作时, 应用程序然后会执行其他处理操作. 当 read 的响应到达时, 就会产生一个信号或执行一个
基于线程的回调函数来完成这次 I/O 处理过程.

![异步非阻塞 I/O 模型典型流程](io_asyn_unblock.gif)


当一个或多个 I/O 请求挂起时, CPU 可以执行其他任务; 或者更为常见的是, 在发起其他 I/O 的同时对已经完成
的 I/O 进行操作.

####服务端

``` server_aio.c

    #include <stdio.h>
    #include <stdlib.h>
    #include <errno.h>
    #include <string.h>
    #include <netinet/in.h>
    #include <sys/socket.h>
    #include <unistd.h>
    #include <fcntl.h>
    #include <aio.h>
    #include <pthread.h>

    #define BUF_SIZE 1024
    int LISTEN_PORT = 8000;
    int BACK_LOG = 10;

    void aio_completion_handler(sigval_t sigval);

    void setup_io(int fd, aiocb& my_aiocb) {
    	//初始化AIO请求
    	bzero( (char *)&my_aiocb, sizeof(struct aiocb) );
    	my_aiocb.aio_fildes = fd;
    	my_aiocb.aio_buf = malloc(BUF_SIZE+1);
    	my_aiocb.aio_nbytes = BUF_SIZE;
    	my_aiocb.aio_offset = 0;

    	//设置线程回调函数
    	my_aiocb.aio_sigevent.sigev_notify = SIGEV_THREAD;
    	my_aiocb.aio_sigevent.sigev_notify_function = aio_completion_handler;
    	my_aiocb.aio_sigevent.sigev_notify_attributes = NULL;
    	my_aiocb.aio_sigevent.sigev_value.sival_ptr = &my_aiocb;
    }

    //回调函数
    void aio_completion_handler(sigval_t sigval) {
    	struct aiocb *req;
    	int ret;

    	req = (struct aiocb *)sigval.sival_ptr;

    	if (aio_error(req) == 0) {
    		if((ret = aio_return(req)) > 0) {
    			printf("Thread id %u recv:%s\n", (unsigned int)pthread_self(), (char*)req->aio_buf);
    		}
    	}

    	char* buf = (char*)req->aio_buf;

    	if (send(req->aio_fildes, buf, strlen(buf), 0) == -1) {
    		perror("send");
    		return;
    	}

    	close(req->aio_fildes);
    	return;
    }

    int main(int argc, char **argv) {
    	int sockfd;
    	int sin_size;
    	struct sockaddr_in addr, cliaddr;

    	//创建socket
    	if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
    		perror("create socket");
    		return -1;
    	}

        LISTEN_PORT = argv[1];

    	//初始化socket结构
    	memset(&addr, 0, sizeof(addr));
    	addr.sin_family = AF_INET;
    	addr.sin_port = htons(LISTEN_PORT);
    	addr.sin_addr.s_addr = htonl(INADDR_ANY);

    	//绑定套接口
    	if (bind(sockfd, (struct sockaddr *)&addr, sizeof(struct sockaddr)) == -1) {
    		perror("bind");
    		return -1;
    	}

    	//创建监听套接口
    	if (listen(sockfd, BACK_LOG) == -1) {
    		perror("listen");
    		return -1;
    	}

    	printf("server is running!\n");

    	//等待连接
    	while (1) {
    		int new_fd;
      		struct aiocb my_aiocb;
    		sin_size = sizeof(struct sockaddr_in);

    		//接受连接
    		if((new_fd = accept(sockfd, (struct sockaddr *)&cliaddr, (socklen_t*)&sin_size)) == -1) {
    			perror("accept");
    			return -1;
    		}

    		printf("Thread id %u accept connect, fd: %d\n", (unsigned int)pthread_self(), new_fd);

    		setup_io(new_fd, my_aiocb);
    		aio_read(&my_aiocb);
    	}
    	close(sockfd);
    }
```

####客户端

```c client_aio.c

    #include <stdio.h>
    #include <stdlib.h>
    #include <errno.h>
    #include <string.h>
    #include <netdb.h>
    #include <sys/types.h>
    #include <netinet/in.h>
    #include <sys/socket.h>
    #include <unistd.h>

    int main(int argc,char *argv[]) {
    	if(argc!=3) {
    		printf("%s: input IP & port\n",argv[0]);
    		return 1;
    	}
    	int sockfd,numbytes;
    	char buf[100] = "hello world";
    	struct hostent *he;
    	struct sockaddr_in their_addr;

    	//将基本名字和地址转换
    	he = gethostbyname(argv[1]);

    	//建立一个TCP套接口
    	if ((sockfd = socket(AF_INET,SOCK_STREAM,0)) == -1) {
    		perror("socket");
    		exit(1);
    	}

    	//初始化结构体
    	their_addr.sin_family = AF_INET;
    	their_addr.sin_port = htons(atoi(argv[2]));
    	their_addr.sin_addr = *((struct in_addr *)he->h_addr);
    	bzero(&(their_addr.sin_zero),8);

    	//和服务器建立连接
    	if (connect(sockfd,(struct sockaddr *)&their_addr,sizeof(struct sockaddr)) == -1) {
    		perror("connect");
    		exit(1);
    	}

    	//向服务器发送字符串
    	if (send(sockfd,buf,strlen(buf),0)==-1) {
    		perror("send");
    		exit(1);
    	}

        //接收数据
    	if ((numbytes = recv(sockfd, buf, 100, 0)) == -1) {
    		perror("recv");
    		return 1;
    	}

    	printf("recv: %s\n", buf);

    	close(sockfd);
    	return 0;
    }
```


###阻塞和异步的关系:

异步是对用户态而言的, 阻塞是对内核态而言的.

###阻塞和非阻塞的区别

阻塞是对内核态而言的, 如果内核态调用后不管成功与否, 理解返回即认为是非阻塞的. 如果内核态等待数据准备好, 就是阻塞的.

阻塞式 IO 可能会造成频繁的上下文切换
非阻塞式 IO 会占用CPU时间过长, 是一种CPu的浪费. 

阻塞是阻塞内核的 I/O, 期间如果用户态进程没有被阻塞, CPU 可以用来做其他事情.
而非阻塞, 由于频繁的内核态和用户态的切换, 导致 CPU 非常忙, 是对 CPU 资源的浪费.

阻塞是指IO操作需要彻底完成后才返回到用户空间；而非阻塞是指IO操作被调用后立即返回给用户一个状态值, 无需等到IO操作彻底完成. 

###同步和异步的区别

同步是相对与用户态而言的, 如果调用后系统调用后, 应用程序不需要进行任何等待, 就是异步的. 反之, 应用程序需要等待内核态的返回, 就是同步.

同步是指用户线程发起 IO 请求后需要等待或者轮询内核 IO 操作完成后才能继续执行, 并且主动将内核缓冲区的数据拷贝到用户进程

异步是指用户线程发起 IO 请求后仍继续执行, 当内核 IO 操作完成后会通知用户线程, 或者调用用户线程注册的回调函数. 因此, 内
核会自动将内核缓冲区的数据拷贝到用于空间.


non-blocking IO在执行recvfrom这个system call的时候, 如果kernel的数据没有准备好, 这时候不会block进程. 但是, 当kernel中数据准备好的时候, recvfrom会将数据从kernel拷贝到用户内存中, 这个时候进程是被block了, 在这段时间内, 进程是被block的. 而asynchronous IO则不一样, 当进程发起IO 操作之后, 就直接返回再也不理睬了, 直到kernel发送一个信号, 告诉进程说IO完成. 在这整个过程中, 进程完全没有被block. 


在non-blocking IO中, 虽然进程大部分时间都不会被block, 但是它仍然要求进程去主动的 check, 并且当数据准备完成以后, 也需要进程主动的再次调用recvfrom来将数据拷贝到用户内存. 而asynchronous IO则完全不同. 它就像是用户进程将整个IO操作交给了他人（kernel）完成, 然后他人做完后发信号通知. 在此期间, 用户进程不需要去检查IO操作的状态, 也不需要主动的去拷贝数据. 

异步有一个很明显的特征, 就是内核向用户层发送读成功的“消息”（用户进程只有一个启动io系统调用, 之后去忙其他事情, 内核完成拷贝后通过消息向该进程说“搞定了”）. 而非异步的操作, 需要程序自己通过系统调用去告诉内核接下来做什么（1.select 获取可读的fd, 2,read 将数据从内核层拷贝到用户层）


帮助理解的例子:

任务分配:

###Windows 的IO模型

* select模型
* WSAAsyncSelect模型
* WSAEventSelect模型
* Overlapped I/O 事件通知模型
* Overlapped I/O 完成例程模型
* IOCP模型

redhat的测试中, epoll的性能要比aio-poll强, 使用 aio 主要是帮助提升poll 的性能


参考:
http://www.ibm.com/developerworks/cn/linux/l-async/
http://blog.csdn.net/yfkiss/article/details/7516589
http://www.ibm.com/developerworks/cn/linux/l-cn-edntwk/
http://blog.csdn.net/yfkiss/article/details/7516589
