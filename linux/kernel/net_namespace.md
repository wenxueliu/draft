

##附录

```
/* linux/net/net_namespace.h

/*
 * Operations on the network namespace
 */
#ifndef __NET_NET_NAMESPACE_H
#define __NET_NET_NAMESPACE_H

#include <linux/atomic.h>
#include <linux/workqueue.h>
#include <linux/list.h>
#include <linux/sysctl.h>

#include <net/flow.h>
#include <net/netns/core.h>
#include <net/netns/mib.h>
#include <net/netns/unix.h>
#include <net/netns/packet.h>
#include <net/netns/ipv4.h>
#include <net/netns/ipv6.h>
#include <net/netns/ieee802154_6lowpan.h>
#include <net/netns/sctp.h>
#include <net/netns/dccp.h>
#include <net/netns/netfilter.h>
#include <net/netns/x_tables.h>
#if defined(CONFIG_NF_CONNTRACK) || defined(CONFIG_NF_CONNTRACK_MODULE)
#include <net/netns/conntrack.h>
#endif
#include <net/netns/nftables.h>
#include <net/netns/xfrm.h>
#include <net/netns/mpls.h>
#include <linux/ns_common.h>

struct user_namespace;
struct proc_dir_entry;
struct net_device;
struct sock;
struct ctl_table_header;
struct net_generic;
struct sock;
struct netns_ipvs;


#define NETDEV_HASHBITS    8
#define NETDEV_HASHENTRIES (1 << NETDEV_HASHBITS)

struct net {
        atomic_t                passive;        /* To decided when the network
                                                 * namespace should be freed.
                                                 */
        atomic_t                count;          /* To decided when the network
                                                 *  namespace should be shut down.
                                                 */
        spinlock_t              rules_mod_lock;

        atomic64_t              cookie_gen;

        //遍历所有 net 时使用
        struct list_head        list;           /* list of network namespaces */
        struct list_head        cleanup_list;   /* namespaces on death row */
        struct list_head        exit_list;      /* Use only net_mutex */

        struct user_namespace   *user_ns;       /* Owning user namespace */
        struct idr              netns_ids;

        struct ns_common        ns;

        struct proc_dir_entry   *proc_net;
        struct proc_dir_entry   *proc_net_stat;

#ifdef CONFIG_SYSCTL
        struct ctl_table_set    sysctls;
#endif

        struct sock             *rtnl;                  /* rtnetlink socket */
        struct sock             *genl_sock;

        struct list_head        dev_base_head;
        struct hlist_head       *dev_name_head;
        struct hlist_head       *dev_index_head;
        unsigned int            dev_base_seq;   /* protected by rtnl_mutex */
        int                     ifindex;
        unsigned int            dev_unreg_count;

        /* core fib_rules */
        struct list_head        rules_ops;


        struct net_device       *loopback_dev;          /* The loopback */
        struct netns_core       core;
        struct netns_mib        mib;
        struct netns_packet     packet;
        struct netns_unix       unx;
        struct netns_ipv4       ipv4;
#if IS_ENABLED(CONFIG_IPV6)
        struct netns_ipv6       ipv6;
#endif
#if IS_ENABLED(CONFIG_IEEE802154_6LOWPAN)
        struct netns_ieee802154_lowpan  ieee802154_lowpan;
#endif
#if defined(CONFIG_IP_SCTP) || defined(CONFIG_IP_SCTP_MODULE)
        struct netns_sctp       sctp;
#endif
#if defined(CONFIG_IP_DCCP) || defined(CONFIG_IP_DCCP_MODULE)
        struct netns_dccp       dccp;
#endif
#ifdef CONFIG_NETFILTER
        struct netns_nf         nf;
        struct netns_xt         xt;
#if defined(CONFIG_NF_CONNTRACK) || defined(CONFIG_NF_CONNTRACK_MODULE)
        struct netns_ct         ct;
#endif
#if defined(CONFIG_NF_TABLES) || defined(CONFIG_NF_TABLES_MODULE)
        struct netns_nftables   nft;
#endif
#if IS_ENABLED(CONFIG_NF_DEFRAG_IPV6)
        struct netns_nf_frag    nf_frag;
#endif
        struct sock             *nfnl;
        struct sock             *nfnl_stash;
#endif
#ifdef CONFIG_WEXT_CORE
        struct sk_buff_head     wext_nlevents;
#endif
        struct net_generic __rcu        *gen;

        /* Note : following structs are cache line aligned */
#ifdef CONFIG_XFRM
        struct netns_xfrm       xfrm;
#endif
#if IS_ENABLED(CONFIG_IP_VS)
        struct netns_ipvs       *ipvs;
#endif
#if IS_ENABLED(CONFIG_MPLS)
        struct netns_mpls       mpls;
#endif
        struct sock             *diag_nlsk;
        atomic_t                fnhe_genid;
};

#include <linux/seq_file_net.h>

/* Init's network namespace */
extern struct net init_net;

#ifdef CONFIG_NET_NS
struct net *copy_net_ns(unsigned long flags, struct user_namespace *user_ns,
                        struct net *old_net);

#else /* CONFIG_NET_NS */
#include <linux/sched.h>
#include <linux/nsproxy.h>
static inline struct net *copy_net_ns(unsigned long flags,
        struct user_namespace *user_ns, struct net *old_net)
{
        if (flags & CLONE_NEWNET)
                return ERR_PTR(-EINVAL);
        return old_net;
}
#endif /* CONFIG_NET_NS */


extern struct list_head net_namespace_list;

struct net *get_net_ns_by_pid(pid_t pid);
struct net *get_net_ns_by_fd(int pid);

#ifdef CONFIG_SYSCTL
void ipx_register_sysctl(void);
void ipx_unregister_sysctl(void);
#else
#define ipx_register_sysctl()
#define ipx_unregister_sysctl()
#endif

#ifdef CONFIG_NET_NS
void __put_net(struct net *net);

static inline struct net *get_net(struct net *net)
{
        atomic_inc(&net->count);
        return net;
}

static inline struct net *maybe_get_net(struct net *net)
{
        /* Used when we know struct net exists but we
         * aren't guaranteed a previous reference count
         * exists.  If the reference count is zero this
         * function fails and returns NULL.
         */
        if (!atomic_inc_not_zero(&net->count))
                net = NULL;
        return net;
}

static inline void put_net(struct net *net)
{
        if (atomic_dec_and_test(&net->count))
                __put_net(net);
}

static inline
int net_eq(const struct net *net1, const struct net *net2)
{
        return net1 == net2;
}

void net_drop_ns(void *);

#else

static inline struct net *get_net(struct net *net)
{
        return net;
}

static inline void put_net(struct net *net)
{
}

static inline struct net *maybe_get_net(struct net *net)
{
        return net;
}

static inline
int net_eq(const struct net *net1, const struct net *net2)
{
        return 1;
}

#define net_drop_ns NULL
#endif


typedef struct {
#ifdef CONFIG_NET_NS
        struct net *net;
#endif
} possible_net_t;

static inline void write_pnet(possible_net_t *pnet, struct net *net)
{
#ifdef CONFIG_NET_NS
        pnet->net = net;
#endif
}

static inline struct net *read_pnet(const possible_net_t *pnet)
{
#ifdef CONFIG_NET_NS
        return pnet->net;
#else
        return &init_net;
#endif
}

#define for_each_net(VAR)                               \
        list_for_each_entry(VAR, &net_namespace_list, list)

#define for_each_net_rcu(VAR)                           \
        list_for_each_entry_rcu(VAR, &net_namespace_list, list)

#ifdef CONFIG_NET_NS
#define __net_init
#define __net_exit
#define __net_initdata
#define __net_initconst
#else
#define __net_init      __init
#define __net_exit      __exit_refok
#define __net_initdata  __initdata
#define __net_initconst __initconst
#endif

int peernet2id(struct net *net, struct net *peer);
struct net *get_net_ns_by_id(struct net *net, int id);

struct pernet_operations {
        struct list_head list;
        int (*init)(struct net *net);
        void (*exit)(struct net *net);
        void (*exit_batch)(struct list_head *net_exit_list);
        int *id;
        size_t size;
};

/*
 * Use these carefully.  If you implement a network device and it
 * needs per network namespace operations use device pernet operations,
 * otherwise use pernet subsys operations.
 *
 * Network interfaces need to be removed from a dying netns _before_
 * subsys notifiers can be called, as most of the network code cleanup
 * (which is done from subsys notifiers) runs with the assumption that
 * dev_remove_pack has been called so no new packets will arrive during
 * and after the cleanup functions have been called.  dev_remove_pack
 * is not per namespace so instead the guarantee of no more packets
 * arriving in a network namespace is provided by ensuring that all
 * network devices and all sockets have left the network namespace
 * before the cleanup methods are called.
 *
 * For the longest time the ipv4 icmp code was registered as a pernet
 * device which caused kernel oops, and panics during network
 * namespace cleanup.   So please don't get this wrong.
 */
int register_pernet_subsys(struct pernet_operations *);
void unregister_pernet_subsys(struct pernet_operations *);
int register_pernet_device(struct pernet_operations *);
void unregister_pernet_device(struct pernet_operations *);

struct ctl_table;
struct ctl_table_header;

#ifdef CONFIG_SYSCTL
int net_sysctl_init(void);
struct ctl_table_header *register_net_sysctl(struct net *net, const char *path,
                                             struct ctl_table *table);
void unregister_net_sysctl_table(struct ctl_table_header *header);
#else
static inline int net_sysctl_init(void) { return 0; }
static inline struct ctl_table_header *register_net_sysctl(struct net *net,
        const char *path, struct ctl_table *table)
{
        return NULL;
}
static inline void unregister_net_sysctl_table(struct ctl_table_header *header)
{
}
#endif

static inline int rt_genid_ipv4(struct net *net)
{
        return atomic_read(&net->ipv4.rt_genid);
}

static inline void rt_genid_bump_ipv4(struct net *net)
{
        atomic_inc(&net->ipv4.rt_genid);
}

extern void (*__fib6_flush_trees)(struct net *net);
static inline void rt_genid_bump_ipv6(struct net *net)
{
        if (__fib6_flush_trees)
                __fib6_flush_trees(net);
}

#if IS_ENABLED(CONFIG_IEEE802154_6LOWPAN)
static inline struct netns_ieee802154_lowpan *
net_ieee802154_lowpan(struct net *net)
{
        return &net->ieee802154_lowpan;
}
#endif

/* For callers who don't really care about whether it's IPv4 or IPv6 */
static inline void rt_genid_bump_all(struct net *net)
{
        rt_genid_bump_ipv4(net);
        rt_genid_bump_ipv6(net);
}

static inline int fnhe_genid(struct net *net)
{
        return atomic_read(&net->fnhe_genid);
}

static inline void fnhe_genid_bump(struct net *net)
{
        atomic_inc(&net->fnhe_genid);
}

#endif /* __NET_NET_NAMESPACE_H */

```


```
/* net/netns/generic.h  */

/*
 * generic net pointers
 */

#ifndef __NET_GENERIC_H__
#define __NET_GENERIC_H__

#include <linux/bug.h>
#include <linux/rcupdate.h>

/*
 * Generic net pointers are to be used by modules to put some private
 * stuff on the struct net without explicit struct net modification
 *
 * The rules are simple:
 * 1. set pernet_operations->id.  After register_pernet_device you
 *    will have the id of your private pointer.
 * 2. set pernet_operations->size to have the code allocate and free
 *    a private structure pointed to from struct net.
 * 3. do not change this pointer while the net is alive;
 * 4. do not try to have any private reference on the net_generic object.
 *
 * After accomplishing all of the above, the private pointer can be
 * accessed with the net_generic() call.
 */

struct net_generic {
        unsigned int len;
        struct rcu_head rcu;

        void *ptr[0];
};

static inline void *net_generic(const struct net *net, int id)
{
        struct net_generic *ng;
        void *ptr;

        rcu_read_lock();
        ng = rcu_dereference(net->gen);
        ptr = ng->ptr[id - 1];
        rcu_read_unlock();

        return ptr;
}
#endif


/* net_namespace.c */

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/workqueue.h>
#include <linux/rtnetlink.h>
#include <linux/cache.h>
#include <linux/slab.h>
#include <linux/list.h>
#include <linux/delay.h>
#include <linux/sched.h>
#include <linux/idr.h>
#include <linux/rculist.h>
#include <linux/nsproxy.h>
#include <linux/fs.h>
#include <linux/proc_ns.h>
#include <linux/file.h>
#include <linux/export.h>
#include <linux/user_namespace.h>
#include <linux/net_namespace.h>
#include <net/sock.h>
#include <net/netlink.h>
#include <net/net_namespace.h>
#include <net/netns/generic.h>

/*
 *      Our network namespace constructor/destructor lists
 */

static LIST_HEAD(pernet_list);
static struct list_head *first_device = &pernet_list;
DEFINE_MUTEX(net_mutex);

LIST_HEAD(net_namespace_list);
EXPORT_SYMBOL_GPL(net_namespace_list);

struct net init_net = {
        .dev_base_head = LIST_HEAD_INIT(init_net.dev_base_head),
};
EXPORT_SYMBOL(init_net);

#define INITIAL_NET_GEN_PTRS    13 /* +1 for len +2 for rcu_head */

static unsigned int max_gen_ptrs = INITIAL_NET_GEN_PTRS;

static struct net_generic *net_alloc_generic(void)
{
        struct net_generic *ng;
        size_t generic_size = offsetof(struct net_generic, ptr[max_gen_ptrs]);

        ng = kzalloc(generic_size, GFP_KERNEL);
        if (ng)
                ng->len = max_gen_ptrs;

        return ng;
}

static int net_assign_generic(struct net *net, int id, void *data)
{
        struct net_generic *ng, *old_ng;

        BUG_ON(!mutex_is_locked(&net_mutex));
        BUG_ON(id == 0);

        old_ng = rcu_dereference_protected(net->gen,
                                           lockdep_is_held(&net_mutex));
        ng = old_ng;
        if (old_ng->len >= id)
                goto assign;

        ng = net_alloc_generic();
        if (ng == NULL)
                return -ENOMEM;

        /*
         * Some synchronisation notes:
         *
         * The net_generic explores the net->gen array inside rcu
         * read section. Besides once set the net->gen->ptr[x]
         * pointer never changes (see rules in netns/generic.h).
         *
         * That said, we simply duplicate this array and schedule
         * the old copy for kfree after a grace period.
         */

        memcpy(&ng->ptr, &old_ng->ptr, old_ng->len * sizeof(void*));

        rcu_assign_pointer(net->gen, ng);
        kfree_rcu(old_ng, rcu);
assign:
        ng->ptr[id - 1] = data;
        return 0;
}

static int ops_init(const struct pernet_operations *ops, struct net *net)
{
        int err = -ENOMEM;
        void *data = NULL;

        if (ops->id && ops->size) {
                data = kzalloc(ops->size, GFP_KERNEL);
                if (!data)
                        goto out;

                err = net_assign_generic(net, *ops->id, data);
                if (err)
                        goto cleanup;
        }
        err = 0;
        if (ops->init)
                err = ops->init(net);
        if (!err)
                return 0;

cleanup:
        kfree(data);

out:
        return err;
}

static void ops_free(const struct pernet_operations *ops, struct net *net)
{
        if (ops->id && ops->size) {
                int id = *ops->id;
                kfree(net_generic(net, id));
        }
}

static void ops_exit_list(const struct pernet_operations *ops,
                          struct list_head *net_exit_list)
{
        struct net *net;
        if (ops->exit) {
                list_for_each_entry(net, net_exit_list, exit_list)
                        ops->exit(net);
        }
        if (ops->exit_batch)
                ops->exit_batch(net_exit_list);
}

static void ops_free_list(const struct pernet_operations *ops,
                          struct list_head *net_exit_list)
{
        struct net *net;
        if (ops->size && ops->id) {
                list_for_each_entry(net, net_exit_list, exit_list)
                        ops_free(ops, net);
        }
}

static void rtnl_net_notifyid(struct net *net, struct net *peer, int cmd,
                              int id);
static int alloc_netid(struct net *net, struct net *peer, int reqid)
{
        int min = 0, max = 0, id;

        ASSERT_RTNL();

        if (reqid >= 0) {
                min = reqid;
                max = reqid + 1;
        }

        id = idr_alloc(&net->netns_ids, peer, min, max, GFP_KERNEL);
        if (id >= 0)
                rtnl_net_notifyid(net, peer, RTM_NEWNSID, id);

        return id;
}

/* This function is used by idr_for_each(). If net is equal to peer, the
 * function returns the id so that idr_for_each() stops. Because we cannot
 * returns the id 0 (idr_for_each() will not stop), we return the magic value
 * NET_ID_ZERO (-1) for it.
 */
#define NET_ID_ZERO -1
static int net_eq_idr(int id, void *net, void *peer)
{
        if (net_eq(net, peer))
                return id ? : NET_ID_ZERO;
        return 0;
}

static int __peernet2id(struct net *net, struct net *peer, bool alloc)
{
        int id = idr_for_each(&net->netns_ids, net_eq_idr, peer);

        ASSERT_RTNL();

        /* Magic value for id 0. */
        if (id == NET_ID_ZERO)
                return 0;
        if (id > 0)
                return id;

        if (alloc)
                return alloc_netid(net, peer, -1);

        return -ENOENT;
}

/* This function returns the id of a peer netns. If no id is assigned, one will
 * be allocated and returned.
 */
int peernet2id(struct net *net, struct net *peer)
{
        bool alloc = atomic_read(&peer->count) == 0 ? false : true;
        int id;

        id = __peernet2id(net, peer, alloc);
        return id >= 0 ? id : NETNSA_NSID_NOT_ASSIGNED;
}
EXPORT_SYMBOL(peernet2id);

struct net *get_net_ns_by_id(struct net *net, int id)
{
        struct net *peer;

        if (id < 0)
                return NULL;

        rcu_read_lock();
        peer = idr_find(&net->netns_ids, id);
        if (peer)
                get_net(peer);
        rcu_read_unlock();

        return peer;
}

/*
 * setup_net runs the initializers for the network namespace object.
 */
static __net_init int setup_net(struct net *net, struct user_namespace *user_ns)
{
        /* Must be called with net_mutex held */
        const struct pernet_operations *ops, *saved_ops;
        int error = 0;
        LIST_HEAD(net_exit_list);

        atomic_set(&net->count, 1);
        atomic_set(&net->passive, 1);
        net->dev_base_seq = 1;
        net->user_ns = user_ns;
        idr_init(&net->netns_ids);

        list_for_each_entry(ops, &pernet_list, list) {
                error = ops_init(ops, net);
                if (error < 0)
                        goto out_undo;
        }
out:
        return error;

out_undo:
        /* Walk through the list backwards calling the exit functions
         * for the pernet modules whose init functions did not fail.
         */
        list_add(&net->exit_list, &net_exit_list);
        saved_ops = ops;
        list_for_each_entry_continue_reverse(ops, &pernet_list, list)
                ops_exit_list(ops, &net_exit_list);

        ops = saved_ops;
        list_for_each_entry_continue_reverse(ops, &pernet_list, list)
                ops_free_list(ops, &net_exit_list);

        rcu_barrier();
        goto out;
}


#ifdef CONFIG_NET_NS
static struct kmem_cache *net_cachep;
static struct workqueue_struct *netns_wq;

static struct net *net_alloc(void)
{
        struct net *net = NULL;
        struct net_generic *ng;

        ng = net_alloc_generic();
        if (!ng)
                goto out;

        net = kmem_cache_zalloc(net_cachep, GFP_KERNEL);
        if (!net)
                goto out_free;

        rcu_assign_pointer(net->gen, ng);
out:
        return net;

out_free:
        kfree(ng);
        goto out;
}

static void net_free(struct net *net)
{
        kfree(rcu_access_pointer(net->gen));
        kmem_cache_free(net_cachep, net);
}

void net_drop_ns(void *p)
{
        struct net *ns = p;
        if (ns && atomic_dec_and_test(&ns->passive))
                net_free(ns);
}

struct net *copy_net_ns(unsigned long flags,
                        struct user_namespace *user_ns, struct net *old_net)
{
        struct net *net;
        int rv;

        if (!(flags & CLONE_NEWNET))
                return get_net(old_net);

        net = net_alloc();
        if (!net)
                return ERR_PTR(-ENOMEM);

        get_user_ns(user_ns);

        mutex_lock(&net_mutex);
        rv = setup_net(net, user_ns);
        if (rv == 0) {
                rtnl_lock();
                list_add_tail_rcu(&net->list, &net_namespace_list);
                rtnl_unlock();
        }
        mutex_unlock(&net_mutex);
        if (rv < 0) {
                put_user_ns(user_ns);
                net_drop_ns(net);
                return ERR_PTR(rv);
        }
        return net;
}

static DEFINE_SPINLOCK(cleanup_list_lock);
static LIST_HEAD(cleanup_list);  /* Must hold cleanup_list_lock to touch */

static void cleanup_net(struct work_struct *work)
{
        const struct pernet_operations *ops;
        struct net *net, *tmp;
        struct list_head net_kill_list;
        LIST_HEAD(net_exit_list);

        /* Atomically snapshot the list of namespaces to cleanup */
        spin_lock_irq(&cleanup_list_lock);
        list_replace_init(&cleanup_list, &net_kill_list);
        spin_unlock_irq(&cleanup_list_lock);

        mutex_lock(&net_mutex);

        /* Don't let anyone else find us. */
        rtnl_lock();
        list_for_each_entry(net, &net_kill_list, cleanup_list) {
                list_del_rcu(&net->list);
                list_add_tail(&net->exit_list, &net_exit_list);
                for_each_net(tmp) {
                        int id = __peernet2id(tmp, net, false);

                        if (id >= 0) {
                                rtnl_net_notifyid(tmp, net, RTM_DELNSID, id);
                                idr_remove(&tmp->netns_ids, id);
                        }
                }
                idr_destroy(&net->netns_ids);

        }
        rtnl_unlock();

        /*
         * Another CPU might be rcu-iterating the list, wait for it.
         * This needs to be before calling the exit() notifiers, so
         * the rcu_barrier() below isn't sufficient alone.
         */
        synchronize_rcu();

        /* Run all of the network namespace exit methods */
        list_for_each_entry_reverse(ops, &pernet_list, list)
                ops_exit_list(ops, &net_exit_list);

        /* Free the net generic variables */
        list_for_each_entry_reverse(ops, &pernet_list, list)
                ops_free_list(ops, &net_exit_list);

        mutex_unlock(&net_mutex);

        /* Ensure there are no outstanding rcu callbacks using this
         * network namespace.
         */
        rcu_barrier();

        /* Finally it is safe to free my network namespace structure */
        list_for_each_entry_safe(net, tmp, &net_exit_list, exit_list) {
                list_del_init(&net->exit_list);
                put_user_ns(net->user_ns);
                net_drop_ns(net);
        }
}
static DECLARE_WORK(net_cleanup_work, cleanup_net);

void __put_net(struct net *net)
{
        /* Cleanup the network namespace in process context */
        unsigned long flags;

        spin_lock_irqsave(&cleanup_list_lock, flags);
        list_add(&net->cleanup_list, &cleanup_list);
        spin_unlock_irqrestore(&cleanup_list_lock, flags);

        queue_work(netns_wq, &net_cleanup_work);
}
EXPORT_SYMBOL_GPL(__put_net);

struct net *get_net_ns_by_fd(int fd)
{
        struct file *file;
        struct ns_common *ns;
        struct net *net;

        file = proc_ns_fget(fd);
        if (IS_ERR(file))
                return ERR_CAST(file);

        ns = get_proc_ns(file_inode(file));
        if (ns->ops == &netns_operations)
                net = get_net(container_of(ns, struct net, ns));
        else
                net = ERR_PTR(-EINVAL);

        fput(file);
        return net;
}

#else
struct net *get_net_ns_by_fd(int fd)
{
        return ERR_PTR(-EINVAL);
}
#endif
EXPORT_SYMBOL_GPL(get_net_ns_by_fd);

struct net *get_net_ns_by_pid(pid_t pid)
{
        struct task_struct *tsk;
        struct net *net;

        /* Lookup the network namespace */
        net = ERR_PTR(-ESRCH);
        rcu_read_lock();
        tsk = find_task_by_vpid(pid);
        if (tsk) {
                struct nsproxy *nsproxy;
                task_lock(tsk);
                nsproxy = tsk->nsproxy;
                if (nsproxy)
                        net = get_net(nsproxy->net_ns);
                task_unlock(tsk);
        }
        rcu_read_unlock();
        return net;
}
EXPORT_SYMBOL_GPL(get_net_ns_by_pid);

static __net_init int net_ns_net_init(struct net *net)
{
#ifdef CONFIG_NET_NS
        net->ns.ops = &netns_operations;
#endif
        return ns_alloc_inum(&net->ns);
}

static __net_exit void net_ns_net_exit(struct net *net)
{
        ns_free_inum(&net->ns);
}

static struct pernet_operations __net_initdata net_ns_ops = {
        .init = net_ns_net_init,
        .exit = net_ns_net_exit,
};

static struct nla_policy rtnl_net_policy[NETNSA_MAX + 1] = {
        [NETNSA_NONE]           = { .type = NLA_UNSPEC },
        [NETNSA_NSID]           = { .type = NLA_S32 },
        [NETNSA_PID]            = { .type = NLA_U32 },
        [NETNSA_FD]             = { .type = NLA_U32 },
};

static int rtnl_net_newid(struct sk_buff *skb, struct nlmsghdr *nlh)
{
        struct net *net = sock_net(skb->sk);
        struct nlattr *tb[NETNSA_MAX + 1];
        struct net *peer;
        int nsid, err;

        err = nlmsg_parse(nlh, sizeof(struct rtgenmsg), tb, NETNSA_MAX,
                          rtnl_net_policy);
        if (err < 0)
                return err;
        if (!tb[NETNSA_NSID])
                return -EINVAL;
        nsid = nla_get_s32(tb[NETNSA_NSID]);

        if (tb[NETNSA_PID])
                peer = get_net_ns_by_pid(nla_get_u32(tb[NETNSA_PID]));
        else if (tb[NETNSA_FD])
                peer = get_net_ns_by_fd(nla_get_u32(tb[NETNSA_FD]));
        else
                return -EINVAL;
        if (IS_ERR(peer))
                return PTR_ERR(peer);

        if (__peernet2id(net, peer, false) >= 0) {
                err = -EEXIST;
                goto out;
        }

        err = alloc_netid(net, peer, nsid);
        if (err > 0)
                err = 0;
out:
        put_net(peer);
        return err;
}

static int rtnl_net_get_size(void)
{
        return NLMSG_ALIGN(sizeof(struct rtgenmsg))
               + nla_total_size(sizeof(s32)) /* NETNSA_NSID */
               ;
}

static int rtnl_net_fill(struct sk_buff *skb, u32 portid, u32 seq, int flags,
                         int cmd, struct net *net, struct net *peer,
                         int nsid)
{
        struct nlmsghdr *nlh;
        struct rtgenmsg *rth;
        int id;

        ASSERT_RTNL();

        nlh = nlmsg_put(skb, portid, seq, cmd, sizeof(*rth), flags);
        if (!nlh)
                return -EMSGSIZE;

        rth = nlmsg_data(nlh);
        rth->rtgen_family = AF_UNSPEC;

        if (nsid >= 0) {
                id = nsid;
        } else {
                id = __peernet2id(net, peer, false);
                if  (id < 0)
                        id = NETNSA_NSID_NOT_ASSIGNED;
        }
        if (nla_put_s32(skb, NETNSA_NSID, id))
                goto nla_put_failure;

        nlmsg_end(skb, nlh);
        return 0;

nla_put_failure:
        nlmsg_cancel(skb, nlh);
        return -EMSGSIZE;
}

static int rtnl_net_getid(struct sk_buff *skb, struct nlmsghdr *nlh)
{
        struct net *net = sock_net(skb->sk);
        struct nlattr *tb[NETNSA_MAX + 1];
        struct sk_buff *msg;
        struct net *peer;
        int err;

        err = nlmsg_parse(nlh, sizeof(struct rtgenmsg), tb, NETNSA_MAX,
                          rtnl_net_policy);
        if (err < 0)
                return err;
        if (tb[NETNSA_PID])
                peer = get_net_ns_by_pid(nla_get_u32(tb[NETNSA_PID]));
        else if (tb[NETNSA_FD])
                peer = get_net_ns_by_fd(nla_get_u32(tb[NETNSA_FD]));
        else
                return -EINVAL;

        if (IS_ERR(peer))
                return PTR_ERR(peer);

        msg = nlmsg_new(rtnl_net_get_size(), GFP_KERNEL);
        if (!msg) {
                err = -ENOMEM;
                goto out;
        }

        err = rtnl_net_fill(msg, NETLINK_CB(skb).portid, nlh->nlmsg_seq, 0,
                            RTM_NEWNSID, net, peer, -1);
        if (err < 0)
                goto err_out;

        err = rtnl_unicast(msg, net, NETLINK_CB(skb).portid);
        goto out;

err_out:
        nlmsg_free(msg);
out:
        put_net(peer);
        return err;
}

struct rtnl_net_dump_cb {
        struct net *net;
        struct sk_buff *skb;
        struct netlink_callback *cb;
        int idx;
        int s_idx;
};

static int rtnl_net_dumpid_one(int id, void *peer, void *data)
{
        struct rtnl_net_dump_cb *net_cb = (struct rtnl_net_dump_cb *)data;
        int ret;

        if (net_cb->idx < net_cb->s_idx)
                goto cont;

        ret = rtnl_net_fill(net_cb->skb, NETLINK_CB(net_cb->cb->skb).portid,
                            net_cb->cb->nlh->nlmsg_seq, NLM_F_MULTI,
                            RTM_NEWNSID, net_cb->net, peer, id);
        if (ret < 0)
                return ret;

cont:
        net_cb->idx++;
        return 0;
}

static int rtnl_net_dumpid(struct sk_buff *skb, struct netlink_callback *cb)
{
        struct net *net = sock_net(skb->sk);
        struct rtnl_net_dump_cb net_cb = {
                .net = net,
                .skb = skb,
                .cb = cb,
                .idx = 0,
                .s_idx = cb->args[0],
        };

        ASSERT_RTNL();

        idr_for_each(&net->netns_ids, rtnl_net_dumpid_one, &net_cb);

        cb->args[0] = net_cb.idx;
        return skb->len;
}

static void rtnl_net_notifyid(struct net *net, struct net *peer, int cmd,
                              int id)
{
        struct sk_buff *msg;
        int err = -ENOMEM;

        msg = nlmsg_new(rtnl_net_get_size(), GFP_KERNEL);
        if (!msg)
                goto out;

        err = rtnl_net_fill(msg, 0, 0, 0, cmd, net, peer, id);
        if (err < 0)
                goto err_out;

        rtnl_notify(msg, net, 0, RTNLGRP_NSID, NULL, 0);
        return;

err_out:
        nlmsg_free(msg);
out:
        rtnl_set_sk_err(net, RTNLGRP_NSID, err);
}

static int __init net_ns_init(void)
{
        struct net_generic *ng;

#ifdef CONFIG_NET_NS
        net_cachep = kmem_cache_create("net_namespace", sizeof(struct net),
                                        SMP_CACHE_BYTES,
                                        SLAB_PANIC, NULL);

        /* Create workqueue for cleanup */
        netns_wq = create_singlethread_workqueue("netns");
        if (!netns_wq)
                panic("Could not create netns workq");
#endif

        ng = net_alloc_generic();
        if (!ng)
                panic("Could not allocate generic netns");

        rcu_assign_pointer(init_net.gen, ng);

        mutex_lock(&net_mutex);
        if (setup_net(&init_net, &init_user_ns))
                panic("Could not setup the initial network namespace");

        rtnl_lock();
        list_add_tail_rcu(&init_net.list, &net_namespace_list);
        rtnl_unlock();

        mutex_unlock(&net_mutex);

        register_pernet_subsys(&net_ns_ops);

        rtnl_register(PF_UNSPEC, RTM_NEWNSID, rtnl_net_newid, NULL, NULL);
        rtnl_register(PF_UNSPEC, RTM_GETNSID, rtnl_net_getid, rtnl_net_dumpid,
                      NULL);

        return 0;
}

pure_initcall(net_ns_init);

#ifdef CONFIG_NET_NS
static int __register_pernet_operations(struct list_head *list,
                                        struct pernet_operations *ops)
{
        struct net *net;
        int error;
        LIST_HEAD(net_exit_list);

        list_add_tail(&ops->list, list);
        if (ops->init || (ops->id && ops->size)) {
                for_each_net(net) {
                        error = ops_init(ops, net);
                        if (error)
                                goto out_undo;
                        list_add_tail(&net->exit_list, &net_exit_list);
                }
        }
        return 0;

out_undo:
        /* If I have an error cleanup all namespaces I initialized */
        list_del(&ops->list);
        ops_exit_list(ops, &net_exit_list);
        ops_free_list(ops, &net_exit_list);
        return error;
}

static void __unregister_pernet_operations(struct pernet_operations *ops)
{
        struct net *net;
        LIST_HEAD(net_exit_list);

        list_del(&ops->list);
        for_each_net(net)
                list_add_tail(&net->exit_list, &net_exit_list);
        ops_exit_list(ops, &net_exit_list);
        ops_free_list(ops, &net_exit_list);
}

#else

static int __register_pernet_operations(struct list_head *list,
                                        struct pernet_operations *ops)
{
        return ops_init(ops, &init_net);
}

static void __unregister_pernet_operations(struct pernet_operations *ops)
{
        LIST_HEAD(net_exit_list);
        list_add(&init_net.exit_list, &net_exit_list);
        ops_exit_list(ops, &net_exit_list);
        ops_free_list(ops, &net_exit_list);
}

#endif /* CONFIG_NET_NS */

static DEFINE_IDA(net_generic_ids);

static int register_pernet_operations(struct list_head *list,
                                      struct pernet_operations *ops)
{
        int error;

        if (ops->id) {
again:
                error = ida_get_new_above(&net_generic_ids, 1, ops->id);
                if (error < 0) {
                        if (error == -EAGAIN) {
                                ida_pre_get(&net_generic_ids, GFP_KERNEL);
                                goto again;
                        }
                        return error;
                }
                max_gen_ptrs = max_t(unsigned int, max_gen_ptrs, *ops->id);
        }
        error = __register_pernet_operations(list, ops);
        if (error) {
                rcu_barrier();
                if (ops->id)
                        ida_remove(&net_generic_ids, *ops->id);
        }

        return error;
}

static void unregister_pernet_operations(struct pernet_operations *ops)
{
        
        __unregister_pernet_operations(ops);
        rcu_barrier();
        if (ops->id)
                ida_remove(&net_generic_ids, *ops->id);
}

/**
 *      register_pernet_subsys - register a network namespace subsystem
 *      @ops:  pernet operations structure for the subsystem
 *
 *      Register a subsystem which has init and exit functions
 *      that are called when network namespaces are created and
 *      destroyed respectively.
 *
 *      When registered all network namespace init functions are
 *      called for every existing network namespace.  Allowing kernel
 *      modules to have a race free view of the set of network namespaces.
 *
 *      When a new network namespace is created all of the init
 *      methods are called in the order in which they were registered.
 *
 *      When a network namespace is destroyed all of the exit methods
 *      are called in the reverse of the order with which they were
 *      registered.
 */
int register_pernet_subsys(struct pernet_operations *ops)
{
        int error;
        mutex_lock(&net_mutex);
        error =  register_pernet_operations(first_device, ops);
        mutex_unlock(&net_mutex);
        return error;
}
EXPORT_SYMBOL_GPL(register_pernet_subsys);

/**
 *      unregister_pernet_subsys - unregister a network namespace subsystem
 *      @ops: pernet operations structure to manipulate
 *
 *      Remove the pernet operations structure from the list to be
 *      used when network namespaces are created or destroyed.  In
 *      addition run the exit method for all existing network
 *      namespaces.
 */
void unregister_pernet_subsys(struct pernet_operations *ops)
{
        mutex_lock(&net_mutex);
        unregister_pernet_operations(ops);
        mutex_unlock(&net_mutex);
}
EXPORT_SYMBOL_GPL(unregister_pernet_subsys);

/**
 *      register_pernet_device - register a network namespace device
 *      @ops:  pernet operations structure for the subsystem
 *
 *      Register a device which has init and exit functions
 *      that are called when network namespaces are created and
 *      destroyed respectively.
 *
 *      When registered all network namespace init functions are
 *      called for every existing network namespace.  Allowing kernel
 *      modules to have a race free view of the set of network namespaces.
 *
 *      When a new network namespace is created all of the init
 *      methods are called in the order in which they were registered.
 *
 *      When a network namespace is destroyed all of the exit methods
 *      are called in the reverse of the order with which they were
 *      registered.
 */
int register_pernet_device(struct pernet_operations *ops)
{
        int error;
        mutex_lock(&net_mutex);
        error = register_pernet_operations(&pernet_list, ops);
        if (!error && (first_device == &pernet_list))
                first_device = &ops->list;
        mutex_unlock(&net_mutex);
        return error;
}
EXPORT_SYMBOL_GPL(register_pernet_device);

/**
 *      unregister_pernet_device - unregister a network namespace netdevice
 *      @ops: pernet operations structure to manipulate
 *
 *      Remove the pernet operations structure from the list to be
 *      used when network namespaces are created or destroyed.  In
 *      addition run the exit method for all existing network
 *      namespaces.
 */
void unregister_pernet_device(struct pernet_operations *ops)
{
        mutex_lock(&net_mutex);
        if (&ops->list == first_device)
                first_device = first_device->next;
        unregister_pernet_operations(ops);
        mutex_unlock(&net_mutex);
}
EXPORT_SYMBOL_GPL(unregister_pernet_device);

#ifdef CONFIG_NET_NS
static struct ns_common *netns_get(struct task_struct *task)
{
        struct net *net = NULL;
        struct nsproxy *nsproxy;

        task_lock(task);
        nsproxy = task->nsproxy;
        if (nsproxy)
                net = get_net(nsproxy->net_ns);
        task_unlock(task);

        return net ? &net->ns : NULL;
}

static inline struct net *to_net_ns(struct ns_common *ns)
{
        return container_of(ns, struct net, ns);
}

static void netns_put(struct ns_common *ns)
{
        put_net(to_net_ns(ns));
}

static int netns_install(struct nsproxy *nsproxy, struct ns_common *ns)
{
        struct net *net = to_net_ns(ns);

        if (!ns_capable(net->user_ns, CAP_SYS_ADMIN) ||
            !ns_capable(current_user_ns(), CAP_SYS_ADMIN))
                return -EPERM;

        put_net(nsproxy->net_ns);
        nsproxy->net_ns = get_net(net);
        return 0;
}

const struct proc_ns_operations netns_operations = {
        .name           = "net",
        .type           = CLONE_NEWNET,
        .get            = netns_get,
        .put            = netns_put,
        .install        = netns_install,
};
#endif
```
