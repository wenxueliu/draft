

首先 git clone githu



http://www.coderli.com/netty-course-hello-world
http://seeallhearall.blogspot.com/2012/05/netty-tutorial-part-1-introduction-to.html

确保你已经阅读这个 guide http://netty.io/3.8/guide/  或 http://docs.jboss.org/netty/3.2/guide/html/start.html

##基础知识

TCP, UDP 基本知识。

java 基本语法及知识


##模型


###Channel  

路径抽象，用于连接服务端和客户端，传输的内容是二进制流。

Channel 的创建有一个专门抽象的 ChannelFactory 类。工厂做什么事，生产各种 Channel，自然而直观。那么它能生产哪些 Channel 呢？

* TCP NIO Channels: NioClientSocketChannelFactory and NioServerSocketChannelFactory
* UDP NIO Channels: NioDatagramChannelFactory
* TCP OIO Channels: OioClientSocketChannelFactory and OioServerSocketChannelFactory
* UDP OIO Channels: OioDatagramChannelFactory 
* HTTP Client:  HttpTunnelingClientSocketChannelFactory
* Local Channels: DefaultLocalClientChannelFactory and DefaultLocalServerChannelFactory 

###Exectors

执行建立 Channel 后，负责后续任务处理。在 Channel 的两端都存在。包括分配任务，执行任务两部分。

#### Boss Thread

	Boss thread create and connect/bind sockets and then pass them off to the worker threads.

分配任务。用于创建，连接或绑定 socket。然后，将连接交给 Worker Threads 处理。Boss Thread 与 Channel 的关系是一对一，或一对多

#### Worker Threads

	Worker threads perform all the asynchronous I/O,They are not general purpose threads and developers should take precautions not to assign unrelated tasks to threads in this pool which may cause the threads to block, be rendered unable to perform their real work which in turn may cause deadlocks and an untold number of performance issues.

执行任务。异步的 IO 操作。Worker Thread 与 Boss Thread 是多对一。


###ChannelPipeline

预处理过程的抽象。当数据到达后，自然的想法是在进行数据处理之前，做一系列预处理。ChannelPipeline 对预处理过程的抽象。处理顺序是非常严格，不能随意安排。

####ChannelHandler

在一系列中的一个处理。


###Buffer

内容抽象，位于 Channel 的两端，与 Channel 直接连接，既可以向 Channel 中写数据，也可以从 Channel 中读数据。由 Worker Threads 管理。

* ChannelBuffer
* 
####Encode Decode

由于 Channle 传输的是二进制流，所以发送端必须将你要传输的内容进行编码为某种二进制流，反之，接受端要将二进制流解码为可以使用的对象。

Netty SDK提供了不同种类的编解码器，例如Google ProtoBufs、Compression、Http Request/Response和Base64。

###ChannelEvent

###Upstream and Downstream

对数据流向的抽象。以当前端为参考， Upstream 数据的来源（读）， Downstream 数据的去向（写）。


###BootServer
###ChannelHandler


###NIO  netty  Jboss 关系

NIO仅仅是一个网络传输框架，而Netty是一个网络应用框架，包括网络以及应用的分层结构。

Netty3.x 包名为 org.jboss.netty，是 JBoss.org 的一部分
Netty4.0 包名从org.jboss.netty改为io.netty，不在是JBoss.org的一部分了。 具体变化参考[这里](http://www.oschina.net/translate/netty-4-0-new-and-noteworthy?print)

###jetty MINA

###术语

POJO:  Plain Old Java Object
BIO



###NIO

The NIO ("New I/O") package1 was introduced in Java 1.4 to get round certain limitations of the original Java I/O package. The main features of NIO are:

    buffers: the java.io package had essentially focussed on stream-based I/O; it is often fiddly to "read a block of data and then process it as a block";
    memory-mapped files: on a related point, the java.io package did not provide file mapping, a feature offered by modern operating systems in which part of a file is effectively "mapped" into memory and accessed as though it were memory— see the section on mapped ByteBuffers for more details;
    readiness selection: when managing concurrent network connections (and indeed, concurrently open streams in general), the traditional I/O package focussed on the conventional way of managing those connections, in which each connection is handled by a separate thread; modern operating systems provide more efficient methods, including readiness selection, in which one thread can poll and handle a number of connections;
    direct transfer of data within kernel memory space: pre-NIO, stream data had to be manipulated at the Java level so that, for example, transferring data from one stream to another had to involve spurious buffer copying from the OS into Java and then back again; NIO, via the new concept of channels, provides a method to conveniently transfer data between files/media in Java;
    locking: the standard I/O package did not deal with file locking (or, more broadly, concurrent access to parts of a file) explicitly. 

Unforunately, NIO still did not address certain issues, some of which will be resolved in Java 7. For example, Java's support for file attributes and shortcuts or symbolic links is currently poor. And there is currently no Java support for file system notifications, in which an application is notified by the OS of events such as file modifications.

1. You're possibly wondering how to pronounce NIO. All I can tell you is that I've heard Sun employees pronounce it both en-eye-oh and nigh-oh, and I've heard other colleagues pronounce it nee-oh. Pick the one you prefer.


##Buffer

buffer中文名又叫缓冲区，按照维基百科的解释，是”在数据传输时，在内存里开辟的一块临时保存数据的区域”。它其实是一种化同步为异步的机制，可以解决数据传输的速率不对等以及不稳定的问题。

根据这个定义，我们可以知道涉及I/O(特别是I/O写)的地方，基本会有buffer的存在。就Java来说，我们非常熟悉的Old I/O–InputStream&OutputStream系列API，基本都是在内部使用到了buffer。Java课程老师就教过，outputStream.write()只将内容写入了buffer，必须调用outputStream.flush()，才能保证数据写入生效！

而NIO中则直接将buffer这个概念封装成了对象，其中最常用的大概是ByteBuffer了。于是使用方式变为了：将数据写入Buffer，flip()一下，然后将数据读出来。于是，buffer的概念更加深入人心了！

Netty中的buffer也不例外。不同的是，Netty的buffer专为网络通讯而生，所以它又叫ChannelBuffer(好吧其实没有什么因果关系…)。我们下面就来讲讲Netty中的buffer。当然，关于Netty，我们必须讲讲它的所谓”Zero-Copy-Capable”机制。

###When & Where: TCP/IP协议与buffer

TCP/IP协议是目前的主流网络协议。它是一个多层协议，最下层是物理层，最上层是应用层(HTTP协议等)，而在Java开发中，一般只接触TCP以上，即传输层和应用层的内容。这就是Netty的主要应用场景。

TCP报文有个比较大的特点，就是它传输的时候，会先把应用层的数据项拆开成字节，然后按照自己的传输需要，选择合适数量的字节进行传输。什么叫”自己的传输需要”？首先TCP包有最大长度限制，那么太大的数据项肯定是要拆开的。其次因为TCP以及下层协议会附加一些协议头信息，如果数据项太小，那么可能报文大部分都是没有价值的头信息，这样传输是很不划算的。因此有了收集一定数量的小数据，并打包传输的Nagle算法(这个东东在HTTP协议里会很讨厌，Netty里可以用setOption(“tcpNoDelay”, true)关掉它)。

这么说可能太抽象了一点，我们举个例子吧：

发送时，我们这样分3次写入(‘|’表示两个buffer的分隔):

   +-----+-----+-----+
   | ABC | DEF | GHI |
   +-----+-----+-----+

接收时，可能变成了这样:

   +----+-------+---+---+
   | AB | CDEFG | H | I |
   +----+-------+---+---+

很好懂吧？可是，说了这么多，跟buffer有个什么关系呢？别急，我们来看下面一部分。

###Why: buffer中的分层思想

我们先回到之前的`messageReceived`方法：
1	public void messageReceived(
2	        ChannelHandlerContext ctx, MessageEvent e) {
3	    // Send back the received message to the remote peer.
4	    transferredBytes.addAndGet(((ChannelBuffer) e.getMessage()).readableBytes());
5	    e.getChannel().write(e.getMessage());
6	}

这里MessageEvent.getMessage()默认的返回值是一个ChannelBuffer。我们知道，业务中需要的”Message”，其实是一条应用层级别的完整消息，而一般的buffer工作在传输层，与”Message”是不能对应上的。那么这个ChannelBuffer是什么呢？

[ChannelBuffer.png]

这里可以看到，TCP层HTTP报文被分成了两个ChannelBuffer，这两个Buffer对我们上层的逻辑(HTTP处理)是没有意义的。但是两个ChannelBuffer被组合起来，就成为了一个有意义的HTTP报文，这个报文对应的ChannelBuffer，才是能称之为”Message”的东西。这里用到了一个词”Virtual Buffer”，也就是所谓的”Zero-Copy-Capable Byte Buffer”了。是不是顿时觉得豁然开朗了？

我这里总结一下，如果要说NIO的Buffer和Netty的ChannelBuffer最大的区别的话，就是前者仅仅是传输上的Buffer，而后者其实是传输Buffer和抽象后的逻辑Buffer的结合。延伸开来说，NIO仅仅是一个网络传输框架，而Netty是一个网络应用框架，包括网络以及应用的分层结构。

当然，使用ChannelBuffer表示”Message”，不失为一个比较实用的方法，但是使用一个对象来表示解码后的Message可能更符合习惯一点。在Netty里，MessageEvent.getMessage()是可以存放一个POJO的，这样子抽象程度又高了一些，这个我们在以后讲到ChannelPipeline的时候会说到。


###How: Netty中的ChannelBuffer及实现

关于代码阅读，我想可能很多朋友跟我一样，喜欢”顺藤摸瓜”式读代码–找到一个入口，然后顺着查看它的调用，直到理解清楚。很幸运，ChannelBuffers(注意有s!)就是这样一根”藤”，它是所有ChannelBuffer实现类的入口，它提供了很多静态的工具方法来创建不同的Buffer，靠“顺藤摸瓜”式读代码方式，大致能把各种ChannelBuffer的实现类摸个遍。



###Zero-Copy-Capable Rich Byte Buffe






###HeapByteBuffer与DirectByteBuffer


HeapByteBuffer与DirectByteBuffer，在原理上，前者可以看出分配的buffer是在heap区域的，其实真正flush到远程的时候会先拷贝得到直接内存，再做下一步操作（考虑细节还会到OS级别的内核区直接内存），其实发送静态文件最快速的方法是通过OS级别的send_file，只会经过OS一个内核拷贝，而不会来回拷贝；在NIO的框架下，很多框架会采用DirectByteBuffer来操作，这样分配的内存不再是在java heap上，而是在C heap上，经过性能测试，可以得到非常快速的网络交互，在大量的网络交互下，一般速度会比HeapByteBuffer要快速好几倍。

最基本的情况下

分配HeapByteBuffer的方法是：

    ByteBuffer.allocate(int capacity);参数大小为字节的数量

分配DirectByteBuffer的方法是：

	ByteBuffer.allocateDirect(int capacity);
	//可以看到分配内存是通过unsafe.allocateMemory()来实现的，这个unsafe默认情况下java代码是没有能力可以调用到的，不过你可以通过反射的手段得到实例进而做操作，当然你需要保证的是程序的稳定性，既然叫unsafe的，就是告诉你这不是安全的，其实并不是不安全，而是交给程序员来操作，它可能会因为程序员的能力而导致不安全，而并非它本身不安全。  
	
由于HeapByteBuffer和DirectByteBuffer类都是default类型的，所以你无法字节访问到，你只能通过ByteBuffer间接访问到它，因为JVM不想让你访问到它，对了，JVM不想让你访问到它肯定就有它不可告人的秘密；后面我们来跟踪下他的秘密吧。

前面说到了，这块区域不是在java heap上，那么这块内存的大小是多少呢？默认是一般是64M，可以通过参数：-XX:MaxDirectMemorySize来控制，你够牛的话，还可以用代码控制，呵呵，这里就不多说了。

直接内存好，我们为啥不都用直接内存？请注意，这个直接内存的释放并不是由你控制的，而是由full gc来控制的，直接内存会自己检测情况而调用system.gc()，但是如果参数中使用了DisableExplicitGC 那么这是个坑了，所以啊，这玩意，设置不设置都是一个坑坑，所以java的优化有没有绝对的，只有针对实际情况的，针对实际情况需要对系统做一些拆分做不同的优化。

那么full gc不触发，我想自己释放这部分内存有方法吗？可以的，在这里没有什么是不可以的，呵呵！私有属性我们都任意玩他，还有什么不可以玩的；我们看看它的源码中DirectByteBuffer发现有一个：Cleaner，貌似是用来搞资源回收的，经过查证，的确是，而且又看到这个对象是sun.misc开头的了，此时既惊喜又郁闷，呵呵，只要我能拿到它，我就能有希望消灭掉了；下面第五步我们来做个试验。


因为我们的代码全是私有的，所以我要访问它不能直接访问，我需要通过反射来实现，OK，我知道要调用cleaner()方法来获取它Cleaner对象，进而通过该对象，执行clean方法；（付：以下代码大部分也取自网络上的一篇copy无数次的代码，但是那个代码是有问题的，有问题的部分，我将用红色标识出来，如果没有哪条代码是无法运行的）





    import java.nio.ByteBuffer;  
    import sun.nio.ch.DirectBuffer;  
      
    public class DirectByteBufferCleaner {  
      
            public static void clean(final ByteBuffer byteBuffer) {  
                  if (byteBuffer.isDirect()) {  
                     ((DirectBuffer)byteBuffer).cleaner().clean();  
                  }  
            }  
    }
   
我们下面来做测试来证明这个程序是有效地回收的：

在任意一个地方写一段main方法来调用，我这里就直接写在这个类里面了：

    public static void sleep(long i) {  
        try {  
              Thread.sleep(i);  
         }catch(Exception e) {  
              /*skip*/  
         }  
    }  
    public static void main(String []args) throws Exception {  
           ByteBuffer buffer = ByteBuffer.allocateDirect(1024 * 1024 * 100);  
           System.out.println("start");  
           sleep(10000);  
           clean(buffer);  
           System.out.println("end");  
           sleep(10000);  
    }  
  
这里分配了100M内存，为了将结果看清楚，在执行前，执行后分别看看延迟10s，当然你可以根据你的要求自己改改。用 Top 查看内存变化。




参考
http://netty.io/3.8/guide/
http://ifeve.com/netty-2-buffer/
http://my.oschina.net/ielts0909/blog?catalog=201987
