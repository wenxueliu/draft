
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


<?xml version="1.0" encoding="UTF-8"?>

<configuration debug="true" scan="true" scanPeriod="30 seconds">

  <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <!-- encoders are  by default assigned the type
         ch.qos.logback.classic.encoder.PatternLayoutEncoder -->
    <encoder>
        <pattern>%d{yyyy-MM-dd HH:mm:ss} [%level] - %m%n</pattern>
        <!-- 常用的Pattern变量,大家可打开该pattern进行输出观察 -->
        <!--
          <pattern>
              %d{yyyy-MM-dd HH:mm:ss} [%level] - %msg%n
              Logger: %logger
              Class: %class
              File: %file
              Caller: %caller
              Line: %line
              Message: %m
              Method: %M
              Relative: %relative
              Thread: %thread
              Exception: %ex
              xException: %xEx
              nopException: %nopex
              rException: %rEx
              Marker: %marker
              %n
          </pattern>
           -->
    </encoder>
  </appender>

  <!-- 按日期区分的滚动日志 -->
  <appender name="ERROR-OUT" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>logs/error.log</file>
    <encoder>
      <pattern>%d{yyyy-MM-dd HH:mm:ss} [%class:%line] - %m%n</pattern>
    </encoder>
    <filter class="ch.qos.logback.classic.filter.LevelFilter">
      <level>ERROR</level>
      <onMatch>ACCEPT</onMatch>
      <onMismatch>DENY</onMismatch>
    </filter>
    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <!-- daily rollover -->
      <fileNamePattern>error.%d{yyyy-MM-dd}.log.zip</fileNamePattern>
      <!-- keep 30 days' worth of history -->
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

  <!-- 按日期和大小区分的滚动日志 -->
  <appender name="DEBUG-OUT" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>logs/debug.log</file>

    <encoder>
      <pattern>%d{yyyy-MM-dd HH:mm:ss} [%class:%line] - %m%n</pattern>
    </encoder>
    <filter class="ch.qos.logback.classic.filter.LevelFilter">
      <level>DEBUG</level>
      <onMatch>ACCEPT</onMatch>
      <onMismatch>DENY</onMismatch>
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

  <!-- 级别阀值过滤 -->
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
  <root level="debug">
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
