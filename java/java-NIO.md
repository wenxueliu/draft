

首先 git clone githu



http://www.coderli.com/netty-course-hello-world
http://seeallhearall.blogspot.com/2012/05/netty-tutorial-part-1-introduction-to.html

确保你已经阅读这个 guide http://netty.io/3.8/guide/  或 http://docs.jboss.org/netty/3.2/guide/html/start.html

##基础知识

TCP, UDP 基本知识。

java 基本语法及知识

##Netty 原理分析

首先我们看 netty 包的组成, 在[官方文档](http://netty.io/3.10/api/index.html)中的左上角, 我们可以看到 netty 包的组成

    org.jboss.netty.bootstrap
    org.jboss.netty.buffer
    org.jboss.netty.channel
    org.jboss.netty.handler
    org.jboss.netty.logging
    org.jboss.netty.util

这六大类, 因此, 基本的概念就是 bootstrap, channel, buffer, handler. logging 忽略不计, util 是工具类.

###模型

Factory 创建对象的辅助类

###bootstrap

org.jboss.netty.bootstrap 包括: Bootstrap, ClientBootstrap, ConnectionlessBootstrap, ServerBootstrap 非常直观.

再看看各个类的说明

####Bootstrap

A helper class which initializes a Channel. This class provides the common data structure for its subclasses which actually
initialize Channels and their child Channels using the common data structure. Please refer to ClientBootstrap, ServerBootstrap,
and ConnectionlessBootstrap for client side, server-side, and connectionless (e.g. UDP) channel initialization respectively.

####ClientBootstrap

A helper class which creates a new client-side Channel and makes a connection attempt.

####ConnectionlessBootstrap

A helper class which creates a new server-side Channel for a connectionless transport.

####ServerBootstrap

A helper class which creates a new server-side Channel and accepts incoming connections.

至此, 它们之间的关系已经很明了. Bootstrap 首先是 Channel 的辅助函数, 实现了 ClientBootstrap, ConnectionlessBootstrap, ServerBootstrap 的公共部分.
其中 ClientBootstrap 用于实现面向连接(TCP)的客户端, ServerBootstrap 用于实现面向连接(TCP)的服务端 ConnectionlessBootstrap 用于实现无连接(UDP)
的客户端或服务端.

分析 Bootstrap 发现它与 ChannelFactory, ChannelPipeline, ChannelPipelineFactory
有关, 与 Channel 的关系后文再表.

此外, 这里通过继承而不是组合来实现, 我们可以思考下, 在其他语言中是否也应该这样做.


##channel

服务端和客户端的每一个连接就是一个 channel, 传输的内容是二进制流. 主要分为三种类或接口, 1. 创建 channel  2. 处理 channel 数据. 3 配置 channel

###创建 channel 的接口及类

####Channel

A nexus to a network socket or a component which is capable of I/O operations such as read, write, connect, and bind. 

A channel provides a user:

* the current state of the channel (e.g. is it open? is it connected?),
* the configuration parameters of the channel (e.g. receive buffer size),
* the I/O operations that the channel supports (e.g. read, write, connect, and bind), and
* the ChannelPipeline which handles all I/O events and requests associated with the channel.

子接口

    DatagramChannel             //Channel
    LocalChannel                //Channel
    ServerChannel               //Channel
    LocalServerChannel          //ServerChannel
    ServerSocketChannel         //ServerChannel
    SocketChannel               //Channel

框架实现的类

    AbstractChannel             //Channel
        AbstractServerChannel   //ServerChannel
        NioDatagramChannel      //DatagramChannel
        NioSocketChannel        //SocketChannel

与 ChannelFuture 和 ChannelConfig 关联

####ChannelFactory

用户创建 channel 的辅助类

The main interface to a transport that creates a Channel associated with a certain communication entity such as a network socket.

子接口

    ClientSocketChannelFactory                 //ChannelFactory
    DatagramChannelFactory                     //ChannelFactory
    LocalClientChannelFactory                  //ChannelFactory
    LocalServerChannelFactory                  //ServerChannelFactory
    ServerChannelFactory                       //ChannelFactory
    ServerSocketChannelFactory                 //ServerChannelFactory

框架默认的实现类

    DefaultLocalClientChannelFactory           //LocalClientChannelFactory
    DefaultLocalServerChannelFactory           //LocalServerChannelFactory
    NioDatagramChannelFactory                  //DatagramChannelFactory
    NioServerSocketChannelFactory              //ServerSocketChannelFactory
    OioServerSocketChannelFactory              //ServerSocketChannelFactory
    HttpTunnelingClientSocketChannelFactory    //ClientSocketChannelFactory
    NioClientSocketChannelFactory              //ClientSocketChannelFactory
    OioClientSocketChannelFactory              //ClientSocketChannelFactory
    OioDatagramChannelFactory                  //DatagramChannelFactory

当需要实现自己的 Channel 时, 根据需要继承 ChannelFactory 或 其子接口

###处理 channle 事件的接口及类

####ChannelPipeline

A list of ChannelHandlers which handles or intercepts ChannelEvents of a Channel. ChannelPipeline implements an advanced form of the Intercepting
Filter pattern to give a user full control over how an event is handled and how the ChannelHandlers in the pipeline interact with each other.

For each new channel, a new pipeline must be created and attached to the channel. Once attached, the coupling between the channel and the pipeline
is permanent; the channel cannot attach another pipeline to it nor detach the current pipeline from it.

1. 创建, 增加, 删除,替换 ChannelHandler
2. 加入 Channel, 获取所属 Channel
3. 加入 ChannelSink, 获取所属 ChannelSink
4. 加入 ChannelHandlerContext, 获取所属 ChannelHandlerContext
5. 发送 ChannelEvent 给 UpstreamHandler, 或 DownstreamHandler

                                           I/O Request
                                         via Channel or
                                     ChannelHandlerContext
                                               |
      +----------------------------------------+---------------+
      |                  ChannelPipeline       |               |
      |                                       \|/              |
      |  +----------------------+  +-----------+------------+  |
      |  | Upstream Handler  N  |  | Downstream Handler  1  |  |
      |  +----------+-----------+  +-----------+------------+  |
      |            /|\                         |               |
      |             |                         \|/              |
      |  +----------+-----------+  +-----------+------------+  |
      |  | Upstream Handler N-1 |  | Downstream Handler  2  |  |
      |  +----------+-----------+  +-----------+------------+  |
      |            /|\                         .               |
      |             .                          .               |
      |     [ sendUpstream() ]        [ sendDownstream() ]     |
      |     [ + INBOUND data ]        [ + OUTBOUND data  ]     |
      |             .                          .               |
      |             .                         \|/              |
      |  +----------+-----------+  +-----------+------------+  |
      |  | Upstream Handler  2  |  | Downstream Handler M-1 |  |
      |  +----------+-----------+  +-----------+------------+  |
      |            /|\                         |               |
      |             |                         \|/              |
      |  +----------+-----------+  +-----------+------------+  |
      |  | Upstream Handler  1  |  | Downstream Handler  M  |  |
      |  +----------+-----------+  +-----------+------------+  |
      |            /|\                         |               |
      +-------------+--------------------------+---------------+
                    |                         \|/
      +-------------+--------------------------+---------------+
      |             |                          |               |
      |     [ Socket.read() ]          [ Socket.write() ]      |
      |                                                        |
      |  Netty Internal I/O Threads (Transport Implementation) |
      +--------------------------------------------------------+

An upstream event is handled by the upstream handlers in the bottom-up direction as shown on the left side of the diagram.
An upstream handler usually handles the inbound data generated by the I/O thread on the bottom of the diagram. The inbound
data is often **read from a remote peer** via the actual input operation such as InputStream.read(byte[]). If an upstream
event goes beyond the top upstream handler, it is discarded silently.

A downstream event is handled by the downstream handler in the top-down direction as shown on the right side of the diagram.
A downstream handler usually generates or transforms the outbound traffic such as write requests. If a downstream event goes
beyond the bottom downstream handler, it is handled by an I/O thread associated with the Channel. The I/O thread often performs
the actual output operation such as OutputStream.write(byte[]).



框架默认的实现类

    DefaultChannelPipeline //ChannelPipeline

与 ChannelHandler, ChannelHandlerContext, Channel, ChannelSink 关联

####ChannelPipelineFactory

Creates a new ChannelPipeline for a new Channel.

When a server-side channel accepts a new incoming connection, a new child channel is created for each newly accepted connection.
A new child channel uses a new ChannelPipeline, which is created by the ChannelPipelineFactory specified in the server-side channel's
"pipelineFactory" option.


####Channels

A helper class which provides various convenience methods related with Channel, ChannelHandler, and ChannelPipeline.

It is always recommended to use the factory methods provided by Channels rather than calling the constructor of the implementation types.

    pipeline()
    pipeline(ChannelPipeline)
    pipelineFactory(ChannelPipeline)
    succeededFuture(Channel)
    failedFuture(Channel, Throwable)

####ChannelEvent

An I/O event or I/O request associated with a Channel.

A ChannelEvent is handled by a series of ChannelHandlers in a ChannelPipeline.

子接口

    ChannelStateEvent           //ChannelEvent

框架默认的实现类

    DownstreamChannelStateEvent //ChannelStateEvent
    UpstreamChannelStateEvent   //ChannelStateEvent

**upstream Event**

When your server receives a message from a client, the event associated with the received message is an upstream event. When
your server sends a message or reply to the client, the event associated with the write request is a downstream event.

**downstream Event**

If your client sent a request to the server, it means your client triggered a downstream event. If your client received a response
from the server, it means your client will be notified with an upstream event.

即写为 downstream, 读为 upstream

**Upstream events**

    Event name	            Event type and condition	                            Meaning
    messageReceived 	        MessageEvent 	                a message object (e.g. ChannelBuffer) was received from a remote peer
    exceptionCaught 	        ExceptionEvent 	                an exception was raised by an I/O thread or a ChannelHandler
    channelOpen 	            ChannelStateEvent         	    a Channel is open, but not bound nor connected
    channelClosed   	        ChannelStateEvent               a Channel was closed and all its related resources were released
    channelBound   	            ChannelStateEvent               a Channel is open and bound to a local address, but not connected.
    channelUnbound 	            ChannelStateEvent               a Channel was unbound from the current local address
    channelConnected            ChannelStateEvent               a Channel is open, bound to a local address, and connected to a remote address
    writeComplete               WriteCompletionEvent            something has been written to a remote peer
    channelDisconnected         ChannelStateEvent               a Channel was disconnected from its remote peer
    channelInterestChanged      ChannelStateEvent               a Channel's interestOps was changed

    childChannelOpen            ChildChannelStateEvent          a child Channel was open (e.g. a server channel accepted a connection.)
    childChannelClosed          ChildChannelStateEvent          a child Channel was closed (e.g. the accepted connection was closed.)

**downstream events**

    Event name	            Event type and condition	                            Meaning
    write                       MessageEvent	                    Send a message to the Channel.
    bind 	                    ChannelStateEvent                   Bind the Channel to the specified local address.
    unbind 	                    ChannelStateEvent                   Unbind the Channel from the current local address.
    connect                     ChannelStateEvent                   Connect the Channel to the specified remote address.
    disconnect                  ChannelStateEvent                   Disconnect the Channel from the current remote address.
    close                       ChannelStateEvent                   Close the Channel.


####ChannelHandler

Handles or intercepts a ChannelEvent, and sends a ChannelEvent to the next handler in a ChannelPipeline.

A ChannelHandler is provided with a ChannelHandlerContext object. A ChannelHandler is supposed to interact with the ChannelPipeline it
belongs to via a context object. Using the context object, the ChannelHandler can pass events upstream or downstream, modify the pipeline
dynamically, or store the information (attachment) which is specific to the handler.

**Because the handler instance has a state variable which is dedicated to one connection, you have to create a new handler instance for each
new channel to avoid a race condition where a unauthenticated client can get the confidential information**

1. 与 ChannelPipeline 的交互通过 ChannelHandlerContext 来实现
2. 发送 ChannelEvent 给下一个 ChannelHandler(UpstreamHandler 或 DownstreamHandler)
3. 在 ChannelHandler 加入之前或之后做预处理或善后工作

子接口

    ChannelDownstreamHandler
    ChannelUpstreamHandler
    LifeCycleAwareChannelHandler

框架默认的实现类

    SimpleChannelUpstreamHandler      //ChannelUpstreamHandler
    IdleStateHandler
    IdleStateHandler

    SimpleChannelDownstreamHandler
    HttpClientCodec
    HttpContentCompressor
    HttpContentEncoder,
    HttpMessageEncoder
    HttpRequestEncoder
    HttpResponseEncoder
    HttpServerCodec
    IdleStateAwareChannelHandler
    OneToOneEncoder

    SimpleChannelHandler

    BufferedWriteHandler //LifeCycleAwareChannelHandler
    HttpContentCompressor
    HttpContentDecoder
    HttpContentDecompressor
    HttpContentEncoder
    HttpMessageDecoder
    HttpRequestDecoder
    HttpResponseDecoder
    IdleStateHandler


####ChannelHandlerContext

Enables a ChannelHandler to interact with its ChannelPipeline and other handlers. A handler can send a
ChannelEvent upstream or downstream, modify the ChannelPipeline it belongs to dynamically.

Please note that a ChannelHandler instance can be added to more than one ChannelPipeline. It means a single
ChannelHandler instance can have more than one ChannelHandlerContext and therefore the single instance can
be invoked with different ChannelHandlerContexts if it is added to one or more ChannelPipelines more than once.

1. 获取所属 channel, channelhandler, channelpipeline
2. 发送 downstream, upstream 事件
3. 存储状态信息


####ChannelFuture

The result of an asynchronous Channel I/O operation.

All I/O operations in Netty are asynchronous. It means any I/O calls will return immediately with no guarantee
that the requested I/O operation has been completed at the end of the call. Instead, you will be returned with
a ChannelFuture instance which gives you the information about the result or status of the I/O operation.

A ChannelFuture is either uncompleted or completed. When an I/O operation begins, a new future object is created.
The new future is uncompleted initially - it is neither succeeded, failed, nor cancelled because the I/O operation
is not finished yet. If the I/O operation is finished either successfully, with failure, or by cancellation, the
future is marked as completed with more specific information, such as the cause of the failure. Please note that
even failure and cancellation belong to the completed state.

                                         +---------------------------+
                                         | Completed successfully    |
                                         +---------------------------+
                                    +---->      isDone() = true      |
    +--------------------------+    |    |   isSuccess() = true      |
    |        Uncompleted       |    |    +===========================+
    +--------------------------+    |    | Completed with failure    |
    |      isDone() = false    |    |    +---------------------------+
    |   isSuccess() = false    |----+---->   isDone() = true         |
    | isCancelled() = false    |    |    | getCause() = non-null     |
    |    getCause() = null     |    |    +===========================+
    +--------------------------+    |    | Completed by cancellation |
                                    |    +---------------------------+
                                    +---->      isDone() = true      |
                                         | isCancelled() = true      |
                                         +---------------------------+




* TCP NIO Channels: NioClientSocketChannelFactory and NioServerSocketChannelFactory
* UDP NIO Channels: NioDatagramChannelFactory
* TCP OIO Channels: OioClientSocketChannelFactory and OioServerSocketChannelFactory
* UDP OIO Channels: OioDatagramChannelFactory
* HTTP Client:  HttpTunnelingClientSocketChannelFactory
* Local Channels: DefaultLocalClientChannelFactory and DefaultLocalServerChannelFactory


每到一个新的连接到达, 就创建一个 channel, ChannelPipeline 附着与 channel, 处理从 channel 进来或出去的数据.

ChannelPipelineFactory 用于创建一个 ChannelPipeline. ChannelPipeline 由一系列
ChannelHandler 按照顺序组成, 不同的 ChannelEvent 对应不同的 ChannelHandler



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

NIO 仅仅是一个网络传输框架，而Netty是一个网络应用框架，包括网络以及应用的分层结构。

Netty3.x 包名为 org.jboss.netty, 是 JBoss.org 的一部分
Netty4.0 包名从 org.jboss.netty 改为 io.netty，不在是 JBoss.org 的一部分了. 具体变化参考[这里](http://www.oschina.net/translate/netty-4-0-new-and-noteworthy?print)

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
