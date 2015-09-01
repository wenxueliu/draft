
##poll

```
	#include <sys/poll.h>

	int poll (struct pollfd *fds, unsigned int nfds, int timeout);

	struct pollfd {
		int fd; /* file descriptor */
		short events; /* requested events to watch */
		short revents; /* returned events witnessed */

	};

```


　　其中POLLIN | POLLPRI等价于select()的读事件，POLLOUT | POLLWRBAND等价于select()的写事件。POLLIN等价于POLLRDNORM | POLLRDBAND，而POLLOUT则等价于POLLWRNORM。假如，要同时监视一个文件描述符是否可读和可写，我们可以设置events为POLLIN | POLLOUT。在poll返回时，我们可以检查revents中的标志，对应于文件描述符请求的events结构体。如果POLLIN事件被设置，则文件描述符可以被读取而不阻塞。如果POLLOUT被设置，则文件描述符可以写入而不导致阻塞。这些标志并不是互斥的：它们可能被同时设置，表示这个文件描述符的读取和写入操作都会正常返回而不阻塞。

　　timeout参数指定等待的毫秒数，无论I/O是否准备好，超时时间一到poll都会返回。timeout指定为负数值表示无限超时，UNPv1 中使用的INFTIM 宏貌似现在已经废弃，因此如果要设置无限等待，直接将timeout赋值为-1；timeout为0指示poll调用立即返回并列出准备好I/O的文件描述符，但并不等待其它的事件。

　　成功时，poll()返回结构体中revents域不为0的文件描述符个数；如果在超时前没有任何事件发生，poll()返回0；失败时，poll()返回-1。


```
//pollEcho.cpp
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
#include <poll.h>
#include <stropts.h>
#include <netdb.h>

#define PORT 1314
#define MAX_LINE_LEN 1024

int main()
{
    struct sockaddr_in cli_addr, server_addr;
    socklen_t addr_len;
    int one,flags,nrcv,nwrite,nready;
    
    int listenfd,connfd;
    char buf[MAX_LINE_LEN],addr_str[INET_ADDRSTRLEN];
    
    std::vector<struct pollfd> pollfdArray;
    struct pollfd pfd;
    
    bzero(&server_addr, sizeof server_addr);
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    
    listenfd = socket(AF_INET, SOCK_STREAM, 0);
    
    if( listenfd < 0)
    {
        printf("listen error: %s \n", strerror(errno));
        exit(1);
    }
       
    one = 1;
    setsockopt(listenfd,SOL_SOCKET,SO_REUSEADDR, &one, sizeof one);
    
    flags = fcntl(listenfd,F_GETFL,0);
    fcntl(listenfd, F_SETFL, flags | O_NONBLOCK);
    
    if(bind(listenfd,reinterpret_cast<struct sockaddr *>(&server_addr),sizeof(server_addr)) < 0)
    {
        printf("bind error: %s \n", strerror(errno));
        exit(1);
    }
    
    listen(listenfd, 100);
    
    pfd.fd = listenfd;
    pfd.events = POLLIN;
    
    pollfdArray.push_back(pfd);
    
    while(1)
    {
        nready = poll(&(*pollfdArray.begin()), pollfdArray.size(), -1);
        
        if( nready < 0)
        {
            printf("poll error: %s \n", strerror(errno));
        }
        
        if( pollfdArray[0].revents & POLLIN)
        {
            addr_len = sizeof cli_addr;
            connfd = accept(listenfd, reinterpret_cast<struct sockaddr *>(&cli_addr), &addr_len);
            
            if( connfd < 0)
            {
                if( errno != ECONNABORTED || errno != EWOULDBLOCK || errno != EINTR)
                {
                    printf("accept error: %s \n", strerror(errno));
                    continue;
                }
            }
            
            printf("recieve from : %s at port %d\n", inet_ntop(AF_INET,&cli_addr.sin_addr,addr_str,INET_ADDRSTRLEN),cli_addr.sin_port);
            
            flags = fcntl(connfd, F_GETFL, 0);
            fcntl(connfd,F_SETFL, flags | O_NONBLOCK);
            
            bzero(&pfd, sizeof pfd);
            
            pfd.fd = connfd;
            pfd.events = POLLIN;
            
            pollfdArray.push_back(pfd);
            
            if(--nready < 0)
            {
                continue;
            }
            
        }
        
        for( unsigned int i = 1; i < pollfdArray.size(); i++) // i from 1 not 0
        {
            pfd = pollfdArray[i];
            
            if(pfd.revents & (POLLIN | POLLERR))
            {
                memset(buf, 0, MAX_LINE_LEN);
                if( (nrcv = read(pfd.fd, buf, MAX_LINE_LEN)) < 0)
                {
                    if(errno != EWOULDBLOCK || errno != EAGAIN || errno != EINTR)
                    {
                        printf("read error: %s\n",strerror(errno));
                    }
                }
                else if( 0 == nrcv)
                {
                    close(pfd.fd);
                    pollfdArray.erase(pollfdArray.begin() + i);
                }
                else
                {
                    printf("nrcv: %s\n",buf);
                    nwrite = write(pfd.fd, buf, nrcv);
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


