HA Client

Controller


###关于缓存实现

###原则

1. 没有 100% 的可靠, 只有更可靠.


HA Client 定期(比如 10 s)向 HA Master 续约, 如果续约成功, 就继续为 Master
Controller

###可能存在的异常

####1. Master Controller 应用crash, 但是 Master Controller 所在的主机正常运行,
HA Client 运行正常

Master Controller Crash, HA Client 正常运行. 这种场景下, HA Client 向 HA Master
发送一个放弃 Controller Crash 报告, 并解除续约. HA Master收到请求后, 直接
将 Slave Controller 提升为 Master. 待原 Master Controller 起来后,作为 Slave
运行

####2. Master Controller 应用所在服务器 crash

此时, 由于 HA Client 和 Master Controller 同时 Crash, HA Master 和 HA
Client 直接无法通讯,这个时候还不能将 Slave Controller 立即提升为 Master
Controller(无法区分是服务器 crash 还是网络问题), 因此,HA Master 无法在
续约期内没有收到 HA Client 的续约, 因此会将 Slave Controller 提升为 Master
Controller. 待原 Master Controller 起来后, 作为 Slave Controller 运行

####3. Master Controller 正常, 但是 Master Controller 到 HA Master 之间
的网络出现问题

HA Client 无法在续约超时前获取续约, HA Client 将 Master Controller 降级为
Slave Controller

HA Master 也在续约超时前无法获取 HA Client 的续约. 故将 Slave Controller
提升为 Master Controller.

####4. HA Client crash, 但是 Controller 所在的主机正常运行,

将 HA Client 设置为不可杀死的 deamon 进程. 此外, HA Client 功能非常有限
出现 Crash 几率很小.

####5. Slave Controller 应用 crash, 但是 Slave Controller 所在的主机正常运行,

HA Client 运行正常

Slave Controller Crash, HA Client 正常运行. 这种场景下, HA Client 向 HA Master
发送一个 Slave Controller Crash 报告, 并解除续约. HA Master 收到请求后,
重启 Slave Controller

####2. Slave Controller 应用所在服务器 crash

HA Master 无法在续约期内没有收到 HA Client 的续约, 重启 Slave Controller

####Master Controller 和 Slave Controller 同时 crash.

根据可靠性需求, 增加 Slave Controller 的数量(据此又引入了将哪个Slave 提升为
Master 的问题, 一般思路, 最先续约的优先成为Master,)

####HA 软件的 crash

####HA 软件所在服务器 crash

HA Master 集群, 通过 Raft 算法选主,保持高可用.


因此,服务最大停服时间取决与续约时间, 这个可以更加业务要求,进行设置.

###思考问题

1. 为什么需要 HA 软件, 没有HA 软件是否可以解决 HA 问题.

2 当 Master crash, 如何保证 Master->Slave 和 Slave->Master 的切换顺序？还是不需要保证？

3 尤其是数据库服务器可能会遇到这种情况，就是服务器loading 过
重，完全无反应，连heartbeat 也无法传递，但此时服务器可能不是真的挂掉，
笔者开玩笑的说法是「假死」, 经过一段时间，loading 没那么重时，又会活过
来，heartbeat 又可以传递。

Fencing is the disconnection of a node from the cluster's shared storage.
Fencing cuts off I/O from shared storage, thus ensuring data integrity.

###参考

* fencing device
* RHCS
