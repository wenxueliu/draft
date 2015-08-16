#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

int main(int argc, char **argv) {
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

        //生成一个子进程来完成和客户端的会话，父进程继续监听, 也可以通过
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

