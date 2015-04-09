  webpy        flask
1. 灵活性
 不可配置 	   可配置

2. 可扩展性
 中间件
 
3. 请求参数解析

  BaseReuqest
 
 
将url和 request 前都可以执行一些函数
 
变量管理
    
	变量管理类  LocalStack 和 ProxyStack 中

LocalStack
	
def push(obj)
	存储在 Local.stack 属性
	
def pop()
	删除 Local.stack 最后一个元素
	



 

app.py 

本文将所有都围绕此接口而设计
def wsgi_app(self, environ, start_response)
	
	ctx = self.request_context(environ) --> RequestContext(self, environ)
	response = self.full_dispatch_request()
	response(environ, start_response)


def full_dispatch_request(self)

	self.try_trigger_before_first_request_functions()
	self.preprocess_request()  OR self.dispatch_request()
	response = self.make_response(rv)
	response = self.process_response(response)
	
	return response
	
def try_trigger_before_first_request_functions(self)
	
	如果不是第一次请求，执行如下函数
	for func in self.before_first_request_funcs:
	 	func()

def preprocess_request()

	URL预处理，默认self.url_value_preprocessors = {}
	funcs = self.url_value_preprocessors.get(None, ()) 
	if bp is not None and bp in self.url_value_preprocessors:
		funcs = chain(funcs, self.url_value_preprocessors[bp])
	for func in funcs:
		func(request.endpoint, request.view_args)
		
	
	执行 request 前的函数调用，默认 self.before_request_funcs = {}
	funcs = self.before_request_funcs.get(None, ()) 
	if bp is not None and bp in self.before_request_funcs:
		funcs = chain(funcs, self.before_request_funcs[bp])
	for func in funcs:
		rv = func()
		if rv is not None:
			return rv

def dispatch_request(self)
	
	执行 self.view_function中的函数
	req = _request_ctx_stack.top.request = Request
	rule = req.url_rule
	return self.view_functions[rule.endpoint](**req.view_args)
	
def make_response(self, rv)

	根据 rv 的类型进行不同的应答方式, self.response_class = Response
	
	rv = self.response_class(rv, headers=headers,status=status_or_headers)
	OR
	rv = self.response_class.force_type(rv, request.environ)

	return rv

def process_response(self, response)
	
	调用请求后的处理函数
	ctx = _request_ctx_stack.top
	bp = ctx.request.blueprint
	funcs = ctx._after_request_functions
	funcs = chain(funcs, reversed(self.after_request_funcs[bp]))
	funcs = chain(funcs, reversed(self.after_request_funcs[None]))
	for handler in funcs:
		response = handler(response)
	return response
	
---------------------------------------------------------------------	

def run(self, host=None, port=None, debug=None, **options)

	调用 werkzeug.serving.run_simple(host, port, self, **options)

	Q: 如果 debug 调用 bool(debug), 可以更优雅处理。

def register_blueprint(self, blueprint, **options)

	全部新增加 module 都维护在 self.blueprints 中
	注册一个module, module需要有name属性和register方法

def add_url_rule(self, rule, endpoint=None, view_func=None, **options)j

	methods 从 options 或 view_func.methods 或 ('GET')
	required_methods 从 view_func
	provide_automatic_options 从 view_func.provide_automatic_options 或 methods.OPTIONS 
	methods 取 methods required_methods 并集

	rule = Rule(rule, methods, options)
	Map.add(rule)
	
def route(self, rule, **options)

	add_url_rule 的装饰器
	
	
	
http 参数解析过程

    所有参数维护在全局变量 _request_ctx_stack 中，每次进入的时候，将 RequestContext 压入 
    _request_ctx_stack，退出的时候，调用 Flask.do_teardown_request，Flask.request_class.close()

	Flask.request.context(self,environ)
	
	RequestContext(app, environ)
		app = Flask
		request = Flask.request_class = Request
		url_adapter = Flask.app.create_url_adapter(request)
	
	RequestContext.push() 将 RequestContext 压入 _request_ctx_stack.top
	RequestContext.pop() 调用 Flask.do_teardown_request，Flask.request_class.close()
	

	
	
cli.py

click.Group(app_option, debug_option).main(self, args, kwargs)

	args = sys.args[1:]
	kwargs[prog_name] ="python -m [module_name]"
	kwargs[obj] = ScriptInfo(create_app=self.create_app)
	kwargs[auto_envvar_prefix] = "FLASK"

ctx = click.Group.make_context(kwargs[prog_name],args)
FlaskGroup.invokecomand(ctx)




run_simple(host, port, app, use_reloader=reload,use_debugger=debugger, threaded=with_threads)

	use_reloader, use_debugger, threaded 在命令行可配置
	app = DispatchingApp(info.load_app)
	
	

	


	
	

	
RequestContext()

def __init__(self, app, environ, request = None)
	app = Flask
	self.environ = environ
	self.request = Request
	self.url_adapter = app.create_url_adapter(self.request)
	
	
	
werkzeug 
===============================

http.py

http 请求参数编解码，处理。

url.py

url 处理

wsgi.py

wsgi 相关参数解析

datastructures.py

辅助的数据结构

routing.py

url 和 app 路由

formparser.py

表单解析


字符处理原则：进入时编码，返回时解码

wrappers.py

BaseRequest()
----------------------------

def __init__(self, environ, populate_request=True, shallow=False)

	默认所有的存储在 self.environ['werkzeug.request'] = self
	
def url_charset(self)

	获取 charset

@classmethod
def from_values(cls, *args, **kwargs)

	模拟请求

@classmethod
def application(cls, f)

	一个装饰器，返回迭代器，f(args1)(args2)
	其中 args1 为倒数第二个参数之前参数，args2是倒数两个参数

def _get_file_stream(self, total_content_length, content_type, filename=None,content_length=None)
	
	用 BytesIO 或 tempfile.TemporaryFile 读写

@property
def want_form_data_parsed(self)

	environ['CONTENT_TYPE'] 是否为 0 

def make_form_data_parser(self)

	初始化解析表单数据类
	调用 self.form_data_parser_class(self._get_file_stream,
		self.charset,
		self.encoding_errors,
		self.max_form_memory_size,
		self.max_content_length,
		self.parameter_storage_class))
		
def _load_form_data(self)

	提取表单数据
	主要接口 FormDataParser.parse()
	
def _get_stream_for_parsing(self)

	如果 self 有 _cached_data 属性，调用 BytesIO, 否则返回 self.stream
	
def close(self)
	
	关闭 iter_multi_items（file）中 

@cached_property
def stream(self)

	安全地从 WSGI 环境读输入流，不用担心超出边界
	调用 get_input_stream()

@cached_property
def args(self)

	 解析 url 参数，默认存储在 ImmutableMultiDict, 返回 ImmutableMultiDict 对象

def get_data(self, cache=True, as_text=False, parse_form_data=False)

	获取 _cached_data 数据，如果 self._cached_data 为真，直接返回。如果为假，调用
	rv = self.stream.read() ，返回 rv
	
@cached_property
def form(self)

	获取表单数据
	调用 self._load_form_data()，返回 self.form

@cached_property
def values(self)

	联合 form 和 args 的数据
	返回 CombinedMultiDict 对象
	


	


IO 类文件读写

cString
tempfile
BytesIO

	
