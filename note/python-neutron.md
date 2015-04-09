iptables
ip
eventlet
greenlet
openvswitch
arping
route

resources
action
request


###Route:

###Mapper:

def connection(*args, **kwargs):
    routename = args[0] or (None,args[0])
    route = routes.route.Route(args,kwargs)
    route.name = routename
    self.matchlist=[route]
    self.maxkeys[route.maxkeys]=[route]


neutron server
==========================================

代码
* `etc/init.d/neutron-server`  这是开启 sever 脚本范例，值得参考
* `neutron/server/__init__.py`
* `neutron/service.py`
* `neutron/wsgi.py`

功能很简单：
* 启动 neutron-api 服务
* 开启日志
* 加载配置api-paste.ini，
如果启动 neutron 失败，将会切换到 quantum。

返回 wsgi.Server 对象
app = paste.deploy.loadapp()

	neutron_server = neutron.service.serve\_wsgi(neutron.service.NeutronApiService)
	-->	service = neutron.service.NeutronApiService.create()
		|-->service = neutron.service.NeutronApiService(app_name)
		|	service.start()
		|	wsgi_app = neutron.service._run_wsgi(app_name)
		|	|-->app = config.load_paste_app(app_name) : load the api-paste.ini file
		|	|	server = neutron.wsgi.Server("Neutron")
		|	|	server.start(app,bind_port,bind_host,workers=0)
		|	|	--> workers < 1
		|	|		_server = eventlet.GreenPool(1000).spawn(_run,app,_socket)
		|	|		: _run = eventlet.wsgi.server(socket,app,custom_pool=self.pool,log=logging.WritableLogger(LOG))
        |   |       : _socket = _get_socket(bind_host,bind_port,backlog=backlog)
        |   |       --> self._run(app,_socket)
		|	|	--> workers >= 1
		|	|		_launcher = neutron.openstack.common.service.ProcessLauncher()
		|	|		_server = neutron.wsgi.WorkerService(neutron.wsgi.Server, application)
		|	|		_launcher.launch_service(_server,workers)
		|	|		--> wrap = neutron.openstack.common.service.ServiceWrapper(_server, workers)
		|	|			_launcher._start_child(wrap) : a child pid in linux
		|	|			--> _launcher._child_process(wrap.service)
		|	|				-->	eventlet.hubs.use_hub()
		|	|				  	eventlet.spawn\_n(\_pipe_watcher)
		|	|					launcher = neutron.openstack.common.service.Launcher()
		|	|					launcher.run_service(wrap.service)
		|	|					-->	wrap.service.start()
		|	|						= 	_server.start()
		|	|						=	WorkerService.start()
		|	|						=	neutron.wsgi.Server.pool.start()
		|	|						=	eventlet.GreenPool(1000).spawn(_run,app,_socket)
		|	|					--> wrap.service.wait() 
		|	|						= 	_server.wait() 
		|	|						= 	WorkerService.wait() 
		|	|						= 	neutron.wsgi.Server.pool.waitall()
		|	|						= 	eventlet.GreenPool(1000).waitall()
		|	|						
		|	|   wsigi_app = server
    	neutron_server = service	
	neutron_server.wait()
	-->	neutron.service.NeutronApiService.wait()
		--> wsigi_app.wait()
			-->	neutron.wsgi.Server("Neutron")
				--> if _launch()
					_launcher.wait()
				--> eventlet.GreenPool(1000).waitall()

由上面代码可知，绕了很多弯子，实际上调用的是 eventlet.GreenPool(1000).spawn(\_run,app,\_socket),而这个函数实际上是调用 \_run\_app(app, _socket)

总结：记载配置文件api-paste.ini, 启动日志。等待用户的请求。

neutron-api 调用流程
================================================
[paste.deploy](http://pythonpaste.org/deploy/)
[eventlet.wsgi](http://eventlet.net/doc/modules/wsgi.html)
[route](http://routes.readthedocs.org/en/latest/)

neutron-server 启动后，由于配置都已经加载好了，日志开启了，就坐等用户的请求，对于请求与应答 主要是 neutron-api 的工作了。

首先，找到配置文件，到/etc/neutron/看到如下文件

	etc/
	|-- api-paste.ini       neutron-api 
	|-- dhcp_agent.ini      neutron-dhcp-agent
	|-- fwaas_driver.ini    
	|-- init.d
	|-- l3_agent.ini        neutron-l3-agent
	|-- lbaas_agent.ini     neutron-lbass-agent
	|-- metadata_agent.ini  neutron-metadata-agent
	|-- metering_agent.ini  neutron-metering-agent
	|-- neutron
	|-- neutron.conf        全局配置
	|-- policy.json         策略控制
	|-- quantum -> neutron
	|-- rootwrap.conf
	|-- services.conf       neutron-server
	`-- vpn_agent.ini       neutron-vpn-server

从这里看到，各个servcie，agent，api的配置文件。如果你熟悉 paste.deploy 就可以找到相应的入口函数。
比如 neutron-api，通过解析配置文件，知道调用了这个函数 neutron.api.v2.router:APIRouter.factory
即，neutron/api/v2/router.py 中的APIRouter.factory()。

下面这个函数字字珠玑，原理很简单，http简单知识 + route 这个库的理解。

    def __init__(self, **local_config):
        mapper = routes_mapper.Mapper() 
        plugin = manager.NeutronManager.get_plugin()
        ext_mgr = extensions.PluginAwareExtensionManager.get_instance()
        ext_mgr.extend_resources("2.0", attributes.RESOURCE_ATTRIBUTE_MAP)

        col_kwargs = dict(collection_actions=COLLECTION_ACTIONS,
                          member_actions=MEMBER_ACTIONS)

        def _map_resource(collection, resource, params, parent=None):
			#如下三个选项可能是后来加上去的。
            allow_bulk = cfg.CONF.allow_bulk
            allow_pagination = cfg.CONF.allow_pagination
            allow_sorting = cfg.CONF.allow_sorting
			
			# controller.resource(request) 是一个 HTTP 的 request 和 response 的实现
			#请求的全部参数都可以从这个请求的环境变量 wsgiorg.routing_args 中得到
			#args = request.environ.get('wsgiorg.routing_args')[1]
			#调用 method = neurton.api.v2.base.Controller.args['action']
			#resault = method(request=request,**args)
			#body = serializer.serialize(result)
			#webob.Response(request=request, status=status,content_type=content_type,body=body)


            controller = base.create_resource(
                collection, resource, plugin, params, allow_bulk=allow_bulk,
                parent=parent, allow_pagination=allow_pagination,
                allow_sorting=allow_sorting)

            path_prefix = None
            if parent:
                path_prefix = "/%s/{%s_id}/%s" % (parent['collection_name'],
                                                  parent['member_name'],
                                                  collection)
            mapper_kwargs = dict(controller=controller,
                                 requirements=REQUIREMENTS,
                                 path_prefix=path_prefix,
                                 **col_kwargs)
            return mapper.collection(collection, resource,
                                     **mapper_kwargs)

        mapper.connect('index', '/', controller=Index(RESOURCES))
        for resource in RESOURCES:
            _map_resource(RESOURCES[resource], resource,
                          attributes.RESOURCE_ATTRIBUTE_MAP.get(
                              RESOURCES[resource], dict()))

        for resource in SUB_RESOURCES:
            _map_resource(SUB_RESOURCES[resource]['collection_name'], resource,
                          attributes.RESOURCE_ATTRIBUTE_MAP.get(
                              SUB_RESOURCES[resource]['collection_name'],
                              dict()),
                          SUB_RESOURCES[resource]['parent'])

        super(APIRouter, self).__init__(mapper)

简单总结，就是route的三步曲
	mapper = routes.Mapper() 
	mapper.collection(collection,resource,kwargs)
	mapper.connect(collection,resource, controller,action)


neutron plugin
=========================================================
1. 加载插件，neutron.manage.py
	加载 core_plugin 选项中指定的插件，初始化 service_plugin
	core_plugin = neutron.plugins.openvswitch.ovs_neutron_plugin.OVSQuantumPluginV2

	每个插件必须定义 supported_extension_aliases 属性
	
	如果 supported_extension_aliases 中有如下属性
	#maps extension alias to service type
	EXT_TO_SERVICE_MAPPING = { 
		'dummy': DUMMY,
		'lbaas': LOADBALANCER,
		'fwaas': FIREWALL,
		'vpnaas': VPN,
		'metering': METERING,
		'router': L3_ROUTER_NAT
	}                            
	则优先加载到 service_plugin。 

	service_plugin = { 	"CORE": self.plugin(),
					 }

	比如 openvswitch 
	supported_extension_aliases = ["provider", "external-net", "router",
                                    "ext-gw-mode", "binding", "quotas",
                                    "security-group", "agent", "extraroute",
                                    "l3_agent_scheduler",
                                    "dhcp_agent_scheduler",
                                    "extra_dhcp_opt",
                                    "allowed-address-pairs"]
  
	service_plugin 必须包含 L3_ROUTER_NAT 关键字
	
2. 加载 service\_plugins 选项中指定的插件, 继续初始化 service_plugin
   service_plugins 可以加载扩展自定义的插件

3. 如果 plugin 有 agent_notifiers 会更新它的 agent_notifiers 属性 .
	

dhcp-agent
-------------------
网络的信息 network subnet port 的信息保存在三个地方
1. NetworkCache这个类中，在 dhcp_agent 初始化的时候从 dnsmasq 获取后建立,
2. dhcp_conf 这个文件夹里面
3. dnsmasq 维护



api/rpc/agentnotifiers/dhcp_rpc_agent_api.py

插件必须支持的方法
	get_network(adminContext, network_id)
	schedule_network(adminContext, network)
	agent = get_dhcp_agents_hosting_networks : agent is list and must have isactive attribute.

dhcp-agent 主要rpc方法
    VALID_RESOURCES = ['network', 'subnet', 'port']
    VALID_METHOD_NAMES = ['network_create_end',
                          'network_update_end',
                          'network_delete_end',
                          'subnet_create_end',
                          'subnet_update_end',
                          'subnet_delete_end',
                          'port_create_end',
                          'port_update_end',
                          'port_delete_end']
   						  agent_updated
	这些方法的 worker 都在 neutron/agent/dhcp_agent.py 中实现了,@utils.synchronized 
是保证一个进程内多个线程只有一个运行的装饰器。

	PS:变量VALID_METHOD_NAMES 应该放在 /neutron/common/contants.py

对于Openvswitch 插件，除了 network.delete.end 调用 rpc.fanout_cast()， 其他都调用了 rpc.cast() 方法

neutron/agent/dhcp_agent.py
-------------------------------------------------
class NetworkCache(object): 建立网络缓存
	self.cache : dict of {network.id : network }
    self.subnet_lookup : dict of {subnet.id : network.id }
	self.port  : dict of { port.id : network.id }

	port.network_id = network.id
	network.ports : list of ports which has id attribute
	network.subnets : list of subnets which has id attribute

class DhcpPluginApi(proxy.RpcProxy) : rpc proxy.call()调用的简单封装
		get_active_networks_info
		get_network_info
		get_dhcp_port
		create_dhcp_port
		update_dhcp_port
		release_dhcp_port
		release_port_fixed_ip
	问题: 这些 rpc 的 worker 在哪里？

class DhcpAgent(manager.Manage)
	def sync_state(self)
		1. 从 dhcp_conf 获取 know_network
        2. 从 plugin_rpc 获取 active_network 
        3. 从 know_network 除去不在 active_network 中的network，删除之
		4. 对于 active_network ，调用 safe_configure_dhcp_for_network(network)
	
   
	def safe_configure_dhcp_for_network(networks) # 这是整个 dhcp_agent.py 中最复杂的函数
		主要是遍历网络，将子网 enable_dhcp == True 增加到 NetworkCache() 
		1. 遍历 networks 的子网，如果有子网 enable_dhcp == False, 继续遍历
		2. 如果 network.subnet.enable_dhcp == True， # networks: list of network
				如果 networks.id 在 /proc/[dnsmasq_pid]/cmdline 中, 重启网络
				如果 network.enable_dhcp == True, 调用 dnsmasq 命令,之后将 networks 放入 NetworkCache() 
	
	

	def disable()
		kill -9 [dnsmasq_pid], 删除配置文件, network 的子网
				

	dhcp_agent.safe_configure_dhcp_for_network(network)
	--> dhcp_agent.configure_dhcp_for_network(network)
		--> for subnet in network
			--> if subnet.enable_dhcp
				--> dhcp_agent.call_driver("enable",network)
	    linux.dhcp.DnsMasq = dhcp_agent.call_driver
	--> linux.dhcp.DnsMasq.enable() 
		--> interface_name = device_manage.setup()
            if linux.dhcp.DnsMasq.active(): linux.dhcp.DnsMasq.restart()
            else linux.dhcp.DnsMasq._enable_dhcp(): linux.dhcp.DnsMasq.spawn_process()
				--> else break 
	

class DhcpAgent
	1. 启动 num_sync_threads 个绿色线程。
	2. 从 dhcp_confs 目录中得到从中的网络ID
		



l3-agent
-------------------
api/rpc/agentnotifiers/l3_rpc_agent_api.py

插件要实现的方法
	get_l3_agents_hosting_routers()
	schedule_routers()


l3-agent 主要的 rpc 方法：
	
	agent_update
	router_deleted		
	routers_updated 
	router_removed_from_agent
	router_added_to_agent
	PS: 这些方法都应该放在 /neutron/common/contants.py
	只有routers_updated 需要检查 L3_AGENT_SCHEDULER_EXT_ALIAS 扩展？
除了router_deleted 调用 fanout_cast()，其他都调用 cast()。


/neutron/agent/l3_agent.py

PS: route id 在 self.conf.external_pids下以 route_id.pid 命名，在/proc/[pid]/cmdline 存放已经激活的 route_id

  	port :  port['id']
			port['mac_address']
			port['network_id']
			port['fixed_ips'] router 端口 ip
			port['subnet']['cidr']  router 端口子网 cidr
			port['ip_cidr']  router 端口 cidr
	route:
			route['id']
			route['admin_state_up']
			route['external_gateway_info']
			route['external_gateway_info']['network_id']

class L3PluginApi : Rpc调用 call 方法
	topic : q-l3-plugin
    method:
		sync_routers
		get_external_network_id
	这里的 worker 由插件来实现，对于 openvswitch 在 neutron/plugins/openvswitch/ovs_neutron_plugin.py

class class RouterInfo(object):维护 router 信息，PS：路由中包含 namespace,表面当前 router 属于这个 namespace
    internal_ports : []  existing_ports_ids 稍旧端口id的信息
    router : gw_port:XXXX  外网网关端口
			 _interfaces:[]  内网端口 list of port's id  internal_ports,每个元素有 id, admin_state_up 属性, 
							  当 admin_state_up=True 为真，为 current_port_ids
			 _floatingips: list of floating_ip, the element has "floating_ip_address" attribute
			
			
			enable_snat : False | True
	ex_gw_port : 外网网关端口


class L3NATAgent
	
	
	self.router_info = {router_id, RouterInfo()}
    ip_lib 是对 ip 命令的封装
    self.router 

	def _check_config_params(self)
		如果不用 namespace，那么必须设置 route_id

	def _destroy_router_namespaces
		1. 通过 ip 命令得到以 qrouter-[router_id] 的 namespace 列表, 并提取 router_id
		2. for ns in namespace 根据条件调用 _destroy_metadata_proxy(router_id, ns), _destroy_router_namespace(ns)
		

	def _destroy_router_namespace
		1. 用ip -o -d link list 得到所有的设备名
    	2. 对于以 qr- 开头的设备，根据条件调用 self.driver.unplug()
			即 ovs 命令删除 bridge(br-in) 的 tap 设备、ip link 删除 veth 设备和 namespace    
		3. 对于以 qg- 开头的设备，根据条件调用 self.driver.unplug()
			即 ovs 命令删除 bridge(br-ex) 的 tap 设备、ip link 删除 veth 设备和 namespace 
		4. 如果 router_delete_namespaces == True，命名空间也会随之删除

	def _router_added(router_id, router)
		1. 从 route_id 得到 RouterInfo 对象 ri，更新 route_info 信息 ri
        2. 根据条件创建 namespace 
        3. 根据条件增加metadata的 filter 和 nat 规则
        4. process_router_add(ri) 
		5. _spawn_metadata_proxy(ri.router_id, ri.ns_name())

	def _router_removed(router_id)
	    1. 从 router_info 得到 ri，清空 ri 的 router 属性
        2. process_router(ri)
		3. 删除 ipv4 的 filter 和 nat 规则
		4. _destroy_metadata_proxy(ri.router_id, ri.ns_name())
		5. _destroy_router_namespace(ri.ns_name())

	def _spawn_metadata_proxy(router_id, ns_name):
		self.conf.external_pids 下寻找 以 [route_id].pid 命名的文件,读取其中的pid，从 /proc/[pid]/cmdline 读取 [route_id]，
		如果已经存在，什么也不做
		如果不存在：
			1. 创建 conf.external_pids+route_id.pid文件。
			2. neutron-ns-metadata-proxy '--pid_file=%s' % pid_file, '--metadata_proxy_socket=%s' % metadata_proxy_socket,
				'--router_id=%s' % router_id,'--state_path=%s' % self.conf.state_path,'--metadata_port=%s' % self.conf.metadata_port]
				'--log-file=%s' % log_file_name --log-dir=%s' % log_dir 
            3. 如果 ns_name 不为None，在 ns 下执行上述命令，否则直接执行上述命令。
	
	def _destroy_metadata_proxy(route_id, ns_name)
		1. 从 conf.external_pids+route_id.pid 文件读取 pid，默认  $state_path/external/pids
		2. kill - 9 pid 杀死当前的进程


	def external_gateway_added(ri, ex_gw_port,interface_name, internal_cidrs) 两次判断 device_exists()
		1. 如果 interface_name 不存在，增加 interface_name 到 conf.external_network_bridge(br-ex)，即调用self.driver.plug()
		2. self.driver.init_l3()
		3. arping -A -I [ri] -c [conf.send_arp_for_ha] [ex_gw_port['ip_cidr']] 即发送 Gratuitous arp 广播
		4. 根据条件调用 route add default gw [ex_gw_port['subnet']['gateway_ip']]
	def external_gateway_removed(self, ri, ex_gw_port,interface_name, internal_cidrs)
		如果 interface_name  存在，调用 ovs 命令删除，即self.driver.unplug()。

	
	def _process_routers(self, ri, all_routers=False)
		对于路由 ri ，新端口增加到网络中，旧端口从网络中删除
		0. ex_gw_port = ri.get('gw_port')
		1. 获取 new_ports 和 old_ports
		2. 对于 new_ports 增加到网络
				根据 fixed_ips 更新 ip_cidr 属性, 
				internal_network_added(ri, network_id, port_id,internal_cidr, mac_address)
				ri.internal_ports.append(p)
        3. 对于 old_ports 从网络中删除
				internal_network_removed(self, ri, port_id, internal_cidr)
				ri.internal_ports.remove(p)
		4. 获取 ex_gw_port_id (ri.ex_gw_port['id'] OR ex_gw_port['id'] )，如果不为空 interface_name = qg-[ex_gw_port_id] 否则 interface_name = None
        5. 如果 ex_gw_port and not ri.ex_gw_port 为真:
			 _set_subnet_info(ex_gw_port) 
			external_gateway_added(ri, ex_gw_port,interface_name, internal_cidrs)
		6. 如果 not ex_gw_port and ri.ex_gw_port 为真:
			external_gateway_removed(ri, ri.ex_gw_port,interface_name, internal_cidrs) 与 5 比较
		7. 外部网关执行 SNAT 规则perform_snat_action(self._handle_router_snat_rules,internal_cidrs, interface_name)
		8. 内部网关执行 process_router_floating_ips(ri, ex_gw_port)
		9. 更新 ri 属性

	def internal_network_added(self, ri, network_id, port_id,internal_cidr, mac_address)
		1. 如果 port_id 对应的 interface_name(qr-[port_id]) 不存在，调用 ovs 命令增加，即self.driver.plug()
        3. arping -A -I [ri] -c [conf.send_arp_for_ha] [ip_address] 即发送 Gratuitous arp 广播
		  PS: Gratuitous ARP is used when hosts need to update other local host ARP tables 
			参考[这里](http://wiki.wireshark.org/Gratuitous_ARP)
	def internal_network_removed(self, ri, port_id, internal_cidr, mac_address)
		如果 port_id 对应的 interface_name(qr-[port_id]) 存在，调用 ovs 命令删除，即self.driver.unplug()。

	def _process_routers(self, routers, all_routers=False)
		1. 获取 prev_router_ids : 既在 self.route_info 又 routers 中的路由
		2. 从 routers 中过滤满足条件的 route, 增加到 cur_router_ids 与 self.route_info 调用 process_router(ri)
		3. _router_removed() 删除 在 prev_router_ids 但不在 cur_router_ids 中的路由。


	def _rpc_loop(self)
		1. 清空 self.updated_routers
		2. rpc 得到路由 routes
		3. _process_routers(routers) 更新路由信息
		4. 清空 self.removed_routers
		5. _router_removed(route_id)

	def _sync_routers_task(self, context)
		1. 根据条件调用 super(L3NATAgent, self).process_services_sync(context)
		2. 清空 self.updated_routers，self.removed_routers
		3. rpc 调用得到 routers
		4. _process_routers(routers, all_routers=True) 更新路由

	def _update_routing_table(self, ri, operation, route)
		ip route [operation] to  route['destination'] via route['nexthop']

	def routes_updated(self, ri)
		获取 add 和 removes 路由
        对与 add 的 route
		ip route replace to  route['destination'] via route['nexthop']
		对于 removes 的 route
		ip route delete to  route['destination'] via route['nexthop']








meter-agent
-------------------
api/rpc/agentnotifiers/l3_rpc_agent_api.py

插件要实现的方法
	get_l3_agents_hosting_routers
	
l2-agent 主要的 rpc 方法：
	router_deleted
	routers_updated
	update_metering_label_rules
	add_metering_label
	remove_metering_label
除了router_deleted 调用 fanout_cast()，其他都调用 cast()。


Rpc
======================================================


		:param context: The request context
        :param msg: The message to send, including the method and args.
					{'method':method, 'namespace':namespace,'args': kwargs}
        :param topic: Override the topic for this message.
        :param version: (Optional) Override the requested API version in this
               message.
        :param timeout: (Optional) A timeout to use when waiting for the
               response.  If no timeout is specified, a default timeout will be
               used that is usually sufficient.

msg['version']


在neutron/openstack/common/rpc 下的 impl_kombu.py, impl_qpid.py
都实现了相同的接口。


firewall
======================================================

class IptablesTable(object)
	self.rules = [] : list of IptablesRule
	self.remove_rules = [] : list of IptablesRule which is removed and unwrap
	self.chains = set() : wrap_name + chain
	self.unwrapped_chains = set() : chain only
	self.remove_chains = set() : chain which is removed and unwrap
	self.wrap_name = binary_name[:16]

class IptablesManager(object):

	self.ipv4:{'filter': IptablesTable, 'nat':IptablesTable}
	self.ipv6:{'filter': IptablesTable, 'nat':IptablesTable}
	self.iptables_apply_deferred = False : 是否立即起作用

	filter 表 ipv4 and ipv6 seperately
	1. FORWARD -j neutron-filter-top
	2. OUTPUT -j neutron-filter-top
	3. neutron-filter-top -j [wrap_name]-local
	
	builtin_chains:
	{4:{'filter':IptablesTable,'nat':IptablesTable}}
	{6:{'filter':IptablesTable,'nat':IptablesTable}}
	
	nat 表 ipv4 and ipv6 seperately
	1. PREROUTING -j -PREROUTING
	2. OUTPUT -j -OUTPUT
	3. POSTROUTING	-j -POSTROUTING
	4. POSTROUTING -j neutron-postrouting-bottom
	5. neutron-postrouting-bottom -j -snat
	6. snat', '-j [wrap-name]-float-snat

	def apply(self)
		ip netns exec [ns] iptables-save -c  保存 [规则]
		ip netns exec [ns] iptables-restore -c [全部规则]







加载配置文件的选项：
------------------------------------------------------

配置文件/etc/neutron.conf的配置选项散落在如下文件中： 
* /neutron/common/config.py
* /neutron/openstack/common/log.py
* /neutron/quota.py
* /neutron/openstack/common/rpc/impl_kombu.py
* /neutron/openstack/common/rpc/__init__.py
* /neutron/openstack/common/notifier/api.py

配置文件 /etc/dhcp_agent.ini 的配置选项散落在如下文件中：
* /neutron/agent/dhcp_agent.py
* /neutron/agent/common/dhcp.py
* /neutron/agent/common/dhcp.py
在这里你可以找到  中的主要选项。

一些选项困惑的选项：
* [pagination](http://en.wikipedia.org/wiki/Pagination)
* qpid_sasl_mechanisms [SASL](http://www.iana.org/assignments/sasl-mechanisms/sasl-mechanisms.xhtml)
* [Nagle algorithm](http://en.wikipedia.org/wiki/Nagle%27s_algorithm)
* backlog : The maximum number of queued connections
* metadata_proxy_socket 

**/neutron/common/config.py**

* 用oslo.conf定义配置选项，
* 启动log，
* 定义了配置文件(load\_paste\_app)。


如下选项没有在配置文件找到：

	amqp_durable_queues
	amqp_auto_delete
	rabbit_retry_backoff
	rabbit_use_ssl
	qpid_topology_version 
	rpc_zmq_matchmaker
	rpc_zmq_port
	rpc_zmq_contexts
	rpc_zmq_topic_backlog
	rpc_zmq_ipc_dir
	rpc_zmq_host
	matchmaker_heartbeat_freq
	topics
	matchmaker_heartbeat_ttl

	external_pids
	backdoor_port
	disable_process_locking
	network_device_mtu 
	meta_flavor_driver_mappings
	ip_lib_force_root
	disable_process_locking

吐槽点:
    route.py 中的 RESOURCES 应该为
	RESOURCES = {attributes.NETWORK:attributes.NETWORKS,
				attributes.SUBNET:attributes.SUBNETS,
				attributes.PORT:attributes.PORTS}

	BASE_RPC_API_VERSION = '1.0' 这个变量应该放在/neutron/common/constants.py

	def get_network_by_port_id(port_id) 如果端口不存在，是否应该捕捉异常，因为 dict 会抛keyError
	def existing_dhcp_networks() 仅仅检查是否符合 uuid 的格式
	
	dhcp_agent_manager 不存在， 在 service.py 中如果manager 不存在的化，会需要这个配置选项

	init_host 在子类中没有实现，现在什么也不做，比如 class DhcpAgentWithStateReport 中需要使用

	def _ivs_add_port(self, device_name, port_id, mac_address) 参数 port_id, mac_address 没有使用
	def routers_updated(self, context, routers) 参数 context 没有使用


neutron.manager.Manger
	class DhcpAgent
	class DhcpAgentWithStateReport

neutron.openstack.common.service
	class Launch()
	class ServiceLauncher()

neutron.service 有个 back_door 属性 调用了 eventlet_backdoor.initialize_if_enabled()。

