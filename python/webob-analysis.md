
BaseRequest
=======================

获取参数 
	url_encoding
	scheme
	method
	http_version
	content_length
	remote_user
	remote_addr
	query_string，
	server_name
	server_port
	script_name
	path_info
	accept
	accept_charset
	accept_encoding
	accept_language
	authorization
	if_match
	if_none_match
	date
	if_modified_since
	if_unmodified_since
	if_range
	max_forwards
	pragma
	range
	referer
	referrer
	user_agent
	
def __init__(self, environ, charset=None, unicode_errors=None,decode_param_names=None, **kw)

* 参数
	environ : \[dict]，环境参数
	kw  : \[dict]，self.method 也可以来自 kw。 key 必须是 self.__class__ 的属性。

* 操作

* 返回

def POST(self)

* 参数
	environ : \[dict]，环境参数
	kw  : \[dict]，self.method 也可以来自 kw。 key 必须是 self.__class__ 的属性。

* 操作
	利用cgi 提取所有表单请求，保持在 vars 中
	fs = cgi.FieldStorage(fs_environ)
	vars = MultiDict.from_fieldstorage(fs)
	f = FakeCGIBody(vars)
	self.body_file = io.BufferedReader(f)
	
	
* 返回
	vars (dict)
	
def GET(self)
