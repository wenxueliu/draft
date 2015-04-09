




application
============================

通过 ThreadLocal 共享数据。首先提取 path, query, 初始化 env, 清除 ThreadLocal 数据，设置 ThreadLocal，调用 map 映射的方法，调用中间件。返回应答。当运行 run 方法后，开启 httpserver，接受请求，应答。


__init__(mapping=(), fvars={}, autoreload=None)

add_processor(self,)

request(self, localpart='/', method='GET', data=None,host="0.0.0.0:8080", headers=None, https=False, **kw)

* 从 localpart 得到 path, query
* env = kw["env"] or {}
* env = dict(env, HTTP_HOST=host, REQUEST_METHOD=method, PATH_INFO=path, QUERY_STRING=query, HTTPS=str(https))
* 从 headers 中取出 key-value 对加入 env
* 对于非 HEAD 和 GET 方法，对 data 参数处理。env['wsgi.input'] = StringIO.StringIO(data)
* 调用 wsgifunc()
* 返回 response


wsgifunc(self, *middleware):

* middleware 用于增加一些中间件，其中中间件接受一个函数迭代器，迭代器为 wsgi(env, start_resp)，所以中间件应该是按照某种你期望的顺序来执行。
* wsgi(env, start_resp)  
	清除 ThreadLocal 
	设置 ThreadLocal数据 ctx
	调用 self.processor 中函数, 比如 self.processor = [ proc1, proc2, proc3] 实际调用为 proc1(proc2(proc3(self.handle)))
	status, headers = web.ctx.status, web.ctx.headers
	start_resp(status, headers)
	
handle()

* mapping 匹配，调用对应的方法。

run()
	wsgirun(wsgifunc(**middleware))
	httpserver.runsimple(func,server_address)
	wsgiserver.CherryPyWSGIServer(server_address, func)


session
============================

__init__(self, app, store, initializer=None)

process(handler)
-------------------

* 清除旧数据
* 认证session_id, 加载 session_id
* 初始化 initializers
* 设置cookie, 将线程数据选择合适方式保存



wsgi server 最简描述
============================
 一个 ThreadPool 维护一组 HttpServer（默认 5 个）
 
 ThreadPool start() 开启 5 个 WorkerThread（线程），每个 WorkerThread run()(死循环) 从 ThreadPool 维护的队列取出一个 conn(HttpConnection), 调用 conn.commuincate(), commuincate() 中接受请求、应答。 由于 communicate() 是死循环，所以这个连接一直占有这个现场，当前连接 close 之后，当前WorkerTread 线程继续从队列中去新的连接。因此，默认支持 5 个连接，新的连接会被阻塞在队列中，直到有新的空闲线程。
 


HttpServer
============================
self.requests = ThreadPool()
self.socket = socket.socket()

start()
-----------------------
* bind_addr 为 (host port) OR host:port
* socket 语义集合
	socket.getaddrinfo()
	socket.socket()
	socket.setsockopt()
	socket.bind()
	self.socket.listen()

* ThreadPool().start()

* tick()
	self.ready = True
	while self.ready
		socket.accept()
		conn = HttpConnection()
		ThreadPool().put(conn)
	
	
stop()
-----------------------
* self.socket = None
* threadPool.stop(timeout)



HttpConnection
=======================
self.req = HttpRequest

communicate()
-----------------------
* self.req.parse_request()
* self.req.respond()
	
	
HttpRequest
=======================

parse_request()
------------------------

* read_request_line()
	method, uri, protocol = rfile.readline()
	scheme, authority, path = parse_request_uri(uri)
	
	初始化 self.request_protocol  self.response_protocol self.path self.qs self.uri self.method self.scheme
	
* read_request_headers()
	read_headers()
	self.sconn.wfile.sendall()
	
	
respond()
------------------------

	ChunkedRFile OR KnownLengthRFile
	self.server.gateway().respond() = WSGIGateWay_10().respond()
	self.send_headers()
	self.conn.wfile.sendall("0\r\n\r\n")
	
read_request_line()





ThreadPool
========================

self.server = HttpServer

start()
------------------------
for i in range(min)
	self._threads.append(WorkerThread(self.server))
for worker in self._threads:
	worker.start()


WorkerThread
========================

run()
------------------------
	while True
		conn = self.server.request.get()
		conn.commuincate()

WSGIGateWay
========================

respond()
------------------------
respond = self.req.server.wsgi_app(self.env, self.start_response)
for rs in respond:
	self.write()

