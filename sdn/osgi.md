 opendaylight Hydrogen app 开发指南 
========================================
**作者** 

刘文学

**版本及修订**

0.1 完成初始化

**预备条件**

自定义一个 app
=======================

$ cd ~/opendaylight-hydrogen/controller/opendaylight

$ mvn archetype:generate -DgroupId=com.example -DartifactId=mystats -DarchetypeArtifactId=maven-archetype-quickstart -Dpackage=com.example.mystats -DinteractiveMode=false

		[INFO] Scanning for projects...
		[INFO]                                                                         
		[INFO] ------------------------------------------------------------------------
		[INFO] Building Maven Stub Project (No POM) 1
		[INFO] ------------------------------------------------------------------------
		[INFO] 
		[INFO] >>> maven-archetype-plugin:2.2:generate (default-cli) @ standalone-pom >>>
		[INFO] 
		[INFO] <<< maven-archetype-plugin:2.2:generate (default-cli) @ standalone-pom <<<
		[INFO] 
		[INFO] --- maven-archetype-plugin:2.2:generate (default-cli) @ standalone-pom ---
		[INFO] Generating project in Batch mode
		[INFO] ----------------------------------------------------------------------------
		[INFO] Using following parameters for creating project from Old (1.x) Archetype: maven-archetype-quickstart:1.0
		[INFO] ----------------------------------------------------------------------------
		[INFO] Parameter: groupId, Value: com.example
		[INFO] Parameter: packageName, Value: com.example.mystats
		[INFO] Parameter: package, Value: com.example.mystats
		[INFO] Parameter: artifactId, Value: mystats
		[INFO] Parameter: basedir, Value: /home/vagrant/opendaylight-hydrogen/controller/opendaylight
		[INFO] Parameter: version, Value: 1.0-SNAPSHOT
		[INFO] project created from Old (1.x) Archetype in dir: /home/vagrant/opendaylight-hydrogen/controller/opendaylight/mystats
		[INFO] ------------------------------------------------------------------------
		[INFO] BUILD SUCCESS
		[INFO] ------------------------------------------------------------------------
		[INFO] Total time: 21.407s
		[INFO] Finished at: Tue Oct 21 08:21:31 UTC 2014
		[INFO] Final Memory: 15M/111M
		[INFO] ------------------------------------------------------------------------


$tree mystats

		mystats/
		|-- pom.xml
		`-- src
			|-- main
			|   `-- java
			|       `-- com
			|           `-- example
			|               `-- mystats
			|                   `-- App.java
			`-- test
				`-- java
				    `-- com
				        `-- example
				            `-- mystats
				                `-- AppTest.java

$ vim mystats/pom.xml

		<?xml version="1.0" encoding="UTF-8"?>
		<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">
		  <modelVersion>4.0.0</modelVersion>
		  <parent>
			<groupId>org.opendaylight.controller</groupId>
			<artifactId>commons.opendaylight</artifactId>
			<version>1.4.1-1-SNAPSHOT</version>
			<relativePath>../commons/opendaylight</relativePath>
		  </parent>
		  <artifactId>mystats</artifactId>
		  <version>0.1-SNAPSHOT</version>
		  <packaging>bundle</packaging>
		  <dependencies>
			<dependency>
			  <groupId>org.opendaylight.controller</groupId>
			  <artifactId>sal</artifactId>
			</dependency>
			<dependency>
			  <groupId>org.opendaylight.controller</groupId>
			  <artifactId>statisticsmanager</artifactId>
			</dependency>
			<dependency>
			  <groupId>junit</groupId>
			  <artifactId>junit</artifactId>
			  <version>3.8.1</version>
			  <scope>test</scope>
			</dependency>
		  </dependencies>
		  <build>
			<plugins>
			  <plugin>
				<groupId>org.apache.felix</groupId>
				<artifactId>maven-bundle-plugin</artifactId>
				<version>${bundle.plugin.version}</version>
				<extensions>true</extensions>
				<configuration>
				  <instructions>
				    <Import-Package>org.opendaylight.controller.sal.core,
				                    org.opendaylight.controller.statisticsmanager,
				                    org.opendaylight.controller.switchmanager,
				                    org.opendaylight.controller.sal.utils,
				                    org.opendaylight.controller.sal.reader,
				                    org.opendaylight.controller.sal.flowprogrammer,
				                    org.opendaylight.controller.sal.match,
				                    org.slf4j,
				                    org.apache.felix.dm</Import-Package>
				    <Bundle-Activator>org.opendaylight.controller.mystats.Activator</Bundle-Activator>
				    <Export-Package>com.example.mystats</Export-Package>
				  </instructions>
				</configuration>
			  </plugin>
			</plugins>
		  </build>
		</project>


$ vim mystats/src/main/java/com/example/mystats/MyStats.java

		package com.example.mystats;

		import org.opendaylight.controller.sal.core.Node;
		import org.opendaylight.controller.sal.match.MatchType;
		import org.opendaylight.controller.sal.reader.FlowOnNode;
		import org.opendaylight.controller.sal.utils.ServiceHelper;
		import org.opendaylight.controller.statisticsmanager.IStatisticsManager;
		import org.opendaylight.controller.switchmanager.ISwitchManager;
		import org.slf4j.Logger;
		import org.slf4j.LoggerFactory;

		/**
		* Simple bundle to grab some statistics
		* Fred Hsu
		*/
		public class MyStats{
				private static final Logger log = LoggerFactory.getLogger(MyStats.class);

				public MyStats() {

				}

				void init() {
				        log.debug("INIT called!");
				}

				void destroy() {
				        log.debug("DESTROY called!");
				}

				void start() {
				        log.debug("START called!");
				        getFlowStatistics();
				}

				void stop() {
				        log.debug("STOP called!");
				}

				void getFlowStatistics() {
                String containerName = "default";
                IStatisticsManager statsManager = (IStatisticsManager) ServiceHelper
                                        .getInstance(IStatisticsManager.class, containerName, this);

                ISwitchManager switchManager = (ISwitchManager) ServiceHelper
                                        .getInstance(ISwitchManager.class, containerName, this);

				        for (Node node : switchManager.getNodes()) {
				                System.out.println("Node: " + node);
				                for (FlowOnNode flow : statsManager.getFlows(node)) {
				                        System.out.println(" DST: "
				                                        + flow.getFlow().getMatch().getField(MatchType.NW_DST)
				                                        + " Bytes: " + flow.getByteCount());
				                }
				        }
				}
		}

$ vim mystats/src/main/java/com/example/mystats/Activator.java

		package com.example.mystats;
		 
		 
		import org.apache.felix.dm.Component;
		import org.opendaylight.controller.sal.core.ComponentActivatorAbstractBase;
		import org.slf4j.Logger;
		import org.slf4j.LoggerFactory;
		 
		public class Activator extends ComponentActivatorAbstractBase {
				protected static final Logger logger = LoggerFactory
				.getLogger(Activator.class);
		 
				public void init() {
				}
		 
				public void destroy() {
				}
		 
				public Object[] getImplementations() {
				        Object[] res = { MyStats.class };
				        return res;
				}
		 
				public void configureInstance(Component c, Object imp, String containerName) {
				        if (imp.equals(MyStats.class)) {
				        // export the service
				        c.setInterface(new String[] { MyStats.class.getName() },
				                        null);
		 
				        }
				}
		}

注意代码风格，文件中不许出现，tab 键，行末不能出现空格。如果出现checkstyle 错误，请确认没有包含tab和 行末没有出现 空格

ComponentActivatorAbstractBase to mange the life-cycle of an OpenDaylight component. From there, the two methods getImplementations() and configureInstance() are called.

The method getImplementations() returns the classes implementing components of this bundle. A bundle can implement more than one component

Method configureInstance() configures the component and, in particular, declares exported service interfaces and the services used. Since an OSGi bundle can implement more than one component, it is good style to check, which component should be configured in line 26.


$ cd mystats

$ mvn clean install



切换到 osgi 运行的窗口

* 安装 app

	osgi> install flie:/home/vagrant/opendaylight-hydrogen/controller/opendaylight/mystats/target/mystats-0.1-SNAPSHOT.jar

* 开始 app 

	osgi> start 258
	Node: OF|00:00:00:00:00:00:00:02
	Node: OF|00:00:00:00:00:00:00:03
	Node: OF|00:00:00:00:00:00:00:01
	Node: OF|00:00:00:00:00:00:00:04
	Node: OF|00:00:00:00:00:00:00:07
	Node: OF|00:00:00:00:00:00:00:06
	Node: OF|00:00:00:00:00:00:00:05

日志设置
============================

* 确认 app 在运行

	osgi> ss | grep mystats
		258     ACTIVE      org.opendaylight.controller.mystats_0.1.0.SNAPSHOT
		true

* 搜索 app 日志级别


	osgi> getloglevel | grep mystats
		Logger org.opendaylight.controller.mystats at unknown level
		Logger org.opendaylight.controller.mystats.Activator at unknown level
		Logger org.opendaylight.controller.mystats.MyStats at unknown level

* 设置 app 日志级别

	osgi> setLogLevel org.opendaylight.controller.mystats debug

* 查看结果
 
  将会记录日志到 opendaylight.log 文件

	 ~/opendaylight-hydrogen/controller/opendaylight/distribution/opendaylight/target/distribution.opendaylight-0.1.0-osgipackage/opendaylight/logs/opendaylight.log


更新bundle
======================

以 mystats 为例

* 查找 mystats
	
	osgi> ss | grep mystats
	258     ACTIVE      org.opendaylight.controller.mystats_0.1.0.SNAPSHOT

* 停止 arphandler
	
	osgi> stop 258

* 切换到arphandler 目录

	cd ~/controller/opendaylight/mystats

* 修改后编译：	
	
	mvn clean install
	
* 拷贝到版本目录

cp target/arphandler-0.1-SNAPSHOT.jar ../distribution/opendaylight/target/distribution.opendaylight-0.1.0-SNAPSHOT-osgipackage/opendaylight/plugins/

* 更新 arphandler

	osgi> update 258

osgi 命令

	pns - print nodes
	ss - lists bundles
	start - start bundle
	stop - stop bundle
	getLogLevel <bundle>
	setLogLevel org.opendaylight.controller.helloworld DEBUG (sets level to DEBUG for helloworld module)
	dm - dependencies for a module

bundle:install  mvn:org.apache.camel/camel-example-osgi/2.7.0/xml/features
features:addurl mvn:org.apache.camel/camel-example-osgi/2.7.0/xml/features
features:install camel-example-osgi


2014-10-29 08:29:11.512 UTC [SwitchEvent Thread] TRACE d.frank_durr.myctrlapp.PacketHandler - Packet from 00:00:00:00:00:00:00:01 3
2014-10-29 08:29:11.513 UTC [SwitchEvent Thread] INFO  d.frank_durr.myctrlapp.PacketHandler - Received packet for load balanced service
2014-10-29 08:29:11.513 UTC [SwitchEvent Thread] INFO  d.frank_durr.myctrlapp.PacketHandler - Server 2 is serving the request
2014-10-29 08:29:11.549 UTC [SwitchEvent Thread] TRACE d.frank_durr.myctrlapp.PacketHandler - Forwarding packet to /10.0.0.2 through port 2


原理解析

* [java  reflection]
* [org.apache.felix 插件]http://felix.apache.org/documentation/subprojects/apache-felix-dependency-manager.html
* [BundleActivator](http://www.osgi.org/javadoc/r4v43/core/org/osgi/framework/BundleActivator.html)
* [BundleContext](http://www.osgi.org/javadoc/r4v43/core/org/osgi/framework/BundleContext.html)

###DependencyManager

[DependencyManager](https://apache.googlesource.com/felix/+/fe742c0d90e1aa79da5fb5057a288120f506aa26/dependencymanager/core/src/main/java/org/apache/felix/dm/DependencyManager.java)

	/**
	* The dependency manager manages all components and their dependencies. Using
	* this API you can declare all components and their dependencies. Under normal
	* circumstances, you get passed an instance of this class through the
	* <code>DependencyActivatorBase</code> subclass you use as your
	* <code>BundleActivator</code>, but it is also possible to create your
	* own instance.
	*
	* @author <a href="mailto:dev@felix.apache.org">Felix Project Team</a>
	*/
	public class DependencyManager {
		public static final String ASPECT = "org.apache.felix.dependencymanager.aspect";
		public static final String SERVICEREGISTRY_CACHE_INDICES = "org.apache.felix.dependencymanager.filterindex";
		public static final String METHOD_CACHE_SIZE = "org.apache.felix.dependencymanager.methodcache";
		private final BundleContext m_context;
		private final Logger m_logger;
		private List m_components = Collections.synchronizedList(new ArrayList());

	/**
	* Adds a new service to the dependency manager. After the service was added
	* it will be started immediately.
	*
	* @param service the service to add
	*/
	public void add(Component service) {
		m_components.add(service);
		service.start();
	}

	 /**
	* Removes a service from the dependency manager. Before the service is removed
	* it is stopped first.
	*
	* @param service the service to remove
	*/
	public void remove(Component service) {
		service.stop();
		m_components.remove(service);
	}

	/**
	* Creates a new service.
	*
	* @return the new service
	*/
	public Component createComponent() {
		return new ComponentImpl(m_context, this, m_logger);
	}


###ComponentStateListener

 [ComponentStateListener](https://apache.googlesource.com/felix/+/fe742c0d90e1aa79da5fb5057a288120f506aa26/dependencymanager/core/src/main/java/org/apache/felix/dm/ComponentStateListener.java)

	/**
	* This interface can be used to register a component state listener. Component
	* state listeners are called whenever a component state changes. You get notified
	* when the component is starting, started, stopping and stopped. Each callback
	* includes a reference to the component in question.
	*
	* @author <a href="mailto:dev@felix.apache.org">Felix Project Team</a>
	*/
	public interface ComponentStateListener {
	/**
	* Called when the component is starting. At this point, the required
	* dependencies have been injected, but the service has not been registered
	* yet.
	*
	* @param component the component
	*/
	public void starting(Component component);
	/**
	* Called when the component is started. At this point, the component has been
	* registered.
	*
	* @param component the component
	*/
	public void started(Component component);
	/**
	* Called when the component is stopping. At this point, the component is still
	* registered.
	*
	* @param component the component
	*/
	public void stopping(Component component);
	/**
	* Called when the component is stopped. At this point, the component has been
	* unregistered.
	*
	* @param component the component
	*/
	public void stopped(Component component);
	}

###Component

[Component interface](https://apache.googlesource.com/felix/+/fe742c0d90e1aa79da5fb5057a288120f506aa26/dependencymanager/core/src/main/java/org/apache/felix/dm/Component.java). Components are the main building blocks for OSGi applications. They can publish themselves as a service, and they can have dependencies. These dependencies will influence their life cycle as component will only be activated when all required dependencies are available. 

	/**
	* Adds a new dependency to this component.
	*
	* @param dependency the dependency to add
	* @return this component
	*/
	public Component add(Dependency dependency);

	/**
	* Adds a list of new dependencies to this component.
	*
	* @param dependencies the dependencies to add
	* @return this component
	*/
	public Component add(List dependencies);

	/**
	* Sets the public interfaces under which this component should be registered
	* in the OSGi service registry.
	*
	* @param serviceNames the names of the service interface
	* @param properties the properties for these services
	* @return this component
	*/
	public Component setInterface(String[] serviceNames, Dictionary properties);

	/**
	* Sets the implementation for this component. You can actually specify
	* an instance you have instantiated manually, or a <code>Class</code>
	* that will be instantiated using its default constructor when the
	* required dependencies are resolved, effectively giving you a lazy
	* instantiation mechanism.
	*
	* There are four special methods that are called when found through
	* reflection to give you life cycle management options:
	* <ol>
	* <li><code>init()</code> is invoked after the instance has been
	* created and dependencies have been resolved, and can be used to
	* initialize the internal state of the instance or even to add more
	* dependencies based on runtime state</li>
	* <li><code>start()</code> is invoked right before the service is
	* registered</li>
	* <li><code>stop()</code> is invoked right after the service is
	* unregistered</li>
	* <li><code>destroy()</code> is invoked after all dependencies are
	* removed</li>
	* </ol>
	* In short, this allows you to initialize your instance before it is
	* registered, perform some post-initialization and pre-destruction code
	* as well as final cleanup. If a method is not defined, it simply is not
	* called, so you can decide which one(s) you need. If you need even more
	* fine-grained control, you can register as a service state listener too.
	*
	* @param implementation the implementation
	* @return this component
	* @see ComponentStateListener
	*/
	public Component setImplementation(Object implementation);
	
	
	/**
	* Sets the service properties associated with the component. If the service
	* was already registered, it will be updated.
	*
	* @param serviceProperties the properties
	*/
	public Component setServiceProperties(Dictionary serviceProperties);


	/**
	* Adds a component state listener to this component.
	*
	* @param listener the state listener
	*/
	public void addStateListener(ComponentStateListener listener);


	/**
	* Invokes a callback method on an array of instances. The method, whose name
	* and signatures you provide, along with the values for the parameters, is
	* invoked on all the instances where it exists.
	*
	* @see InvocationUtil#invokeCallbackMethod(Object, String, Class[][], Object[][])
	*
	* @param instances an array of instances to invoke the method on
	* @param methodName the name of the method
	* @param signatures the signatures of the method
	* @param parameters the parameter values
	*/
	public void invokeCallbackMethod(Object[] instances, String methodName, Class[][] signatures, Object[][] parameters);


###参考

http://fredhsu.wordpress.com/2013/05/14/odl-maven-osgi/
http://networkstatic.net/opendaylight-maven-and-osgi-dev-notes/
http://sdntutorials.com/hello-world-application-using-osgi-bundle/
http://www.frank-durr.de/?p=84
https://fredhsu.wordpress.com/2013/07/11/handling-packets-on-the-opendaylight-controller/
[loadbalance app example](http://www.frank-durr.de/?p=126) 
[hydrogen 负载均衡测试](https://wiki.opendaylight.org/view/OpenDaylight_Controller:Load_Balancer_Service)
[MD-SAL](https://github.com/opendaylight/docs/blob/master/manuals/developers-guide/src/main/asciidoc/controller.adoc)
