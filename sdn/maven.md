maven 

###配置文件

project : Defined in the project POM file, pom.xml
Per User : Defined in Maven settings xml file (%USER_HOME%/.m2/settings.xml)
Global : Defined in Maven global settings xml file (%M2_HOME%/conf/settings.xml)


###依赖搜索
   
1 搜索依赖本地资源库，如果没有找到，移动到第2步，否则，如果发现然后做进一步处理。
2 搜索依赖中央存储库中，如果没有找到，远程资源库/存储库/被提及，然后移动到步骤4，否则，如果找到，那么它下载到本地存储库中，以备将来参考。
3 如果没有提到远程仓库，Maven的只是停止处理并抛出错误（找不到的依赖）。
4 远程仓库或储存库中的搜索依赖，如果发现它下载到本地资源库以供将来参考，否则Maven的预期停止处理并抛出错误（找不到的依赖）。

###插件

Maven是一个实际执行的插件框架，每一个任务实际上是由插件完成的。Maven的插件通常用于：

* 创建 jar 文件
* 创建 war 文件 
* 编译代码文件
* 代码进行单元测试
* 创建项目文档
* 创建项目报告

一个插件通常提供了一组目标，可使用以下语法来执行：

		mvn [plugin-name]:[goal-name]

####插件类型

构建插件：在生成过程中执行，并应在pom.xml中的<build/>元素进行配置
报告插件：他们的网站生成期间执行的，他们应该在pom.xml中的<reporting/>元素进行配置

常用插件

		clean 		Clean up target after the build. Deletes the target directory.
		compiler 	Compiles Java source files.
		surefile 	Run the JUnit unit tests. Creates test reports.
		jar 		Builds a JAR file from the current project.
		war 		Builds a WAR file from the current project.
		javadoc 	Generates Javadoc for the project.
		antrun 		Runs a set of ant tasks from any phase mentioned of the build.

Example 

	mvn compile - to compile individual modules
	mvn install - copy jar files to target
	mvn clean
	mvn package - creates package
	mvn clean install -DskipTests - To skip tests(Tests are automatically built as part of each module)

###依赖管理

all dependent Jar files gets stored in $HOME/.m2

* Dependency mediation

Determines what version of a dependency is to be used when multiple versions of an artifact are encountered. If two dependency versions are at the same depth in the dependency tree, the first declared dependency will be used.

* Dependency management

Directly specify the versions of artifacts to be used when they are encountered in transitive dependencies. For an example project C can include B as a dependency in its dependencyManagement section and directly control which version of B is to be used when it is ever referenced.

* Dependency scope

 Includes dependencies as per the current stage of the build
 
* Excluded dependencies

Any transitive dependency can be excluede using "exclusion" element. As example, A depends upon B and B depends upon C then A can mark C as excluded.

* Optional dependencies

Any transitive dependency can be marked as optional using "optional" element. As example, A depends upon B and B depends upon C. Now B marked C as optional. Then A will not use C.

	compile 	dependency is available in classpath of project. It is default scope.
	provided 	dependency is to be provided by JDK or web-Server/Container at runtime.
	runtime 	dependency is not required for compilation, but is required during execution.
	test 		dependency is only available for the test compilation and execution phases.
	system 		you have to provide the system path.
	import 		This scope is only used when dependency is of type pom. This scopes indicates that the specified POM 
				should be replaced with the dependencies in that POM's <dependencyManagement> section.


###项目文件构成

controller 注意 opendaylight/commons  opendaylight/archetypes 这两个目录
####META-INF

####pom.xml

注：

该文件中路径，都是相对于 pom.xml 文件

一般jar文件的命令格式：groupId+ artifactId+ “-”+version +“.jar”


* project : 后面的所有条目都包含在该条目下。
* modelVersion : 指定POM模型的版本，对Maven2、Maven3来说只能是4.0.0。
* groupId : 定义Maven项目（模块）隶属的实际项目，即项目属于那个组，主要来标志项目，格式为：com+公司名+项目名，例如”com.mycom.myapp”。
* artifactId：定义实际项目的Maven项目（模块），即项目的模块名称，主要是来标志模块，例如“util”、“implementation”，如果模块可以分为子模块，那么可以用“-”或者“.”分开，比如“util.io”,“util.log”或者“util-io”,“util-log”。有些情况下也在artifactId命名以groupId作为前缀，比如myapp-utli，这样有区别于其他项目的util-XXX-util。
* parent : 如果继承自某个 pom.xml，加入继承的 pom.xml。

		groupId
		artifactId
		version
		relativePath
		
* version : project 的版本。如果包含 SNAPSHOT 字段表示每次编译都会下载最新版本
* artifactId : project 的 id, 常用用分隔符"."来表示的目录结构命名。
* packaging :  pom bundle jar war 在 opendaylight 一般是 pom 或 bundle
* prerequisites : 
* properties : 
	定义一些变量，被后面使用
* build : 
	plugin: 
	
		groupId
		artifactId
		version
		configuration(可选)
		dependencies(可选)
		executions（可选）
		
* distributionManagement
	repository
		id
		url ：http://nexus.opendaylight.org/content/repositories/opendaylight.release/ opendaylight 的代码都在这个 url 下。
	snapshotRepository
		id
		url
	site
		id
		url

* dependencyManagement
	dependency
		groupId
		artifactId
		version


* modules: 子模块列表，所有的模块都在 pom.xml 目录下。每一个子模块都可以继续包含子模块,因为每个子模块下都与 pom.xml文件
* scm
		connection
		developerConnection
		tag
		url
	
* profiles
	id   
	activation
	modules

* reporting
	outputDirectory
	excludeDefaults
	plugins
	
* repositories
	releases
		id
		url
		name
		snapshots
		releases

* pluginRepositories
	pluginRepository
		id
		url
		name
		snapshots
		releases

关键pom.xml

 <build>
   <plugins>
	<plugin>
        <groupId>org.apache.felix</groupId>
        <artifactId>maven-bundle-plugin</artifactId>
        <version>${bundle.plugin.version}</version>
        <extensions>true</extensions>
        <configuration>
          <instructions>
 			<Export-Package>
 			....
 			</Export-Package>
 			<Import-Package>
 			.....
 			</Import-Package>
 			<manifestLocation>${project.basedir}/META-INF</manifestLocation>
        </configuration>
      </plugin>
    </plugins>
  </build>


####src
####target
####enunciate.xml  org.codehaus.enunciate maven-enunciate-plugin  It describes where the APIs should be mounted on the REST path.



###构建生命周期

prepare-resources  	resource copying 	Resource copying can be customized in this phase.
compile				compilation			Source code compilation is done in this phase.
package				packaging			This phase creates the JAR / WAR package as mentioned in packaging in POM.xml.
install				installation		This phase installs the package in local/remote maven repository.

《Maven 实战》
