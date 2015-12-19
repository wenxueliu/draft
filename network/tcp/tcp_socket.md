

    packet: improve socket create/bind latency in some cases
    Most people acquire PF_PACKET sockets with a protocol argument in
    the socket call, e.g. libpcap does so with htons(ETH_P_ALL) for
    all its sockets. Most likely, at some point in time a subsequent
    bind() call will follow, e.g. in libpcap with ...
      memset(&sll, 0, sizeof(sll));
      sll.sll_family = AF_PACKET;
      sll.sll_ifindex = ifindex;
      sll.sll_protocol = htons(ETH_P_ALL);
    ... as arguments. What happens in the kernel is that already
    in socket() syscall, we install a proto hook via register_prot_hook()
    if our protocol argument is != 0. Yet, in bind() we're almost
    doing the same work by doing a unregister_prot_hook() with an
    expensive synchronize_net() call in case during socket() the proto
    was != 0, plus follow-up register_prot_hook() with a bound device
    to it this time, in order to limit traffic we get.
    In the case when the protocol and user supplied device index (== 0)
    does not change from socket() to bind(), we can spare us doing
    the same work twice. Similarly for re-binding to the same device
    and protocol. For these scenarios, we can decrease create/bind
    latency from ~7447us (sock-bind-2 case) to ~89us (sock-bind-1 case)
    with this patch.
    Alternatively, for the first case, if people care, they should
    simply create their sockets with proto == 0 argument and define
    the protocol during bind() as this saves a call to synchronize_net()
    as well (sock-bind-3 case).
    In all other cases, we're tied to user space behaviour we must not
    change, also since a bind() is not strictly required. Thus, we need
    the synchronize_net() to make sure no asynchronous packet processing
    paths still refer to the previous elements of po->prot_hook.
    In case of mmap()ed sockets, the workflow that includes bind() is
    socket() -> setsockopt(<ring>) -> bind(). In that case, a pair of
    {__unregister, register}_prot_hook is being called from setsockopt()
    in order to install the new protocol receive handler. Thus, when
    we call bind and can skip a re-hook, we have already previously
    installed the new handler. For fanout, this is handled different
    entirely, so we should be good.
    Timings on an i7-3520M machine:
      * sock-bind-1: 89 us
      * sock-bind-2: 7447 us
      * sock-bind-3: 75 us
    sock-bind-1:
      socket(PF_PACKET, SOCK_RAW, htons(ETH_P_IP)) = 3
      bind(3, {sa_family=AF_PACKET, proto=htons(ETH_P_IP), if=all(0),
               pkttype=PACKET_HOST, addr(0)={0, }, 20) = 0
    sock-bind-2:
      socket(PF_PACKET, SOCK_RAW, htons(ETH_P_IP)) = 3
      bind(3, {sa_family=AF_PACKET, proto=htons(ETH_P_IP), if=lo(1),
               pkttype=PACKET_HOST, addr(0)={0, }, 20) = 0
    sock-bind-3:
      socket(PF_PACKET, SOCK_RAW, 0) = 3
      bind(3, {sa_family=AF_PACKET, proto=htons(ETH_P_IP), if=lo(1),
               pkttype=PACKET_HOST, addr(0)={0, }, 20) = 0
    Signed-off-by: Daniel Borkmann <dborkman@redhat.com>
    Signed-off-by: David S. Miller <davem@davemloft.net>


