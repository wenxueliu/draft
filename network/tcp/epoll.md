
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




    在linux的网络编程中,新的事件触发机制-epoll。

    相比于select，epoll最大的好处在于它不会随着监听fd数目的增长而降低效率。因为在内核中的select实现中，它是采用轮询来处理的，轮询的fd数目越多，自然耗时越多。并且，在linux/posix_types.h头文件有这样的声明：
    #define __FD_SETSIZE 1024
    表示select最多同时监听1024个fd，当然，可以通过修改头文件再重编译内核来扩大这个数目。

    epoll的接口非常简单，一共就三个函数：
    1. int epoll_create(int size);
    创建一个epoll的句柄，size用来告诉内核这个监听的数目一共有多大。这个参数不同于select()中的第一个参数，给出最大监听的fd+1的值。需要注意的是，当创建好epoll句柄后，它就会占用一个fd值，在linux下如果查看/proc/进程id/fd/，是能够看到这个fd的，所以在使用完epoll后，必须调用close()关闭，否则可能导致fd被耗尽。


    2. int epoll_ctl(int epfd, int op, int fd, struct epoll_event *event);
    epoll的事件注册函数，它不同与select()是在监听事件时告诉内核要监听什么类型的事件，而是在这里先注册要监听的事件类型。第一个参数是epoll_create()的返回值，第二个参数表示动作，用三个宏来表示：
    EPOLL_CTL_ADD：注册新的fd到epfd中；
    EPOLL_CTL_MOD：修改已经注册的fd的监听事件；
    EPOLL_CTL_DEL：从epfd中删除一个fd；
    第三个参数是需要监听的fd，第四个参数是告诉内核需要监听什么事，struct epoll_event结构如下：

    typedef union epoll_data {
        void *ptr;
        int fd;
        __uint32_t u32;
        __uint64_t u64;
    } epoll_data_t;

    struct epoll_event {
        __uint32_t events; /* Epoll events */
        epoll_data_t data; /* User data variable */
    };

    events可以是以下几个宏的集合：
    EPOLLIN ：表示对应的文件描述符可以读（包括对端SOCKET正常关闭）；
    EPOLLOUT：表示对应的文件描述符可以写；
    EPOLLPRI：表示对应的文件描述符有紧急的数据可读（这里应该表示有带外数据到来）；
    EPOLLERR：表示对应的文件描述符发生错误；
    EPOLLHUP：表示对应的文件描述符被挂断；
    EPOLLET： 将EPOLL设为边缘触发(Edge Triggered)模式，这是相对于水平触发(Level Triggered)来说的。
    EPOLLONESHOT：只监听一次事件，当监听完这次事件之后，如果还需要继续监听这个socket的话，需要再次把这个socket加入到EPOLL队列里


    3. int epoll_wait(int epfd, struct epoll_event * events, int maxevents, int timeout);
    等待事件的产生，类似于select()调用。参数events用来从内核得到事件的集合，maxevents告之内核这个events有多大，这个 maxevents的值不能大于创建epoll_create()时的size，参数timeout是超时时间（毫秒，0会立即返回，-1将不确定，也有说法说是永久阻塞）。该函数返回需要处理的事件数目，如返回0表示已超时。


    4、关于ET、LT两种工作模式：

    EPOLL事件有两种模型：
    Edge Triggered (ET)
    Level Triggered (LT)

    LT(level triggered)是缺省的工作方式，并且同时支持block和no-block socket.在这种做法中，内核告诉你一个文件描述符是否就绪了，然后你可以对这个就绪的fd进行IO操作。如果你不作任何操作，内核还是会继续通知你的，所以，这种模式编程出错误可能性要小一点。传统的select/poll都是这种模型的代表．

    ET(edge-triggered)是高速工作方式，只支持no-block socket。在这种模式下，当描述符从未就绪变为就绪时，内核通过epoll告诉你。然后它会假设你知道文件描述符已经就绪，并且不会再为那个文件描述符发送更多的就绪通知，直到你做了某些操作导致那个文件描述符不再为就绪状态了(比如，你在发送，接收或者接收请求，或者发送接收的数据少于一定量时导致了一个EWOULDBLOCK 错误）。但是请注意，如果一直不对这个fd作IO操作(从而导致它再次变成未就绪)，内核不会发送更多的通知(only once),不过在TCP协议中，ET模式的加速效用仍需要更多的benchmark确认

    另外，当使用epoll的ET模型来工作时，当产生了一个EPOLLIN事件后，
    读数据的时候需要考虑的是当recv()返回的大小如果等于请求的大小，那么很有可能是缓冲区还有数据未读完，也意味着该次事件还没有处理完，所以还需要再次读取：
    while(rs)
    {
      buflen = recv(activeevents[i].data.fd, buf, sizeof(buf), 0);
      if(buflen < 0)
      {
        // 由于是非阻塞的模式,所以当errno为EAGAIN时,表示当前缓冲区已无数据可读
        // 在这里就当作是该次事件已处理处.
        if(errno == EAGAIN)
         break;
        else
         return;
       }
       else if(buflen == 0)
       {
         // 这里表示对端的socket已正常关闭.
       }
       if(buflen == sizeof(buf)
         rs = 1; // 需要再次读取
       else
         rs = 0;
    }


    还有，假如发送端流量大于接收端的流量(意思是epoll所在的程序读比转发的socket要快),由于是非阻塞的socket,那么send()函数虽然返回,但实际缓冲区的数据并未真正发给接收端,这样不断的读和发，当缓冲区满后会产生EAGAIN错误(参考man send),同时,不理会这次请求发送的数据.所以,需要封装socket_send()的函数用来处理这种情况,该函数会尽量将数据写完再返回，返回-1表示出错。在socket_send()内部,当写缓冲已满(send()返回-1,且errno为EAGAIN),那么会等待后再重试.这种方式并不很完美,在理论上可能会长时间的阻塞在socket_send()内部,但暂没有更好的办法.

    ssize_t socket_send(int sockfd, const char* buffer, size_t buflen)
    {
      ssize_t tmp;
      size_t total = buflen;
      const char *p = buffer;

      while(1)
      {
        tmp = send(sockfd, p, total, 0);
        if(tmp < 0)
        {
          // 当send收到信号时,可以继续写,但这里返回-1.
          if(errno == EINTR)
            return -1;

          // 当socket是非阻塞时,如返回此错误,表示写缓冲队列已满,
          // 在这里做延时后再重试.
          if(errno == EAGAIN)
          {
            usleep(1000);
            continue;
          }

          return -1;
        }

        if((size_t)tmp == total)
          return buflen;

        total -= tmp;
        p += tmp;
      }

      return tmp;
    }


    采用LT模式下， 如果accept调用有返回就可以马上建立当前这个连接了，再epoll_wait等待下次通知，和select一样。
    但是对于ET而言，如果accpet调用有返回，除了建立当前这个连接外，不能马上就epoll_wait还需要继续循环accpet，直到返回-1，且errno==EAGAIN，TAF里面的示例代码：
    if(ev.events & EPOLLIN)
    {
        do
        {
            struct sockaddr_in stSockAddr;
            socklen_t iSockAddrSize = sizeof(sockaddr_in);
            TC_Socket cs;
            cs.setOwner(false);
            //接收连接
            TC_Socket s;
            s.init(fd, false, AF_INET);
            int iRetCode = s.accept(cs, (struct sockaddr *) &stSockAddr, iSockAddrSize);
            if (iRetCode > 0)
            {
                ...建立连接
            }
            else
            {
                //直到发生EAGAIN才不继续accept
                if(errno == EAGAIN)
                {
                    break;
                }
            }
        }while(true);
    }
    同样，recv/send等函数， 都需要到errno==EAGAIN从本质上讲：与LT相比，ET模型是通过减少系统调用来达到提高并行效率的。


    ET模型的逻辑：内核的读buffer有内核态主动变化时，内核会通知你， 无需再去mod。写事件是给用户使用的，最开始add之后，内核都不会通知你了，你可以强制写数据（直到EAGAIN或者实际字节数小于 需要写的字节数），当然你可以主动mod OUT，此时如果句柄可以写了（send buffer有空间），内核就通知你。
    这里内核态主动的意思是：内核从网络接收了数据放入了读buffer（会通知用户IN事件，即用户可以recv数据）
    并且这种通知只会通知一次，如果这次处理（recv）没有到刚才说的两种情况（EAGIN或者实际字节数小于 需要读写的字节数），则该事件会被丢弃，直到下次buffer发生变化。
    与LT的差别就在这里体现，LT在这种情况下，事件不会丢弃，而是只要读buffer里面有数据可以让用户读，则不断的通知你。
    另外对于ET而言，当然也不一定非send/recv到前面所述的结束条件才结束，用户可以自己随时控制，即用户可以在自己认为合适的时候去设置IN和OUT事件：
    1 如果用户主动epoll_mod OUT事件，此时只要该句柄可以发送数据（发送buffer不满），则epoll
    _wait就会响应（有时候采用该机制通知epoll_wai醒过来）。
    2 如果用户主动epoll_mod IN事件，只要该句柄还有数据可以读，则epoll_wait会响应。
    这种逻辑在普通的服务里面都不需要，可能在某些特殊的情况需要。 但是请注意，如果每次调用的时候都去epoll mod将显著降低效率！
    因此采用et写服务框架的时候，最简单的处理就是：
    建立连接的时候epoll_add IN和OUT事件， 后面就不需要管了

    每次read/write的时候，到两种情况下结束：
    1 发生EAGAIN
    2 read/write的实际字节数小于需要读写的字节数

    对于第二点需要注意两点：
    A：如果是UDP服务，处理就不完全是这样，必须要recv到发生EAGAIN为止，否则就丢失事件了
    因为UDP和TCP不同，是有边界的，每次接收一定是一个完整的UDP包，当然recv的buffer需要至少大于一个UDP包的大小
    随便再说一下，一个UDP包到底应该多大？对于internet，由于MTU的限制，UDP包的大小不要超过576个字节，否则容易被分包，对于公司的IDC环境，建议不要超过1472，否则也比较容易分包。
    B 如果发送方发送完数据以后，就close连接，这个时候如果recv到数据是实际字节数小于读写字节数，根据开始所述就认为到EAGIN了从而直接返回，等待下一次事件，这样是有问题的，close事件丢失了！因此如果依赖这种关闭逻辑的服务，必须接收数据到EAGIN为止，例如lb。



    那么究竟如何来使用epoll呢？
    通过在包含一个头文件#include <sys/epoll.h> 以及几个简单的API将可以大大的提高你的网络服务器的支持人数。

    首先通过create_epoll(int maxfds)来创建一个epoll的句柄，其中maxfds为你epoll所支持的最大句柄数。这个函数会返回一个新的epoll句柄，之后的所有操作将通过这个句柄来进行操作。在用完之后，记得用close()来关闭这个创建出来的epoll句柄。

    之后在你的网络主循环里面，每一帧的调用epoll_wait(int epfd, epoll_event events, int max events, int timeout)来查询所有的网络接口，看哪一个可以读，哪一个可以写了。基本的语法为：
    nfds = epoll_wait(kdpfd, events, maxevents, -1);
    其中kdpfd为用epoll_create创建之后的句柄，events是一个epoll_event*的指针，当epoll_wait这个函数操作成功之后，epoll_events里面将储存所有的读写事件。max_events是当前需要监听的所有socket句柄数。最后一个timeout是 epoll_wait的超时，为0的时候表示马上返回，为-1的时候表示一直等下去，直到有事件范围，为任意正整数的时候表示等这么长的时间，如果一直没有事件，则范围。一般如果网络主循环是单独的线程的话，可以用-1来等，这样可以保证一些效率，如果是和主逻辑在同一个线程的话，则可以用0来保证主循环的效率。

    epoll_wait范围之后应该是一个循环，遍利所有的事件。

    几乎所有的epoll程序都使用下面的框架：

        for( ; ; )
        {
            nfds = epoll_wait(epfd,events,20,500);
            for(i=0;i<nfds;++i)
            {
                if(events[i].data.fd==listenfd) //有新的连接
                {
                    connfd = accept(listenfd,(sockaddr *)&clientaddr, &clilen); //accept这个连接
                    ev.data.fd=connfd;
                    ev.events=EPOLLIN|EPOLLET;
                    epoll_ctl(epfd,EPOLL_CTL_ADD,connfd,&ev); //将新的fd添加到epoll的监听队列中
                }
                else if( events[i].events&EPOLLIN ) //接收到数据，读socket
                {
                    n = read(sockfd, line, MAXLINE)) < 0 //读
                    ev.data.ptr = md; //md为自定义类型，添加数据
                    ev.events=EPOLLOUT|EPOLLET;
                    epoll_ctl(epfd,EPOLL_CTL_MOD,sockfd,&ev);//修改标识符，等待下一个循环时发送数据，异步处理的精髓
                }
                else if(events[i].events&EPOLLOUT) //有数据待发送，写socket
                {
                    struct myepoll_data* md = (myepoll_data*)events[i].data.ptr; //取数据
                    sockfd = md->fd;
                    send( sockfd, md->ptr, strlen((char*)md->ptr), 0 ); //发送数据
                    ev.data.fd=sockfd;
                    ev.events=EPOLLIN|EPOLLET;
                    epoll_ctl(epfd,EPOLL_CTL_MOD,sockfd,&ev); //修改标识符，等待下一个循环时接收数据
                }
                else
                {
                    //其他的处理
                }
            }
        }


http://blog.chinaunix.net/uid-25203957-id-2938265.html


epoll是Linux下多路复用IO接口select/poll的增强版本，它能显著减少程序在大量并发连接中只有少量活跃的情况下的系统CPU利用率，因为它不会复用文件描述符集合来传递结果而迫使开发者每次等待事件之前都必须重新准备要被侦听的文件描述符集合，另一点原因就是获取事件的时候，它无须遍历整个被侦听的描述符集，只要遍历那些被内核IO事件异步唤醒而加入Ready队列的描述符集合就行了。

	#include<sys/epoll.h>
	int epoll_create(int size);
	int epoll_ctl(int epfd, int op, int fd, struct epoll_event *event);
	int epoll_wait(int epfd, struct epoll_event *events,int maxevents, int timeout);

第一个函数 epoll_create() 创建一个epoll的句柄，size用来告诉内核这个监听的数目一共有多大，其实size参数内核不会用到，只是开发者自己提醒自己的一个标记。epoll对监听的描述符数目没有限制，它所支持的FD上限是最大可以打开文件的数目，这个数字一般远大于2048,举个例子,在1GB内存的机器上大约是10万左右，具体数目可以cat /proc/sys/fs/file-max察看,一般来说这个数目和系统内存关系很大，在我的机器上这个值为：149197.

　　第二个函数 epoll_ctl() 是epoll的事件注册函数，它不同于select()是在监听事件时告诉内核要监听什么类型的事件，而是在这里先注册要监听的事件类型。第一个参数是epoll_create()的返回值，第二个参数表示动作，用三个宏来表示：

　　EPOLL_CTL_ADD：注册新的fd到epfd中；

　　EPOLL_CTL_MOD: 修改已经注册的fd监听事件；

　　EPOLL_CTL_DEL:  从epfd中删除一个fd；

第三个参数是需要监听的fd，第四个参数是告诉内核需要监听什么事，struct epoll_event结构如下：

	struct epoll_event {
	  __uint32_t events;  /* Epoll events */
	  epoll_data_t data;  /* User data variable */
	};

其中epoll_data_t 结构如下：

	typedef union epoll_data {
	void *ptr;
	int fd;
	__uint32_t u32;
	__uint64_t u64;
	} epoll_data_t;

　　注意这是一个union 结构。　　

　　events可以是以下几个宏的集合：
　　EPOLLIN ：表示对应的文件描述符可以读（包括对端SOCKET正常关闭）；
　　EPOLLOUT：表示对应的文件描述符可以写；
　　EPOLLPRI：表示对应的文件描述符有紧急的数据可读（这里应该表示有带外数据到来）；
　　EPOLLERR：表示对应的文件描述符发生错误；
　　EPOLLHUP：表示对应的文件描述符被挂断；
　　EPOLLET： 将EPOLL设为边缘触发(Edge Triggered)模式，这是相对于水平触发(Level Triggered)来说的。
　　EPOLLONESHOT：只监听一次事件，当监听完这次事件之后，如果还需要继续监听这个socket的话，需要再次把这个socket加入到EPOLL队列里

　　这里介绍一下边沿触发和水平触发（epoll默认使用水平触发）：

　　LT 电平触发（高电平触发）：
　　EPOLLIN 事件
　　　　　　内核中的某个socket接收缓冲区 　　 为空 　　 低电平
　　　　　　内核中的某个socket接收缓冲区　　 不为空 　　高电平

　　EPOLLOUT 事件
　　　　　　内核中的某个socket发送缓冲区 　　 不满 　　 高电平
　　　　　　内核中的某个socket发送缓冲区 　　 满 　　　 低电平　　

　　ET 边沿触发：
　　　　　　低电平 -> 高电平 触发
　　　　　　高电平 -> 低电平 触发

　　推荐使用默认的水平触发。

 　　第三个函数epoll_wait() 等待事件的产生，类似于select()调用。参数events用来从内核得到事件的集合，返回的事件都保存在该events数组中，需要通过判断该数组中各个元素的状态来决定该如何处理，该maxevents告之内核这个events数组的大小。该函数返回需要处理的事件数目，如返回0表示已超时。

```
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
#include <errno.h>
#include <sys/epoll.h>
using namespace std;
#define PORT 1314
#define MAX_LINE_LEN 1024
#define EPOLL_EVENTS 1024

int main()   
{
    struct sockaddr_in cli_addr, server_addr;
    socklen_t addr_len;
    int one,flags,nrcv,nwrite,nready;
    
    int listenfd,epollfd,connfd;
    char buf[MAX_LINE_LEN],addr_str[INET_ADDRSTRLEN];
    
    struct epoll_event ev;
    std::vector<struct epoll_event> eventsArray(16);

    bzero(&server_addr, sizeof server_addr);
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    
    listenfd = socket(AF_INET, SOCK_STREAM, 0);
    
    if( listenfd < 0)
    {
        perror("socket open error! \n");
        exit(1);
    }
    
    
    one = 1;
    setsockopt(listenfd,SOL_SOCKET,SO_REUSEADDR, &one, sizeof one);
    
    flags = fcntl(listenfd,F_GETFL,0);
    fcntl(listenfd, F_SETFL, flags | O_NONBLOCK);
    
    if(bind(listenfd,reinterpret_cast<struct sockaddr *>(&server_addr),sizeof(server_addr)) < 0)
    {
        perror("Bind error! \n");
        exit(1);
    }
    
    listen(listenfd, 100);
    
    epollfd = epoll_create(EPOLL_EVENTS);
    
    if(epollfd < 0)
    {
        printf("epoll_create error: %s \n",strerror(errno));
        exit(1);
    }
    
    ev.events = EPOLLIN;
    ev.data.fd = listenfd;
    
    if(epoll_ctl(epollfd, EPOLL_CTL_ADD,listenfd,&ev) < 0)
    {
        printf("register listenfd failed: %s",strerror(errno));
        exit(1);
    }
    
    while(1)
    {
        nready = epoll_wait(epollfd,&(*eventsArray.begin()),static_cast<int>(eventsArray.size()),-1);
        
        if(nready < 0)
        {
            printf("epoll_wait error: %s \n",strerror(errno));
        }
        
        for( int i = 0; i < nready; i++)
        {
            if(eventsArray[i].data.fd == listenfd)
            {
                addr_len = sizeof cli_addr;
                connfd = accept(listenfd, reinterpret_cast<struct sockaddr *>(&cli_addr),&addr_len);
                
                if( connfd < 0)
                {
                    if( errno != ECONNABORTED || errno != EWOULDBLOCK || errno != EINTR)
                    {
                        printf("accept socket aborted: %s \n",strerror(errno));
                        continue;
                    }
                }
                
                flags = fcntl(connfd, F_GETFL, 0);
                fcntl(connfd,F_SETFL, flags | O_NONBLOCK);
                
                ev.events = EPOLLIN;
                ev.data.fd = connfd;
                
                if(epoll_ctl(epollfd,EPOLL_CTL_ADD,connfd,&ev) < 0)
                {
                    printf("epoll add error: %s",strerror(errno));
                }
                
                printf("recieve from : %s at port %d\n", inet_ntop(AF_INET,&cli_addr.sin_addr,addr_str,INET_ADDRSTRLEN),cli_addr.sin_port);
                
                if(--nready < 0)
                {
                    continue;
                }
        
            }
            else
            {
                ev = eventsArray[i];
                
                printf("fd = %d \n",ev.data.fd);
                
                memset(buf,0,MAX_LINE_LEN);
                
                if( (nrcv = read(ev.data.fd, buf, MAX_LINE_LEN)) < 0)
                {
                    if(errno != EWOULDBLOCK || errno != EAGAIN || errno != EINTR)
                    {
                        printf("read error: %s\n",strerror(errno));
                    }
                }
                else if( 0 == nrcv)
                {
                    close(ev.data.fd);
                    printf("close: %d fd \n",ev.data.fd);
                    eventsArray.erase(eventsArray.begin() + i);
                }
                else
                {
                    printf("nrcv, content: %s\n",buf);
                    nwrite = write(ev.data.fd, buf, nrcv);
                    if( nwrite < 0)
                    {
                        if(errno != EAGAIN || errno != EWOULDBLOCK)
                            printf("write error: %s\n",strerror(errno));
                    }
                    printf("nwrite = %d\n",nwrite);
                }
            }
        }
    }
    
    return 0;
}
```


##select/poll/epoll 对比


首先还是来看常见的select和poll。对于网络编程来说，一般认为poll比select要高级一些，这主要源于以下几个原因：

    poll() 不要求开发者计算最大文件描述符加一的大小。
    poll() 在应付大数目的文件描述符的时候速度更快，因为对于select()来说内核需要检查大量描述符对应的fd_set 中的每一个比特位，比较费时。
    select 可以监控的文件描述符数目是固定的，相对来说也较少（1024或2048），如果需要监控数值比较大的文件描述符，就算所监控的描述符很少，如果分布的很稀疏也会效率很低，对于poll() 函数来说，就可以创建特定大小的数组来保存监控的描述符，而不受文件描述符值大小的影响，而且poll()可以监控的文件数目远大于select。
    对于select来说，所监控的fd_set在select返回之后会发生变化，所以在下一次进入select()之前都需要重新初始化需要监控的fd_set，poll() 函数将监控的输入和输出事件分开，允许被监控的文件数组被复用而不需要重新初始化。
    select() 函数的超时参数在返回时也是未定义的，考虑到可移植性，每次在超时之后在下一次进入到select之前都需要重新设置超时参数。

　　当然也不是说select就没有优点：

    select()的可移植性更好，在某些Unix系统上不支持poll()
    select() 对于超时值提供了更好的精度：微秒，而poll是毫秒。

epoll的优点：

1.支持一个进程打开大数目的socket描述符(FD)

　　select 最不能忍受的是一个进程所打开的FD是有一定限制的，由FD_SETSIZE设置，默认值是1024/2048。对于那些需要支持的上万连接数目的IM服务器来说显然太少了。这时候你一是可以选择修改这个宏然后重新编译内核。不过 epoll则没有这个限制，它所支持的FD上限是最大可以打开文件的数目，这个数字一般远大于2048,举个例子,在1GB内存的机器上大约是10万左右，具体数目可以cat /proc/sys/fs/file-max察看,一般来说这个数目和系统内存关系很大。

2.IO效率不随FD数目增加而线性下降

　　传统的select/poll另一个致命弱点就是当你拥有一个很大的socket集合，不过由于网络延时，任一时间只有部分的socket是"活跃"的，但是select/poll每次调用都会线性扫描全部的集合，导致效率呈现线性下降。但是epoll不存在这个问题，它只会对"活跃"的socket进行操作---这是因为在内核实现中epoll是根据每个fd上面的callback函数实现的。那么，只有"活跃"的socket才会主动的去调用 callback函数，其他idle状态socket则不会，在这点上，epoll实现了一个"伪"AIO，因为这时候推动力在Linux内核。

3.使用mmap加速内核与用户空间的消息传递。

　　这点实际上涉及到epoll的具体实现了。无论是select,poll还是epoll都需要内核把FD消息通知给用户空间，如何避免不必要的内存拷贝就很重要，在这点上，epoll是通过内核与用户空间mmap同一块内存实现的。 

　　对于poll来说需要将用户传入的 pollfd 数组拷贝到内核空间，因为拷贝操作和数组长度相关，时间上这是一个O（n）操作，当事件发生，poll返回将获得的数据传送到用户空间并执行释放内存和剥离等待队列等善后工作，向用户空间拷贝数据与剥离等待队列等操作的的时间复杂度同样是O（n）。

 

　　这两天看到一个云风他们那里的bug就是因为使用的开源库中作者使用了非阻塞connect使用select() 来等待超时，但是并未检查FD_SETSIZE，当文件描述符数目大于这个数目之后就会出现内存越界错误，造成coredump。
