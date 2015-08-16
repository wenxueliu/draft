
###目标

从设计目标看G1完全是为了大型应用而准备的。



    支持很大的堆

    高吞吐量
    --支持多CPU和垃圾回收线程
    --在主线程暂停的情况下，使用并行收集
    --在主线程运行的情况下，使用并发收集

    实时目标：可配置在N毫秒内最多只占用M毫秒的时间进行垃圾回收

当然 G1 要达到实时性的要求, 相对传统的分代回收算法, 在性能上会有一些损失.


###算法详解

G1 可谓博采众家之长, 力求到达一种完美. 他吸取了增量收集优点, 把整个堆划分为
一个一个等大小的区域(region). 内存的回收和划分都以 region 为单位; 同时, 他也
吸取了 CMS 的特点, 把这个垃圾回收过程分为几个阶段, 分散一个垃圾回收过程; 而且,
G1 也认同分代垃圾回收的思想, 认为不同对象的生命周期不同, 可以采取不同收集方式,
因此, 它也支持分代的垃圾回收. 为了达到对回收时间的可预计性, G1 在扫描了 region
以后, 对其中的活跃对象的大小进行排序, 首先会收集那些活跃对象小的 region, 以便
快速回收空间(要复制的活跃对象少了), 因为活跃对象小, 里面可以认为多数都是垃圾,
所以这种方式被称为 Garbage First(G1) 的垃圾回收算法, 即: 垃圾优先的回收.

回收步骤:

###初始标记(Initial Marking)

G1 对于每个 region 都保存了两个标识用的 bitmap, 一个为 previous marking bitmap,
一个为 next marking bitmap, bitmap 中包含了一个 bit 的地址信息来指向对象的起始点.

开始 Initial Marking 之前, 首先并发的清空 next marking bitmap, 然后停止所有应用线程,
并扫描标识出每个 region 中 root 可直接访问到的对象, 将 region 中 top 的值放入 next
top at mark start(TAMS)中, 之后恢复所有应用线程.

触发这个步骤执行的条件为:

G1 定义了一个 JVM Heap 大小的百分比的阀值, 称为 h, 另外还有一个H, H的值为(1-h)*Heap
Size, 目前这个 h 的值是固定的, 后续 G1 也许会将其改为动态的, 根据 jvm 的运行情况来动
态的调整, 在分代方式下, G1 还定义了一个 u 以及 soft limit, soft limit 的值为
H-u*Heap Size, 当 Heap 中使用的内存超过了 soft limit 值时, 就会在一次 clean up 执行
完毕后在应用允许的 GC 暂停时间范围内尽快的执行此步骤:

在 pure 方式下, G1 将 marking 与 clean up 组成一个环, 以便 clean up 能充分的使用
marking 的信息, 当 clean up 开始回收时, 首先回收能够带来最多内存空间的 regions,
当经过多次的clean up, 回收到没多少空间的 regions 时, G1 重新初始化一个新的 marking
与 clean up 构成的环. ????

###并发标记(Concurrent Marking)

按照之前 Initial Marking 扫描到的对象进行遍历, 以识别这些对象的下层对象的活跃状态,
对于在此期间应用线程并发修改的对象的以来关系则记录到 remembered set logs 中, 新创
建的对象则放入比 top 值更高的地址区间中, 这些新创建的对象默认状态即为活跃的, 同时
修改 top 值.

###最终标记暂停(Final Marking Pause)

当应用线程的 remembered set logs 未满时, 是不会放入filled RS buffers 中的, 在这样
的情况下, 这些 remebered set logs 中记录的 card 的修改就会被更新了, 因此需要这一步,
这一步要做的就是把应用线程中存在的 remembered set logs 的内容进行处理, 并相应的修改
remembered sets, 这一步需要暂停应用,并行的运行.

###存活对象计算及清除(Live Data Counting and Cleanup)

值得注意的是, 在 G1 中, 并不是说 Final Marking Pause 执行完了, 就肯定执行 Cleanup 这
步的, 由于这步需要暂停应用, G1 为了能够达到准实时的要求, 需要根据用户指定的最大的 GC
造成的暂停时间来合理的规划什么时候执行 Cleanup , 另外还有几种情况也是会触发这个步骤
的执行的:

G1 采用的是复制方法来进行收集, 必须保证每次的 "to space" 的空间都是够的, 因此 G1 采取
的策略是当已经使用的内存空间达到了 H 时, 就执行 Cleanup 这个步骤;

对于 full-young 和 partially-young 的分代模式的 G1 而言, 则还有情况会触发 Cleanup 的执行,

full-young 模式下, G1 根据应用可接受的暂停时间, 回收 young regions 需要消耗的时间来估算出
一个 yound regions 的数量值, 当 JVM 中分配对象的 young regions 的数量达到此值时, Cleanup
就会执行;

partially-young 模式下, 则会尽量频繁的在应用可接受的暂停时间范围内执行 Cleanup, 并最大限
度的去执行 non-young regions 的 Cleanup。


疑问:
top 值:

参考

http://pengjiaheng.iteye.com/blog/548472
