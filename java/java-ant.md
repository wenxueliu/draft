ant的编译文件默认为build.xml，一般无需改变。

###project 

build.xml的根节点为 < project >，一般格式如下：

   <project name="AntStudy" default="init" basedir=".">

* name    : 工程名称；
* default : 默认的 target，就是任务；
* basedir : 基路径。一般为"."


###property 

可以定义变量，一般格式如下：

   <property name="test" value="shit" />

* 引用方式 "${test}"

###target

    <target name="compile" depends="init"><!--other command--></target>

* name : target的名称，可以在编译的时候指定是完成哪个target，否则采用project那里定义的default。
* depends : 定义了依赖关系，值为其他target的name。多个依赖关系用","隔开，顺序执行完定义的依赖关系，才会执行这个target。
* target 在 build.xml 中定义的顺序无所谓，但是 depends 中的顺序必须正确。
* if 用于验证指定的属性是否存在，若不存在，所在 target 将不会被执行。
* unless 与 if 功能正好相反，它也用于验证指定的属性是否存在，若不存在，所在 target 将会被执行。
* description 关于 target 功能的简短描述和说明。

###编译源代码

    <javac srcdir="src" destdir="classes">

         <classpath> 

             <fileset dir="lib"> 

                 <include name="**/*.jar"/> 

             </fileset>

         </classpath> 

     </javac>

这个标签自动寻找 src 中以 .java 为扩展名的文件，并且调用 javac 命令。destdir 制定编译后的 .class 文件目录

这个任务有个特点，它仅仅编译那些需要编译的源文件。如果没有更新，就不需要编译，速度就加快。

编译文件和 ant 使用的同一个 jvm，大大减少资源浪费。还可以指定　classpath。classpath　中指定文件夹，然后指定包含的文件的规则。

###创建文件

eg1. 如果文件不存在，创建文件，如果存在，更改最后访问时间为当前系统时间

        <touch file="myfile"/>

eg2. 如果文件不存在，创建文件，更改最后访问时间

        <touch file="myfile" datetime="06/28/2000 2:02 pm"/>

eg3. 更改目录下所有文件的最后访问时间

        <touch datetime="09/10/1974 4:30 pm">
            <fileset dir="src_dir"/>
        </touch>

###创建目录

       <mkdir dir="classes" />

创建dir的文件夹。

###删除目录

   对文件或目录进行删除

eg1. 删除某个文件：

	<delete file="/home/photos/philander.jpg"/>

eg2. 删除某个目录：

	<delete dir="/home/photos"/>

eg3. 删除所有的备份目录或空目录：

	<delete includeEmptyDirs="true">
		   <fileset dir="." includes="**/*.bak"/>
	</delete>
	
       <delete dir="classes" />   删除classes文件夹

eg4. 删除当前目录下所有的文件和目录，包括空目录

        <delete includeEmptyDirs="true">
            <fileset dir="build"/>
        </delete>

eg5. 删除当前目录下所有的文件和目录，不包括当前目录-->

        <delete includeEmptyDirs="true">
            <fileset dir="build" includes="**/*"/>
        </delete>

eg5. 删除文件目录树

        <deltree dir="dist"/>

###拷贝文件：

   	主要用来对文件和目录的复制功能

eg1. 复制单个文件：

	<copy file="original.txt" tofile="copied.txt"/>

eg2. 对文件目录进行复制：

	<copy todir="../dest_dir">
	    <fileset dir="src_dir"/>
	</copy>

eg3. 将文件复制到另外的目录：

	<copy file="source.txt" todir="../home/philander"/>
		
eg4. 利用 property

		<copy todir="${backup.dir}"> 
		    <fileset dir="${classes.dir}"/> 
		</copy>

把 fileset 文件夹下面的所有文件拷贝到 backup.dir

eg5. 拷贝过滤

        <copy todir="../destdir">
            <fileset dir="src_dir">
                <exclude name="**/*.java"/>
            </fileset>
        </copy>    

eg6. 拷贝一个文件集合到一个目录，同时建立备份文件-->

        <copy todir="../backup/dir">
            <fileset dir="src_dir"/>
            <globmapper from="*" to="*bak"/>
        </copy>

eg7. 拷贝一个集合的文件到指定目录，并替换掉TITLE-->

        <copy todir="../backup/dir">
            <fileset dir="src_dir"/>
            <filterset>
                <filter token="TITLE" value="Foo Bar"/>
            </filterset>
        </copy>

eg8. 其他

        <copydir src="${src}/resources" dest="${dest}" includes="**/*.java" excludes="**/Test.java"/>
        <copyfile src="test.java" dest="subdir/test.java"/>

###移动文件或目录

eg1. 移动单个文件：

        <move file="sourcefile" tofile=”destfile”/>

eg2. 移动单个文件到另一个目录：

        <move file="sourcefile" todir=”movedir”/>

eg3. 移动某个目录到另一个目录：

        <move todir="newdir"> <fileset dir="olddir"/></move>

eg4. 按照某种模式移动

        <move todir="some/new/dir">
            <fileset dir="my/src/dir">
                <include name="**/*.jar"/>
                <exclude name="**/ant.jar"/>
            </fileset>
        </move>

###重命名

        <rename src="foo.jar" dest="ant-${version}.jar"/>

###建立临时文件

        <tempfile property="temp.file" destDir="build" suffix=".xml"/>

在目录build下，建立文件名为temp.file，后缀名为xml的文件



###echo 命令

该任务的作用是根据日志或监控器的级别输出信息。它包括 message 、 file 、 append 和 level 四个属性，举例如下

    <echo message="Hello,ANT" file="/home/philander/logs/ant.log" append="true">

###Classpath

有两个属性path和location，path指定jar包，location指定包含jar包的路径。可以通过fileset和dirset简化配置。

        <classpath>
              <pathelement path="${classpath}"/>
              <fileset dir="lib">
                <include name="**/*.jar"/>
              </fileset>
              <pathelement location="classes"/>
              <dirset dir="${build.dir}">
                <include name="apps/**/classes"/>
                <exclude name="apps/**/*Test*"/>
              </dirset>
              <filelist refid="third-party_jars"/>
        </classpath>

###条件语句

        <java classname="HelloWorld">
            <classpath path="${classdir}"/>
        </java>
        <if>
            <equals arg1="${hello}" arg2="true"/>
            <then>
                <echo>${hello} is true</echo>
            </then>
            <elseif>
                <equals arg1="${hello}" arg2="false"/>
                <then>
                    <echo>${hello} is false</echo>
                </then>
            </elseif>
            <else>
                <echo>${hello}</echo>
            </else>
        </if>

###javac

用户编译一个或一组 java 文件。

* srcdir        表示源程序的目录。
* destdir       表示 .class 文件的输出目录。
* include       表示被编译的文件的模式。
* excludes      表示被排除的文件的模式。
* classpath     表示所使用的类路径。
* debug         表示是否包含的调试信息。
* optimize      表示是否使用优化。
* verbose       表示提供详细的输出信息。
* fileonerror   表示当碰到错误就自动停止。
* includeantruntime    指定编译任务是否包含ant的classpath,可有可无，不影响编译，

例如:

        <javac srcdir="${src}" destdit="${build}" classpath="xyz.jar" debug="on" source="1.4"/>

###java

用于执行编译的 .class 文件

* dir　: 工作文件夹
* classname     表示将执行的类名。程序入口类, 该类必须定义 main 函数。
* jar           表示包含该类的 JAR 文件名。
* classpath     所表示用到的类路径。
* fork          表示在一个新的虚拟机中运行该类。
* failonerror   表示当出现错误时自动停止。
* output        表示输出文件。
* append        表示追加或者覆盖默认文件。

因为你编译放 class 的文件夹正在使用，所以要新打开一个虚拟机。因此 fork 一般为 true

例如:

        <java classname="test.Main" dir="${exec.dir}" jar="${exec.dir}/dist/test.jar" fork="true" failonerror="true" maxmemory="128m">
            <arg value="-h"/>
            <classpath>
                <pathelement location="dist/test.jar"/>
                <pathelement path="/Users/antoine/dev/asf/ant-core/bootstrap/lib/ant-launcher.jar"/>
            </classpath>
        </java>

###jar

用来生成一个 jar 包文件。

* destfile      表示生成的 JAR 文件名。
* basedir       表示被归档的文件夹, 即将 basedir 的文件归档为 jar 包。
* includes      表示包括归档的文件模式。
* exchudes      表示被排除归档的文件模式。
* manifest      为jar包指定 manifest，当然，如果jar包不需要打成runnable的形式，manifest可以不要

           <manifest>
                <!--指定main-class-->
                <attribute name="Main-Class" value="oata.HelloLog4j" />
                <!--指定Class-Path-->
                <attribute name="Class-Path" value="${libs}">
                </attribute>
            </manifest>

###javadoc：

* packagenames="com.lcore.*"
* sourcepath="${basedir}/src"
* destdir="api"
* version="true"
* use="true"
* windowtitle="Docs API"
* encoding="UTF-8"
* docencoding="GBK">  

###执行命令

        <target name="help">
            <exec executable="cmd">
                <arg value="/c">
                <arg value="ant.bat"/>
                <arg value="-p"/>
            </exec>
        </target>


###path

可以定义path对象，在其他地方可以直接复用。

        <path id="1"> 

           <pathelement location="."/> 

           <pathelement location="./lib/junit.jar"/> 

        </path>

        <path id="2"> 

           <fileset dir="lib"> 

           <include name="**/*.jar"/> 

           </fileset> 

        </path>

        <javac srcdir="./src" destdir="./classes"> 

           <classpath refid="1"/> 

        </javac>

        <javac srcdir="./src" destdir="./classes"> 

              <classpath refid="1"> 

                  <pathelement location="."/> 

                  <pathelement location="./lib/junit.jar"/> 

              </classpath> 

        </javac>


###导入一个XML文件

        <import file="../common-targets.xml"/>

###条件使用

        <condition property="isMacOsButNotMacOsX">
            <and>
                <os family="mac">
                <not>
                    <os family="unix">
                </not>
            </and>
        </condition>

###替换

        <replace 
            file="configure.sh"
            value="defaultvalue"
            propertyFile="src/name.properties">
          <replacefilter 
            token="@token1@"/>
          <replacefilter 
            token="@token2@" 
            value="value2"/>
          <replacefilter 
            token="@token3@" 
            property="property.key"/>
          <replacefilter>
            <replacetoken>@token4@</replacetoken> 
            <replacevalue>value4</replacevalue>
          </replacefilter>
        </replace>

###chmod

        <chmod perm="go-rwx" type="file">
            <fileset dir="/web">
                <include name="**/*.cgi"/>
                <include name="**/*.old"/>
            </fileset>
            <dirset dir="/web">
                <include name="**/private_*"/>
            </dirset>
        </chmod>    

###显示错误信息

Fail task 退出当前构建，抛出BuildException，打印错误信息。

message:    A message giving further information on why the build exited

if:        Only fail if a property of the given name exists in the current project

unless:    Only fail if a property of the given name doesn't exist in the current project

status:    Exit using the specified status code; assuming the generated Exception is not caught, the JVM will exit with this status.Since Apache Ant 1.6.2

        <fail>Something wrong here.</fail>
        <fail message="${属性}"/>
        <!--如果这个属性不存在，显示错误-->
        <fail unless="failCondition" message="unless Condition"/>
        <!--如果这个属性存在，显示错误-->
        <fail if="failCondition" message="if Condition"/>
        <!--如果符合条件，显示错误-->
        <fial message="tag condition">
            <condition>
                <not>
                    <isset property="failCondition"/>
                </not>
            </condition>
        </fail>


###length 

把字符串foo的长度保存到属性length.foo中

        <length string="foo" property="length.foo"/>

把文件bar的长度保存到属性length.bar
        
        <length file="bar" property="length.bar"/>

###input 

        <input message="Please enter db-username:" addproperty="db.user" defaultvalue="Scott-Tiger"/>

###压缩与解压缩

解压缩zip文件

        <unzip src="apache-ant-bin.zip" dest="${tools.home}">
            <patternset>    
                <include name="apache-ant/lib/ant.jar"/>
            </patternset>
            <mapper type="flatten"/>
        </unzip>

压缩zip文件

        <zip destfile="${dist}/manual.zip" basedir="htdoc/manual" includes="api/**/*.html" excludes="**/todo.html"/>

打tar包

        <tar destfile="/Users/antoine/dev/asf/ant-core/docs.tar">
            <tarfileset dir="${dir.src}/doc" fullpath="/usr/doc/ant/README" preserveLeadingSlashes="true">
                <include name="readme.txt"/>
            <tarfileset>
            <tarfileset dir="${dir.src}/docs" prefix="/usr/doc/ant" preserveLeadingSlashes="true">
                <include name="*.html"/>
            </tarfileset>
        </tar>

解压tar包

        <untar src="tools.tar" dest="${tools.home}"/>

打war包

<war destfile="myapp.war" webxml="src/metadata/myapp.xml">
    <fileset dir="src/html/myapp"/>
    <fileset dir="src/jsp/myapp"/>
    <lib dir="thirdparty/libs">
        <exclude name="jdbc1.jar">
    </lib>
    <classes dir="build/main"/>
    <zipfileset dir="src/graphics/images/gifs" prefix="images"/>
</war>