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

		//生成一个子进程来完成和客户端的会话，父进程继续监听
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

