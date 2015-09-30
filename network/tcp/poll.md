
##poll

```
	#include <sys/poll.h>

	int poll (struct pollfd *fds, unsigned int nfds, int timeout);

	struct pollfd {
		int fd; /* file descriptor */
		short events; /* requested events to watch */
		short revents; /* returned events witnessed */

	};

    详细描述见 man poll
```


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
    int one, flags, nrcv, nwrite, nready;

    int listenfd,connfd;
    char buf[MAX_LINE_LEN],addr_str[INET_ADDRSTRLEN];

    std::vector<struct pollfd> pollfdArray;
    struct pollfd pfd;

    bzero(&server_addr, sizeof server_addr);
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);

    listenfd = socket(AF_INET, SOCK_STREAM, 0);

    if (listenfd < 0) {
        printf("listen error: %s \n", strerror(errno));
        exit(1);
    }

    one = 1;
    setsockopt(listenfd,SOL_SOCKET,SO_REUSEADDR, &one, sizeof one);

    flags = fcntl(listenfd,F_GETFL,0);
    fcntl(listenfd, F_SETFL, flags | O_NONBLOCK);

    if (bind(listenfd, reinterpret_cast<struct sockaddr *>(&server_addr), sizeof(server_addr)) < 0) {
        printf("bind error: %s \n", strerror(errno));
        exit(1);
    }

    listen(listenfd, 100);

    pfd.fd = listenfd;
    pfd.events = POLLIN;

    pollfdArray.push_back(pfd);

    while(1) {
        nready = poll(&(*pollfdArray.begin()), pollfdArray.size(), -1);

        if (nready < 0) {
            printf("poll error: %s \n", strerror(errno));
        }

        if (pollfdArray[0].revents & POLLIN) {
            addr_len = sizeof cli_addr;
            connfd = accept(listenfd, reinterpret_cast<struct sockaddr *>(&cli_addr), &addr_len);

            if (connfd < 0) {
                if (errno != ECONNABORTED || errno != EWOULDBLOCK || errno != EINTR) {
                    printf("accept error: %s \n", strerror(errno));
                    continue;
                }
            }

            printf("recieve from : %s at port %d\n", inet_ntop(AF_INET, &cli_addr.sin_addr, addr_str, INET_ADDRSTRLEN), cli_addr.sin_port);

            flags = fcntl(connfd, F_GETFL, 0);
            fcntl(connfd,F_SETFL, flags | O_NONBLOCK);

            bzero(&pfd, sizeof pfd);
            pfd.fd = connfd;
            pfd.events = POLLIN;

            pollfdArray.push_back(pfd);
            if(--nready < 0) {
                continue;
            }
        }

        for (unsigned int i = 1; i < pollfdArray.size(); i++) {
            pfd = pollfdArray[i];

            if (pfd.revents & (POLLIN | POLLERR)) {
                memset(buf, 0, MAX_LINE_LEN);
                if( (nrcv = read(pfd.fd, buf, MAX_LINE_LEN)) < 0) {
                    if(errno != EWOULDBLOCK || errno != EAGAIN || errno != EINTR) {
                        printf("read error: %s\n",strerror(errno));
                    }
                } else if( 0 == nrcv) {
                    close(pfd.fd);
                    pollfdArray.erase(pollfdArray.begin() + i);
                } else {
                    printf("nrcv: %s\n",buf);
                    nwrite = write(pfd.fd, buf, nrcv);
                    if (nwrite < 0) {
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

