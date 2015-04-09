karaf guide for opendaylight 
==============================

* Version : 0.1
* Date: 2014-10-30
* By : wenxueliu
* comment : you can start at section [Hands on Guide to Doing your Karaf Features]

What is Karaf
==============================
[Apache Karaf](http://karaf.apache.org/) is a small OSGi based runtime which provides a lightweight container onto which various components and applications can be deployed. It tends to be helpful to think of Karaf as providing an ecosystem for your application - we've collected together various libraries and frameworks, and tested that they work well together, simplifying your runtime experience.

Here is a short list of features supported by the Karaf:

* Hot deployment: Karaf supports hot deployment of OSGi bundles by monitoring jar files inside the [home]/deploy directory. Each time a jar is copied in this folder, it will be installed inside the runtime. You can then update or delete it and changes will be handled automatically. In addition, the Karaf also supports exploded bundles and custom deployers (blueprint and spring ones are included by default).
    
* Dynamic configuration: Services are usually configured through the ConfigurationAdmin OSGi service. Such configuration can be defined in Karaf using property files inside the [home]/etc directory. These configurations are monitored and changes on the properties files will be propagated to the services.
    
* Logging System: using a centralized logging back end supported by Log4J, Karaf supports a number of different APIs (JDK 1.4, JCL, SLF4J, Avalon, Tomcat, OSGi)
    
* Provisioning: Provisioning of libraries or applications can be done through a number of different ways, by which they will be downloaded locally, installed and started.
    
* Native OS integration: Karaf can be integrated into your own Operating System as a service so that the lifecycle will be bound to your Operating System.
    
* Extensible Shell console: Karaf features a nice text console where you can manage the services, install new applications or libraries and manage their state. This shell is easily extensible by deploying new commands dynamically along with new features or applications.
    
* Remote access: use any SSH client to connect to Karaf and issue commands in the console
    
* Security framework based on JAAS
    
* Managing instances: Karaf provides simple commands for managing multiple instances. You can easily create, delete, start and stop instances of Karaf through the console.


Karaf Provisioning in Details
==================================

Karaf has two methods of provisioning high level components known as features. This can be done via Feature Descriptors or standalone .KAR file packages. Feature descriptors are suitable for development , testing and advanced users while .KAR archives provides downloadable binary artifacts mostly suitable for end-user standalone offline installation.

Feature Descriptors
------------------------------
Karaf supports provisioning via 'feature descriptors' which allow developers to group together sub-features, bundles, configuration files, and other resources into one simple to use deployable package. The bundles will be resolved via [1] compatible URL as defined in the feature file. The current descriptors currently is using the local maven repository (.m2/repository) along with whatever is part of the custom distribution (/system) as the locations from which to fetch the bundles. The feature descriptor also specifies the *start-level* and order in which the bundles have to start as such making feature start-stop behaviour more deterministic thus reducing the number of runtime errors encountered.

* Example: 

Feature MD-SAL contains 25+ bundles, and requires yang tools. All told that around 40 bundles plus configuration files. Using feature:install odl-mdsal-all" will provision all of these bundles along with the configuration files and install them into the OSGi container. This frees users and developers from needing to know about all the individual components required to run MD-SAL.

* Example: 

Feature openflowplugin contains two openflowplugin bundles, and requires the md-sal feature. Just specifying the openflowplugin feature get you exactly what you need, no more, no less.

KAR Archives
-----------------------------
The KAR archive (Karaf Archive) is a special archive package that contains both the feature descriptor file along with all the referenced bundles. This way a user doesn't need to have a local or remote maven repository with the bundles in order to install the feature. This makes .kar files suitable for offline installations or easy to download links. Installing KAR files can be done via

kar:install /path/odl-feature.kar

on the console or simply by putting the .kar file in the /deploy folder of the customized Karaf distribution for OpenDaylight



What makes Karaf useful as a Release Vehicle
========================================

Karaf allows us to have:

* A minimal karaf-based OpenDaylight container which consists of : karaf + branding fragment + osgi framework extensions + a few config files
* Features which can be installed as one liners like:

feature:install odl-openflowplugin-all"

which pull in openflowplugin and everything you need for it to work. 

Published Repositories
------------------------------

Because Karaf allows us to specify high level features which users can be installed in the container, we have the opportunity to allow users to have exactly the high level features they want.

As an example a download page could either provide a list of downloadable .kar packages for each features or we can host an online official /TSC approved feature repository from which features can be downloaded. Moreover, there could be different repositories based on the stability of the projects. As such a list of "stable" features would make it into the stable repository while "unstable" and "experimental" features could be available based on user's needs. Moreover project may have stable and experimental features published which makes it possible for projects to innovate without disrupting their stable components. 

		Feature Repository 						Stability
		http://xxx/stable-features.xml 			Stable
		http://xxx/unstable-features.xml 		Unstable
		http://xxx/experimental-features.xml 	Experimental 
		
These repositories would be available as part of the minimal customized ...
Downloadable Configuration Profiles

A suggestion would be to make a small web application that would generate proper configuration files from a set of selectable features. Users would then simply put that configuration file at the right startup location. This configuration file could also be bundled and added to a release .zip archive along with the .kar files if necessary to provide users with their completely customized distribution.

For example user wants features:

* bgpcep-all
* ovsdb-neutron

Thus when they start OpenDaylight, they will get *precisely* the minimum set of things they need for the requested features to run. No more, no less. 

User Driven Feature Selection
===============================

Because there is a huge set of combinatronics in terms of the features that users want together, and they are difficult to predict accurately, having User Driven Feature Selection rather than Centrally Planned Release Vehicle Definition allows us to give our users what they actually want. 


Recommended Release Vehicles for Karaf
===============================

This proposal requires no 'hard' Release Vehicles based on projects and features, because we provide users with the ability to choose the features (add-ons) they want to have for their controller.
OpenDaylight Container

OpenDaylight Container
---------------------------

This download contains the minimal OpenDaylight container as a standard Karaf distribution will not work because of ODL specific requirements. This container should ideally also serve a CLI & GUI interfaces which allows end-users to configure the environment by adding features. This distribution is currently available from controller but should be sitting in OpenDaylight's root dependency whether this is parent pom project or a runtime project of some sort.
OpenDaylight Online Distribution

OpenDaylight Online Distribution
--------------------------

While it is impossible to predict the features that end-users would expect I would consult a small user group to know what are end-users expecting from a base controller. My personal bias would be to support basic behaviors like l2switching along with an OpenFlow southbound, the other features should then be downloaded from the online repository on demand as required. (Think Package-Manager like). Other add-ons can also be added by dropping a .kar in Deploy.
OpenDaylight Offline Distribution

OpenDaylight Offline Distribution
--------------------------

The offline distribution will package all projects without installing them so that environments without internet can install the features from the local repository instead. It should have the same level of basic functionality as decided for the online distribution working from the start.


Karaf Features Guidelines
===========================

Introduction
--------------------------

This section outlines the guidelines required in creating and maintaining Apache Karaf feature files for your projects for use with OpenDaylight's Karaf-based distribution. 

About Features
--------------------------

A feature contains a list of bundles or sub-features that acts as an atomically installable unit. Features can be either downloaded online from the Maven repository or offline via a localized distribution or installable .kar artifacts. 

Creating Project Feature File
--------------------------

To create a feature file one must simply list the bundle and sub-feature dependencies. It also should provide a description which is used when listing features available in the container.

		<?xml version="1.0" encoding="UTF-8"?>
		<features name="openflowplugin-${project.version}" xmlns="http://karaf.apache.org/xmlns/features/v1.2.0"  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://karaf.apache.org/xmlns/features/v1.2.0 http://karaf.apache.org/xmlns/features/v1.2.0">
			<feature name='odl-openflowplugin' description="OpenDaylight :: Openflow Plugin :: Plugin" version='${project.version}'>
				<feature version="${mdsal.version}">odl-mdsal-all</feature>
				<feature version="${openflowjava.version}">odl-openflowjava</feature>
				<bundle>mvn:org.opendaylight.openflowplugin/openflowplugin/${project.version}</bundle>
			</feature>
		</features>

Feature Best Practices
--------------------------

This section outlines some best practices in naming conventions, location and versioning for your feature files.

**Project Location**

It is highly suggested to have features reside under /features of the root directory for a project in order to easily locate them and for automation purposes. 

**Naming Convention**

_* Feature Naming *_

To follow the current naming convention best practices the feature names should follow the following format:

_* odl-<projectname>-<featurename> *_

Feature names should be lower case, so

	odl-myfeature <-- THIS

	odl-myFeature <-- NOT THIS

The odl prefix is necessary to differentiate ODL specific features from any other thirdparty installable features available to karaf. The project name helps identify rapidly which project is providing this feature and finally the featurename identifies 

_*Maven artifactId Naming*_

For a features/ maven project a useful naming convention for maven artifact naming of:

	<artifactId>features-<projectname></artifactId>

Example:

	<artifactId>features-mdsal</artifactId>

Versioning
----------------------------

Feature versioning should follow semantic versioning practices which is important for any external component depending on this features. As such versioning should follow : <major>.<minor>.<micro>.

* A major version increase means that backward compatibility is no longer being provided and that there is a major change in the API or architecture.
* A minor version increase means that additional functionality is available but not breaking backward compatibility.
* A micro version increase means a bugfix, patch or other changes to the feature that doesn't imply a new functionality.

Feature versioning doesn't need to follow the bundle versioning and represents the high-level version of this atomic unit. However where applicable it is recommended to follow the bundle versioning if these bundle are all linked together to provide a component-level functionality.

Description
-----------------------------

A feature description is usually a single line item on "what this feature install" it is not a substitute for component-level description. It is recommended to follow the following format:

	OpenDaylight :: <Project Name> :: Small Feature Summary Text

This format is displayed when listing features through the features:list command and as such should ideally fit in the terminal screen response to that command.

Avoid start-levels
----------------------------

Things like

		<bundle ... start-level='35' ... >

should be avoided, as feature specifying start-levels can break other projects features and even sometimes the karaf containers features.


Granularity(粒度)
----------------------------

Features should be provided with appropriate granularity. As such where there are different choices of implementation the API should be available as a seperate feature on which the implementations would depend. The same applies to "add-ons" to a core-level feature to the project such as additional protocols, transports etc. which might not be required all the time by the users of this component. As such we expect projects to provide the appropriate level of granularity to their projects. 

Overinclusion
-----------------------------

Features should define roughly the minimal shell of things they need to function. As such, be cautious to avoiid overinclusion. If you only need a single bundle, you probably should declare the bundle, not a <otherproject>-all feature. 

Consumability
-----------------------------

You can have a transitive tree of features.xml files. You would like to make it easy for folks to consume your feature file as a standalone unit. Because one features.xml can depend on features from another, you need to make sure to reference it correctly. For example, protocol framework below uses features from the config feature:

		<features name="odl-protocol-framework-${protocol-framework.version}" xmlns="http://karaf.apache.org/xmlns/features/v1.2.0"
				  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
				  xsi:schemaLocation="http://karaf.apache.org/xmlns/features/v1.2.0 http://karaf.apache.org/xmlns/features/v1.2.0">
		  <repository>mvn:org.opendaylight.controller/config-features/${config.version}/xml/features</repository>
		  <feature name='odl-protocol-framework' version='${project.version}'>
			<bundle>mvn:org.opendaylight.controller/protocol-framework/${protocol-framework.version}</bundle>
			<feature version='${config.version}'>odl-config-api</feature> <!-- needed by netty-config-api -->
			<feature version='${config.version}'>odl-config-netty-config-api</feature> <!-- needed by netty-config-api -->
		  </feature>
		</features>

The element:

		<repository>mvn:org.opendaylight.controller/config-features/${config.version}/xml/features</repository>

Indicates that this feature file uses features from the config-features features.xml and how to get it (via maven).

Of course, you also then want to put in the pom.xml file for your features/ a proper dependency as well

		<dependency>
			  <groupId>org.opendaylight.controller</groupId>
			  <artifactId>config-features</artifactId>
			  <version>${config.version}</version>
			  <classifier>features</classifier>
			  <type>xml</type>
			</dependency>


Cycles
--------------------------

Try to avoid having cycles between features.xml files (meaning A/features.xml uses features from B/features.xml and B/features.xml uses features from A/features.xml). This causes problems because you can't have maven cyclic dependencies, and users of your features.xml files that use maven will then have difficulties. 

Atomicity
--------------------------

It should *always* be the case that if a feature is defined, then in a blank container with no other features installed that:

	feature:install <feature>

succeeds in installing at the OSGI level, and *functions* as a feature without needing to install any other features.

If you find yourself writing instructions like:

	To make this work type
	feature:install foo
	feature:install bar

then you have violated atomicity, and it is probably true that you need to fix feature bar to either depend on feature foo, or dependent on other things that happen to also be brought in by foo (see Overinclusion) 

Complex situations
--------------------------

If your project has the need to have multiple features.xml files, then under your /features/ directory have sub-maven modules for each one. Example:

controller/features/config/ controller/features/mdsal/ 

Component Meta-Features
==================================

If the project provides multiple features provide component-level meta-features should be provided to provide easy and quick component-level installation of the feature. This meta-feature will only contain other features that should be logically grouped to provide an easy way for other projects to specify their dependency. This is especially useful when a feature can have different implementation options off a different core and allows projects to specify and quickly import the correct 'stack'.

An example meta-feature.

	  <feature name="odl-adsal-all" description="OpenDaylight AD-SAL All Features" version="${sal.version}">
		  <feature version="${sal.version}">odl-adsal-core</feature>
		  <feature version="${sal.networkconfiguration.version}">odl-adsal-networkconfiguration</feature>
		  <feature version="${sal.connection.version}">odl-adsal-connection</feature>
		  <feature version="${clustering.services.version}">odl-adsal-clustering</feature>
		  <feature version="${configuration.version}">odl-adsal-configuration</feature>
	   </feature>

It is customary to create a feature with a -all suffix to provide a way to quickly install all related features. 

Hands on Guide to Doing your Karaf Features
====================================

Guidance for Feature Creators
------------------------------

**Create a features file**

1 Run the opendaylight-karaf-features archetype

From a directory in your project which contains a pom.xml suitable to be a parent pom run 

	mvn archetype:generate -DarchetypeGroupId=org.opendaylight.controller -DarchetypeArtifactId=opendaylight-karaf-features-archetype -DarchetypeRepository=http://nexus.opendaylight.org/content/repositories/opendaylight.snapshot/ -DarchetypeCatalog=http://nexus.opendaylight.org/content/repositories/opendaylight.snapshot/archetype-catalog.xml

You will be prompted for

	groupId: (enter your project groupId)
	artifactId: features-${repoName}
	version: (version of your project)
	package: (accept default)
	repoName: (your projects repoName, examples: controller, yangtools, openflowplugin)

example 

	Define value for property 'groupId': : org.opendaylight.controller    
	Define value for property 'artifactId': : features-loadbalancer
	Define value for property 'version':  1.0-SNAPSHOT: : 
	Define value for property 'package':  org.opendaylight.controller: : 
	Define value for property 'repoName': : loadbalancer

2 Edit the features-${repoName}/src/main/resource/features.xml or 

Edit the

	features-${repoName}/src/main/resources/features.xml

find the TODO items, and do them :)

Note: If you have config files you need included, see section [How to create a configfile project for Karaf]. 

4 Edit the features-${repoName}/pom.xml

Edit the

	features-${repoName}/pom.xml

find the TODO items, and do them :) 

5 Build and debug

	cd features-${repoName}/
	mvn clean install //if you run some error, add  options `-DskipTests -DskipIT `

This will run the features test, which will check to see if your features load at the OSGI level. You will likely have to iterate debugging the load failures, adding bundles or features to your features until the tests pass. 

you are stopped by some exception ? reference section [Common Test Failures and their solutions]

the simple example of opendaylight is dlux, you can find at *_distribution-karaf-0.2.0-Helium/system/org/opendaylight*_ when you
download the zip package and unzip it.


*Really* test your features.xml
------------------------------

Your feature should be able to build with an empty .m2, so try:

	rm ~/.m2/repository/org/opendaylight/  //if you want to delete, please use mv to backup somewhere
	mvn clean install

and track down the last of your missing dependencies.

This is because you may have a really warm .m2 cache from building your project locally, but your consumers may not. 


_*A bit more about warm vs cold .m2 and why it matters*_

Karaf when it seeks to load bundles, looks in the 'central' maven repo and your .m2/ locally. If you build your whole project, or have done something else which causes the things you need to be in your local .m2, that .m2 is said to be 'warm'.

When people *use* your feature, their .m2 is unlikely to be warm. If you have the dependencies in your features/pom.xml correct then it will make sure all the thing your consumer needs get into their .m2.

To make sure you got it right, you want to delete your .m2 as instructed above, and then try building your feature. That should shake out the last of the errors in your pom.xml file. 


Test your features for functionality in your local karaf distro
-----------------------------------------------------------

**Create your local distro**

1 Run the opendaylight-karaf-distro-archetype

mvn archetype:generate -DarchetypeGroupId=org.opendaylight.controller -DarchetypeArtifactId=opendaylight-karaf-distro-archetype -DarchetypeRepository=http://nexus.opendaylight.org/content/repositories/opendaylight.snapshot/ -DarchetypeCatalog=http://nexus.opendaylight.org/content/repositories/opendaylight.snapshot/archetype-catalog.xml

2 Edit the karaf/pom.xml file

Edit the features/pom.xml, find the TODO items, and do them :)

You will be prompted for

	groupId: (enter your project groupId)
	artifactId: distribution-karaf
	version: (version of your project)
	package: (accept default)
	repoName: (your projects repoName, examples: controller, yangtools, openflowplugin)

for example 

	Define value for property 'groupId': : org.opendaylight.controller
	Define value for property 'artifactId': : distribution-karaf
	Define value for property 'version':  1.0-SNAPSHOT: : 
	Define value for property 'package':  org.opendaylight.controller: : 
	Define value for property 'repoName': : loadbalancer


3 Rename the directory

You will now have a directory

	distribution-karaf

4 Build your local distribution

	mvn clean install

5 Run the karaf distro

From the directory of your karaf distribution:

	cd target/assembly/bin
	./karaf

Test your feature functionally

You can check to see if your features are installed with

	feature:list -i

If they are not, try installing them with:

	feature:install <yourfeature>

Run your functional tests to make sure things work.

Note: restconf is on port 8181, not 8080.

You can also see the logs with

	log:display


Common Test Failures and their solutions
------------------------------

1 Reason: Missing Constraint: Import-Package:

This error means you are missing a bundle in a feature of yours. Fixing it is simple, add the bundle containing the indicated package to the failing feature. 

2 Could not find artifact

This error means you are missing a dependency for either a bundle, config file, or other features.xml repo in your features/pom.xml. Add the dependency at scope compile and all will be well. 

3 Exceptions you can ignore

		Exception in thread "config-pusher" java.lang.IllegalStateException: java.lang.InterruptedException: sleep interrupted
			at org.opendaylight.controller.netconf.persist.impl.ConfigPusherImpl.sleep(ConfigPusherImpl.java:219)
		
		--------------------------------------------------
		
		java.lang.IllegalStateException: Error while copying old configuration from ModuleInternalInfo [name=ModuleIdentifier{factoryName='shutdown', instanceName='shutdown'}] to org.opendaylight.controller.config.yang.shutdown.impl.ShutdownModuleFactory@1ea5c8f6
			at org.opendaylight.controller.config.manager.impl.ConfigTransactionControllerImpl.copyExistingModule(ConfigTransactionControllerImpl.java:189)
			at org.opendaylight.controller.config.manager.impl.ConfigTransactionControllerImpl.copyExistingModulesAndProcessFactoryDiff(ConfigTransactionControllerImpl.java:110)
			at org.opendaylight.controller.config.manager.impl.ConfigRegistryImpl.beginConfigInternal(ConfigRegistryImpl.java:191)

		java.util.ConcurrentModificationException
			at java.util.HashMap$HashIterator.nextEntry(HashMap.java:922)[:1.7.0_65]
			at java.util.HashMap$KeyIterator.next(HashMap.java:956)[:1.7.0_65]
			at java.util.AbstractCollection.toArray(AbstractCollection.java:195)[:1.7.0_65]
			at org.apache.karaf.features.internal.FeaturesServiceImpl.listInstalledFeatures(FeaturesServiceImpl.java:754)[24:org.apache.karaf.features.core:3.0.1]
			at Proxy0810500d_6b67_43e5_bf83_eba0f2f7b203.listInstalledFeatures(Unknown Source)[:]


		org.sonatype.aether.resolution.ArtifactResolutionException: Could not find artifact org.eclipse.equinox:region:jar:1.0.0.v20110506 in defaultlocal (file:/C:/...)
				at org.sonatype.aether.impl.internal.DefaultArtifactResolver.resolve(DefaultArtifactResolver.java:538)
				at org.sonatype.aether.impl.internal.DefaultArtifactResolver.resolveArtifacts(DefaultArtifactResolver.java:216)
				at org.sonatype.aether.impl.internal.DefaultArtifactResolver.resolveArtifact(DefaultArtifactResolver.java:193)
				at org.sonatype.aether.impl.internal.DefaultRepositorySystem.resolveArtifact(DefaultRepositorySystem.java:286)


NOTE: The last exception on org.eclipse.equinox:region:jar can be seen when building locally. Exception is not seen when project is being built by jenkins. 

Advance Topic 
===========================


How to create a configfile project for Karaf
----------------------------------------------------

In order to be able to reference your <configfile> you need to have it available as a maven accessible artifact. Not in a jar, but the file itself.

For that you will need a new maven project for your config file.

**Create a configfile project**

Run the opendaylight-configfile-archetype

	mvn archetype:generate -DarchetypeGroupId=org.opendaylight.controller -DarchetypeArtifactId=opendaylight-configfile-archetype -DarchetypeRepository=http://nexus.opendaylight.org/content/repositories/opendaylight.snapshot/ -DarchetypeCatalog=http://nexus.opendaylight.org/content/repositories/opendaylight.snapshot/archetype-catalog.xml

You will be prompted for

	groupId: (enter your project groupId)
	artifactId: ${repoName}-config
	version: (version of your project)
	package: (accept default)
	repoName: (your projects repoName, examples: controller, yangtools, openflowplugin)


for example 

	Define value for property 'groupId': : org.opendaylight.controller
	Define value for property 'artifactId': : loadbalancer-config       
	Define value for property 'version':  1.0-SNAPSHOT: : 
	Define value for property 'package':  org.opendaylight.controller: : 
	Define value for property 'repoName': : loadbalancer 

**Edit the ${repoName}-config/pom.xml**

Edit the

	${repoName}-config/pom.xml

find the TODO items, and do them :) 

example at _*distribution-karaf-0.2.0-Helium/system/org/opendaylight/l2switch/features-l2switch*_  

###LOG

Logging in ODL container is done via Logback. Comprehensive documentation is available at http://logback.qos.ch/documentation.html

By default logging messages are appended to stdout of the java process and to file logs/opendaylight.log . When debugging a problem it might be useful to increase logging level:

<logger name="org.opendaylight.controller" level="DEBUG"/>

Logger tags can be appended under root node <configuration/>. Name of logger is used to select all loggers to which specified rules should apply. Loggers are usually named after class in which they reside. The example above matches all loggers in controller - they all are starting with org.opendaylight.controller . There are 5 logging levels: TRACE,DEBUG,INFO, WARN, ERROR. Additionally one can specify which appenders should be used for given loggers. This might be helpful to redirect certain log messages to another file or send them to syslog or over SMTP. See logback documentation for details. 

Reference
==========================
[1](https://wiki.opendaylight.org/view/Karaf:Step_by_Step_Guide)
[2](https://wiki.opendaylight.org/view/Runtime:Karaf_Features_Guidelines)
[3](https://wiki.opendaylight.org/view/Karaf:How_to_create_a_configfile_project_for_Karaf)
