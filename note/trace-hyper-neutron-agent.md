

C:\Program Files (x86)\Cloudbase Solutions\OpenStack\Nova\Python27\lib\site-packages\neutron\plugins\hyperv\agent\hyperv_neutron_agent.py

	daemon_loop()
	-->_process_network_ports(port_info)
	-->_treat_devices_added(port_info['added'])
	-->_treat_vif_port()
	-->_port_bound()

C:\Program Files (x86)\Cloudbase Solutions\OpenStack\Nova\Python27\lib\site-packages\neutron\plugins\hyperv\agent\utilsv2.py
	_port_bound()
	-->connect_vnic_to_vswitch()
	-->_add_virt_resource()


1. daemon_loop() :一直循环，如果有port_info就执行_process_network_port(port_info)
	port_info: {'current': set([u'8b547d6c-08ff-4704-a668-04e964aa981c', 
								u'573bb1ba-108d-4211-8aff-db6f3c727c21', 
								u'Network Adapter', 
								u'7f884340-a009-4314-9c90-b7971953e8bc']), 
	'removed': set([]), 
	'added': set([u'7f884340-a009-4314-9c90-b7971953e8bc'])}

2. _process_network_port(): 得到device_detail,调用用_treat_devices_added(port_info['added'])
	Port 7f884340-a009-4314-9c90-b7971953e8bc 
	Details: {u'admin_state_up': True,
		u'network_id': u'8f76b5b4-c943-401b-b503-a3b55f8da8a0', 
		u'segmentation_id': 2, 
		u'physical_network': u'physnet1', 
		u'device': u'7f884340-a009-4314-9c90-b7971953e8bc', 
		u'port_id': u'7f884340-a009-4314-9c90-b7971953e8bc', 
		u'network_type': u'vlan'}

  这里看出hyperV从控制节点得到了正确的信息。如网卡，端口。

3. _treat_vif_port():如果port_id存在,admin_state_up=True,就用_port_bound()
                     否则，用_port_unbound()

4. _port_bound(): 得到map = _network_vswitch_map(dict),调用connect_vnic_to_vswitch(map['vswitch_name'],port_id)
                  如果网络类型是VLAN,?用set_vswitch_port_vlan_id(VLAN_ID, port_id)
                  如果网络是其他类型如FLAT，LOCAL，则什么也不做。

  	Binding port : ba1fccdd-3a82-487e-9d20-e74174f9a429, 
	network_vswitch_map : {u'8f76b5b4-c943-401b-b503-a3b55f8da8a0': 
							{'vswitch_name': 'NewSwitch',
							'network_type': u'vlan', 
							'vlan_id': 2, 
							'ports': [u'8b547d6c-08ff-4704-a668-04e964aa981c', u'573bb1ba-108d-4211-8aff-db6f3c727c21', 				
										u'ba1fccdd-3a82-487e-9d20-e74174f9a429', u'8b547d6c-08ff-4704-a668-04e964aa981c', 
										u'573bb1ba-108d-4211-8aff-db6f3c727c21']
							 }
						   }

	map {'vswitch_name': 'NewSwitch',
		 'network_type': u'vlan',  
		'vlan_id': 2, 
		'ports': [u'8b547d6c-08ff-4704-a668-04e964aa981c', u'573bb1ba-108d-4211-8aff-db6f3c727c21',
					u'ba1fccdd-3a82-487e-9d20-e74174f9a429', u'8b547d6c-08ff-4704-a668-04e964aa981c', 
					u'573bb1ba-108d-4211-8aff-db6f3c727c21', u'ba1fccdd-3a82-487e-9d20-e74174f9a429']}, 
		connect NewSwitch to ba1fccdd-3a82-487e-9d20-e74174f9a429

   从这里看出，在port_id存在，控制节点与hyperv的Newswitch连接正常。

5. connect_vnic_to_vswitch(vswitch_name,switch_port_name)：调用_get_vnic_settings(switch_port_name)得到vnic
                                                           调用_get_vswitch(vswitch_name)得到vswitch
                                                           调用_get_switch_port_allocation(switch_port_name)得到port,found.
                                                           如果found 是True:调用_get_vm_from_res_setting_datav(vnic)
																			调用_add_virt_resource(vm, port)
                                                           否则,调用_modify_virt_resource(port)

端口得到的虚拟网卡的信息：
vnic:
instance of Msvm_SyntheticEthernetPortSettingData
{
	Address = "FA163EB00BE6";  MAC地址
	AddressOnParent = NULL;
	AllocationUnits = "count";
	AutomaticAllocation = TRUE;
	AutomaticDeallocation = TRUE;
	Caption = "Ethernet Port";
	ClusterMonitored = TRUE;
	Connection = {""};
	ConsumerVisibility = 3;
	Description = "Settings for the Microsoft Synthetic Ethernet Port.";
	DesiredVLANEndpointMode = NULL;
	ElementName = "ba1fccdd-3a82-487e-9d20-e74174f9a429";  控制??neiwang1
	HostResource = NULL;
	InstanceID = "Microsoft:750606C5-9522-4A08-B211-00AA914D6DAC\\09029749-5D1D-4883-ABDE-581B23738AF6";
	Limit = "1";
	MappingBehavior = NULL;
	OtherEndpointMode = NULL;
	OtherResourceType = NULL;
	Parent = NULL;
	PoolID = "";
	Reservation = "1";
	ResourceSubType = "Microsoft:Hyper-V:Synthetic Ethernet Port";
	ResourceType = 10;
	StaticMacAddress = TRUE;
	VirtualQuantity = "1";
	VirtualQuantityUnits = "count";
	VirtualSystemIdentifiers = {"{89b28ea3-16f6-4069-a09e-b76241a1cbba}"};
	Weight = 0;
};
hyperv 交换机
vswitch: instance of Msvm_VirtualEthernetSwitch
{
	AvailableRequestedStates = NULL;
	Caption = "Virtual Switch";
	CommunicationStatus = NULL;
	CreationClassName = "Msvm_VirtualEthernetSwitch";
	Dedicated = {38};
	Description = "Microsoft Virtual Switch";
	DetailedStatus = NULL;
	ElementName = "NewSwitch";  ??交?机的名?
	EnabledDefault = 2;
	EnabledState = 5;
	HealthState = 5;
	IdentifyingDescriptions = {"Virtual Switch Extension Miniport Adapter Id"};
	InstallDate = NULL;
	InstanceID = NULL;
	MaxIOVOffloads = 0;
	MaxVMQOffloads = 0;
	Name = "261E80E6-CFDC-4622-9420-E3FF50A44FF9";
	NameFormat = NULL;
	OperatingStatus = NULL;
	OperationalStatus = {2};
	OtherDedicatedDescriptions = NULL;
	OtherEnabledState = NULL;
	OtherIdentifyingInfo = {"{CB2532EF-AA9A-4352-9E99-D7FAA232B64C}"};
	PowerManagementCapabilities = NULL;
	PrimaryOwnerContact = NULL;
	PrimaryOwnerName = NULL;
	PrimaryStatus = NULL;
	RequestedState = 12;
	ResetCapability = 5;
	Roles = NULL;
	Status = "OK";       ??是好的
	StatusDescriptions = {"OK"};
	TimeOfLastStateChange = NULL;
	TransitioningToState = NULL;
};

port : instance of Msvm_EthernetPortAllocationSettingData
{
	AllocationUnits = "count";
	AutomaticAllocation = TRUE;
	AutomaticDeallocation = TRUE;
	Caption = "Ethernet Connection Default Settings";
	ConsumerVisibility = 3;
	Description = "Describes the default settings for ethernet connection resources.";
	DesiredVLANEndpointMode = 2;
	ElementName = "ba1fccdd-3a82-487e-9d20-e74174f9a429";
	EnabledState = 2;
	HostResource = {"\\\\WS2012R2\\root\\virtualization\\v2:Msvm_VirtualEthernetSwitch.CreationClassName=\"Msvm_VirtualEthernetSwitch\",Name=\"261E80E6-CFDC-4622-9420-E3FF50A44FF9\""};
	InstanceID = "Microsoft:Definition\\72027ECE-E44A-446E-AF2B-8D8C4B8A2279\\Default";
	Limit = "1";
	Parent = "\\\\WS2012R2\\root\\virtualization\\v2:Msvm_SyntheticEthernetPortSettingData.InstanceID=\"Microsoft:750606C5-9522-4A08-B211-00AA914D6DAC\\\\09029749-5D1D-4883-ABDE-581B23738AF6\"";
	PoolID = "";
	Reservation = "1";
	ResourceSubType = "Microsoft:Hyper-V:Ethernet Connection";
	ResourceType = 33;
	VirtualQuantity = "1";
	VirtualQuantityUnits = "count";
	Weight = 0;
};

found : False 



6. _get_switch_port_allocation()
7. _get_vm_from_res_setting_data()


8. _add_virt_resource(): 调用 wmi.WMI(moniker='//./root/virtualization').Msvm_VirtualSystemManagementService()[0].AddResourceSettings(vm.path_(), [port.GetText_(1)])
                         调用_check_job_status(ret_val, job_path)?查返回值的??.

9. _check_job_status()由于ret_val一般为0，直接返回。



