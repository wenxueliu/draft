
Ceki Gülcü在Java日志领域世界知名。他创造了Log4J，这个最早的Java日志框架即便在JRE
内置日志功能的竞争下仍然非常流行。随后他又着手实现SLF4J 这个“简单的日志前端接口
（Fade）”来替代Jakarta Commons-Logging 。

LOGBack，一个“可靠、通用、快速而又灵活的Java日志框架”。

###Commons-logging

apache最早提供的日志的门面接口。避免和具体的日志方案直接耦合。类似于JDBC 的api
接口，具体的的JDBC driver
实现由各数据库提供商实现。通过统一接口解耦，不过其内部也实现了一些简单日志方案。

###Log4j

经典的一种日志解决方案。内部把日志系统抽象封装成Logger 、appender
、pattern 等实现。我们可以通过配置文件轻松的实现日志系统的管理和多样化配置。

###Slf4j

全称为Simple Logging Facade for JAVA：java简单日志门面。
是对不同日志框架提供的一个门面封装。可以在部署的时候不修改任何配置即可接入一种日志实现方案。和commons-loging
应该有一样的初衷。个人感觉设从计上更好一些，没有commons
那么多潜规则。同时有两个额外特点：

1. 能支持多个参数，并通过{} 占位符进行替换，避免老写logger.isXXXEnabled
这种无奈的判断，带来性能提升见：http://www.slf4j.org/faq.html#logging_performance 。

2.OSGI 机制更好兼容支持

###Logback

LOGBack 作为一个通用可靠、快速灵活的日志框架，将作为 Log4j 的替代和 SLF4J
组成新的日志系统的完整实现。官网上称具有极佳的性能，在关键路径上执行速度是log4j
的10 倍，且内存消耗更少。具体优势见：

http://logback.qos.ch/reasonsToSwitch.html

Logback 分为三个模块：logback-core，logback-classic，logback-access(我们只用到前两个)

* logback-core 是核心；
* logback-classic 改善了 log4j，且自身实现了 SLF4J API，所以即使用 Logback 你仍然可以使用其他的日志实现，
如原始的 Log4J，java.util.logging 等；
* logback-access 让你方便的访问日志信息，如通过 http 的方式。

在工程 src 目录下建立 logback.xml

注:
1. logback首先会试着查找logback.groovy文件;
2. 当没有找到时，继续试着查找logback-test.xml文件;
3. 当没有找到时，继续试着查找logback.xml文件;
4. 如果仍然没有找到，则使用默认配置（打印到控制台）。

<?xml version="1.0" encoding="UTF-8"?>

<!--
scan      : 当此属性设置为 true 时，配置文件如果发生改变，将会被重新加载，默认值为 true。
scanPeriod: 设置监测配置文件是否有修改的时间间隔，如果没有给出时间单位，默认单位是毫秒。当 scan 为 true 时，此属性生效。默认的时间间隔为1分钟。
debug     : 当此属性设置为 true 时，将打印出 logback 内部日志信息，实时查看 logback 运行状态。默认值为 false。
-->
<configuration debug="true" scan="true" scanPeriod="30 seconds">

  <!--
  每个 logger 都关联到 logger 上下文，默认上下文名称为 "default"。但可以使用 <contextName> 设置成其他名字，
  用于区分不同应用程序的记录。一旦设置，不能修改。
  -->
  <contextName>myAppName</contextName>

  <!--
  用来定义变量值的标签，<property> 有两个属性，name 和 value; 其中 name 的值是变量的名称, value 的值时变量定义的值。
  通过 <property> 定义的值会被插入到 logger 上下文中。定义变量后，可以使 "${}" 来使用变量。

  例如使用<property>定义上下文名称，然后在<contentName>设置logger上下文时使用。
  <property name="APP_Name" value="myAppName" />
  <contextName>${myAppName}</contextName>
  -->

  <!--
  timestamp 有两个属性
    key        : 标识此 <timestamp> 的名字;
    datePattern: 设置将当前时间（解析配置文件的时间）转换为字符串的模式，遵循 java.txt.SimpleDateFormat 的格式。

  例如将解析配置文件的时间作为上下文名称:

  <timestamp key="bySecond" datePattern="yyyyMMdd'T'HHmmss"/>
  <contextName>${bySecond}</contextName>
  -->

  <!-- 以下每个配置的 filter 是过滤掉输出文件里面，会出现高级别文件，依然出现低级别的日志信息，通过filter 过滤只记录本级别的日志-->

  <!--
  <appender> 是 <configuration> 的子节点，是负责写日志的组件。
  <appender> 有两个必要属性 name 和 class。name 指定 appender 名称，class 指定 appender 的全限定名。
  另外还有 SocketAppender、SMTPAppender、DBAppender、SyslogAppender、SiftingAppender，并不常用，参考官方文档。当然编写自己的 Appender。
  -->

  <!--
  Filter 过滤器，执行一个过滤器会有返回个枚举值，即 DENY，NEUTRAL，ACCEPT其中之一。
    返回DENY，日志将立即被抛弃不再经过其他过滤器；
    返回 NEUTRAL，有序列表里的下个过滤器过接着处理日志；
    返回ACCEPT，日志会被立即处理，不再经过剩余过滤器。

  过滤器被添加到 <Appender> 中，为 <Appender> 添加一个或多个过滤器后，可以用任意条件对日志进行过滤。
  <Appender> 有多个过滤器时，按照配置顺序执行。
  -->

  <!--
  ConsoleAppender 把日志添加到控制台，有以下子节点：
  <encoder>: 对日志进行格式化。（具体参数见下例）
  <target> : 字符串 System.out 或者 System.err ，默认 System.out ；
  -->
  <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <!--
    encoders 默认配置为 ch.qos.logback.classic.encoder.PatternLayoutEncoder
    -->
    <encoder>
        <pattern>%d{yyyy-MM-dd HH:mm:ss} [%level] %-5level %logger{36} - %m%n</pattern>
        <!-- 常用的Pattern变量,大家可打开该pattern进行输出观察 -->
        <!--
          <pattern>
              %d{yyyy-MM-dd HH:mm:ss} [%level] - %msg%n
              Logger           : %logger{length}
              Class            : %class{length} //尽量避免使用，除非执行速度不造成任何问题。
              contextName      :
              File             : %file   //尽量避免使用，除非执行速度不造成任何问题。
              Caller           : %caller{depth}
              Line: %line   //尽量避免使用，除非执行速度不造成任何问题。
              Message: %m
              Method: %M    //尽量避免使用，除非执行速度不造成任何问题。
              Relative: %relative //输出从程序启动到创建日志记录的时间
              Thread: %thread
              Exception: %ex
              xException: %xEx
              nopException: %nopex
              rException: %rEx
              Marker: %marker
              replace(p){r, t} //p 为日志内容，r 是正则表达式，将 p 中符合 r 的内容替换为 t。例如， "%replace(%msg){'\s', ''}"
              %n
              "%" : "\%"
              "-[N]" : 左对齐, 接着是最小宽度修饰符，用十进制数表示。小则填充,大不截断
              ".[N]" : 最大宽度修饰符，符号是点号后面加十进制数。如果字符大于最大宽度，则从前面截断。
              ".-[N]": 最大宽度修饰符，符号是点号后面加十进制数。如果字符大于最大宽度，从尾部截断。
                       例如: %-4relative : 表示，将输出从程序启动到创建日志记录的时间 进行左对齐且最小宽度为 4。
          </pattern>
           -->
    </encoder>
  </appender>


  <!--
  FileAppender 把日志添加到文件，有以下子节点:
  <file>      : 被写入的文件名，可以是相对目录，也可以是绝对目录，如果上级目录不存在会自动创建，没有默认值。
  <append>    : 如果是 true，日志被追加到文件结尾，如果是 false，清空现存文件，默认是 true。
  <encoder>   : 对记录事件进行格式化。（具体参数见例子）
  <prudent>   : 如果是 true，日志会被安全的写入文件，即使其他的 FileAppender 也在向此文件做写入操作，效率低，默认是 false。
  -->
  <appender name="FILE" class="ch.qos.logback.core.FileAppender">
     <file>testFile.log</file>
     <append>true</append>
     <encoder>
        <pattern>%-4relative [%thread] %-5level %logger{35} -%msg%n</pattern>
     </encoder>
  </appender>

  <!--
  RollingFileAppender 滚动记录文件，先将日志记录到指定文件，当符合某个条件时，将日志记录到其他文件。有以下子节点:
  <file>             : 被写入的文件名，可以是相对目录，也可以是绝对目录，如果上级目录不存在会自动创建，没有默认值。
  <append>           : 如果是 true，日志被追加到文件结尾，如果是 false，清空现存文件，默认是 true。
  <encoder>          : 对记录事件进行格式化。（具体参数见例子）
  <rollingPolicy>    : 当发生滚动时，决定 RollingFileAppender 的行为，涉及文件移动和重命名。
  <triggeringPolicy >: 告知 RollingFileAppender 合适激活滚动。
  <prudent>          : 当为true时，不支持 FixedWindowRollingPolicy。支持 TimeBasedRollingPolicy，
                       但是有两个限制，1 不支持也不允许文件压缩，2 不能设置file属性，必须留空。

  -->

  <!--
  rollingPolicy 策略如下:

  TimeBasedRollingPolicy 最常用的滚动策略，它根据时间来制定滚动策略，既负责滚动也负责触发滚动。有以下子节点：
    <fileNamePattern> : 必要节点，包含文件名及 "%d" 转换符， "%d" 可以包含一个 java.text.SimpleDateFormat 指定的时间格式，
                        如: %d{yyyy-MM}。如果直接使用 %d，默认格式是 yy
    <maxHistory>      : 可选节点，控制保留的归档文件的最大数量，超出数量就删除旧文件。假设设置每个月滚动，且
                        <maxHistory>是 6，则只保存最近 6 天的文件，删除之前的旧文件。注意，删除旧文件时，那些为了归档而
                        创建的目录也会被删除。
    RollingFileAppender 的 file 字节点可有可无，通过设置 file，可以为活动文件和归档文件指定不同位置，当前日志总是记录到 file
    指定的文件（活动文件），活动文件的名字不会改变；如果没设置 file，活动文件的名字会根据 fileNamePattern 的值，每隔一段时间改
    变一次。"/" 或者 "\" 会被当做目录分隔符。

  FixedWindowRollingPolicy 根据固定窗口算法重命名文件的滚动策略。有以下子节点:
    <minIndex>        : 窗口索引最小值
    <maxIndex>        : 窗口索引最大值，当用户指定的窗口过大时，会自动将窗口设置为 12。
    <fileNamePattern >: 必须包含 "%i" 例如，假设最小值和最大值分别为 1 和 2，命名模式为 mylog%i.log, 会产生归档文件
                        mylog1.log 和 mylog2.log。还可以指定文件压缩选项，例如: mylog%i.log.gz 或者 log%i.log.zip

  -->

  <!--
  LevelFilter： 级别过滤器，根据日志级别进行过滤。如果日志级别等于配置级别，过滤器会根据 onMath
  和 onMismatch 接收或拒绝日志。有以下子节点:
    <level>      : 设置过滤级别
    <onMatch>    : 用于配置符合过滤条件的操作
    <onMismatch> : 用于配置不符合过滤条件的操作
  -->
  
  <!--
  triggeringPolicy 触发策略

  SizeBasedTriggeringPolicy 查看当前活动文件的大小，如果超过指定大小会告知 RollingFileAppender 触发当前活动文件滚动。
    <maxFileSize>             : 这是活动文件的大小，默认值是10MB。
  -->

  <!-- 按日期区分的滚动日志 -->
  <appender name="ERROR-OUT" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>logs/error.log</file>
    <encoder>
      <pattern>%d{yyyy-MM-dd HH:mm:ss} [%class:%line] - %m%n</pattern>
    </encoder>
    <!-- 如果没有 filter, 日志级别参考 root, 增加过滤器, 则只输出 ERROR -->
    <filter class="ch.qos.logback.classic.filter.LevelFilter">
      <level>ERROR</level>
      <onMatch>ACCEPT</onMatch>
      <onMismatch>DENY</onMismatch>
    </filter>
    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <!-- daily rollover -->
      <fileNamePattern>error.%d{yyyy-MM-dd}.log.zip</fileNamePattern>
      <!-- keep 30 days of history -->
      <maxHistory>30</maxHistory>
    </rollingPolicy>
  </appender>

  <!-- 按文件大小区分的滚动日志 -->
  <appender name="INFO-OUT" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>logs/info.log</file>
    <encoder>
      <pattern>%d{yyyy-MM-dd HH:mm:ss} [%class:%line] - %m%n</pattern>
    </encoder>

    <filter class="ch.qos.logback.classic.filter.LevelFilter">
      <level>INFO</level>
      <onMatch>ACCEPT</onMatch>
      <onMismatch>DENY</onMismatch>
    </filter>
    <rollingPolicy class="ch.qos.logback.core.rolling.FixedWindowRollingPolicy">
      <fileNamePattern>info.%i.log</fileNamePattern>
      <minIndex>1</minIndex>
      <maxIndex>3</maxIndex>
    </rollingPolicy>

    <triggeringPolicy class="ch.qos.logback.core.rolling.SizeBasedTriggeringPolicy">
      <maxFileSize>5MB</maxFileSize>
    </triggeringPolicy>
  </appender>

  <!--
  EvaluatorFilter 求值过滤器，评估、鉴别日志是否符合指定条件。
  需要额外的两个JAR包，commons-compiler.jar和janino.jar有以下子节点：

  <evaluator>  : 鉴别器，常用的鉴别器是 JaninoEventEvaluato，也是默认的鉴别器，它以任意的 java 布尔值表达式作为求值条件，
                 求值条件在配置文件解释成功被动态编译，布尔值表达式返回 true 就表示符合过滤条件。evaluator 有个子标签
                 <expression>，用于配置求值条件, 求值表达式作用于当前日志，logback 向求值表达式暴露日志的各种字段：
                 event              LoggingEvent
                 message            String
                 formatedMessage    String
                 logger             String
                 loggerContext      LoggerContextVO
                 level              int
                 timeStamp          long
                 marker             Marker
                 mdc                Map
                 throwable          java.lang.Throwable
                 throwableProxy     IThrowableProxy

  <onMatch>    : 用于配置符合过滤条件的操作
  <onMismatch> : 用于配置不符合过滤条件的操作
  <matcher>    : 匹配器，尽管可以使用 String 类的 matches() 方法进行模式匹配，但会导致每次调用过滤器时都会创建一个新的
                 Pattern 对象，为了消除这种开销，可以预定义一个或多个 matcher 对象，定以后就可以在求值表达式中重复引用。
                 <matcher> 是 <evaluator> 的子标签。
                 <matcher> 中包含两个子标签，一个是 <name>，用于定义 matcher 的名字，求值表达式中使用这个名字来引用 matcher；
                 另一个是 <regex>，用于配置匹配条件。
  -->

  <!-- 按日期和大小区分的滚动日志 -->
  <appender name="DEBUG-OUT" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>logs/debug.log</file>

    <encoder>
      <pattern>%d{yyyy-MM-dd HH:mm:ss} [%class:%line] - %m%n</pattern>
    </encoder>
    <!-- 过滤掉所有日志消息中不包含“billing”字符串的日志。-->
    <filter class="ch.qos.logback.core.filter.EvaluatorFilter">
      <evaluator>
        <!-- 默认为 ch.qos.logback.classic.boolex.JaninoEventEvaluator -->
        <expression>return message.contains("billing");</expression>
      </evaluator>
      <OnMatch>ACCEPT</OnMatch>
      <OnMismatch>DENY</OnMismatch>
    </filter>
    <filter class="ch.qos.logback.core.filter.EvaluatorFilter">
      <evaluator>
        <matcher>
          <Name>odd</Name>
          <!-- filter out odd numbered statements -->
          <regex>statement[13579]</regex>
        </matcher>
        <expression>odd.matches(formattedMessage)</expression>
      </evaluator>
      <OnMismatch>NEUTRAL</OnMismatch>
      <OnMatch>DENY</OnMatch>
    </filter>
    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <!-- rollover daily -->
      <fileNamePattern>debug-%d{yyyy-MM-dd}.%i.log</fileNamePattern>
      <timeBasedFileNamingAndTriggeringPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedFNATP">
        <!-- or whenever the file size reaches 100MB -->
        <maxFileSize>100MB</maxFileSize>
      </timeBasedFileNamingAndTriggeringPolicy>
    </rollingPolicy>
  </appender>

  <!--
  ThresholdFilter 级别阀值过滤
  临界值过滤器，过滤掉低于指定临界值的日志。当日志级别等于或高于临界值时，过滤器返回NEUTRAL；当日志级别低于临界值时，日志会被拒绝。
  -->
  <appender name="SUM-OUT" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>logs/sum.log</file>
    <encoder>
      <pattern>%d{yyyy-MM-dd HH:mm:ss} [%class:%line] - %m%n</pattern>
    </encoder>
    <!-- deny all events with a level below INFO, that is TRACE and DEBUG -->
    <filter class="ch.qos.logback.classic.filter.ThresholdFilter">
      <level>INFO</level>
    </filter>

    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <!-- rollover daily -->
      <fileNamePattern>debug-%d{yyyy-MM-dd}.%i.log</fileNamePattern>
      <timeBasedFileNamingAndTriggeringPolicy
            class="ch.qos.logback.core.rolling.SizeAndTimeBasedFNATP">
        <!-- or whenever the file size reaches 100MB -->
        <maxFileSize>100MB</maxFileSize>
      </timeBasedFileNamingAndTriggeringPolicy>
    </rollingPolicy>
  </appender>

  <!-- 从高到地低 OFF 、 FATAL 、 ERROR 、 WARN 、 INFO 、 DEBUG 、 TRACE 、 ALL -->
  <!-- 日志输出规则  根据当前 ROOT 级别，日志输出时，级别高于 root 默认的级别时会输出 -->
  <!--
  <loger> 仅有一个 name 属性，一个可选的 level 和一个可选的 addtivity 属性。
  name:  用来指定受此loger约束的某一个包或者具体的某一个类。
  level: 用来设置打印级别，大小写无关: TRACE, DEBUG, INFO, WARN, ERROR, ALL 和
         OFF，还有一个特殊值 INHERITED 或者同义词 NULL，代表强制执行上级的级别。
         如果未设置此属性，那么当前 loger 将会继承上级的级别。
  addtivity: 是否向上级 loger 传递打印信息。默认是 true。
  <loger> 可以包含零个或多个<appender-ref>元素，标识这个 appender 将会添加到这个 loger。
  -->

  <!--
  logback 为 java 中的包, 将控制 logback 包下的所有类的日志的打印，但是并没用设置打印级别，
  所以继承他的上级 <root> 的日志级别"DEBUG"；
  没有设置addtivity，默认为true，将此loger的打印信息向上级传递；
  没有设置appender，此loger本身不打印任何信息。
  -->
  <logger name="logback"/>

  <!--
  控制 logback.LogbackDemo 类的日志打印，打印级别为 "INFO";
  additivity 属性为 false，表示此 loger 的打印信息不再向上级传递,
  指定了名字为"STDOUT" 的 appender.
  logback.LogbackDemo: 类的全路径
  注意: 如果将 additivity 改为 true, 日志打印了两次，因为打印信息向上级传递，logger 本身打印一次，root 接到后又打印一次
  -->
  <logger name="logback.LogbackDemo" level="INFO" additivity="false">
    <appender-ref ref="STDOUT"/>
  </logger>

  <!--
  <root> 也是 <loger> 元素，但是它是根 loger. 因为已经被命名为 "root", 只有一个 level 属性.
  level: 默认是DEBUG。
  <root> 可以包含零个或多个<appender-ref>元素，标识这个appender将会添加到这个loger。
  -->
  <root level="DEBUG">
    <!-- 将root的打印级别设置为"DEBUG"，指定了名字为"STDOUT"的appender。-->
    <appender-ref ref="STDOUT" />
    <appender-ref ref="ERROR-OUT" />
    <appender-ref ref="INFO-OUT" />
    <appender-ref ref="DEBUG-OUT" />
    <appender-ref ref="SUM-OUT" />
  </root>
</configuration>


public class Slf4jTest {

    private static Logger Log = LoggerFactory.getLogger(Slf4jTest.class);
    @Test
    public void testLogBack(){
        Log.debug("Test the MessageFormat for {} to {} endTo {}", 1,2,3);
        Log.info("Test the MessageFormat for {} to {} endTo {}", 1,2,3);
        Log.error("Test the MessageFormat for {} to {} endTo {}", 1,2,3);
        try {
            throw new IllegalStateException("try to throw an Exception");
        } catch(Exception e) {
            Log.error(e.getMessage(),e);
        }
    }
}

参考
[1]:http://aub.iteye.com/blog/1101260
