openflow

###feature
* decouple  : the control and date are decouple
* centralized : network intelligence and state are logically centralized
* abstracted : underlying network infrastructure is abstracted from the applications
* programmability : highly scalable and flexible adapt to changing business needs
* automation : 


###多级流表

解决单级流表导致的流表数指数级增长问题.

比如 MAC 学习, 1000 台机器, 在单级流表下, 每两台机器之间需要 2 条流表,
需要 1000*1000 条流表, 在多级流表下, 只需要 2000 条流表.

此外, 基于 VLAN 的 MAC 转发, 50 个端口支持 100 的 MAC 转发表的交换机,
需要 50 * 100 条流表项, 而采用两级流表, 只需要 100 + 50 条流表项.

VRF(virtual route forwarding) 中, 如果是单级流表, 需要 Nport * Nvrf * Nipentry
采用两级流表 Nport + (Nvrf x Nipentry ) 条流表
