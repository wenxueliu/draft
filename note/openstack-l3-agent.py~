l3_agent 

main()
-------------------
* 注册配置文件选项
* 开启日志
* 开始 ProcessLauncher()	, 具体见 neutron server worker >= 1 的分析



未注册
periodic_interval  		neutron/service.py
periodic_fuzzy_delay	neutron/service.py

注册未用
external_pids
network_device_mtu 
meta_flavor_driver_mappings

l3_agent 配置
--------------------------------------------------------
/etc/neutron.conf 的 section：agent 中
root_helper
report_interval

全局配置

periodic_interval  		neutron/service.py
periodic_fuzzy_delay	neutron/service.py

其他选项

/neutron/agent/l3_agent.py
/neutron/agent/common/config.py
/neutron/agent/linux/interface.py
/neutron/agent/linux/external_process.py

关键参数解释

####conf.interface_driver 可以选参数，没有默认值，所以一定要配置，可选值：
	
	neutron.agent.linux.interface.OVSInterfaceDriver  建议采用
	neutron.agent.linux.interface.IVSInterfaceDriver
	neutron.agent.linux.interface.NullDriver
	neutron.agent.linux.interface.MidonetInterfaceDriver 调用到neutronclient
	neutron.agent.linux.interface.BridgeInterfaceDriver 

####代码实现

位置 /neutron/agent/linux/interface.py
class LinuxInterfaceDriver(object):
	def init_l3(self, device_name, ip_cidrs, namespace=None,preserve_ips=[])
		:param  ip_cidrs ： list of 'X.X.X.X/YY' strings
		:param  preserve_ips=[] : list of ip cidrs that should not be removed from device
		1. ip link show [device] permanent  scope global PS: 此处待验证
		2. 返回[dict(cidr,broadcast,scope,ip_version,dynamic)]的list

class NullDriver(LinuxInterfaceDriver)
	什么也没做，如果你不想用任何驱动的化，设置为此选项

class OVSInterfaceDriver(LinuxInterfaceDriver)
	def plug(self, network_id, port_id, device_name, mac_address, =None, namespace=None, prefix=None)
		param: network_id : port['network_id']
		param: port_id : port['id']
		param: device_name : port['ip_cidr'] 或 port_id 获取
		param: mac_address : port['mac_address']
		1. 如果 bridge 不存在，取 bridge = conf.ovs_integration_bridge, 用 ip 命令检查 bridge 是否存在
		2. 用 ip 命令检查 device_name 是否存在，如果存在什么也不做，不存在，继续
		3. 获取 device_name 的 tap_name，即将device_name 前缀改为tap，得到tap_name
		4. 根据条件 ip add [tap_name] type veth peer name [device_name]
		5. ovs-vsctl -- --may-exist add-port [bridge] [device_name] 
			-- set Interface [device_name] type=internal
			-- set Interface [device_name] external-ids:iface-id=[port_id]
			-- set Interface [device_name] external-ids:iface-status=active
			-- set Interface [device_name] external-ids:attached-mac=mac_address
	    6. ip linke set [device_name] address [mac_address]
        7. 根据条件 ip link set [device_name] mtu conf.network_device_mtu
		8. 根据条件增加到 namespace		
		9. ip link set [ns_dev] up 开启设备

	def unplug(self, device_name, bridge=None, namespace=None, prefix=None)
		1. 获取 device_name 的 tap_name，即将device_name 前缀改为tap，得到tap_name
		2. 检查 bridge
		3. ovs-ctl --timeout=2 -- --if-exists  del-port [bridge] [tap_name]
		4. ip link delete [device_name]


class IVSInterfaceDriver(LinuxInterfaceDriver)
	def plug(self, network_id, port_id, device_name, mac_address,bridge=None, namespace=None, prefix=None)
		param: network_id : port['network_id']
		param: port_id : port['id']
		param: device_name : port['ip_cidr'] 或 port_id 获取
        param: mac_address : port['mac_address']
		1. 如果 bridge 不存在，取 bridge = conf.ovs_integration_bridge, 用 ip 命令检查 bridge 是否存在
		2. 用 ip 命令检查 device_name 是否存在，如果存在什么也不做，不存在，继续
		3. 获取 device_name 的 tap_name，即将 device_name 前缀改为tap，得到tap_name
		4. 根据条件 ip add [tap_name] type veth peer name [device_name]
		5. ivs-ctl add-port [tap_name]
	    6. ip linke set [device_name] address [mac_address]
        7. 根据条件 ip link set [device_name] mtu conf.network_device_mtu
		8. 根据条件增加到 namespace
		9. ip link set [ns_dev] up 开启设备

	def unplug(self, device_name, bridge=None, namespace=None, prefix=None)
		1. 获取 device_name 的 tap_name，即将device_name 前缀改为tap，得到tap_name
		2. ivs-ctl del-port tapname
		3. ip linke delete [device_name]
		PS: 此处应该检查 bridge 是否存在

class MidonetInterfaceDriver(LinuxInterfaceDriver) 忽略
class BridgeInterfaceDriver(LinuxInterfaceDriver)  忽略
class MetaInterfaceDriver(LinuxInterfaceDriver)  忽略

