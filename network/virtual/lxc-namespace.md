
##Example:One bridge with two VM
apt-get install bridge-utils
ip netns add net0
ip netns add net1
ip netns add bridge
ip link add type veth
ip link set dev veth0 name net0-bridge netns net0
ip link set dev veth1 name bridge-net0 netns bridge
ip link add type veth
ip link set dev veth0 name net1-bridge netns net1
ip link set dev veth1 name bridge-net1 netns bridge

ip netns exec bridge brctl addbr br
ip netns exec bridge ip link set dev br up
ip netns exec bridge ip link set dev bridge-net0 up
ip netns exec bridge ip link set dev bridge-net1 up
ip netns exec bridge brctl addif br bridge-net0
ip netns exec bridge brctl addif br bridge-net1

ip netns exec net0 ip link set dev net0-bridge up
ip netns exec net0 ip address add 10.0.1.1/24 dev net0-bridge

ip netns exec net1 ip link set dev net1-bridge up
ip netns exec net1 ip address add 10.0.1.2/24 dev net1-bridge

##Test
ip netns exec net0 ping -c 3 10.0.1.2


##Example:OVS bridge with two VM (pipework)
ovs-vsctl add-br ovsbr0
ip addr add dev ovsbr0 10.10.0.1/16
ip link set dev ovsbr0 up
ip link add veth_hostc0 type veth peer name veth_contc0
ovs-vsctl add-port ovsbr0 veth_hostc0
docker run --net='none' -itd busybox /bin/sh
    6a37777816a7073d1d238161e1f88d4a8e5032f26209b1dfacdaad69dea99606
docker inspect -f '{{.State.Pid}}' 6a37777816a7
    3975
mkdir -p /var/run/netns
ln -s /proc/3975/ns/net /var/run/netns/3975
ip link set veth_contc0 netns 3975
docker attach 6a37777816a7
ip netns exec 3975 ip link set dev veth_contc0 name eth0
ip netns exec 3975 ip link set dev eth0 up

cat /etc/default/isc-dhcp-server
    INTERFACES="ovsbr0"
    [host]#cat /etc/dhcp/dhcpd.conf
    subnet 10.10.0.0 netmask 255.255.0.0 {
    range 10.10.0.2 10.10.0.254;
    option routers 10.10.0.1;
    }

http://cloudgeekz.com/400/how-to-use-openvswitch-with-docker.html
