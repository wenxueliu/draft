##ZAB 协议实例

在一个分布式数据库系统中，如果各节点的初始状态一致，每个节点都执行相同的操作序列，
那么他们最后能得到一个一致的状态。为保证每个节点执行相同的命令序列，需要在每一条
指令上执行一个“一致性算法”以保证每个节点看到的指令一致

##前提

* 强一致性
* 可用
* 分区容忍

* 一个节点在任何时候可能停止, 重启
* 消息可能被延迟(序列号), 可能被重复(忽略), 可能丢失(TCP重传), 但是不会被损坏

##算法描述

* 消息广播
* 崩溃恢复

* 发现
* 同步
* 广播

* LOOKING
* FOLLOWING
* LEADING

##条件

* 5个节点(n1, n2, n3, n4, n5)
* 一个 leader, 四个 follower
* 只有 leader 才处理写请求, follower 只处理读请求
* 每个请求都包含两个事务 ID, 并且每个事务 ID 是全局递增. 消息顺序的事务 ID, 和 leader 的 ID
* 每个节点都可以接受读写请求, 如果 follower 节点接收到写请求都会转发给 leader
* 如果 nj 收到 ni 发送的消息, 那么 ni 确实发送了消息.(完整性)
* 每个节点处理新的消息, 必须保证之前的消息处理成功. 而消息的顺序依赖于递增的事务 ID(前置性)
* 每进行一次选主, leader 的 ID 都是递增的.
* leader 和所有 follower 保持心跳. 如果超时没有收到消息, leader 会放弃 leader * 角色. follower 会发起重新选举的消息
* leader 处于 leader 角色, 处于 LEADING 状态, 当不能保持与多于一半的节点保持联系, 失去 leader 角色, 处于 LOOKING 状态
* follower 处于 leader 角色, 处于 FOLLOWING 状态, 失去与 leader 联系, 处于 LOOKING 状态

##异常

* 宕机
* 网络异常

##选主


##写操作

###正常

假设 n1 是 leader , 此外 客户端发送写请求, 给任一节点, 如果 leader 接收到该请求, 直接处理, 如果 follower
接收到该写请求, 转发给 leader.

1. leader 在本地完成 写操作, 发起 proposal 写请求给所有的 follower, follower 接收 leader 的请求
2. 如果 follower 接收到 leader 的请求, 在本地完成写操作, 如果写操作成功, 应答写操作成功给 leader
3. leader 接收到一半以上 follower 应答写操作成功, 完成本地事务提交. (此时, leader 认为该写操作是成功的)
4. leader 发送事务写成功广播给所有 follower, follower 接收 leader 的广播
5. follower 接受到 leader 的事务提交广播消息, 在本地完成事务提交. (至此, follower 认为该写操作成功.)
6. leadr 接收到一半以上 follower 应答提交成功. 写操作成功.

###异常及处理

异常一

* 发生超过一半 follower 网络异常(宕机)

结果及处理办法

* (2) 中少于一半 follower 没有接受到 leader 请求
* (3) leader 没有接收到超过一半 follower 的成功应答, 因此, 进入重新选主的阶段.

异常二

* (2) 如果超过一半 follower 接收到 leader 的请求, 但有部分没有完成本地写操作(或宕机)

结果及处理办法

* (2) 少于一半应答写成功给 leader
* (3) leader 没有接收到超过一半 follower 的成功应答, 因此, 进入重新选主的阶段.

异常三

* (2) 如果超过一半 follower 接收到 leader 的请求, 而且超过一半完成写请求, 但由于网络异常(宕机), 少于一半成功发送应答给 leader

结果及处理办法

* (2) 少于一半应答写成功给 leader
* (3) leader 没有接收到超过一半 follower 的成功应答, 因此, 进入重新选主的阶段.

异常四

* leader 少于一半接收到 follower 应答写成功. 异常参考异常一, 二, 三.

结果及处理办法

* 因此, 进入重新选主的阶段.

异常五

* leader 在本地完成事务提及失败

结果及处理办法

* leader 发送写失败广播给所有 follower

异常六

* 异常五, 广播消息发生网络异常(写成功的 follower 宕机)

结果及处理办法

* 如果之前写失败的 follower 收到该消息, 忽略
* 如果写成功的 follower 没有收到写失败广播 , 超时, follower 取消本地提交.
* 如果写成功的 follower 收到写失败的广播, 取消事务提交

异常七

* leader 发送事务提交广播消息, 但发生网络异常(宕机)之前写成功的 follower 中加起来少于一半收到 leader 广播信息.

结果及处理办法

* 如果之前写失败的 follower 收到该消息, 忽略
* 如果写成功的 follower 没有收到写成功广播, 超时, follower 取消本地提交.
* 如果写成功的 follower 收到写成功的广播, 完成事务提交
* follower 宕机, follower 重启后, 取消之前的事务

此时会出现数据不一致: 由于少于返回给 leader, 因此, 在 进行 leader 选举之前,
后续读写提及成功的节点的值, 会读取到提交的值, 但这个值会在新的选举成功之后, 被取消掉.

异常八

* 异常七中, 由于少于一半的 follower 完成真实的事务提交.

结果及处理办法

* leader 进行重新选主. (此时, leader 在完成事务提交的节点中产生)

##正常读操作

TODO


##问题

###只有 leader 能处理写请求, 那么 leader 会成为整个系统的瓶颈, 让 follower 也可以直接处理写请求, 这样会更复杂么?

###是否每个节点都是对等的, 即 P2P 协议?


##角色

proposer : P1
acceptor :
value    : V






##Paxos


* promise：Acceptor对proposer承诺，如果没有更大编号的proposal会accept它提交的proposal
* accept ：Acceptor没有发现有比之前的proposal更大编号的proposal，就批准了该proposal
* chosen ：当Acceptor的多数派都accept一个proposal时，该proposal就被最终选择，也称为决议

three class of agent:

* proposers
* acceptors
* learners

a single process may act as more than one agent

agents can communicate with one another by sending mes-
sages.

* Agents operate at arbitrary speed, may fail by stopping, and may
restart. Since all agents may fail after a value is chosen and then
restart, a solution is impossible unless some information can be re-
membered by an agent that has failed and restarted.

* Messages can take arbitrarily long to be delivered, can be duplicated,
and can be lost, but they are not corrupted.


###The Problem

Assume a collection of processes that can propose values. A consensus al-
gorithm ensures that a single one among the proposed values is chosen. If
no value is proposed, then no value should be chosen. If a value has been
chosen, then processes should be able to learn the chosen value. The safety
requirements for consensus are:

* Only a value that has been proposed may be chosen,
* Only a single value is chosen, and
* A process never learns that a value has been chosen unless it actually
has been.

We won’t try to specify precise liveness requirements. However, the goal is
to ensure that some proposed value is eventually chosen and, if a value has
been chosen, then a process can eventually learn the value.

###Choosing a Value

A proposer sends a proposed value to a set of acceptors. An acceptor may
accept the proposed value. The value is chosen when a large enough set of
acceptors have accepted it.

How large is large enough?

To ensure that only a single value is chosen, we can let a large
enough set consist of any majority of the agents. Because any two majorities
have at least one acceptor in common, this works if an acceptor can accept
at most one value.

In the absence of failure or message loss, we want a value to be chosen
even if only one value is proposed by a single proposer. This suggests the
requirement:

P1. An acceptor must accept the first proposal that it receives.

But this requirement raises a problem.

Several values could be proposed by different proposers at about the same
time, leading to a situation in which every acceptor has accepted a value,
but no single value is accepted by a majority of them.

Even with just two proposed values, if each is accepted by about half the
acceptors, failure of a single acceptor could make it impossible to learn
which of the values was chosen.

P1 and the requirement that a value is chosen only when it is accepted
by a majority of acceptors imply that an acceptor must be allowed to accept
more than one proposal.

We keep track of the different proposals that an acceptor may accept by
assigning a (natural) number to each proposal, so a proposal consists of
a proposal number and a value. To prevent confusion, we require that
different proposals have different numbers. How this is achieved depends
on the implementation, so for now we just assume it.

A value is chosen when a single proposal with that value has been accepted by
a majority of the acceptors. In that case, we say that the proposal (as well
as its value) has been chosen.

We can allow multiple proposals to be chosen, but we must guarantee
that all chosen proposals have the same value. By induction on the proposal
number, it suffices to guarantee:

P2. If a proposal with value v is chosen, then every higher-numbered pro-
posal that is chosen has value v .

Since numbers are totally ordered, condition P2 guarantees the crucial safety
property that only a single value is chosen.

To be chosen, a proposal must be accepted by at least one acceptor. So,
we can satisfy P2 by satisfying:

P2^a . If a proposal with value v is chosen, then every higher-numbered pro-
posal accepted by any acceptor has value v .

We still maintain P1 to ensure that some proposal is chosen. Because com-
munication is asynchronous, a proposal could be chosen with some particu-
lar acceptor c never having received any proposal. Suppose a new proposer
“wakes up” and issues a higher-numbered proposal with a different value.
P1 requires c to accept this proposal, violating P2 a . Maintaining both P1
and P2 a requires strengthening P2 a to:

P2^b . If a proposal with value v is chosen, then every higher-numbered pro-
posal issued by any proposer has value v .

Since a proposal must be issued by a proposer before it can be accepted by
an acceptor, P2 b implies P2 a , which in turn implies P 2.

To discover how to satisfy P2 b , let’s consider how we would prove that
it holds. We would assume that some proposal with number m and value
v is chosen and show that any proposal issued with number n > m also
has value v .


完整的算法描述

Phase 1. (a) A proposer selects a proposal number n and sends a prepare
request with number n to a majority of acceptors.
(b) If an acceptor receives a prepare request with number n greater
than that of any prepare request to which it has already responded,
then it responds to the request with a promise not to accept any more
proposals numbered less than n and with the highest-numbered pro-
posal (if any) that it has accepted.

Phase 2. (a) If the proposer receives a response to its prepare requests
(numbered n) from a majority of acceptors, then it sends an accept
request to each of those acceptors for a proposal numbered n with a
value v , where v is the value of the highest-numbered proposal among
the responses, or is any value if the responses reported no proposals.
(b) If an acceptor receives an accept request for a proposal numbered
n, it accepts the proposal unless it has already responded to a prepare
request having a number greater than n.

A proposer can make multiple proposals, so long as it follows the algorithm
for each one. It can abandon a proposal in the middle of the protocol at any
time.(Correctness is maintained, even though requests and/or responses
for the proposal may arrive at their destinations long after the proposal
was abandoned.)  It is probably a good idea to abandon a proposal if some
proposer has begun trying to issue a higher-numbered one. Therefore, if an
acceptor ignores a prepare or accept request because it has already received
a prepare request with a higher number, then it should probably inform
the proposer, who should then abandon its proposal. This is a performance
optimization that does not affect correctness.

###Learner algorithm

To learn that a value has been chosen, a learner must find out that a pro-
posal has been accepted by a majority of acceptors. The obvious algorithm
is to have each acceptor, whenever it accepts a proposal, respond to all
learners, sending them the proposal. This allows learners to find out about
a chosen value as soon as possible, but it requires each acceptor to respond
to each learner—a number of responses equal to the product of the number
of acceptors and the number of learners.

More generally, the acceptors could respond with their acceptances to
some set of distinguished learners, each of which can then inform all the
learners when a value has been chosen. Using a larger set of distinguished
learners provides greater reliability at the cost of greater communication
complexity.

Because of message loss, a value could be chosen with no learner ever
finding out. The learner could ask the acceptors what proposals they have
accepted, but failure of an acceptor could make it impossible to know whether
or not a majority had accepted a particular proposal. In that case, learners
will find out what value is chosen only when a new proposal is chosen. If
a learner needs to know whether a value has been chosen, it can have a
proposer issue a proposal, using the algorithm described above.





结论

Only a value that has been proposed may be chosen

为此条件一

    选中的 value, 必须被多于一半 acceptor 接受.

必须被满足

为了让条件一可行, 条件二

    一个 acceptor 同时只能接受一个 proposer 的 proposal number 和 value

这里暗含 acceptor 可以接受多个 proposer 的 proposer number 但是, 最终
只选择一个, 要不保留旧的, 要不丢弃旧的, 采用新的.

必须满足

即(逆向思维), 为了满足结论, 必须满足条件一, 为了满足条件一, 条件二必须被满足

需要注意的是这里条件一和条件二是必要条件而非充分条件.


我们先证明条件一必须被满足:

如果选中的 value 没有被超过一半的 acceptor 接受, 那么, 就可能导致不知道以
哪个 value 为准. 比如 proposer1, proposer2 分别提出 value1, value2, 各自被
一半的 acceptor 接受. 那么, 就无法确定最终哪个 value 被选中.

证明条件二必须被满足:

如果一个 acceptor 可以接受多余一个 proposer 的 proposal, 那么, 最终
就会出现两个 value 都被多于一半的 acceptor 接受的情况, 仍然无法确保哪个被选中.


此外, 条件二暗含一个条件, 即条件三

    为了让一个 acceptor 可以一个接受 process 的 proposal, 那么它必须接受它收到的第一个 proposal

必须被满足

条件三有一个问题,

如果有 proposer 同时 proposed 不同的 value, 这可能导致没有一个 acceptor 可以接受
多余一半的 proposal(条件一).

最简单的例子, 比如 proposer1, proposer2 分别提出 value1, value2, 有一半的 acceptor
第一个收到的 proposal 是 value1, 一半的 acceptor 第一个收到 proposal 是 value2
这显然违反了条件一. 也许让 acceptor 成为奇数, 能解决上面例子的问题, 事实上不行,
例子也不难找到.

原文相似描述

    Several values could be proposed by different proposers at about the same
    time, leading to a situation in which every acceptor has accepted a value,
    but no single value is accepted by a majority of them.

    Even with just two proposed values, if each is accepted by about half the
    acceptors, failure of a single acceptor could make it impossible to learn
    which of the values was chosen.

因此, 为了让条件三满足, 必须增加更多的约束

条件三和条件一同时满足, 暗含一个条件, 即条件四

    一个 acceptor 必须允许接受多于一个 proposal

必须满足

为了支持条件四, 必须对同一个 acceptor 收到的不同 proposer 的 proposal 加以区别.
解决办法很简单, 就是每一个 acceptor 接受到的消息包含 proposal number 和 value.
为了解决不同的 proposer 提出相同的 value 导致的混淆. 不同的 proposer 的 proposal number
必须不同. 至于如何保证每个 proposer 的 proposal number 不同, 这是一个实现问题.
我们假设可以已经实现.

现在一个 acceptor 可以接受多个 proposer 的 proposal 了, 但一个问题必须解决,
一个 acceptor 已经接受了一个 proposer 的 proposal 了, 新来的 proposer 到底是
接受呢还是拒绝呢? 为了满足确保一个 value 被多余一半的 acceptor 接受, 我们必须
对条件四加以约束.

条件五


    如果一个 proposal 的 value v 被最终选中, 那么, 该
    acceptor 的 proposal 就是 (n,v). 如果后续收到其他 proposer 的 proposal 为 (m, u)
    那么, u 必须等于 v. m 必须大于 n.

必须被满足

TODO : 如果一个 acceptor 第一次收到了一个 proposer 的 proposal 为 (n, v)

问题, 为什么是这样的约束条件, 可以是其他么? 此处按下不表.

一个 proposer 的 proposal 的 value 被选中, 至少被一个 acceptor 接受, 即为了满足条件五,
可以通过满足条件六获得.

条件六

    如果一个 proposal 的 (n,v) 已经被最终选中, 每个 proposal number 为 m (m > n)
    的 proposal 只能被任何 value 已经为 v 的 acceptor 接受

必须满足

但是条件六存在一个问题, 由于网络是异步的, 完成可能存在一个 acceptor 首次收到
proposer 的 proposal 为 (m, u) (m > n, u != v), 根据条件三, 该 acceptor 必须
接受该 proposal. 但是, 这与条件六冲突了(该 proposal 只能被 value 为 v 的
acceptor 接受, 但当前接受的 acceptor 没有 value 为 v).

因此为了让条件六和条件三不冲突(即同时满足), 需要修改条件六为条件七

    如果一个 proposal 的 (n,v) 已经被最终选中, 每个 proposal number 为 m(m > n)
    的 proposal 必须被 value 为 v 的 proposer 发布

由于一个 proposal 被 acceptor 接受之前, 必须被 proposer 发布.

满足条件七, 必然满足条件六, 当然也与条件三不冲突.


根据条件七, 假设 proposal 为 (m, v), 那么任何 proposal number 为 n(n > m) 的 proposal,
它的 value 为 v.

求证: 对于 proposal number 为 i(m <= i <= n-1) proposal, value 为 v 被选中. 证明
proposal number 为 n 的 proposal 的 value 为 v

由于 proposal number 为 m 的 proposal 被选中. 因此, 存在 acceptors 的子集 C (C
为 acceptors 的大多数, C 中每个 proposal 的 proposal number 为 m...n-1, 每个
acceptor 的 value 为 v), 任何其他子集 S 也为 acceptors 的大多数, 那么, S 和 C
必然存在交集.


S 为 acceptors 的一个(包含多数元素)子集, S 中至少有一个 acceptor 为 C 的元素.
为了得到 proposal number 为 n 的 proposal 的 value 为 v. 可以通过下面的条件八
的不变性来得到.

条件八

对应任何 (n,v), 如果 (n,v) 的 proposal 被发布, 那就有一个集合 S 包含大多数的
acceptors, 对于 S 中的每一个元素, 满足以下两个条件之一
1. S 中没有任何 acceptor 接受 proposal number 低于 n 的 proposal
2. 对于 S 中的 acceptor 接受的 proposal 中, 如果 proposal number 小于 n,
proposal number 最大的 proposal 的 value 为 n

通过保留条件八来满足条件七

为了保留条件八的不变性, 一个想发布 proposal number 为 n 的 proposer, 必须学习
最大 proposal number(小于 n)的 proposal. (已经接受或将被接受被 acceptors 的大多数)

学习已经接受过的 proposal 非常容易, 预测将来的 acceptors 非常难, 与其预测将来,
proposer 通过提取约定, TODO, 换而言之, proposer 请求 acceptor, 该 acceptor 没有接受
任何 proposal number 小于 n 的 proposal. 为了保留 proposal 这导致下面的算法

###proposer 的算法.

1) 一个 proposer 选择一个新的 proposal number n, 发送一个请求给 acceptors
子集中的每个成员, 请求 acceptor 应答:

(a) 不接受任何 proposal number 小于 n 的 proposal
(b) 已经接受过的且小于 n 的最大 proposal number 的 proposal

这被称为 proposal number 为 n 的 prepare 请求

2) 如果一个 proposer 接受多余一半 acceptors 的应答就发布 (n,v) 的 proposal. 其中
value 是所有应答中 proposal number 最大的 proposal 对应的 value. 如果应答中没有
proposal, (n,v) 就是 proposer 发送的 proposal.

这被称为 accept 请求

注: 1) 和 2) 中的 acceptors 不需要是完全相同的.

###acceptor 的算法

在没有损害安全性的前提下, 一个 acceptor 可以忽略任何请求.

一个 acceptor 如果没有应答 proposal number 大于 n 的 prepare 请求, 就可以接受一个
proposal number 为 n 的 proposal.


















一个 processes 的集合定义为 P.  一个一致性的算法确保只有一个值被选择，如果有一个值被最终选择,
那么其他 process 可以学习到该值. 为了满足这个条件需要一些约束:

* Only a value that has been proposed may be chosen,
* Only a single value is chosen, and
* A process never learns that a value has been chosen unless it actually
has been. 如果一个 process 的 value 被选中, 则该 process 不会学习


条件一, 一个提议被接受的条件是, 多于一半 acceptor 接受了该提议的 value

条件二, 每个 acceptor 无条件接受收到的第一个提议及其所携带值

An acceptor must accept the first proposal that it receives.

如果多个 proposal 提出多个 value , 但是没有一个 value 被多数 acceptor 接受怎么办?
如果多个 proposal 都被多于一半 acceptor 接受怎么解决?

1,2 暗示一个 acceptor 必须允许接受多个 proposal 的提议, 因此，为了区别不同的
proposal，一个 acceptor 接受的提议必须包含 proposal number 和 value, 为了防止
混淆, 不同的提议必须包含不同的 proposal number.

一个 acceptor 可以接受多个提议, 但为了同时保证每次只选出一个值. 也即

条件三 If a proposal with value v is chosen, then every higher-numbered proposal that is chosen has value v.

条件三满足了 1) 每个 acceptor 只有一个单独的 value 被选择; 2) 每个 acceptor 可以接受多个提议

为了满足条件三

条件四 如果提议的 vaule 被最终选择, 那么，每个更高的 proposal number 只能被已经接受了 value 的 acceptor 接受.

If a proposal with value v is chosen, then every higher-numbered proposal accepted by any acceptor has value v.

由于通信是异步的, 如果一个 acceptor C 没有接受提议1(proposal number 为 x)的
value. 直接接受了提议2(proposal number 为 y,y>x), 为了让 acceptor C 接受提议 1,
将条件四加强为:

条件五, 如果 P 的 vaule 被最终选择, 那么, 每个更高的 proposal number
被任何 V=value 的 Pi

If a proposal with value v is chosen, then every higher-numbered pro-
posal issued by any proposer has value v

条件五包含条件四，和条件三

条件五可以用数学表示为, 为了 (m, v) 被最终选择, 那么, Pi(i > m), Pi->value == m.

证明:

条件: 最终 Pm->value = v 被选中, Pi(m<i<n), Pi->value = v, acceptor 集合 A, C 是 A 的多数.
C 中每个元素都接受 (Pi,v), 那么, A 中任何包含大多数的子集 S, S 中至少有一个是 C 中的元素.

S 是 A 的多数. 那么必须满足两个条件中的一个:

1. S 中没有任何 acceptor 接受小于 proposal number 小于 n 的提议.
2. S 中 acceptor, 任何 proposal number 低于 n 的 proposer 中, v 是 proposal number 最高的值.

一个 proposer 必须学习 proposal number 小于 n 中最高的 highest-numbered proposal

proposal number 为 n 的 proposer 请求 acceptor 不要接受 proposal number 小于 n
的 proposal

条件六, 一个 acceptor 可以接受一个 proposal number n 如果它没有应答 proposal
number 大于 n 的 prepare 请求. 也即 一个 acceptor 只接受 proposal number 大于
它之前接受过的 proposal number.


