
1. removal
2. reclamation

###典型的步骤

1 Remove pointers to a data structure, so that subsequent readers cannot gain a reference to it.
2 Wait for all previous readers to complete their RCU read-side critical sections.
3 (Atomic) At this point, there cannot be any readers who hold references to the data
structure, so it now may safely be reclaimed

###关键点:

* 仅限于指针
* 对指针的操作是原子的
* 多读少写的情况

###角色

* 读者
* 更新者
* 回收者

###问题

1. 在读者期间, 更新者进行多次更新, 那么, 待所有读者读完, 更新者的最后一次更新有效, 其他更新都是无效的, 这是期望的么?

   当更新者更新之后, 就必须等待从上次更新者到这次更新操作之前的所有读者都完成读操作, 并且同步之后,
   下一次更新者才能继续更新. 在同步之前, 下一次更新者只能等待.

2. reclamation 如何知道所有读者读完成 ?

引用计数


rcu_assign_pointer() : 更新者更新一个已经受 RCU 保护的指针为新值

rcu_dereference() : 读者获取一个已经受 RCU 保护的指针

    rcu_read_lock();
    p = rcu_dereference(head.next);
    a = p->address;
    rcu_read_unlock();
    x = p->address; /* BUG!!! */
    rcu_read_lock();
    y = p->data; /* BUG!!! */
    rcu_read_unlock();

###参考

https://github.com/torvalds/linux/blob/master/Documentation/RCU/whatisRCU.txt
