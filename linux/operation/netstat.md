

平时只用 netstat -ant 来查看当前 TCP 连接是否成功. 一直没有整理 netstat
的全部使用, 最近, 在诊断 TCP 问题上, 各种纠结, 结果在网络上乱逛的时候
发现[这篇文章]:[1], 于是决定仔细梳理一下 netstat 的命令.



##netstat -s


202270382 invalid SYN cookies received                      : 三次握手 ack 包, syncookies 校验没通过;
13700572 resets received for embryonic SYN_RECV sockets     : syn_recv状态下, 收到非重传的 syn 包, 则返回 reset
1123035 passive connections rejected because of time stamp  : 开启 sysctl_tw_recycle, syn 包相应连接的时间戳小于路由中保存的时间戳;
14886782 failed connection attempts                         : syn_recv 状态下, socket 被关闭; 或者收到 syn 包(非重传)
438798 times the listen queue of a socket overflowed        : 收到三次握手ack包，accept队列满
438798 SYNs to LISTEN sockets ignored                       : 收到三次握手ack包，因各种原因（包括accept队列满） 创建socket失败

[1]: http://huoding.com/2015/04/09/427

参考

http://blog.sina.com.cn/s/blog_781b0c850101pu2q.html
