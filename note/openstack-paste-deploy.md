上一节中梳理了Python Paste中Deploy机制的概念，这一节就做一点小小的实践。首先，我们举一个使用了Deploy的例子，这个就是OpenStack的 Quantum组件的WSGI部分。我们先来看关于WSGI部分的配置文件，以ini后缀，那么就是api-paste.ini文件，决定了API的处理 流程。我加入了适当的注释。
1 OpenStack Quantum配置文件api-paste.ini

[composite:quantum]
use=egg:Paste#urlmap
/:quantumversions
/v2.0:quantumapi_v2_0 
#使用composite分解机制，composite使用了usrlmap，xxxxx/xxx的API交给quantumversions处理。xxxx/v2.0/xxxx的API交给quantumapi_v2_0处理。

[composite:quantumapi_v2_0]
use=call:quantum.auth:pipeline_factory 
noauth=extensions quantumapiapp_v2_0 
keystone=authtoken keystonecontext extensions quantumapiapp_v2_0
#quantumapi_v2_0 依然是一个分解组件，使用了quantum.auth模块下的pipeline_factory，对于这个factory，传递了两个参数，一个是noauth,一个是keystone。

[filter:keystonecontext]
paste.filter_factory=quantum.auth:QuantumKeystoneContext.factory
#对于keystonecontext，实际上是一个过滤器，使用了quantum.auth模块下的类的QuantumKeystoneContext的factory函数

[filter:authtoken]
paste.filter\_factory=keystone.middleware.auth\_token:filter_factory 
auth_host=127.0.0.1
auth_port=35357
auth_protocol=http 
admin_tenant_name=%SERVICE_TENANT_NAME%
admin_user=%SERVICE_USER%
admin_password=%SERVICE_PASSWORD%#定义了另外一个filter

[filter:extensions]
paste.filter\_factory=quantum.extensions.extensions:plugin\_aware_extension_middleware_factory
#定义了另外一个filter,这个filter是为了支持扩展quantum api的

[app:quantumversions]
paste.app\_factory=quantum.api.versions:Versions.factory
#核心的app部分，使用工厂函数，将app指向python代码。app_factory表明这个函数接收一系列参数，[DEFAULET]以及[app:]下面的，本部分本section没有参数，并返回一个函数对象。

[app:quantumapiapp_v2_0]
paste.app_factory=quantum.api.v2.router:APIRouter.factory#同上


我们来总结一下，整个Quantum处理api的流程如下,其中，强调的部分为函数代码，其他为配置文件中的section部分。

对于路径为/类的API——quantumversions处理——调用quantum.api.versions:Version类的factory函数处理。

对于路径为/2.0类的API——quantumapi_v2_0处理——调用quantum.auth中的pipeline\_factory处理,同时传递了两个参数noauth和keystone,类型为字典。 这个pipeline_factory 中会读取另外一个变量CONF.auth（来自另外一个配置文件，不考虑），选择采用的认证方式，然后选择noauth或者keystone，并读取参数的值。 那么，就有两种情况：

noauth: 应用将会先经过extensions这个filter处理——调用了quantum.extensions.extensions:plugin\_aware\_extension\_middleware\_factory，用来处理扩展api请求，这是第一次包装——quantumapiapp_v2_0，这才是实际的WSGI应用，调用了quantum.api.v2.router:APIRouter.factory，并处理返回结果。

keystone：和上面类似，不同的是多了几个filter,authtoken keystonecontext extensions quantumapiapp\_v2_0,并且在每个filter中可能还会有参数传递给这个fliter。

总的来说，通过pipeline装载多个filter,将最基本的app— APIRouter，层层包装，使其变为一个具有处理认证，扩展API等的应用（逻辑上看），filter的好处就是可以自定义，比如可以不要认证功能，这比写一个囊括全部功能的应用明显要好的多。

###2 代码实践
####2.1 配置文件

[DEFAULT]
company=UESTC 
school=CommuicationandInformation

[composite:common]
use=egg:Paste#urlmap
/:showversion
/detail:showdetail

[pipeline:showdetail]
pipeline=filter1 filter2 showstudetail

[filter:filter1]
#filter1 deal with auth,read args below
paste.filter\_factory=python_paste:AuthFilter.factory 
user=admin 
passwd=admin

[filter:filter2]
#filter2 deal with time,read args below
paste.filter\_factory=python\_paste:LogFilter.factory
#all value is string
date=20121120

[app:showstudetail]
name=wangchang 
age=23
paste.app\_factory=python_paste:ShowStuDetail.factory

[app:showversion]
version=1.0.0


从配置文件可以看出，这个程序会有如下操作： *对于http://localhost/的访问，会调用showversion这个应用，应用读取ini文件中的version值并返回。__注意，在ini中的所有值都是字符串。

对于http://localhost/detail的访问，会先经过filter1以及filter2，这两个filter分别处理认证和LOG信息， 他们会读取ini配置中的用户信息以及时间。最后才是交给showstudetail处理，showstudetail会读取ini中的用户信息并返回。 __注意，使用多个filter的时候需要使用pipeline方式。


####2.2 代码

	import sys
	import os
	import webob 
	from webob import Request
	from webob import Response
	#from webob import environ
	from paste.deploy import loadapp
	from wsgiref.simple_server import make_server
	from pprint import pprint

	class AuthFilter(object):
		'''filter1,auth     
		1.factory read args and print,return self instance        
	 	2.call method return app         
		3.AuthFilter(app)      
		'''     
		def__init__(self,app):         
			self.app=app      	
			def__call__(self,environ,start_response):         
				print'this is Auth call filter1'         
			#pass environ and start_response to app         
		returnself.app(environ,start_response)     

		@classmethod     
		def factory(cls,global_conf,**kwargs): 
		'''global_conf and kwargs are dict'''  
		   print '######filter1##########'      
		   print 'global_conf type:',type(global_conf)      
		   print '[DEFAULT]',global_conf         
		   print 'kwargs type:',type(kwargs)      
		   print 'Auth Info',kwargs       
		   return AuthFilter

	class LogFilter(object):     
			'''      filter2,Log      '''
		def __init__(self,app):      
			self.app=app      	
			def __call__(self,environ,start_response):         
				print'This is call LogFilter filter2'         
			return self.app(environ,start_response)     

		@classmethod     
		def factory(cls,global_conf,**kwargs):         
			#print type(global_conf)         
			#print type(kwargs)         
			print '######filter2###########'         
			print '[DEFAULT]',global_conf          
			print 'Log Info',kwargs          
			return LogFilter

	class ShowStuDetail(object):     
		'''      app      '''     
		def__init__(self,name,age):         
			self.name=name          
			self.age=age      

		def__call__(self,environ,start_response):         
			print'this is call ShowStuDetail'         
			#pprint(environ)         
			#pprint environ         
			start_response("200 OK",[("Content-type","text/plain")])         
							content=[]         
							content.append("name: %s age:%s\n"%(self.name,self.age))         
							content.append("**********WSGI INFO***********\n")         
							fork,vinenviron.iteritems():             
							content.append('%s:%s \n'%(k,v))         
			return['\n'.join(content)]#return a list     

		@classmethod     
		def factory(cls,global_conf,**kwargs):         
			#self.name = kwargs['name']         
			#self.age = kwargs['age']         
			return ShowStuDetail(kwargs['name'],kwargs['age'])

	class ShowVersion(object):     
		'''      app      '''     
		def__init__(self,version):         
			self.version=version      
	
		def__call__(self,environ,start_response):         
			print'this is call ShowVersion'         
			req=Request(environ)         
			res=Response()         
			res.status='200 OK'         
			res.content_type="text/plain"         
			content=[]         
			#pprint(req.environ)         
			content.append("%s\n"%self.version)        
			content.append("*********WSGI INFO*********")         
			for k,v in environ.iteritems():             
				content.append('%s:%s\n'%(k,v))         
				res.body='\n'.join(content)         
			return res(environ,start_response)     

		@classmethod     
		def factory(cls,global_conf,**kwargs):        
			#self.version = kwargs['version']         
			return ShowVersion(kwargs['version'])

	if__name__=='__main__':    
		config="python_paste.ini"   
		appname="common"    
		wsgi_app=loadapp("config:%s"%os.path.abspath(config),appname)    
		server=make_server('localhost',7070,wsgi_app)    
		server.serve_forever()   
		pass

在程序中，对于web请求的处理，我分别采用了webob和普通WSGI定义的方式，后续我会补上webob的使用。

####2.3 结果

先从服务端结果分析一下调用流程：
Ubuntu:~/python$ python python_paste.py
######filter1##########
global_conf type:<type'dict'>
[DEFAULT]
{'school':'Commuication and Information','company':'UESTC','here':       
'/home/wachang/python','__file__':'/home/wachang/python/python_paste.ini'}

kwargs type:<type'dict'>
AuthInfo{'passwd':'admin','user':'admin'}

######filter2###########
[DEFAULT]
{'school':'Commuication and Information','company':'UESTC','here':   
'/home/wachang/python','__file__':'/home/wachang/python/python_paste.ini'}

LogInfo{'date':'20121120'}

以上是PD载入应用时，调用filter的factory方法输出的结果，可以看到，此读出了相关的变量信息。
this is call ShowVersionlocalhost--[21/Nov/201213:23:40]"GET / HTTP/1.1"2002938
this is call ShowVersionlocalhost--[21/Nov/201213:23:40]"GET /favicon.ico HTTP/1.1"2002889
以上是接收/请求，因为没有使用filter，直接交予showversion应用处理，并返回。
this is Auth call filter1
This is call LogFilterfilter2 
this is call ShowStuDetail localhost--[21/Nov/201213:24:23]"GET /detail HTTP/1.1"2003016thisiscallShowVersionlocalhost--[21/Nov/201213:24:24]"GET /favicon.ico HTTP/1.1"2002889filter的调用时重点啊，可以看到，调用的顺序和pipeline中一样。最后才调用应用。
需要继续折腾的话，就看看webob:do-it-yourselfrself


