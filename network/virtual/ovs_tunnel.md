
$ sudo ovs-dpctl show

    system@ovs-system:
        lookups: hit:308129543 missed:38878373 lost:0
        flows: 0
        masks: hit:934093039 total:0 hit/pkt:2.69
        port 0: ovs-system (internal)
        port 1: ovs-s0 (internal)
        port 2: p4p2
        port 3: p4p3
        port 4: test (internal)







$ time sudo  strace -v  -T -r -c -p 2291
Process 2291 attached
^CProcess 2291 detached
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 61.03    0.079407         309       257           poll
 12.57    0.016357          13      1290      1290 accept
 10.61    0.013803          15       895       639 read
  6.57    0.008555           8      1130      1052 recvmsg
  5.32    0.006925          26       264           getrusage
  2.77    0.003608          37        98           sendmsg
  0.47    0.000614          25        25           write
  0.18    0.000232          33         7           open
  0.14    0.000178          25         7           mmap
  0.08    0.000101          14         7           ioctl
  0.07    0.000093          93         1           clone
  0.06    0.000084          12         7           munmap
  0.06    0.000081          81         1           restart_syscall
  0.05    0.000064           9         7           fstat
  0.01    0.000014           7         2           rt_sigprocmask
  0.00    0.000000           0         7           close
  0.00    0.000000           0         1           futex
------ ----------- ----------- --------- --------- ----------------
100.00    0.130116                  4006      2981 total

real    1m7.718s
user    0m0.067s
sys     0m0.150s


$ sudo perf stat -p 2291 sleep 60

 Performance counter stats for process id '2291':

        164.864807 task-clock (msec)         #    0.003 CPUs utilized          
             1,396 context-switches          #    0.008 M/sec                  
                75 cpu-migrations            #    0.455 K/sec                  
                 0 page-faults               #    0.000 K/sec                  
       157,433,064 cycles                    #    0.955 GHz
   <not supported> stalled-cycles-frontend 
   <not supported> stalled-cycles-backend
       147,629,803 instructions              #    0.94  insns per cycle
        32,994,162 branches                  #  200.129 M/sec                  
           888,282 branch-misses             #    2.69% of all branches        

      60.000586317 seconds time elapsed



TSO(tcp-segmentation-offload) : 一种利用网卡的少量处理能力，降低CPU发送数据包负载的技术，需要网卡硬件及驱动的支持。

###TSO

TSO(TCP Segmentation Offload) 是一种利用网卡对TCP数据包分片, 减轻CPU负荷的一种技术, 有时也被叫做
LSO (Large segment offload), TSO 是针对 TCP 的, UFO 是针对 UDP 的. 如果硬件支持 TSO 功能, 同时也需
要硬件支持的 TCP 校验计算和分散/聚集 (Scatter Gather) 功能.

###GSO

GSO(Generic Segmentation Offload) 它比 TSO 更通用, 基本思想就是尽可能的推迟数据分片直至发送到网卡
驱动之前, 此时会检查网卡是否支持分片功能(如TSO、UFO), 如果支持直接发送到网卡, 如果不支持就进行分片
后再发往网卡. 这样大数据包只需走一次协议栈, 而不是被分割成几个数据包分别走, 这就提高了效率.

###LRO

LRO(Large Receive Offload) 通过将接收到的多个 TCP 数据聚合成一个大的数据包, 然后传递给网络协议栈处理,
以减少上层协议栈处理开销, 提高系统接收 TCP 数据包的能力.

###GRO

GRO(Generic Receive Offload) 基本思想跟 LRO 类似, 克服了 LRO 的一些缺点, 更通用. 后续的驱动都使用 GRO
的接口, 而不是 LRO.

###RSS

RSS(Receive Side Scaling) 是一项网卡的新特性, 俗称多队列. 具备多个 RSS 队列的网卡, 可以将不同的网络流
分成不同的队列, 再分别将这些队列分配到多个 CPU 核心上进行处理, 从而将负荷分散, 充分利用多核处理器的能力.

可以使用如下命令来关闭对应的参数：
/usr/sbin/ethtool -K eth1 gro off
/usr/sbin/ethtool -K eth1 lro off
/usr/sbin/ethtool -K eth1 tso off

http://www.ibm.com/developerworks/cn/linux/l-cn-network-pt/
