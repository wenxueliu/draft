
###部署注意问题

* 超级进程管理
* 监控
* 日志, snap 文件定期清理, 专用日志设备
* 集群中的配置文件一定要一致
* 关闭 swap 分区

参考 https://zookeeper.apache.org/doc/trunk/zookeeperAdmin.html

##事务日志

###日志格式
/*
 * LogFile:
 *     FileHeader TxnList ZeroPad
 * 
 * FileHeader: {
 *     magic 4bytes (ZKLG)
 *     version 4bytes
 *     dbid 8bytes
 *   }
 * 
 * TxnList: *     Txn || Txn TxnList
 *     
 * Txn:
 *     checksum Txnlen TxnHeader Record 0x42
 * 
 * checksum: 8bytes Adler32 is currently used
 *   calculated across payload -- TxnHeader, Record
 * 
 * Txnlen:
 *     len 4bytes -- TxnHeader + Record
 * 
 * TxnHeader: {
 *     sessionid 8bytes
 *     cxid 4bytes
 *     zxid 8bytes
 *     time 8bytes
 *     type 4bytes
 *   }
 *     
 * Record:
 *     See Jute definition file for details on the various record types
 *      
 * ZeroPad:
 *     0 padded to EOF (filled during preallocation stage)
 */

1. 采用 Adler-32 校验事务日志
2. 实现 DataOuput 接口的 DataOutputStream 序列化具体 java 对象到 byte 流
3. BufferedOutputStream -> FileOutputStream -> File
4. DataOutputStream(实现 DataOuput 接口) -> BufferedOutputStream 实现 java 到 byte 的转换并写入 BufferedOutputStream
   PositionInputStream -> BufferedInputStream -> FileInputStream(logFile)
5. Log 文件名以 log.zxid 格式

其中 BufferedOutputStream buffer 大小为默认buffer 8192, 大于 8192 将刷新到 FileOutputStream

首先, 数据通过 DataOutputStream 写到 BufferedOutputStream, BufferedOutputStream
中 buffer 中超过 8192 byte 数据就刷新到 FileOutputStream. FileOutputStream 中每
次 buffer 不够就预分配 preAllocSize. 调用 flush 刷新到操作系统的文件 pageCache,
当调用 force 的时候才会真正的写入磁盘.


logDir           : 日志目录
long currentSize : 文件大小(byte)
LinkedList<FileOutputStream> streamsToFlush :

* synchronized boolean append(TxnHeader hdr, Record txn)

将 TxnHeader, Record 转为二进制, 采用 [Adler-32][1] 算法校验. 

1. 如果 FileHeader 没有创建, 创建之. 创建 FileHeader 后立即刷新 FileHeader 到磁盘. 并将对应的 FileOutputStream 加入 streamsToFlush
2. 计算预分配空间是否够用(position + 4096 > currentSize), 如果不够, 预分配 preAllocSize;
3. 计算 hdr, txn 的 Adler-32 值.
4. 写 校验值, TxnHeader, Record, 0x42 到磁盘缓存


* static File[] getLogFiles(File[] logDirList,long snapshotZxid)

提取 LogDir 中所有文件中的 fzxid, 找到 zxid 大于 snapshotZxid 的文件列表. 注: Log 文件名以 log.zxid 格式

1. 将 log 文件以 zxid 升序排序
2. 遍历 logDirList 中的每个元素, 记录所有文件名中 zxid 的最大值 logZid(logZxid < snapshotZxid)
3. 找到大于 logZid 的所有文件列表, 并返回

* long getLastLoggedZxid()

提取 LogDir 中所有文件中最大 fzxid 对应文件中最大的 zxid

* void close(TxnIterator itr)

iter.close()

* synchronized void commit()

1. 将 logStream 刷新到 FileOutputStream. 将 streamsToFlush 中的 FileOutputStream 写刷新到操作 pageCache, 之后刷新到磁盘. 数据元数据并不能保证写到磁盘
2. 关闭 streamsToFlush 中的 FileOutputStream. 为什么?

* TxnIterator read(long zxid)

从 logDir 读出 zxid 所在文件对应 zxid 的 hdr, record

* TxnIterator read(long zxid, boolean fastForward)

如果 fastForward = true; 从配置文件夹读出 zxid 所在文件对应 zxid 的 hdr, record
如果 fastForward = false; 从配置文件夹读出 zxid 所在文件第一个 hdr, record

* boolean truncate(long zxid)

删除 logDir 中 zxid 对应之后的所有日志文件

* static FileHeader readHeader(File file)

从 file 读出 FileHeader 之后解序列化为 hdr, 后返回 hdr.

* long getDbId()

读出 logDir 中 zxid 对应文件头的 dbid

* boolean isForceSync()

设置强制刷新

* PositionInputStream extends FilterInputStream

增加 position 参数

[1]: https://en.wikipedia.org/wiki/Adler-32

####日志清理

    java -cp zookeeper.jar:lib/slf4j-api-1.7.5.jar:lib/slf4j-log4j12-1.7.5.jar:lib/log4j-1.2.16.jar:conf org.apache.zookeeper.server.PurgeTxnLog <dataDir> <snapDir> -n <count>
