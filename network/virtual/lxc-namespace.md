
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
