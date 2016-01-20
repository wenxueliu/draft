

###event

接口定义在 core/api/src/main/java/org/onosproject/event/

默认实现在 core/net/src/main/java/org/onosproject/event/impl/CoreEventDispatcher.java
           core/api/src/main/java/org/onosproject/event/impl/ListenerRegistry.java


public void addListener(L listener)
public void removeListener(L listener)
public void process(E event)
public void onProcessLimit()


//开始(结束)事件处理
public void deactivate()
public void activate()

//设置事件最大处理时间
public void setDispatchTimeLimit(long millis)
public long getDispatchTimeLimit()

//单独的线程监控处理时间
watchDog

通过阅读以下模块代码可以理解 Event 的处理机制

###Device

这里的设备可以是很多类型, 路由器, 交换机等等

接口定义在 core/api/src/main/java/org/onosproject/net/device
默认实现在 core/net/src/main/java/org/onosproject/net/impl/

###Host

接口定义在 core/api/src/main/java/org/onosproject/net/host
默认实现在 core/net/src/main/java/org/onosproject/net/impl/

###Packet

接口定义在 core/api/src/main/java/org/onosproject/net/packet
默认实现在 core/net/src/main/java/org/onosproject/net/impl/

###Provider

接口定义在 core/api/src/main/java/org/onosproject/net/provider
默认实现在 core/net/src/main/java/org/onosproject/net/impl/

-------------------------------------------------------------------------

###app

接口定义在 core/api/src/main/java/org/onosproject/app
默认实现在 core/net/src/main/java/org/onosproject/
