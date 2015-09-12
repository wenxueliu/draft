
接受 : 设备内存 --> DMA --> 主存 --> 硬件中断 --> 中断处理 --> 软中断 --> 收包(分配skb)

发送 : 主存 --> DMA --> 设备内存 --> 硬件发送 --> 硬件中断 --> 中断处理(释放skb)

dev_queue_xmit_sk() -->__dev_queue_xmit() --> dev_hard_start_xmit()


##附录

```		Linux/net/core/net-sysfs.h
#ifndef __NET_SYSFS_H__
#define __NET_SYSFS_H__

int __init netdev_kobject_init(void);
int netdev_register_kobject(struct net_device *);
void netdev_unregister_kobject(struct net_device *);
int net_rx_queue_update_kobjects(struct net_device *, int old_num, int new_num);
int netdev_queue_update_kobjects(struct net_device *net,
                                 int old_num, int new_num);

#endif


```

```
/*
 * Linux/net/core/net-sysfs.c
 * 
 * net-sysfs.c - network device class and attributes
 *
 * Copyright (c) 2003 Stephen Hemminger <shemminger@osdl.org>
 *
 *      This program is free software; you can redistribute it and/or
 *      modify it under the terms of the GNU General Public License
 *      as published by the Free Software Foundation; either version
 *      2 of the License, or (at your option) any later version.
 */

#include <linux/capability.h>
#include <linux/kernel.h>
#include <linux/netdevice.h>
#include <net/switchdev.h>
#include <linux/if_arp.h>
#include <linux/slab.h>
#include <linux/nsproxy.h>
#include <net/sock.h>
#include <net/net_namespace.h>
#include <linux/rtnetlink.h>
#include <linux/vmalloc.h>
#include <linux/export.h>
#include <linux/jiffies.h>
#include <linux/pm_runtime.h>
#include <linux/of.h>

#include "net-sysfs.h"

#ifdef CONFIG_SYSFS
static const char fmt_hex[] = "%#x\n";
static const char fmt_long_hex[] = "%#lx\n";
static const char fmt_dec[] = "%d\n";
static const char fmt_udec[] = "%u\n";
static const char fmt_ulong[] = "%lu\n";
static const char fmt_u64[] = "%llu\n";

static inline int dev_isalive(const struct net_device *dev)
{
        return dev->reg_state <= NETREG_REGISTERED;
}

/* use same locking rules as GIF* ioctl's */
static ssize_t netdev_show(const struct device *dev,
                           struct device_attribute *attr, char *buf,
                           ssize_t (*format)(const struct net_device *, char *))
{
        struct net_device *ndev = to_net_dev(dev);
        ssize_t ret = -EINVAL;

        read_lock(&dev_base_lock);
        if (dev_isalive(ndev))
                ret = (*format)(ndev, buf);
        read_unlock(&dev_base_lock);

        return ret;
}

/* generate a show function for simple field */
#define NETDEVICE_SHOW(field, format_string)                            \
static ssize_t format_##field(const struct net_device *dev, char *buf)  \
{                                                                       \
        return sprintf(buf, format_string, dev->field);                 \
}                                                                       \
static ssize_t field##_show(struct device *dev,                         \
                            struct device_attribute *attr, char *buf)   \
{                                                                       \
        return netdev_show(dev, attr, buf, format_##field);             \
}                                                                       \

#define NETDEVICE_SHOW_RO(field, format_string)                         \
NETDEVICE_SHOW(field, format_string);                                   \
static DEVICE_ATTR_RO(field)

#define NETDEVICE_SHOW_RW(field, format_string)                         \
NETDEVICE_SHOW(field, format_string);                                   \
static DEVICE_ATTR_RW(field)

/* use same locking and permission rules as SIF* ioctl's */
static ssize_t netdev_store(struct device *dev, struct device_attribute *attr,
                            const char *buf, size_t len,
                            int (*set)(struct net_device *, unsigned long))
{
        struct net_device *netdev = to_net_dev(dev);
        struct net *net = dev_net(netdev);
        unsigned long new;
        int ret = -EINVAL;

        if (!ns_capable(net->user_ns, CAP_NET_ADMIN))
                return -EPERM;

        ret = kstrtoul(buf, 0, &new);
        if (ret)
                goto err;

        if (!rtnl_trylock())
                return restart_syscall();

        if (dev_isalive(netdev)) {
                if ((ret = (*set)(netdev, new)) == 0)
                        ret = len;
        }
        rtnl_unlock();
 err:
        return ret;
}

NETDEVICE_SHOW_RO(dev_id, fmt_hex);
NETDEVICE_SHOW_RO(dev_port, fmt_dec);
NETDEVICE_SHOW_RO(addr_assign_type, fmt_dec);
NETDEVICE_SHOW_RO(addr_len, fmt_dec);
NETDEVICE_SHOW_RO(ifindex, fmt_dec);
NETDEVICE_SHOW_RO(type, fmt_dec);
NETDEVICE_SHOW_RO(link_mode, fmt_dec);

static ssize_t iflink_show(struct device *dev, struct device_attribute *attr,
                           char *buf)
{
        struct net_device *ndev = to_net_dev(dev);

        return sprintf(buf, fmt_dec, dev_get_iflink(ndev));
}
static DEVICE_ATTR_RO(iflink);

static ssize_t format_name_assign_type(const struct net_device *dev, char *buf)
{
        return sprintf(buf, fmt_dec, dev->name_assign_type);
}

static ssize_t name_assign_type_show(struct device *dev,
                                     struct device_attribute *attr,
                                     char *buf)
{
        struct net_device *ndev = to_net_dev(dev);
        ssize_t ret = -EINVAL;

        if (ndev->name_assign_type != NET_NAME_UNKNOWN)
                ret = netdev_show(dev, attr, buf, format_name_assign_type);

        return ret;
}
static DEVICE_ATTR_RO(name_assign_type);

/* use same locking rules as GIFHWADDR ioctl's */
static ssize_t address_show(struct device *dev, struct device_attribute *attr,
                            char *buf)
{
        struct net_device *ndev = to_net_dev(dev);
        ssize_t ret = -EINVAL;

        read_lock(&dev_base_lock);
        if (dev_isalive(ndev))
                ret = sysfs_format_mac(buf, ndev->dev_addr, ndev->addr_len);
        read_unlock(&dev_base_lock);
        return ret;
}
static DEVICE_ATTR_RO(address);

static ssize_t broadcast_show(struct device *dev,
                              struct device_attribute *attr, char *buf)
{
        struct net_device *ndev = to_net_dev(dev);
        if (dev_isalive(ndev))
                return sysfs_format_mac(buf, ndev->broadcast, ndev->addr_len);
        return -EINVAL;
}
static DEVICE_ATTR_RO(broadcast);

static int change_carrier(struct net_device *dev, unsigned long new_carrier)
{
        if (!netif_running(dev))
                return -EINVAL;
        return dev_change_carrier(dev, (bool) new_carrier);
}

static ssize_t carrier_store(struct device *dev, struct device_attribute *attr,
                             const char *buf, size_t len)
{
        return netdev_store(dev, attr, buf, len, change_carrier);
}

static ssize_t carrier_show(struct device *dev,
                            struct device_attribute *attr, char *buf)
{
        struct net_device *netdev = to_net_dev(dev);
        if (netif_running(netdev)) {
                return sprintf(buf, fmt_dec, !!netif_carrier_ok(netdev));
        }
        return -EINVAL;
}
static DEVICE_ATTR_RW(carrier);

static ssize_t speed_show(struct device *dev,
                          struct device_attribute *attr, char *buf)
{
        struct net_device *netdev = to_net_dev(dev);
        int ret = -EINVAL;

        if (!rtnl_trylock())
                return restart_syscall();

        if (netif_running(netdev)) {
                struct ethtool_cmd cmd;
                if (!__ethtool_get_settings(netdev, &cmd))
                        ret = sprintf(buf, fmt_udec, ethtool_cmd_speed(&cmd));
        }
        rtnl_unlock();
        return ret;
}
static DEVICE_ATTR_RO(speed);

static ssize_t duplex_show(struct device *dev,
                           struct device_attribute *attr, char *buf)
{
        struct net_device *netdev = to_net_dev(dev);
        int ret = -EINVAL;

        if (!rtnl_trylock())
                return restart_syscall();

        if (netif_running(netdev)) {
                struct ethtool_cmd cmd;
                if (!__ethtool_get_settings(netdev, &cmd)) {
                        const char *duplex;
                        switch (cmd.duplex) {
                        case DUPLEX_HALF:
                                duplex = "half";
                                break;
                        case DUPLEX_FULL:
                                duplex = "full";
                                break;
                        default:
                                duplex = "unknown";
                                break;
                        }
                        ret = sprintf(buf, "%s\n", duplex);
                }
        }
        rtnl_unlock();
        return ret;
}
static DEVICE_ATTR_RO(duplex);

static ssize_t dormant_show(struct device *dev,
                            struct device_attribute *attr, char *buf)
{
        struct net_device *netdev = to_net_dev(dev);

        if (netif_running(netdev))
                return sprintf(buf, fmt_dec, !!netif_dormant(netdev));

        return -EINVAL;
}
static DEVICE_ATTR_RO(dormant);

static const char *const operstates[] = {
        "unknown",
        "notpresent", /* currently unused */
        "down",
        "lowerlayerdown",
        "testing", /* currently unused */
        "dormant",
        "up"
};

static ssize_t operstate_show(struct device *dev,
                              struct device_attribute *attr, char *buf)
{
        const struct net_device *netdev = to_net_dev(dev);
        unsigned char operstate;

        read_lock(&dev_base_lock);
        operstate = netdev->operstate;
        if (!netif_running(netdev))
                operstate = IF_OPER_DOWN;
        read_unlock(&dev_base_lock);

        if (operstate >= ARRAY_SIZE(operstates))
                return -EINVAL; /* should not happen */

        return sprintf(buf, "%s\n", operstates[operstate]);
}
static DEVICE_ATTR_RO(operstate);

static ssize_t carrier_changes_show(struct device *dev,
                                    struct device_attribute *attr,
                                    char *buf)
{
        struct net_device *netdev = to_net_dev(dev);
        return sprintf(buf, fmt_dec,
                       atomic_read(&netdev->carrier_changes));
}
static DEVICE_ATTR_RO(carrier_changes);

/* read-write attributes */

static int change_mtu(struct net_device *dev, unsigned long new_mtu)
{
        return dev_set_mtu(dev, (int) new_mtu);
}

static ssize_t mtu_store(struct device *dev, struct device_attribute *attr,
                         const char *buf, size_t len)
{
        return netdev_store(dev, attr, buf, len, change_mtu);
}
NETDEVICE_SHOW_RW(mtu, fmt_dec);

static int change_flags(struct net_device *dev, unsigned long new_flags)
{
        return dev_change_flags(dev, (unsigned int) new_flags);
}

static ssize_t flags_store(struct device *dev, struct device_attribute *attr,
                           const char *buf, size_t len)
{
        return netdev_store(dev, attr, buf, len, change_flags);
}
NETDEVICE_SHOW_RW(flags, fmt_hex);

static int change_tx_queue_len(struct net_device *dev, unsigned long new_len)
{
        dev->tx_queue_len = new_len;
        return 0;
}

static ssize_t tx_queue_len_store(struct device *dev,
                                  struct device_attribute *attr,
                                  const char *buf, size_t len)
{
        if (!capable(CAP_NET_ADMIN))
                return -EPERM;

        return netdev_store(dev, attr, buf, len, change_tx_queue_len);
}
NETDEVICE_SHOW_RW(tx_queue_len, fmt_ulong);

static int change_gro_flush_timeout(struct net_device *dev, unsigned long val)
{
        dev->gro_flush_timeout = val;
        return 0;
}

static ssize_t gro_flush_timeout_store(struct device *dev,
                                  struct device_attribute *attr,
                                  const char *buf, size_t len)
{
        if (!capable(CAP_NET_ADMIN))
                return -EPERM;

        return netdev_store(dev, attr, buf, len, change_gro_flush_timeout);
}
NETDEVICE_SHOW_RW(gro_flush_timeout, fmt_ulong);

static ssize_t ifalias_store(struct device *dev, struct device_attribute *attr,
                             const char *buf, size_t len)
{
        struct net_device *netdev = to_net_dev(dev);
        struct net *net = dev_net(netdev);
        size_t count = len;
        ssize_t ret;

        if (!ns_capable(net->user_ns, CAP_NET_ADMIN))
                return -EPERM;

        /* ignore trailing newline */
        if (len >  0 && buf[len - 1] == '\n')
                --count;

        if (!rtnl_trylock())
                return restart_syscall();
        ret = dev_set_alias(netdev, buf, count);
        rtnl_unlock();

        return ret < 0 ? ret : len;
}

static ssize_t ifalias_show(struct device *dev,
                            struct device_attribute *attr, char *buf)
{
        const struct net_device *netdev = to_net_dev(dev);
        ssize_t ret = 0;

        if (!rtnl_trylock())
                return restart_syscall();
        if (netdev->ifalias)
                ret = sprintf(buf, "%s\n", netdev->ifalias);
        rtnl_unlock();
        return ret;
}
static DEVICE_ATTR_RW(ifalias);

static int change_group(struct net_device *dev, unsigned long new_group)
{
        dev_set_group(dev, (int) new_group);
        return 0;
}

static ssize_t group_store(struct device *dev, struct device_attribute *attr,
                           const char *buf, size_t len)
{
        return netdev_store(dev, attr, buf, len, change_group);
}
NETDEVICE_SHOW(group, fmt_dec);
static DEVICE_ATTR(netdev_group, S_IRUGO | S_IWUSR, group_show, group_store);

static ssize_t phys_port_id_show(struct device *dev,
                                 struct device_attribute *attr, char *buf)
{
        struct net_device *netdev = to_net_dev(dev);
        ssize_t ret = -EINVAL;

        if (!rtnl_trylock())
                return restart_syscall();

        if (dev_isalive(netdev)) {
                struct netdev_phys_item_id ppid;

                ret = dev_get_phys_port_id(netdev, &ppid);
                if (!ret)
                        ret = sprintf(buf, "%*phN\n", ppid.id_len, ppid.id);
        }
        rtnl_unlock();

        return ret;
}
static DEVICE_ATTR_RO(phys_port_id);

static ssize_t phys_port_name_show(struct device *dev,
                                   struct device_attribute *attr, char *buf)
{
        struct net_device *netdev = to_net_dev(dev);
        ssize_t ret = -EINVAL;

        if (!rtnl_trylock())
                return restart_syscall();

        if (dev_isalive(netdev)) {
                char name[IFNAMSIZ];

                ret = dev_get_phys_port_name(netdev, name, sizeof(name));
                if (!ret)
                        ret = sprintf(buf, "%s\n", name);
        }
        rtnl_unlock();

        return ret;
}
static DEVICE_ATTR_RO(phys_port_name);

static ssize_t phys_switch_id_show(struct device *dev,
                                   struct device_attribute *attr, char *buf)
{
        struct net_device *netdev = to_net_dev(dev);
        ssize_t ret = -EINVAL;

        if (!rtnl_trylock())
                return restart_syscall();

        if (dev_isalive(netdev)) {
                struct netdev_phys_item_id ppid;

                ret = netdev_switch_parent_id_get(netdev, &ppid);
                if (!ret)
                        ret = sprintf(buf, "%*phN\n", ppid.id_len, ppid.id);
        }
        rtnl_unlock();

        return ret;
}
static DEVICE_ATTR_RO(phys_switch_id);

static struct attribute *net_class_attrs[] = {
        &dev_attr_netdev_group.attr,
        &dev_attr_type.attr,
        &dev_attr_dev_id.attr,
        &dev_attr_dev_port.attr,
        &dev_attr_iflink.attr,
        &dev_attr_ifindex.attr,
        &dev_attr_name_assign_type.attr,
        &dev_attr_addr_assign_type.attr,
        &dev_attr_addr_len.attr,
        &dev_attr_link_mode.attr,
        &dev_attr_address.attr,
        &dev_attr_broadcast.attr,
        &dev_attr_speed.attr,
        &dev_attr_duplex.attr,
        &dev_attr_dormant.attr,
        &dev_attr_operstate.attr,
        &dev_attr_carrier_changes.attr,
        &dev_attr_ifalias.attr,
        &dev_attr_carrier.attr,
        &dev_attr_mtu.attr,
        &dev_attr_flags.attr,
        &dev_attr_tx_queue_len.attr,
        &dev_attr_gro_flush_timeout.attr,
        &dev_attr_phys_port_id.attr,
        &dev_attr_phys_port_name.attr,
        &dev_attr_phys_switch_id.attr,
        NULL,
};
ATTRIBUTE_GROUPS(net_class);

/* Show a given an attribute in the statistics group */
static ssize_t netstat_show(const struct device *d,
                            struct device_attribute *attr, char *buf,
                            unsigned long offset)
{
        struct net_device *dev = to_net_dev(d);
        ssize_t ret = -EINVAL;

        WARN_ON(offset > sizeof(struct rtnl_link_stats64) ||
                        offset % sizeof(u64) != 0);

        read_lock(&dev_base_lock);
        if (dev_isalive(dev)) {
                struct rtnl_link_stats64 temp;
                const struct rtnl_link_stats64 *stats = dev_get_stats(dev, &temp);

                ret = sprintf(buf, fmt_u64, *(u64 *)(((u8 *) stats) + offset));
        }
        read_unlock(&dev_base_lock);
        return ret;
}

/* generate a read-only statistics attribute */
#define NETSTAT_ENTRY(name)                                             \
static ssize_t name##_show(struct device *d,                            \
                           struct device_attribute *attr, char *buf)    \
{                                                                       \
        return netstat_show(d, attr, buf,                               \
                            offsetof(struct rtnl_link_stats64, name));  \
}                                                                       \
static DEVICE_ATTR_RO(name)

NETSTAT_ENTRY(rx_packets);
NETSTAT_ENTRY(tx_packets);
NETSTAT_ENTRY(rx_bytes);
NETSTAT_ENTRY(tx_bytes);
NETSTAT_ENTRY(rx_errors);
NETSTAT_ENTRY(tx_errors);
NETSTAT_ENTRY(rx_dropped);
NETSTAT_ENTRY(tx_dropped);
NETSTAT_ENTRY(multicast);
NETSTAT_ENTRY(collisions);
NETSTAT_ENTRY(rx_length_errors);
NETSTAT_ENTRY(rx_over_errors);
NETSTAT_ENTRY(rx_crc_errors);
NETSTAT_ENTRY(rx_frame_errors);
NETSTAT_ENTRY(rx_fifo_errors);
NETSTAT_ENTRY(rx_missed_errors);
NETSTAT_ENTRY(tx_aborted_errors);
NETSTAT_ENTRY(tx_carrier_errors);
NETSTAT_ENTRY(tx_fifo_errors);
NETSTAT_ENTRY(tx_heartbeat_errors);
NETSTAT_ENTRY(tx_window_errors);
NETSTAT_ENTRY(rx_compressed);
NETSTAT_ENTRY(tx_compressed);

static struct attribute *netstat_attrs[] = {
        &dev_attr_rx_packets.attr,
        &dev_attr_tx_packets.attr,
        &dev_attr_rx_bytes.attr,
        &dev_attr_tx_bytes.attr,
        &dev_attr_rx_errors.attr,
        &dev_attr_tx_errors.attr,
        &dev_attr_rx_dropped.attr,
        &dev_attr_tx_dropped.attr,
        &dev_attr_multicast.attr,
        &dev_attr_collisions.attr,
        &dev_attr_rx_length_errors.attr,
        &dev_attr_rx_over_errors.attr,
        &dev_attr_rx_crc_errors.attr,
        &dev_attr_rx_frame_errors.attr,
        &dev_attr_rx_fifo_errors.attr,
        &dev_attr_rx_missed_errors.attr,
        &dev_attr_tx_aborted_errors.attr,
        &dev_attr_tx_carrier_errors.attr,
        &dev_attr_tx_fifo_errors.attr,
        &dev_attr_tx_heartbeat_errors.attr,
        &dev_attr_tx_window_errors.attr,
        &dev_attr_rx_compressed.attr,
        &dev_attr_tx_compressed.attr,
        NULL
};


static struct attribute_group netstat_group = {
        .name  = "statistics",
        .attrs  = netstat_attrs,
};

#if IS_ENABLED(CONFIG_WIRELESS_EXT) || IS_ENABLED(CONFIG_CFG80211)
static struct attribute *wireless_attrs[] = {
        NULL
};

static struct attribute_group wireless_group = {
        .name = "wireless",
        .attrs = wireless_attrs,
};
#endif

#else /* CONFIG_SYSFS */
#define net_class_groups        NULL
#endif /* CONFIG_SYSFS */

#ifdef CONFIG_SYSFS
#define to_rx_queue_attr(_attr) container_of(_attr,             \
    struct rx_queue_attribute, attr)

#define to_rx_queue(obj) container_of(obj, struct netdev_rx_queue, kobj)

static ssize_t rx_queue_attr_show(struct kobject *kobj, struct attribute *attr,
                                  char *buf)
{
        struct rx_queue_attribute *attribute = to_rx_queue_attr(attr);
        struct netdev_rx_queue *queue = to_rx_queue(kobj);

        if (!attribute->show)
                return -EIO;

        return attribute->show(queue, attribute, buf);
}

static ssize_t rx_queue_attr_store(struct kobject *kobj, struct attribute *attr,
                                   const char *buf, size_t count)
{
        struct rx_queue_attribute *attribute = to_rx_queue_attr(attr);
        struct netdev_rx_queue *queue = to_rx_queue(kobj);

        if (!attribute->store)
                return -EIO;

        return attribute->store(queue, attribute, buf, count);
}

static const struct sysfs_ops rx_queue_sysfs_ops = {
        .show = rx_queue_attr_show,
        .store = rx_queue_attr_store,
};

#ifdef CONFIG_RPS
static ssize_t show_rps_map(struct netdev_rx_queue *queue,
                            struct rx_queue_attribute *attribute, char *buf)
{
        struct rps_map *map;
        cpumask_var_t mask;
        int i, len;

        if (!zalloc_cpumask_var(&mask, GFP_KERNEL))
                return -ENOMEM;

        rcu_read_lock();
        map = rcu_dereference(queue->rps_map);
        if (map)
                for (i = 0; i < map->len; i++)
                        cpumask_set_cpu(map->cpus[i], mask);

        len = snprintf(buf, PAGE_SIZE, "%*pb\n", cpumask_pr_args(mask));
        rcu_read_unlock();
        free_cpumask_var(mask);

        return len < PAGE_SIZE ? len : -EINVAL;
}

static ssize_t store_rps_map(struct netdev_rx_queue *queue,
                      struct rx_queue_attribute *attribute,
                      const char *buf, size_t len)
{
        struct rps_map *old_map, *map;
        cpumask_var_t mask;
        int err, cpu, i;
        static DEFINE_SPINLOCK(rps_map_lock);

        if (!capable(CAP_NET_ADMIN))
                return -EPERM;

        if (!alloc_cpumask_var(&mask, GFP_KERNEL))
                return -ENOMEM;

        err = bitmap_parse(buf, len, cpumask_bits(mask), nr_cpumask_bits);
        if (err) {
                free_cpumask_var(mask);
                return err;
        }

        map = kzalloc(max_t(unsigned int,
            RPS_MAP_SIZE(cpumask_weight(mask)), L1_CACHE_BYTES),
            GFP_KERNEL);
        if (!map) {
                free_cpumask_var(mask);
                return -ENOMEM;
        }

        i = 0;
        for_each_cpu_and(cpu, mask, cpu_online_mask)
                map->cpus[i++] = cpu;

        if (i)
                map->len = i;
        else {
                kfree(map);
                map = NULL;
        }

        spin_lock(&rps_map_lock);
        old_map = rcu_dereference_protected(queue->rps_map,
                                            lockdep_is_held(&rps_map_lock));
        rcu_assign_pointer(queue->rps_map, map);
        spin_unlock(&rps_map_lock);

        if (map)
                static_key_slow_inc(&rps_needed);
        if (old_map) {
                kfree_rcu(old_map, rcu);
                static_key_slow_dec(&rps_needed);
        }
        free_cpumask_var(mask);
        return len;
}

static ssize_t show_rps_dev_flow_table_cnt(struct netdev_rx_queue *queue,
                                           struct rx_queue_attribute *attr,
                                           char *buf)
{
        struct rps_dev_flow_table *flow_table;
        unsigned long val = 0;

        rcu_read_lock();
        flow_table = rcu_dereference(queue->rps_flow_table);
        if (flow_table)
                val = (unsigned long)flow_table->mask + 1;
        rcu_read_unlock();

        return sprintf(buf, "%lu\n", val);
}

static void rps_dev_flow_table_release(struct rcu_head *rcu)
{
        struct rps_dev_flow_table *table = container_of(rcu,
            struct rps_dev_flow_table, rcu);
        vfree(table);
}

static ssize_t store_rps_dev_flow_table_cnt(struct netdev_rx_queue *queue,
                                     struct rx_queue_attribute *attr,
                                     const char *buf, size_t len)
{
        unsigned long mask, count;
        struct rps_dev_flow_table *table, *old_table;
        static DEFINE_SPINLOCK(rps_dev_flow_lock);
        int rc;

        if (!capable(CAP_NET_ADMIN))
                return -EPERM;

        rc = kstrtoul(buf, 0, &count);
        if (rc < 0)
                return rc;

        if (count) {
                mask = count - 1;
                /* mask = roundup_pow_of_two(count) - 1;
                 * without overflows...
                 */
                while ((mask | (mask >> 1)) != mask)
                        mask |= (mask >> 1);
                /* On 64 bit arches, must check mask fits in table->mask (u32),
                 * and on 32bit arches, must check
                 * RPS_DEV_FLOW_TABLE_SIZE(mask + 1) doesn't overflow.
                 */
#if BITS_PER_LONG > 32
                if (mask > (unsigned long)(u32)mask)
                        return -EINVAL;
#else
                if (mask > (ULONG_MAX - RPS_DEV_FLOW_TABLE_SIZE(1))
                                / sizeof(struct rps_dev_flow)) {
                        /* Enforce a limit to prevent overflow */
                        return -EINVAL;
                }
#endif
                table = vmalloc(RPS_DEV_FLOW_TABLE_SIZE(mask + 1));
                if (!table)
                        return -ENOMEM;

                table->mask = mask;
                for (count = 0; count <= mask; count++)
                        table->flows[count].cpu = RPS_NO_CPU;
        } else
                table = NULL;

        spin_lock(&rps_dev_flow_lock);
        old_table = rcu_dereference_protected(queue->rps_flow_table,
                                              lockdep_is_held(&rps_dev_flow_lock));
        rcu_assign_pointer(queue->rps_flow_table, table);
        spin_unlock(&rps_dev_flow_lock);

        if (old_table)
                call_rcu(&old_table->rcu, rps_dev_flow_table_release);

        return len;
}

static struct rx_queue_attribute rps_cpus_attribute =
        __ATTR(rps_cpus, S_IRUGO | S_IWUSR, show_rps_map, store_rps_map);


static struct rx_queue_attribute rps_dev_flow_table_cnt_attribute =
        __ATTR(rps_flow_cnt, S_IRUGO | S_IWUSR,
            show_rps_dev_flow_table_cnt, store_rps_dev_flow_table_cnt);
#endif /* CONFIG_RPS */

static struct attribute *rx_queue_default_attrs[] = {
#ifdef CONFIG_RPS
        &rps_cpus_attribute.attr,
        &rps_dev_flow_table_cnt_attribute.attr,
#endif
        NULL
};

static void rx_queue_release(struct kobject *kobj)
{
        struct netdev_rx_queue *queue = to_rx_queue(kobj);
#ifdef CONFIG_RPS
        struct rps_map *map;
        struct rps_dev_flow_table *flow_table;


        map = rcu_dereference_protected(queue->rps_map, 1);
        if (map) {
                RCU_INIT_POINTER(queue->rps_map, NULL);
                kfree_rcu(map, rcu);
        }

        flow_table = rcu_dereference_protected(queue->rps_flow_table, 1);
        if (flow_table) {
                RCU_INIT_POINTER(queue->rps_flow_table, NULL);
                call_rcu(&flow_table->rcu, rps_dev_flow_table_release);
        }
#endif

        memset(kobj, 0, sizeof(*kobj));
        dev_put(queue->dev);
}

static const void *rx_queue_namespace(struct kobject *kobj)
{
        struct netdev_rx_queue *queue = to_rx_queue(kobj);
        struct device *dev = &queue->dev->dev;
        const void *ns = NULL;

        if (dev->class && dev->class->ns_type)
                ns = dev->class->namespace(dev);

        return ns;
}

static struct kobj_type rx_queue_ktype = {
        .sysfs_ops = &rx_queue_sysfs_ops,
        .release = rx_queue_release,
        .default_attrs = rx_queue_default_attrs,
        .namespace = rx_queue_namespace
};

static int rx_queue_add_kobject(struct net_device *dev, int index)
{
        struct netdev_rx_queue *queue = dev->_rx + index;
        struct kobject *kobj = &queue->kobj;
        int error = 0;

        kobj->kset = dev->queues_kset;
        error = kobject_init_and_add(kobj, &rx_queue_ktype, NULL,
            "rx-%u", index);
        if (error)
                goto exit;

        if (dev->sysfs_rx_queue_group) {
                error = sysfs_create_group(kobj, dev->sysfs_rx_queue_group);
                if (error)
                        goto exit;
        }

        kobject_uevent(kobj, KOBJ_ADD);
        dev_hold(queue->dev);

        return error;
exit:
        kobject_put(kobj);
        return error;
}
#endif /* CONFIG_SYSFS */

int
net_rx_queue_update_kobjects(struct net_device *dev, int old_num, int new_num)
{
#ifdef CONFIG_SYSFS
        int i;
        int error = 0;

#ifndef CONFIG_RPS
        if (!dev->sysfs_rx_queue_group)
                return 0;
#endif
        for (i = old_num; i < new_num; i++) {
                error = rx_queue_add_kobject(dev, i);
                if (error) {
                        new_num = old_num;
                        break;
                }
        }

        while (--i >= new_num) {
                if (dev->sysfs_rx_queue_group)
                        sysfs_remove_group(&dev->_rx[i].kobj,
                                           dev->sysfs_rx_queue_group);
                kobject_put(&dev->_rx[i].kobj);
        }

        return error;
#else
        return 0;
#endif
}

#ifdef CONFIG_SYSFS
/*
 * netdev_queue sysfs structures and functions.
 */
struct netdev_queue_attribute {
        struct attribute attr;
        ssize_t (*show)(struct netdev_queue *queue,
            struct netdev_queue_attribute *attr, char *buf);
        ssize_t (*store)(struct netdev_queue *queue,
            struct netdev_queue_attribute *attr, const char *buf, size_t len);
};
#define to_netdev_queue_attr(_attr) container_of(_attr,         \
    struct netdev_queue_attribute, attr)

#define to_netdev_queue(obj) container_of(obj, struct netdev_queue, kobj)

static ssize_t netdev_queue_attr_show(struct kobject *kobj,
                                      struct attribute *attr, char *buf)
{
        struct netdev_queue_attribute *attribute = to_netdev_queue_attr(attr);
        struct netdev_queue *queue = to_netdev_queue(kobj);

        if (!attribute->show)
                return -EIO;

        return attribute->show(queue, attribute, buf);
}

static ssize_t netdev_queue_attr_store(struct kobject *kobj,
                                       struct attribute *attr,
                                       const char *buf, size_t count)
{
        struct netdev_queue_attribute *attribute = to_netdev_queue_attr(attr);
        struct netdev_queue *queue = to_netdev_queue(kobj);

        if (!attribute->store)
                return -EIO;

        return attribute->store(queue, attribute, buf, count);
}

static const struct sysfs_ops netdev_queue_sysfs_ops = {
        .show = netdev_queue_attr_show,
        .store = netdev_queue_attr_store,
};

static ssize_t show_trans_timeout(struct netdev_queue *queue,
                                  struct netdev_queue_attribute *attribute,
                                  char *buf)
{
        unsigned long trans_timeout;

        spin_lock_irq(&queue->_xmit_lock);
        trans_timeout = queue->trans_timeout;
        spin_unlock_irq(&queue->_xmit_lock);

        return sprintf(buf, "%lu", trans_timeout);
}

#ifdef CONFIG_XPS
static inline unsigned int get_netdev_queue_index(struct netdev_queue *queue)
{
        struct net_device *dev = queue->dev;
        int i;

        for (i = 0; i < dev->num_tx_queues; i++)
                if (queue == &dev->_tx[i])
                        break;

        BUG_ON(i >= dev->num_tx_queues);

        return i;
}

 static ssize_t show_tx_maxrate(struct netdev_queue *queue,
                                struct netdev_queue_attribute *attribute,
                                char *buf)
 {
         return sprintf(buf, "%lu\n", queue->tx_maxrate);
 }
 
 static ssize_t set_tx_maxrate(struct netdev_queue *queue,
                               struct netdev_queue_attribute *attribute,
                               const char *buf, size_t len)
 {
         struct net_device *dev = queue->dev;
         int err, index = get_netdev_queue_index(queue);
         u32 rate = 0;
 
         err = kstrtou32(buf, 10, &rate);
         if (err < 0)
                 return err;
 
         if (!rtnl_trylock())
                 return restart_syscall();
 
         err = -EOPNOTSUPP;
         if (dev->netdev_ops->ndo_set_tx_maxrate)
                 err = dev->netdev_ops->ndo_set_tx_maxrate(dev, index, rate);
 
         rtnl_unlock();
         if (!err) {
                 queue->tx_maxrate = rate;
                 return len;
         }
         return err;
 }
 
 static struct netdev_queue_attribute queue_tx_maxrate =
         __ATTR(tx_maxrate, S_IRUGO | S_IWUSR,
                show_tx_maxrate, set_tx_maxrate);
 #endif
 
 static struct netdev_queue_attribute queue_trans_timeout =
         __ATTR(tx_timeout, S_IRUGO, show_trans_timeout, NULL);
 
 #ifdef CONFIG_BQL
 /*
  * Byte queue limits sysfs structures and functions.
  */
 static ssize_t bql_show(char *buf, unsigned int value)
 {
         return sprintf(buf, "%u\n", value);
 }
 
 static ssize_t bql_set(const char *buf, const size_t count,
                        unsigned int *pvalue)
 {
         unsigned int value;
         int err;
 
         if (!strcmp(buf, "max") || !strcmp(buf, "max\n"))
                 value = DQL_MAX_LIMIT;
         else {
                 err = kstrtouint(buf, 10, &value);
                 if (err < 0)
                         return err;
                 if (value > DQL_MAX_LIMIT)
                         return -EINVAL;
         }
 
         *pvalue = value;
 
         return count;
 }
 
 static ssize_t bql_show_hold_time(struct netdev_queue *queue,
                                   struct netdev_queue_attribute *attr,
                                   char *buf)
 {
         struct dql *dql = &queue->dql;
 
         return sprintf(buf, "%u\n", jiffies_to_msecs(dql->slack_hold_time));
 }
 
 static ssize_t bql_set_hold_time(struct netdev_queue *queue,
                                  struct netdev_queue_attribute *attribute,
                                  const char *buf, size_t len)
 {
         struct dql *dql = &queue->dql;
         unsigned int value;
         int err;
 
         err = kstrtouint(buf, 10, &value);
         if (err < 0)
                 return err;
 
         dql->slack_hold_time = msecs_to_jiffies(value);
 
         return len;
 }
 
 static struct netdev_queue_attribute bql_hold_time_attribute =
         __ATTR(hold_time, S_IRUGO | S_IWUSR, bql_show_hold_time,
             bql_set_hold_time);
 
 static ssize_t bql_show_inflight(struct netdev_queue *queue,
                                  struct netdev_queue_attribute *attr,
                                  char *buf)
 {
         struct dql *dql = &queue->dql;
 
         return sprintf(buf, "%u\n", dql->num_queued - dql->num_completed);
 }
 
 static struct netdev_queue_attribute bql_inflight_attribute =
         __ATTR(inflight, S_IRUGO, bql_show_inflight, NULL);
 
 #define BQL_ATTR(NAME, FIELD)                                           \
 static ssize_t bql_show_ ## NAME(struct netdev_queue *queue,            \
                                  struct netdev_queue_attribute *attr,   \
                                  char *buf)                             \
 {                                                                       \
         return bql_show(buf, queue->dql.FIELD);                         \
 }                                                                       \
                                                                         \
 static ssize_t bql_set_ ## NAME(struct netdev_queue *queue,             \
                                 struct netdev_queue_attribute *attr,    \
                                 const char *buf, size_t len)            \
 {                                                                       \
         return bql_set(buf, len, &queue->dql.FIELD);                    \
 }                                                                       \
                                                                         \
 static struct netdev_queue_attribute bql_ ## NAME ## _attribute =       \
         __ATTR(NAME, S_IRUGO | S_IWUSR, bql_show_ ## NAME,              \
             bql_set_ ## NAME);
 
 BQL_ATTR(limit, limit)
 BQL_ATTR(limit_max, max_limit)
 BQL_ATTR(limit_min, min_limit)
 
 static struct attribute *dql_attrs[] = {
         &bql_limit_attribute.attr,
         &bql_limit_max_attribute.attr,
         &bql_limit_min_attribute.attr,
         &bql_hold_time_attribute.attr,
         &bql_inflight_attribute.attr,
         NULL
 };
 
 static struct attribute_group dql_group = {
         .name  = "byte_queue_limits",
         .attrs  = dql_attrs,
 };
 #endif /* CONFIG_BQL */
 
 #ifdef CONFIG_XPS
 static ssize_t show_xps_map(struct netdev_queue *queue,
                             struct netdev_queue_attribute *attribute, char *buf)
 {
         struct net_device *dev = queue->dev;
         struct xps_dev_maps *dev_maps;
         cpumask_var_t mask;
         unsigned long index;
         int i, len;
 
         if (!zalloc_cpumask_var(&mask, GFP_KERNEL))
                 return -ENOMEM;
 
         index = get_netdev_queue_index(queue);
 
         rcu_read_lock();
         dev_maps = rcu_dereference(dev->xps_maps);
         if (dev_maps) {
                 for_each_possible_cpu(i) {
                         struct xps_map *map =
                             rcu_dereference(dev_maps->cpu_map[i]);
                         if (map) {
                                 int j;
                                 for (j = 0; j < map->len; j++) {
                                         if (map->queues[j] == index) {
                                                 cpumask_set_cpu(i, mask);
                                                 break;
                                         }
                                 }
                         }
                 }
         }
         rcu_read_unlock();
 
         len = snprintf(buf, PAGE_SIZE, "%*pb\n", cpumask_pr_args(mask));
         free_cpumask_var(mask);
         return len < PAGE_SIZE ? len : -EINVAL;
 }
 
 static ssize_t store_xps_map(struct netdev_queue *queue,
                       struct netdev_queue_attribute *attribute,
                       const char *buf, size_t len)
 {
         struct net_device *dev = queue->dev;
         unsigned long index;
         cpumask_var_t mask;
         int err;
 
         if (!capable(CAP_NET_ADMIN))
                 return -EPERM;
 
         if (!alloc_cpumask_var(&mask, GFP_KERNEL))
                 return -ENOMEM;
 
         index = get_netdev_queue_index(queue);
 
         err = bitmap_parse(buf, len, cpumask_bits(mask), nr_cpumask_bits);
         if (err) {
                 free_cpumask_var(mask);
                 return err;
         }
 
         err = netif_set_xps_queue(dev, mask, index);
 
         free_cpumask_var(mask);
 
         return err ? : len;
 }
 
 static struct netdev_queue_attribute xps_cpus_attribute =
     __ATTR(xps_cpus, S_IRUGO | S_IWUSR, show_xps_map, store_xps_map);
 #endif /* CONFIG_XPS */
 
 static struct attribute *netdev_queue_default_attrs[] = {
         &queue_trans_timeout.attr,
 #ifdef CONFIG_XPS
         &xps_cpus_attribute.attr,
         &queue_tx_maxrate.attr,
 #endif
         NULL
 };
 
 static void netdev_queue_release(struct kobject *kobj)
 {
         struct netdev_queue *queue = to_netdev_queue(kobj);
 
         memset(kobj, 0, sizeof(*kobj));
         dev_put(queue->dev);
 }
 
 static const void *netdev_queue_namespace(struct kobject *kobj)
 {
         struct netdev_queue *queue = to_netdev_queue(kobj);
         struct device *dev = &queue->dev->dev;
         const void *ns = NULL;
 
         if (dev->class && dev->class->ns_type)
                 ns = dev->class->namespace(dev);
 
         return ns;
 }
 
 static struct kobj_type netdev_queue_ktype = {
         .sysfs_ops = &netdev_queue_sysfs_ops,
         .release = netdev_queue_release,
         .default_attrs = netdev_queue_default_attrs,
         .namespace = netdev_queue_namespace,
 };
 
 static int netdev_queue_add_kobject(struct net_device *dev, int index)
 {
         struct netdev_queue *queue = dev->_tx + index;
         struct kobject *kobj = &queue->kobj;
         int error = 0;
 
         kobj->kset = dev->queues_kset;
         error = kobject_init_and_add(kobj, &netdev_queue_ktype, NULL,
             "tx-%u", index);
         if (error)
                 goto exit;
 
 #ifdef CONFIG_BQL
         error = sysfs_create_group(kobj, &dql_group);
         if (error)
                 goto exit;
 #endif
 
         kobject_uevent(kobj, KOBJ_ADD);
         dev_hold(queue->dev);
 
         return 0;
 exit:
         kobject_put(kobj);
         return error;
 }
 #endif /* CONFIG_SYSFS */
 
 int
 netdev_queue_update_kobjects(struct net_device *dev, int old_num, int new_num)
 {
 #ifdef CONFIG_SYSFS
         int i;
         int error = 0;
 
         for (i = old_num; i < new_num; i++) {
                 error = netdev_queue_add_kobject(dev, i);
                 if (error) {
                         new_num = old_num;
                         break;
                 }
         }
 
         while (--i >= new_num) {
                 struct netdev_queue *queue = dev->_tx + i;
 
 #ifdef CONFIG_BQL
                 sysfs_remove_group(&queue->kobj, &dql_group);
 #endif
                 kobject_put(&queue->kobj);
         }
 
         return error;
 #else
         return 0;
 #endif /* CONFIG_SYSFS */
 }
 
 static int register_queue_kobjects(struct net_device *dev)
 {
         int error = 0, txq = 0, rxq = 0, real_rx = 0, real_tx = 0;
 
 #ifdef CONFIG_SYSFS
         dev->queues_kset = kset_create_and_add("queues",
             NULL, &dev->dev.kobj);
         if (!dev->queues_kset)
                 return -ENOMEM;
         real_rx = dev->real_num_rx_queues;
 #endif
         real_tx = dev->real_num_tx_queues;
 
         error = net_rx_queue_update_kobjects(dev, 0, real_rx);
         if (error)
                 goto error;
         rxq = real_rx;
 
         error = netdev_queue_update_kobjects(dev, 0, real_tx);
         if (error)
                 goto error;
         txq = real_tx;
 
         return 0;
 
 error:
         netdev_queue_update_kobjects(dev, txq, 0);
         net_rx_queue_update_kobjects(dev, rxq, 0);
         return error;
 }
 
 static void remove_queue_kobjects(struct net_device *dev)
 {
         int real_rx = 0, real_tx = 0;
 
 #ifdef CONFIG_SYSFS
         real_rx = dev->real_num_rx_queues;
 #endif
         real_tx = dev->real_num_tx_queues;
 
         net_rx_queue_update_kobjects(dev, real_rx, 0);
         netdev_queue_update_kobjects(dev, real_tx, 0);
 #ifdef CONFIG_SYSFS
         kset_unregister(dev->queues_kset);
 #endif
 }
 
 static bool net_current_may_mount(void)
 {
         struct net *net = current->nsproxy->net_ns;
 
         return ns_capable(net->user_ns, CAP_SYS_ADMIN);
 }
 
 static void *net_grab_current_ns(void)
 {
         struct net *ns = current->nsproxy->net_ns;
 #ifdef CONFIG_NET_NS
         if (ns)
                 atomic_inc(&ns->passive);
 #endif
         return ns;
 }
 
 static const void *net_initial_ns(void)
 {
         return &init_net;
 }
 
 static const void *net_netlink_ns(struct sock *sk)
 {
         return sock_net(sk);
 }
 
 struct kobj_ns_type_operations net_ns_type_operations = {
         .type = KOBJ_NS_TYPE_NET,
         .current_may_mount = net_current_may_mount,
         .grab_current_ns = net_grab_current_ns,
         .netlink_ns = net_netlink_ns,
         .initial_ns = net_initial_ns,
         .drop_ns = net_drop_ns,
 };
 EXPORT_SYMBOL_GPL(net_ns_type_operations);
 
 static int netdev_uevent(struct device *d, struct kobj_uevent_env *env)
 {
         struct net_device *dev = to_net_dev(d);
         int retval;
 
         /* pass interface to uevent. */
         retval = add_uevent_var(env, "INTERFACE=%s", dev->name);
         if (retval)
                 goto exit;
 
         /* pass ifindex to uevent.
          * ifindex is useful as it won't change (interface name may change)
          * and is what RtNetlink uses natively. */
         retval = add_uevent_var(env, "IFINDEX=%d", dev->ifindex);
 
 exit:
         return retval;
 }
 
 /*
  *      netdev_release -- destroy and free a dead device.
  *      Called when last reference to device kobject is gone.
  */
 static void netdev_release(struct device *d)
 {
         struct net_device *dev = to_net_dev(d);
 
         BUG_ON(dev->reg_state != NETREG_RELEASED);
 
         kfree(dev->ifalias);
         netdev_freemem(dev);
 }
 
 static const void *net_namespace(struct device *d)
 {
         struct net_device *dev;
         dev = container_of(d, struct net_device, dev);
         return dev_net(dev);
 }
 
 static struct class net_class = {
         .name = "net",
         .dev_release = netdev_release,
         .dev_groups = net_class_groups,
         .dev_uevent = netdev_uevent,
         .ns_type = &net_ns_type_operations,
         .namespace = net_namespace,
 };
 
 #ifdef CONFIG_OF_NET
 static int of_dev_node_match(struct device *dev, const void *data)
 {
         int ret = 0;
 
         if (dev->parent)
                 ret = dev->parent->of_node == data;
 
         return ret == 0 ? dev->of_node == data : ret;
 }
 
 struct net_device *of_find_net_device_by_node(struct device_node *np)
 {
         struct device *dev;
 
         dev = class_find_device(&net_class, NULL, np, of_dev_node_match);
         if (!dev)
                 return NULL;
 
         return to_net_dev(dev);
 }
 EXPORT_SYMBOL(of_find_net_device_by_node);
 #endif
 
 /* Delete sysfs entries but hold kobject reference until after all
  * netdev references are gone.
  */
 void netdev_unregister_kobject(struct net_device *ndev)
 {
         struct device *dev = &(ndev->dev);
 
         kobject_get(&dev->kobj);
 
         remove_queue_kobjects(ndev);
 
         pm_runtime_set_memalloc_noio(dev, false);
 
         device_del(dev);
 }
 
 /* Create sysfs entries for network device. */
 int netdev_register_kobject(struct net_device *ndev)
 {
         struct device *dev = &(ndev->dev);
         const struct attribute_group **groups = ndev->sysfs_groups;
         int error = 0;
 
         device_initialize(dev);
         dev->class = &net_class;
         dev->platform_data = ndev;
         dev->groups = groups;
 
         dev_set_name(dev, "%s", ndev->name);
 
 #ifdef CONFIG_SYSFS
         /* Allow for a device specific group */
         if (*groups)
                 groups++;
 
         *groups++ = &netstat_group;
 
 #if IS_ENABLED(CONFIG_WIRELESS_EXT) || IS_ENABLED(CONFIG_CFG80211)
         if (ndev->ieee80211_ptr)
                 *groups++ = &wireless_group;
 #if IS_ENABLED(CONFIG_WIRELESS_EXT)
         else if (ndev->wireless_handlers)
                 *groups++ = &wireless_group;
 #endif
 #endif
 #endif /* CONFIG_SYSFS */
 
         error = device_add(dev);
         if (error)
                 return error;
 
         error = register_queue_kobjects(ndev);
         if (error) {
                 device_del(dev);
                 return error;
         }
 
         pm_runtime_set_memalloc_noio(dev, true);
 
         return error;
 }
 
 int netdev_class_create_file_ns(struct class_attribute *class_attr,
                                 const void *ns)
 {
         return class_create_file_ns(&net_class, class_attr, ns);
 }
 EXPORT_SYMBOL(netdev_class_create_file_ns);
 
 void netdev_class_remove_file_ns(struct class_attribute *class_attr,
                                  const void *ns)
 {
         class_remove_file_ns(&net_class, class_attr, ns);
 }
 EXPORT_SYMBOL(netdev_class_remove_file_ns);
 
 int __init netdev_kobject_init(void)
 {
         kobj_ns_type_register(&net_ns_type_operations);
         return class_register(&net_class);
 }
 
```

```

/*
 * Linux/include/linux/netdev_features.h
 *
 * Network device features.
 *
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version
 * 2 of the License, or (at your option) any later version.
 */
#ifndef _LINUX_NETDEV_FEATURES_H
#define _LINUX_NETDEV_FEATURES_H

#include <linux/types.h>

typedef u64 netdev_features_t;

enum {
        NETIF_F_SG_BIT,                 /* Scatter/gather IO. */
        NETIF_F_IP_CSUM_BIT,            /* Can checksum TCP/UDP over IPv4. */
        __UNUSED_NETIF_F_1,
        NETIF_F_HW_CSUM_BIT,            /* Can checksum all the packets. */
        NETIF_F_IPV6_CSUM_BIT,          /* Can checksum TCP/UDP over IPV6 */
        NETIF_F_HIGHDMA_BIT,            /* Can DMA to high memory. */
        NETIF_F_FRAGLIST_BIT,           /* Scatter/gather IO. */
        NETIF_F_HW_VLAN_CTAG_TX_BIT,    /* Transmit VLAN CTAG HW acceleration */
        NETIF_F_HW_VLAN_CTAG_RX_BIT,    /* Receive VLAN CTAG HW acceleration */
        NETIF_F_HW_VLAN_CTAG_FILTER_BIT,/* Receive filtering on VLAN CTAGs */
        NETIF_F_VLAN_CHALLENGED_BIT,    /* Device cannot handle VLAN packets */
        NETIF_F_GSO_BIT,                /* Enable software GSO. */
        NETIF_F_LLTX_BIT,               /* LockLess TX - deprecated. Please */
                                        /* do not use LLTX in new drivers */
        NETIF_F_NETNS_LOCAL_BIT,        /* Does not change network namespaces */
        NETIF_F_GRO_BIT,                /* Generic receive offload */
        NETIF_F_LRO_BIT,                /* large receive offload */

        /**/NETIF_F_GSO_SHIFT,          /* keep the order of SKB_GSO_* bits */
        NETIF_F_TSO_BIT                 /* ... TCPv4 segmentation */
                = NETIF_F_GSO_SHIFT,
        NETIF_F_UFO_BIT,                /* ... UDPv4 fragmentation */
        NETIF_F_GSO_ROBUST_BIT,         /* ... ->SKB_GSO_DODGY */
        NETIF_F_TSO_ECN_BIT,            /* ... TCP ECN support */
        NETIF_F_TSO6_BIT,               /* ... TCPv6 segmentation */
        NETIF_F_FSO_BIT,                /* ... FCoE segmentation */
        NETIF_F_GSO_GRE_BIT,            /* ... GRE with TSO */
        NETIF_F_GSO_GRE_CSUM_BIT,       /* ... GRE with csum with TSO */
        NETIF_F_GSO_IPIP_BIT,           /* ... IPIP tunnel with TSO */
        NETIF_F_GSO_SIT_BIT,            /* ... SIT tunnel with TSO */
        NETIF_F_GSO_UDP_TUNNEL_BIT,     /* ... UDP TUNNEL with TSO */
        NETIF_F_GSO_UDP_TUNNEL_CSUM_BIT,/* ... UDP TUNNEL with TSO & CSUM */
        NETIF_F_GSO_TUNNEL_REMCSUM_BIT, /* ... TUNNEL with TSO & REMCSUM */
        /**/NETIF_F_GSO_LAST =          /* last bit, see GSO_MASK */
                NETIF_F_GSO_TUNNEL_REMCSUM_BIT,

        NETIF_F_FCOE_CRC_BIT,           /* FCoE CRC32 */
        NETIF_F_SCTP_CSUM_BIT,          /* SCTP checksum offload */
        NETIF_F_FCOE_MTU_BIT,           /* Supports max FCoE MTU, 2158 bytes*/
        NETIF_F_NTUPLE_BIT,             /* N-tuple filters supported */
        NETIF_F_RXHASH_BIT,             /* Receive hashing offload */
        NETIF_F_RXCSUM_BIT,             /* Receive checksumming offload */
        NETIF_F_NOCACHE_COPY_BIT,       /* Use no-cache copyfromuser */
        NETIF_F_LOOPBACK_BIT,           /* Enable loopback */
        NETIF_F_RXFCS_BIT,              /* Append FCS to skb pkt data */
        NETIF_F_RXALL_BIT,              /* Receive errored frames too */
        NETIF_F_HW_VLAN_STAG_TX_BIT,    /* Transmit VLAN STAG HW acceleration */
        NETIF_F_HW_VLAN_STAG_RX_BIT,    /* Receive VLAN STAG HW acceleration */
        NETIF_F_HW_VLAN_STAG_FILTER_BIT,/* Receive filtering on VLAN STAGs */
        NETIF_F_HW_L2FW_DOFFLOAD_BIT,   /* Allow L2 Forwarding in Hardware */
        NETIF_F_BUSY_POLL_BIT,          /* Busy poll */
        NETIF_F_HW_SWITCH_OFFLOAD_BIT,  /* HW switch offload */

        /*
         * Add your fresh new feature above and remember to update
         * netdev_features_strings[] in net/core/ethtool.c and maybe
         * some feature mask #defines below. Please also describe it
         * in Documentation/networking/netdev-features.txt.
         */

        /**/NETDEV_FEATURE_COUNT
};

/* copy'n'paste compression ;) */
#define __NETIF_F_BIT(bit)      ((netdev_features_t)1 << (bit))
#define __NETIF_F(name)         __NETIF_F_BIT(NETIF_F_##name##_BIT)

#define NETIF_F_FCOE_CRC        __NETIF_F(FCOE_CRC)
#define NETIF_F_FCOE_MTU        __NETIF_F(FCOE_MTU)
#define NETIF_F_FRAGLIST        __NETIF_F(FRAGLIST)
#define NETIF_F_FSO             __NETIF_F(FSO)
#define NETIF_F_GRO             __NETIF_F(GRO)
#define NETIF_F_GSO             __NETIF_F(GSO)
#define NETIF_F_GSO_ROBUST      __NETIF_F(GSO_ROBUST)
#define NETIF_F_HIGHDMA         __NETIF_F(HIGHDMA)
#define NETIF_F_HW_CSUM         __NETIF_F(HW_CSUM)
#define NETIF_F_HW_VLAN_CTAG_FILTER __NETIF_F(HW_VLAN_CTAG_FILTER)
#define NETIF_F_HW_VLAN_CTAG_RX __NETIF_F(HW_VLAN_CTAG_RX)
#define NETIF_F_HW_VLAN_CTAG_TX __NETIF_F(HW_VLAN_CTAG_TX)
#define NETIF_F_IP_CSUM         __NETIF_F(IP_CSUM)
#define NETIF_F_IPV6_CSUM       __NETIF_F(IPV6_CSUM)
#define NETIF_F_LLTX            __NETIF_F(LLTX)
#define NETIF_F_LOOPBACK        __NETIF_F(LOOPBACK)
#define NETIF_F_LRO             __NETIF_F(LRO)
#define NETIF_F_NETNS_LOCAL     __NETIF_F(NETNS_LOCAL)
#define NETIF_F_NOCACHE_COPY    __NETIF_F(NOCACHE_COPY)
#define NETIF_F_NTUPLE          __NETIF_F(NTUPLE)
#define NETIF_F_RXCSUM          __NETIF_F(RXCSUM)
#define NETIF_F_RXHASH          __NETIF_F(RXHASH)
#define NETIF_F_SCTP_CSUM       __NETIF_F(SCTP_CSUM)
#define NETIF_F_SG              __NETIF_F(SG)
#define NETIF_F_TSO6            __NETIF_F(TSO6)
#define NETIF_F_TSO_ECN         __NETIF_F(TSO_ECN)
#define NETIF_F_TSO             __NETIF_F(TSO)
#define NETIF_F_UFO             __NETIF_F(UFO)
#define NETIF_F_VLAN_CHALLENGED __NETIF_F(VLAN_CHALLENGED)
#define NETIF_F_RXFCS           __NETIF_F(RXFCS)
#define NETIF_F_RXALL           __NETIF_F(RXALL)
#define NETIF_F_GSO_GRE         __NETIF_F(GSO_GRE)
#define NETIF_F_GSO_GRE_CSUM    __NETIF_F(GSO_GRE_CSUM)
#define NETIF_F_GSO_IPIP        __NETIF_F(GSO_IPIP)
#define NETIF_F_GSO_SIT         __NETIF_F(GSO_SIT)
#define NETIF_F_GSO_UDP_TUNNEL  __NETIF_F(GSO_UDP_TUNNEL)
#define NETIF_F_GSO_UDP_TUNNEL_CSUM __NETIF_F(GSO_UDP_TUNNEL_CSUM)
#define NETIF_F_GSO_TUNNEL_REMCSUM __NETIF_F(GSO_TUNNEL_REMCSUM)
#define NETIF_F_HW_VLAN_STAG_FILTER __NETIF_F(HW_VLAN_STAG_FILTER)
#define NETIF_F_HW_VLAN_STAG_RX __NETIF_F(HW_VLAN_STAG_RX)
#define NETIF_F_HW_VLAN_STAG_TX __NETIF_F(HW_VLAN_STAG_TX)
#define NETIF_F_HW_L2FW_DOFFLOAD        __NETIF_F(HW_L2FW_DOFFLOAD)
#define NETIF_F_BUSY_POLL       __NETIF_F(BUSY_POLL)
#define NETIF_F_HW_SWITCH_OFFLOAD       __NETIF_F(HW_SWITCH_OFFLOAD)

/* Features valid for ethtool to change */
/* = all defined minus driver/device-class-related */
#define NETIF_F_NEVER_CHANGE    (NETIF_F_VLAN_CHALLENGED | \
                                 NETIF_F_LLTX | NETIF_F_NETNS_LOCAL)

/* remember that ((t)1 << t_BITS) is undefined in C99 */
#define NETIF_F_ETHTOOL_BITS    ((__NETIF_F_BIT(NETDEV_FEATURE_COUNT - 1) | \
                (__NETIF_F_BIT(NETDEV_FEATURE_COUNT - 1) - 1)) & \
                ~NETIF_F_NEVER_CHANGE)

/* Segmentation offload feature mask */
#define NETIF_F_GSO_MASK        (__NETIF_F_BIT(NETIF_F_GSO_LAST + 1) - \
                __NETIF_F_BIT(NETIF_F_GSO_SHIFT))

/* List of features with software fallbacks. */
#define NETIF_F_GSO_SOFTWARE    (NETIF_F_TSO | NETIF_F_TSO_ECN | \
                                 NETIF_F_TSO6 | NETIF_F_UFO)

#define NETIF_F_GEN_CSUM        NETIF_F_HW_CSUM
#define NETIF_F_V4_CSUM         (NETIF_F_GEN_CSUM | NETIF_F_IP_CSUM)
#define NETIF_F_V6_CSUM         (NETIF_F_GEN_CSUM | NETIF_F_IPV6_CSUM)
#define NETIF_F_ALL_CSUM        (NETIF_F_V4_CSUM | NETIF_F_V6_CSUM)

#define NETIF_F_ALL_TSO         (NETIF_F_TSO | NETIF_F_TSO6 | NETIF_F_TSO_ECN)

#define NETIF_F_ALL_FCOE        (NETIF_F_FCOE_CRC | NETIF_F_FCOE_MTU | \
                                 NETIF_F_FSO)

/*
 * If one device supports one of these features, then enable them
 * for all in netdev_increment_features.
 */
#define NETIF_F_ONE_FOR_ALL     (NETIF_F_GSO_SOFTWARE | NETIF_F_GSO_ROBUST | \
                                 NETIF_F_SG | NETIF_F_HIGHDMA |         \
                                 NETIF_F_FRAGLIST | NETIF_F_VLAN_CHALLENGED | \
                                 NETIF_F_HW_SWITCH_OFFLOAD)

/*
 * If one device doesn't support one of these features, then disable it
 * for all in netdev_increment_features.
 */
#define NETIF_F_ALL_FOR_ALL     (NETIF_F_NOCACHE_COPY | NETIF_F_FSO)

/* changeable features with no special hardware requirements */
#define NETIF_F_SOFT_FEATURES   (NETIF_F_GSO | NETIF_F_GRO)

#define NETIF_F_VLAN_FEATURES   (NETIF_F_HW_VLAN_CTAG_FILTER | \
                                 NETIF_F_HW_VLAN_CTAG_RX | \
                                 NETIF_F_HW_VLAN_CTAG_TX | \
                                 NETIF_F_HW_VLAN_STAG_FILTER | \
                                 NETIF_F_HW_VLAN_STAG_RX | \
                                 NETIF_F_HW_VLAN_STAG_TX)

#define NETIF_F_GSO_ENCAP_ALL   (NETIF_F_GSO_GRE |                      \
                                 NETIF_F_GSO_GRE_CSUM |                 \
                                 NETIF_F_GSO_IPIP |                     \
                                 NETIF_F_GSO_SIT |                      \
                                 NETIF_F_GSO_UDP_TUNNEL |               \
                                 NETIF_F_GSO_UDP_TUNNEL_CSUM)

#endif  /* _LINUX_NETDEV_FEATURES_H */

```






```
/*
 *              Linux/include/linux/netdevice.h
 *
 * INET         An implementation of the TCP/IP protocol suite for the LINUX
 *              operating system.  INET is implemented using the  BSD Socket
 *              interface as the means of communication with the user level.
 *
 *              Definitions for the Interfaces handler.
 *
 * Version:     @(#)dev.h       1.0.10  08/12/93
 *
 * Authors:     Ross Biro
 *              Fred N. van Kempen, <waltje@uWalt.NL.Mugnet.ORG>
 *              Corey Minyard <wf-rch!minyard@relay.EU.net>
 *              Donald J. Becker, <becker@cesdis.gsfc.nasa.gov>
 *              Alan Cox, <alan@lxorguk.ukuu.org.uk>
 *              Bjorn Ekwall. <bj0rn@blox.se>
 *              Pekka Riikonen <priikone@poseidon.pspt.fi>
 *
 *              This program is free software; you can redistribute it and/or
 *              modify it under the terms of the GNU General Public License
 *              as published by the Free Software Foundation; either version
 *              2 of the License, or (at your option) any later version.
 *
 *              Moved to /usr/include/linux for NET3
 *
 */
#ifndef _LINUX_NETDEVICE_H
#define _LINUX_NETDEVICE_H

#include <linux/timer.h>
#include <linux/bug.h>
#include <linux/delay.h>
#include <linux/atomic.h>
#include <linux/prefetch.h>
#include <asm/cache.h>
#include <asm/byteorder.h>

#include <linux/percpu.h>
#include <linux/rculist.h>
#include <linux/dmaengine.h>
#include <linux/workqueue.h>
#include <linux/dynamic_queue_limits.h>

#include <linux/ethtool.h>
#include <net/net_namespace.h>
#include <net/dsa.h>
#ifdef CONFIG_DCB
#include <net/dcbnl.h>
#endif
#include <net/netprio_cgroup.h>

#include <linux/netdev_features.h>
#include <linux/neighbour.h>
#include <uapi/linux/netdevice.h>
#include <uapi/linux/if_bonding.h>

struct netpoll_info;
struct device;
struct phy_device;
/* 802.11 specific */
struct wireless_dev;
/* 802.15.4 specific */
struct wpan_dev;
struct mpls_dev;

void netdev_set_default_ethtool_ops(struct net_device *dev,
                                    const struct ethtool_ops *ops);

/* Backlog congestion levels */
#define NET_RX_SUCCESS          0       /* keep 'em coming, baby */
#define NET_RX_DROP             1       /* packet dropped */

/*
 * Transmit return codes: transmit return codes originate from three different
 * namespaces:
 *
 * - qdisc return codes
 * - driver transmit return codes
 * - errno values
 *
 * Drivers are allowed to return any one of those in their hard_start_xmit()
 * function. Real network devices commonly used with qdiscs should only return
 * the driver transmit return codes though - when qdiscs are used, the actual
 * transmission happens asynchronously, so the value is not propagated to
 * higher layers. Virtual network devices transmit synchronously, in this case
 * the driver transmit return codes are consumed by dev_queue_xmit(), all
 * others are propagated to higher layers.
 */

/* qdisc ->enqueue() return codes. */
#define NET_XMIT_SUCCESS        0x00
#define NET_XMIT_DROP           0x01    /* skb dropped                  */
#define NET_XMIT_CN             0x02    /* congestion notification      */
#define NET_XMIT_POLICED        0x03    /* skb is shot by police        */
#define NET_XMIT_MASK           0x0f    /* qdisc flags in net/sch_generic.h */

/* NET_XMIT_CN is special. It does not guarantee that this packet is lost. It
 * indicates that the device will soon be dropping packets, or already drops
 * some packets of the same priority; prompting us to send less aggressively. */
#define net_xmit_eval(e)        ((e) == NET_XMIT_CN ? 0 : (e))
#define net_xmit_errno(e)       ((e) != NET_XMIT_CN ? -ENOBUFS : 0)

/* Driver transmit return codes */
#define NETDEV_TX_MASK          0xf0

enum netdev_tx {
        __NETDEV_TX_MIN  = INT_MIN,     /* make sure enum is signed */
        NETDEV_TX_OK     = 0x00,        /* driver took care of packet */
        NETDEV_TX_BUSY   = 0x10,        /* driver tx path was busy*/
        NETDEV_TX_LOCKED = 0x20,        /* driver tx lock was already taken */
};
typedef enum netdev_tx netdev_tx_t;

/*
 * Current order: NETDEV_TX_MASK > NET_XMIT_MASK >= 0 is significant;
 * hard_start_xmit() return < NET_XMIT_MASK means skb was consumed.
 */
static inline bool dev_xmit_complete(int rc)
{
        /*
         * Positive cases with an skb consumed by a driver:
         * - successful transmission (rc == NETDEV_TX_OK)
         * - error while transmitting (rc < 0)
         * - error while queueing to a different device (rc & NET_XMIT_MASK)
         */
        if (likely(rc < NET_XMIT_MASK))
                return true;

        return false;
}

/*
 *      Compute the worst case header length according to the protocols
 *      used.
 */

#if defined(CONFIG_WLAN) || IS_ENABLED(CONFIG_AX25)
# if defined(CONFIG_MAC80211_MESH)
#  define LL_MAX_HEADER 128
# else
#  define LL_MAX_HEADER 96
# endif
#else
# define LL_MAX_HEADER 32
#endif

#if !IS_ENABLED(CONFIG_NET_IPIP) && !IS_ENABLED(CONFIG_NET_IPGRE) && \
    !IS_ENABLED(CONFIG_IPV6_SIT) && !IS_ENABLED(CONFIG_IPV6_TUNNEL)
#define MAX_HEADER LL_MAX_HEADER
#else
#define MAX_HEADER (LL_MAX_HEADER + 48)
#endif

/*
 *      Old network device statistics. Fields are native words
 *      (unsigned long) so they can be read and written atomically.
 */

struct net_device_stats {
        unsigned long   rx_packets;
        unsigned long   tx_packets;
        unsigned long   rx_bytes;
        unsigned long   tx_bytes;
        unsigned long   rx_errors;
        unsigned long   tx_errors;
        unsigned long   rx_dropped;
        unsigned long   tx_dropped;
        unsigned long   multicast;
        unsigned long   collisions;
        unsigned long   rx_length_errors;
        unsigned long   rx_over_errors;
        unsigned long   rx_crc_errors;
        unsigned long   rx_frame_errors;
        unsigned long   rx_fifo_errors;
        unsigned long   rx_missed_errors;
        unsigned long   tx_aborted_errors;
        unsigned long   tx_carrier_errors;
        unsigned long   tx_fifo_errors;
        unsigned long   tx_heartbeat_errors;
        unsigned long   tx_window_errors;
        unsigned long   rx_compressed;
        unsigned long   tx_compressed;
};


#include <linux/cache.h>
#include <linux/skbuff.h>

#ifdef CONFIG_RPS
#include <linux/static_key.h>
extern struct static_key rps_needed;
#endif

struct neighbour;
struct neigh_parms;
struct sk_buff;

struct netdev_hw_addr {
        struct list_head        list;
        unsigned char           addr[MAX_ADDR_LEN];
        unsigned char           type;
#define NETDEV_HW_ADDR_T_LAN            1
#define NETDEV_HW_ADDR_T_SAN            2
#define NETDEV_HW_ADDR_T_SLAVE          3
#define NETDEV_HW_ADDR_T_UNICAST        4
#define NETDEV_HW_ADDR_T_MULTICAST      5
        bool                    global_use;
        int                     sync_cnt;
        int                     refcount;
        int                     synced;
        struct rcu_head         rcu_head;
};

struct netdev_hw_addr_list {
        struct list_head        list;
        int                     count;
};

#define netdev_hw_addr_list_count(l) ((l)->count)
#define netdev_hw_addr_list_empty(l) (netdev_hw_addr_list_count(l) == 0)
#define netdev_hw_addr_list_for_each(ha, l) \
        list_for_each_entry(ha, &(l)->list, list)

#define netdev_uc_count(dev) netdev_hw_addr_list_count(&(dev)->uc)
#define netdev_uc_empty(dev) netdev_hw_addr_list_empty(&(dev)->uc)
#define netdev_for_each_uc_addr(ha, dev) \
        netdev_hw_addr_list_for_each(ha, &(dev)->uc)

#define netdev_mc_count(dev) netdev_hw_addr_list_count(&(dev)->mc)
#define netdev_mc_empty(dev) netdev_hw_addr_list_empty(&(dev)->mc)
#define netdev_for_each_mc_addr(ha, dev) \
        netdev_hw_addr_list_for_each(ha, &(dev)->mc)

struct hh_cache {
        u16             hh_len;
        u16             __pad;
        seqlock_t       hh_lock;

        /* cached hardware header; allow for machine alignment needs.        */
#define HH_DATA_MOD     16
#define HH_DATA_OFF(__len) \
        (HH_DATA_MOD - (((__len - 1) & (HH_DATA_MOD - 1)) + 1))
#define HH_DATA_ALIGN(__len) \
        (((__len)+(HH_DATA_MOD-1))&~(HH_DATA_MOD - 1))
        unsigned long   hh_data[HH_DATA_ALIGN(LL_MAX_HEADER) / sizeof(long)];
};

/* Reserve HH_DATA_MOD byte aligned hard_header_len, but at least that much.
 * Alternative is:
 *   dev->hard_header_len ? (dev->hard_header_len +
 *                           (HH_DATA_MOD - 1)) & ~(HH_DATA_MOD - 1) : 0
 *
 * We could use other alignment values, but we must maintain the
 * relationship HH alignment <= LL alignment.
 */
#define LL_RESERVED_SPACE(dev) \
        ((((dev)->hard_header_len+(dev)->needed_headroom)&~(HH_DATA_MOD - 1)) + HH_DATA_MOD)
#define LL_RESERVED_SPACE_EXTRA(dev,extra) \
        ((((dev)->hard_header_len+(dev)->needed_headroom+(extra))&~(HH_DATA_MOD - 1)) + HH_DATA_MOD)

struct header_ops {
        int     (*create) (struct sk_buff *skb, struct net_device *dev,
                           unsigned short type, const void *daddr,
                           const void *saddr, unsigned int len);
        int     (*parse)(const struct sk_buff *skb, unsigned char *haddr);
        int     (*cache)(const struct neighbour *neigh, struct hh_cache *hh, __be16 type);
        void    (*cache_update)(struct hh_cache *hh,
                                const struct net_device *dev,
                                const unsigned char *haddr);
};

/* These flag bits are private to the generic network queueing
 * layer, they may not be explicitly referenced by any other
 * code.
 */

enum netdev_state_t {
        __LINK_STATE_START,
        __LINK_STATE_PRESENT,
        __LINK_STATE_NOCARRIER,
        __LINK_STATE_LINKWATCH_PENDING,
        __LINK_STATE_DORMANT,
};


/*
 * This structure holds at boot time configured netdevice settings. They
 * are then used in the device probing.
 */
struct netdev_boot_setup {
        char name[IFNAMSIZ];
        struct ifmap map;
};
#define NETDEV_BOOT_SETUP_MAX 8

int __init netdev_boot_setup(char *str);

/*
 * Structure for NAPI scheduling similar to tasklet but with weighting
 */
struct napi_struct {
        /* The poll_list must only be managed by the entity which
         * changes the state of the NAPI_STATE_SCHED bit.  This means
         * whoever atomically sets that bit can add this napi_struct
         * to the per-cpu poll_list, and whoever clears that bit
         * can remove from the list right before clearing the bit.
         */
        struct list_head        poll_list;

        unsigned long           state;
        int                     weight;
        unsigned int            gro_count;
        int                     (*poll)(struct napi_struct *, int);
#ifdef CONFIG_NETPOLL
        spinlock_t              poll_lock;
        int                     poll_owner;
#endif
        struct net_device       *dev;
        struct sk_buff          *gro_list;
        struct sk_buff          *skb;
        struct hrtimer          timer;
        struct list_head        dev_list;
        struct hlist_node       napi_hash_node;
        unsigned int            napi_id;
};

enum {
        NAPI_STATE_SCHED,       /* Poll is scheduled */
        NAPI_STATE_DISABLE,     /* Disable pending */
        NAPI_STATE_NPSVC,       /* Netpoll - don't dequeue from poll_list */
        NAPI_STATE_HASHED,      /* In NAPI hash */
};

enum gro_result {
        GRO_MERGED,
        GRO_MERGED_FREE,
        GRO_HELD,
        GRO_NORMAL,
        GRO_DROP,
};
typedef enum gro_result gro_result_t;

/*
 * enum rx_handler_result - Possible return values for rx_handlers.
 * @RX_HANDLER_CONSUMED: skb was consumed by rx_handler, do not process it
 * further.
 * @RX_HANDLER_ANOTHER: Do another round in receive path. This is indicated in
 * case skb->dev was changed by rx_handler.
 * @RX_HANDLER_EXACT: Force exact delivery, no wildcard.
 * @RX_HANDLER_PASS: Do nothing, passe the skb as if no rx_handler was called.
 *
 * rx_handlers are functions called from inside __netif_receive_skb(), to do
 * special processing of the skb, prior to delivery to protocol handlers.
 *
 * Currently, a net_device can only have a single rx_handler registered. Trying
 * to register a second rx_handler will return -EBUSY.
 *
 * To register a rx_handler on a net_device, use netdev_rx_handler_register().
 * To unregister a rx_handler on a net_device, use
 * netdev_rx_handler_unregister().
 *
 * Upon return, rx_handler is expected to tell __netif_receive_skb() what to
 * do with the skb.
 *
 * If the rx_handler consumed to skb in some way, it should return
 * RX_HANDLER_CONSUMED. This is appropriate when the rx_handler arranged for
 * the skb to be delivered in some other ways.
 *
 * If the rx_handler changed skb->dev, to divert the skb to another
 * net_device, it should return RX_HANDLER_ANOTHER. The rx_handler for the
 * new device will be called if it exists.
 *
 * If the rx_handler consider the skb should be ignored, it should return
 * RX_HANDLER_EXACT. The skb will only be delivered to protocol handlers that
 * are registered on exact device (ptype->dev == skb->dev).
 *
 * If the rx_handler didn't changed skb->dev, but want the skb to be normally
 * delivered, it should return RX_HANDLER_PASS.
 *
 * A device without a registered rx_handler will behave as if rx_handler
 * returned RX_HANDLER_PASS.
 */

enum rx_handler_result {
        RX_HANDLER_CONSUMED,
        RX_HANDLER_ANOTHER,
        RX_HANDLER_EXACT,
        RX_HANDLER_PASS,
};
typedef enum rx_handler_result rx_handler_result_t;
typedef rx_handler_result_t rx_handler_func_t(struct sk_buff **pskb);

void __napi_schedule(struct napi_struct *n);
void __napi_schedule_irqoff(struct napi_struct *n);

static inline bool napi_disable_pending(struct napi_struct *n)
{
        return test_bit(NAPI_STATE_DISABLE, &n->state);
}

/**
 *      napi_schedule_prep - check if napi can be scheduled
 *      @n: napi context
 *
 * Test if NAPI routine is already running, and if not mark
 * it as running.  This is used as a condition variable
 * insure only one NAPI poll instance runs.  We also make
 * sure there is no pending NAPI disable.
 */
static inline bool napi_schedule_prep(struct napi_struct *n)
{
        return !napi_disable_pending(n) &&
                !test_and_set_bit(NAPI_STATE_SCHED, &n->state);
}

/**
 *      napi_schedule - schedule NAPI poll
 *      @n: napi context
 *
 * Schedule NAPI poll routine to be called if it is not already
 * running.
 */
static inline void napi_schedule(struct napi_struct *n)
{
        if (napi_schedule_prep(n))
                __napi_schedule(n);
}

/**
 *      napi_schedule_irqoff - schedule NAPI poll
 *      @n: napi context
 *
 * Variant of napi_schedule(), assuming hard irqs are masked.
 */
static inline void napi_schedule_irqoff(struct napi_struct *n)
{
        if (napi_schedule_prep(n))
                __napi_schedule_irqoff(n);
}

/* Try to reschedule poll. Called by dev->poll() after napi_complete().  */
static inline bool napi_reschedule(struct napi_struct *napi)
{
        if (napi_schedule_prep(napi)) {
                __napi_schedule(napi);
                return true;
        }
        return false;
}

void __napi_complete(struct napi_struct *n);
void napi_complete_done(struct napi_struct *n, int work_done);
/**
 *      napi_complete - NAPI processing complete
 *      @n: napi context
 *
 * Mark NAPI processing as complete.
 * Consider using napi_complete_done() instead.
 */
static inline void napi_complete(struct napi_struct *n)
{
        return napi_complete_done(n, 0);
}

/**
 *      napi_by_id - lookup a NAPI by napi_id
 *      @napi_id: hashed napi_id
 *
 * lookup @napi_id in napi_hash table
 * must be called under rcu_read_lock()
 */
struct napi_struct *napi_by_id(unsigned int napi_id);

/**
 *      napi_hash_add - add a NAPI to global hashtable
 *      @napi: napi context
 *
 * generate a new napi_id and store a @napi under it in napi_hash
 */
void napi_hash_add(struct napi_struct *napi);

/**
 *      napi_hash_del - remove a NAPI from global table
 *      @napi: napi context
 *
 * Warning: caller must observe rcu grace period
 * before freeing memory containing @napi
 */
void napi_hash_del(struct napi_struct *napi);

/**
 *      napi_disable - prevent NAPI from scheduling
 *      @n: napi context
 *
 * Stop NAPI from being scheduled on this context.
 * Waits till any outstanding processing completes.
 */
void napi_disable(struct napi_struct *n);

/**
 *      napi_enable - enable NAPI scheduling
 *      @n: napi context
 *
 * Resume NAPI from being scheduled on this context.
 * Must be paired with napi_disable.
 */
static inline void napi_enable(struct napi_struct *n)
{
        BUG_ON(!test_bit(NAPI_STATE_SCHED, &n->state));
        smp_mb__before_atomic();
        clear_bit(NAPI_STATE_SCHED, &n->state);
}

#ifdef CONFIG_SMP
/**
 *      napi_synchronize - wait until NAPI is not running
 *      @n: napi context
 *
 * Wait until NAPI is done being scheduled on this context.
 * Waits till any outstanding processing completes but
 * does not disable future activations.
 */
static inline void napi_synchronize(const struct napi_struct *n)
{
        while (test_bit(NAPI_STATE_SCHED, &n->state))
                msleep(1);
}
#else
# define napi_synchronize(n)    barrier()
#endif

enum netdev_queue_state_t {
        __QUEUE_STATE_DRV_XOFF,
        __QUEUE_STATE_STACK_XOFF,
        __QUEUE_STATE_FROZEN,
};

#define QUEUE_STATE_DRV_XOFF    (1 << __QUEUE_STATE_DRV_XOFF)
#define QUEUE_STATE_STACK_XOFF  (1 << __QUEUE_STATE_STACK_XOFF)
#define QUEUE_STATE_FROZEN      (1 << __QUEUE_STATE_FROZEN)

#define QUEUE_STATE_ANY_XOFF    (QUEUE_STATE_DRV_XOFF | QUEUE_STATE_STACK_XOFF)
#define QUEUE_STATE_ANY_XOFF_OR_FROZEN (QUEUE_STATE_ANY_XOFF | \
                                        QUEUE_STATE_FROZEN)
#define QUEUE_STATE_DRV_XOFF_OR_FROZEN (QUEUE_STATE_DRV_XOFF | \
                                        QUEUE_STATE_FROZEN)

/*
 * __QUEUE_STATE_DRV_XOFF is used by drivers to stop the transmit queue.  The
 * netif_tx_* functions below are used to manipulate this flag.  The
 * __QUEUE_STATE_STACK_XOFF flag is used by the stack to stop the transmit
 * queue independently.  The netif_xmit_*stopped functions below are called
 * to check if the queue has been stopped by the driver or stack (either
 * of the XOFF bits are set in the state).  Drivers should not need to call
 * netif_xmit*stopped functions, they should only be using netif_tx_*.
 */

struct netdev_queue {
/*
 * read mostly part
 */
        struct net_device       *dev;
        struct Qdisc __rcu      *qdisc;
        struct Qdisc            *qdisc_sleeping;
#ifdef CONFIG_SYSFS
        struct kobject          kobj;
#endif
#if defined(CONFIG_XPS) && defined(CONFIG_NUMA)
        int                     numa_node;
#endif
/*
 * write mostly part
 */
        spinlock_t              _xmit_lock ____cacheline_aligned_in_smp;
        int                     xmit_lock_owner;
        /*
         * please use this field instead of dev->trans_start
         */
        unsigned long           trans_start;

        /*
         * Number of TX timeouts for this queue
         * (/sys/class/net/DEV/Q/trans_timeout)
         */
        unsigned long           trans_timeout;

        unsigned long           state;

#ifdef CONFIG_BQL
        struct dql              dql;
#endif
        unsigned long           tx_maxrate;
} ____cacheline_aligned_in_smp;

static inline int netdev_queue_numa_node_read(const struct netdev_queue *q)
{
#if defined(CONFIG_XPS) && defined(CONFIG_NUMA)
        return q->numa_node;
#else
        return NUMA_NO_NODE;
#endif
}

static inline void netdev_queue_numa_node_write(struct netdev_queue *q, int node)
{
#if defined(CONFIG_XPS) && defined(CONFIG_NUMA)
        q->numa_node = node;
#endif
}

#ifdef CONFIG_RPS
/*
 * This structure holds an RPS map which can be of variable length.  The
 * map is an array of CPUs.
 */
struct rps_map {
        unsigned int len;
        struct rcu_head rcu;
        u16 cpus[0];
};
#define RPS_MAP_SIZE(_num) (sizeof(struct rps_map) + ((_num) * sizeof(u16)))

/*
 * The rps_dev_flow structure contains the mapping of a flow to a CPU, the
 * tail pointer for that CPU's input queue at the time of last enqueue, and
 * a hardware filter index.
 */
struct rps_dev_flow {
        u16 cpu;
        u16 filter;
        unsigned int last_qtail;
};
#define RPS_NO_FILTER 0xffff

/*
 * The rps_dev_flow_table structure contains a table of flow mappings.
 */
struct rps_dev_flow_table {
        unsigned int mask;
        struct rcu_head rcu;
        struct rps_dev_flow flows[0];
};
#define RPS_DEV_FLOW_TABLE_SIZE(_num) (sizeof(struct rps_dev_flow_table) + \
    ((_num) * sizeof(struct rps_dev_flow)))

/*
 * The rps_sock_flow_table contains mappings of flows to the last CPU
 * on which they were processed by the application (set in recvmsg).
 * Each entry is a 32bit value. Upper part is the high order bits
 * of flow hash, lower part is cpu number.
 * rps_cpu_mask is used to partition the space, depending on number of
 * possible cpus : rps_cpu_mask = roundup_pow_of_two(nr_cpu_ids) - 1
 * For example, if 64 cpus are possible, rps_cpu_mask = 0x3f,
 * meaning we use 32-6=26 bits for the hash.
 */
struct rps_sock_flow_table {
        u32     mask;

        u32     ents[0] ____cacheline_aligned_in_smp;
};
#define RPS_SOCK_FLOW_TABLE_SIZE(_num) (offsetof(struct rps_sock_flow_table, ents[_num]))

#define RPS_NO_CPU 0xffff

extern u32 rps_cpu_mask;
extern struct rps_sock_flow_table __rcu *rps_sock_flow_table;

static inline void rps_record_sock_flow(struct rps_sock_flow_table *table,
                                        u32 hash)
{
        if (table && hash) {
                unsigned int index = hash & table->mask;
                u32 val = hash & ~rps_cpu_mask;

                /* We only give a hint, preemption can change cpu under us */
                val |= raw_smp_processor_id();

                if (table->ents[index] != val)
                        table->ents[index] = val;
        }
}

#ifdef CONFIG_RFS_ACCEL
bool rps_may_expire_flow(struct net_device *dev, u16 rxq_index, u32 flow_id,
                         u16 filter_id);
#endif
#endif /* CONFIG_RPS */

/* This structure contains an instance of an RX queue. */
struct netdev_rx_queue {
#ifdef CONFIG_RPS
        struct rps_map __rcu            *rps_map;
        struct rps_dev_flow_table __rcu *rps_flow_table;
#endif
        struct kobject                  kobj;
        struct net_device               *dev;
} ____cacheline_aligned_in_smp;

/*
 * RX queue sysfs structures and functions.
 */
struct rx_queue_attribute {
        struct attribute attr;
        ssize_t (*show)(struct netdev_rx_queue *queue,
            struct rx_queue_attribute *attr, char *buf);
        ssize_t (*store)(struct netdev_rx_queue *queue,
            struct rx_queue_attribute *attr, const char *buf, size_t len);
};

#ifdef CONFIG_XPS
/*
 * This structure holds an XPS map which can be of variable length.  The
 * map is an array of queues.
 */
struct xps_map {
        unsigned int len;
        unsigned int alloc_len;
        struct rcu_head rcu;
        u16 queues[0];
};
#define XPS_MAP_SIZE(_num) (sizeof(struct xps_map) + ((_num) * sizeof(u16)))
#define XPS_MIN_MAP_ALLOC ((L1_CACHE_BYTES - sizeof(struct xps_map))    \
    / sizeof(u16))

/*
 * This structure holds all XPS maps for device.  Maps are indexed by CPU.
 */
struct xps_dev_maps {
        struct rcu_head rcu;
        struct xps_map __rcu *cpu_map[0];
};
#define XPS_DEV_MAPS_SIZE (sizeof(struct xps_dev_maps) +                \
    (nr_cpu_ids * sizeof(struct xps_map *)))
#endif /* CONFIG_XPS */

#define TC_MAX_QUEUE    16
#define TC_BITMASK      15
/* HW offloaded queuing disciplines txq count and offset maps */
struct netdev_tc_txq {
        u16 count;
        u16 offset;
};

#if defined(CONFIG_FCOE) || defined(CONFIG_FCOE_MODULE)
/*
 * This structure is to hold information about the device
 * configured to run FCoE protocol stack.
 */
struct netdev_fcoe_hbainfo {
        char    manufacturer[64];
        char    serial_number[64];
        char    hardware_version[64];
        char    driver_version[64];
        char    optionrom_version[64];
        char    firmware_version[64];
        char    model[256];
        char    model_description[256];
};
#endif

#define MAX_PHYS_ITEM_ID_LEN 32

/* This structure holds a unique identifier to identify some
 * physical item (port for example) used by a netdevice.
 */
struct netdev_phys_item_id {
        unsigned char id[MAX_PHYS_ITEM_ID_LEN];
        unsigned char id_len;
};

typedef u16 (*select_queue_fallback_t)(struct net_device *dev,
                                       struct sk_buff *skb);

/*
 * This structure defines the management hooks for network devices.
 * The following hooks can be defined; unless noted otherwise, they are
 * optional and can be filled with a null pointer.
 *
 * int (*ndo_init)(struct net_device *dev);
 *     This function is called once when network device is registered.
 *     The network device can use this to any late stage initializaton
 *     or semantic validattion. It can fail with an error code which will
 *     be propogated back to register_netdev
 *
 * void (*ndo_uninit)(struct net_device *dev);
 *     This function is called when device is unregistered or when registration
 *     fails. It is not called if init fails.
 *
 * int (*ndo_open)(struct net_device *dev);
 *     This function is called when network device transistions to the up
 *     state.
 *
 * int (*ndo_stop)(struct net_device *dev);
 *     This function is called when network device transistions to the down
 *     state.
 *
 * netdev_tx_t (*ndo_start_xmit)(struct sk_buff *skb,
 *                               struct net_device *dev);
 *      Called when a packet needs to be transmitted.
 *      Returns NETDEV_TX_OK.  Can return NETDEV_TX_BUSY, but you should stop
 *      the queue before that can happen; it's for obsolete devices and weird
 *      corner cases, but the stack really does a non-trivial amount
 *      of useless work if you return NETDEV_TX_BUSY.
 *        (can also return NETDEV_TX_LOCKED iff NETIF_F_LLTX)
 *      Required can not be NULL.
 *
 * u16 (*ndo_select_queue)(struct net_device *dev, struct sk_buff *skb,
 *                         void *accel_priv, select_queue_fallback_t fallback);
 *      Called to decide which queue to when device supports multiple
 *      transmit queues.
 *
 * void (*ndo_change_rx_flags)(struct net_device *dev, int flags);
 *      This function is called to allow device receiver to make
 *      changes to configuration when multicast or promiscious is enabled.
 *
 * void (*ndo_set_rx_mode)(struct net_device *dev);
 *      This function is called device changes address list filtering.
 *      If driver handles unicast address filtering, it should set
 *      IFF_UNICAST_FLT to its priv_flags.
 *
 * int (*ndo_set_mac_address)(struct net_device *dev, void *addr);
 *      This function  is called when the Media Access Control address
 *      needs to be changed. If this interface is not defined, the
 *      mac address can not be changed.
 *
 * int (*ndo_validate_addr)(struct net_device *dev);
 *      Test if Media Access Control address is valid for the device.
 *
 * int (*ndo_do_ioctl)(struct net_device *dev, struct ifreq *ifr, int cmd);
 *      Called when a user request an ioctl which can't be handled by
 *      the generic interface code. If not defined ioctl's return
 *      not supported error code.
 *
 * int (*ndo_set_config)(struct net_device *dev, struct ifmap *map);
 *      Used to set network devices bus interface parameters. This interface
 *      is retained for legacy reason, new devices should use the bus
 *      interface (PCI) for low level management.
 *
 * int (*ndo_change_mtu)(struct net_device *dev, int new_mtu);
 *      Called when a user wants to change the Maximum Transfer Unit
 *      of a device. If not defined, any request to change MTU will
 *      will return an error.
 *
 * void (*ndo_tx_timeout)(struct net_device *dev);
 *      Callback uses when the transmitter has not made any progress
 *      for dev->watchdog ticks.
 *
 * struct rtnl_link_stats64* (*ndo_get_stats64)(struct net_device *dev,
 *                      struct rtnl_link_stats64 *storage);
 * struct net_device_stats* (*ndo_get_stats)(struct net_device *dev);
 *      Called when a user wants to get the network device usage
 *      statistics. Drivers must do one of the following:
 *      1. Define @ndo_get_stats64 to fill in a zero-initialised
 *         rtnl_link_stats64 structure passed by the caller.
 *      2. Define @ndo_get_stats to update a net_device_stats structure
 *         (which should normally be dev->stats) and return a pointer to
 *         it. The structure may be changed asynchronously only if each
 *         field is written atomically.
 *      3. Update dev->stats asynchronously and atomically, and define
 *         neither operation.
 *
 * int (*ndo_vlan_rx_add_vid)(struct net_device *dev, __be16 proto, u16 vid);
 *      If device support VLAN filtering this function is called when a
 *      VLAN id is registered.
 *
 * int (*ndo_vlan_rx_kill_vid)(struct net_device *dev, __be16 proto, u16 vid);
 *      If device support VLAN filtering this function is called when a
 *      VLAN id is unregistered.
 *
 * void (*ndo_poll_controller)(struct net_device *dev);
 *
 *      SR-IOV management functions.
 * int (*ndo_set_vf_mac)(struct net_device *dev, int vf, u8* mac);
 * int (*ndo_set_vf_vlan)(struct net_device *dev, int vf, u16 vlan, u8 qos);
 * int (*ndo_set_vf_rate)(struct net_device *dev, int vf, int min_tx_rate,
 *                        int max_tx_rate);
 * int (*ndo_set_vf_spoofchk)(struct net_device *dev, int vf, bool setting);
 * int (*ndo_get_vf_config)(struct net_device *dev,
 *                          int vf, struct ifla_vf_info *ivf);
 * int (*ndo_set_vf_link_state)(struct net_device *dev, int vf, int link_state);
 * int (*ndo_set_vf_port)(struct net_device *dev, int vf,
 *                        struct nlattr *port[]);
 *
 *      Enable or disable the VF ability to query its RSS Redirection Table and
 *      Hash Key. This is needed since on some devices VF share this information
 *      with PF and querying it may adduce a theoretical security risk.
 * int (*ndo_set_vf_rss_query_en)(struct net_device *dev, int vf, bool setting);
 * int (*ndo_get_vf_port)(struct net_device *dev, int vf, struct sk_buff *skb);
 * int (*ndo_setup_tc)(struct net_device *dev, u8 tc)
 *      Called to setup 'tc' number of traffic classes in the net device. This
 *      is always called from the stack with the rtnl lock held and netif tx
 *      queues stopped. This allows the netdevice to perform queue management
 *      safely.
 *
 *      Fiber Channel over Ethernet (FCoE) offload functions.
 * int (*ndo_fcoe_enable)(struct net_device *dev);
 *      Called when the FCoE protocol stack wants to start using LLD for FCoE
 *      so the underlying device can perform whatever needed configuration or
 *      initialization to support acceleration of FCoE traffic.
 *
 * int (*ndo_fcoe_disable)(struct net_device *dev);
 *      Called when the FCoE protocol stack wants to stop using LLD for FCoE
 *      so the underlying device can perform whatever needed clean-ups to
 *      stop supporting acceleration of FCoE traffic.
 *
 * int (*ndo_fcoe_ddp_setup)(struct net_device *dev, u16 xid,
 *                           struct scatterlist *sgl, unsigned int sgc);
 *      Called when the FCoE Initiator wants to initialize an I/O that
 *      is a possible candidate for Direct Data Placement (DDP). The LLD can
 *      perform necessary setup and returns 1 to indicate the device is set up
 *      successfully to perform DDP on this I/O, otherwise this returns 0.
 *
 * int (*ndo_fcoe_ddp_done)(struct net_device *dev,  u16 xid);
 *      Called when the FCoE Initiator/Target is done with the DDPed I/O as
 *      indicated by the FC exchange id 'xid', so the underlying device can
 *      clean up and reuse resources for later DDP requests.
 *
 * int (*ndo_fcoe_ddp_target)(struct net_device *dev, u16 xid,
 *                            struct scatterlist *sgl, unsigned int sgc);
 *      Called when the FCoE Target wants to initialize an I/O that
 *      is a possible candidate for Direct Data Placement (DDP). The LLD can
 *      perform necessary setup and returns 1 to indicate the device is set up
 *      successfully to perform DDP on this I/O, otherwise this returns 0.
 *
 * int (*ndo_fcoe_get_hbainfo)(struct net_device *dev,
 *                             struct netdev_fcoe_hbainfo *hbainfo);
 *      Called when the FCoE Protocol stack wants information on the underlying
 *      device. This information is utilized by the FCoE protocol stack to
 *      register attributes with Fiber Channel management service as per the
 *      FC-GS Fabric Device Management Information(FDMI) specification.
 *
 * int (*ndo_fcoe_get_wwn)(struct net_device *dev, u64 *wwn, int type);
 *      Called when the underlying device wants to override default World Wide
 *      Name (WWN) generation mechanism in FCoE protocol stack to pass its own
 *      World Wide Port Name (WWPN) or World Wide Node Name (WWNN) to the FCoE
 *      protocol stack to use.
 *
 *      RFS acceleration.
 * int (*ndo_rx_flow_steer)(struct net_device *dev, const struct sk_buff *skb,
 *                          u16 rxq_index, u32 flow_id);
 *      Set hardware filter for RFS.  rxq_index is the target queue index;
 *      flow_id is a flow ID to be passed to rps_may_expire_flow() later.
 *      Return the filter ID on success, or a negative error code.
 *
 *      Slave management functions (for bridge, bonding, etc).
 * int (*ndo_add_slave)(struct net_device *dev, struct net_device *slave_dev);
 *      Called to make another netdev an underling.
 *
 * int (*ndo_del_slave)(struct net_device *dev, struct net_device *slave_dev);
 *      Called to release previously enslaved netdev.
 *
 *      Feature/offload setting functions.
 * netdev_features_t (*ndo_fix_features)(struct net_device *dev,
 *              netdev_features_t features);
 *      Adjusts the requested feature flags according to device-specific
 *      constraints, and returns the resulting flags. Must not modify
 *      the device state.
 *
 * int (*ndo_set_features)(struct net_device *dev, netdev_features_t features);
 *      Called to update device configuration to new features. Passed
 *      feature set might be less than what was returned by ndo_fix_features()).
 *      Must return >0 or -errno if it changed dev->features itself.
 *
 * int (*ndo_fdb_add)(struct ndmsg *ndm, struct nlattr *tb[],
 *                    struct net_device *dev,
 *                    const unsigned char *addr, u16 vid, u16 flags)
 *      Adds an FDB entry to dev for addr.
 * int (*ndo_fdb_del)(struct ndmsg *ndm, struct nlattr *tb[],
 *                    struct net_device *dev,
 *                    const unsigned char *addr, u16 vid)
 *      Deletes the FDB entry from dev coresponding to addr.
 * int (*ndo_fdb_dump)(struct sk_buff *skb, struct netlink_callback *cb,
 *                     struct net_device *dev, struct net_device *filter_dev,
 *                     int idx)
 *      Used to add FDB entries to dump requests. Implementers should add
 *      entries to skb and update idx with the number of entries.
 *
 * int (*ndo_bridge_setlink)(struct net_device *dev, struct nlmsghdr *nlh,
 *                           u16 flags)
 * int (*ndo_bridge_getlink)(struct sk_buff *skb, u32 pid, u32 seq,
 *                           struct net_device *dev, u32 filter_mask,
 *                           int nlflags)
 * int (*ndo_bridge_dellink)(struct net_device *dev, struct nlmsghdr *nlh,
 *                           u16 flags);
 *
 * int (*ndo_change_carrier)(struct net_device *dev, bool new_carrier);
 *      Called to change device carrier. Soft-devices (like dummy, team, etc)
 *      which do not represent real hardware may define this to allow their
 *      userspace components to manage their virtual carrier state. Devices
 *      that determine carrier state from physical hardware properties (eg
 *      network cables) or protocol-dependent mechanisms (eg
 *      USB_CDC_NOTIFY_NETWORK_CONNECTION) should NOT implement this function.
 *
 * int (*ndo_get_phys_port_id)(struct net_device *dev,
 *                             struct netdev_phys_item_id *ppid);
 *      Called to get ID of physical port of this device. If driver does
 *      not implement this, it is assumed that the hw is not able to have
 *      multiple net devices on single physical port.
 *
 * void (*ndo_add_vxlan_port)(struct  net_device *dev,
 *                            sa_family_t sa_family, __be16 port);
  *      Called by vxlan to notiy a driver about the UDP port and socket
  *      address family that vxlan is listnening to. It is called only when
  *      a new port starts listening. The operation is protected by the
  *      vxlan_net->sock_lock.
  *
  * void (*ndo_del_vxlan_port)(struct  net_device *dev,
  *                            sa_family_t sa_family, __be16 port);
  *      Called by vxlan to notify the driver about a UDP port and socket
  *      address family that vxlan is not listening to anymore. The operation
  *      is protected by the vxlan_net->sock_lock.
  *
  * void* (*ndo_dfwd_add_station)(struct net_device *pdev,
  *                               struct net_device *dev)
  *      Called by upper layer devices to accelerate switching or other
  *      station functionality into hardware. 'pdev is the lowerdev
  *      to use for the offload and 'dev' is the net device that will
  *      back the offload. Returns a pointer to the private structure
  *      the upper layer will maintain.
  * void (*ndo_dfwd_del_station)(struct net_device *pdev, void *priv)
  *      Called by upper layer device to delete the station created
  *      by 'ndo_dfwd_add_station'. 'pdev' is the net device backing
  *      the station and priv is the structure returned by the add
  *      operation.
  * netdev_tx_t (*ndo_dfwd_start_xmit)(struct sk_buff *skb,
  *                                    struct net_device *dev,
  *                                    void *priv);
  *      Callback to use for xmit over the accelerated station. This
  *      is used in place of ndo_start_xmit on accelerated net
  *      devices.
  * netdev_features_t (*ndo_features_check) (struct sk_buff *skb,
  *                                          struct net_device *dev
  *                                          netdev_features_t features);
  *      Called by core transmit path to determine if device is capable of
  *      performing offload operations on a given packet. This is to give
  *      the device an opportunity to implement any restrictions that cannot
  *      be otherwise expressed by feature flags. The check is called with
  *      the set of features that the stack has calculated and it returns
  *      those the driver believes to be appropriate.
  * int (*ndo_set_tx_maxrate)(struct net_device *dev,
  *                           int queue_index, u32 maxrate);
  *      Called when a user wants to set a max-rate limitation of specific
  *      TX queue.
  * int (*ndo_get_iflink)(const struct net_device *dev);
  *      Called to get the iflink value of this device.
  */
 struct net_device_ops {
         int                     (*ndo_init)(struct net_device *dev);
         void                    (*ndo_uninit)(struct net_device *dev);
         int                     (*ndo_open)(struct net_device *dev);
         int                     (*ndo_stop)(struct net_device *dev);
         netdev_tx_t             (*ndo_start_xmit) (struct sk_buff *skb,
                                                    struct net_device *dev);
         u16                     (*ndo_select_queue)(struct net_device *dev,
                                                     struct sk_buff *skb,
                                                     void *accel_priv,
                                                     select_queue_fallback_t fallback);
         void                    (*ndo_change_rx_flags)(struct net_device *dev,
                                                        int flags);
         void                    (*ndo_set_rx_mode)(struct net_device *dev);
         int                     (*ndo_set_mac_address)(struct net_device *dev,
                                                        void *addr);
         int                     (*ndo_validate_addr)(struct net_device *dev);
         int                     (*ndo_do_ioctl)(struct net_device *dev,
                                                 struct ifreq *ifr, int cmd);
         int                     (*ndo_set_config)(struct net_device *dev,
                                                   struct ifmap *map);
         int                     (*ndo_change_mtu)(struct net_device *dev,
                                                   int new_mtu);
         int                     (*ndo_neigh_setup)(struct net_device *dev,
                                                    struct neigh_parms *);
         void                    (*ndo_tx_timeout) (struct net_device *dev);
 
         struct rtnl_link_stats64* (*ndo_get_stats64)(struct net_device *dev,
                                                      struct rtnl_link_stats64 *storage);
         struct net_device_stats* (*ndo_get_stats)(struct net_device *dev);
 
         int                     (*ndo_vlan_rx_add_vid)(struct net_device *dev,
                                                        __be16 proto, u16 vid);
         int                     (*ndo_vlan_rx_kill_vid)(struct net_device *dev,
                                                         __be16 proto, u16 vid);
 #ifdef CONFIG_NET_POLL_CONTROLLER
         void                    (*ndo_poll_controller)(struct net_device *dev);
         int                     (*ndo_netpoll_setup)(struct net_device *dev,
                                                      struct netpoll_info *info);
         void                    (*ndo_netpoll_cleanup)(struct net_device *dev);
 #endif
 #ifdef CONFIG_NET_RX_BUSY_POLL
         int                     (*ndo_busy_poll)(struct napi_struct *dev);
 #endif
         int                     (*ndo_set_vf_mac)(struct net_device *dev,
                                                   int queue, u8 *mac);
         int                     (*ndo_set_vf_vlan)(struct net_device *dev,
                                                    int queue, u16 vlan, u8 qos);
         int                     (*ndo_set_vf_rate)(struct net_device *dev,
                                                    int vf, int min_tx_rate,
                                                    int max_tx_rate);
         int                     (*ndo_set_vf_spoofchk)(struct net_device *dev,
                                                        int vf, bool setting);
         int                     (*ndo_get_vf_config)(struct net_device *dev,
                                                      int vf,
                                                      struct ifla_vf_info *ivf);
         int                     (*ndo_set_vf_link_state)(struct net_device *dev,
                                                          int vf, int link_state);
         int                     (*ndo_set_vf_port)(struct net_device *dev,
                                                    int vf,
                                                    struct nlattr *port[]);
         int                     (*ndo_get_vf_port)(struct net_device *dev,
                                                    int vf, struct sk_buff *skb);
         int                     (*ndo_set_vf_rss_query_en)(
                                                    struct net_device *dev,
                                                    int vf, bool setting);
         int                     (*ndo_setup_tc)(struct net_device *dev, u8 tc);
 #if IS_ENABLED(CONFIG_FCOE)
         int                     (*ndo_fcoe_enable)(struct net_device *dev);
         int                     (*ndo_fcoe_disable)(struct net_device *dev);
         int                     (*ndo_fcoe_ddp_setup)(struct net_device *dev,
                                                       u16 xid,
                                                       struct scatterlist *sgl,
                                                       unsigned int sgc);
         int                     (*ndo_fcoe_ddp_done)(struct net_device *dev,
                                                      u16 xid);
         int                     (*ndo_fcoe_ddp_target)(struct net_device *dev,
                                                        u16 xid,
                                                        struct scatterlist *sgl,
                                                        unsigned int sgc);
         int                     (*ndo_fcoe_get_hbainfo)(struct net_device *dev,
                                                         struct netdev_fcoe_hbainfo *hbainfo);
 #endif
 
 #if IS_ENABLED(CONFIG_LIBFCOE)
 #define NETDEV_FCOE_WWNN 0
 #define NETDEV_FCOE_WWPN 1
         int                     (*ndo_fcoe_get_wwn)(struct net_device *dev,
                                                     u64 *wwn, int type);
 #endif
 
 #ifdef CONFIG_RFS_ACCEL
         int                     (*ndo_rx_flow_steer)(struct net_device *dev,
                                                      const struct sk_buff *skb,
                                                      u16 rxq_index,
                                                      u32 flow_id);
 #endif
         int                     (*ndo_add_slave)(struct net_device *dev,
                                                  struct net_device *slave_dev);
         int                     (*ndo_del_slave)(struct net_device *dev,
                                                  struct net_device *slave_dev);
         netdev_features_t       (*ndo_fix_features)(struct net_device *dev,
                                                     netdev_features_t features);
         int                     (*ndo_set_features)(struct net_device *dev,
                                                     netdev_features_t features);
         int                     (*ndo_neigh_construct)(struct neighbour *n);
         void                    (*ndo_neigh_destroy)(struct neighbour *n);
 
         int                     (*ndo_fdb_add)(struct ndmsg *ndm,
                                                struct nlattr *tb[],
                                                struct net_device *dev,
                                                const unsigned char *addr,
                                                u16 vid,
                                                u16 flags);
         int                     (*ndo_fdb_del)(struct ndmsg *ndm,
                                                struct nlattr *tb[],
                                                struct net_device *dev,
                                                const unsigned char *addr,
                                                u16 vid);
         int                     (*ndo_fdb_dump)(struct sk_buff *skb,
                                                 struct netlink_callback *cb,
                                                 struct net_device *dev,
                                                 struct net_device *filter_dev,
                                                 int idx);
 
         int                     (*ndo_bridge_setlink)(struct net_device *dev,
                                                       struct nlmsghdr *nlh,
                                                       u16 flags);
         int                     (*ndo_bridge_getlink)(struct sk_buff *skb,
                                                       u32 pid, u32 seq,
                                                       struct net_device *dev,
                                                       u32 filter_mask,
                                                       int nlflags);
         int                     (*ndo_bridge_dellink)(struct net_device *dev,
                                                       struct nlmsghdr *nlh,
                                                       u16 flags);
         int                     (*ndo_change_carrier)(struct net_device *dev,
                                                       bool new_carrier);
         int                     (*ndo_get_phys_port_id)(struct net_device *dev,
                                                         struct netdev_phys_item_id *ppid);
         int                     (*ndo_get_phys_port_name)(struct net_device *dev,
                                                           char *name, size_t len);
         void                    (*ndo_add_vxlan_port)(struct  net_device *dev,
                                                       sa_family_t sa_family,
                                                       __be16 port);
         void                    (*ndo_del_vxlan_port)(struct  net_device *dev,
                                                       sa_family_t sa_family,
                                                       __be16 port);
 
         void*                   (*ndo_dfwd_add_station)(struct net_device *pdev,
                                                         struct net_device *dev);
         void                    (*ndo_dfwd_del_station)(struct net_device *pdev,
                                                         void *priv);
 
         netdev_tx_t             (*ndo_dfwd_start_xmit) (struct sk_buff *skb,
                                                         struct net_device *dev,
                                                         void *priv);
         int                     (*ndo_get_lock_subclass)(struct net_device *dev);
         netdev_features_t       (*ndo_features_check) (struct sk_buff *skb,
                                                        struct net_device *dev,
                                                        netdev_features_t features);
         int                     (*ndo_set_tx_maxrate)(struct net_device *dev,
                                                       int queue_index,
                                                       u32 maxrate);
         int                     (*ndo_get_iflink)(const struct net_device *dev);
 };
 
 /**
  * enum net_device_priv_flags - &struct net_device priv_flags
  *
  * These are the &struct net_device, they are only set internally
  * by drivers and used in the kernel. These flags are invisible to
  * userspace, this means that the order of these flags can change
  * during any kernel release.
  *
  * You should have a pretty good reason to be extending these flags.
  *
  * @IFF_802_1Q_VLAN: 802.1Q VLAN device
  * @IFF_EBRIDGE: Ethernet bridging device
  * @IFF_SLAVE_INACTIVE: bonding slave not the curr. active
  * @IFF_MASTER_8023AD: bonding master, 802.3ad
  * @IFF_MASTER_ALB: bonding master, balance-alb
  * @IFF_BONDING: bonding master or slave
  * @IFF_SLAVE_NEEDARP: need ARPs for validation
  * @IFF_ISATAP: ISATAP interface (RFC4214)
  * @IFF_MASTER_ARPMON: bonding master, ARP mon in use
  * @IFF_WAN_HDLC: WAN HDLC device
  * @IFF_XMIT_DST_RELEASE: dev_hard_start_xmit() is allowed to
  *      release skb->dst
  * @IFF_DONT_BRIDGE: disallow bridging this ether dev
  * @IFF_DISABLE_NETPOLL: disable netpoll at run-time
  * @IFF_MACVLAN_PORT: device used as macvlan port
  * @IFF_BRIDGE_PORT: device used as bridge port
  * @IFF_OVS_DATAPATH: device used as Open vSwitch datapath port
  * @IFF_TX_SKB_SHARING: The interface supports sharing skbs on transmit
  * @IFF_UNICAST_FLT: Supports unicast filtering
  * @IFF_TEAM_PORT: device used as team port
  * @IFF_SUPP_NOFCS: device supports sending custom FCS
  * @IFF_LIVE_ADDR_CHANGE: device supports hardware address
  *      change when it's running
  * @IFF_MACVLAN: Macvlan device
  */
 enum netdev_priv_flags {
         IFF_802_1Q_VLAN                 = 1<<0,
         IFF_EBRIDGE                     = 1<<1,
         IFF_SLAVE_INACTIVE              = 1<<2,
         IFF_MASTER_8023AD               = 1<<3,
         IFF_MASTER_ALB                  = 1<<4,
         IFF_BONDING                     = 1<<5,
         IFF_SLAVE_NEEDARP               = 1<<6,
         IFF_ISATAP                      = 1<<7,
         IFF_MASTER_ARPMON               = 1<<8,
         IFF_WAN_HDLC                    = 1<<9,
         IFF_XMIT_DST_RELEASE            = 1<<10,
         IFF_DONT_BRIDGE                 = 1<<11,
         IFF_DISABLE_NETPOLL             = 1<<12,
         IFF_MACVLAN_PORT                = 1<<13,
         IFF_BRIDGE_PORT                 = 1<<14,
         IFF_OVS_DATAPATH                = 1<<15,
         IFF_TX_SKB_SHARING              = 1<<16,
         IFF_UNICAST_FLT                 = 1<<17,
         IFF_TEAM_PORT                   = 1<<18,
         IFF_SUPP_NOFCS                  = 1<<19,
         IFF_LIVE_ADDR_CHANGE            = 1<<20,
         IFF_MACVLAN                     = 1<<21,
         IFF_XMIT_DST_RELEASE_PERM       = 1<<22,
         IFF_IPVLAN_MASTER               = 1<<23,
         IFF_IPVLAN_SLAVE                = 1<<24,
 };
 
 #define IFF_802_1Q_VLAN                 IFF_802_1Q_VLAN
 #define IFF_EBRIDGE                     IFF_EBRIDGE
 #define IFF_SLAVE_INACTIVE              IFF_SLAVE_INACTIVE
 #define IFF_MASTER_8023AD               IFF_MASTER_8023AD
 #define IFF_MASTER_ALB                  IFF_MASTER_ALB
 #define IFF_BONDING                     IFF_BONDING
 #define IFF_SLAVE_NEEDARP               IFF_SLAVE_NEEDARP
 #define IFF_ISATAP                      IFF_ISATAP
 #define IFF_MASTER_ARPMON               IFF_MASTER_ARPMON
 #define IFF_WAN_HDLC                    IFF_WAN_HDLC
 #define IFF_XMIT_DST_RELEASE            IFF_XMIT_DST_RELEASE
 #define IFF_DONT_BRIDGE                 IFF_DONT_BRIDGE
 #define IFF_DISABLE_NETPOLL             IFF_DISABLE_NETPOLL
 #define IFF_MACVLAN_PORT                IFF_MACVLAN_PORT
 #define IFF_BRIDGE_PORT                 IFF_BRIDGE_PORT
 #define IFF_OVS_DATAPATH                IFF_OVS_DATAPATH
 #define IFF_TX_SKB_SHARING              IFF_TX_SKB_SHARING
 #define IFF_UNICAST_FLT                 IFF_UNICAST_FLT
 #define IFF_TEAM_PORT                   IFF_TEAM_PORT
 #define IFF_SUPP_NOFCS                  IFF_SUPP_NOFCS
 #define IFF_LIVE_ADDR_CHANGE            IFF_LIVE_ADDR_CHANGE
 #define IFF_MACVLAN                     IFF_MACVLAN
 #define IFF_XMIT_DST_RELEASE_PERM       IFF_XMIT_DST_RELEASE_PERM
 #define IFF_IPVLAN_MASTER               IFF_IPVLAN_MASTER
 #define IFF_IPVLAN_SLAVE                IFF_IPVLAN_SLAVE
 
 /**
  *      struct net_device - The DEVICE structure.
  *              Actually, this whole structure is a big mistake.  It mixes I/O
  *              data with strictly "high-level" data, and it has to know about
  *              almost every data structure used in the INET module.
  *
  *      @name:  This is the first field of the "visible" part of this structure
  *              (i.e. as seen by users in the "Space.c" file).  It is the name
  *              of the interface.
  *
  *      @name_hlist:    Device name hash chain, please keep it close to name[]
  *      @ifalias:       SNMP alias
  *      @mem_end:       Shared memory end
  *      @mem_start:     Shared memory start
  *      @base_addr:     Device I/O address
  *      @irq:           Device IRQ number
  *
  *      @carrier_changes:       Stats to monitor carrier on<->off transitions
  *
  *      @state:         Generic network queuing layer state, see netdev_state_t
  *      @dev_list:      The global list of network devices
  *      @napi_list:     List entry, that is used for polling napi devices
  *      @unreg_list:    List entry, that is used, when we are unregistering the
  *                      device, see the function unregister_netdev
  *      @close_list:    List entry, that is used, when we are closing the device
  *
  *      @adj_list:      Directly linked devices, like slaves for bonding
  *      @all_adj_list:  All linked devices, *including* neighbours
  *      @features:      Currently active device features
  *      @hw_features:   User-changeable features
  *
  *      @wanted_features:       User-requested features
  *      @vlan_features:         Mask of features inheritable by VLAN devices
  *
  *      @hw_enc_features:       Mask of features inherited by encapsulating devices
  *                              This field indicates what encapsulation
  *                              offloads the hardware is capable of doing,
  *                              and drivers will need to set them appropriately.
  *
  *      @mpls_features: Mask of features inheritable by MPLS
  *
  *      @ifindex:       interface index
  *      @group:         The group, that the device belongs to
  *
  *      @stats:         Statistics struct, which was left as a legacy, use
  *                      rtnl_link_stats64 instead
  *
  *      @rx_dropped:    Dropped packets by core network,
  *                      do not use this in drivers
  *      @tx_dropped:    Dropped packets by core network,
  *                      do not use this in drivers
  *
  *      @wireless_handlers:     List of functions to handle Wireless Extensions,
  *                              instead of ioctl,
  *                              see <net/iw_handler.h> for details.
  *      @wireless_data: Instance data managed by the core of wireless extensions
  *
  *      @netdev_ops:    Includes several pointers to callbacks,
  *                      if one wants to override the ndo_*() functions
  *      @ethtool_ops:   Management operations
  *      @header_ops:    Includes callbacks for creating,parsing,caching,etc
  *                      of Layer 2 headers.
  *
  *      @flags:         Interface flags (a la BSD)
  *      @priv_flags:    Like 'flags' but invisible to userspace,
  *                      see if.h for the definitions
  *      @gflags:        Global flags ( kept as legacy )
  *      @padded:        How much padding added by alloc_netdev()
  *      @operstate:     RFC2863 operstate
  *      @link_mode:     Mapping policy to operstate
  *      @if_port:       Selectable AUI, TP, ...
  *      @dma:           DMA channel
  *      @mtu:           Interface MTU value
  *      @type:          Interface hardware type
  *      @hard_header_len: Hardware header length
  *
  *      @needed_headroom: Extra headroom the hardware may need, but not in all
  *                        cases can this be guaranteed
  *      @needed_tailroom: Extra tailroom the hardware may need, but not in all
  *                        cases can this be guaranteed. Some cases also use
  *                        LL_MAX_HEADER instead to allocate the skb
  *
  *      interface address info:
  *
  *      @perm_addr:             Permanent hw address
  *      @addr_assign_type:      Hw address assignment type
  *      @addr_len:              Hardware address length
  *      @neigh_priv_len;        Used in neigh_alloc(),
  *                              initialized only in atm/clip.c
  *      @dev_id:                Used to differentiate devices that share
  *                              the same link layer address
  *      @dev_port:              Used to differentiate devices that share
  *                              the same function
  *      @addr_list_lock:        XXX: need comments on this one
  *      @uc_promisc:            Counter, that indicates, that promiscuous mode
  *                              has been enabled due to the need to listen to
  *                              additional unicast addresses in a device that
  *                              does not implement ndo_set_rx_mode()
  *      @uc:                    unicast mac addresses
  *      @mc:                    multicast mac addresses
  *      @dev_addrs:             list of device hw addresses
  *      @queues_kset:           Group of all Kobjects in the Tx and RX queues
  *      @promiscuity:           Number of times, the NIC is told to work in
  *                              Promiscuous mode, if it becomes 0 the NIC will
  *                              exit from working in Promiscuous mode
  *      @allmulti:              Counter, enables or disables allmulticast mode
  *
  *      @vlan_info:     VLAN info
  *      @dsa_ptr:       dsa specific data
  *      @tipc_ptr:      TIPC specific data
  *      @atalk_ptr:     AppleTalk link
  *      @ip_ptr:        IPv4 specific data
  *      @dn_ptr:        DECnet specific data
  *      @ip6_ptr:       IPv6 specific data
  *      @ax25_ptr:      AX.25 specific data
  *      @ieee80211_ptr: IEEE 802.11 specific data, assign before registering
  *
  *      @last_rx:       Time of last Rx
  *      @dev_addr:      Hw address (before bcast,
  *                      because most packets are unicast)
  *
  *      @_rx:                   Array of RX queues
  *      @num_rx_queues:         Number of RX queues
  *                              allocated at register_netdev() time
  *      @real_num_rx_queues:    Number of RX queues currently active in device
  *
  *      @rx_handler:            handler for received packets
  *      @rx_handler_data:       XXX: need comments on this one
  *      @ingress_queue:         XXX: need comments on this one
  *      @broadcast:             hw bcast address
  *
  *      @rx_cpu_rmap:   CPU reverse-mapping for RX completion interrupts,
  *                      indexed by RX queue number. Assigned by driver.
  *                      This must only be set if the ndo_rx_flow_steer
  *                      operation is defined
  *      @index_hlist:           Device index hash chain
  *
  *      @_tx:                   Array of TX queues
  *      @num_tx_queues:         Number of TX queues allocated at alloc_netdev_mq() time
  *      @real_num_tx_queues:    Number of TX queues currently active in device
  *      @qdisc:                 Root qdisc from userspace point of view
  *      @tx_queue_len:          Max frames per queue allowed
  *      @tx_global_lock:        XXX: need comments on this one
  *
  *      @xps_maps:      XXX: need comments on this one
  *
  *      @trans_start:           Time (in jiffies) of last Tx
  *      @watchdog_timeo:        Represents the timeout that is used by
  *                              the watchdog ( see dev_watchdog() )
  *      @watchdog_timer:        List of timers
  *
  *      @pcpu_refcnt:           Number of references to this device
  *      @todo_list:             Delayed register/unregister
  *      @link_watch_list:       XXX: need comments on this one
  *
  *      @reg_state:             Register/unregister state machine
  *      @dismantle:             Device is going to be freed
  *      @rtnl_link_state:       This enum represents the phases of creating
  *                              a new link
  *
  *      @destructor:            Called from unregister,
  *                              can be used to call free_netdev
  *      @npinfo:                XXX: need comments on this one
  *      @nd_net:                Network namespace this network device is inside
  *
  *      @ml_priv:       Mid-layer private
  *      @lstats:        Loopback statistics
  *      @tstats:        Tunnel statistics
  *      @dstats:        Dummy statistics
  *      @vstats:        Virtual ethernet statistics
  *
  *      @garp_port:     GARP
  *      @mrp_port:      MRP
  *
  *      @dev:           Class/net/name entry
  *      @sysfs_groups:  Space for optional device, statistics and wireless
  *                      sysfs groups
  *
  *      @sysfs_rx_queue_group:  Space for optional per-rx queue attributes
  *      @rtnl_link_ops: Rtnl_link_ops
  *
  *      @gso_max_size:  Maximum size of generic segmentation offload
  *      @gso_max_segs:  Maximum number of segments that can be passed to the
  *                      NIC for GSO
  *      @gso_min_segs:  Minimum number of segments that can be passed to the
  *                      NIC for GSO
  *
  *      @dcbnl_ops:     Data Center Bridging netlink ops
  *      @num_tc:        Number of traffic classes in the net device
  *      @tc_to_txq:     XXX: need comments on this one
  *      @prio_tc_map    XXX: need comments on this one
  *
  *      @fcoe_ddp_xid:  Max exchange id for FCoE LRO by ddp
  *
  *      @priomap:       XXX: need comments on this one
  *      @phydev:        Physical device may attach itself
  *                      for hardware timestamping
  *
  *      @qdisc_tx_busylock:     XXX: need comments on this one
  *
  *      FIXME: cleanup struct net_device such that network protocol info
  *      moves out.
  */
 
 struct net_device {
         char                    name[IFNAMSIZ];
         struct hlist_node       name_hlist;
         char                    *ifalias;
         /*
          *      I/O specific fields
          *      FIXME: Merge these and struct ifmap into one
          */
         unsigned long           mem_end;
         unsigned long           mem_start;
         unsigned long           base_addr;
         int                     irq;
 
         atomic_t                carrier_changes;
 
         /*
          *      Some hardware also needs these fields (state,dev_list,
          *      napi_list,unreg_list,close_list) but they are not
          *      part of the usual set specified in Space.c.
          */
 
         unsigned long           state;
 
         struct list_head        dev_list;
         struct list_head        napi_list;
         struct list_head        unreg_list;
         struct list_head        close_list;
         struct list_head        ptype_all;
         struct list_head        ptype_specific;
 
         struct {
                 struct list_head upper;
                 struct list_head lower;
         } adj_list;
 
         struct {
                 struct list_head upper;
                 struct list_head lower;
         } all_adj_list;
 
         netdev_features_t       features;
         netdev_features_t       hw_features;
         netdev_features_t       wanted_features;
         netdev_features_t       vlan_features;
         netdev_features_t       hw_enc_features;
         netdev_features_t       mpls_features;
 
         int                     ifindex;
         int                     group;
 
         struct net_device_stats stats;
 
         atomic_long_t           rx_dropped;
         atomic_long_t           tx_dropped;
 
 #ifdef CONFIG_WIRELESS_EXT
         const struct iw_handler_def *   wireless_handlers;
         struct iw_public_data * wireless_data;
 #endif
         const struct net_device_ops *netdev_ops;
         const struct ethtool_ops *ethtool_ops;
 #ifdef CONFIG_NET_SWITCHDEV
         const struct swdev_ops *swdev_ops;
 #endif
 
         const struct header_ops *header_ops;
 
         unsigned int            flags;
         unsigned int            priv_flags;
 
         unsigned short          gflags;
         unsigned short          padded;
 
         unsigned char           operstate;
         unsigned char           link_mode;
 
         unsigned char           if_port;
         unsigned char           dma;
 
         unsigned int            mtu;
         unsigned short          type;
         unsigned short          hard_header_len;
 
         unsigned short          needed_headroom;
         unsigned short          needed_tailroom;
 
         /* Interface address info. */
         unsigned char           perm_addr[MAX_ADDR_LEN];
         unsigned char           addr_assign_type;
         unsigned char           addr_len;
         unsigned short          neigh_priv_len;
         unsigned short          dev_id;
         unsigned short          dev_port;
         spinlock_t              addr_list_lock;
         unsigned char           name_assign_type;
         bool                    uc_promisc;
         struct netdev_hw_addr_list      uc;
         struct netdev_hw_addr_list      mc;
         struct netdev_hw_addr_list      dev_addrs;
 
 #ifdef CONFIG_SYSFS
         struct kset             *queues_kset;
 #endif
         unsigned int            promiscuity;
         unsigned int            allmulti;
 
 
         /* Protocol specific pointers */
 
 #if IS_ENABLED(CONFIG_VLAN_8021Q)
         struct vlan_info __rcu  *vlan_info;
 #endif
 #if IS_ENABLED(CONFIG_NET_DSA)
         struct dsa_switch_tree  *dsa_ptr;
 #endif
 #if IS_ENABLED(CONFIG_TIPC)
         struct tipc_bearer __rcu *tipc_ptr;
 #endif
         void                    *atalk_ptr;
         struct in_device __rcu  *ip_ptr;
         struct dn_dev __rcu     *dn_ptr;
         struct inet6_dev __rcu  *ip6_ptr;
         void                    *ax25_ptr;
         struct wireless_dev     *ieee80211_ptr;
         struct wpan_dev         *ieee802154_ptr;
 #if IS_ENABLED(CONFIG_MPLS_ROUTING)
         struct mpls_dev __rcu   *mpls_ptr;
 #endif
 
 /*
  * Cache lines mostly used on receive path (including eth_type_trans())
  */
         unsigned long           last_rx;
 
         /* Interface address info used in eth_type_trans() */
         unsigned char           *dev_addr;
 
 
 #ifdef CONFIG_SYSFS
         struct netdev_rx_queue  *_rx;
 
         unsigned int            num_rx_queues;
         unsigned int            real_num_rx_queues;
 
 #endif
 
         unsigned long           gro_flush_timeout;
         rx_handler_func_t __rcu *rx_handler;
         void __rcu              *rx_handler_data;
 
         struct netdev_queue __rcu *ingress_queue;
         unsigned char           broadcast[MAX_ADDR_LEN];
 #ifdef CONFIG_RFS_ACCEL
         struct cpu_rmap         *rx_cpu_rmap;
 #endif
         struct hlist_node       index_hlist;
 
 /*
  * Cache lines mostly used on transmit path
  */
         struct netdev_queue     *_tx ____cacheline_aligned_in_smp;
         unsigned int            num_tx_queues;
         unsigned int            real_num_tx_queues;
         struct Qdisc            *qdisc;
         unsigned long           tx_queue_len;
         spinlock_t              tx_global_lock;
         int                     watchdog_timeo;
 
 #ifdef CONFIG_XPS
         struct xps_dev_maps __rcu *xps_maps;
 #endif
 
         /* These may be needed for future network-power-down code. */
 
         /*
          * trans_start here is expensive for high speed devices on SMP,
          * please use netdev_queue->trans_start instead.
          */
         unsigned long           trans_start;
 
         struct timer_list       watchdog_timer;
 
         int __percpu            *pcpu_refcnt;
         struct list_head        todo_list;
 
         struct list_head        link_watch_list;
 
         enum { NETREG_UNINITIALIZED=0,
                NETREG_REGISTERED,       /* completed register_netdevice */
                NETREG_UNREGISTERING,    /* called unregister_netdevice */
                NETREG_UNREGISTERED,     /* completed unregister todo */
                NETREG_RELEASED,         /* called free_netdev */
                NETREG_DUMMY,            /* dummy device for NAPI poll */
         } reg_state:8;
 
         bool dismantle;
 
         enum {
                 RTNL_LINK_INITIALIZED,
                 RTNL_LINK_INITIALIZING,
         } rtnl_link_state:16;
 
         void (*destructor)(struct net_device *dev);
 
 #ifdef CONFIG_NETPOLL
         struct netpoll_info __rcu       *npinfo;
 #endif
 
         possible_net_t                  nd_net;
 
         /* mid-layer private */
         union {
                 void                                    *ml_priv;
                 struct pcpu_lstats __percpu             *lstats;
                 struct pcpu_sw_netstats __percpu        *tstats;
                 struct pcpu_dstats __percpu             *dstats;
                 struct pcpu_vstats __percpu             *vstats;
         };
 
         struct garp_port __rcu  *garp_port;
         struct mrp_port __rcu   *mrp_port;
 
         struct device   dev;
         const struct attribute_group *sysfs_groups[4];
         const struct attribute_group *sysfs_rx_queue_group;
 
         const struct rtnl_link_ops *rtnl_link_ops;
 
         /* for setting kernel sock attribute on TCP connection setup */
 #define GSO_MAX_SIZE            65536
         unsigned int            gso_max_size;
 #define GSO_MAX_SEGS            65535
         u16                     gso_max_segs;
         u16                     gso_min_segs;
 #ifdef CONFIG_DCB
         const struct dcbnl_rtnl_ops *dcbnl_ops;
 #endif
         u8 num_tc;
         struct netdev_tc_txq tc_to_txq[TC_MAX_QUEUE];
         u8 prio_tc_map[TC_BITMASK + 1];
 
 #if IS_ENABLED(CONFIG_FCOE)
         unsigned int            fcoe_ddp_xid;
 #endif
 #if IS_ENABLED(CONFIG_CGROUP_NET_PRIO)
         struct netprio_map __rcu *priomap;
 #endif
         struct phy_device *phydev;
         struct lock_class_key *qdisc_tx_busylock;
 };
 #define to_net_dev(d) container_of(d, struct net_device, dev)
 
 #define NETDEV_ALIGN            32
 
 static inline
 int netdev_get_prio_tc_map(const struct net_device *dev, u32 prio)
 {
         return dev->prio_tc_map[prio & TC_BITMASK];
 }
 
 static inline
 int netdev_set_prio_tc_map(struct net_device *dev, u8 prio, u8 tc)
 {
         if (tc >= dev->num_tc)
                 return -EINVAL;
 
         dev->prio_tc_map[prio & TC_BITMASK] = tc & TC_BITMASK;
         return 0;
 }
 
 static inline
 void netdev_reset_tc(struct net_device *dev)
 {
         dev->num_tc = 0;
         memset(dev->tc_to_txq, 0, sizeof(dev->tc_to_txq));
         memset(dev->prio_tc_map, 0, sizeof(dev->prio_tc_map));
 }
 
 static inline
 int netdev_set_tc_queue(struct net_device *dev, u8 tc, u16 count, u16 offset)
 {
         if (tc >= dev->num_tc)
                 return -EINVAL;
 
         dev->tc_to_txq[tc].count = count;
         dev->tc_to_txq[tc].offset = offset;
         return 0;
 }
 
 static inline
 int netdev_set_num_tc(struct net_device *dev, u8 num_tc)
 {
         if (num_tc > TC_MAX_QUEUE)
                 return -EINVAL;
 
         dev->num_tc = num_tc;
         return 0;
 }
 
 static inline
 int netdev_get_num_tc(struct net_device *dev)
 {
         return dev->num_tc;
 }
 
 static inline
 struct netdev_queue *netdev_get_tx_queue(const struct net_device *dev,
                                          unsigned int index)
 {
         return &dev->_tx[index];
 }
 
 static inline struct netdev_queue *skb_get_tx_queue(const struct net_device *dev,
                                                     const struct sk_buff *skb)
 {
         return netdev_get_tx_queue(dev, skb_get_queue_mapping(skb));
 }
 
 static inline void netdev_for_each_tx_queue(struct net_device *dev,
                                             void (*f)(struct net_device *,
                                                       struct netdev_queue *,
                                                       void *),
                                             void *arg)
 {
         unsigned int i;
 
         for (i = 0; i < dev->num_tx_queues; i++)
                 f(dev, &dev->_tx[i], arg);
 }
 
 struct netdev_queue *netdev_pick_tx(struct net_device *dev,
                                     struct sk_buff *skb,
                                     void *accel_priv);
 
 /*
  * Net namespace inlines
  */
 static inline
 struct net *dev_net(const struct net_device *dev)
 {
         return read_pnet(&dev->nd_net);
 }
 
 static inline
 void dev_net_set(struct net_device *dev, struct net *net)
 {
         write_pnet(&dev->nd_net, net);
 }
 
 static inline bool netdev_uses_dsa(struct net_device *dev)
 {
 #if IS_ENABLED(CONFIG_NET_DSA)
         if (dev->dsa_ptr != NULL)
                 return dsa_uses_tagged_protocol(dev->dsa_ptr);
 #endif
         return false;
 }
 
 /**
  *      netdev_priv - access network device private data
  *      @dev: network device
  *
  * Get network device private data
  */
 static inline void *netdev_priv(const struct net_device *dev)
 {
         return (char *)dev + ALIGN(sizeof(struct net_device), NETDEV_ALIGN);
 }
 
 /* Set the sysfs physical device reference for the network logical device
  * if set prior to registration will cause a symlink during initialization.
  */
 #define SET_NETDEV_DEV(net, pdev)       ((net)->dev.parent = (pdev))
 
 /* Set the sysfs device type for the network logical device to allow
  * fine-grained identification of different network device types. For
  * example Ethernet, Wirelss LAN, Bluetooth, WiMAX etc.
  */
 #define SET_NETDEV_DEVTYPE(net, devtype)        ((net)->dev.type = (devtype))
 
 /* Default NAPI poll() weight
  * Device drivers are strongly advised to not use bigger value
  */
 #define NAPI_POLL_WEIGHT 64
 
 /**
  *      netif_napi_add - initialize a napi context
  *      @dev:  network device
  *      @napi: napi context
  *      @poll: polling function
  *      @weight: default weight
  *
  * netif_napi_add() must be used to initialize a napi context prior to calling
  * *any* of the other napi related functions.
  */
 void netif_napi_add(struct net_device *dev, struct napi_struct *napi,
                     int (*poll)(struct napi_struct *, int), int weight);
 
 /**
  *  netif_napi_del - remove a napi context
  *  @napi: napi context
  *
  *  netif_napi_del() removes a napi context from the network device napi list
  */
 void netif_napi_del(struct napi_struct *napi);
 
 struct napi_gro_cb {
         /* Virtual address of skb_shinfo(skb)->frags[0].page + offset. */
         void *frag0;
 
         /* Length of frag0. */
         unsigned int frag0_len;
 
         /* This indicates where we are processing relative to skb->data. */
         int data_offset;
 
         /* This is non-zero if the packet cannot be merged with the new skb. */
         u16     flush;
 
         /* Save the IP ID here and check when we get to the transport layer */
         u16     flush_id;
 
         /* Number of segments aggregated. */
         u16     count;
 
         /* Start offset for remote checksum offload */
         u16     gro_remcsum_start;
 
         /* jiffies when first packet was created/queued */
         unsigned long age;
 
         /* Used in ipv6_gro_receive() and foo-over-udp */
         u16     proto;
 
         /* This is non-zero if the packet may be of the same flow. */
         u8      same_flow:1;
 
         /* Used in udp_gro_receive */
         u8      udp_mark:1;
 
         /* GRO checksum is valid */
         u8      csum_valid:1;
 
         /* Number of checksums via CHECKSUM_UNNECESSARY */
         u8      csum_cnt:3;
 
         /* Free the skb? */
         u8      free:2;
 #define NAPI_GRO_FREE             1
 #define NAPI_GRO_FREE_STOLEN_HEAD 2
 
         /* Used in foo-over-udp, set in udp[46]_gro_receive */
         u8      is_ipv6:1;
 
         /* 7 bit hole */
 
         /* used to support CHECKSUM_COMPLETE for tunneling protocols */
         __wsum  csum;
 
         /* used in skb_gro_receive() slow path */
         struct sk_buff *last;
 };
 
 #define NAPI_GRO_CB(skb) ((struct napi_gro_cb *)(skb)->cb)
 
 struct packet_type {
         __be16                  type;   /* This is really htons(ether_type). */
         struct net_device       *dev;   /* NULL is wildcarded here           */
         int                     (*func) (struct sk_buff *,
                                          struct net_device *,
                                          struct packet_type *,
                                          struct net_device *);
         bool                    (*id_match)(struct packet_type *ptype,
                                             struct sock *sk);
         void                    *af_packet_priv;
         struct list_head        list;
 };
 
 struct offload_callbacks {
         struct sk_buff          *(*gso_segment)(struct sk_buff *skb,
                                                 netdev_features_t features);
         struct sk_buff          **(*gro_receive)(struct sk_buff **head,
                                                  struct sk_buff *skb);
         int                     (*gro_complete)(struct sk_buff *skb, int nhoff);
 };
 
 struct packet_offload {
         __be16                   type;  /* This is really htons(ether_type). */
         struct offload_callbacks callbacks;
         struct list_head         list;
 };
 
 struct udp_offload;
 
 struct udp_offload_callbacks {
         struct sk_buff          **(*gro_receive)(struct sk_buff **head,
                                                  struct sk_buff *skb,
                                                  struct udp_offload *uoff);
         int                     (*gro_complete)(struct sk_buff *skb,
                                                 int nhoff,
                                                 struct udp_offload *uoff);
 };
 
 struct udp_offload {
         __be16                   port;
         u8                       ipproto;
         struct udp_offload_callbacks callbacks;
 };
 
 /* often modified stats are per cpu, other are shared (netdev->stats) */
 struct pcpu_sw_netstats {
         u64     rx_packets;
         u64     rx_bytes;
         u64     tx_packets;
         u64     tx_bytes;
         struct u64_stats_sync   syncp;
 };
 
 #define netdev_alloc_pcpu_stats(type)                           \
 ({                                                              \
         typeof(type) __percpu *pcpu_stats = alloc_percpu(type); \
         if (pcpu_stats) {                                       \
                 int __cpu;                                      \
                 for_each_possible_cpu(__cpu) {                  \
                         typeof(type) *stat;                     \
                         stat = per_cpu_ptr(pcpu_stats, __cpu);  \
                         u64_stats_init(&stat->syncp);           \
                 }                                               \
         }                                                       \
         pcpu_stats;                                             \
 })
 
 #include <linux/notifier.h>
 
 /* netdevice notifier chain. Please remember to update the rtnetlink
  * notification exclusion list in rtnetlink_event() when adding new
  * types.
  */
 #define NETDEV_UP       0x0001  /* For now you can't veto a device up/down */
 #define NETDEV_DOWN     0x0002
 #define NETDEV_REBOOT   0x0003  /* Tell a protocol stack a network interface
                                    detected a hardware crash and restarted
                                    - we can use this eg to kick tcp sessions
                                    once done */
 #define NETDEV_CHANGE   0x0004  /* Notify device state change */
 #define NETDEV_REGISTER 0x0005
 #define NETDEV_UNREGISTER       0x0006
 #define NETDEV_CHANGEMTU        0x0007 /* notify after mtu change happened */
 #define NETDEV_CHANGEADDR       0x0008
 #define NETDEV_GOING_DOWN       0x0009
 #define NETDEV_CHANGENAME       0x000A
 #define NETDEV_FEAT_CHANGE      0x000B
 #define NETDEV_BONDING_FAILOVER 0x000C
 #define NETDEV_PRE_UP           0x000D
 #define NETDEV_PRE_TYPE_CHANGE  0x000E
 #define NETDEV_POST_TYPE_CHANGE 0x000F
 #define NETDEV_POST_INIT        0x0010
 #define NETDEV_UNREGISTER_FINAL 0x0011
 #define NETDEV_RELEASE          0x0012
 #define NETDEV_NOTIFY_PEERS     0x0013
 #define NETDEV_JOIN             0x0014
 #define NETDEV_CHANGEUPPER      0x0015
 #define NETDEV_RESEND_IGMP      0x0016
 #define NETDEV_PRECHANGEMTU     0x0017 /* notify before mtu change happened */
 #define NETDEV_CHANGEINFODATA   0x0018
 #define NETDEV_BONDING_INFO     0x0019
 
 int register_netdevice_notifier(struct notifier_block *nb);
 int unregister_netdevice_notifier(struct notifier_block *nb);
 
 struct netdev_notifier_info {
         struct net_device *dev;
 };
 
 struct netdev_notifier_change_info {
         struct netdev_notifier_info info; /* must be first */
         unsigned int flags_changed;
 };
 
 static inline void netdev_notifier_info_init(struct netdev_notifier_info *info,
                                              struct net_device *dev)
 {
         info->dev = dev;
 }
 
 static inline struct net_device *
 netdev_notifier_info_to_dev(const struct netdev_notifier_info *info)
 {
         return info->dev;
 }
 
 int call_netdevice_notifiers(unsigned long val, struct net_device *dev);
 
 
 extern rwlock_t                         dev_base_lock;          /* Device list lock */
 
 #define for_each_netdev(net, d)         \
                 list_for_each_entry(d, &(net)->dev_base_head, dev_list)
 #define for_each_netdev_reverse(net, d) \
                 list_for_each_entry_reverse(d, &(net)->dev_base_head, dev_list)
 #define for_each_netdev_rcu(net, d)             \
                 list_for_each_entry_rcu(d, &(net)->dev_base_head, dev_list)
 #define for_each_netdev_safe(net, d, n) \
                 list_for_each_entry_safe(d, n, &(net)->dev_base_head, dev_list)
 #define for_each_netdev_continue(net, d)                \
                 list_for_each_entry_continue(d, &(net)->dev_base_head, dev_list)
 #define for_each_netdev_continue_rcu(net, d)            \
         list_for_each_entry_continue_rcu(d, &(net)->dev_base_head, dev_list)
 #define for_each_netdev_in_bond_rcu(bond, slave)        \
                 for_each_netdev_rcu(&init_net, slave)   \
                         if (netdev_master_upper_dev_get_rcu(slave) == (bond))
 #define net_device_entry(lh)    list_entry(lh, struct net_device, dev_list)
 
 static inline struct net_device *next_net_device(struct net_device *dev)
 {
         struct list_head *lh;
         struct net *net;
 
         net = dev_net(dev);
         lh = dev->dev_list.next;
         return lh == &net->dev_base_head ? NULL : net_device_entry(lh);
 }
 
 static inline struct net_device *next_net_device_rcu(struct net_device *dev)
 {
         struct list_head *lh;
         struct net *net;
 
         net = dev_net(dev);
         lh = rcu_dereference(list_next_rcu(&dev->dev_list));
         return lh == &net->dev_base_head ? NULL : net_device_entry(lh);
 }
 
 static inline struct net_device *first_net_device(struct net *net)
 {
         return list_empty(&net->dev_base_head) ? NULL :
                 net_device_entry(net->dev_base_head.next);
 }
 
 static inline struct net_device *first_net_device_rcu(struct net *net)
 {
         struct list_head *lh = rcu_dereference(list_next_rcu(&net->dev_base_head));
 
         return lh == &net->dev_base_head ? NULL : net_device_entry(lh);
 }
 
 int netdev_boot_setup_check(struct net_device *dev);
 unsigned long netdev_boot_base(const char *prefix, int unit);
 struct net_device *dev_getbyhwaddr_rcu(struct net *net, unsigned short type,
                                        const char *hwaddr);
 struct net_device *dev_getfirstbyhwtype(struct net *net, unsigned short type);
 struct net_device *__dev_getfirstbyhwtype(struct net *net, unsigned short type);
 void dev_add_pack(struct packet_type *pt);
 void dev_remove_pack(struct packet_type *pt);
 void __dev_remove_pack(struct packet_type *pt);
 void dev_add_offload(struct packet_offload *po);
 void dev_remove_offload(struct packet_offload *po);
 
 int dev_get_iflink(const struct net_device *dev);
 struct net_device *__dev_get_by_flags(struct net *net, unsigned short flags,
                                       unsigned short mask);
 struct net_device *dev_get_by_name(struct net *net, const char *name);
 struct net_device *dev_get_by_name_rcu(struct net *net, const char *name);
 struct net_device *__dev_get_by_name(struct net *net, const char *name);
 int dev_alloc_name(struct net_device *dev, const char *name);
 int dev_open(struct net_device *dev);
 int dev_close(struct net_device *dev);
 int dev_close_many(struct list_head *head, bool unlink);
 void dev_disable_lro(struct net_device *dev);
 int dev_loopback_xmit(struct sock *sk, struct sk_buff *newskb);
 int dev_queue_xmit_sk(struct sock *sk, struct sk_buff *skb);
 static inline int dev_queue_xmit(struct sk_buff *skb)
 {
         return dev_queue_xmit_sk(skb->sk, skb);
 }
 int dev_queue_xmit_accel(struct sk_buff *skb, void *accel_priv);
 int register_netdevice(struct net_device *dev);
 void unregister_netdevice_queue(struct net_device *dev, struct list_head *head);
 void unregister_netdevice_many(struct list_head *head);
 static inline void unregister_netdevice(struct net_device *dev)
 {
         unregister_netdevice_queue(dev, NULL);
 }
 
 int netdev_refcnt_read(const struct net_device *dev);
 void free_netdev(struct net_device *dev);
 void netdev_freemem(struct net_device *dev);
 void synchronize_net(void);
 int init_dummy_netdev(struct net_device *dev);
 
 DECLARE_PER_CPU(int, xmit_recursion);
 static inline int dev_recursion_level(void)
 {
         return this_cpu_read(xmit_recursion);
 }
 
 struct net_device *dev_get_by_index(struct net *net, int ifindex);
 struct net_device *__dev_get_by_index(struct net *net, int ifindex);
 struct net_device *dev_get_by_index_rcu(struct net *net, int ifindex);
 int netdev_get_name(struct net *net, char *name, int ifindex);
 int dev_restart(struct net_device *dev);
 int skb_gro_receive(struct sk_buff **head, struct sk_buff *skb);
 
 static inline unsigned int skb_gro_offset(const struct sk_buff *skb)
 {
         return NAPI_GRO_CB(skb)->data_offset;
 }
 
 static inline unsigned int skb_gro_len(const struct sk_buff *skb)
 {
         return skb->len - NAPI_GRO_CB(skb)->data_offset;
 }
 
 static inline void skb_gro_pull(struct sk_buff *skb, unsigned int len)
 {
         NAPI_GRO_CB(skb)->data_offset += len;
 }
 
 static inline void *skb_gro_header_fast(struct sk_buff *skb,
                                         unsigned int offset)
 {
         return NAPI_GRO_CB(skb)->frag0 + offset;
 }
 
 static inline int skb_gro_header_hard(struct sk_buff *skb, unsigned int hlen)
 {
         return NAPI_GRO_CB(skb)->frag0_len < hlen;
 }
 
 static inline void *skb_gro_header_slow(struct sk_buff *skb, unsigned int hlen,
                                         unsigned int offset)
 {
         if (!pskb_may_pull(skb, hlen))
                 return NULL;
 
         NAPI_GRO_CB(skb)->frag0 = NULL;
         NAPI_GRO_CB(skb)->frag0_len = 0;
         return skb->data + offset;
 }
 
 static inline void *skb_gro_network_header(struct sk_buff *skb)
 {
         return (NAPI_GRO_CB(skb)->frag0 ?: skb->data) +
                skb_network_offset(skb);
 }
 
 static inline void skb_gro_postpull_rcsum(struct sk_buff *skb,
                                         const void *start, unsigned int len)
 {
         if (NAPI_GRO_CB(skb)->csum_valid)
                 NAPI_GRO_CB(skb)->csum = csum_sub(NAPI_GRO_CB(skb)->csum,
                                                   csum_partial(start, len, 0));
 }
 
 /* GRO checksum functions. These are logical equivalents of the normal
  * checksum functions (in skbuff.h) except that they operate on the GRO
  * offsets and fields in sk_buff.
  */
 
 __sum16 __skb_gro_checksum_complete(struct sk_buff *skb);
 
 static inline bool skb_at_gro_remcsum_start(struct sk_buff *skb)
 {
         return (NAPI_GRO_CB(skb)->gro_remcsum_start - skb_headroom(skb) ==
                 skb_gro_offset(skb));
 }
 
 static inline bool __skb_gro_checksum_validate_needed(struct sk_buff *skb,
                                                       bool zero_okay,
                                                       __sum16 check)
 {
         return ((skb->ip_summed != CHECKSUM_PARTIAL ||
                 skb_checksum_start_offset(skb) <
                  skb_gro_offset(skb)) &&
                 !skb_at_gro_remcsum_start(skb) &&
                 NAPI_GRO_CB(skb)->csum_cnt == 0 &&
                 (!zero_okay || check));
 }
 
 static inline __sum16 __skb_gro_checksum_validate_complete(struct sk_buff *skb,
                                                            __wsum psum)
 {
         if (NAPI_GRO_CB(skb)->csum_valid &&
             !csum_fold(csum_add(psum, NAPI_GRO_CB(skb)->csum)))
                 return 0;
 
         NAPI_GRO_CB(skb)->csum = psum;
 
         return __skb_gro_checksum_complete(skb);
 }
 
 static inline void skb_gro_incr_csum_unnecessary(struct sk_buff *skb)
 {
         if (NAPI_GRO_CB(skb)->csum_cnt > 0) {
                 /* Consume a checksum from CHECKSUM_UNNECESSARY */
                 NAPI_GRO_CB(skb)->csum_cnt--;
         } else {
                 /* Update skb for CHECKSUM_UNNECESSARY and csum_level when we
                  * verified a new top level checksum or an encapsulated one
                  * during GRO. This saves work if we fallback to normal path.
                  */
                 __skb_incr_checksum_unnecessary(skb);
         }
 }
 
 #define __skb_gro_checksum_validate(skb, proto, zero_okay, check,       \
                                     compute_pseudo)                     \
 ({                                                                      \
         __sum16 __ret = 0;                                              \
         if (__skb_gro_checksum_validate_needed(skb, zero_okay, check))  \
                 __ret = __skb_gro_checksum_validate_complete(skb,       \
                                 compute_pseudo(skb, proto));            \
         if (__ret)                                                      \
                 __skb_mark_checksum_bad(skb);                           \
         else                                                            \
                 skb_gro_incr_csum_unnecessary(skb);                     \
         __ret;                                                          \
 })
 
 #define skb_gro_checksum_validate(skb, proto, compute_pseudo)           \
         __skb_gro_checksum_validate(skb, proto, false, 0, compute_pseudo)
 
 #define skb_gro_checksum_validate_zero_check(skb, proto, check,         \
                                              compute_pseudo)            \
         __skb_gro_checksum_validate(skb, proto, true, check, compute_pseudo)
 
 #define skb_gro_checksum_simple_validate(skb)                           \
         __skb_gro_checksum_validate(skb, 0, false, 0, null_compute_pseudo)
 
 static inline bool __skb_gro_checksum_convert_check(struct sk_buff *skb)
 {
         return (NAPI_GRO_CB(skb)->csum_cnt == 0 &&
                 !NAPI_GRO_CB(skb)->csum_valid);
 }
 
 static inline void __skb_gro_checksum_convert(struct sk_buff *skb,
                                               __sum16 check, __wsum pseudo)
 {
         NAPI_GRO_CB(skb)->csum = ~pseudo;
         NAPI_GRO_CB(skb)->csum_valid = 1;
 }
 
 #define skb_gro_checksum_try_convert(skb, proto, check, compute_pseudo) \
 do {                                                                    \
         if (__skb_gro_checksum_convert_check(skb))                      \
                 __skb_gro_checksum_convert(skb, check,                  \
                                            compute_pseudo(skb, proto)); \
 } while (0)
 
 struct gro_remcsum {
         int offset;
         __wsum delta;
 };
 
 static inline void skb_gro_remcsum_init(struct gro_remcsum *grc)
 {
         grc->offset = 0;
         grc->delta = 0;
 }
 
 static inline void skb_gro_remcsum_process(struct sk_buff *skb, void *ptr,
                                            int start, int offset,
                                            struct gro_remcsum *grc,
                                            bool nopartial)
 {
         __wsum delta;
 
         BUG_ON(!NAPI_GRO_CB(skb)->csum_valid);
 
         if (!nopartial) {
                 NAPI_GRO_CB(skb)->gro_remcsum_start =
                     ((unsigned char *)ptr + start) - skb->head;
                 return;
         }
 
         delta = remcsum_adjust(ptr, NAPI_GRO_CB(skb)->csum, start, offset);
 
         /* Adjust skb->csum since we changed the packet */
         NAPI_GRO_CB(skb)->csum = csum_add(NAPI_GRO_CB(skb)->csum, delta);
 
         grc->offset = (ptr + offset) - (void *)skb->head;
         grc->delta = delta;
 }
 
 static inline void skb_gro_remcsum_cleanup(struct sk_buff *skb,
                                            struct gro_remcsum *grc)
 {
         if (!grc->delta)
                 return;
 
         remcsum_unadjust((__sum16 *)(skb->head + grc->offset), grc->delta);
 }
 
 static inline int dev_hard_header(struct sk_buff *skb, struct net_device *dev,
                                   unsigned short type,
                                   const void *daddr, const void *saddr,
                                   unsigned int len)
 {
         if (!dev->header_ops || !dev->header_ops->create)
                 return 0;
 
         return dev->header_ops->create(skb, dev, type, daddr, saddr, len);
 }
 
 static inline int dev_parse_header(const struct sk_buff *skb,
                                    unsigned char *haddr)
 {
         const struct net_device *dev = skb->dev;
 
         if (!dev->header_ops || !dev->header_ops->parse)
                 return 0;
         return dev->header_ops->parse(skb, haddr);
 }
 
 typedef int gifconf_func_t(struct net_device * dev, char __user * bufptr, int len);
 int register_gifconf(unsigned int family, gifconf_func_t *gifconf);
 static inline int unregister_gifconf(unsigned int family)
 {
         return register_gifconf(family, NULL);
 }
 
 #ifdef CONFIG_NET_FLOW_LIMIT
 #define FLOW_LIMIT_HISTORY      (1 << 7)  /* must be ^2 and !overflow buckets */
 struct sd_flow_limit {
         u64                     count;
         unsigned int            num_buckets;
         unsigned int            history_head;
         u16                     history[FLOW_LIMIT_HISTORY];
         u8                      buckets[];
 };
 
 extern int netdev_flow_limit_table_len;
 #endif /* CONFIG_NET_FLOW_LIMIT */
 
 /*
  * Incoming packets are placed on per-cpu queues
  */
 struct softnet_data {
         struct list_head        poll_list;
         struct sk_buff_head     process_queue;
 
         /* stats */
         unsigned int            processed;
         unsigned int            time_squeeze;
         unsigned int            cpu_collision;
         unsigned int            received_rps;
 #ifdef CONFIG_RPS
         struct softnet_data     *rps_ipi_list;
 #endif
 #ifdef CONFIG_NET_FLOW_LIMIT
         struct sd_flow_limit __rcu *flow_limit;
 #endif
         struct Qdisc            *output_queue;
         struct Qdisc            **output_queue_tailp;
         struct sk_buff          *completion_queue;
 
 #ifdef CONFIG_RPS
         /* Elements below can be accessed between CPUs for RPS */
         struct call_single_data csd ____cacheline_aligned_in_smp;
         struct softnet_data     *rps_ipi_next;
         unsigned int            cpu;
         unsigned int            input_queue_head;
         unsigned int            input_queue_tail;
 #endif
         unsigned int            dropped;
         struct sk_buff_head     input_pkt_queue;
         struct napi_struct      backlog;
 
 };
 
 static inline void input_queue_head_incr(struct softnet_data *sd)
 {
 #ifdef CONFIG_RPS
         sd->input_queue_head++;
 #endif
 }
 
 static inline void input_queue_tail_incr_save(struct softnet_data *sd,
                                               unsigned int *qtail)
 {
 #ifdef CONFIG_RPS
         *qtail = ++sd->input_queue_tail;
 #endif
 }
 
 DECLARE_PER_CPU_ALIGNED(struct softnet_data, softnet_data);
 
 void __netif_schedule(struct Qdisc *q);
 void netif_schedule_queue(struct netdev_queue *txq);
 
 static inline void netif_tx_schedule_all(struct net_device *dev)
 {
         unsigned int i;
 
         for (i = 0; i < dev->num_tx_queues; i++)
                 netif_schedule_queue(netdev_get_tx_queue(dev, i));
 }
 
 static inline void netif_tx_start_queue(struct netdev_queue *dev_queue)
 {
         clear_bit(__QUEUE_STATE_DRV_XOFF, &dev_queue->state);
 }
 
 /**
  *      netif_start_queue - allow transmit
  *      @dev: network device
  *
  *      Allow upper layers to call the device hard_start_xmit routine.
  */
 static inline void netif_start_queue(struct net_device *dev)
 {
         netif_tx_start_queue(netdev_get_tx_queue(dev, 0));
 }
 
 static inline void netif_tx_start_all_queues(struct net_device *dev)
 {
         unsigned int i;
 
         for (i = 0; i < dev->num_tx_queues; i++) {
                 struct netdev_queue *txq = netdev_get_tx_queue(dev, i);
                 netif_tx_start_queue(txq);
         }
 }
 
 void netif_tx_wake_queue(struct netdev_queue *dev_queue);
 
 /**
  *      netif_wake_queue - restart transmit
  *      @dev: network device
  *
  *      Allow upper layers to call the device hard_start_xmit routine.
  *      Used for flow control when transmit resources are available.
  */
 static inline void netif_wake_queue(struct net_device *dev)
 {
         netif_tx_wake_queue(netdev_get_tx_queue(dev, 0));
 }
 
 static inline void netif_tx_wake_all_queues(struct net_device *dev)
 {
         unsigned int i;
 
         for (i = 0; i < dev->num_tx_queues; i++) {
                 struct netdev_queue *txq = netdev_get_tx_queue(dev, i);
                 netif_tx_wake_queue(txq);
         }
 }
 
 static inline void netif_tx_stop_queue(struct netdev_queue *dev_queue)
 {
         if (WARN_ON(!dev_queue)) {
                 pr_info("netif_stop_queue() cannot be called before register_netdev()\n");
                 return;
         }
         set_bit(__QUEUE_STATE_DRV_XOFF, &dev_queue->state);
 }
 
 /**
  *      netif_stop_queue - stop transmitted packets
  *      @dev: network device
  *
  *      Stop upper layers calling the device hard_start_xmit routine.
  *      Used for flow control when transmit resources are unavailable.
  */
 static inline void netif_stop_queue(struct net_device *dev)
 {
         netif_tx_stop_queue(netdev_get_tx_queue(dev, 0));
 }
 
 static inline void netif_tx_stop_all_queues(struct net_device *dev)
 {
         unsigned int i;
 
         for (i = 0; i < dev->num_tx_queues; i++) {
                 struct netdev_queue *txq = netdev_get_tx_queue(dev, i);
                 netif_tx_stop_queue(txq);
         }
 }
 
 static inline bool netif_tx_queue_stopped(const struct netdev_queue *dev_queue)
 {
         return test_bit(__QUEUE_STATE_DRV_XOFF, &dev_queue->state);
 }
 
 /**
  *      netif_queue_stopped - test if transmit queue is flowblocked
  *      @dev: network device
  *
  *      Test if transmit queue on device is currently unable to send.
  */
 static inline bool netif_queue_stopped(const struct net_device *dev)
 {
         return netif_tx_queue_stopped(netdev_get_tx_queue(dev, 0));
 }
 
 static inline bool netif_xmit_stopped(const struct netdev_queue *dev_queue)
 {
         return dev_queue->state & QUEUE_STATE_ANY_XOFF;
 }
 
 static inline bool
 netif_xmit_frozen_or_stopped(const struct netdev_queue *dev_queue)
 {
         return dev_queue->state & QUEUE_STATE_ANY_XOFF_OR_FROZEN;
 }
 
 static inline bool
 netif_xmit_frozen_or_drv_stopped(const struct netdev_queue *dev_queue)
 {
         return dev_queue->state & QUEUE_STATE_DRV_XOFF_OR_FROZEN;
 }
 
 /**
  *      netdev_txq_bql_enqueue_prefetchw - prefetch bql data for write
  *      @dev_queue: pointer to transmit queue
  *
  * BQL enabled drivers might use this helper in their ndo_start_xmit(),
  * to give appropriate hint to the cpu.
  */
 static inline void netdev_txq_bql_enqueue_prefetchw(struct netdev_queue *dev_queue)
 {
 #ifdef CONFIG_BQL
         prefetchw(&dev_queue->dql.num_queued);
 #endif
 }
 
 /**
  *      netdev_txq_bql_complete_prefetchw - prefetch bql data for write
  *      @dev_queue: pointer to transmit queue
  *
  * BQL enabled drivers might use this helper in their TX completion path,
  * to give appropriate hint to the cpu.
  */
 static inline void netdev_txq_bql_complete_prefetchw(struct netdev_queue *dev_queue)
 {
 #ifdef CONFIG_BQL
         prefetchw(&dev_queue->dql.limit);
 #endif
 }
 
 static inline void netdev_tx_sent_queue(struct netdev_queue *dev_queue,
                                         unsigned int bytes)
 {
 #ifdef CONFIG_BQL
         dql_queued(&dev_queue->dql, bytes);
 
         if (likely(dql_avail(&dev_queue->dql) >= 0))
                 return;
 
         set_bit(__QUEUE_STATE_STACK_XOFF, &dev_queue->state);
 
         /*
          * The XOFF flag must be set before checking the dql_avail below,
          * because in netdev_tx_completed_queue we update the dql_completed
          * before checking the XOFF flag.
          */
         smp_mb();
 
         /* check again in case another CPU has just made room avail */
         if (unlikely(dql_avail(&dev_queue->dql) >= 0))
                 clear_bit(__QUEUE_STATE_STACK_XOFF, &dev_queue->state);
 #endif
 }
 
 /**
  *      netdev_sent_queue - report the number of bytes queued to hardware
  *      @dev: network device
  *      @bytes: number of bytes queued to the hardware device queue
  *
  *      Report the number of bytes queued for sending/completion to the network
  *      device hardware queue. @bytes should be a good approximation and should
  *      exactly match netdev_completed_queue() @bytes
  */
 static inline void netdev_sent_queue(struct net_device *dev, unsigned int bytes)
 {
         netdev_tx_sent_queue(netdev_get_tx_queue(dev, 0), bytes);
 }
 
 static inline void netdev_tx_completed_queue(struct netdev_queue *dev_queue,
                                              unsigned int pkts, unsigned int bytes)
 {
 #ifdef CONFIG_BQL
         if (unlikely(!bytes))
                 return;
 
         dql_completed(&dev_queue->dql, bytes);
 
         /*
          * Without the memory barrier there is a small possiblity that
          * netdev_tx_sent_queue will miss the update and cause the queue to
          * be stopped forever
          */
         smp_mb();
 
         if (dql_avail(&dev_queue->dql) < 0)
                 return;
 
         if (test_and_clear_bit(__QUEUE_STATE_STACK_XOFF, &dev_queue->state))
                 netif_schedule_queue(dev_queue);
 #endif
 }
 
 /**
  *      netdev_completed_queue - report bytes and packets completed by device
  *      @dev: network device
  *      @pkts: actual number of packets sent over the medium
  *      @bytes: actual number of bytes sent over the medium
  *
  *      Report the number of bytes and packets transmitted by the network device
  *      hardware queue over the physical medium, @bytes must exactly match the
  *      @bytes amount passed to netdev_sent_queue()
  */
 static inline void netdev_completed_queue(struct net_device *dev,
                                           unsigned int pkts, unsigned int bytes)
 {
         netdev_tx_completed_queue(netdev_get_tx_queue(dev, 0), pkts, bytes);
 }
 
 static inline void netdev_tx_reset_queue(struct netdev_queue *q)
 {
 #ifdef CONFIG_BQL
         clear_bit(__QUEUE_STATE_STACK_XOFF, &q->state);
         dql_reset(&q->dql);
 #endif
 }
 
 /**
  *      netdev_reset_queue - reset the packets and bytes count of a network device
  *      @dev_queue: network device
  *
  *      Reset the bytes and packet count of a network device and clear the
  *      software flow control OFF bit for this network device
  */
 static inline void netdev_reset_queue(struct net_device *dev_queue)
 {
         netdev_tx_reset_queue(netdev_get_tx_queue(dev_queue, 0));
 }
 
 /**
  *      netdev_cap_txqueue - check if selected tx queue exceeds device queues
  *      @dev: network device
  *      @queue_index: given tx queue index
  *
  *      Returns 0 if given tx queue index >= number of device tx queues,
  *      otherwise returns the originally passed tx queue index.
  */
 static inline u16 netdev_cap_txqueue(struct net_device *dev, u16 queue_index)
 {
         if (unlikely(queue_index >= dev->real_num_tx_queues)) {
                 net_warn_ratelimited("%s selects TX queue %d, but real number of TX queues is %d\n",
                                      dev->name, queue_index,
                                      dev->real_num_tx_queues);
                 return 0;
         }
 
         return queue_index;
 }
 
 /**
  *      netif_running - test if up
  *      @dev: network device
  *
  *      Test if the device has been brought up.
  */
 static inline bool netif_running(const struct net_device *dev)
 {
         return test_bit(__LINK_STATE_START, &dev->state);
 }
 
 /*
  * Routines to manage the subqueues on a device.  We only need start
  * stop, and a check if it's stopped.  All other device management is
  * done at the overall netdevice level.
  * Also test the device if we're multiqueue.
  */
 
 /**
  *      netif_start_subqueue - allow sending packets on subqueue
  *      @dev: network device
  *      @queue_index: sub queue index
  *
  * Start individual transmit queue of a device with multiple transmit queues.
  */
 static inline void netif_start_subqueue(struct net_device *dev, u16 queue_index)
 {
         struct netdev_queue *txq = netdev_get_tx_queue(dev, queue_index);
 
         netif_tx_start_queue(txq);
 }
 
 /**
  *      netif_stop_subqueue - stop sending packets on subqueue
  *      @dev: network device
  *      @queue_index: sub queue index
  *
  * Stop individual transmit queue of a device with multiple transmit queues.
  */
 static inline void netif_stop_subqueue(struct net_device *dev, u16 queue_index)
 {
         struct netdev_queue *txq = netdev_get_tx_queue(dev, queue_index);
         netif_tx_stop_queue(txq);
 }
 
 /**
  *      netif_subqueue_stopped - test status of subqueue
  *      @dev: network device
  *      @queue_index: sub queue index
  *
  * Check individual transmit queue of a device with multiple transmit queues.
  */
 static inline bool __netif_subqueue_stopped(const struct net_device *dev,
                                             u16 queue_index)
 {
         struct netdev_queue *txq = netdev_get_tx_queue(dev, queue_index);
 
         return netif_tx_queue_stopped(txq);
 }
 
 static inline bool netif_subqueue_stopped(const struct net_device *dev,
                                           struct sk_buff *skb)
 {
         return __netif_subqueue_stopped(dev, skb_get_queue_mapping(skb));
 }
 
 void netif_wake_subqueue(struct net_device *dev, u16 queue_index);
 
 #ifdef CONFIG_XPS
 int netif_set_xps_queue(struct net_device *dev, const struct cpumask *mask,
                         u16 index);
 #else
 static inline int netif_set_xps_queue(struct net_device *dev,
                                       const struct cpumask *mask,
                                       u16 index)
 {
         return 0;
 }
 #endif
 
 /*
  * Returns a Tx hash for the given packet when dev->real_num_tx_queues is used
  * as a distribution range limit for the returned value.
  */
 static inline u16 skb_tx_hash(const struct net_device *dev,
                               struct sk_buff *skb)
 {
         return __skb_tx_hash(dev, skb, dev->real_num_tx_queues);
 }
 
 /**
  *      netif_is_multiqueue - test if device has multiple transmit queues
  *      @dev: network device
  *
  * Check if device has multiple transmit queues
  */
 static inline bool netif_is_multiqueue(const struct net_device *dev)
 {
         return dev->num_tx_queues > 1;
 }
 
 int netif_set_real_num_tx_queues(struct net_device *dev, unsigned int txq);
 
 #ifdef CONFIG_SYSFS
 int netif_set_real_num_rx_queues(struct net_device *dev, unsigned int rxq);
 #else
 static inline int netif_set_real_num_rx_queues(struct net_device *dev,
                                                 unsigned int rxq)
 {
         return 0;
 }
 #endif
 
 #ifdef CONFIG_SYSFS
 static inline unsigned int get_netdev_rx_queue_index(
                 struct netdev_rx_queue *queue)
 {
         struct net_device *dev = queue->dev;
         int index = queue - dev->_rx;
 
         BUG_ON(index >= dev->num_rx_queues);
         return index;
 }
 #endif
 
 #define DEFAULT_MAX_NUM_RSS_QUEUES      (8)
 int netif_get_num_default_rss_queues(void);
 
 enum skb_free_reason {
         SKB_REASON_CONSUMED,
         SKB_REASON_DROPPED,
 };
 
 void __dev_kfree_skb_irq(struct sk_buff *skb, enum skb_free_reason reason);
 void __dev_kfree_skb_any(struct sk_buff *skb, enum skb_free_reason reason);
 
 /*
  * It is not allowed to call kfree_skb() or consume_skb() from hardware
  * interrupt context or with hardware interrupts being disabled.
  * (in_irq() || irqs_disabled())
  *
  * We provide four helpers that can be used in following contexts :
  *
  * dev_kfree_skb_irq(skb) when caller drops a packet from irq context,
  *  replacing kfree_skb(skb)
  *
  * dev_consume_skb_irq(skb) when caller consumes a packet from irq context.
  *  Typically used in place of consume_skb(skb) in TX completion path
  *
  * dev_kfree_skb_any(skb) when caller doesn't know its current irq context,
  *  replacing kfree_skb(skb)
  *
  * dev_consume_skb_any(skb) when caller doesn't know its current irq context,
  *  and consumed a packet. Used in place of consume_skb(skb)
  */
 static inline void dev_kfree_skb_irq(struct sk_buff *skb)
 {
         __dev_kfree_skb_irq(skb, SKB_REASON_DROPPED);
 }
 
 static inline void dev_consume_skb_irq(struct sk_buff *skb)
 {
         __dev_kfree_skb_irq(skb, SKB_REASON_CONSUMED);
 }
 
 static inline void dev_kfree_skb_any(struct sk_buff *skb)
 {
         __dev_kfree_skb_any(skb, SKB_REASON_DROPPED);
 }
 
 static inline void dev_consume_skb_any(struct sk_buff *skb)
 {
         __dev_kfree_skb_any(skb, SKB_REASON_CONSUMED);
 }
 
 int netif_rx(struct sk_buff *skb);
 int netif_rx_ni(struct sk_buff *skb);
 int netif_receive_skb_sk(struct sock *sk, struct sk_buff *skb);
 static inline int netif_receive_skb(struct sk_buff *skb)
 {
         return netif_receive_skb_sk(skb->sk, skb);
 }
 gro_result_t napi_gro_receive(struct napi_struct *napi, struct sk_buff *skb);
 void napi_gro_flush(struct napi_struct *napi, bool flush_old);
 struct sk_buff *napi_get_frags(struct napi_struct *napi);
 gro_result_t napi_gro_frags(struct napi_struct *napi);
 struct packet_offload *gro_find_receive_by_type(__be16 type);
 struct packet_offload *gro_find_complete_by_type(__be16 type);
 
 static inline void napi_free_frags(struct napi_struct *napi)
 {
         kfree_skb(napi->skb);
         napi->skb = NULL;
 }
 
 int netdev_rx_handler_register(struct net_device *dev,
                                rx_handler_func_t *rx_handler,
                                void *rx_handler_data);
 void netdev_rx_handler_unregister(struct net_device *dev);
 
 bool dev_valid_name(const char *name);
 int dev_ioctl(struct net *net, unsigned int cmd, void __user *);
 int dev_ethtool(struct net *net, struct ifreq *);
 unsigned int dev_get_flags(const struct net_device *);
 int __dev_change_flags(struct net_device *, unsigned int flags);
 int dev_change_flags(struct net_device *, unsigned int);
 void __dev_notify_flags(struct net_device *, unsigned int old_flags,
                         unsigned int gchanges);
 int dev_change_name(struct net_device *, const char *);
 int dev_set_alias(struct net_device *, const char *, size_t);
 int dev_change_net_namespace(struct net_device *, struct net *, const char *);
 int dev_set_mtu(struct net_device *, int);
 void dev_set_group(struct net_device *, int);
 int dev_set_mac_address(struct net_device *, struct sockaddr *);
 int dev_change_carrier(struct net_device *, bool new_carrier);
 int dev_get_phys_port_id(struct net_device *dev,
                          struct netdev_phys_item_id *ppid);
 int dev_get_phys_port_name(struct net_device *dev,
                            char *name, size_t len);
 struct sk_buff *validate_xmit_skb_list(struct sk_buff *skb, struct net_device *dev);
 struct sk_buff *dev_hard_start_xmit(struct sk_buff *skb, struct net_device *dev,
                                     struct netdev_queue *txq, int *ret);
 int __dev_forward_skb(struct net_device *dev, struct sk_buff *skb);
 int dev_forward_skb(struct net_device *dev, struct sk_buff *skb);
 bool is_skb_forwardable(struct net_device *dev, struct sk_buff *skb);
 
 extern int              netdev_budget;
 
 /* Called by rtnetlink.c:rtnl_unlock() */
 void netdev_run_todo(void);
 
 /**
  *      dev_put - release reference to device
  *      @dev: network device
  *
  * Release reference to device to allow it to be freed.
  */
 static inline void dev_put(struct net_device *dev)
 {
         this_cpu_dec(*dev->pcpu_refcnt);
 }
 
 /**
  *      dev_hold - get reference to device
  *      @dev: network device
  *
  * Hold reference to device to keep it from being freed.
  */
 static inline void dev_hold(struct net_device *dev)
 {
         this_cpu_inc(*dev->pcpu_refcnt);
 }
 
 /* Carrier loss detection, dial on demand. The functions netif_carrier_on
  * and _off may be called from IRQ context, but it is caller
  * who is responsible for serialization of these calls.
  *
  * The name carrier is inappropriate, these functions should really be
  * called netif_lowerlayer_*() because they represent the state of any
  * kind of lower layer not just hardware media.
  */
 
 void linkwatch_init_dev(struct net_device *dev);
 void linkwatch_fire_event(struct net_device *dev);
 void linkwatch_forget_dev(struct net_device *dev);
 
 /**
  *      netif_carrier_ok - test if carrier present
  *      @dev: network device
  *
  * Check if carrier is present on device
  */
 static inline bool netif_carrier_ok(const struct net_device *dev)
 {
         return !test_bit(__LINK_STATE_NOCARRIER, &dev->state);
 }
 
 unsigned long dev_trans_start(struct net_device *dev);
 
 void __netdev_watchdog_up(struct net_device *dev);
 
 void netif_carrier_on(struct net_device *dev);
 
 void netif_carrier_off(struct net_device *dev);
 
 /**
  *      netif_dormant_on - mark device as dormant.
  *      @dev: network device
  *
  * Mark device as dormant (as per RFC2863).
  *
  * The dormant state indicates that the relevant interface is not
  * actually in a condition to pass packets (i.e., it is not 'up') but is
  * in a "pending" state, waiting for some external event.  For "on-
  * demand" interfaces, this new state identifies the situation where the
  * interface is waiting for events to place it in the up state.
  *
  */
 static inline void netif_dormant_on(struct net_device *dev)
 {
         if (!test_and_set_bit(__LINK_STATE_DORMANT, &dev->state))
                 linkwatch_fire_event(dev);
 }
 
 /**
  *      netif_dormant_off - set device as not dormant.
  *      @dev: network device
  *
  * Device is not in dormant state.
  */
 static inline void netif_dormant_off(struct net_device *dev)
 {
         if (test_and_clear_bit(__LINK_STATE_DORMANT, &dev->state))
                 linkwatch_fire_event(dev);
 }
 
 /**
  *      netif_dormant - test if carrier present
  *      @dev: network device
  *
  * Check if carrier is present on device
  */
 static inline bool netif_dormant(const struct net_device *dev)
 {
         return test_bit(__LINK_STATE_DORMANT, &dev->state);
 }
 
 
 /**
  *      netif_oper_up - test if device is operational
  *      @dev: network device
  *
  * Check if carrier is operational
  */
 static inline bool netif_oper_up(const struct net_device *dev)
 {
         return (dev->operstate == IF_OPER_UP ||
                 dev->operstate == IF_OPER_UNKNOWN /* backward compat */);
 }
 
 /**
  *      netif_device_present - is device available or removed
  *      @dev: network device
  *
  * Check if device has not been removed from system.
  */
 static inline bool netif_device_present(struct net_device *dev)
 {
         return test_bit(__LINK_STATE_PRESENT, &dev->state);
 }
 
 void netif_device_detach(struct net_device *dev);
 
 void netif_device_attach(struct net_device *dev);
 
 /*
  * Network interface message level settings
  */
 
 enum {
         NETIF_MSG_DRV           = 0x0001,
         NETIF_MSG_PROBE         = 0x0002,
         NETIF_MSG_LINK          = 0x0004,
         NETIF_MSG_TIMER         = 0x0008,
         NETIF_MSG_IFDOWN        = 0x0010,
         NETIF_MSG_IFUP          = 0x0020,
         NETIF_MSG_RX_ERR        = 0x0040,
         NETIF_MSG_TX_ERR        = 0x0080,
         NETIF_MSG_TX_QUEUED     = 0x0100,
         NETIF_MSG_INTR          = 0x0200,
         NETIF_MSG_TX_DONE       = 0x0400,
         NETIF_MSG_RX_STATUS     = 0x0800,
         NETIF_MSG_PKTDATA       = 0x1000,
         NETIF_MSG_HW            = 0x2000,
         NETIF_MSG_WOL           = 0x4000,
 };
 
 #define netif_msg_drv(p)        ((p)->msg_enable & NETIF_MSG_DRV)
 #define netif_msg_probe(p)      ((p)->msg_enable & NETIF_MSG_PROBE)
 #define netif_msg_link(p)       ((p)->msg_enable & NETIF_MSG_LINK)
 #define netif_msg_timer(p)      ((p)->msg_enable & NETIF_MSG_TIMER)
 #define netif_msg_ifdown(p)     ((p)->msg_enable & NETIF_MSG_IFDOWN)
 #define netif_msg_ifup(p)       ((p)->msg_enable & NETIF_MSG_IFUP)
 #define netif_msg_rx_err(p)     ((p)->msg_enable & NETIF_MSG_RX_ERR)
 #define netif_msg_tx_err(p)     ((p)->msg_enable & NETIF_MSG_TX_ERR)
 #define netif_msg_tx_queued(p)  ((p)->msg_enable & NETIF_MSG_TX_QUEUED)
 #define netif_msg_intr(p)       ((p)->msg_enable & NETIF_MSG_INTR)
 #define netif_msg_tx_done(p)    ((p)->msg_enable & NETIF_MSG_TX_DONE)
 #define netif_msg_rx_status(p)  ((p)->msg_enable & NETIF_MSG_RX_STATUS)
 #define netif_msg_pktdata(p)    ((p)->msg_enable & NETIF_MSG_PKTDATA)
 #define netif_msg_hw(p)         ((p)->msg_enable & NETIF_MSG_HW)
 #define netif_msg_wol(p)        ((p)->msg_enable & NETIF_MSG_WOL)
 
 static inline u32 netif_msg_init(int debug_value, int default_msg_enable_bits)
 {
         /* use default */
         if (debug_value < 0 || debug_value >= (sizeof(u32) * 8))
                 return default_msg_enable_bits;
         if (debug_value == 0)   /* no output */
                 return 0;
         /* set low N bits */
         return (1 << debug_value) - 1;
 }
 
 static inline void __netif_tx_lock(struct netdev_queue *txq, int cpu)
 {
         spin_lock(&txq->_xmit_lock);
         txq->xmit_lock_owner = cpu;
 }
 
 static inline void __netif_tx_lock_bh(struct netdev_queue *txq)
 {
         spin_lock_bh(&txq->_xmit_lock);
         txq->xmit_lock_owner = smp_processor_id();
 }
 
 static inline bool __netif_tx_trylock(struct netdev_queue *txq)
 {
         bool ok = spin_trylock(&txq->_xmit_lock);
         if (likely(ok))
                 txq->xmit_lock_owner = smp_processor_id();
         return ok;
 }
 
 static inline void __netif_tx_unlock(struct netdev_queue *txq)
 {
         txq->xmit_lock_owner = -1;
         spin_unlock(&txq->_xmit_lock);
 }
 
 static inline void __netif_tx_unlock_bh(struct netdev_queue *txq)
 {
         txq->xmit_lock_owner = -1;
         spin_unlock_bh(&txq->_xmit_lock);
 }
 
 static inline void txq_trans_update(struct netdev_queue *txq)
 {
         if (txq->xmit_lock_owner != -1)
                 txq->trans_start = jiffies;
 }
 
 /**
  *      netif_tx_lock - grab network device transmit lock
  *      @dev: network device
  *
  * Get network device transmit lock
  */
 static inline void netif_tx_lock(struct net_device *dev)
 {
         unsigned int i;
         int cpu;
 
         spin_lock(&dev->tx_global_lock);
         cpu = smp_processor_id();
         for (i = 0; i < dev->num_tx_queues; i++) {
                 struct netdev_queue *txq = netdev_get_tx_queue(dev, i);
 
                 /* We are the only thread of execution doing a
                  * freeze, but we have to grab the _xmit_lock in
                  * order to synchronize with threads which are in
                  * the ->hard_start_xmit() handler and already
                  * checked the frozen bit.
                  */
                 __netif_tx_lock(txq, cpu);
                 set_bit(__QUEUE_STATE_FROZEN, &txq->state);
                 __netif_tx_unlock(txq);
         }
 }
 
 static inline void netif_tx_lock_bh(struct net_device *dev)
 {
         local_bh_disable();
         netif_tx_lock(dev);
 }
 
 static inline void netif_tx_unlock(struct net_device *dev)
 {
         unsigned int i;
 
         for (i = 0; i < dev->num_tx_queues; i++) {
                 struct netdev_queue *txq = netdev_get_tx_queue(dev, i);
 
                 /* No need to grab the _xmit_lock here.  If the
                  * queue is not stopped for another reason, we
                  * force a schedule.
                  */
                 clear_bit(__QUEUE_STATE_FROZEN, &txq->state);
                 netif_schedule_queue(txq);
         }
         spin_unlock(&dev->tx_global_lock);
 }
 
 static inline void netif_tx_unlock_bh(struct net_device *dev)
 {
         netif_tx_unlock(dev);
         local_bh_enable();
 }
 
 #define HARD_TX_LOCK(dev, txq, cpu) {                   \
         if ((dev->features & NETIF_F_LLTX) == 0) {      \
                 __netif_tx_lock(txq, cpu);              \
         }                                               \
 }
 
 #define HARD_TX_TRYLOCK(dev, txq)                       \
         (((dev->features & NETIF_F_LLTX) == 0) ?        \
                 __netif_tx_trylock(txq) :               \
                 true )
 
 #define HARD_TX_UNLOCK(dev, txq) {                      \
         if ((dev->features & NETIF_F_LLTX) == 0) {      \
                 __netif_tx_unlock(txq);                 \
         }                                               \
 }
 
 static inline void netif_tx_disable(struct net_device *dev)
 {
         unsigned int i;
         int cpu;
 
         local_bh_disable();
         cpu = smp_processor_id();
         for (i = 0; i < dev->num_tx_queues; i++) {
                 struct netdev_queue *txq = netdev_get_tx_queue(dev, i);
 
                 __netif_tx_lock(txq, cpu);
                 netif_tx_stop_queue(txq);
                 __netif_tx_unlock(txq);
         }
         local_bh_enable();
 }
 
 static inline void netif_addr_lock(struct net_device *dev)
 {
         spin_lock(&dev->addr_list_lock);
 }
 
 static inline void netif_addr_lock_nested(struct net_device *dev)
 {
         int subclass = SINGLE_DEPTH_NESTING;
 
         if (dev->netdev_ops->ndo_get_lock_subclass)
                 subclass = dev->netdev_ops->ndo_get_lock_subclass(dev);
 
         spin_lock_nested(&dev->addr_list_lock, subclass);
 }
 
 static inline void netif_addr_lock_bh(struct net_device *dev)
 {
         spin_lock_bh(&dev->addr_list_lock);
 }
 
 static inline void netif_addr_unlock(struct net_device *dev)
 {
         spin_unlock(&dev->addr_list_lock);
 }
 
 static inline void netif_addr_unlock_bh(struct net_device *dev)
 {
         spin_unlock_bh(&dev->addr_list_lock);
 }
 
 /*
  * dev_addrs walker. Should be used only for read access. Call with
  * rcu_read_lock held.
  */
 #define for_each_dev_addr(dev, ha) \
                 list_for_each_entry_rcu(ha, &dev->dev_addrs.list, list)
 
 /* These functions live elsewhere (drivers/net/net_init.c, but related) */
 
 void ether_setup(struct net_device *dev);
 
 /* Support for loadable net-drivers */
 struct net_device *alloc_netdev_mqs(int sizeof_priv, const char *name,
                                     unsigned char name_assign_type,
                                     void (*setup)(struct net_device *),
                                     unsigned int txqs, unsigned int rxqs);
 #define alloc_netdev(sizeof_priv, name, name_assign_type, setup) \
         alloc_netdev_mqs(sizeof_priv, name, name_assign_type, setup, 1, 1)
 
 #define alloc_netdev_mq(sizeof_priv, name, name_assign_type, setup, count) \
         alloc_netdev_mqs(sizeof_priv, name, name_assign_type, setup, count, \
                          count)
 
 int register_netdev(struct net_device *dev);
 void unregister_netdev(struct net_device *dev);
 
 /* General hardware address lists handling functions */
 int __hw_addr_sync(struct netdev_hw_addr_list *to_list,
                    struct netdev_hw_addr_list *from_list, int addr_len);
 void __hw_addr_unsync(struct netdev_hw_addr_list *to_list,
                       struct netdev_hw_addr_list *from_list, int addr_len);
 int __hw_addr_sync_dev(struct netdev_hw_addr_list *list,
                        struct net_device *dev,
                        int (*sync)(struct net_device *, const unsigned char *),
                        int (*unsync)(struct net_device *,
                                      const unsigned char *));
 void __hw_addr_unsync_dev(struct netdev_hw_addr_list *list,
                           struct net_device *dev,
                           int (*unsync)(struct net_device *,
                                         const unsigned char *));
 void __hw_addr_init(struct netdev_hw_addr_list *list);
 
 /* Functions used for device addresses handling */
 int dev_addr_add(struct net_device *dev, const unsigned char *addr,
                  unsigned char addr_type);
 int dev_addr_del(struct net_device *dev, const unsigned char *addr,
                  unsigned char addr_type);
 void dev_addr_flush(struct net_device *dev);
 int dev_addr_init(struct net_device *dev);
 
 /* Functions used for unicast addresses handling */
 int dev_uc_add(struct net_device *dev, const unsigned char *addr);
 int dev_uc_add_excl(struct net_device *dev, const unsigned char *addr);
 int dev_uc_del(struct net_device *dev, const unsigned char *addr);
 int dev_uc_sync(struct net_device *to, struct net_device *from);
 int dev_uc_sync_multiple(struct net_device *to, struct net_device *from);
 void dev_uc_unsync(struct net_device *to, struct net_device *from);
 void dev_uc_flush(struct net_device *dev);
 void dev_uc_init(struct net_device *dev);
 
 /**
  *  __dev_uc_sync - Synchonize device's unicast list
  *  @dev:  device to sync
  *  @sync: function to call if address should be added
  *  @unsync: function to call if address should be removed
  *
  *  Add newly added addresses to the interface, and release
  *  addresses that have been deleted.
  **/
 static inline int __dev_uc_sync(struct net_device *dev,
                                 int (*sync)(struct net_device *,
                                             const unsigned char *),
                                 int (*unsync)(struct net_device *,
                                               const unsigned char *))
 {
         return __hw_addr_sync_dev(&dev->uc, dev, sync, unsync);
 }
 
 /**
  *  __dev_uc_unsync - Remove synchronized addresses from device
  *  @dev:  device to sync
  *  @unsync: function to call if address should be removed
  *
  *  Remove all addresses that were added to the device by dev_uc_sync().
  **/
 static inline void __dev_uc_unsync(struct net_device *dev,
                                    int (*unsync)(struct net_device *,
                                                  const unsigned char *))
 {
         __hw_addr_unsync_dev(&dev->uc, dev, unsync);
 }
 
 /* Functions used for multicast addresses handling */
 int dev_mc_add(struct net_device *dev, const unsigned char *addr);
 int dev_mc_add_global(struct net_device *dev, const unsigned char *addr);
 int dev_mc_add_excl(struct net_device *dev, const unsigned char *addr);
 int dev_mc_del(struct net_device *dev, const unsigned char *addr);
 int dev_mc_del_global(struct net_device *dev, const unsigned char *addr);
 int dev_mc_sync(struct net_device *to, struct net_device *from);
 int dev_mc_sync_multiple(struct net_device *to, struct net_device *from);
 void dev_mc_unsync(struct net_device *to, struct net_device *from);
 void dev_mc_flush(struct net_device *dev);
 void dev_mc_init(struct net_device *dev);
 
 /**
  *  __dev_mc_sync - Synchonize device's multicast list
  *  @dev:  device to sync
  *  @sync: function to call if address should be added
  *  @unsync: function to call if address should be removed
  *
  *  Add newly added addresses to the interface, and release
  *  addresses that have been deleted.
  **/
 static inline int __dev_mc_sync(struct net_device *dev,
                                 int (*sync)(struct net_device *,
                                             const unsigned char *),
                                 int (*unsync)(struct net_device *,
                                               const unsigned char *))
 {
         return __hw_addr_sync_dev(&dev->mc, dev, sync, unsync);
 }
 
 /**
  *  __dev_mc_unsync - Remove synchronized addresses from device
  *  @dev:  device to sync
  *  @unsync: function to call if address should be removed
  *
  *  Remove all addresses that were added to the device by dev_mc_sync().
  **/
 static inline void __dev_mc_unsync(struct net_device *dev,
                                    int (*unsync)(struct net_device *,
                                                  const unsigned char *))
 {
         __hw_addr_unsync_dev(&dev->mc, dev, unsync);
 }
 
 /* Functions used for secondary unicast and multicast support */
 void dev_set_rx_mode(struct net_device *dev);
 void __dev_set_rx_mode(struct net_device *dev);
 int dev_set_promiscuity(struct net_device *dev, int inc);
 int dev_set_allmulti(struct net_device *dev, int inc);
 void netdev_state_change(struct net_device *dev);
 void netdev_notify_peers(struct net_device *dev);
 void netdev_features_change(struct net_device *dev);
 /* Load a device via the kmod */
 void dev_load(struct net *net, const char *name);
 struct rtnl_link_stats64 *dev_get_stats(struct net_device *dev,
                                         struct rtnl_link_stats64 *storage);
 void netdev_stats_to_stats64(struct rtnl_link_stats64 *stats64,
                              const struct net_device_stats *netdev_stats);
 
 extern int              netdev_max_backlog;
 extern int              netdev_tstamp_prequeue;
 extern int              weight_p;
 extern int              bpf_jit_enable;
 
 bool netdev_has_upper_dev(struct net_device *dev, struct net_device *upper_dev);
 struct net_device *netdev_upper_get_next_dev_rcu(struct net_device *dev,
                                                      struct list_head **iter);
 struct net_device *netdev_all_upper_get_next_dev_rcu(struct net_device *dev,
                                                      struct list_head **iter);
 
 /* iterate through upper list, must be called under RCU read lock */
 #define netdev_for_each_upper_dev_rcu(dev, updev, iter) \
         for (iter = &(dev)->adj_list.upper, \
              updev = netdev_upper_get_next_dev_rcu(dev, &(iter)); \
              updev; \
              updev = netdev_upper_get_next_dev_rcu(dev, &(iter)))
 
 /* iterate through upper list, must be called under RCU read lock */
 #define netdev_for_each_all_upper_dev_rcu(dev, updev, iter) \
         for (iter = &(dev)->all_adj_list.upper, \
              updev = netdev_all_upper_get_next_dev_rcu(dev, &(iter)); \
              updev; \
              updev = netdev_all_upper_get_next_dev_rcu(dev, &(iter)))
 
 void *netdev_lower_get_next_private(struct net_device *dev,
                                     struct list_head **iter);
 void *netdev_lower_get_next_private_rcu(struct net_device *dev,
                                         struct list_head **iter);
 
 #define netdev_for_each_lower_private(dev, priv, iter) \
         for (iter = (dev)->adj_list.lower.next, \
              priv = netdev_lower_get_next_private(dev, &(iter)); \
              priv; \
              priv = netdev_lower_get_next_private(dev, &(iter)))
 
 #define netdev_for_each_lower_private_rcu(dev, priv, iter) \
         for (iter = &(dev)->adj_list.lower, \
              priv = netdev_lower_get_next_private_rcu(dev, &(iter)); \
              priv; \
              priv = netdev_lower_get_next_private_rcu(dev, &(iter)))
 
 void *netdev_lower_get_next(struct net_device *dev,
                                 struct list_head **iter);
 #define netdev_for_each_lower_dev(dev, ldev, iter) \
         for (iter = &(dev)->adj_list.lower, \
              ldev = netdev_lower_get_next(dev, &(iter)); \
              ldev; \
              ldev = netdev_lower_get_next(dev, &(iter)))
 
 void *netdev_adjacent_get_private(struct list_head *adj_list);
 void *netdev_lower_get_first_private_rcu(struct net_device *dev);
 struct net_device *netdev_master_upper_dev_get(struct net_device *dev);
 struct net_device *netdev_master_upper_dev_get_rcu(struct net_device *dev);
 int netdev_upper_dev_link(struct net_device *dev, struct net_device *upper_dev);
 int netdev_master_upper_dev_link(struct net_device *dev,
                                  struct net_device *upper_dev);
 int netdev_master_upper_dev_link_private(struct net_device *dev,
                                          struct net_device *upper_dev,
                                          void *private);
 void netdev_upper_dev_unlink(struct net_device *dev,
                              struct net_device *upper_dev);
 void netdev_adjacent_rename_links(struct net_device *dev, char *oldname);
 void *netdev_lower_dev_get_private(struct net_device *dev,
                                    struct net_device *lower_dev);
 
 /* RSS keys are 40 or 52 bytes long */
 #define NETDEV_RSS_KEY_LEN 52
 extern u8 netdev_rss_key[NETDEV_RSS_KEY_LEN];
 void netdev_rss_key_fill(void *buffer, size_t len);
 
 int dev_get_nest_level(struct net_device *dev,
                        bool (*type_check)(struct net_device *dev));
 int skb_checksum_help(struct sk_buff *skb);
 struct sk_buff *__skb_gso_segment(struct sk_buff *skb,
                                   netdev_features_t features, bool tx_path);
 struct sk_buff *skb_mac_gso_segment(struct sk_buff *skb,
                                     netdev_features_t features);
 
 struct netdev_bonding_info {
         ifslave slave;
         ifbond  master;
 };
 
 struct netdev_notifier_bonding_info {
         struct netdev_notifier_info info; /* must be first */
         struct netdev_bonding_info  bonding_info;
 };
 
 void netdev_bonding_info_change(struct net_device *dev,
                                 struct netdev_bonding_info *bonding_info);
 
 static inline
 struct sk_buff *skb_gso_segment(struct sk_buff *skb, netdev_features_t features)
 {
         return __skb_gso_segment(skb, features, true);
 }
 __be16 skb_network_protocol(struct sk_buff *skb, int *depth);
 
 static inline bool can_checksum_protocol(netdev_features_t features,
                                          __be16 protocol)
 {
         return ((features & NETIF_F_GEN_CSUM) ||
                 ((features & NETIF_F_V4_CSUM) &&
                  protocol == htons(ETH_P_IP)) ||
                 ((features & NETIF_F_V6_CSUM) &&
                  protocol == htons(ETH_P_IPV6)) ||
                 ((features & NETIF_F_FCOE_CRC) &&
                  protocol == htons(ETH_P_FCOE)));
 }
 
 #ifdef CONFIG_BUG
 void netdev_rx_csum_fault(struct net_device *dev);
 #else
 static inline void netdev_rx_csum_fault(struct net_device *dev)
 {
 }
 #endif
 /* rx skb timestamps */
 void net_enable_timestamp(void);
 void net_disable_timestamp(void);
 
 #ifdef CONFIG_PROC_FS
 int __init dev_proc_init(void);
 #else
 #define dev_proc_init() 0
 #endif
 
 static inline netdev_tx_t __netdev_start_xmit(const struct net_device_ops *ops,
                                               struct sk_buff *skb, struct net_device *dev,
                                               bool more)
 {
         skb->xmit_more = more ? 1 : 0;
         return ops->ndo_start_xmit(skb, dev);
 }
 
 static inline netdev_tx_t netdev_start_xmit(struct sk_buff *skb, struct net_device *dev,
                                             struct netdev_queue *txq, bool more)
 {
         const struct net_device_ops *ops = dev->netdev_ops;
         int rc;
 
         rc = __netdev_start_xmit(ops, skb, dev, more);
         if (rc == NETDEV_TX_OK)
                 txq_trans_update(txq);
 
         return rc;
 }
 
 int netdev_class_create_file_ns(struct class_attribute *class_attr,
                                 const void *ns);
 void netdev_class_remove_file_ns(struct class_attribute *class_attr,
                                  const void *ns);
 
 static inline int netdev_class_create_file(struct class_attribute *class_attr)
 {
         return netdev_class_create_file_ns(class_attr, NULL);
 }
 
 static inline void netdev_class_remove_file(struct class_attribute *class_attr)
 {
         netdev_class_remove_file_ns(class_attr, NULL);
 }
 
 extern struct kobj_ns_type_operations net_ns_type_operations;
 
 const char *netdev_drivername(const struct net_device *dev);
 
 void linkwatch_run_queue(void);
 
 static inline netdev_features_t netdev_intersect_features(netdev_features_t f1,
                                                           netdev_features_t f2)
 {
         if (f1 & NETIF_F_GEN_CSUM)
                 f1 |= (NETIF_F_ALL_CSUM & ~NETIF_F_GEN_CSUM);
         if (f2 & NETIF_F_GEN_CSUM)
                 f2 |= (NETIF_F_ALL_CSUM & ~NETIF_F_GEN_CSUM);
         f1 &= f2;
         if (f1 & NETIF_F_GEN_CSUM)
                 f1 &= ~(NETIF_F_ALL_CSUM & ~NETIF_F_GEN_CSUM);
 
         return f1;
 }
 
 static inline netdev_features_t netdev_get_wanted_features(
         struct net_device *dev)
 {
         return (dev->features & ~dev->hw_features) | dev->wanted_features;
 }
 netdev_features_t netdev_increment_features(netdev_features_t all,
         netdev_features_t one, netdev_features_t mask);
 
 /* Allow TSO being used on stacked device :
  * Performing the GSO segmentation before last device
  * is a performance improvement.
  */
 static inline netdev_features_t netdev_add_tso_features(netdev_features_t features,
                                                         netdev_features_t mask)
 {
         return netdev_increment_features(features, NETIF_F_ALL_TSO, mask);
 }
 
 int __netdev_update_features(struct net_device *dev);
 void netdev_update_features(struct net_device *dev);
 void netdev_change_features(struct net_device *dev);
 
 void netif_stacked_transfer_operstate(const struct net_device *rootdev,
                                         struct net_device *dev);
 
 netdev_features_t passthru_features_check(struct sk_buff *skb,
                                           struct net_device *dev,
                                           netdev_features_t features);
 netdev_features_t netif_skb_features(struct sk_buff *skb);
 
 static inline bool net_gso_ok(netdev_features_t features, int gso_type)
 {
         netdev_features_t feature = gso_type << NETIF_F_GSO_SHIFT;
 
         /* check flags correspondence */
         BUILD_BUG_ON(SKB_GSO_TCPV4   != (NETIF_F_TSO >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_UDP     != (NETIF_F_UFO >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_DODGY   != (NETIF_F_GSO_ROBUST >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_TCP_ECN != (NETIF_F_TSO_ECN >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_TCPV6   != (NETIF_F_TSO6 >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_FCOE    != (NETIF_F_FSO >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_GRE     != (NETIF_F_GSO_GRE >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_GRE_CSUM != (NETIF_F_GSO_GRE_CSUM >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_IPIP    != (NETIF_F_GSO_IPIP >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_SIT     != (NETIF_F_GSO_SIT >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_UDP_TUNNEL != (NETIF_F_GSO_UDP_TUNNEL >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_UDP_TUNNEL_CSUM != (NETIF_F_GSO_UDP_TUNNEL_CSUM >> NETIF_F_GSO_SHIFT));
         BUILD_BUG_ON(SKB_GSO_TUNNEL_REMCSUM != (NETIF_F_GSO_TUNNEL_REMCSUM >> NETIF_F_GSO_SHIFT));
 
         return (features & feature) == feature;
 }
 
 static inline bool skb_gso_ok(struct sk_buff *skb, netdev_features_t features)
 {
         return net_gso_ok(features, skb_shinfo(skb)->gso_type) &&
                (!skb_has_frag_list(skb) || (features & NETIF_F_FRAGLIST));
 }
 
 static inline bool netif_needs_gso(struct sk_buff *skb,
                                    netdev_features_t features)
 {
         return skb_is_gso(skb) && (!skb_gso_ok(skb, features) ||
                 unlikely((skb->ip_summed != CHECKSUM_PARTIAL) &&
                          (skb->ip_summed != CHECKSUM_UNNECESSARY)));
 }
 
 static inline void netif_set_gso_max_size(struct net_device *dev,
                                           unsigned int size)
 {
         dev->gso_max_size = size;
 }
 
 static inline void skb_gso_error_unwind(struct sk_buff *skb, __be16 protocol,
                                         int pulled_hlen, u16 mac_offset,
                                         int mac_len)
 {
         skb->protocol = protocol;
         skb->encapsulation = 1;
         skb_push(skb, pulled_hlen);
         skb_reset_transport_header(skb);
         skb->mac_header = mac_offset;
         skb->network_header = skb->mac_header + mac_len;
         skb->mac_len = mac_len;
 }
 
 static inline bool netif_is_macvlan(struct net_device *dev)
 {
         return dev->priv_flags & IFF_MACVLAN;
 }
 
 static inline bool netif_is_macvlan_port(struct net_device *dev)
 {
         return dev->priv_flags & IFF_MACVLAN_PORT;
 }
 
 static inline bool netif_is_ipvlan(struct net_device *dev)
 {
         return dev->priv_flags & IFF_IPVLAN_SLAVE;
 }
 
 static inline bool netif_is_ipvlan_port(struct net_device *dev)
 {
         return dev->priv_flags & IFF_IPVLAN_MASTER;
 }
 
 static inline bool netif_is_bond_master(struct net_device *dev)
 {
         return dev->flags & IFF_MASTER && dev->priv_flags & IFF_BONDING;
 }
 
 static inline bool netif_is_bond_slave(struct net_device *dev)
 {
         return dev->flags & IFF_SLAVE && dev->priv_flags & IFF_BONDING;
 }
 
 static inline bool netif_supports_nofcs(struct net_device *dev)
 {
         return dev->priv_flags & IFF_SUPP_NOFCS;
 }
 
 /* This device needs to keep skb dst for qdisc enqueue or ndo_start_xmit() */
 static inline void netif_keep_dst(struct net_device *dev)
 {
         dev->priv_flags &= ~(IFF_XMIT_DST_RELEASE | IFF_XMIT_DST_RELEASE_PERM);
 }
 
 extern struct pernet_operations __net_initdata loopback_net_ops;
 
 /* Logging, debugging and troubleshooting/diagnostic helpers. */
 
 /* netdev_printk helpers, similar to dev_printk */
 
 static inline const char *netdev_name(const struct net_device *dev)
 {
         if (!dev->name[0] || strchr(dev->name, '%'))
                 return "(unnamed net_device)";
         return dev->name;
 }
 
 static inline const char *netdev_reg_state(const struct net_device *dev)
 {
         switch (dev->reg_state) {
         case NETREG_UNINITIALIZED: return " (uninitialized)";
         case NETREG_REGISTERED: return "";
         case NETREG_UNREGISTERING: return " (unregistering)";
         case NETREG_UNREGISTERED: return " (unregistered)";
         case NETREG_RELEASED: return " (released)";
         case NETREG_DUMMY: return " (dummy)";
         }
 
         WARN_ONCE(1, "%s: unknown reg_state %d\n", dev->name, dev->reg_state);
         return " (unknown)";
 }
 
 __printf(3, 4)
 void netdev_printk(const char *level, const struct net_device *dev,
                    const char *format, ...);
 __printf(2, 3)
 void netdev_emerg(const struct net_device *dev, const char *format, ...);
 __printf(2, 3)
 void netdev_alert(const struct net_device *dev, const char *format, ...);
 __printf(2, 3)
 void netdev_crit(const struct net_device *dev, const char *format, ...);
 __printf(2, 3)
 void netdev_err(const struct net_device *dev, const char *format, ...);
 __printf(2, 3)
 void netdev_warn(const struct net_device *dev, const char *format, ...);
 __printf(2, 3)
 void netdev_notice(const struct net_device *dev, const char *format, ...);
 __printf(2, 3)
 void netdev_info(const struct net_device *dev, const char *format, ...);
 
 #define MODULE_ALIAS_NETDEV(device) \
         MODULE_ALIAS("netdev-" device)
 
 #if defined(CONFIG_DYNAMIC_DEBUG)
 #define netdev_dbg(__dev, format, args...)                      \
 do {                                                            \
         dynamic_netdev_dbg(__dev, format, ##args);              \
 } while (0)
 #elif defined(DEBUG)
 #define netdev_dbg(__dev, format, args...)                      \
         netdev_printk(KERN_DEBUG, __dev, format, ##args)
 #else
 #define netdev_dbg(__dev, format, args...)                      \
 ({                                                              \
         if (0)                                                  \
                 netdev_printk(KERN_DEBUG, __dev, format, ##args); \
 })
 #endif
 
 #if defined(VERBOSE_DEBUG)
 #define netdev_vdbg     netdev_dbg
 #else
 
 #define netdev_vdbg(dev, format, args...)                       \
 ({                                                              \
         if (0)                                                  \
                 netdev_printk(KERN_DEBUG, dev, format, ##args); \
         0;                                                      \
 })
 #endif
 
 /*
  * netdev_WARN() acts like dev_printk(), but with the key difference
  * of using a WARN/WARN_ON to get the message out, including the
  * file/line information and a backtrace.
  */
 #define netdev_WARN(dev, format, args...)                       \
         WARN(1, "netdevice: %s%s\n" format, netdev_name(dev),   \
              netdev_reg_state(dev), ##args)
 
 /* netif printk helpers, similar to netdev_printk */
 
 #define netif_printk(priv, type, level, dev, fmt, args...)      \
 do {                                                            \
         if (netif_msg_##type(priv))                             \
                 netdev_printk(level, (dev), fmt, ##args);       \
 } while (0)
 
 #define netif_level(level, priv, type, dev, fmt, args...)       \
 do {                                                            \
         if (netif_msg_##type(priv))                             \
                 netdev_##level(dev, fmt, ##args);               \
 } while (0)
 
 #define netif_emerg(priv, type, dev, fmt, args...)              \
         netif_level(emerg, priv, type, dev, fmt, ##args)
 #define netif_alert(priv, type, dev, fmt, args...)              \
         netif_level(alert, priv, type, dev, fmt, ##args)
 #define netif_crit(priv, type, dev, fmt, args...)               \
         netif_level(crit, priv, type, dev, fmt, ##args)
 #define netif_err(priv, type, dev, fmt, args...)                \
         netif_level(err, priv, type, dev, fmt, ##args)
 #define netif_warn(priv, type, dev, fmt, args...)               \
         netif_level(warn, priv, type, dev, fmt, ##args)
 #define netif_notice(priv, type, dev, fmt, args...)             \
         netif_level(notice, priv, type, dev, fmt, ##args)
 #define netif_info(priv, type, dev, fmt, args...)               \
         netif_level(info, priv, type, dev, fmt, ##args)
 
 #if defined(CONFIG_DYNAMIC_DEBUG)
 #define netif_dbg(priv, type, netdev, format, args...)          \
 do {                                                            \
         if (netif_msg_##type(priv))                             \
                 dynamic_netdev_dbg(netdev, format, ##args);     \
 } while (0)
 #elif defined(DEBUG)
 #define netif_dbg(priv, type, dev, format, args...)             \
         netif_printk(priv, type, KERN_DEBUG, dev, format, ##args)
 #else
 #define netif_dbg(priv, type, dev, format, args...)                     \
 ({                                                                      \
         if (0)                                                          \
                 netif_printk(priv, type, KERN_DEBUG, dev, format, ##args); \
         0;                                                              \
 })
 #endif
 
 #if defined(VERBOSE_DEBUG)
 #define netif_vdbg      netif_dbg
 #else
 #define netif_vdbg(priv, type, dev, format, args...)            \
 ({                                                              \
         if (0)                                                  \
                 netif_printk(priv, type, KERN_DEBUG, dev, format, ##args); \
         0;                                                      \
 })
 #endif
 
 /*
  *      The list of packet types we will receive (as opposed to discard)
  *      and the routines to invoke.
  *
  *      Why 16. Because with 16 the only overlap we get on a hash of the
  *      low nibble of the protocol value is RARP/SNAP/X.25.
  *
  *      NOTE:  That is no longer true with the addition of VLAN tags.  Not
  *             sure which should go first, but I bet it won't make much
  *             difference if we are running VLANs.  The good news is that
  *             this protocol won't be in the list unless compiled in, so
  *             the average user (w/out VLANs) will not be adversely affected.
  *             --BLG
  *
  *              0800    IP
  *              8100    802.1Q VLAN
  *              0001    802.3
  *              0002    AX.25
  *              0004    802.2
  *              8035    RARP
  *              0005    SNAP
  *              0805    X.25
  *              0806    ARP
  *              8137    IPX
  *              0009    Localtalk
  *              86DD    IPv6
  */
 #define PTYPE_HASH_SIZE (16)
 #define PTYPE_HASH_MASK (PTYPE_HASH_SIZE - 1)
 
 #endif  /* _LINUX_NETDEVICE_H */
```


```
/*
 *      Linux/net/core/dev.c
 *
 *      NET3    Protocol independent device support routines.
 *
 *              This program is free software; you can redistribute it and/or
 *              modify it under the terms of the GNU General Public License
 *              as published by the Free Software Foundation; either version
 *              2 of the License, or (at your option) any later version.
 *
 *      Derived from the non IP parts of dev.c 1.0.19
 *              Authors:        Ross Biro
 *                              Fred N. van Kempen, <waltje@uWalt.NL.Mugnet.ORG>
 *                              Mark Evans, <evansmp@uhura.aston.ac.uk>
 *
 *      Additional Authors:
 *              Florian la Roche <rzsfl@rz.uni-sb.de>
 *              Alan Cox <gw4pts@gw4pts.ampr.org>
 *              David Hinds <dahinds@users.sourceforge.net>
 *              Alexey Kuznetsov <kuznet@ms2.inr.ac.ru>
 *              Adam Sulmicki <adam@cfar.umd.edu>
 *              Pekka Riikonen <priikone@poesidon.pspt.fi>
 *
 *      Changes:
 *              D.J. Barrow     :       Fixed bug where dev->refcnt gets set
 *                                      to 2 if register_netdev gets called
 *                                      before net_dev_init & also removed a
 *                                      few lines of code in the process.
 *              Alan Cox        :       device private ioctl copies fields back.
 *              Alan Cox        :       Transmit queue code does relevant
 *                                      stunts to keep the queue safe.
 *              Alan Cox        :       Fixed double lock.
 *              Alan Cox        :       Fixed promisc NULL pointer trap
 *              ????????        :       Support the full private ioctl range
 *              Alan Cox        :       Moved ioctl permission check into
 *                                      drivers
 *              Tim Kordas      :       SIOCADDMULTI/SIOCDELMULTI
 *              Alan Cox        :       100 backlog just doesn't cut it when
 *                                      you start doing multicast video 8)
 *              Alan Cox        :       Rewrote net_bh and list manager.
 *              Alan Cox        :       Fix ETH_P_ALL echoback lengths.
 *              Alan Cox        :       Took out transmit every packet pass
 *                                      Saved a few bytes in the ioctl handler
 *              Alan Cox        :       Network driver sets packet type before
 *                                      calling netif_rx. Saves a function
 *                                      call a packet.
 *              Alan Cox        :       Hashed net_bh()
 *              Richard Kooijman:       Timestamp fixes.
 *              Alan Cox        :       Wrong field in SIOCGIFDSTADDR
 *              Alan Cox        :       Device lock protection.
 *              Alan Cox        :       Fixed nasty side effect of device close
 *                                      changes.
 *              Rudi Cilibrasi  :       Pass the right thing to
 *                                      set_mac_address()
 *              Dave Miller     :       32bit quantity for the device lock to
 *                                      make it work out on a Sparc.
 *              Bjorn Ekwall    :       Added KERNELD hack.
 *              Alan Cox        :       Cleaned up the backlog initialise.
 *              Craig Metz      :       SIOCGIFCONF fix if space for under
 *                                      1 device.
 *          Thomas Bogendoerfer :       Return ENODEV for dev_open, if there
 *                                      is no device open function.
 *              Andi Kleen      :       Fix error reporting for SIOCGIFCONF
 *          Michael Chastain    :       Fix signed/unsigned for SIOCGIFCONF
 *              Cyrus Durgin    :       Cleaned for KMOD
 *              Adam Sulmicki   :       Bug Fix : Network Device Unload
 *                                      A network device unload needs to purge
 *                                      the backlog queue.
 *      Paul Rusty Russell      :       SIOCSIFNAME
 *              Pekka Riikonen  :       Netdev boot-time settings code
 *              Andrew Morton   :       Make unregister_netdevice wait
 *                                      indefinitely on dev->refcnt
 *              J Hadi Salim    :       - Backlog queue sampling
 *                                      - netif_rx() feedback
 */

#include <asm/uaccess.h>
#include <linux/bitops.h>
#include <linux/capability.h>
#include <linux/cpu.h>
#include <linux/types.h>
#include <linux/kernel.h>
#include <linux/hash.h>
#include <linux/slab.h>
#include <linux/sched.h>
#include <linux/mutex.h>
#include <linux/string.h>
#include <linux/mm.h>
#include <linux/socket.h>
#include <linux/sockios.h>
#include <linux/errno.h>
#include <linux/interrupt.h>
#include <linux/if_ether.h>
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/ethtool.h>
#include <linux/notifier.h>
#include <linux/skbuff.h>
#include <net/net_namespace.h>
#include <net/sock.h>
#include <linux/rtnetlink.h>
#include <linux/stat.h>
#include <net/dst.h>
#include <net/pkt_sched.h>
#include <net/checksum.h>
#include <net/xfrm.h>
#include <linux/highmem.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/netpoll.h>
#include <linux/rcupdate.h>
#include <linux/delay.h>
#include <net/iw_handler.h>
#include <asm/current.h>
#include <linux/audit.h>
#include <linux/dmaengine.h>
#include <linux/err.h>
#include <linux/ctype.h>
#include <linux/if_arp.h>
#include <linux/if_vlan.h>
#include <linux/ip.h>
#include <net/ip.h>
#include <net/mpls.h>
#include <linux/ipv6.h>
#include <linux/in.h>
#include <linux/jhash.h>
#include <linux/random.h>
#include <trace/events/napi.h>
#include <trace/events/net.h>
#include <trace/events/skb.h>
#include <linux/pci.h>
#include <linux/inetdevice.h>
#include <linux/cpu_rmap.h>
#include <linux/static_key.h>
#include <linux/hashtable.h>
#include <linux/vmalloc.h>
#include <linux/if_macvlan.h>
#include <linux/errqueue.h>
#include <linux/hrtimer.h>

#include "net-sysfs.h"

/* Instead of increasing this, you should create a hash table. */
#define MAX_GRO_SKBS 8

/* This should be increased if a protocol with a bigger head is added. */
#define GRO_MAX_HEAD (MAX_HEADER + 128)

static DEFINE_SPINLOCK(ptype_lock);
static DEFINE_SPINLOCK(offload_lock);
struct list_head ptype_base[PTYPE_HASH_SIZE] __read_mostly;
struct list_head ptype_all __read_mostly;       /* Taps */
static struct list_head offload_base __read_mostly;

static int netif_rx_internal(struct sk_buff *skb);
static int call_netdevice_notifiers_info(unsigned long val,
                                         struct net_device *dev,
                                         struct netdev_notifier_info *info);

/*
 * The @dev_base_head list is protected by @dev_base_lock and the rtnl
 * semaphore.
 *
 * Pure readers hold dev_base_lock for reading, or rcu_read_lock()
 *
 * Writers must hold the rtnl semaphore while they loop through the
 * dev_base_head list, and hold dev_base_lock for writing when they do the
 * actual updates.  This allows pure readers to access the list even
 * while a writer is preparing to update it.
 *
 * To put it another way, dev_base_lock is held for writing only to
 * protect against pure readers; the rtnl semaphore provides the
 * protection against other writers.
 *
 * See, for example usages, register_netdevice() and
 * unregister_netdevice(), which must be called with the rtnl
 * semaphore held.
 */
DEFINE_RWLOCK(dev_base_lock);
EXPORT_SYMBOL(dev_base_lock);

/* protects napi_hash addition/deletion and napi_gen_id */
static DEFINE_SPINLOCK(napi_hash_lock);

static unsigned int napi_gen_id;
static DEFINE_HASHTABLE(napi_hash, 8);

static seqcount_t devnet_rename_seq;

static inline void dev_base_seq_inc(struct net *net)
{
        while (++net->dev_base_seq == 0);
}

static inline struct hlist_head *dev_name_hash(struct net *net, const char *name)
{
        unsigned int hash = full_name_hash(name, strnlen(name, IFNAMSIZ));

        return &net->dev_name_head[hash_32(hash, NETDEV_HASHBITS)];
}

static inline struct hlist_head *dev_index_hash(struct net *net, int ifindex)
{
        return &net->dev_index_head[ifindex & (NETDEV_HASHENTRIES - 1)];
}

static inline void rps_lock(struct softnet_data *sd)
{
#ifdef CONFIG_RPS
        spin_lock(&sd->input_pkt_queue.lock);
#endif
}

static inline void rps_unlock(struct softnet_data *sd)
{
#ifdef CONFIG_RPS
        spin_unlock(&sd->input_pkt_queue.lock);
#endif
}

/* Device list insertion */
//将 dev->dev_list 增加到 dev->net->dev_base_head 链表中
//将 dev->nam_hlist 增加到 &dev->net->dev_name_head[hash_32(full_name_hash(dev->name, strnlen(dev->name, IFNAMSIZ)), NETDEV_HASHBITS)]
//将 dev->index_hlist 增加到 dev->net->dev_index_head[dev->ifindex & (NETDEV_HASHENTRIES - 1)] 中
//将 dev 加入如上散列表中, 当网络子系统高层的代码需要发送数据包的时候, 能通过这几个散列表找到特定的网络设备
static void list_netdevice(struct net_device *dev)
{
        struct net *net = dev_net(dev);

        ASSERT_RTNL();

        write_lock_bh(&dev_base_lock);
        list_add_tail_rcu(&dev->dev_list, &net->dev_base_head);
        hlist_add_head_rcu(&dev->name_hlist, dev_name_hash(net, dev->name));
        hlist_add_head_rcu(&dev->index_hlist,
                           dev_index_hash(net, dev->ifindex));
        write_unlock_bh(&dev_base_lock);

        dev_base_seq_inc(net);
}

/* Device list removal
 * caller must respect a RCU grace period before freeing/reusing dev
 */
static void unlist_netdevice(struct net_device *dev)
{
        ASSERT_RTNL();

        /* Unlink dev from the device chain */
        write_lock_bh(&dev_base_lock);
        list_del_rcu(&dev->dev_list);
        hlist_del_rcu(&dev->name_hlist);
        hlist_del_rcu(&dev->index_hlist);
        write_unlock_bh(&dev_base_lock);

        dev_base_seq_inc(dev_net(dev));
}

/*
 *      Our notifier list
 */

static RAW_NOTIFIER_HEAD(netdev_chain);

/*
 *      Device drivers call our routines to queue packets here. We empty the
 *      queue in the local softnet handler.
 */

DEFINE_PER_CPU_ALIGNED(struct softnet_data, softnet_data);
EXPORT_PER_CPU_SYMBOL(softnet_data);

#ifdef CONFIG_LOCKDEP
/*
 * register_netdevice() inits txq->_xmit_lock and sets lockdep class
 * according to dev->type
 */
static const unsigned short netdev_lock_type[] =
        {ARPHRD_NETROM, ARPHRD_ETHER, ARPHRD_EETHER, ARPHRD_AX25,
         ARPHRD_PRONET, ARPHRD_CHAOS, ARPHRD_IEEE802, ARPHRD_ARCNET,
         ARPHRD_APPLETLK, ARPHRD_DLCI, ARPHRD_ATM, ARPHRD_METRICOM,
         ARPHRD_IEEE1394, ARPHRD_EUI64, ARPHRD_INFINIBAND, ARPHRD_SLIP,
         ARPHRD_CSLIP, ARPHRD_SLIP6, ARPHRD_CSLIP6, ARPHRD_RSRVD,
         ARPHRD_ADAPT, ARPHRD_ROSE, ARPHRD_X25, ARPHRD_HWX25,
         ARPHRD_PPP, ARPHRD_CISCO, ARPHRD_LAPB, ARPHRD_DDCMP,
         ARPHRD_RAWHDLC, ARPHRD_TUNNEL, ARPHRD_TUNNEL6, ARPHRD_FRAD,
         ARPHRD_SKIP, ARPHRD_LOOPBACK, ARPHRD_LOCALTLK, ARPHRD_FDDI,
         ARPHRD_BIF, ARPHRD_SIT, ARPHRD_IPDDP, ARPHRD_IPGRE,
         ARPHRD_PIMREG, ARPHRD_HIPPI, ARPHRD_ASH, ARPHRD_ECONET,
         ARPHRD_IRDA, ARPHRD_FCPP, ARPHRD_FCAL, ARPHRD_FCPL,
         ARPHRD_FCFABRIC, ARPHRD_IEEE80211, ARPHRD_IEEE80211_PRISM,
         ARPHRD_IEEE80211_RADIOTAP, ARPHRD_PHONET, ARPHRD_PHONET_PIPE,
         ARPHRD_IEEE802154, ARPHRD_VOID, ARPHRD_NONE};

static const char *const netdev_lock_name[] =
        {"_xmit_NETROM", "_xmit_ETHER", "_xmit_EETHER", "_xmit_AX25",
         "_xmit_PRONET", "_xmit_CHAOS", "_xmit_IEEE802", "_xmit_ARCNET",
         "_xmit_APPLETLK", "_xmit_DLCI", "_xmit_ATM", "_xmit_METRICOM",
         "_xmit_IEEE1394", "_xmit_EUI64", "_xmit_INFINIBAND", "_xmit_SLIP",
         "_xmit_CSLIP", "_xmit_SLIP6", "_xmit_CSLIP6", "_xmit_RSRVD",
         "_xmit_ADAPT", "_xmit_ROSE", "_xmit_X25", "_xmit_HWX25",
         "_xmit_PPP", "_xmit_CISCO", "_xmit_LAPB", "_xmit_DDCMP",
         "_xmit_RAWHDLC", "_xmit_TUNNEL", "_xmit_TUNNEL6", "_xmit_FRAD",
         "_xmit_SKIP", "_xmit_LOOPBACK", "_xmit_LOCALTLK", "_xmit_FDDI",
         "_xmit_BIF", "_xmit_SIT", "_xmit_IPDDP", "_xmit_IPGRE",
         "_xmit_PIMREG", "_xmit_HIPPI", "_xmit_ASH", "_xmit_ECONET",
         "_xmit_IRDA", "_xmit_FCPP", "_xmit_FCAL", "_xmit_FCPL",
         "_xmit_FCFABRIC", "_xmit_IEEE80211", "_xmit_IEEE80211_PRISM",
         "_xmit_IEEE80211_RADIOTAP", "_xmit_PHONET", "_xmit_PHONET_PIPE",
         "_xmit_IEEE802154", "_xmit_VOID", "_xmit_NONE"};

static struct lock_class_key netdev_xmit_lock_key[ARRAY_SIZE(netdev_lock_type)];
static struct lock_class_key netdev_addr_lock_key[ARRAY_SIZE(netdev_lock_type)];

static inline unsigned short netdev_lock_pos(unsigned short dev_type)
{
        int i;

        for (i = 0; i < ARRAY_SIZE(netdev_lock_type); i++)
                if (netdev_lock_type[i] == dev_type)
                        return i;
        /* the last key is used by default */
        return ARRAY_SIZE(netdev_lock_type) - 1;
}

static inline void netdev_set_xmit_lockdep_class(spinlock_t *lock,
                                                 unsigned short dev_type)
{
        int i;

        i = netdev_lock_pos(dev_type);
        lockdep_set_class_and_name(lock, &netdev_xmit_lock_key[i],
                                   netdev_lock_name[i]);
}

static inline void netdev_set_addr_lockdep_class(struct net_device *dev)
{
        int i;

        i = netdev_lock_pos(dev->type);
        lockdep_set_class_and_name(&dev->addr_list_lock,
                                   &netdev_addr_lock_key[i],
                                   netdev_lock_name[i]);
}
#else
static inline void netdev_set_xmit_lockdep_class(spinlock_t *lock,
                                                 unsigned short dev_type)
{
}
static inline void netdev_set_addr_lockdep_class(struct net_device *dev)
{
}
#endif

/*******************************************************************************

                Protocol management and registration routines

*******************************************************************************/

/*
 *      Add a protocol ID to the list. Now that the input handler is
 *      smarter we can dispense with all the messy stuff that used to be
 *      here.
 *
 *      BEWARE!!! Protocol handlers, mangling input packets,
 *      MUST BE last in hash buckets and checking protocol handlers
 *      MUST start from promiscuous ptype_all chain in net_bh.
 *      It is true now, do not change it.
 *      Explanation follows: if protocol handler, mangling packet, will
 *      be the first on list, it is not able to sense, that packet
 *      is cloned and should be copied-on-write, so that it will
 *      change it and subsequent readers will get broken packet.
 *                                                      --ANK (980803)
 */

static inline struct list_head *ptype_head(const struct packet_type *pt)
{
        if (pt->type == htons(ETH_P_ALL))
                return pt->dev ? &pt->dev->ptype_all : &ptype_all;
        else
                return pt->dev ? &pt->dev->ptype_specific :
                                 &ptype_base[ntohs(pt->type) & PTYPE_HASH_MASK];
}

/**
 *      dev_add_pack - add packet handler
 *      @pt: packet type declaration
 *
 *      Add a protocol handler to the networking stack. The passed &packet_type
 *      is linked into kernel lists and may not be freed until it has been
 *      removed from the kernel lists.
 *
 *      This call does not sleep therefore it can not
 *      guarantee all CPU's that are in middle of receiving packets
 *      will see the new packet type (until the next received packet).
 */

void dev_add_pack(struct packet_type *pt)
{
        struct list_head *head = ptype_head(pt);

        spin_lock(&ptype_lock);
        list_add_rcu(&pt->list, head);
        spin_unlock(&ptype_lock);
}
EXPORT_SYMBOL(dev_add_pack);

/**
 *      __dev_remove_pack        - remove packet handler
 *      @pt: packet type declaration
 *
 *      Remove a protocol handler that was previously added to the kernel
 *      protocol handlers by dev_add_pack(). The passed &packet_type is removed
 *      from the kernel lists and can be freed or reused once this function
 *      returns.
 *
 *      The packet type might still be in use by receivers
 *      and must not be freed until after all the CPU's have gone
 *      through a quiescent state.
 */
void __dev_remove_pack(struct packet_type *pt)
{
        struct list_head *head = ptype_head(pt);
        struct packet_type *pt1;

        spin_lock(&ptype_lock);

        list_for_each_entry(pt1, head, list) {
                if (pt == pt1) {
                        list_del_rcu(&pt->list);
                        goto out;
                }
        }

        pr_warn("dev_remove_pack: %p not found\n", pt);
out:
        spin_unlock(&ptype_lock);
}
EXPORT_SYMBOL(__dev_remove_pack);

/**
 *      dev_remove_pack  - remove packet handler
 *      @pt: packet type declaration
 *
 *      Remove a protocol handler that was previously added to the kernel
 *      protocol handlers by dev_add_pack(). The passed &packet_type is removed
 *      from the kernel lists and can be freed or reused once this function
 *      returns.
 *
 *      This call sleeps to guarantee that no CPU is looking at the packet
 *      type after return.
 */
void dev_remove_pack(struct packet_type *pt)
{
        __dev_remove_pack(pt);

        synchronize_net();
}
EXPORT_SYMBOL(dev_remove_pack);


/**
 *      dev_add_offload - register offload handlers
 *      @po: protocol offload declaration
 *
 *      Add protocol offload handlers to the networking stack. The passed
 *      &proto_offload is linked into kernel lists and may not be freed until
 *      it has been removed from the kernel lists.
 *
 *      This call does not sleep therefore it can not
 *      guarantee all CPU's that are in middle of receiving packets
 *      will see the new offload handlers (until the next received packet).
 */
void dev_add_offload(struct packet_offload *po)
{
        struct list_head *head = &offload_base;

        spin_lock(&offload_lock);
        list_add_rcu(&po->list, head);
        spin_unlock(&offload_lock);
}
EXPORT_SYMBOL(dev_add_offload);

/**
 *      __dev_remove_offload     - remove offload handler
 *      @po: packet offload declaration
 *
 *      Remove a protocol offload handler that was previously added to the
 *      kernel offload handlers by dev_add_offload(). The passed &offload_type
 *      is removed from the kernel lists and can be freed or reused once this
 *      function returns.
 *
 *      The packet type might still be in use by receivers
 *      and must not be freed until after all the CPU's have gone
 *      through a quiescent state.
 */
static void __dev_remove_offload(struct packet_offload *po)
{
        struct list_head *head = &offload_base;
        struct packet_offload *po1;

        spin_lock(&offload_lock);

        list_for_each_entry(po1, head, list) {
                if (po == po1) {
                        list_del_rcu(&po->list);
                        goto out;
                }
        }

        pr_warn("dev_remove_offload: %p not found\n", po);
out:
        spin_unlock(&offload_lock);
}

/**
 *      dev_remove_offload       - remove packet offload handler
 *      @po: packet offload declaration
 *
 *      Remove a packet offload handler that was previously added to the kernel
 *      offload handlers by dev_add_offload(). The passed &offload_type is
 *      removed from the kernel lists and can be freed or reused once this
 *      function returns.
 *
 *      This call sleeps to guarantee that no CPU is looking at the packet
 *      type after return.
 */
void dev_remove_offload(struct packet_offload *po)
{
        __dev_remove_offload(po);

        synchronize_net();
}
EXPORT_SYMBOL(dev_remove_offload);

/******************************************************************************

                      Device Boot-time Settings Routines

*******************************************************************************/

/* Boot time configuration table */
static struct netdev_boot_setup dev_boot_setup[NETDEV_BOOT_SETUP_MAX];

/**
 *      netdev_boot_setup_add   - add new setup entry
 *      @name: name of the device
 *      @map: configured settings for the device
 *
 *      Adds new setup entry to the dev_boot_setup list.  The function
 *      returns 0 on error and 1 on success.  This is a generic routine to
 *      all netdevices.
 */
static int netdev_boot_setup_add(char *name, struct ifmap *map)
{
        struct netdev_boot_setup *s;
        int i;

        s = dev_boot_setup;
        for (i = 0; i < NETDEV_BOOT_SETUP_MAX; i++) {
                if (s[i].name[0] == '\0' || s[i].name[0] == ' ') {
                        memset(s[i].name, 0, sizeof(s[i].name));
                        strlcpy(s[i].name, name, IFNAMSIZ);
                        memcpy(&s[i].map, map, sizeof(s[i].map));
                        break;
                }
        }

        return i >= NETDEV_BOOT_SETUP_MAX ? 0 : 1;
}

/**
 *      netdev_boot_setup_check - check boot time settings
 *      @dev: the netdevice
 *
 *      Check boot time settings for the device.
 *      The found settings are set for the device to be used
 *      later in the device probing.
 *      Returns 0 if no settings found, 1 if they are.
 */
int netdev_boot_setup_check(struct net_device *dev)
{
        struct netdev_boot_setup *s = dev_boot_setup;
        int i;

        for (i = 0; i < NETDEV_BOOT_SETUP_MAX; i++) {
                if (s[i].name[0] != '\0' && s[i].name[0] != ' ' &&
                    !strcmp(dev->name, s[i].name)) {
                        dev->irq        = s[i].map.irq;
                        dev->base_addr  = s[i].map.base_addr;
                        dev->mem_start  = s[i].map.mem_start;
                        dev->mem_end    = s[i].map.mem_end;
                        return 1;
                }
        }
        return 0;
}
EXPORT_SYMBOL(netdev_boot_setup_check);


/**
 *      netdev_boot_base        - get address from boot time settings
 *      @prefix: prefix for network device
 *      @unit: id for network device
 *
 *      Check boot time settings for the base address of device.
 *      The found settings are set for the device to be used
 *      later in the device probing.
 *      Returns 0 if no settings found.
 */
unsigned long netdev_boot_base(const char *prefix, int unit)
{
        const struct netdev_boot_setup *s = dev_boot_setup;
        char name[IFNAMSIZ];
        int i;

        sprintf(name, "%s%d", prefix, unit);

        /*
         * If device already registered then return base of 1
         * to indicate not to probe for this interface
         */
        if (__dev_get_by_name(&init_net, name))
                return 1;

        for (i = 0; i < NETDEV_BOOT_SETUP_MAX; i++)
                if (!strcmp(name, s[i].name))
                        return s[i].map.base_addr;
        return 0;
}

/*
 * Saves at boot time configured settings for any netdevice.
 */
int __init netdev_boot_setup(char *str)
{
        int ints[5];
        struct ifmap map;

        str = get_options(str, ARRAY_SIZE(ints), ints);
        if (!str || !*str)
                return 0;

        /* Save settings */
        memset(&map, 0, sizeof(map));
        if (ints[0] > 0)
                map.irq = ints[1];
        if (ints[0] > 1)
                map.base_addr = ints[2];
        if (ints[0] > 2)
                map.mem_start = ints[3];
        if (ints[0] > 3)
                map.mem_end = ints[4];

        /* Add new entry to the list */
        return netdev_boot_setup_add(str, &map);
}

__setup("netdev=", netdev_boot_setup);

/*******************************************************************************

                            Device Interface Subroutines

*******************************************************************************/

/**
 *      dev_get_iflink  - get 'iflink' value of a interface
 *      @dev: targeted interface
 *
 *      Indicates the ifindex the interface is linked to.
 *      Physical interfaces have the same 'ifindex' and 'iflink' values.
 */

int dev_get_iflink(const struct net_device *dev)
{
        if (dev->netdev_ops && dev->netdev_ops->ndo_get_iflink)
                return dev->netdev_ops->ndo_get_iflink(dev);

        /* If dev->rtnl_link_ops is set, it's a virtual interface. */
        if (dev->rtnl_link_ops)
                return 0;

        return dev->ifindex;
}
EXPORT_SYMBOL(dev_get_iflink);

/**
 *      __dev_get_by_name       - find a device by its name
 *      @net: the applicable net namespace
 *      @name: name to find
 *
 *      Find an interface by name. Must be called under RTNL semaphore
 *      or @dev_base_lock. If the name is found a pointer to the device
 *      is returned. If the name is not found then %NULL is returned. The
 *      reference counters are not incremented so the caller must be
 *      careful with locks.
 */

struct net_device *__dev_get_by_name(struct net *net, const char *name)
{
        struct net_device *dev;
        struct hlist_head *head = dev_name_hash(net, name);

        hlist_for_each_entry(dev, head, name_hlist)
                if (!strncmp(dev->name, name, IFNAMSIZ))
                        return dev;

        return NULL;
}
EXPORT_SYMBOL(__dev_get_by_name);

/**
 *      dev_get_by_name_rcu     - find a device by its name
 *      @net: the applicable net namespace
 *      @name: name to find
 *
 *      Find an interface by name.
 *      If the name is found a pointer to the device is returned.
 *      If the name is not found then %NULL is returned.
 *      The reference counters are not incremented so the caller must be
 *      careful with locks. The caller must hold RCU lock.
 */

struct net_device *dev_get_by_name_rcu(struct net *net, const char *name)
{
        struct net_device *dev;
        struct hlist_head *head = dev_name_hash(net, name);

        hlist_for_each_entry_rcu(dev, head, name_hlist)
                if (!strncmp(dev->name, name, IFNAMSIZ))
                        return dev;

        return NULL;
}
EXPORT_SYMBOL(dev_get_by_name_rcu);

/**
 *      dev_get_by_name         - find a device by its name
 *      @net: the applicable net namespace
 *      @name: name to find
 *
 *      Find an interface by name. This can be called from any
 *      context and does its own locking. The returned handle has
 *      the usage count incremented and the caller must use dev_put() to
 *      release it when it is no longer needed. %NULL is returned if no
 *      matching device is found.
 */

struct net_device *dev_get_by_name(struct net *net, const char *name)
{
        struct net_device *dev;

        rcu_read_lock();
        dev = dev_get_by_name_rcu(net, name);
        if (dev)
                dev_hold(dev);
        rcu_read_unlock();
        return dev;
}
EXPORT_SYMBOL(dev_get_by_name);

/**
 *      __dev_get_by_index - find a device by its ifindex
 *      @net: the applicable net namespace
 *      @ifindex: index of device
 *
 *      Search for an interface by index. Returns %NULL if the device
 *      is not found or a pointer to the device. The device has not
 *      had its reference counter increased so the caller must be careful
 *      about locking. The caller must hold either the RTNL semaphore
 *      or @dev_base_lock.
 */

struct net_device *__dev_get_by_index(struct net *net, int ifindex)
{
        struct net_device *dev;
        struct hlist_head *head = dev_index_hash(net, ifindex);

        hlist_for_each_entry(dev, head, index_hlist)
                if (dev->ifindex == ifindex)
                        return dev;

        return NULL;
}
EXPORT_SYMBOL(__dev_get_by_index);

/**
 *      dev_get_by_index_rcu - find a device by its ifindex
 *      @net: the applicable net namespace
 *      @ifindex: index of device
 *
 *      Search for an interface by index. Returns %NULL if the device
 *      is not found or a pointer to the device. The device has not
 *      had its reference counter increased so the caller must be careful
 *      about locking. The caller must hold RCU lock.
 */

struct net_device *dev_get_by_index_rcu(struct net *net, int ifindex)
{
        struct net_device *dev;
        struct hlist_head *head = dev_index_hash(net, ifindex);

        hlist_for_each_entry_rcu(dev, head, index_hlist)
                if (dev->ifindex == ifindex)
                        return dev;

        return NULL;
}
EXPORT_SYMBOL(dev_get_by_index_rcu);


/**
 *      dev_get_by_index - find a device by its ifindex
 *      @net: the applicable net namespace
 *      @ifindex: index of device
 *
 *      Search for an interface by index. Returns NULL if the device
 *      is not found or a pointer to the device. The device returned has
 *      had a reference added and the pointer is safe until the user calls
 *      dev_put to indicate they have finished with it.
 */

struct net_device *dev_get_by_index(struct net *net, int ifindex)
{
        struct net_device *dev;

        rcu_read_lock();
        dev = dev_get_by_index_rcu(net, ifindex);
        if (dev)
                dev_hold(dev);
        rcu_read_unlock();
        return dev;
}
EXPORT_SYMBOL(dev_get_by_index);

/**
 *      netdev_get_name - get a netdevice name, knowing its ifindex.
 *      @net: network namespace
 *      @name: a pointer to the buffer where the name will be stored.
 *      @ifindex: the ifindex of the interface to get the name from.
 *
 *      The use of raw_seqcount_begin() and cond_resched() before
 *      retrying is required as we want to give the writers a chance
 *      to complete when CONFIG_PREEMPT is not set.
 */
int netdev_get_name(struct net *net, char *name, int ifindex)
{
        struct net_device *dev;
        unsigned int seq;

retry:
        seq = raw_seqcount_begin(&devnet_rename_seq);
        rcu_read_lock();
        dev = dev_get_by_index_rcu(net, ifindex);
        if (!dev) {
                rcu_read_unlock();
                return -ENODEV;
        }

        strcpy(name, dev->name);
        rcu_read_unlock();
        if (read_seqcount_retry(&devnet_rename_seq, seq)) {
                cond_resched();
                goto retry;
        }

        return 0;
}

/**
 *      dev_getbyhwaddr_rcu - find a device by its hardware address
 *      @net: the applicable net namespace
 *      @type: media type of device
 *      @ha: hardware address
 *
 *      Search for an interface by MAC address. Returns NULL if the device
 *      is not found or a pointer to the device.
 *      The caller must hold RCU or RTNL.
 *      The returned device has not had its ref count increased
 *      and the caller must therefore be careful about locking
 *
 */

struct net_device *dev_getbyhwaddr_rcu(struct net *net, unsigned short type,
                                       const char *ha)
{
        struct net_device *dev;

        for_each_netdev_rcu(net, dev)
                if (dev->type == type &&
                    !memcmp(dev->dev_addr, ha, dev->addr_len))
                        return dev;

        return NULL;
}
EXPORT_SYMBOL(dev_getbyhwaddr_rcu);

struct net_device *__dev_getfirstbyhwtype(struct net *net, unsigned short type)
{
        struct net_device *dev;

        ASSERT_RTNL();
        for_each_netdev(net, dev)
                if (dev->type == type)
                        return dev;

        return NULL;
}
EXPORT_SYMBOL(__dev_getfirstbyhwtype);

struct net_device *dev_getfirstbyhwtype(struct net *net, unsigned short type)
{
        struct net_device *dev, *ret = NULL;

        rcu_read_lock();
        for_each_netdev_rcu(net, dev)
                if (dev->type == type) {
                        dev_hold(dev);
                        ret = dev;
                        break;
                }
        rcu_read_unlock();
        return ret;
}
EXPORT_SYMBOL(dev_getfirstbyhwtype);

/**
 *      __dev_get_by_flags - find any device with given flags
 *      @net: the applicable net namespace
 *      @if_flags: IFF_* values
 *      @mask: bitmask of bits in if_flags to check
 *
 *      Search for any interface with the given flags. Returns NULL if a device
 *      is not found or a pointer to the device. Must be called inside
 *      rtnl_lock(), and result refcount is unchanged.
 */

struct net_device *__dev_get_by_flags(struct net *net, unsigned short if_flags,
                                      unsigned short mask)
{
        struct net_device *dev, *ret;

        ASSERT_RTNL();

        ret = NULL;
        for_each_netdev(net, dev) {
                if (((dev->flags ^ if_flags) & mask) == 0) {
                        ret = dev;
                        break;
                }
        }
        return ret;
}
EXPORT_SYMBOL(__dev_get_by_flags);

/**
 *      dev_valid_name - check if name is okay for network device
 *      @name: name string
 *
 *      Network device names need to be valid file names to
 *      to allow sysfs to work.  We also disallow any kind of
 *      whitespace.
 */
bool dev_valid_name(const char *name)
{
        if (*name == '\0')
                return false;
        if (strlen(name) >= IFNAMSIZ)
                return false;
        if (!strcmp(name, ".") || !strcmp(name, ".."))
                return false;

        while (*name) {
                if (*name == '/' || *name == ':' || isspace(*name))
                        return false;
                name++;
        }
        return true;
}
EXPORT_SYMBOL(dev_valid_name);

/**
 *      __dev_alloc_name - allocate a name for a device
 *      @net: network namespace to allocate the device name in
 *      @name: name format string
 *      @buf:  scratch buffer and result name string
 *
 *      Passed a format string - eg "lt%d" it will try and find a suitable
 *      id. It scans list of devices to build up a free map, then chooses
 *      the first empty slot. The caller must hold the dev_base or rtnl lock
 *      while allocating the name and adding the device in order to avoid
 *      duplicates.
 *      Limited to bits_per_byte * page size devices (ie 32K on most platforms).
 *      Returns the number of the unit assigned or a negative errno code.
 */

static int __dev_alloc_name(struct net *net, const char *name, char *buf)
{
        int i = 0;
        const char *p;
        const int max_netdevices = 8*PAGE_SIZE;
        unsigned long *inuse;
        struct net_device *d;
 
         p = strnchr(name, IFNAMSIZ-1, '%');
         if (p) {
                 /*
                  * Verify the string as this thing may have come from
                  * the user.  There must be either one "%d" and no other "%"
                  * characters.
                  */
                 if (p[1] != 'd' || strchr(p + 2, '%'))
                         return -EINVAL;
 
                 /* Use one page as a bit array of possible slots */
                 inuse = (unsigned long *) get_zeroed_page(GFP_ATOMIC);
                 if (!inuse)
                         return -ENOMEM;
 
                 for_each_netdev(net, d) {
                         if (!sscanf(d->name, name, &i))
                                 continue;
                         if (i < 0 || i >= max_netdevices)
                                 continue;
 
                         /*  avoid cases where sscanf is not exact inverse of printf */
                         snprintf(buf, IFNAMSIZ, name, i);
                         if (!strncmp(buf, d->name, IFNAMSIZ))
                                 set_bit(i, inuse);
                 }
 
                 i = find_first_zero_bit(inuse, max_netdevices);
                 free_page((unsigned long) inuse);
         }
 
         if (buf != name)
                 snprintf(buf, IFNAMSIZ, name, i);
         if (!__dev_get_by_name(net, buf))
                 return i;
 
         /* It is possible to run out of possible slots
          * when the name is long and there isn't enough space left
          * for the digits, or if all bits are used.
          */
         return -ENFILE;
 }
 
 /**
  *      dev_alloc_name - allocate a name for a device
  *      @dev: device
  *      @name: name format string
  *
  *      Passed a format string - eg "lt%d" it will try and find a suitable
  *      id. It scans list of devices to build up a free map, then chooses
  *      the first empty slot. The caller must hold the dev_base or rtnl lock
  *      while allocating the name and adding the device in order to avoid
  *      duplicates.
  *      Limited to bits_per_byte * page size devices (ie 32K on most platforms).
  *      Returns the number of the unit assigned or a negative errno code.
  */
 
 int dev_alloc_name(struct net_device *dev, const char *name)
 {
         char buf[IFNAMSIZ];
         struct net *net;
         int ret;
 
         BUG_ON(!dev_net(dev));
         net = dev_net(dev);
         ret = __dev_alloc_name(net, name, buf);
         if (ret >= 0)
                 strlcpy(dev->name, buf, IFNAMSIZ);
         return ret;
 }
 EXPORT_SYMBOL(dev_alloc_name);
 
 static int dev_alloc_name_ns(struct net *net,
                              struct net_device *dev,
                              const char *name)
 {
         char buf[IFNAMSIZ];
         int ret;
 
         ret = __dev_alloc_name(net, name, buf);
         if (ret >= 0)
                 strlcpy(dev->name, buf, IFNAMSIZ);
         return ret;
 }
 
 static int dev_get_valid_name(struct net *net,
                               struct net_device *dev,
                               const char *name)
 {
         BUG_ON(!net);
 
         if (!dev_valid_name(name))
                 return -EINVAL;
 
         if (strchr(name, '%'))
                 return dev_alloc_name_ns(net, dev, name);
         else if (__dev_get_by_name(net, name))
                 return -EEXIST;
         else if (dev->name != name)
                 strlcpy(dev->name, name, IFNAMSIZ);
 
         return 0;
 }
 
 /**
  *      dev_change_name - change name of a device
  *      @dev: device
  *      @newname: name (or format string) must be at least IFNAMSIZ
  *
  *      Change name of a device, can pass format strings "eth%d".
  *      for wildcarding.
  */
 int dev_change_name(struct net_device *dev, const char *newname)
 {
         unsigned char old_assign_type;
         char oldname[IFNAMSIZ];
         int err = 0;
         int ret;
         struct net *net;
 
         ASSERT_RTNL();
         BUG_ON(!dev_net(dev));
 
         net = dev_net(dev);
         if (dev->flags & IFF_UP)
                 return -EBUSY;
 
         write_seqcount_begin(&devnet_rename_seq);
 
         if (strncmp(newname, dev->name, IFNAMSIZ) == 0) {
                 write_seqcount_end(&devnet_rename_seq);
                 return 0;
         }
 
         memcpy(oldname, dev->name, IFNAMSIZ);
 
         err = dev_get_valid_name(net, dev, newname);
         if (err < 0) {
                 write_seqcount_end(&devnet_rename_seq);
                 return err;
         }
 
         if (oldname[0] && !strchr(oldname, '%'))
                 netdev_info(dev, "renamed from %s\n", oldname);
 
         old_assign_type = dev->name_assign_type;
         dev->name_assign_type = NET_NAME_RENAMED;
 
 rollback:
         ret = device_rename(&dev->dev, dev->name);
         if (ret) {
                 memcpy(dev->name, oldname, IFNAMSIZ);
                 dev->name_assign_type = old_assign_type;
                 write_seqcount_end(&devnet_rename_seq);
                 return ret;
         }
 
         write_seqcount_end(&devnet_rename_seq);
 
         netdev_adjacent_rename_links(dev, oldname);
 
         write_lock_bh(&dev_base_lock);
         hlist_del_rcu(&dev->name_hlist);
         write_unlock_bh(&dev_base_lock);
 
         synchronize_rcu();
 
         write_lock_bh(&dev_base_lock);
         hlist_add_head_rcu(&dev->name_hlist, dev_name_hash(net, dev->name));
         write_unlock_bh(&dev_base_lock);
 
         ret = call_netdevice_notifiers(NETDEV_CHANGENAME, dev);
         ret = notifier_to_errno(ret);
 
         if (ret) {
                 /* err >= 0 after dev_alloc_name() or stores the first errno */
                 if (err >= 0) {
                         err = ret;
                         write_seqcount_begin(&devnet_rename_seq);
                         memcpy(dev->name, oldname, IFNAMSIZ);
                         memcpy(oldname, newname, IFNAMSIZ);
                         dev->name_assign_type = old_assign_type;
                         old_assign_type = NET_NAME_RENAMED;
                         goto rollback;
                 } else {
                         pr_err("%s: name change rollback failed: %d\n",
                                dev->name, ret);
                 }
         }
 
         return err;
 }
 
 /**
  *      dev_set_alias - change ifalias of a device
  *      @dev: device
  *      @alias: name up to IFALIASZ
  *      @len: limit of bytes to copy from info
  *
  *      Set ifalias for a device,
  */
 int dev_set_alias(struct net_device *dev, const char *alias, size_t len)
 {
         char *new_ifalias;
 
         ASSERT_RTNL();
 
         if (len >= IFALIASZ)
                 return -EINVAL;
 
         if (!len) {
                 kfree(dev->ifalias);
                 dev->ifalias = NULL;
                 return 0;
         }
 
         new_ifalias = krealloc(dev->ifalias, len + 1, GFP_KERNEL);
         if (!new_ifalias)
                 return -ENOMEM;
         dev->ifalias = new_ifalias;
 
         strlcpy(dev->ifalias, alias, len+1);
         return len;
 }
 
 
 /**
  *      netdev_features_change - device changes features
  *      @dev: device to cause notification
  *
  *      Called to indicate a device has changed features.
  */
 void netdev_features_change(struct net_device *dev)
 {
         call_netdevice_notifiers(NETDEV_FEAT_CHANGE, dev);
 }
 EXPORT_SYMBOL(netdev_features_change);
 
 /**
  *      netdev_state_change - device changes state
  *      @dev: device to cause notification
  *
  *      Called to indicate a device has changed state. This function calls
  *      the notifier chains for netdev_chain and sends a NEWLINK message
  *      to the routing socket.
  */
 void netdev_state_change(struct net_device *dev)
 {
         if (dev->flags & IFF_UP) {
                 struct netdev_notifier_change_info change_info;
 
                 change_info.flags_changed = 0;
                 call_netdevice_notifiers_info(NETDEV_CHANGE, dev,
                                               &change_info.info);
                 rtmsg_ifinfo(RTM_NEWLINK, dev, 0, GFP_KERNEL);
         }
 }
 EXPORT_SYMBOL(netdev_state_change);
 
 /**
  *      netdev_notify_peers - notify network peers about existence of @dev
  *      @dev: network device
  *
  * Generate traffic such that interested network peers are aware of
  * @dev, such as by generating a gratuitous ARP. This may be used when
  * a device wants to inform the rest of the network about some sort of
  * reconfiguration such as a failover event or virtual machine
  * migration.
  */
 void netdev_notify_peers(struct net_device *dev)
 {
         rtnl_lock();
         call_netdevice_notifiers(NETDEV_NOTIFY_PEERS, dev);
         rtnl_unlock();
 }
 EXPORT_SYMBOL(netdev_notify_peers);
 
 static int __dev_open(struct net_device *dev)
 {
         const struct net_device_ops *ops = dev->netdev_ops;
         int ret;
 
         ASSERT_RTNL();
 
         if (!netif_device_present(dev))
                 return -ENODEV;
 
         /* Block netpoll from trying to do any rx path servicing.
          * If we don't do this there is a chance ndo_poll_controller
          * or ndo_poll may be running while we open the device
          */
         netpoll_poll_disable(dev);
 
         ret = call_netdevice_notifiers(NETDEV_PRE_UP, dev);
         ret = notifier_to_errno(ret);
         if (ret)
                 return ret;
 
         set_bit(__LINK_STATE_START, &dev->state);
 
         if (ops->ndo_validate_addr)
                 ret = ops->ndo_validate_addr(dev);
 
         if (!ret && ops->ndo_open)
                 ret = ops->ndo_open(dev);
 
         netpoll_poll_enable(dev);
 
         if (ret)
                 clear_bit(__LINK_STATE_START, &dev->state);
         else {
                 dev->flags |= IFF_UP;
                 dev_set_rx_mode(dev);
                 dev_activate(dev);
                 add_device_randomness(dev->dev_addr, dev->addr_len);
         }
 
         return ret;
 }
 
 /**
  *      dev_open        - prepare an interface for use.
  *      @dev:   device to open
  *
  *      Takes a device from down to up state. The device's private open
  *      function is invoked and then the multicast lists are loaded. Finally
  *      the device is moved into the up state and a %NETDEV_UP message is
  *      sent to the netdev notifier chain.
  *
  *      Calling this function on an active interface is a nop. On a failure
  *      a negative errno code is returned.
  */
 int dev_open(struct net_device *dev)
 {
         int ret;
 
         if (dev->flags & IFF_UP)
                 return 0;
 
         ret = __dev_open(dev);
         if (ret < 0)
                 return ret;
 
         rtmsg_ifinfo(RTM_NEWLINK, dev, IFF_UP|IFF_RUNNING, GFP_KERNEL);
         call_netdevice_notifiers(NETDEV_UP, dev);
 
         return ret;
 }
 EXPORT_SYMBOL(dev_open);
 
 static int __dev_close_many(struct list_head *head)
 {
         struct net_device *dev;
 
         ASSERT_RTNL();
         might_sleep();
 
         list_for_each_entry(dev, head, close_list) {
                 /* Temporarily disable netpoll until the interface is down */
                 netpoll_poll_disable(dev);
 
                 call_netdevice_notifiers(NETDEV_GOING_DOWN, dev);
 
                 clear_bit(__LINK_STATE_START, &dev->state);
 
                 /* Synchronize to scheduled poll. We cannot touch poll list, it
                  * can be even on different cpu. So just clear netif_running().
                  *
                  * dev->stop() will invoke napi_disable() on all of it's
                  * napi_struct instances on this device.
                  */
                 smp_mb__after_atomic(); /* Commit netif_running(). */
         }
 
         dev_deactivate_many(head);
 
         list_for_each_entry(dev, head, close_list) {
                 const struct net_device_ops *ops = dev->netdev_ops;
 
                 /*
                  *      Call the device specific close. This cannot fail.
                  *      Only if device is UP
                  *
                  *      We allow it to be called even after a DETACH hot-plug
                  *      event.
                  */
                 if (ops->ndo_stop)
                         ops->ndo_stop(dev);
 
                 dev->flags &= ~IFF_UP;
                 netpoll_poll_enable(dev);
         }
 
         return 0;
 }
 
 static int __dev_close(struct net_device *dev)
 {
         int retval;
         LIST_HEAD(single);
 
         list_add(&dev->close_list, &single);
         retval = __dev_close_many(&single);
         list_del(&single);
 
         return retval;
 }
 
 int dev_close_many(struct list_head *head, bool unlink)
 {
         struct net_device *dev, *tmp;
 
         /* Remove the devices that don't need to be closed */
         list_for_each_entry_safe(dev, tmp, head, close_list)
                 if (!(dev->flags & IFF_UP))
                         list_del_init(&dev->close_list);
 
         __dev_close_many(head);
 
         list_for_each_entry_safe(dev, tmp, head, close_list) {
                 rtmsg_ifinfo(RTM_NEWLINK, dev, IFF_UP|IFF_RUNNING, GFP_KERNEL);
                 call_netdevice_notifiers(NETDEV_DOWN, dev);
                 if (unlink)
                         list_del_init(&dev->close_list);
         }
 
         return 0;
 }
 EXPORT_SYMBOL(dev_close_many);
 
 /**
  *      dev_close - shutdown an interface.
  *      @dev: device to shutdown
  *
  *      This function moves an active device into down state. A
  *      %NETDEV_GOING_DOWN is sent to the netdev notifier chain. The device
  *      is then deactivated and finally a %NETDEV_DOWN is sent to the notifier
  *      chain.
  */
 int dev_close(struct net_device *dev)
 {
         if (dev->flags & IFF_UP) {
                 LIST_HEAD(single);
 
                 list_add(&dev->close_list, &single);
                 dev_close_many(&single, true);
                 list_del(&single);
         }
         return 0;
 }
 EXPORT_SYMBOL(dev_close);
 
 
 /**
  *      dev_disable_lro - disable Large Receive Offload on a device
  *      @dev: device
  *
  *      Disable Large Receive Offload (LRO) on a net device.  Must be
  *      called under RTNL.  This is needed if received packets may be
  *      forwarded to another interface.
  */
 void dev_disable_lro(struct net_device *dev)
 {
         struct net_device *lower_dev;
         struct list_head *iter;
 
         dev->wanted_features &= ~NETIF_F_LRO;
         netdev_update_features(dev);
 
         if (unlikely(dev->features & NETIF_F_LRO))
                 netdev_WARN(dev, "failed to disable LRO!\n");
 
         netdev_for_each_lower_dev(dev, lower_dev, iter)
                 dev_disable_lro(lower_dev);
 }
 EXPORT_SYMBOL(dev_disable_lro);
 
 static int call_netdevice_notifier(struct notifier_block *nb, unsigned long val,
                                    struct net_device *dev)
 {
         struct netdev_notifier_info info;
 
         netdev_notifier_info_init(&info, dev);
         return nb->notifier_call(nb, val, &info);
 }
 
 static int dev_boot_phase = 1;
 
 /**
  *      register_netdevice_notifier - register a network notifier block
  *      @nb: notifier
  *
  *      Register a notifier to be called when network device events occur.
  *      The notifier passed is linked into the kernel structures and must
  *      not be reused until it has been unregistered. A negative errno code
  *      is returned on a failure.
  *
  *      When registered all registration and up events are replayed
  *      to the new notifier to allow device to have a race free
  *      view of the network device list.
  */
 
 int register_netdevice_notifier(struct notifier_block *nb)
 {
         struct net_device *dev;
         struct net_device *last;
         struct net *net;
         int err;
 
         rtnl_lock();
         err = raw_notifier_chain_register(&netdev_chain, nb);
         if (err)
                 goto unlock;
         if (dev_boot_phase)
                 goto unlock;
         for_each_net(net) {
                 for_each_netdev(net, dev) {
                         err = call_netdevice_notifier(nb, NETDEV_REGISTER, dev);
                         err = notifier_to_errno(err);
                         if (err)
                                 goto rollback;
 
                         if (!(dev->flags & IFF_UP))
                                 continue;
 
                         call_netdevice_notifier(nb, NETDEV_UP, dev);
                 }
         }
 
 unlock:
         rtnl_unlock();
         return err;
 
 rollback:
         last = dev;
         for_each_net(net) {
                 for_each_netdev(net, dev) {
                         if (dev == last)
                                 goto outroll;
 
                         if (dev->flags & IFF_UP) {
                                 call_netdevice_notifier(nb, NETDEV_GOING_DOWN,
                                                         dev);
                                 call_netdevice_notifier(nb, NETDEV_DOWN, dev);
                         }
                         call_netdevice_notifier(nb, NETDEV_UNREGISTER, dev);
                 }
         }
 
 outroll:
         raw_notifier_chain_unregister(&netdev_chain, nb);
         goto unlock;
 }
 EXPORT_SYMBOL(register_netdevice_notifier);
 
 /**
  *      unregister_netdevice_notifier - unregister a network notifier block
  *      @nb: notifier
  *
  *      Unregister a notifier previously registered by
  *      register_netdevice_notifier(). The notifier is unlinked into the
  *      kernel structures and may then be reused. A negative errno code
  *      is returned on a failure.
  *
  *      After unregistering unregister and down device events are synthesized
  *      for all devices on the device list to the removed notifier to remove
  *      the need for special case cleanup code.
  */
 
 int unregister_netdevice_notifier(struct notifier_block *nb)
 {
         struct net_device *dev;
         struct net *net;
         int err;
 
         rtnl_lock();
         err = raw_notifier_chain_unregister(&netdev_chain, nb);
         if (err)
                 goto unlock;
 
         for_each_net(net) {
                 for_each_netdev(net, dev) {
                         if (dev->flags & IFF_UP) {
                                 call_netdevice_notifier(nb, NETDEV_GOING_DOWN,
                                                         dev);
                                 call_netdevice_notifier(nb, NETDEV_DOWN, dev);
                         }
                         call_netdevice_notifier(nb, NETDEV_UNREGISTER, dev);
                 }
         }
 unlock:
         rtnl_unlock();
         return err;
 }
 EXPORT_SYMBOL(unregister_netdevice_notifier);
 
 /**
  *      call_netdevice_notifiers_info - call all network notifier blocks
  *      @val: value passed unmodified to notifier function
  *      @dev: net_device pointer passed unmodified to notifier function
  *      @info: notifier information data
  *
  *      Call all network notifier blocks.  Parameters and return value
  *      are as for raw_notifier_call_chain().
  */
 
 static int call_netdevice_notifiers_info(unsigned long val,
                                          struct net_device *dev,
                                          struct netdev_notifier_info *info)
 {
         ASSERT_RTNL();
         netdev_notifier_info_init(info, dev);
         return raw_notifier_call_chain(&netdev_chain, val, info);
 }
 
 /**
  *      call_netdevice_notifiers - call all network notifier blocks
  *      @val: value passed unmodified to notifier function
  *      @dev: net_device pointer passed unmodified to notifier function
  *
  *      Call all network notifier blocks.  Parameters and return value
  *      are as for raw_notifier_call_chain().
  */
 
 int call_netdevice_notifiers(unsigned long val, struct net_device *dev)
 {
         struct netdev_notifier_info info;
 
         return call_netdevice_notifiers_info(val, dev, &info);
 }
 EXPORT_SYMBOL(call_netdevice_notifiers);
 
 #ifdef CONFIG_NET_CLS_ACT
 static struct static_key ingress_needed __read_mostly;
 
 void net_inc_ingress_queue(void)
 {
         static_key_slow_inc(&ingress_needed);
 }
 EXPORT_SYMBOL_GPL(net_inc_ingress_queue);
 
 void net_dec_ingress_queue(void)
 {
         static_key_slow_dec(&ingress_needed);
 }
 EXPORT_SYMBOL_GPL(net_dec_ingress_queue);
 #endif
 
 static struct static_key netstamp_needed __read_mostly;
 #ifdef HAVE_JUMP_LABEL
 /* We are not allowed to call static_key_slow_dec() from irq context
  * If net_disable_timestamp() is called from irq context, defer the
  * static_key_slow_dec() calls.
  */
 static atomic_t netstamp_needed_deferred;
 #endif
 
 void net_enable_timestamp(void)
 {
 #ifdef HAVE_JUMP_LABEL
         int deferred = atomic_xchg(&netstamp_needed_deferred, 0);
 
         if (deferred) {
                 while (--deferred)
                         static_key_slow_dec(&netstamp_needed);
                 return;
         }
 #endif
         static_key_slow_inc(&netstamp_needed);
 }
 EXPORT_SYMBOL(net_enable_timestamp);
 
 void net_disable_timestamp(void)
 {
 #ifdef HAVE_JUMP_LABEL
         if (in_interrupt()) {
                 atomic_inc(&netstamp_needed_deferred);
                 return;
         }
 #endif
         static_key_slow_dec(&netstamp_needed);
 }
 EXPORT_SYMBOL(net_disable_timestamp);
 
 static inline void net_timestamp_set(struct sk_buff *skb)
 {
         skb->tstamp.tv64 = 0;
         if (static_key_false(&netstamp_needed))
                 __net_timestamp(skb);
 }
 
 #define net_timestamp_check(COND, SKB)                  \
         if (static_key_false(&netstamp_needed)) {               \
                 if ((COND) && !(SKB)->tstamp.tv64)      \
                         __net_timestamp(SKB);           \
         }                                               \
 
 bool is_skb_forwardable(struct net_device *dev, struct sk_buff *skb)
 {
         unsigned int len;
 
         if (!(dev->flags & IFF_UP))
                 return false;
 
         len = dev->mtu + dev->hard_header_len + VLAN_HLEN;
         if (skb->len <= len)
                 return true;
 
         /* if TSO is enabled, we don't care about the length as the packet
          * could be forwarded without being segmented before
          */
         if (skb_is_gso(skb))
                 return true;
 
         return false;
 }
 EXPORT_SYMBOL_GPL(is_skb_forwardable);
 
 int __dev_forward_skb(struct net_device *dev, struct sk_buff *skb)
 {
         if (skb_orphan_frags(skb, GFP_ATOMIC) ||
             unlikely(!is_skb_forwardable(dev, skb))) {
                 atomic_long_inc(&dev->rx_dropped);
                 kfree_skb(skb);
                 return NET_RX_DROP;
         }
 
         skb_scrub_packet(skb, true);
         skb->priority = 0;
         skb->protocol = eth_type_trans(skb, dev);
         skb_postpull_rcsum(skb, eth_hdr(skb), ETH_HLEN);
 
         return 0;
 }
 EXPORT_SYMBOL_GPL(__dev_forward_skb);
 
 /**
  * dev_forward_skb - loopback an skb to another netif
  *
  * @dev: destination network device
  * @skb: buffer to forward
  *
  * return values:
  *      NET_RX_SUCCESS  (no congestion)
  *      NET_RX_DROP     (packet was dropped, but freed)
  *
  * dev_forward_skb can be used for injecting an skb from the
  * start_xmit function of one device into the receive queue
  * of another device.
  *
  * The receiving device may be in another namespace, so
  * we have to clear all information in the skb that could
  * impact namespace isolation.
  */
 int dev_forward_skb(struct net_device *dev, struct sk_buff *skb)
 {
         return __dev_forward_skb(dev, skb) ?: netif_rx_internal(skb);
 }
 EXPORT_SYMBOL_GPL(dev_forward_skb);
 
 static inline int deliver_skb(struct sk_buff *skb,
                               struct packet_type *pt_prev,
                               struct net_device *orig_dev)
 {
         if (unlikely(skb_orphan_frags(skb, GFP_ATOMIC)))
                 return -ENOMEM;
         atomic_inc(&skb->users);
         return pt_prev->func(skb, skb->dev, pt_prev, orig_dev);
 }
 
 static inline void deliver_ptype_list_skb(struct sk_buff *skb,
                                           struct packet_type **pt,
                                           struct net_device *orig_dev,
                                           __be16 type,
                                           struct list_head *ptype_list)
 {
         struct packet_type *ptype, *pt_prev = *pt;
 
         list_for_each_entry_rcu(ptype, ptype_list, list) {
                 if (ptype->type != type)
                         continue;
                 if (pt_prev)
                         deliver_skb(skb, pt_prev, orig_dev);
                 pt_prev = ptype;
         }
         *pt = pt_prev;
 }
 
 static inline bool skb_loop_sk(struct packet_type *ptype, struct sk_buff *skb)
 {
         if (!ptype->af_packet_priv || !skb->sk)
                 return false;
 
         if (ptype->id_match)
                 return ptype->id_match(ptype, skb->sk);
         else if ((struct sock *)ptype->af_packet_priv == skb->sk)
                 return true;
 
         return false;
 }
 
 /*
  *      Support routine. Sends outgoing frames to any network
  *      taps currently in use.
  */
 
 static void dev_queue_xmit_nit(struct sk_buff *skb, struct net_device *dev)
 {
         struct packet_type *ptype;
         struct sk_buff *skb2 = NULL;
         struct packet_type *pt_prev = NULL;
         struct list_head *ptype_list = &ptype_all;
 
         rcu_read_lock();
 again:
         list_for_each_entry_rcu(ptype, ptype_list, list) {
                 /* Never send packets back to the socket
                  * they originated from - MvS (miquels@drinkel.ow.org)
                  */
                 if (skb_loop_sk(ptype, skb))
                         continue;
 
                 if (pt_prev) {
                         deliver_skb(skb2, pt_prev, skb->dev);
                         pt_prev = ptype;
                         continue;
                 }
 
                 /* need to clone skb, done only once */
                 skb2 = skb_clone(skb, GFP_ATOMIC);
                 if (!skb2)
                         goto out_unlock;
 
                 net_timestamp_set(skb2);
 
                 /* skb->nh should be correctly
                  * set by sender, so that the second statement is
                  * just protection against buggy protocols.
                  */
                 skb_reset_mac_header(skb2);
 
                 if (skb_network_header(skb2) < skb2->data ||
                     skb_network_header(skb2) > skb_tail_pointer(skb2)) {
                         net_crit_ratelimited("protocol %04x is buggy, dev %s\n",
                                              ntohs(skb2->protocol),
                                              dev->name);
                         skb_reset_network_header(skb2);
                 }
 
                 skb2->transport_header = skb2->network_header;
                 skb2->pkt_type = PACKET_OUTGOING;
                 pt_prev = ptype;
         }
 
         if (ptype_list == &ptype_all) {
                 ptype_list = &dev->ptype_all;
                 goto again;
         }
 out_unlock:
         if (pt_prev)
                 pt_prev->func(skb2, skb->dev, pt_prev, skb->dev);
         rcu_read_unlock();
 }
 
 /**
  * netif_setup_tc - Handle tc mappings on real_num_tx_queues change
  * @dev: Network device
  * @txq: number of queues available
  *
  * If real_num_tx_queues is changed the tc mappings may no longer be
  * valid. To resolve this verify the tc mapping remains valid and if
  * not NULL the mapping. With no priorities mapping to this
  * offset/count pair it will no longer be used. In the worst case TC0
  * is invalid nothing can be done so disable priority mappings. If is
  * expected that drivers will fix this mapping if they can before
  * calling netif_set_real_num_tx_queues.
  */
 static void netif_setup_tc(struct net_device *dev, unsigned int txq)
 {
         int i;
         struct netdev_tc_txq *tc = &dev->tc_to_txq[0];
 
         /* If TC0 is invalidated disable TC mapping */
         if (tc->offset + tc->count > txq) {
                 pr_warn("Number of in use tx queues changed invalidating tc mappings. Priority traffic classification disabled!\n");
                 dev->num_tc = 0;
                 return;
         }
 
         /* Invalidated prio to tc mappings set to TC0 */
         for (i = 1; i < TC_BITMASK + 1; i++) {
                 int q = netdev_get_prio_tc_map(dev, i);
 
                 tc = &dev->tc_to_txq[q];
                 if (tc->offset + tc->count > txq) {
                         pr_warn("Number of in use tx queues changed. Priority %i to tc mapping %i is no longer valid. Setting map to 0\n",
                                 i, q);
                         netdev_set_prio_tc_map(dev, i, 0);
                 }
         }
 }
 
 #ifdef CONFIG_XPS
 static DEFINE_MUTEX(xps_map_mutex);
 #define xmap_dereference(P)             \
         rcu_dereference_protected((P), lockdep_is_held(&xps_map_mutex))
 
 static struct xps_map *remove_xps_queue(struct xps_dev_maps *dev_maps,
                                         int cpu, u16 index)
 {
         struct xps_map *map = NULL;
         int pos;
 
         if (dev_maps)
                 map = xmap_dereference(dev_maps->cpu_map[cpu]);
 
         for (pos = 0; map && pos < map->len; pos++) {
                 if (map->queues[pos] == index) {
                         if (map->len > 1) {
                                 map->queues[pos] = map->queues[--map->len];
                         } else {
                                 RCU_INIT_POINTER(dev_maps->cpu_map[cpu], NULL);
                                 kfree_rcu(map, rcu);
                                 map = NULL;
                         }
                         break;
                 }
         }
 
         return map;
 }
 
 static void netif_reset_xps_queues_gt(struct net_device *dev, u16 index)
 {
         struct xps_dev_maps *dev_maps;
         int cpu, i;
         bool active = false;
 
         mutex_lock(&xps_map_mutex);
         dev_maps = xmap_dereference(dev->xps_maps);
 
         if (!dev_maps)
                 goto out_no_maps;
 
         for_each_possible_cpu(cpu) {
                 for (i = index; i < dev->num_tx_queues; i++) {
                         if (!remove_xps_queue(dev_maps, cpu, i))
                                 break;
                 }
                 if (i == dev->num_tx_queues)
                         active = true;
         }
 
         if (!active) {
                 RCU_INIT_POINTER(dev->xps_maps, NULL);
                 kfree_rcu(dev_maps, rcu);
         }
 
         for (i = index; i < dev->num_tx_queues; i++)
                 netdev_queue_numa_node_write(netdev_get_tx_queue(dev, i),
                                              NUMA_NO_NODE);
 
 out_no_maps:
         mutex_unlock(&xps_map_mutex);
 }
 
 static struct xps_map *expand_xps_map(struct xps_map *map,
                                       int cpu, u16 index)
 {
         struct xps_map *new_map;
         int alloc_len = XPS_MIN_MAP_ALLOC;
         int i, pos;
 
         for (pos = 0; map && pos < map->len; pos++) {
                 if (map->queues[pos] != index)
                         continue;
                 return map;
         }
 
         /* Need to add queue to this CPU's existing map */
         if (map) {
                 if (pos < map->alloc_len)
                         return map;
 
                 alloc_len = map->alloc_len * 2;
         }
 
         /* Need to allocate new map to store queue on this CPU's map */
         new_map = kzalloc_node(XPS_MAP_SIZE(alloc_len), GFP_KERNEL,
                                cpu_to_node(cpu));
         if (!new_map)
                 return NULL;
 
         for (i = 0; i < pos; i++)
                 new_map->queues[i] = map->queues[i];
         new_map->alloc_len = alloc_len;
         new_map->len = pos;
 
         return new_map;
 }
 
 int netif_set_xps_queue(struct net_device *dev, const struct cpumask *mask,
                         u16 index)
 {
         struct xps_dev_maps *dev_maps, *new_dev_maps = NULL;
         struct xps_map *map, *new_map;
         int maps_sz = max_t(unsigned int, XPS_DEV_MAPS_SIZE, L1_CACHE_BYTES);
         int cpu, numa_node_id = -2;
         bool active = false;
 
         mutex_lock(&xps_map_mutex);
 
         dev_maps = xmap_dereference(dev->xps_maps);
 
         /* allocate memory for queue storage */
         for_each_online_cpu(cpu) {
                 if (!cpumask_test_cpu(cpu, mask))
                         continue;
 
                 if (!new_dev_maps)
                         new_dev_maps = kzalloc(maps_sz, GFP_KERNEL);
                 if (!new_dev_maps) {
                         mutex_unlock(&xps_map_mutex);
                         return -ENOMEM;
                 }
 
                 map = dev_maps ? xmap_dereference(dev_maps->cpu_map[cpu]) :
                                  NULL;
 
                 map = expand_xps_map(map, cpu, index);
                 if (!map)
                         goto error;
 
                 RCU_INIT_POINTER(new_dev_maps->cpu_map[cpu], map);
         }
 
         if (!new_dev_maps)
                 goto out_no_new_maps;
 
         for_each_possible_cpu(cpu) {
                 if (cpumask_test_cpu(cpu, mask) && cpu_online(cpu)) {
                         /* add queue to CPU maps */
                         int pos = 0;
 
                         map = xmap_dereference(new_dev_maps->cpu_map[cpu]);
                         while ((pos < map->len) && (map->queues[pos] != index))
                                 pos++;
 
                         if (pos == map->len)
                                 map->queues[map->len++] = index;
 #ifdef CONFIG_NUMA
                         if (numa_node_id == -2)
                                 numa_node_id = cpu_to_node(cpu);
                         else if (numa_node_id != cpu_to_node(cpu))
                                 numa_node_id = -1;
 #endif
                 } else if (dev_maps) {
                         /* fill in the new device map from the old device map */
                         map = xmap_dereference(dev_maps->cpu_map[cpu]);
                         RCU_INIT_POINTER(new_dev_maps->cpu_map[cpu], map);
                 }
 
         }
 
         rcu_assign_pointer(dev->xps_maps, new_dev_maps);
 
         /* Cleanup old maps */
         if (dev_maps) {
                 for_each_possible_cpu(cpu) {
                         new_map = xmap_dereference(new_dev_maps->cpu_map[cpu]);
                         map = xmap_dereference(dev_maps->cpu_map[cpu]);
                         if (map && map != new_map)
                                 kfree_rcu(map, rcu);
                 }
 
                 kfree_rcu(dev_maps, rcu);
         }
 
         dev_maps = new_dev_maps;
         active = true;
 
 out_no_new_maps:
         /* update Tx queue numa node */
         netdev_queue_numa_node_write(netdev_get_tx_queue(dev, index),
                                      (numa_node_id >= 0) ? numa_node_id :
                                      NUMA_NO_NODE);
 
         if (!dev_maps)
                 goto out_no_maps;
 
         /* removes queue from unused CPUs */
         for_each_possible_cpu(cpu) {
                 if (cpumask_test_cpu(cpu, mask) && cpu_online(cpu))
                         continue;
 
                 if (remove_xps_queue(dev_maps, cpu, index))
                         active = true;
         }
 
         /* free map if not active */
         if (!active) {
                 RCU_INIT_POINTER(dev->xps_maps, NULL);
                 kfree_rcu(dev_maps, rcu);
         }
 
 out_no_maps:
         mutex_unlock(&xps_map_mutex);
 
         return 0;
 error:
         /* remove any maps that we added */
         for_each_possible_cpu(cpu) {
                 new_map = xmap_dereference(new_dev_maps->cpu_map[cpu]);
                 map = dev_maps ? xmap_dereference(dev_maps->cpu_map[cpu]) :
                                  NULL;
                 if (new_map && new_map != map)
                         kfree(new_map);
         }
 
         mutex_unlock(&xps_map_mutex);
 
         kfree(new_dev_maps);
         return -ENOMEM;
 }
 EXPORT_SYMBOL(netif_set_xps_queue);
 
 #endif
 /*
  * Routine to help set real_num_tx_queues. To avoid skbs mapped to queues
  * greater then real_num_tx_queues stale skbs on the qdisc must be flushed.
  */
 int netif_set_real_num_tx_queues(struct net_device *dev, unsigned int txq)
 {
         int rc;
 
         if (txq < 1 || txq > dev->num_tx_queues)
                 return -EINVAL;
 
         if (dev->reg_state == NETREG_REGISTERED ||
             dev->reg_state == NETREG_UNREGISTERING) {
                 ASSERT_RTNL();
 
                 rc = netdev_queue_update_kobjects(dev, dev->real_num_tx_queues,
                                                   txq);
                 if (rc)
                         return rc;
 
                 if (dev->num_tc)
                         netif_setup_tc(dev, txq);
 
                 if (txq < dev->real_num_tx_queues) {
                         qdisc_reset_all_tx_gt(dev, txq);
 #ifdef CONFIG_XPS
                         netif_reset_xps_queues_gt(dev, txq);
 #endif
                 }
         }
 
         dev->real_num_tx_queues = txq;
         return 0;
 }
 EXPORT_SYMBOL(netif_set_real_num_tx_queues);
 
 #ifdef CONFIG_SYSFS
 /**
  *      netif_set_real_num_rx_queues - set actual number of RX queues used
  *      @dev: Network device
  *      @rxq: Actual number of RX queues
  *
  *      This must be called either with the rtnl_lock held or before
  *      registration of the net device.  Returns 0 on success, or a
  *      negative error code.  If called before registration, it always
  *      succeeds.
  */
 int netif_set_real_num_rx_queues(struct net_device *dev, unsigned int rxq)
 {
         int rc;
 
         if (rxq < 1 || rxq > dev->num_rx_queues)
                 return -EINVAL;
 
         if (dev->reg_state == NETREG_REGISTERED) {
                 ASSERT_RTNL();
 
                 rc = net_rx_queue_update_kobjects(dev, dev->real_num_rx_queues,
                                                   rxq);
                 if (rc)
                         return rc;
         }
 
         dev->real_num_rx_queues = rxq;
         return 0;
 }
 EXPORT_SYMBOL(netif_set_real_num_rx_queues);
 #endif
 
 /**
  * netif_get_num_default_rss_queues - default number of RSS queues
  *
  * This routine should set an upper limit on the number of RSS queues
  * used by default by multiqueue devices.
  */
 int netif_get_num_default_rss_queues(void)
 {
         return min_t(int, DEFAULT_MAX_NUM_RSS_QUEUES, num_online_cpus());
 }
 EXPORT_SYMBOL(netif_get_num_default_rss_queues);
 
 static inline void __netif_reschedule(struct Qdisc *q)
 {
         struct softnet_data *sd;
         unsigned long flags;
 
         local_irq_save(flags);
         sd = this_cpu_ptr(&softnet_data);
         q->next_sched = NULL;
         *sd->output_queue_tailp = q;
         sd->output_queue_tailp = &q->next_sched;
         raise_softirq_irqoff(NET_TX_SOFTIRQ);
         local_irq_restore(flags);
 }
 
 void __netif_schedule(struct Qdisc *q)
 {
         if (!test_and_set_bit(__QDISC_STATE_SCHED, &q->state))
                 __netif_reschedule(q);
 }
 EXPORT_SYMBOL(__netif_schedule);
 
 struct dev_kfree_skb_cb {
         enum skb_free_reason reason;
 };
 
 static struct dev_kfree_skb_cb *get_kfree_skb_cb(const struct sk_buff *skb)
 {
         return (struct dev_kfree_skb_cb *)skb->cb;
 }
 
 void netif_schedule_queue(struct netdev_queue *txq)
 {
         rcu_read_lock();
         if (!(txq->state & QUEUE_STATE_ANY_XOFF)) {
                 struct Qdisc *q = rcu_dereference(txq->qdisc);
 
                 __netif_schedule(q);
         }
         rcu_read_unlock();
 }
 EXPORT_SYMBOL(netif_schedule_queue);
 
 /**
  *      netif_wake_subqueue - allow sending packets on subqueue
  *      @dev: network device
  *      @queue_index: sub queue index
  *
  * Resume individual transmit queue of a device with multiple transmit queues.
  */
 void netif_wake_subqueue(struct net_device *dev, u16 queue_index)
 {
         struct netdev_queue *txq = netdev_get_tx_queue(dev, queue_index);
 
         if (test_and_clear_bit(__QUEUE_STATE_DRV_XOFF, &txq->state)) {
                 struct Qdisc *q;
 
                 rcu_read_lock();
                 q = rcu_dereference(txq->qdisc);
                 __netif_schedule(q);
                 rcu_read_unlock();
         }
 }
 EXPORT_SYMBOL(netif_wake_subqueue);
 
 void netif_tx_wake_queue(struct netdev_queue *dev_queue)
 {
         if (test_and_clear_bit(__QUEUE_STATE_DRV_XOFF, &dev_queue->state)) {
                 struct Qdisc *q;
 
                 rcu_read_lock();
                 q = rcu_dereference(dev_queue->qdisc);
                 __netif_schedule(q);
                 rcu_read_unlock();
         }
 }
 EXPORT_SYMBOL(netif_tx_wake_queue);
 
 void __dev_kfree_skb_irq(struct sk_buff *skb, enum skb_free_reason reason)
 {
         unsigned long flags;
 
         if (likely(atomic_read(&skb->users) == 1)) {
                 smp_rmb();
                 atomic_set(&skb->users, 0);
         } else if (likely(!atomic_dec_and_test(&skb->users))) {
                 return;
         }
         get_kfree_skb_cb(skb)->reason = reason;
         local_irq_save(flags);
         skb->next = __this_cpu_read(softnet_data.completion_queue);
         __this_cpu_write(softnet_data.completion_queue, skb);
         raise_softirq_irqoff(NET_TX_SOFTIRQ);
         local_irq_restore(flags);
 }
 EXPORT_SYMBOL(__dev_kfree_skb_irq);
 
 void __dev_kfree_skb_any(struct sk_buff *skb, enum skb_free_reason reason)
 {
         if (in_irq() || irqs_disabled())
                 __dev_kfree_skb_irq(skb, reason);
         else
                 dev_kfree_skb(skb);
 }
 EXPORT_SYMBOL(__dev_kfree_skb_any);
 
 
 /**
  * netif_device_detach - mark device as removed
  * @dev: network device
  *
  * Mark device as removed from system and therefore no longer available.
  */
 void netif_device_detach(struct net_device *dev)
 {
         if (test_and_clear_bit(__LINK_STATE_PRESENT, &dev->state) &&
             netif_running(dev)) {
                 netif_tx_stop_all_queues(dev);
         }
 }
 EXPORT_SYMBOL(netif_device_detach);
 
 /**
  * netif_device_attach - mark device as attached
  * @dev: network device
  *
  * Mark device as attached from system and restart if needed.
  */
 void netif_device_attach(struct net_device *dev)
 {
         if (!test_and_set_bit(__LINK_STATE_PRESENT, &dev->state) &&
             netif_running(dev)) {
                 netif_tx_wake_all_queues(dev);
                 __netdev_watchdog_up(dev);
         }
 }
 EXPORT_SYMBOL(netif_device_attach);
 
 static void skb_warn_bad_offload(const struct sk_buff *skb)
 {
         static const netdev_features_t null_features = 0;
         struct net_device *dev = skb->dev;
         const char *driver = "";
 
         if (!net_ratelimit())
                 return;
 
         if (dev && dev->dev.parent)
                 driver = dev_driver_string(dev->dev.parent);
 
         WARN(1, "%s: caps=(%pNF, %pNF) len=%d data_len=%d gso_size=%d "
              "gso_type=%d ip_summed=%d\n",
              driver, dev ? &dev->features : &null_features,
              skb->sk ? &skb->sk->sk_route_caps : &null_features,
              skb->len, skb->data_len, skb_shinfo(skb)->gso_size,
              skb_shinfo(skb)->gso_type, skb->ip_summed);
 }
 
 /*
  * Invalidate hardware checksum when packet is to be mangled, and
  * complete checksum manually on outgoing path.
  */
 int skb_checksum_help(struct sk_buff *skb)
 {
         __wsum csum;
         int ret = 0, offset;
 
         if (skb->ip_summed == CHECKSUM_COMPLETE)
                 goto out_set_summed;
 
         if (unlikely(skb_shinfo(skb)->gso_size)) {
                 skb_warn_bad_offload(skb);
                 return -EINVAL;
         }
 
         /* Before computing a checksum, we should make sure no frag could
          * be modified by an external entity : checksum could be wrong.
          */
         if (skb_has_shared_frag(skb)) {
                 ret = __skb_linearize(skb);
                 if (ret)
                         goto out;
         }
 
         offset = skb_checksum_start_offset(skb);
         BUG_ON(offset >= skb_headlen(skb));
         csum = skb_checksum(skb, offset, skb->len - offset, 0);
 
         offset += skb->csum_offset;
         BUG_ON(offset + sizeof(__sum16) > skb_headlen(skb));
 
         if (skb_cloned(skb) &&
             !skb_clone_writable(skb, offset + sizeof(__sum16))) {
                 ret = pskb_expand_head(skb, 0, 0, GFP_ATOMIC);
                 if (ret)
                         goto out;
         }
 
         *(__sum16 *)(skb->data + offset) = csum_fold(csum);
 out_set_summed:
         skb->ip_summed = CHECKSUM_NONE;
 out:
         return ret;
 }
 EXPORT_SYMBOL(skb_checksum_help);
 
 __be16 skb_network_protocol(struct sk_buff *skb, int *depth)
 {
         __be16 type = skb->protocol;
 
         /* Tunnel gso handlers can set protocol to ethernet. */
         if (type == htons(ETH_P_TEB)) {
                 struct ethhdr *eth;
 
                 if (unlikely(!pskb_may_pull(skb, sizeof(struct ethhdr))))
                         return 0;
 
                 eth = (struct ethhdr *)skb_mac_header(skb);
                 type = eth->h_proto;
         }
 
         return __vlan_get_protocol(skb, type, depth);
 }
 
 /**
  *      skb_mac_gso_segment - mac layer segmentation handler.
  *      @skb: buffer to segment
  *      @features: features for the output path (see dev->features)
  */
 struct sk_buff *skb_mac_gso_segment(struct sk_buff *skb,
                                     netdev_features_t features)
 {
         struct sk_buff *segs = ERR_PTR(-EPROTONOSUPPORT);
         struct packet_offload *ptype;
         int vlan_depth = skb->mac_len;
         __be16 type = skb_network_protocol(skb, &vlan_depth);
 
         if (unlikely(!type))
                 return ERR_PTR(-EINVAL);
 
         __skb_pull(skb, vlan_depth);
 
         rcu_read_lock();
         list_for_each_entry_rcu(ptype, &offload_base, list) {
                 if (ptype->type == type && ptype->callbacks.gso_segment) {
                         segs = ptype->callbacks.gso_segment(skb, features);
                         break;
                 }
         }
         rcu_read_unlock();
 
         __skb_push(skb, skb->data - skb_mac_header(skb));
 
         return segs;
 }
 EXPORT_SYMBOL(skb_mac_gso_segment);
 
 
 /* openvswitch calls this on rx path, so we need a different check.
  */
 static inline bool skb_needs_check(struct sk_buff *skb, bool tx_path)
 {
         if (tx_path)
                 return skb->ip_summed != CHECKSUM_PARTIAL;
         else
                 return skb->ip_summed == CHECKSUM_NONE;
 }
 
 /**
  *      __skb_gso_segment - Perform segmentation on skb.
  *      @skb: buffer to segment
  *      @features: features for the output path (see dev->features)
  *      @tx_path: whether it is called in TX path
  *
  *      This function segments the given skb and returns a list of segments.
  *
  *      It may return NULL if the skb requires no segmentation.  This is
  *      only possible when GSO is used for verifying header integrity.
  */
 struct sk_buff *__skb_gso_segment(struct sk_buff *skb,
                                   netdev_features_t features, bool tx_path)
 {
         if (unlikely(skb_needs_check(skb, tx_path))) {
                 int err;
 
                 skb_warn_bad_offload(skb);
 
                 err = skb_cow_head(skb, 0);
                 if (err < 0)
                         return ERR_PTR(err);
         }
 
         SKB_GSO_CB(skb)->mac_offset = skb_headroom(skb);
         SKB_GSO_CB(skb)->encap_level = 0;
 
         skb_reset_mac_header(skb);
         skb_reset_mac_len(skb);
 
         return skb_mac_gso_segment(skb, features);
 }
 EXPORT_SYMBOL(__skb_gso_segment);
 
 /* Take action when hardware reception checksum errors are detected. */
 #ifdef CONFIG_BUG
 void netdev_rx_csum_fault(struct net_device *dev)
 {
         if (net_ratelimit()) {
                 pr_err("%s: hw csum failure\n", dev ? dev->name : "<unknown>");
                 dump_stack();
         }
 }
 EXPORT_SYMBOL(netdev_rx_csum_fault);
 #endif
 
 /* Actually, we should eliminate this check as soon as we know, that:
  * 1. IOMMU is present and allows to map all the memory.
  * 2. No high memory really exists on this machine.
  */
 
 static int illegal_highdma(struct net_device *dev, struct sk_buff *skb)
 {
 #ifdef CONFIG_HIGHMEM
         int i;
         if (!(dev->features & NETIF_F_HIGHDMA)) {
                 for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
                         skb_frag_t *frag = &skb_shinfo(skb)->frags[i];
                         if (PageHighMem(skb_frag_page(frag)))
                                 return 1;
                 }
         }
 
         if (PCI_DMA_BUS_IS_PHYS) {
                 struct device *pdev = dev->dev.parent;
 
                 if (!pdev)
                         return 0;
                 for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
                         skb_frag_t *frag = &skb_shinfo(skb)->frags[i];
                         dma_addr_t addr = page_to_phys(skb_frag_page(frag));
                         if (!pdev->dma_mask || addr + PAGE_SIZE - 1 > *pdev->dma_mask)
                                 return 1;
                 }
         }
 #endif
         return 0;
 }
 
 /* If MPLS offload request, verify we are testing hardware MPLS features
  * instead of standard features for the netdev.
  */
 #if IS_ENABLED(CONFIG_NET_MPLS_GSO)
 static netdev_features_t net_mpls_features(struct sk_buff *skb,
                                            netdev_features_t features,
                                            __be16 type)
 {
         if (eth_p_mpls(type))
                 features &= skb->dev->mpls_features;
 
         return features;
 }
 #else
 static netdev_features_t net_mpls_features(struct sk_buff *skb,
                                            netdev_features_t features,
                                            __be16 type)
 {
         return features;
 }
 #endif
 
 static netdev_features_t harmonize_features(struct sk_buff *skb,
         netdev_features_t features)
 {
         int tmp;
         __be16 type;
 
         type = skb_network_protocol(skb, &tmp);
         features = net_mpls_features(skb, features, type);
 
         if (skb->ip_summed != CHECKSUM_NONE &&
             !can_checksum_protocol(features, type)) {
                 features &= ~NETIF_F_ALL_CSUM;
         } else if (illegal_highdma(skb->dev, skb)) {
                 features &= ~NETIF_F_SG;
         }
 
         return features;
 }
 
 netdev_features_t passthru_features_check(struct sk_buff *skb,
                                           struct net_device *dev,
                                           netdev_features_t features)
 {
         return features;
 }
 EXPORT_SYMBOL(passthru_features_check);
 
 static netdev_features_t dflt_features_check(const struct sk_buff *skb,
                                              struct net_device *dev,
                                              netdev_features_t features)
 {
         return vlan_features_check(skb, features);
 }
 
 netdev_features_t netif_skb_features(struct sk_buff *skb)
 {
         struct net_device *dev = skb->dev;
         netdev_features_t features = dev->features;
         u16 gso_segs = skb_shinfo(skb)->gso_segs;
 
         if (gso_segs > dev->gso_max_segs || gso_segs < dev->gso_min_segs)
                 features &= ~NETIF_F_GSO_MASK;
 
         /* If encapsulation offload request, verify we are testing
          * hardware encapsulation features instead of standard
          * features for the netdev
          */
         if (skb->encapsulation)
                 features &= dev->hw_enc_features;
 
         if (skb_vlan_tagged(skb))
                 features = netdev_intersect_features(features,
                                                      dev->vlan_features |
                                                      NETIF_F_HW_VLAN_CTAG_TX |
                                                      NETIF_F_HW_VLAN_STAG_TX);
 
         if (dev->netdev_ops->ndo_features_check)
                 features &= dev->netdev_ops->ndo_features_check(skb, dev,
                                                                 features);
         else
                 features &= dflt_features_check(skb, dev, features);
 
         return harmonize_features(skb, features);
 }
 EXPORT_SYMBOL(netif_skb_features);
 
 static int xmit_one(struct sk_buff *skb, struct net_device *dev,
                     struct netdev_queue *txq, bool more)
 {
         unsigned int len;
         int rc;
 
         if (!list_empty(&ptype_all) || !list_empty(&dev->ptype_all))
                 dev_queue_xmit_nit(skb, dev);
 
         len = skb->len;
         trace_net_dev_start_xmit(skb, dev);
         rc = netdev_start_xmit(skb, dev, txq, more);
         trace_net_dev_xmit(skb, rc, dev, len);
 
         return rc;
 }
 
 struct sk_buff *dev_hard_start_xmit(struct sk_buff *first, struct net_device *dev,
                                     struct netdev_queue *txq, int *ret)
 {
         struct sk_buff *skb = first;
         int rc = NETDEV_TX_OK;
 
         while (skb) {
                 struct sk_buff *next = skb->next;
 
                 skb->next = NULL;
                 rc = xmit_one(skb, dev, txq, next != NULL);
                 if (unlikely(!dev_xmit_complete(rc))) {
                         skb->next = next;
                         goto out;
                 }
 
                 skb = next;
                //驱动通过 netif_xmit_stopped(txq)
                //通知高层停止发送数据给驱动
                 if (netif_xmit_stopped(txq) && skb) {
                         rc = NETDEV_TX_BUSY;
                         break;
                 }
         }
 
 out:
         *ret = rc;
         return skb;
 }
 
 static struct sk_buff *validate_xmit_vlan(struct sk_buff *skb,
                                           netdev_features_t features)
 {
         if (skb_vlan_tag_present(skb) &&
             !vlan_hw_offload_capable(features, skb->vlan_proto))
                 skb = __vlan_hwaccel_push_inside(skb);
         return skb;
 }
 
 static struct sk_buff *validate_xmit_skb(struct sk_buff *skb, struct net_device *dev)
 {
         netdev_features_t features;
 
         if (skb->next)
                 return skb;
 
         features = netif_skb_features(skb);
         skb = validate_xmit_vlan(skb, features);
         if (unlikely(!skb))
                 goto out_null;
 
         if (netif_needs_gso(skb, features)) {
                 struct sk_buff *segs;
 
                 segs = skb_gso_segment(skb, features);
                 if (IS_ERR(segs)) {
                         goto out_kfree_skb;
                 } else if (segs) {
                         consume_skb(skb);
                         skb = segs;
                 }
         } else {
                 if (skb_needs_linearize(skb, features) &&
                     __skb_linearize(skb))
                         goto out_kfree_skb;
 
                 /* If packet is not checksummed and device does not
                  * support checksumming for this protocol, complete
                  * checksumming here.
                  */
                 if (skb->ip_summed == CHECKSUM_PARTIAL) {
                         if (skb->encapsulation)
                                 skb_set_inner_transport_header(skb,
                                                                skb_checksum_start_offset(skb));
                         else
                                 skb_set_transport_header(skb,
                                                          skb_checksum_start_offset(skb));
                         if (!(features & NETIF_F_ALL_CSUM) &&
                             skb_checksum_help(skb))
                                 goto out_kfree_skb;
                 }
         }
 
         return skb;
 
 out_kfree_skb:
         kfree_skb(skb);
 out_null:
         return NULL;
 }
 
 struct sk_buff *validate_xmit_skb_list(struct sk_buff *skb, struct net_device *dev)
 {
         struct sk_buff *next, *head = NULL, *tail;
 
         for (; skb != NULL; skb = next) {
                 next = skb->next;
                 skb->next = NULL;
 
                 /* in case skb wont be segmented, point to itself */
                 skb->prev = skb;
 
                 skb = validate_xmit_skb(skb, dev);
                 if (!skb)
                         continue;
 
                 if (!head)
                         head = skb;
                 else
                         tail->next = skb;
                 /* If skb was segmented, skb->prev points to
                  * the last segment. If not, it still contains skb.
                  */
                 tail = skb->prev;
         }
         return head;
 }
 
 static void qdisc_pkt_len_init(struct sk_buff *skb)
 {
         const struct skb_shared_info *shinfo = skb_shinfo(skb);
 
         qdisc_skb_cb(skb)->pkt_len = skb->len;
 
         /* To get more precise estimation of bytes sent on wire,
          * we add to pkt_len the headers size of all segments
          */
         if (shinfo->gso_size)  {
                 unsigned int hdr_len;
                 u16 gso_segs = shinfo->gso_segs;
 
                 /* mac layer + network layer */
                 hdr_len = skb_transport_header(skb) - skb_mac_header(skb);
 
                 /* + transport layer */
                 if (likely(shinfo->gso_type & (SKB_GSO_TCPV4 | SKB_GSO_TCPV6)))
                         hdr_len += tcp_hdrlen(skb);
                 else
                         hdr_len += sizeof(struct udphdr);
 
                 if (shinfo->gso_type & SKB_GSO_DODGY)
                         gso_segs = DIV_ROUND_UP(skb->len - hdr_len,
                                                 shinfo->gso_size);
 
                 qdisc_skb_cb(skb)->pkt_len += (gso_segs - 1) * hdr_len;
         }
 }
 
 static inline int __dev_xmit_skb(struct sk_buff *skb, struct Qdisc *q,
                                  struct net_device *dev,
                                  struct netdev_queue *txq)
 {
         spinlock_t *root_lock = qdisc_lock(q);
         bool contended;
         int rc;
 
         qdisc_pkt_len_init(skb);
         qdisc_calculate_pkt_len(skb, q);
         /*
          * Heuristic to force contended enqueues to serialize on a
          * separate lock before trying to get qdisc main lock.
          * This permits __QDISC___STATE_RUNNING owner to get the lock more
          * often and dequeue packets faster.
          */
         contended = qdisc_is_running(q);
         if (unlikely(contended))
                 spin_lock(&q->busylock);
 
         spin_lock(root_lock);
         if (unlikely(test_bit(__QDISC_STATE_DEACTIVATED, &q->state))) {
                 kfree_skb(skb);
                 rc = NET_XMIT_DROP;
         } else if ((q->flags & TCQ_F_CAN_BYPASS) && !qdisc_qlen(q) &&
                    qdisc_run_begin(q)) {
                 /*
                  * This is a work-conserving queue; there are no old skbs
                  * waiting to be sent out; and the qdisc is not running -
                  * xmit the skb directly.
                  */
 
                 qdisc_bstats_update(q, skb);
 
                 if (sch_direct_xmit(skb, q, dev, txq, root_lock, true)) {
                         if (unlikely(contended)) {
                                 spin_unlock(&q->busylock);
                                 contended = false;
                         }
                         __qdisc_run(q);
                 } else
                         qdisc_run_end(q);
 
                 rc = NET_XMIT_SUCCESS;
         } else {
                 rc = q->enqueue(skb, q) & NET_XMIT_MASK;
                 if (qdisc_run_begin(q)) {
                         if (unlikely(contended)) {
                                 spin_unlock(&q->busylock);
                                 contended = false;
                         }
                         __qdisc_run(q);
                 }
         }
         spin_unlock(root_lock);
         if (unlikely(contended))
                 spin_unlock(&q->busylock);
         return rc;
 }
 
 #if IS_ENABLED(CONFIG_CGROUP_NET_PRIO)
 static void skb_update_prio(struct sk_buff *skb)
 {
         struct netprio_map *map = rcu_dereference_bh(skb->dev->priomap);
 
         if (!skb->priority && skb->sk && map) {
                 unsigned int prioidx = skb->sk->sk_cgrp_prioidx;
 
                 if (prioidx < map->priomap_len)
                         skb->priority = map->priomap[prioidx];
         }
 }
 #else
 #define skb_update_prio(skb)
 #endif
 
 DEFINE_PER_CPU(int, xmit_recursion);
 EXPORT_SYMBOL(xmit_recursion);
 
 #define RECURSION_LIMIT 10
 
 /**
  *      dev_loopback_xmit - loop back @skb
  *      @skb: buffer to transmit
  */
 int dev_loopback_xmit(struct sock *sk, struct sk_buff *skb)
 {
         skb_reset_mac_header(skb);
         __skb_pull(skb, skb_network_offset(skb));
         skb->pkt_type = PACKET_LOOPBACK;
         skb->ip_summed = CHECKSUM_UNNECESSARY;
         WARN_ON(!skb_dst(skb));
         skb_dst_force(skb);
         netif_rx_ni(skb);
         return 0;
 }
 EXPORT_SYMBOL(dev_loopback_xmit);
 
 /**
  *      __dev_queue_xmit - transmit a buffer
  *      @skb: buffer to transmit
  *      @accel_priv: private data used for L2 forwarding offload
  *
  *      Queue a buffer for transmission to a network device. The caller must
  *      have set the device and priority and built the buffer before calling
  *      this function. The function can be called from an interrupt.
  *
  *      A negative errno code is returned on a failure. A success does not
  *      guarantee the frame will be transmitted as it may be dropped due
  *      to congestion or traffic shaping.
  *
  * -----------------------------------------------------------------------------------
  *      I notice this method can also return errors from the queue disciplines,
  *      including NET_XMIT_DROP, which is a positive value.  So, errors can also
  *      be positive.
  *
  *      Regardless of the return value, the skb is consumed, so it is currently
  *      difficult to retry a send to this method.  (You can bump the ref count
  *      before sending to hold a reference for retry if you are careful.)
  *
  *      When calling this method, interrupts MUST be enabled.  This is because
  *      the BH enable code must have IRQs enabled so that it will not deadlock.
  *          --BLG
  */
 static int __dev_queue_xmit(struct sk_buff *skb, void *accel_priv)
 {
         struct net_device *dev = skb->dev;
         struct netdev_queue *txq;
         struct Qdisc *q;
         int rc = -ENOMEM;
 
         skb_reset_mac_header(skb);
 
         if (unlikely(skb_shinfo(skb)->tx_flags & SKBTX_SCHED_TSTAMP))
                 __skb_tstamp_tx(skb, NULL, skb->sk, SCM_TSTAMP_SCHED);
 
         /* Disable soft irqs for various locks below. Also
          * stops preemption for RCU.
          */
         rcu_read_lock_bh();
 
         skb_update_prio(skb);
 
         /* If device/qdisc don't need skb->dst, release it right now while
          * its hot in this cpu cache.
          */
         if (dev->priv_flags & IFF_XMIT_DST_RELEASE)
                 skb_dst_drop(skb);
         else
                 skb_dst_force(skb);
 
         txq = netdev_pick_tx(dev, skb, accel_priv);
         q = rcu_dereference_bh(txq->qdisc);
 
 #ifdef CONFIG_NET_CLS_ACT
         skb->tc_verd = SET_TC_AT(skb->tc_verd, AT_EGRESS);
 #endif
         trace_net_dev_queue(skb);
         if (q->enqueue) {
                 rc = __dev_xmit_skb(skb, q, dev, txq);
                 goto out;
         }
 
         /* The device has no queue. Common case for software devices:
            loopback, all the sorts of tunnels...
 
            Really, it is unlikely that netif_tx_lock protection is necessary
            here.  (f.e. loopback and IP tunnels are clean ignoring statistics
            counters.)
            However, it is possible, that they rely on protection
            made by us here.
 
            Check this and shot the lock. It is not prone from deadlocks.
            Either shot noqueue qdisc, it is even simpler 8)
          */
         if (dev->flags & IFF_UP) {
                 int cpu = smp_processor_id(); /* ok because BHs are off */
 
                 if (txq->xmit_lock_owner != cpu) {
 
                         if (__this_cpu_read(xmit_recursion) > RECURSION_LIMIT)
                                 goto recursion_alert;
 
                         skb = validate_xmit_skb(skb, dev);
                         if (!skb)
                                 goto drop;
 
                         HARD_TX_LOCK(dev, txq, cpu);
 
                         //驱动通过 netif_xmit_stopped(txq)
                         //通知高层停止发送数据给驱动
                         if (!netif_xmit_stopped(txq)) {
                                 __this_cpu_inc(xmit_recursion);
                                 skb = dev_hard_start_xmit(skb, dev, txq, &rc);
                                 __this_cpu_dec(xmit_recursion);
                                 if (dev_xmit_complete(rc)) {
                                         HARD_TX_UNLOCK(dev, txq);
                                         goto out;
                                 }
                         }
                         HARD_TX_UNLOCK(dev, txq);
                         net_crit_ratelimited("Virtual device %s asks to queue packet!\n",
                                              dev->name);
                 } else {
                         /* Recursion is detected! It is possible,
                          * unfortunately
                          */
 recursion_alert:
                         net_crit_ratelimited("Dead loop on virtual device %s, fix it urgently!\n",
                                              dev->name);
                 }
         }
 
         rc = -ENETDOWN;
 drop:
         rcu_read_unlock_bh();
 
         atomic_long_inc(&dev->tx_dropped);
         kfree_skb_list(skb);
         return rc;
 out:
         rcu_read_unlock_bh();
         return rc;
 }
 
 int dev_queue_xmit_sk(struct sock *sk, struct sk_buff *skb)
 {
         return __dev_queue_xmit(skb, NULL);
 }
 EXPORT_SYMBOL(dev_queue_xmit_sk);
 
 int dev_queue_xmit_accel(struct sk_buff *skb, void *accel_priv)
 {
         return __dev_queue_xmit(skb, accel_priv);
 }
 EXPORT_SYMBOL(dev_queue_xmit_accel);
 
 
 /*=======================================================================
                         Receiver routines
   =======================================================================*/
 
 int netdev_max_backlog __read_mostly = 1000;
 EXPORT_SYMBOL(netdev_max_backlog);
 
 int netdev_tstamp_prequeue __read_mostly = 1;
 int netdev_budget __read_mostly = 300;
 int weight_p __read_mostly = 64;            /* old backlog weight */
 
 /* Called with irq disabled */
 static inline void ____napi_schedule(struct softnet_data *sd,
                                      struct napi_struct *napi)
 {
         list_add_tail(&napi->poll_list, &sd->poll_list);
         __raise_softirq_irqoff(NET_RX_SOFTIRQ);
 }
 
 #ifdef CONFIG_RPS
 
 /* One global table that all flow-based protocols share. */
 struct rps_sock_flow_table __rcu *rps_sock_flow_table __read_mostly;
 EXPORT_SYMBOL(rps_sock_flow_table);
 u32 rps_cpu_mask __read_mostly;
 EXPORT_SYMBOL(rps_cpu_mask);
 
 struct static_key rps_needed __read_mostly;
 
 static struct rps_dev_flow *
 set_rps_cpu(struct net_device *dev, struct sk_buff *skb,
             struct rps_dev_flow *rflow, u16 next_cpu)
 {
         if (next_cpu < nr_cpu_ids) {
 #ifdef CONFIG_RFS_ACCEL
                 struct netdev_rx_queue *rxqueue;
                 struct rps_dev_flow_table *flow_table;
                 struct rps_dev_flow *old_rflow;
                 u32 flow_id;
                 u16 rxq_index;
                 int rc;
 
                 /* Should we steer this flow to a different hardware queue? */
                 if (!skb_rx_queue_recorded(skb) || !dev->rx_cpu_rmap ||
                     !(dev->features & NETIF_F_NTUPLE))
                         goto out;
                 rxq_index = cpu_rmap_lookup_index(dev->rx_cpu_rmap, next_cpu);
                 if (rxq_index == skb_get_rx_queue(skb))
                         goto out;
 
                 rxqueue = dev->_rx + rxq_index;
                 flow_table = rcu_dereference(rxqueue->rps_flow_table);
                 if (!flow_table)
                         goto out;
                 flow_id = skb_get_hash(skb) & flow_table->mask;
                 rc = dev->netdev_ops->ndo_rx_flow_steer(dev, skb,
                                                         rxq_index, flow_id);
                 if (rc < 0)
                         goto out;
                 old_rflow = rflow;
                 rflow = &flow_table->flows[flow_id];
                 rflow->filter = rc;
                 if (old_rflow->filter == rflow->filter)
                         old_rflow->filter = RPS_NO_FILTER;
         out:
 #endif
                 rflow->last_qtail =
                         per_cpu(softnet_data, next_cpu).input_queue_head;
         }
 
         rflow->cpu = next_cpu;
         return rflow;
 }
 
 /*
  * get_rps_cpu is called from netif_receive_skb and returns the target
  * CPU from the RPS map of the receiving queue for a given skb.
  * rcu_read_lock must be held on entry.
  */
 static int get_rps_cpu(struct net_device *dev, struct sk_buff *skb,
                        struct rps_dev_flow **rflowp)
 {
         const struct rps_sock_flow_table *sock_flow_table;
         struct netdev_rx_queue *rxqueue = dev->_rx;
         struct rps_dev_flow_table *flow_table;
         struct rps_map *map;
         int cpu = -1;
         u32 tcpu;
         u32 hash;
 
         if (skb_rx_queue_recorded(skb)) {
                 u16 index = skb_get_rx_queue(skb);
 
                 if (unlikely(index >= dev->real_num_rx_queues)) {
                         WARN_ONCE(dev->real_num_rx_queues > 1,
                                   "%s received packet on queue %u, but number "
                                   "of RX queues is %u\n",
                                   dev->name, index, dev->real_num_rx_queues);
                         goto done;
                 }
                 rxqueue += index;
         }
 
         /* Avoid computing hash if RFS/RPS is not active for this rxqueue */
 
         flow_table = rcu_dereference(rxqueue->rps_flow_table);
         map = rcu_dereference(rxqueue->rps_map);
         if (!flow_table && !map)
                 goto done;
 
         skb_reset_network_header(skb);
         hash = skb_get_hash(skb);
         if (!hash)
                 goto done;
 
         sock_flow_table = rcu_dereference(rps_sock_flow_table);
         if (flow_table && sock_flow_table) {
                 struct rps_dev_flow *rflow;
                 u32 next_cpu;
                 u32 ident;
 
                 /* First check into global flow table if there is a match */
                 ident = sock_flow_table->ents[hash & sock_flow_table->mask];
                 if ((ident ^ hash) & ~rps_cpu_mask)
                         goto try_rps;
 
                 next_cpu = ident & rps_cpu_mask;
 
                 /* OK, now we know there is a match,
                  * we can look at the local (per receive queue) flow table
                  */
                 rflow = &flow_table->flows[hash & flow_table->mask];
                 tcpu = rflow->cpu;
 
                 /*
                  * If the desired CPU (where last recvmsg was done) is
                  * different from current CPU (one in the rx-queue flow
                  * table entry), switch if one of the following holds:
                  *   - Current CPU is unset (>= nr_cpu_ids).
                  *   - Current CPU is offline.
                  *   - The current CPU's queue tail has advanced beyond the
                  *     last packet that was enqueued using this table entry.
                  *     This guarantees that all previous packets for the flow
                  *     have been dequeued, thus preserving in order delivery.
                  */
                 if (unlikely(tcpu != next_cpu) &&
                     (tcpu >= nr_cpu_ids || !cpu_online(tcpu) ||
                      ((int)(per_cpu(softnet_data, tcpu).input_queue_head -
                       rflow->last_qtail)) >= 0)) {
                         tcpu = next_cpu;
                         rflow = set_rps_cpu(dev, skb, rflow, next_cpu);
                 }
 
                 if (tcpu < nr_cpu_ids && cpu_online(tcpu)) {
                         *rflowp = rflow;
                         cpu = tcpu;
                         goto done;
                 }
         }
 
 try_rps:
 
         if (map) {
                 tcpu = map->cpus[reciprocal_scale(hash, map->len)];
                 if (cpu_online(tcpu)) {
                         cpu = tcpu;
                         goto done;
                 }
         }
 
 done:
         return cpu;
 }
 
 #ifdef CONFIG_RFS_ACCEL
 
 /**
  * rps_may_expire_flow - check whether an RFS hardware filter may be removed
  * @dev: Device on which the filter was set
  * @rxq_index: RX queue index
  * @flow_id: Flow ID passed to ndo_rx_flow_steer()
  * @filter_id: Filter ID returned by ndo_rx_flow_steer()
  *
  * Drivers that implement ndo_rx_flow_steer() should periodically call
  * this function for each installed filter and remove the filters for
  * which it returns %true.
  */
 bool rps_may_expire_flow(struct net_device *dev, u16 rxq_index,
                          u32 flow_id, u16 filter_id)
 {
         struct netdev_rx_queue *rxqueue = dev->_rx + rxq_index;
         struct rps_dev_flow_table *flow_table;
         struct rps_dev_flow *rflow;
         bool expire = true;
         unsigned int cpu;
 
         rcu_read_lock();
         flow_table = rcu_dereference(rxqueue->rps_flow_table);
         if (flow_table && flow_id <= flow_table->mask) {
                 rflow = &flow_table->flows[flow_id];
                 cpu = ACCESS_ONCE(rflow->cpu);
                 if (rflow->filter == filter_id && cpu < nr_cpu_ids &&
                     ((int)(per_cpu(softnet_data, cpu).input_queue_head -
                            rflow->last_qtail) <
                      (int)(10 * flow_table->mask)))
                         expire = false;
         }
         rcu_read_unlock();
         return expire;
 }
 EXPORT_SYMBOL(rps_may_expire_flow);
 
 #endif /* CONFIG_RFS_ACCEL */
 
 /* Called from hardirq (IPI) context */
 static void rps_trigger_softirq(void *data)
 {
         struct softnet_data *sd = data;
 
         ____napi_schedule(sd, &sd->backlog);
         sd->received_rps++;
 }
 
 #endif /* CONFIG_RPS */
 
 /*
  * Check if this softnet_data structure is another cpu one
  * If yes, queue it to our IPI list and return 1
  * If no, return 0
  */
 static int rps_ipi_queued(struct softnet_data *sd)
 {
 #ifdef CONFIG_RPS
         struct softnet_data *mysd = this_cpu_ptr(&softnet_data);
 
         if (sd != mysd) {
                 sd->rps_ipi_next = mysd->rps_ipi_list;
                 mysd->rps_ipi_list = sd;
 
                 __raise_softirq_irqoff(NET_RX_SOFTIRQ);
                 return 1;
         }
 #endif /* CONFIG_RPS */
         return 0;
 }
 
 #ifdef CONFIG_NET_FLOW_LIMIT
 int netdev_flow_limit_table_len __read_mostly = (1 << 12);
 #endif
 
 static bool skb_flow_limit(struct sk_buff *skb, unsigned int qlen)
 {
 #ifdef CONFIG_NET_FLOW_LIMIT
         struct sd_flow_limit *fl;
         struct softnet_data *sd;
         unsigned int old_flow, new_flow;
 
         if (qlen < (netdev_max_backlog >> 1))
                 return false;
 
         sd = this_cpu_ptr(&softnet_data);
 
         rcu_read_lock();
         fl = rcu_dereference(sd->flow_limit);
         if (fl) {
                 new_flow = skb_get_hash(skb) & (fl->num_buckets - 1);
                 old_flow = fl->history[fl->history_head];
                 fl->history[fl->history_head] = new_flow;
 
                 fl->history_head++;
                 fl->history_head &= FLOW_LIMIT_HISTORY - 1;
 
                 if (likely(fl->buckets[old_flow]))
                         fl->buckets[old_flow]--;
 
                 if (++fl->buckets[new_flow] > (FLOW_LIMIT_HISTORY >> 1)) {
                         fl->count++;
                         rcu_read_unlock();
                         return true;
                 }
         }
         rcu_read_unlock();
 #endif
         return false;
 }
 
 /*
  * enqueue_to_backlog is called to queue an skb to a per CPU backlog
  * queue (may be a remote CPU queue).
  */
 static int enqueue_to_backlog(struct sk_buff *skb, int cpu,
                               unsigned int *qtail)
 {
         struct softnet_data *sd;
         unsigned long flags;
         unsigned int qlen;
 
         sd = &per_cpu(softnet_data, cpu);
 
         local_irq_save(flags);
 
         rps_lock(sd);
         qlen = skb_queue_len(&sd->input_pkt_queue);
         if (qlen <= netdev_max_backlog && !skb_flow_limit(skb, qlen)) {
                 if (qlen) {
 enqueue:
                         //加入 sd->input_pkt_queue 中 sd 为 CPU ID 为 cpu 的 softnet_data
                         __skb_queue_tail(&sd->input_pkt_queue, skb);
                         input_queue_tail_incr_save(sd, qtail);
                         rps_unlock(sd);
                         local_irq_restore(flags);
                         return NET_RX_SUCCESS;
                 }
 
                 /* Schedule NAPI for backlog device
                  * We can use non atomic operation since we own the queue lock
                  */
                 if (!__test_and_set_bit(NAPI_STATE_SCHED, &sd->backlog.state)) {
                         if (!rps_ipi_queued(sd))
                                 ____napi_schedule(sd, &sd->backlog);
                 }
                 goto enqueue;
         }
 
         sd->dropped++;
         rps_unlock(sd);
 
         local_irq_restore(flags);
 
         atomic_long_inc(&skb->dev->rx_dropped);
         kfree_skb(skb);
         return NET_RX_DROP;
 }
 
 static int netif_rx_internal(struct sk_buff *skb)
 {
         int ret;
 
         net_timestamp_check(netdev_tstamp_prequeue, skb);
 
         trace_netif_rx(skb);
 #ifdef CONFIG_RPS
         if (static_key_false(&rps_needed)) {
                 struct rps_dev_flow voidflow, *rflow = &voidflow;
                 int cpu;
 
                 preempt_disable();
                 rcu_read_lock();
 
                 cpu = get_rps_cpu(skb->dev, skb, &rflow);
                 if (cpu < 0)
                         cpu = smp_processor_id();
 
                 ret = enqueue_to_backlog(skb, cpu, &rflow->last_qtail);
 
                 rcu_read_unlock();
                 preempt_enable();
         } else
 #endif
         {
                 unsigned int qtail;
                 //将包放在中断所属的 CPU 的 softnet_data->input_pkt_queue 队列中
                 ret = enqueue_to_backlog(skb, get_cpu(), &qtail);
                 put_cpu();
         }
         return ret;
 }
 
 /**
  *      netif_rx        -       post buffer to the network code
  *      @skb: buffer to post
  *
  *      This function receives a packet from a device driver and queues it for
  *      the upper (protocol) levels to process.  It always succeeds. The buffer
  *      may be dropped during processing for congestion control or by the
  *      protocol layers.
  *
  *      return values:
  *      NET_RX_SUCCESS  (no congestion)
  *      NET_RX_DROP     (packet was dropped)
  *
  */
 
 int netif_rx(struct sk_buff *skb)
 {
         trace_netif_rx_entry(skb);
 
         return netif_rx_internal(skb);
 }
 EXPORT_SYMBOL(netif_rx);
 
 int netif_rx_ni(struct sk_buff *skb)
 {
         int err;
 
         trace_netif_rx_ni_entry(skb);
 
         preempt_disable();
         err = netif_rx_internal(skb);
         if (local_softirq_pending())
                 do_softirq();
         preempt_enable();
 
         return err;
 }
 EXPORT_SYMBOL(netif_rx_ni);
 
 static void net_tx_action(struct softirq_action *h)
 {
         struct softnet_data *sd = this_cpu_ptr(&softnet_data);
 
         if (sd->completion_queue) {
                 struct sk_buff *clist;
 
                 local_irq_disable();
                 clist = sd->completion_queue;
                 sd->completion_queue = NULL;
                 local_irq_enable();
 
                 while (clist) {
                         struct sk_buff *skb = clist;
                         clist = clist->next;
 
                         WARN_ON(atomic_read(&skb->users));
                         if (likely(get_kfree_skb_cb(skb)->reason == SKB_REASON_CONSUMED))
                                 trace_consume_skb(skb);
                         else
                                 trace_kfree_skb(skb, net_tx_action);
                         __kfree_skb(skb);
                 }
         }
 
         if (sd->output_queue) {
                 struct Qdisc *head;
 
                 local_irq_disable();
                 head = sd->output_queue;
                 sd->output_queue = NULL;
                 sd->output_queue_tailp = &sd->output_queue;
                 local_irq_enable();
 
                 while (head) {
                         struct Qdisc *q = head;
                         spinlock_t *root_lock;
 
                         head = head->next_sched;
 
                         root_lock = qdisc_lock(q);
                         if (spin_trylock(root_lock)) {
                                 smp_mb__before_atomic();
                                 clear_bit(__QDISC_STATE_SCHED,
                                           &q->state);
                                 qdisc_run(q);
                                 spin_unlock(root_lock);
                         } else {
                                 if (!test_bit(__QDISC_STATE_DEACTIVATED,
                                               &q->state)) {
                                         __netif_reschedule(q);
                                 } else {
                                         smp_mb__before_atomic();
                                         clear_bit(__QDISC_STATE_SCHED,
                                                   &q->state);
                                 }
                         }
                 }
         }
 }
 
 #if (defined(CONFIG_BRIDGE) || defined(CONFIG_BRIDGE_MODULE)) && \
     (defined(CONFIG_ATM_LANE) || defined(CONFIG_ATM_LANE_MODULE))
 /* This hook is defined here for ATM LANE */
 int (*br_fdb_test_addr_hook)(struct net_device *dev,
                              unsigned char *addr) __read_mostly;
 EXPORT_SYMBOL_GPL(br_fdb_test_addr_hook);
 #endif
 
 #ifdef CONFIG_NET_CLS_ACT
 /* TODO: Maybe we should just force sch_ingress to be compiled in
  * when CONFIG_NET_CLS_ACT is? otherwise some useless instructions
  * a compare and 2 stores extra right now if we dont have it on
  * but have CONFIG_NET_CLS_ACT
  * NOTE: This doesn't stop any functionality; if you dont have
  * the ingress scheduler, you just can't add policies on ingress.
  *
  */
 static int ing_filter(struct sk_buff *skb, struct netdev_queue *rxq)
 {
         struct net_device *dev = skb->dev;
         u32 ttl = G_TC_RTTL(skb->tc_verd);
         int result = TC_ACT_OK;
         struct Qdisc *q;
 
         if (unlikely(MAX_RED_LOOP < ttl++)) {
                 net_warn_ratelimited("Redir loop detected Dropping packet (%d->%d)\n",
                                      skb->skb_iif, dev->ifindex);
                 return TC_ACT_SHOT;
         }
 
         skb->tc_verd = SET_TC_RTTL(skb->tc_verd, ttl);
         skb->tc_verd = SET_TC_AT(skb->tc_verd, AT_INGRESS);
 
         q = rcu_dereference(rxq->qdisc);
         if (q != &noop_qdisc) {
                 spin_lock(qdisc_lock(q));
                 if (likely(!test_bit(__QDISC_STATE_DEACTIVATED, &q->state)))
                         result = qdisc_enqueue_root(skb, q);
                 spin_unlock(qdisc_lock(q));
         }
 
         return result;
 }
 
 static inline struct sk_buff *handle_ing(struct sk_buff *skb,
                                          struct packet_type **pt_prev,
                                          int *ret, struct net_device *orig_dev)
 {
         struct netdev_queue *rxq = rcu_dereference(skb->dev->ingress_queue);
 
         if (!rxq || rcu_access_pointer(rxq->qdisc) == &noop_qdisc)
                 return skb;
 
         if (*pt_prev) {
                 *ret = deliver_skb(skb, *pt_prev, orig_dev);
                 *pt_prev = NULL;
         }
 
         switch (ing_filter(skb, rxq)) {
         case TC_ACT_SHOT:
         case TC_ACT_STOLEN:
                 kfree_skb(skb);
                 return NULL;
         }
 
         return skb;
 }
 #endif
 
 /**
  *      netdev_rx_handler_register - register receive handler
  *      @dev: device to register a handler for
  *      @rx_handler: receive handler to register
  *      @rx_handler_data: data pointer that is used by rx handler
  *
  *      Register a receive handler for a device. This handler will then be
  *      called from __netif_receive_skb. A negative errno code is returned
  *      on a failure.
  *
  *      The caller must hold the rtnl_mutex.
  *
  *      For a general description of rx_handler, see enum rx_handler_result.
  */
 int netdev_rx_handler_register(struct net_device *dev,
                                rx_handler_func_t *rx_handler,
                                void *rx_handler_data)
 {
         ASSERT_RTNL();
 
         if (dev->rx_handler)
                 return -EBUSY;
 
         /* Note: rx_handler_data must be set before rx_handler */
         rcu_assign_pointer(dev->rx_handler_data, rx_handler_data);
         rcu_assign_pointer(dev->rx_handler, rx_handler);
 
         return 0;
 }
 EXPORT_SYMBOL_GPL(netdev_rx_handler_register);
 
 /**
  *      netdev_rx_handler_unregister - unregister receive handler
  *      @dev: device to unregister a handler from
  *
  *      Unregister a receive handler from a device.
  *
  *      The caller must hold the rtnl_mutex.
  */
 void netdev_rx_handler_unregister(struct net_device *dev)
 {
 
         ASSERT_RTNL();
         RCU_INIT_POINTER(dev->rx_handler, NULL);
         /* a reader seeing a non NULL rx_handler in a rcu_read_lock()
          * section has a guarantee to see a non NULL rx_handler_data
          * as well.
          */
         synchronize_net();
         RCU_INIT_POINTER(dev->rx_handler_data, NULL);
 }
 EXPORT_SYMBOL_GPL(netdev_rx_handler_unregister);
 
 /*
  * Limit the use of PFMEMALLOC reserves to those protocols that implement
  * the special handling of PFMEMALLOC skbs.
  */
 static bool skb_pfmemalloc_protocol(struct sk_buff *skb)
 {
         switch (skb->protocol) {
         case htons(ETH_P_ARP):
         case htons(ETH_P_IP):
         case htons(ETH_P_IPV6):
         case htons(ETH_P_8021Q):
         case htons(ETH_P_8021AD):
                 return true;
         default:
                 return false;
         }
 }
 
 static int __netif_receive_skb_core(struct sk_buff *skb, bool pfmemalloc)
 {
         struct packet_type *ptype, *pt_prev;
         rx_handler_func_t *rx_handler;
         struct net_device *orig_dev;
         bool deliver_exact = false;
         int ret = NET_RX_DROP;
         __be16 type;
 
         net_timestamp_check(!netdev_tstamp_prequeue, skb);
 
         trace_netif_receive_skb(skb);
 
         orig_dev = skb->dev;
 
         skb_reset_network_header(skb);
         if (!skb_transport_header_was_set(skb))
                 skb_reset_transport_header(skb);
         skb_reset_mac_len(skb);
 
         pt_prev = NULL;
 
         rcu_read_lock();
 
 another_round:
         skb->skb_iif = skb->dev->ifindex;
 
         __this_cpu_inc(softnet_data.processed);
 
         if (skb->protocol == cpu_to_be16(ETH_P_8021Q) ||
             skb->protocol == cpu_to_be16(ETH_P_8021AD)) {
                 skb = skb_vlan_untag(skb);
                 if (unlikely(!skb))
                         goto unlock;
         }
 
 #ifdef CONFIG_NET_CLS_ACT
         if (skb->tc_verd & TC_NCLS) {
                 skb->tc_verd = CLR_TC_NCLS(skb->tc_verd);
                 goto ncls;
         }
 #endif
 
         if (pfmemalloc)
                 goto skip_taps;
 
         list_for_each_entry_rcu(ptype, &ptype_all, list) {
                 if (pt_prev)
                         ret = deliver_skb(skb, pt_prev, orig_dev);
                 pt_prev = ptype;
         }
 
         list_for_each_entry_rcu(ptype, &skb->dev->ptype_all, list) {
                 if (pt_prev)
                         ret = deliver_skb(skb, pt_prev, orig_dev);
                 pt_prev = ptype;
         }
 
 skip_taps:
 #ifdef CONFIG_NET_CLS_ACT
         if (static_key_false(&ingress_needed)) {
                 skb = handle_ing(skb, &pt_prev, &ret, orig_dev);
                 if (!skb)
                         goto unlock;
         }
 
         skb->tc_verd = 0;
 ncls:
 #endif
         if (pfmemalloc && !skb_pfmemalloc_protocol(skb))
                 goto drop;
 
         if (skb_vlan_tag_present(skb)) {
                 if (pt_prev) {
                         ret = deliver_skb(skb, pt_prev, orig_dev);
                         pt_prev = NULL;
                 }
                 if (vlan_do_receive(&skb))
                         goto another_round;
                 else if (unlikely(!skb))
                         goto unlock;
         }
 
         rx_handler = rcu_dereference(skb->dev->rx_handler);
         if (rx_handler) {
                 if (pt_prev) {
                         ret = deliver_skb(skb, pt_prev, orig_dev);
                         pt_prev = NULL;
                 }
                 switch (rx_handler(&skb)) {
                 case RX_HANDLER_CONSUMED:
                         ret = NET_RX_SUCCESS;
                         goto unlock;
                 case RX_HANDLER_ANOTHER:
                         goto another_round;
                 case RX_HANDLER_EXACT:
                         deliver_exact = true;
                 case RX_HANDLER_PASS:
                         break;
                 default:
                         BUG();
                 }
         }
 
         if (unlikely(skb_vlan_tag_present(skb))) {
                 if (skb_vlan_tag_get_id(skb))
                         skb->pkt_type = PACKET_OTHERHOST;
                 /* Note: we might in the future use prio bits
                  * and set skb->priority like in vlan_do_receive()
                  * For the time being, just ignore Priority Code Point
                  */
                 skb->vlan_tci = 0;
         }
 
         type = skb->protocol;
 
         /* deliver only exact match when indicated */
         if (likely(!deliver_exact)) {
                 deliver_ptype_list_skb(skb, &pt_prev, orig_dev, type,
                                        &ptype_base[ntohs(type) &
                                                    PTYPE_HASH_MASK]);
         }
 
         deliver_ptype_list_skb(skb, &pt_prev, orig_dev, type,
                                &orig_dev->ptype_specific);
 
         if (unlikely(skb->dev != orig_dev)) {
                 deliver_ptype_list_skb(skb, &pt_prev, orig_dev, type,
                                        &skb->dev->ptype_specific);
         }
 
         if (pt_prev) {
                 if (unlikely(skb_orphan_frags(skb, GFP_ATOMIC)))
                         goto drop;
                 else
                         ret = pt_prev->func(skb, skb->dev, pt_prev, orig_dev);
         } else {
 drop:
                 atomic_long_inc(&skb->dev->rx_dropped);
                 kfree_skb(skb);
                 /* Jamal, now you will not able to escape explaining
                  * me how you were going to use this. :-)
                  */
                 ret = NET_RX_DROP;
         }
 
 unlock:
         rcu_read_unlock();
         return ret;
 }
 
 static int __netif_receive_skb(struct sk_buff *skb)
 {
         int ret;
 
         if (sk_memalloc_socks() && skb_pfmemalloc(skb)) {
                 unsigned long pflags = current->flags;
 
                 /*
                  * PFMEMALLOC skbs are special, they should
                  * - be delivered to SOCK_MEMALLOC sockets only
                  * - stay away from userspace
                  * - have bounded memory usage
                  *
                  * Use PF_MEMALLOC as this saves us from propagating the allocation
                  * context down to all allocation sites.
                  */
                 current->flags |= PF_MEMALLOC;
                 ret = __netif_receive_skb_core(skb, true);
                 tsk_restore_flags(current, pflags, PF_MEMALLOC);
         } else
                 ret = __netif_receive_skb_core(skb, false);
 
         return ret;
 }
 
 static int netif_receive_skb_internal(struct sk_buff *skb)
 {
         net_timestamp_check(netdev_tstamp_prequeue, skb);
 
         if (skb_defer_rx_timestamp(skb))
                 return NET_RX_SUCCESS;
 
 #ifdef CONFIG_RPS
         if (static_key_false(&rps_needed)) {
                 struct rps_dev_flow voidflow, *rflow = &voidflow;
                 int cpu, ret;
 
                 rcu_read_lock();
 
                 cpu = get_rps_cpu(skb->dev, skb, &rflow);
 
                 if (cpu >= 0) {
                         ret = enqueue_to_backlog(skb, cpu, &rflow->last_qtail);
                         rcu_read_unlock();
                         return ret;
                 }
                 rcu_read_unlock();
         }
 #endif
         return __netif_receive_skb(skb);
 }
 
 /**
  *      netif_receive_skb - process receive buffer from network
  *      @skb: buffer to process
  *
  *      netif_receive_skb() is the main receive data processing function.
  *      It always succeeds. The buffer may be dropped during processing
  *      for congestion control or by the protocol layers.
  *
  *      This function may only be called from softirq context and interrupts
  *      should be enabled.
  *
  *      Return values (usually ignored):
  *      NET_RX_SUCCESS: no congestion
  *      NET_RX_DROP: packet was dropped
  */
 int netif_receive_skb_sk(struct sock *sk, struct sk_buff *skb)
 {
         trace_netif_receive_skb_entry(skb);
 
         return netif_receive_skb_internal(skb);
 }
 EXPORT_SYMBOL(netif_receive_skb_sk);
 
 /* Network device is going away, flush any packets still pending
  * Called with irqs disabled.
  */
 static void flush_backlog(void *arg)
 {
         struct net_device *dev = arg;
         struct softnet_data *sd = this_cpu_ptr(&softnet_data);
         struct sk_buff *skb, *tmp;
 
         rps_lock(sd);
         skb_queue_walk_safe(&sd->input_pkt_queue, skb, tmp) {
                 if (skb->dev == dev) {
                         __skb_unlink(skb, &sd->input_pkt_queue);
                         kfree_skb(skb);
                         input_queue_head_incr(sd);
                 }
         }
         rps_unlock(sd);
 
         skb_queue_walk_safe(&sd->process_queue, skb, tmp) {
                 if (skb->dev == dev) {
                         __skb_unlink(skb, &sd->process_queue);
                         kfree_skb(skb);
                         input_queue_head_incr(sd);
                 }
         }
 }
 
 static int napi_gro_complete(struct sk_buff *skb)
 {
         struct packet_offload *ptype;
         __be16 type = skb->protocol;
         struct list_head *head = &offload_base;
         int err = -ENOENT;
 
         BUILD_BUG_ON(sizeof(struct napi_gro_cb) > sizeof(skb->cb));
 
         if (NAPI_GRO_CB(skb)->count == 1) {
                 skb_shinfo(skb)->gso_size = 0;
                 goto out;
         }
 
         rcu_read_lock();
         list_for_each_entry_rcu(ptype, head, list) {
                 if (ptype->type != type || !ptype->callbacks.gro_complete)
                         continue;
 
                 err = ptype->callbacks.gro_complete(skb, 0);
                 break;
         }
         rcu_read_unlock();
 
         if (err) {
                 WARN_ON(&ptype->list == head);
                 kfree_skb(skb);
                 return NET_RX_SUCCESS;
         }
 
 out:
         return netif_receive_skb_internal(skb);
 }
 
 /* napi->gro_list contains packets ordered by age.
  * youngest packets at the head of it.
  * Complete skbs in reverse order to reduce latencies.
  */
 void napi_gro_flush(struct napi_struct *napi, bool flush_old)
 {
         struct sk_buff *skb, *prev = NULL;
 
         /* scan list and build reverse chain */
         for (skb = napi->gro_list; skb != NULL; skb = skb->next) {
                 skb->prev = prev;
                 prev = skb;
         }
 
         for (skb = prev; skb; skb = prev) {
                 skb->next = NULL;
 
                 if (flush_old && NAPI_GRO_CB(skb)->age == jiffies)
                         return;
 
                 prev = skb->prev;
                 napi_gro_complete(skb);
                 napi->gro_count--;
         }
 
         napi->gro_list = NULL;
 }
 EXPORT_SYMBOL(napi_gro_flush);
 
 static void gro_list_prepare(struct napi_struct *napi, struct sk_buff *skb)
 {
         struct sk_buff *p;
         unsigned int maclen = skb->dev->hard_header_len;
         u32 hash = skb_get_hash_raw(skb);
 
         for (p = napi->gro_list; p; p = p->next) {
                 unsigned long diffs;
 
                 NAPI_GRO_CB(p)->flush = 0;
 
                 if (hash != skb_get_hash_raw(p)) {
                         NAPI_GRO_CB(p)->same_flow = 0;
                         continue;
                 }
 
                 diffs = (unsigned long)p->dev ^ (unsigned long)skb->dev;
                 diffs |= p->vlan_tci ^ skb->vlan_tci;
                 if (maclen == ETH_HLEN)
                         diffs |= compare_ether_header(skb_mac_header(p),
                                                       skb_mac_header(skb));
                 else if (!diffs)
                         diffs = memcmp(skb_mac_header(p),
                                        skb_mac_header(skb),
                                        maclen);
                 NAPI_GRO_CB(p)->same_flow = !diffs;
         }
 }
 
 static void skb_gro_reset_offset(struct sk_buff *skb)
 {
         const struct skb_shared_info *pinfo = skb_shinfo(skb);
         const skb_frag_t *frag0 = &pinfo->frags[0];
 
         NAPI_GRO_CB(skb)->data_offset = 0;
         NAPI_GRO_CB(skb)->frag0 = NULL;
         NAPI_GRO_CB(skb)->frag0_len = 0;
 
         if (skb_mac_header(skb) == skb_tail_pointer(skb) &&
             pinfo->nr_frags &&
             !PageHighMem(skb_frag_page(frag0))) {
                 NAPI_GRO_CB(skb)->frag0 = skb_frag_address(frag0);
                 NAPI_GRO_CB(skb)->frag0_len = skb_frag_size(frag0);
         }
 }
 
 static void gro_pull_from_frag0(struct sk_buff *skb, int grow)
 {
         struct skb_shared_info *pinfo = skb_shinfo(skb);
 
         BUG_ON(skb->end - skb->tail < grow);
 
         memcpy(skb_tail_pointer(skb), NAPI_GRO_CB(skb)->frag0, grow);
 
         skb->data_len -= grow;
         skb->tail += grow;
 
         pinfo->frags[0].page_offset += grow;
         skb_frag_size_sub(&pinfo->frags[0], grow);
 
         if (unlikely(!skb_frag_size(&pinfo->frags[0]))) {
                 skb_frag_unref(skb, 0);
                 memmove(pinfo->frags, pinfo->frags + 1,
                         --pinfo->nr_frags * sizeof(pinfo->frags[0]));
         }
 }
 
 static enum gro_result dev_gro_receive(struct napi_struct *napi, struct sk_buff *skb)
 {
         struct sk_buff **pp = NULL;
         struct packet_offload *ptype;
         __be16 type = skb->protocol;
         struct list_head *head = &offload_base;
         int same_flow;
         enum gro_result ret;
         int grow;
 
         if (!(skb->dev->features & NETIF_F_GRO))
                 goto normal;
 
         if (skb_is_gso(skb) || skb_has_frag_list(skb) || skb->csum_bad)
                 goto normal;
 
         gro_list_prepare(napi, skb);
 
         rcu_read_lock();
         list_for_each_entry_rcu(ptype, head, list) {
                 if (ptype->type != type || !ptype->callbacks.gro_receive)
                         continue;
 
                 skb_set_network_header(skb, skb_gro_offset(skb));
                 skb_reset_mac_len(skb);
                 NAPI_GRO_CB(skb)->same_flow = 0;
                 NAPI_GRO_CB(skb)->flush = 0;
                 NAPI_GRO_CB(skb)->free = 0;
                 NAPI_GRO_CB(skb)->udp_mark = 0;
                 NAPI_GRO_CB(skb)->gro_remcsum_start = 0;
 
                 /* Setup for GRO checksum validation */
                 switch (skb->ip_summed) {
                 case CHECKSUM_COMPLETE:
                         NAPI_GRO_CB(skb)->csum = skb->csum;
                         NAPI_GRO_CB(skb)->csum_valid = 1;
                         NAPI_GRO_CB(skb)->csum_cnt = 0;
                         break;
                 case CHECKSUM_UNNECESSARY:
                         NAPI_GRO_CB(skb)->csum_cnt = skb->csum_level + 1;
                         NAPI_GRO_CB(skb)->csum_valid = 0;
                         break;
                 default:
                         NAPI_GRO_CB(skb)->csum_cnt = 0;
                         NAPI_GRO_CB(skb)->csum_valid = 0;
                 }
 
                 pp = ptype->callbacks.gro_receive(&napi->gro_list, skb);
                 break;
         }
         rcu_read_unlock();
 
         if (&ptype->list == head)
                 goto normal;
 
         same_flow = NAPI_GRO_CB(skb)->same_flow;
         ret = NAPI_GRO_CB(skb)->free ? GRO_MERGED_FREE : GRO_MERGED;
 
         if (pp) {
                 struct sk_buff *nskb = *pp;
 
                 *pp = nskb->next;
                 nskb->next = NULL;
                 napi_gro_complete(nskb);
                 napi->gro_count--;
         }
 
         if (same_flow)
                 goto ok;
 
         if (NAPI_GRO_CB(skb)->flush)
                 goto normal;
 
         if (unlikely(napi->gro_count >= MAX_GRO_SKBS)) {
                 struct sk_buff *nskb = napi->gro_list;
 
                 /* locate the end of the list to select the 'oldest' flow */
                 while (nskb->next) {
                         pp = &nskb->next;
                         nskb = *pp;
                 }
                 *pp = NULL;
                 nskb->next = NULL;
                 napi_gro_complete(nskb);
         } else {
                 napi->gro_count++;
         }
         NAPI_GRO_CB(skb)->count = 1;
         NAPI_GRO_CB(skb)->age = jiffies;
         NAPI_GRO_CB(skb)->last = skb;
         skb_shinfo(skb)->gso_size = skb_gro_len(skb);
         skb->next = napi->gro_list;
         napi->gro_list = skb;
         ret = GRO_HELD;
 
 pull:
         grow = skb_gro_offset(skb) - skb_headlen(skb);
         if (grow > 0)
                 gro_pull_from_frag0(skb, grow);
 ok:
         return ret;
 
 normal:
         ret = GRO_NORMAL;
         goto pull;
 }
 
 struct packet_offload *gro_find_receive_by_type(__be16 type)
 {
         struct list_head *offload_head = &offload_base;
         struct packet_offload *ptype;
 
         list_for_each_entry_rcu(ptype, offload_head, list) {
                 if (ptype->type != type || !ptype->callbacks.gro_receive)
                         continue;
                 return ptype;
         }
         return NULL;
 }
 EXPORT_SYMBOL(gro_find_receive_by_type);
 
 struct packet_offload *gro_find_complete_by_type(__be16 type)
 {
         struct list_head *offload_head = &offload_base;
         struct packet_offload *ptype;
 
         list_for_each_entry_rcu(ptype, offload_head, list) {
                 if (ptype->type != type || !ptype->callbacks.gro_complete)
                         continue;
                 return ptype;
         }
         return NULL;
 }
 EXPORT_SYMBOL(gro_find_complete_by_type);
 
 static gro_result_t napi_skb_finish(gro_result_t ret, struct sk_buff *skb)
 {
         switch (ret) {
         case GRO_NORMAL:
                 if (netif_receive_skb_internal(skb))
                         ret = GRO_DROP;
                 break;
 
         case GRO_DROP:
                 kfree_skb(skb);
                 break;
 
         case GRO_MERGED_FREE:
                 if (NAPI_GRO_CB(skb)->free == NAPI_GRO_FREE_STOLEN_HEAD)
                         kmem_cache_free(skbuff_head_cache, skb);
                 else
                         __kfree_skb(skb);
                 break;
 
         case GRO_HELD:
         case GRO_MERGED:
                 break;
         }
 
         return ret;
 }
 
 gro_result_t napi_gro_receive(struct napi_struct *napi, struct sk_buff *skb)
 {
         trace_napi_gro_receive_entry(skb);
 
         skb_gro_reset_offset(skb);
 
         return napi_skb_finish(dev_gro_receive(napi, skb), skb);
 }
 EXPORT_SYMBOL(napi_gro_receive);
 
 static void napi_reuse_skb(struct napi_struct *napi, struct sk_buff *skb)
 {
         if (unlikely(skb->pfmemalloc)) {
                 consume_skb(skb);
                 return;
         }
         __skb_pull(skb, skb_headlen(skb));
         /* restore the reserve we had after netdev_alloc_skb_ip_align() */
         skb_reserve(skb, NET_SKB_PAD + NET_IP_ALIGN - skb_headroom(skb));
         skb->vlan_tci = 0;
         skb->dev = napi->dev;
         skb->skb_iif = 0;
         skb->encapsulation = 0;
         skb_shinfo(skb)->gso_type = 0;
         skb->truesize = SKB_TRUESIZE(skb_end_offset(skb));
 
         napi->skb = skb;
 }
 
 struct sk_buff *napi_get_frags(struct napi_struct *napi)
 {
         struct sk_buff *skb = napi->skb;
 
         if (!skb) {
                 skb = napi_alloc_skb(napi, GRO_MAX_HEAD);
                 napi->skb = skb;
         }
         return skb;
 }
 EXPORT_SYMBOL(napi_get_frags);
 
 static gro_result_t napi_frags_finish(struct napi_struct *napi,
                                       struct sk_buff *skb,
                                       gro_result_t ret)
 {
         switch (ret) {
         case GRO_NORMAL:
         case GRO_HELD:
                 __skb_push(skb, ETH_HLEN);
                 skb->protocol = eth_type_trans(skb, skb->dev);
                 if (ret == GRO_NORMAL && netif_receive_skb_internal(skb))
                         ret = GRO_DROP;
                 break;
 
         case GRO_DROP:
         case GRO_MERGED_FREE:
                 napi_reuse_skb(napi, skb);
                 break;
 
         case GRO_MERGED:
                 break;
         }
 
         return ret;
 }
 
 /* Upper GRO stack assumes network header starts at gro_offset=0
  * Drivers could call both napi_gro_frags() and napi_gro_receive()
  * We copy ethernet header into skb->data to have a common layout.
  */
 static struct sk_buff *napi_frags_skb(struct napi_struct *napi)
 {
         struct sk_buff *skb = napi->skb;
         const struct ethhdr *eth;
         unsigned int hlen = sizeof(*eth);
 
         napi->skb = NULL;
 
         skb_reset_mac_header(skb);
         skb_gro_reset_offset(skb);
 
         eth = skb_gro_header_fast(skb, 0);
         if (unlikely(skb_gro_header_hard(skb, hlen))) {
                 eth = skb_gro_header_slow(skb, hlen, 0);
                 if (unlikely(!eth)) {
                         napi_reuse_skb(napi, skb);
                         return NULL;
                 }
         } else {
                 gro_pull_from_frag0(skb, hlen);
                 NAPI_GRO_CB(skb)->frag0 += hlen;
                 NAPI_GRO_CB(skb)->frag0_len -= hlen;
         }
         __skb_pull(skb, hlen);
 
         /*
          * This works because the only protocols we care about don't require
          * special handling.
          * We'll fix it up properly in napi_frags_finish()
          */
         skb->protocol = eth->h_proto;
 
         return skb;
 }
 
 gro_result_t napi_gro_frags(struct napi_struct *napi)
 {
         struct sk_buff *skb = napi_frags_skb(napi);
 
         if (!skb)
                 return GRO_DROP;
 
         trace_napi_gro_frags_entry(skb);
 
         return napi_frags_finish(napi, skb, dev_gro_receive(napi, skb));
 }
 EXPORT_SYMBOL(napi_gro_frags);
 
 /* Compute the checksum from gro_offset and return the folded value
  * after adding in any pseudo checksum.
  */
 __sum16 __skb_gro_checksum_complete(struct sk_buff *skb)
 {
         __wsum wsum;
         __sum16 sum;
 
         wsum = skb_checksum(skb, skb_gro_offset(skb), skb_gro_len(skb), 0);
 
         /* NAPI_GRO_CB(skb)->csum holds pseudo checksum */
         sum = csum_fold(csum_add(NAPI_GRO_CB(skb)->csum, wsum));
         if (likely(!sum)) {
                 if (unlikely(skb->ip_summed == CHECKSUM_COMPLETE) &&
                     !skb->csum_complete_sw)
                         netdev_rx_csum_fault(skb->dev);
         }
 
         NAPI_GRO_CB(skb)->csum = wsum;
         NAPI_GRO_CB(skb)->csum_valid = 1;
 
         return sum;
 }
 EXPORT_SYMBOL(__skb_gro_checksum_complete);
 
 /*
  * net_rps_action_and_irq_enable sends any pending IPI's for rps.
  * Note: called with local irq disabled, but exits with local irq enabled.
  */
 static void net_rps_action_and_irq_enable(struct softnet_data *sd)
 {
 #ifdef CONFIG_RPS
         struct softnet_data *remsd = sd->rps_ipi_list;
 
         if (remsd) {
                 sd->rps_ipi_list = NULL;
 
                 local_irq_enable();
 
                 /* Send pending IPI's to kick RPS processing on remote cpus. */
                 while (remsd) {
                         struct softnet_data *next = remsd->rps_ipi_next;
 
                         if (cpu_online(remsd->cpu))
                                 smp_call_function_single_async(remsd->cpu,
                                                            &remsd->csd);
                         remsd = next;
                 }
         } else
 #endif
                 local_irq_enable();
 }
 
 static bool sd_has_rps_ipi_waiting(struct softnet_data *sd)
 {
 #ifdef CONFIG_RPS
         return sd->rps_ipi_list != NULL;
 #else
         return false;
 #endif
 }
 
 static int process_backlog(struct napi_struct *napi, int quota)
 {
         int work = 0;
         struct softnet_data *sd = container_of(napi, struct softnet_data, backlog);
 
         /* Check if we have pending ipi, its better to send them now,
          * not waiting net_rx_action() end.
          */
         if (sd_has_rps_ipi_waiting(sd)) {
                 local_irq_disable();
                 net_rps_action_and_irq_enable(sd);
         }
 
         napi->weight = weight_p;
         local_irq_disable();
         while (1) {
                 struct sk_buff *skb;
 
                 while ((skb = __skb_dequeue(&sd->process_queue))) {
                         local_irq_enable();
                         __netif_receive_skb(skb);
                         local_irq_disable();
                         input_queue_head_incr(sd);
                         if (++work >= quota) {
                                 local_irq_enable();
                                 return work;
                         }
                 }
 
                 rps_lock(sd);
                 if (skb_queue_empty(&sd->input_pkt_queue)) {
                         /*
                          * Inline a custom version of __napi_complete().
                          * only current cpu owns and manipulates this napi,
                          * and NAPI_STATE_SCHED is the only possible flag set
                          * on backlog.
                          * We can use a plain write instead of clear_bit(),
                          * and we dont need an smp_mb() memory barrier.
                          */
                         napi->state = 0;
                         rps_unlock(sd);
 
                         break;
                 }
 
                 skb_queue_splice_tail_init(&sd->input_pkt_queue,
                                            &sd->process_queue);
                 rps_unlock(sd);
         }
         local_irq_enable();
 
         return work;
 }
 
 /**
  * __napi_schedule - schedule for receive
  * @n: entry to schedule
  *
  * The entry's receive function will be scheduled to run.
  * Consider using __napi_schedule_irqoff() if hard irqs are masked.
  */
 void __napi_schedule(struct napi_struct *n)
 {
         unsigned long flags;
 
         local_irq_save(flags);
         ____napi_schedule(this_cpu_ptr(&softnet_data), n);
         local_irq_restore(flags);
 }
 EXPORT_SYMBOL(__napi_schedule);
 
 /**
  * __napi_schedule_irqoff - schedule for receive
  * @n: entry to schedule
  *
  * Variant of __napi_schedule() assuming hard irqs are masked
  */
 void __napi_schedule_irqoff(struct napi_struct *n)
 {
         ____napi_schedule(this_cpu_ptr(&softnet_data), n);
 }
 EXPORT_SYMBOL(__napi_schedule_irqoff);
 
 void __napi_complete(struct napi_struct *n)
 {
         BUG_ON(!test_bit(NAPI_STATE_SCHED, &n->state));
 
         list_del_init(&n->poll_list);
         smp_mb__before_atomic();
         clear_bit(NAPI_STATE_SCHED, &n->state);
 }
 EXPORT_SYMBOL(__napi_complete);
 
 void napi_complete_done(struct napi_struct *n, int work_done)
 {
         unsigned long flags;
 
         /*
          * don't let napi dequeue from the cpu poll list
          * just in case its running on a different cpu
          */
         if (unlikely(test_bit(NAPI_STATE_NPSVC, &n->state)))
                 return;
 
         if (n->gro_list) {
                 unsigned long timeout = 0;
 
                 if (work_done)
                         timeout = n->dev->gro_flush_timeout;
 
                 if (timeout)
                         hrtimer_start(&n->timer, ns_to_ktime(timeout),
                                       HRTIMER_MODE_REL_PINNED);
                 else
                         napi_gro_flush(n, false);
         }
         if (likely(list_empty(&n->poll_list))) {
                 WARN_ON_ONCE(!test_and_clear_bit(NAPI_STATE_SCHED, &n->state));
         } else {
                 /* If n->poll_list is not empty, we need to mask irqs */
                 local_irq_save(flags);
                 __napi_complete(n);
                 local_irq_restore(flags);
         }
 }
 EXPORT_SYMBOL(napi_complete_done);
 
 /* must be called under rcu_read_lock(), as we dont take a reference */
 struct napi_struct *napi_by_id(unsigned int napi_id)
 {
         unsigned int hash = napi_id % HASH_SIZE(napi_hash);
         struct napi_struct *napi;
 
         hlist_for_each_entry_rcu(napi, &napi_hash[hash], napi_hash_node)
                 if (napi->napi_id == napi_id)
                         return napi;
 
         return NULL;
 }
 EXPORT_SYMBOL_GPL(napi_by_id);
 
 void napi_hash_add(struct napi_struct *napi)
 {
         if (!test_and_set_bit(NAPI_STATE_HASHED, &napi->state)) {
 
                 spin_lock(&napi_hash_lock);
 
                 /* 0 is not a valid id, we also skip an id that is taken
                  * we expect both events to be extremely rare
                  */
                 napi->napi_id = 0;
                 while (!napi->napi_id) {
                         napi->napi_id = ++napi_gen_id;
                         if (napi_by_id(napi->napi_id))
                                 napi->napi_id = 0;
                 }
 
                 hlist_add_head_rcu(&napi->napi_hash_node,
                         &napi_hash[napi->napi_id % HASH_SIZE(napi_hash)]);
 
                 spin_unlock(&napi_hash_lock);
         }
 }
 EXPORT_SYMBOL_GPL(napi_hash_add);
 
 /* Warning : caller is responsible to make sure rcu grace period
  * is respected before freeing memory containing @napi
  */
 void napi_hash_del(struct napi_struct *napi)
 {
         spin_lock(&napi_hash_lock);
 
         if (test_and_clear_bit(NAPI_STATE_HASHED, &napi->state))
                 hlist_del_rcu(&napi->napi_hash_node);
 
         spin_unlock(&napi_hash_lock);
 }
 EXPORT_SYMBOL_GPL(napi_hash_del);
 
 static enum hrtimer_restart napi_watchdog(struct hrtimer *timer)
 {
         struct napi_struct *napi;
 
         napi = container_of(timer, struct napi_struct, timer);
         if (napi->gro_list)
                 napi_schedule(napi);
 
         return HRTIMER_NORESTART;
 }
 
 void netif_napi_add(struct net_device *dev, struct napi_struct *napi,
                     int (*poll)(struct napi_struct *, int), int weight)
 {
         INIT_LIST_HEAD(&napi->poll_list);
         hrtimer_init(&napi->timer, CLOCK_MONOTONIC, HRTIMER_MODE_REL_PINNED);
         napi->timer.function = napi_watchdog;
         napi->gro_count = 0;
         napi->gro_list = NULL;
         napi->skb = NULL;
         napi->poll = poll;
         if (weight > NAPI_POLL_WEIGHT)
                 pr_err_once("netif_napi_add() called with weight %d on device %s\n",
                             weight, dev->name);
         napi->weight = weight;
         list_add(&napi->dev_list, &dev->napi_list);
         napi->dev = dev;
 #ifdef CONFIG_NETPOLL
         spin_lock_init(&napi->poll_lock);
         napi->poll_owner = -1;
 #endif
         set_bit(NAPI_STATE_SCHED, &napi->state);
 }
 EXPORT_SYMBOL(netif_napi_add);
 
 void napi_disable(struct napi_struct *n)
 {
         might_sleep();
         set_bit(NAPI_STATE_DISABLE, &n->state);
 
         while (test_and_set_bit(NAPI_STATE_SCHED, &n->state))
                 msleep(1);
 
         hrtimer_cancel(&n->timer);
 
         clear_bit(NAPI_STATE_DISABLE, &n->state);
 }
 EXPORT_SYMBOL(napi_disable);
 
 void netif_napi_del(struct napi_struct *napi)
 {
         list_del_init(&napi->dev_list);
         napi_free_frags(napi);
 
         kfree_skb_list(napi->gro_list);
         napi->gro_list = NULL;
         napi->gro_count = 0;
 }
 EXPORT_SYMBOL(netif_napi_del);
 
 static int napi_poll(struct napi_struct *n, struct list_head *repoll)
 {
         void *have;
         int work, weight;
 
         list_del_init(&n->poll_list);
 
         have = netpoll_poll_lock(n);
 
         weight = n->weight;
 
         /* This NAPI_STATE_SCHED test is for avoiding a race
          * with netpoll's poll_napi().  Only the entity which
          * obtains the lock and sees NAPI_STATE_SCHED set will
          * actually make the ->poll() call.  Therefore we avoid
          * accidentally calling ->poll() when NAPI is not scheduled.
          */
         work = 0;
         if (test_bit(NAPI_STATE_SCHED, &n->state)) {
                 work = n->poll(n, weight);
                 trace_napi_poll(n);
         }
 
         WARN_ON_ONCE(work > weight);
 
         if (likely(work < weight))
                 goto out_unlock;
 
         /* Drivers must not modify the NAPI state if they
          * consume the entire weight.  In such cases this code
          * still "owns" the NAPI instance and therefore can
          * move the instance around on the list at-will.
          */
         if (unlikely(napi_disable_pending(n))) {
                 napi_complete(n);
                 goto out_unlock;
         }
 
         if (n->gro_list) {
                 /* flush too old packets
                  * If HZ < 1000, flush all packets.
                  */
                 napi_gro_flush(n, HZ >= 1000);
         }
 
         /* Some drivers may have called napi_schedule
          * prior to exhausting their budget.
          */
         if (unlikely(!list_empty(&n->poll_list))) {
                 pr_warn_once("%s: Budget exhausted after napi rescheduled\n",
                              n->dev ? n->dev->name : "backlog");
                 goto out_unlock;
         }
 
         list_add_tail(&n->poll_list, repoll);
 
 out_unlock:
         netpoll_poll_unlock(have);
 
         return work;
 }
 
 static void net_rx_action(struct softirq_action *h)
 {
         struct softnet_data *sd = this_cpu_ptr(&softnet_data);
         unsigned long time_limit = jiffies + 2;
         int budget = netdev_budget;
         LIST_HEAD(list);
         LIST_HEAD(repoll);
 
         local_irq_disable();
         list_splice_init(&sd->poll_list, &list);
         local_irq_enable();
 
         for (;;) {
                 struct napi_struct *n;
 
                 if (list_empty(&list)) {
                         if (!sd_has_rps_ipi_waiting(sd) && list_empty(&repoll))
                                 return;
                         break;
                 }
 
                 n = list_first_entry(&list, struct napi_struct, poll_list);
                 budget -= napi_poll(n, &repoll);
 
                 /* If softirq window is exhausted then punt.
                  * Allow this to run for 2 jiffies since which will allow
                  * an average latency of 1.5/HZ.
                  */
                 if (unlikely(budget <= 0 ||
                              time_after_eq(jiffies, time_limit))) {
                         sd->time_squeeze++;
                         break;
                 }
         }
 
         local_irq_disable();
 
         list_splice_tail_init(&sd->poll_list, &list);
         list_splice_tail(&repoll, &list);
         list_splice(&list, &sd->poll_list);
         if (!list_empty(&sd->poll_list))
                 __raise_softirq_irqoff(NET_RX_SOFTIRQ);
 
         net_rps_action_and_irq_enable(sd);
 }
 
 struct netdev_adjacent {
         struct net_device *dev;
 
         /* upper master flag, there can only be one master device per list */
         bool master;
 
         /* counter for the number of times this device was added to us */
         u16 ref_nr;
 
         /* private field for the users */
         void *private;
 
         struct list_head list;
         struct rcu_head rcu;
 };
 
 static struct netdev_adjacent *__netdev_find_adj(struct net_device *dev,
                                                  struct net_device *adj_dev,
                                                  struct list_head *adj_list)
 {
         struct netdev_adjacent *adj;
 
         list_for_each_entry(adj, adj_list, list) {
                 if (adj->dev == adj_dev)
                         return adj;
         }
         return NULL;
 }
 
 /**
  * netdev_has_upper_dev - Check if device is linked to an upper device
  * @dev: device
  * @upper_dev: upper device to check
  *
  * Find out if a device is linked to specified upper device and return true
  * in case it is. Note that this checks only immediate upper device,
  * not through a complete stack of devices. The caller must hold the RTNL lock.
  */
 bool netdev_has_upper_dev(struct net_device *dev,
                           struct net_device *upper_dev)
 {
         ASSERT_RTNL();
 
         return __netdev_find_adj(dev, upper_dev, &dev->all_adj_list.upper);
 }
 EXPORT_SYMBOL(netdev_has_upper_dev);
 
 /**
  * netdev_has_any_upper_dev - Check if device is linked to some device
  * @dev: device
  *
  * Find out if a device is linked to an upper device and return true in case
  * it is. The caller must hold the RTNL lock.
  */
 static bool netdev_has_any_upper_dev(struct net_device *dev)
 {
         ASSERT_RTNL();
 
         return !list_empty(&dev->all_adj_list.upper);
 }
 
 /**
  * netdev_master_upper_dev_get - Get master upper device
  * @dev: device
  *
  * Find a master upper device and return pointer to it or NULL in case
  * it's not there. The caller must hold the RTNL lock.
  */
 struct net_device *netdev_master_upper_dev_get(struct net_device *dev)
 {
         struct netdev_adjacent *upper;
 
         ASSERT_RTNL();
 
         if (list_empty(&dev->adj_list.upper))
                 return NULL;
 
         upper = list_first_entry(&dev->adj_list.upper,
                                  struct netdev_adjacent, list);
         if (likely(upper->master))
                 return upper->dev;
         return NULL;
 }
 EXPORT_SYMBOL(netdev_master_upper_dev_get);
 
 void *netdev_adjacent_get_private(struct list_head *adj_list)
 {
         struct netdev_adjacent *adj;
 
         adj = list_entry(adj_list, struct netdev_adjacent, list);
 
         return adj->private;
 }
 EXPORT_SYMBOL(netdev_adjacent_get_private);
 
 /**
  * netdev_upper_get_next_dev_rcu - Get the next dev from upper list
  * @dev: device
  * @iter: list_head ** of the current position
  *
  * Gets the next device from the dev's upper list, starting from iter
  * position. The caller must hold RCU read lock.
  */
 struct net_device *netdev_upper_get_next_dev_rcu(struct net_device *dev,
                                                  struct list_head **iter)
 {
         struct netdev_adjacent *upper;
 
         WARN_ON_ONCE(!rcu_read_lock_held() && !lockdep_rtnl_is_held());
 
         upper = list_entry_rcu((*iter)->next, struct netdev_adjacent, list);
 
         if (&upper->list == &dev->adj_list.upper)
                 return NULL;
 
         *iter = &upper->list;
 
         return upper->dev;
 }
 EXPORT_SYMBOL(netdev_upper_get_next_dev_rcu);
 
 /**
  * netdev_all_upper_get_next_dev_rcu - Get the next dev from upper list
  * @dev: device
  * @iter: list_head ** of the current position
  *
  * Gets the next device from the dev's upper list, starting from iter
  * position. The caller must hold RCU read lock.
  */
 struct net_device *netdev_all_upper_get_next_dev_rcu(struct net_device *dev,
                                                      struct list_head **iter)
 {
         struct netdev_adjacent *upper;
 
         WARN_ON_ONCE(!rcu_read_lock_held() && !lockdep_rtnl_is_held());
 
         upper = list_entry_rcu((*iter)->next, struct netdev_adjacent, list);
 
         if (&upper->list == &dev->all_adj_list.upper)
                 return NULL;
 
         *iter = &upper->list;
 
         return upper->dev;
 }
 EXPORT_SYMBOL(netdev_all_upper_get_next_dev_rcu);
 
 /**
  * netdev_lower_get_next_private - Get the next ->private from the
  *                                 lower neighbour list
  * @dev: device
  * @iter: list_head ** of the current position
  *
  * Gets the next netdev_adjacent->private from the dev's lower neighbour
  * list, starting from iter position. The caller must hold either hold the
  * RTNL lock or its own locking that guarantees that the neighbour lower
  * list will remain unchainged.
  */
 void *netdev_lower_get_next_private(struct net_device *dev,
                                     struct list_head **iter)
 {
         struct netdev_adjacent *lower;
 
         lower = list_entry(*iter, struct netdev_adjacent, list);
 
         if (&lower->list == &dev->adj_list.lower)
                 return NULL;
 
         *iter = lower->list.next;
 
         return lower->private;
 }
 EXPORT_SYMBOL(netdev_lower_get_next_private);
 
 /**
  * netdev_lower_get_next_private_rcu - Get the next ->private from the
  *                                     lower neighbour list, RCU
  *                                     variant
  * @dev: device
  * @iter: list_head ** of the current position
  *
  * Gets the next netdev_adjacent->private from the dev's lower neighbour
  * list, starting from iter position. The caller must hold RCU read lock.
  */
 void *netdev_lower_get_next_private_rcu(struct net_device *dev,
                                         struct list_head **iter)
 {
         struct netdev_adjacent *lower;
 
         WARN_ON_ONCE(!rcu_read_lock_held());
 
         lower = list_entry_rcu((*iter)->next, struct netdev_adjacent, list);
 
         if (&lower->list == &dev->adj_list.lower)
                 return NULL;
 
         *iter = &lower->list;
 
         return lower->private;
 }
 EXPORT_SYMBOL(netdev_lower_get_next_private_rcu);
 
 /**
  * netdev_lower_get_next - Get the next device from the lower neighbour
  *                         list
  * @dev: device
  * @iter: list_head ** of the current position
  *
  * Gets the next netdev_adjacent from the dev's lower neighbour
  * list, starting from iter position. The caller must hold RTNL lock or
  * its own locking that guarantees that the neighbour lower
  * list will remain unchainged.
  */
 void *netdev_lower_get_next(struct net_device *dev, struct list_head **iter)
 {
         struct netdev_adjacent *lower;
 
         lower = list_entry((*iter)->next, struct netdev_adjacent, list);
 
         if (&lower->list == &dev->adj_list.lower)
                 return NULL;
 
         *iter = &lower->list;
 
         return lower->dev;
 }
 EXPORT_SYMBOL(netdev_lower_get_next);
 
 /**
  * netdev_lower_get_first_private_rcu - Get the first ->private from the
  *                                     lower neighbour list, RCU
  *                                     variant
  * @dev: device
  *
  * Gets the first netdev_adjacent->private from the dev's lower neighbour
  * list. The caller must hold RCU read lock.
  */
 void *netdev_lower_get_first_private_rcu(struct net_device *dev)
 {
         struct netdev_adjacent *lower;
 
         lower = list_first_or_null_rcu(&dev->adj_list.lower,
                         struct netdev_adjacent, list);
         if (lower)
                 return lower->private;
         return NULL;
 }
 EXPORT_SYMBOL(netdev_lower_get_first_private_rcu);
 
 /**
  * netdev_master_upper_dev_get_rcu - Get master upper device
  * @dev: device
  *
  * Find a master upper device and return pointer to it or NULL in case
  * it's not there. The caller must hold the RCU read lock.
  */
 struct net_device *netdev_master_upper_dev_get_rcu(struct net_device *dev)
 {
         struct netdev_adjacent *upper;
 
         upper = list_first_or_null_rcu(&dev->adj_list.upper,
                                        struct netdev_adjacent, list);
         if (upper && likely(upper->master))
                 return upper->dev;
         return NULL;
 }
 EXPORT_SYMBOL(netdev_master_upper_dev_get_rcu);
 
 static int netdev_adjacent_sysfs_add(struct net_device *dev,
                               struct net_device *adj_dev,
                               struct list_head *dev_list)
 {
         char linkname[IFNAMSIZ+7];
         sprintf(linkname, dev_list == &dev->adj_list.upper ?
                 "upper_%s" : "lower_%s", adj_dev->name);
         return sysfs_create_link(&(dev->dev.kobj), &(adj_dev->dev.kobj),
                                  linkname);
 }
 static void netdev_adjacent_sysfs_del(struct net_device *dev,
                                char *name,
                                struct list_head *dev_list)
 {
         char linkname[IFNAMSIZ+7];
         sprintf(linkname, dev_list == &dev->adj_list.upper ?
                 "upper_%s" : "lower_%s", name);
         sysfs_remove_link(&(dev->dev.kobj), linkname);
 }
 
 static inline bool netdev_adjacent_is_neigh_list(struct net_device *dev,
                                                  struct net_device *adj_dev,
                                                  struct list_head *dev_list)
 {
         return (dev_list == &dev->adj_list.upper ||
                 dev_list == &dev->adj_list.lower) &&
                 net_eq(dev_net(dev), dev_net(adj_dev));
 }
 
 static int __netdev_adjacent_dev_insert(struct net_device *dev,
                                         struct net_device *adj_dev,
                                         struct list_head *dev_list,
                                         void *private, bool master)
 {
         struct netdev_adjacent *adj;
         int ret;
 
         adj = __netdev_find_adj(dev, adj_dev, dev_list);
 
         if (adj) {
                 adj->ref_nr++;
                 return 0;
         }
 
         adj = kmalloc(sizeof(*adj), GFP_KERNEL);
         if (!adj)
                 return -ENOMEM;
 
         adj->dev = adj_dev;
         adj->master = master;
         adj->ref_nr = 1;
         adj->private = private;
         dev_hold(adj_dev);
 
         pr_debug("dev_hold for %s, because of link added from %s to %s\n",
                  adj_dev->name, dev->name, adj_dev->name);
 
         if (netdev_adjacent_is_neigh_list(dev, adj_dev, dev_list)) {
                 ret = netdev_adjacent_sysfs_add(dev, adj_dev, dev_list);
                 if (ret)
                         goto free_adj;
         }
 
         /* Ensure that master link is always the first item in list. */
         if (master) {
                 ret = sysfs_create_link(&(dev->dev.kobj),
                                         &(adj_dev->dev.kobj), "master");
                 if (ret)
                         goto remove_symlinks;
 
                 list_add_rcu(&adj->list, dev_list);
         } else {
                 list_add_tail_rcu(&adj->list, dev_list);
         }
 
         return 0;
 
 remove_symlinks:
         if (netdev_adjacent_is_neigh_list(dev, adj_dev, dev_list))
                 netdev_adjacent_sysfs_del(dev, adj_dev->name, dev_list);
 free_adj:
         kfree(adj);
         dev_put(adj_dev);
 
         return ret;
 }
 
 static void __netdev_adjacent_dev_remove(struct net_device *dev,
                                          struct net_device *adj_dev,
                                          struct list_head *dev_list)
 {
         struct netdev_adjacent *adj;
 
         adj = __netdev_find_adj(dev, adj_dev, dev_list);
 
         if (!adj) {
                 pr_err("tried to remove device %s from %s\n",
                        dev->name, adj_dev->name);
                 BUG();
         }
 
         if (adj->ref_nr > 1) {
                 pr_debug("%s to %s ref_nr-- = %d\n", dev->name, adj_dev->name,
                          adj->ref_nr-1);
                 adj->ref_nr--;
                 return;
         }
 
         if (adj->master)
                 sysfs_remove_link(&(dev->dev.kobj), "master");
 
         if (netdev_adjacent_is_neigh_list(dev, adj_dev, dev_list))
                 netdev_adjacent_sysfs_del(dev, adj_dev->name, dev_list);
 
         list_del_rcu(&adj->list);
         pr_debug("dev_put for %s, because link removed from %s to %s\n",
                  adj_dev->name, dev->name, adj_dev->name);
         dev_put(adj_dev);
         kfree_rcu(adj, rcu);
 }
 
 static int __netdev_adjacent_dev_link_lists(struct net_device *dev,
                                             struct net_device *upper_dev,
                                             struct list_head *up_list,
                                             struct list_head *down_list,
                                             void *private, bool master)
 {
         int ret;
 
         ret = __netdev_adjacent_dev_insert(dev, upper_dev, up_list, private,
                                            master);
         if (ret)
                 return ret;
 
         ret = __netdev_adjacent_dev_insert(upper_dev, dev, down_list, private,
                                            false);
         if (ret) {
                 __netdev_adjacent_dev_remove(dev, upper_dev, up_list);
                 return ret;
         }
 
         return 0;
 }
 
 static int __netdev_adjacent_dev_link(struct net_device *dev,
                                       struct net_device *upper_dev)
 {
         return __netdev_adjacent_dev_link_lists(dev, upper_dev,
                                                 &dev->all_adj_list.upper,
                                                 &upper_dev->all_adj_list.lower,
                                                 NULL, false);
 }
 
 static void __netdev_adjacent_dev_unlink_lists(struct net_device *dev,
                                                struct net_device *upper_dev,
                                                struct list_head *up_list,
                                                struct list_head *down_list)
 {
         __netdev_adjacent_dev_remove(dev, upper_dev, up_list);
         __netdev_adjacent_dev_remove(upper_dev, dev, down_list);
 }
 
 static void __netdev_adjacent_dev_unlink(struct net_device *dev,
                                          struct net_device *upper_dev)
 {
         __netdev_adjacent_dev_unlink_lists(dev, upper_dev,
                                            &dev->all_adj_list.upper,
                                            &upper_dev->all_adj_list.lower);
 }
 
 static int __netdev_adjacent_dev_link_neighbour(struct net_device *dev,
                                                 struct net_device *upper_dev,
                                                 void *private, bool master)
 {
         int ret = __netdev_adjacent_dev_link(dev, upper_dev);
 
         if (ret)
                 return ret;
 
         ret = __netdev_adjacent_dev_link_lists(dev, upper_dev,
                                                &dev->adj_list.upper,
                                                &upper_dev->adj_list.lower,
                                                private, master);
         if (ret) {
                 __netdev_adjacent_dev_unlink(dev, upper_dev);
                 return ret;
         }
 
         return 0;
 }
 
 static void __netdev_adjacent_dev_unlink_neighbour(struct net_device *dev,
                                                    struct net_device *upper_dev)
 {
         __netdev_adjacent_dev_unlink(dev, upper_dev);
         __netdev_adjacent_dev_unlink_lists(dev, upper_dev,
                                            &dev->adj_list.upper,
                                            &upper_dev->adj_list.lower);
 }
 
 static int __netdev_upper_dev_link(struct net_device *dev,
                                    struct net_device *upper_dev, bool master,
                                    void *private)
 {
         struct netdev_adjacent *i, *j, *to_i, *to_j;
         int ret = 0;
 
         ASSERT_RTNL();
 
         if (dev == upper_dev)
                 return -EBUSY;
 
         /* To prevent loops, check if dev is not upper device to upper_dev. */
         if (__netdev_find_adj(upper_dev, dev, &upper_dev->all_adj_list.upper))
                 return -EBUSY;
 
         if (__netdev_find_adj(dev, upper_dev, &dev->adj_list.upper))
                 return -EEXIST;
 
         if (master && netdev_master_upper_dev_get(dev))
                 return -EBUSY;
 
         ret = __netdev_adjacent_dev_link_neighbour(dev, upper_dev, private,
                                                    master);
         if (ret)
                 return ret;
 
         /* Now that we linked these devs, make all the upper_dev's
          * all_adj_list.upper visible to every dev's all_adj_list.lower an
          * versa, and don't forget the devices itself. All of these
          * links are non-neighbours.
          */
         list_for_each_entry(i, &dev->all_adj_list.lower, list) {
                 list_for_each_entry(j, &upper_dev->all_adj_list.upper, list) {
                         pr_debug("Interlinking %s with %s, non-neighbour\n",
                                  i->dev->name, j->dev->name);
                         ret = __netdev_adjacent_dev_link(i->dev, j->dev);
                         if (ret)
                                 goto rollback_mesh;
                 }
         }
 
         /* add dev to every upper_dev's upper device */
         list_for_each_entry(i, &upper_dev->all_adj_list.upper, list) {
                 pr_debug("linking %s's upper device %s with %s\n",
                          upper_dev->name, i->dev->name, dev->name);
                 ret = __netdev_adjacent_dev_link(dev, i->dev);
                 if (ret)
                         goto rollback_upper_mesh;
         }
 
         /* add upper_dev to every dev's lower device */
         list_for_each_entry(i, &dev->all_adj_list.lower, list) {
                 pr_debug("linking %s's lower device %s with %s\n", dev->name,
                          i->dev->name, upper_dev->name);
                 ret = __netdev_adjacent_dev_link(i->dev, upper_dev);
                 if (ret)
                         goto rollback_lower_mesh;
         }
 
         call_netdevice_notifiers(NETDEV_CHANGEUPPER, dev);
         return 0;
 
 rollback_lower_mesh:
         to_i = i;
         list_for_each_entry(i, &dev->all_adj_list.lower, list) {
                 if (i == to_i)
                         break;
                 __netdev_adjacent_dev_unlink(i->dev, upper_dev);
         }
 
         i = NULL;
 
 rollback_upper_mesh:
         to_i = i;
         list_for_each_entry(i, &upper_dev->all_adj_list.upper, list) {
                 if (i == to_i)
                         break;
                 __netdev_adjacent_dev_unlink(dev, i->dev);
         }
 
         i = j = NULL;
 
 rollback_mesh:
         to_i = i;
         to_j = j;
         list_for_each_entry(i, &dev->all_adj_list.lower, list) {
                 list_for_each_entry(j, &upper_dev->all_adj_list.upper, list) {
                         if (i == to_i && j == to_j)
                                 break;
                         __netdev_adjacent_dev_unlink(i->dev, j->dev);
                 }
                 if (i == to_i)
                         break;
         }
 
         __netdev_adjacent_dev_unlink_neighbour(dev, upper_dev);
 
         return ret;
 }
 
 /**
  * netdev_upper_dev_link - Add a link to the upper device
  * @dev: device
  * @upper_dev: new upper device
  *
  * Adds a link to device which is upper to this one. The caller must hold
  * the RTNL lock. On a failure a negative errno code is returned.
  * On success the reference counts are adjusted and the function
  * returns zero.
  */
 int netdev_upper_dev_link(struct net_device *dev,
                           struct net_device *upper_dev)
 {
         return __netdev_upper_dev_link(dev, upper_dev, false, NULL);
 }
 EXPORT_SYMBOL(netdev_upper_dev_link);
 
 /**
  * netdev_master_upper_dev_link - Add a master link to the upper device
  * @dev: device
  * @upper_dev: new upper device
  *
  * Adds a link to device which is upper to this one. In this case, only
  * one master upper device can be linked, although other non-master devices
  * might be linked as well. The caller must hold the RTNL lock.
  * On a failure a negative errno code is returned. On success the reference
  * counts are adjusted and the function returns zero.
  */
 int netdev_master_upper_dev_link(struct net_device *dev,
                                  struct net_device *upper_dev)
 {
         return __netdev_upper_dev_link(dev, upper_dev, true, NULL);
 }
 EXPORT_SYMBOL(netdev_master_upper_dev_link);
 
 int netdev_master_upper_dev_link_private(struct net_device *dev,
                                          struct net_device *upper_dev,
                                          void *private)
 {
         return __netdev_upper_dev_link(dev, upper_dev, true, private);
 }
 EXPORT_SYMBOL(netdev_master_upper_dev_link_private);
 
 /**
  * netdev_upper_dev_unlink - Removes a link to upper device
  * @dev: device
  * @upper_dev: new upper device
  *
  * Removes a link to device which is upper to this one. The caller must hold
  * the RTNL lock.
  */
 void netdev_upper_dev_unlink(struct net_device *dev,
                              struct net_device *upper_dev)
 {
         struct netdev_adjacent *i, *j;
         ASSERT_RTNL();
 
         __netdev_adjacent_dev_unlink_neighbour(dev, upper_dev);
 
         /* Here is the tricky part. We must remove all dev's lower
          * devices from all upper_dev's upper devices and vice
          * versa, to maintain the graph relationship.
          */
         list_for_each_entry(i, &dev->all_adj_list.lower, list)
                 list_for_each_entry(j, &upper_dev->all_adj_list.upper, list)
                         __netdev_adjacent_dev_unlink(i->dev, j->dev);
 
         /* remove also the devices itself from lower/upper device
          * list
          */
         list_for_each_entry(i, &dev->all_adj_list.lower, list)
                 __netdev_adjacent_dev_unlink(i->dev, upper_dev);
 
         list_for_each_entry(i, &upper_dev->all_adj_list.upper, list)
                 __netdev_adjacent_dev_unlink(dev, i->dev);
 
         call_netdevice_notifiers(NETDEV_CHANGEUPPER, dev);
 }
 EXPORT_SYMBOL(netdev_upper_dev_unlink);
 
 /**
  * netdev_bonding_info_change - Dispatch event about slave change
  * @dev: device
  * @bonding_info: info to dispatch
  *
  * Send NETDEV_BONDING_INFO to netdev notifiers with info.
  * The caller must hold the RTNL lock.
  */
 void netdev_bonding_info_change(struct net_device *dev,
                                 struct netdev_bonding_info *bonding_info)
 {
         struct netdev_notifier_bonding_info     info;
 
         memcpy(&info.bonding_info, bonding_info,
                sizeof(struct netdev_bonding_info));
         call_netdevice_notifiers_info(NETDEV_BONDING_INFO, dev,
                                       &info.info);
 }
 EXPORT_SYMBOL(netdev_bonding_info_change);
 
 static void netdev_adjacent_add_links(struct net_device *dev)
 {
         struct netdev_adjacent *iter;
 
         struct net *net = dev_net(dev);
 
         list_for_each_entry(iter, &dev->adj_list.upper, list) {
                 if (!net_eq(net,dev_net(iter->dev)))
                         continue;
                 netdev_adjacent_sysfs_add(iter->dev, dev,
                                           &iter->dev->adj_list.lower);
                 netdev_adjacent_sysfs_add(dev, iter->dev,
                                           &dev->adj_list.upper);
         }
 
         list_for_each_entry(iter, &dev->adj_list.lower, list) {
                 if (!net_eq(net,dev_net(iter->dev)))
                         continue;
                 netdev_adjacent_sysfs_add(iter->dev, dev,
                                           &iter->dev->adj_list.upper);
                 netdev_adjacent_sysfs_add(dev, iter->dev,
                                           &dev->adj_list.lower);
         }
 }
 
 static void netdev_adjacent_del_links(struct net_device *dev)
 {
         struct netdev_adjacent *iter;
 
         struct net *net = dev_net(dev);
 
         list_for_each_entry(iter, &dev->adj_list.upper, list) {
                 if (!net_eq(net,dev_net(iter->dev)))
                         continue;
                 netdev_adjacent_sysfs_del(iter->dev, dev->name,
                                           &iter->dev->adj_list.lower);
                 netdev_adjacent_sysfs_del(dev, iter->dev->name,
                                           &dev->adj_list.upper);
         }
 
         list_for_each_entry(iter, &dev->adj_list.lower, list) {
                 if (!net_eq(net,dev_net(iter->dev)))
                         continue;
                 netdev_adjacent_sysfs_del(iter->dev, dev->name,
                                           &iter->dev->adj_list.upper);
                 netdev_adjacent_sysfs_del(dev, iter->dev->name,
                                           &dev->adj_list.lower);
         }
 }
 
 void netdev_adjacent_rename_links(struct net_device *dev, char *oldname)
 {
         struct netdev_adjacent *iter;
 
         struct net *net = dev_net(dev);
 
         list_for_each_entry(iter, &dev->adj_list.upper, list) {
                 if (!net_eq(net,dev_net(iter->dev)))
                         continue;
                 netdev_adjacent_sysfs_del(iter->dev, oldname,
                                           &iter->dev->adj_list.lower);
                 netdev_adjacent_sysfs_add(iter->dev, dev,
                                           &iter->dev->adj_list.lower);
         }
 
         list_for_each_entry(iter, &dev->adj_list.lower, list) {
                 if (!net_eq(net,dev_net(iter->dev)))
                         continue;
                 netdev_adjacent_sysfs_del(iter->dev, oldname,
                                           &iter->dev->adj_list.upper);
                 netdev_adjacent_sysfs_add(iter->dev, dev,
                                           &iter->dev->adj_list.upper);
         }
 }
 
 void *netdev_lower_dev_get_private(struct net_device *dev,
                                    struct net_device *lower_dev)
 {
         struct netdev_adjacent *lower;
 
         if (!lower_dev)
                 return NULL;
         lower = __netdev_find_adj(dev, lower_dev, &dev->adj_list.lower);
         if (!lower)
                 return NULL;
 
         return lower->private;
 }
 EXPORT_SYMBOL(netdev_lower_dev_get_private);
 
 
 int dev_get_nest_level(struct net_device *dev,
                        bool (*type_check)(struct net_device *dev))
 {
         struct net_device *lower = NULL;
         struct list_head *iter;
         int max_nest = -1;
         int nest;
 
         ASSERT_RTNL();
 
         netdev_for_each_lower_dev(dev, lower, iter) {
                 nest = dev_get_nest_level(lower, type_check);
                 if (max_nest < nest)
                         max_nest = nest;
         }
 
         if (type_check(dev))
                 max_nest++;
 
         return max_nest;
 }
 EXPORT_SYMBOL(dev_get_nest_level);
 
 static void dev_change_rx_flags(struct net_device *dev, int flags)
 {
         const struct net_device_ops *ops = dev->netdev_ops;
 
         if (ops->ndo_change_rx_flags)
                 ops->ndo_change_rx_flags(dev, flags);
 }
 
 static int __dev_set_promiscuity(struct net_device *dev, int inc, bool notify)
 {
         unsigned int old_flags = dev->flags;
         kuid_t uid;
         kgid_t gid;
 
         ASSERT_RTNL();
 
         dev->flags |= IFF_PROMISC;
         dev->promiscuity += inc;
         if (dev->promiscuity == 0) {
                 /*
                  * Avoid overflow.
                  * If inc causes overflow, untouch promisc and return error.
                  */
                 if (inc < 0)
                         dev->flags &= ~IFF_PROMISC;
                 else {
                         dev->promiscuity -= inc;
                         pr_warn("%s: promiscuity touches roof, set promiscuity failed. promiscuity feature of device might be broken.\n",
                                 dev->name);
                         return -EOVERFLOW;
                 }
         }
         if (dev->flags != old_flags) {
                 pr_info("device %s %s promiscuous mode\n",
                         dev->name,
                         dev->flags & IFF_PROMISC ? "entered" : "left");
                 if (audit_enabled) {
                         current_uid_gid(&uid, &gid);
                         audit_log(current->audit_context, GFP_ATOMIC,
                                 AUDIT_ANOM_PROMISCUOUS,
                                 "dev=%s prom=%d old_prom=%d auid=%u uid=%u gid=%u ses=%u",
                                 dev->name, (dev->flags & IFF_PROMISC),
                                 (old_flags & IFF_PROMISC),
                                 from_kuid(&init_user_ns, audit_get_loginuid(current)),
                                 from_kuid(&init_user_ns, uid),
                                 from_kgid(&init_user_ns, gid),
                                 audit_get_sessionid(current));
                 }
 
                 dev_change_rx_flags(dev, IFF_PROMISC);
         }
         if (notify)
                 __dev_notify_flags(dev, old_flags, IFF_PROMISC);
         return 0;
 }
 
 /**
  *      dev_set_promiscuity     - update promiscuity count on a device
  *      @dev: device
  *      @inc: modifier
  *
  *      Add or remove promiscuity from a device. While the count in the device
  *      remains above zero the interface remains promiscuous. Once it hits zero
  *      the device reverts back to normal filtering operation. A negative inc
  *      value is used to drop promiscuity on the device.
  *      Return 0 if successful or a negative errno code on error.
  */
 int dev_set_promiscuity(struct net_device *dev, int inc)
 {
         unsigned int old_flags = dev->flags;
         int err;
 
         err = __dev_set_promiscuity(dev, inc, true);
         if (err < 0)
                 return err;
         if (dev->flags != old_flags)
                 dev_set_rx_mode(dev);
         return err;
 }
 EXPORT_SYMBOL(dev_set_promiscuity);
 
 static int __dev_set_allmulti(struct net_device *dev, int inc, bool notify)
 {
         unsigned int old_flags = dev->flags, old_gflags = dev->gflags;
 
         ASSERT_RTNL();
 
         dev->flags |= IFF_ALLMULTI;
         dev->allmulti += inc;
         if (dev->allmulti == 0) {
                 /*
                  * Avoid overflow.
                  * If inc causes overflow, untouch allmulti and return error.
                  */
                 if (inc < 0)
                         dev->flags &= ~IFF_ALLMULTI;
                 else {
                         dev->allmulti -= inc;
                         pr_warn("%s: allmulti touches roof, set allmulti failed. allmulti feature of device might be broken.\n",
                                 dev->name);
                         return -EOVERFLOW;
                 }
         }
         if (dev->flags ^ old_flags) {
                 dev_change_rx_flags(dev, IFF_ALLMULTI);
                 dev_set_rx_mode(dev);
                 if (notify)
                         __dev_notify_flags(dev, old_flags,
                                            dev->gflags ^ old_gflags);
         }
         return 0;
 }
 
 /**
  *      dev_set_allmulti        - update allmulti count on a device
  *      @dev: device
  *      @inc: modifier
  *
  *      Add or remove reception of all multicast frames to a device. While the
  *      count in the device remains above zero the interface remains listening
  *      to all interfaces. Once it hits zero the device reverts back to normal
  *      filtering operation. A negative @inc value is used to drop the counter
  *      when releasing a resource needing all multicasts.
  *      Return 0 if successful or a negative errno code on error.
  */
 
 int dev_set_allmulti(struct net_device *dev, int inc)
 {
         return __dev_set_allmulti(dev, inc, true);
 }
 EXPORT_SYMBOL(dev_set_allmulti);
 
 /*
  *      Upload unicast and multicast address lists to device and
  *      configure RX filtering. When the device doesn't support unicast
  *      filtering it is put in promiscuous mode while unicast addresses
  *      are present.
  */
 void __dev_set_rx_mode(struct net_device *dev)
 {
         const struct net_device_ops *ops = dev->netdev_ops;
 
         /* dev_open will call this function so the list will stay sane. */
         if (!(dev->flags&IFF_UP))
                 return;
 
         if (!netif_device_present(dev))
                 return;
 
         if (!(dev->priv_flags & IFF_UNICAST_FLT)) {
                 /* Unicast addresses changes may only happen under the rtnl,
                  * therefore calling __dev_set_promiscuity here is safe.
                  */
                 if (!netdev_uc_empty(dev) && !dev->uc_promisc) {
                         __dev_set_promiscuity(dev, 1, false);
                         dev->uc_promisc = true;
                 } else if (netdev_uc_empty(dev) && dev->uc_promisc) {
                         __dev_set_promiscuity(dev, -1, false);
                         dev->uc_promisc = false;
                 }
         }
 
         if (ops->ndo_set_rx_mode)
                 ops->ndo_set_rx_mode(dev);
 }
 
 void dev_set_rx_mode(struct net_device *dev)
 {
         netif_addr_lock_bh(dev);
         __dev_set_rx_mode(dev);
         netif_addr_unlock_bh(dev);
 }
 
 /**
  *      dev_get_flags - get flags reported to userspace
  *      @dev: device
  *
  *      Get the combination of flag bits exported through APIs to userspace.
  */
 unsigned int dev_get_flags(const struct net_device *dev)
 {
         unsigned int flags;
 
         flags = (dev->flags & ~(IFF_PROMISC |
                                 IFF_ALLMULTI |
                                 IFF_RUNNING |
                                 IFF_LOWER_UP |
                                 IFF_DORMANT)) |
                 (dev->gflags & (IFF_PROMISC |
                                 IFF_ALLMULTI));
 
         if (netif_running(dev)) {
                 if (netif_oper_up(dev))
                         flags |= IFF_RUNNING;
                 if (netif_carrier_ok(dev))
                         flags |= IFF_LOWER_UP;
                 if (netif_dormant(dev))
                         flags |= IFF_DORMANT;
         }
 
         return flags;
 }
 EXPORT_SYMBOL(dev_get_flags);
 
 int __dev_change_flags(struct net_device *dev, unsigned int flags)
 {
         unsigned int old_flags = dev->flags;
         int ret;
 
         ASSERT_RTNL();
 
         /*
          *      Set the flags on our device.
          */
 
         dev->flags = (flags & (IFF_DEBUG | IFF_NOTRAILERS | IFF_NOARP |
                                IFF_DYNAMIC | IFF_MULTICAST | IFF_PORTSEL |
                                IFF_AUTOMEDIA)) |
                      (dev->flags & (IFF_UP | IFF_VOLATILE | IFF_PROMISC |
                                     IFF_ALLMULTI));
 
         /*
          *      Load in the correct multicast list now the flags have changed.
          */
 
         if ((old_flags ^ flags) & IFF_MULTICAST)
                 dev_change_rx_flags(dev, IFF_MULTICAST);
 
         dev_set_rx_mode(dev);
 
         /*
          *      Have we downed the interface. We handle IFF_UP ourselves
          *      according to user attempts to set it, rather than blindly
          *      setting it.
          */
 
         ret = 0;
         if ((old_flags ^ flags) & IFF_UP)
                 ret = ((old_flags & IFF_UP) ? __dev_close : __dev_open)(dev);
 
         if ((flags ^ dev->gflags) & IFF_PROMISC) {
                 int inc = (flags & IFF_PROMISC) ? 1 : -1;
                 unsigned int old_flags = dev->flags;
 
                 dev->gflags ^= IFF_PROMISC;
 
                 if (__dev_set_promiscuity(dev, inc, false) >= 0)
                         if (dev->flags != old_flags)
                                 dev_set_rx_mode(dev);
         }
 
         /* NOTE: order of synchronization of IFF_PROMISC and IFF_ALLMULTI
            is important. Some (broken) drivers set IFF_PROMISC, when
            IFF_ALLMULTI is requested not asking us and not reporting.
          */
         if ((flags ^ dev->gflags) & IFF_ALLMULTI) {
                 int inc = (flags & IFF_ALLMULTI) ? 1 : -1;
 
                 dev->gflags ^= IFF_ALLMULTI;
                 __dev_set_allmulti(dev, inc, false);
         }
 
         return ret;
 }
 
 void __dev_notify_flags(struct net_device *dev, unsigned int old_flags,
                         unsigned int gchanges)
 {
         unsigned int changes = dev->flags ^ old_flags;
 
         if (gchanges)
                 rtmsg_ifinfo(RTM_NEWLINK, dev, gchanges, GFP_ATOMIC);
 
         if (changes & IFF_UP) {
                 if (dev->flags & IFF_UP)
                         call_netdevice_notifiers(NETDEV_UP, dev);
                 else
                         call_netdevice_notifiers(NETDEV_DOWN, dev);
         }
 
         if (dev->flags & IFF_UP &&
             (changes & ~(IFF_UP | IFF_PROMISC | IFF_ALLMULTI | IFF_VOLATILE))) {
                 struct netdev_notifier_change_info change_info;
 
                 change_info.flags_changed = changes;
                 call_netdevice_notifiers_info(NETDEV_CHANGE, dev,
                                               &change_info.info);
         }
 }
 
 /**
  *      dev_change_flags - change device settings
  *      @dev: device
  *      @flags: device state flags
  *
  *      Change settings on device based state flags. The flags are
  *      in the userspace exported format.
  */
 int dev_change_flags(struct net_device *dev, unsigned int flags)
 {
         int ret;
         unsigned int changes, old_flags = dev->flags, old_gflags = dev->gflags;
 
         ret = __dev_change_flags(dev, flags);
         if (ret < 0)
                 return ret;
 
         changes = (old_flags ^ dev->flags) | (old_gflags ^ dev->gflags);
         __dev_notify_flags(dev, old_flags, changes);
         return ret;
 }
 EXPORT_SYMBOL(dev_change_flags);
 
 static int __dev_set_mtu(struct net_device *dev, int new_mtu)
 {
         const struct net_device_ops *ops = dev->netdev_ops;
 
         if (ops->ndo_change_mtu)
                 return ops->ndo_change_mtu(dev, new_mtu);
 
         dev->mtu = new_mtu;
         return 0;
 }
 
 /**
  *      dev_set_mtu - Change maximum transfer unit
  *      @dev: device
  *      @new_mtu: new transfer unit
  *
  *      Change the maximum transfer size of the network device.
  */
 int dev_set_mtu(struct net_device *dev, int new_mtu)
 {
         int err, orig_mtu;
 
         if (new_mtu == dev->mtu)
                 return 0;
 
         /*      MTU must be positive.    */
         if (new_mtu < 0)
                 return -EINVAL;
 
         if (!netif_device_present(dev))
                 return -ENODEV;
 
         err = call_netdevice_notifiers(NETDEV_PRECHANGEMTU, dev);
         err = notifier_to_errno(err);
         if (err)
                 return err;
 
         orig_mtu = dev->mtu;
         err = __dev_set_mtu(dev, new_mtu);
 
         if (!err) {
                 err = call_netdevice_notifiers(NETDEV_CHANGEMTU, dev);
                 err = notifier_to_errno(err);
                 if (err) {
                         /* setting mtu back and notifying everyone again,
                          * so that they have a chance to revert changes.
                          */
                         __dev_set_mtu(dev, orig_mtu);
                         call_netdevice_notifiers(NETDEV_CHANGEMTU, dev);
                 }
         }
         return err;
 }
 EXPORT_SYMBOL(dev_set_mtu);
 
 /**
  *      dev_set_group - Change group this device belongs to
  *      @dev: device
  *      @new_group: group this device should belong to
  */
 void dev_set_group(struct net_device *dev, int new_group)
 {
         dev->group = new_group;
 }
 EXPORT_SYMBOL(dev_set_group);
 
 /**
  *      dev_set_mac_address - Change Media Access Control Address
  *      @dev: device
  *      @sa: new address
  *
  *      Change the hardware (MAC) address of the device
  */
 int dev_set_mac_address(struct net_device *dev, struct sockaddr *sa)
 {
         const struct net_device_ops *ops = dev->netdev_ops;
         int err;
 
         if (!ops->ndo_set_mac_address)
                 return -EOPNOTSUPP;
         if (sa->sa_family != dev->type)
                 return -EINVAL;
         if (!netif_device_present(dev))
                 return -ENODEV;
         err = ops->ndo_set_mac_address(dev, sa);
         if (err)
                 return err;
         dev->addr_assign_type = NET_ADDR_SET;
         call_netdevice_notifiers(NETDEV_CHANGEADDR, dev);
         add_device_randomness(dev->dev_addr, dev->addr_len);
         return 0;
 }
 EXPORT_SYMBOL(dev_set_mac_address);
 
 /**
  *      dev_change_carrier - Change device carrier
  *      @dev: device
  *      @new_carrier: new value
  *
  *      Change device carrier
  */
 int dev_change_carrier(struct net_device *dev, bool new_carrier)
 {
         const struct net_device_ops *ops = dev->netdev_ops;
 
         if (!ops->ndo_change_carrier)
                 return -EOPNOTSUPP;
         if (!netif_device_present(dev))
                 return -ENODEV;
         return ops->ndo_change_carrier(dev, new_carrier);
 }
 EXPORT_SYMBOL(dev_change_carrier);
 
 /**
  *      dev_get_phys_port_id - Get device physical port ID
  *      @dev: device
  *      @ppid: port ID
  *
  *      Get device physical port ID
  */
 int dev_get_phys_port_id(struct net_device *dev,
                          struct netdev_phys_item_id *ppid)
 {
         const struct net_device_ops *ops = dev->netdev_ops;
 
         if (!ops->ndo_get_phys_port_id)
                 return -EOPNOTSUPP;
         return ops->ndo_get_phys_port_id(dev, ppid);
 }
 EXPORT_SYMBOL(dev_get_phys_port_id);
 
 /**
  *      dev_get_phys_port_name - Get device physical port name
  *      @dev: device
  *      @name: port name
  *
  *      Get device physical port name
  */
 int dev_get_phys_port_name(struct net_device *dev,
                            char *name, size_t len)
 {
         const struct net_device_ops *ops = dev->netdev_ops;
 
         if (!ops->ndo_get_phys_port_name)
                 return -EOPNOTSUPP;
         return ops->ndo_get_phys_port_name(dev, name, len);
 }
 EXPORT_SYMBOL(dev_get_phys_port_name);
 
 /**
  *      dev_new_index   -       allocate an ifindex
  *      @net: the applicable net namespace
  *
  *      Returns a suitable unique value for a new device interface
  *      number.  The caller must hold the rtnl semaphore or the
  *      dev_base_lock to be sure it remains unique.
  */
 static int dev_new_index(struct net *net)
 {
         int ifindex = net->ifindex;
         for (;;) {
                 if (++ifindex <= 0)
                         ifindex = 1;
                 if (!__dev_get_by_index(net, ifindex))
                         return net->ifindex = ifindex;
         }
 }
 
 /* Delayed registration/unregisteration */
 static LIST_HEAD(net_todo_list);
 DECLARE_WAIT_QUEUE_HEAD(netdev_unregistering_wq);
 
 static void net_set_todo(struct net_device *dev)
 {
         list_add_tail(&dev->todo_list, &net_todo_list);
         dev_net(dev)->dev_unreg_count++;
 }
 
 static void rollback_registered_many(struct list_head *head)
 {
         struct net_device *dev, *tmp;
         LIST_HEAD(close_head);
 
         BUG_ON(dev_boot_phase);
         ASSERT_RTNL();
 
         list_for_each_entry_safe(dev, tmp, head, unreg_list) {
                 /* Some devices call without registering
                  * for initialization unwind. Remove those
                  * devices and proceed with the remaining.
                  */
                 if (dev->reg_state == NETREG_UNINITIALIZED) {
                         pr_debug("unregister_netdevice: device %s/%p never was registered\n",
                                  dev->name, dev);
 
                         WARN_ON(1);
                         list_del(&dev->unreg_list);
                         continue;
                 }
                 dev->dismantle = true;
                 BUG_ON(dev->reg_state != NETREG_REGISTERED);
         }
 
         /* If device is running, close it first. */
         list_for_each_entry(dev, head, unreg_list)
                 list_add_tail(&dev->close_list, &close_head);
         dev_close_many(&close_head, true);
 
         list_for_each_entry(dev, head, unreg_list) {
                 /* And unlink it from device chain. */
                 unlist_netdevice(dev);
 
                 dev->reg_state = NETREG_UNREGISTERING;
         }
 
         synchronize_net();
 
         list_for_each_entry(dev, head, unreg_list) {
                 struct sk_buff *skb = NULL;
 
                 /* Shutdown queueing discipline. */
                 dev_shutdown(dev);
 
 
                 /* Notify protocols, that we are about to destroy
                    this device. They should clean all the things.
                 */
                 call_netdevice_notifiers(NETDEV_UNREGISTER, dev);
 
                 if (!dev->rtnl_link_ops ||
                     dev->rtnl_link_state == RTNL_LINK_INITIALIZED)
                         skb = rtmsg_ifinfo_build_skb(RTM_DELLINK, dev, ~0U,
                                                      GFP_KERNEL);
 
                 /*
                  *      Flush the unicast and multicast chains
                  */
                 dev_uc_flush(dev);
                 dev_mc_flush(dev);
 
                 if (dev->netdev_ops->ndo_uninit)
                         dev->netdev_ops->ndo_uninit(dev);
 
                 if (skb)
                         rtmsg_ifinfo_send(skb, dev, GFP_KERNEL);
 
                 /* Notifier chain MUST detach us all upper devices. */
                 WARN_ON(netdev_has_any_upper_dev(dev));
 
                 /* Remove entries from kobject tree */
                 netdev_unregister_kobject(dev);
 #ifdef CONFIG_XPS
                 /* Remove XPS queueing entries */
                 netif_reset_xps_queues_gt(dev, 0);
 #endif
         }
 
         synchronize_net();
 
         list_for_each_entry(dev, head, unreg_list)
                 dev_put(dev);
 }
 
 static void rollback_registered(struct net_device *dev)
 {
         LIST_HEAD(single);
 
         list_add(&dev->unreg_list, &single);
         rollback_registered_many(&single);
         list_del(&single);
 }
 
 static netdev_features_t netdev_fix_features(struct net_device *dev,
         netdev_features_t features)
 {
         /* Fix illegal checksum combinations */
         if ((features & NETIF_F_HW_CSUM) &&
             (features & (NETIF_F_IP_CSUM|NETIF_F_IPV6_CSUM))) {
                 netdev_warn(dev, "mixed HW and IP checksum settings.\n");
                 features &= ~(NETIF_F_IP_CSUM|NETIF_F_IPV6_CSUM);
         }
 
         /* TSO requires that SG is present as well. */
         if ((features & NETIF_F_ALL_TSO) && !(features & NETIF_F_SG)) {
                 netdev_dbg(dev, "Dropping TSO features since no SG feature.\n");
                 features &= ~NETIF_F_ALL_TSO;
         }
 
         if ((features & NETIF_F_TSO) && !(features & NETIF_F_HW_CSUM) &&
                                         !(features & NETIF_F_IP_CSUM)) {
                 netdev_dbg(dev, "Dropping TSO features since no CSUM feature.\n");
                 features &= ~NETIF_F_TSO;
                 features &= ~NETIF_F_TSO_ECN;
         }
 
         if ((features & NETIF_F_TSO6) && !(features & NETIF_F_HW_CSUM) &&
                                          !(features & NETIF_F_IPV6_CSUM)) {
                 netdev_dbg(dev, "Dropping TSO6 features since no CSUM feature.\n");
                 features &= ~NETIF_F_TSO6;
         }
 
         /* TSO ECN requires that TSO is present as well. */
         if ((features & NETIF_F_ALL_TSO) == NETIF_F_TSO_ECN)
                 features &= ~NETIF_F_TSO_ECN;
 
         /* Software GSO depends on SG. */
         if ((features & NETIF_F_GSO) && !(features & NETIF_F_SG)) {
                 netdev_dbg(dev, "Dropping NETIF_F_GSO since no SG feature.\n");
                 features &= ~NETIF_F_GSO;
         }
 
         /* UFO needs SG and checksumming */
         if (features & NETIF_F_UFO) {
                 /* maybe split UFO into V4 and V6? */
                 if (!((features & NETIF_F_GEN_CSUM) ||
                     (features & (NETIF_F_IP_CSUM|NETIF_F_IPV6_CSUM))
                             == (NETIF_F_IP_CSUM|NETIF_F_IPV6_CSUM))) {
                         netdev_dbg(dev,
                                 "Dropping NETIF_F_UFO since no checksum offload features.\n");
                         features &= ~NETIF_F_UFO;
                 }
 
                 if (!(features & NETIF_F_SG)) {
                         netdev_dbg(dev,
                                 "Dropping NETIF_F_UFO since no NETIF_F_SG feature.\n");
                         features &= ~NETIF_F_UFO;
                 }
         }
 
 #ifdef CONFIG_NET_RX_BUSY_POLL
         if (dev->netdev_ops->ndo_busy_poll)
                 features |= NETIF_F_BUSY_POLL;
         else
 #endif
                 features &= ~NETIF_F_BUSY_POLL;
 
         return features;
 }
 
 int __netdev_update_features(struct net_device *dev)
 {
         netdev_features_t features;
         int err = 0;
 
         ASSERT_RTNL();
 
         features = netdev_get_wanted_features(dev);
 
         if (dev->netdev_ops->ndo_fix_features)
                 features = dev->netdev_ops->ndo_fix_features(dev, features);
 
         /* driver might be less strict about feature dependencies */
         features = netdev_fix_features(dev, features);
 
         if (dev->features == features)
                 return 0;
 
         netdev_dbg(dev, "Features changed: %pNF -> %pNF\n",
                 &dev->features, &features);
 
         if (dev->netdev_ops->ndo_set_features)
                 err = dev->netdev_ops->ndo_set_features(dev, features);
 
         if (unlikely(err < 0)) {
                 netdev_err(dev,
                         "set_features() failed (%d); wanted %pNF, left %pNF\n",
                         err, &features, &dev->features);
                 return -1;
         }
 
         if (!err)
                 dev->features = features;
 
         return 1;
 }
 
 /**
  *      netdev_update_features - recalculate device features
  *      @dev: the device to check
  *
  *      Recalculate dev->features set and send notifications if it
  *      has changed. Should be called after driver or hardware dependent
  *      conditions might have changed that influence the features.
  */
 void netdev_update_features(struct net_device *dev)
 {
         if (__netdev_update_features(dev))
                 netdev_features_change(dev);
 }
 EXPORT_SYMBOL(netdev_update_features);
 
 /**
  *      netdev_change_features - recalculate device features
  *      @dev: the device to check
  *
  *      Recalculate dev->features set and send notifications even
  *      if they have not changed. Should be called instead of
  *      netdev_update_features() if also dev->vlan_features might
  *      have changed to allow the changes to be propagated to stacked
  *      VLAN devices.
  */
 void netdev_change_features(struct net_device *dev)
 {
         __netdev_update_features(dev);
         netdev_features_change(dev);
 }
 EXPORT_SYMBOL(netdev_change_features);
 
 /**
  *      netif_stacked_transfer_operstate -      transfer operstate
  *      @rootdev: the root or lower level device to transfer state from
  *      @dev: the device to transfer operstate to
  *
  *      Transfer operational state from root to device. This is normally
  *      called when a stacking relationship exists between the root
  *      device and the device(a leaf device).
  */
 void netif_stacked_transfer_operstate(const struct net_device *rootdev,
                                         struct net_device *dev)
 {
         if (rootdev->operstate == IF_OPER_DORMANT)
                 netif_dormant_on(dev);
         else
                 netif_dormant_off(dev);
 
         if (netif_carrier_ok(rootdev)) {
                 if (!netif_carrier_ok(dev))
                         netif_carrier_on(dev);
         } else {
                 if (netif_carrier_ok(dev))
                         netif_carrier_off(dev);
         }
 }
 EXPORT_SYMBOL(netif_stacked_transfer_operstate);
 
 #ifdef CONFIG_SYSFS
 static int netif_alloc_rx_queues(struct net_device *dev)
 {
         unsigned int i, count = dev->num_rx_queues;
         struct netdev_rx_queue *rx;
         size_t sz = count * sizeof(*rx);
 
         BUG_ON(count < 1);
 
         rx = kzalloc(sz, GFP_KERNEL | __GFP_NOWARN | __GFP_REPEAT);
         if (!rx) {
                 rx = vzalloc(sz);
                 if (!rx)
                         return -ENOMEM;
         }
         dev->_rx = rx;
 
         for (i = 0; i < count; i++)
                 rx[i].dev = dev;
         return 0;
 }
 #endif
 
 static void netdev_init_one_queue(struct net_device *dev,
                                   struct netdev_queue *queue, void *_unused)
 {
         /* Initialize queue lock */
         spin_lock_init(&queue->_xmit_lock);
         netdev_set_xmit_lockdep_class(&queue->_xmit_lock, dev->type);
         queue->xmit_lock_owner = -1;
         netdev_queue_numa_node_write(queue, NUMA_NO_NODE);
         queue->dev = dev;
 #ifdef CONFIG_BQL
         dql_init(&queue->dql, HZ);
 #endif
 }
 
 static void netif_free_tx_queues(struct net_device *dev)
 {
         kvfree(dev->_tx);
 }
 
 static int netif_alloc_netdev_queues(struct net_device *dev)
 {
         unsigned int count = dev->num_tx_queues;
         struct netdev_queue *tx;
         size_t sz = count * sizeof(*tx);
 
         BUG_ON(count < 1 || count > 0xffff);
 
         tx = kzalloc(sz, GFP_KERNEL | __GFP_NOWARN | __GFP_REPEAT);
         if (!tx) {
                 tx = vzalloc(sz);
                 if (!tx)
                         return -ENOMEM;
         }
         dev->_tx = tx;
 
         netdev_for_each_tx_queue(dev, netdev_init_one_queue, NULL);
         spin_lock_init(&dev->tx_global_lock);
 
         return 0;
 }
 
 /**
  *      register_netdevice      - register a network device
  *      @dev: device to register
  *
  *      Take a completed network device structure and add it to the kernel
  *      interfaces. A %NETDEV_REGISTER message is sent to the netdev notifier
  *      chain. 0 is returned on success. A negative errno code is returned
  *      on a failure to set up the device, or if the name is a duplicate.
  *
  *      Callers must hold the rtnl semaphore. You may want
  *      register_netdev() instead of this.
  *
  *      BUGS:
  *      The locking appears insufficient to guarantee two parallel registers
  *      will not get the same name.
  *
  *      当网络子系统中高层要发送一个数据包时, 通过查找路由表得到接口信息, 比如
  *      eth0, 然后再到设备列表中查找对应的设备. 所以当一个 NIC 设备向系统注册后
  *      它将纳入子系统的高层代码之中, 其携带的设备方法随时可能被高层代码所征用
  *
  */
 
 int register_netdevice(struct net_device *dev)
 {
         int ret;
         struct net *net = dev_net(dev);
 
         BUG_ON(dev_boot_phase);
         ASSERT_RTNL();
 
         might_sleep();
 
         /* When net_device's are persistent, this will be fatal. */
         BUG_ON(dev->reg_state != NETREG_UNINITIALIZED);
         BUG_ON(!net);
 
         spin_lock_init(&dev->addr_list_lock);
         netdev_set_addr_lockdep_class(dev);
 
         ret = dev_get_valid_name(net, dev, dev->name);
         if (ret < 0)
                 goto out;
 
         /* Init, if this function is available */
         if (dev->netdev_ops->ndo_init) {
                 ret = dev->netdev_ops->ndo_init(dev);
                 if (ret) {
                         if (ret > 0)
                                 ret = -EIO;
                         goto out;
                 }
         }
 
         if (((dev->hw_features | dev->features) &
              NETIF_F_HW_VLAN_CTAG_FILTER) &&
             (!dev->netdev_ops->ndo_vlan_rx_add_vid ||
              !dev->netdev_ops->ndo_vlan_rx_kill_vid)) {
                 netdev_WARN(dev, "Buggy VLAN acceleration in driver!\n");
                 ret = -EINVAL;
                 goto err_uninit;
         }
 
         ret = -EBUSY;
         if (!dev->ifindex)
                 dev->ifindex = dev_new_index(net);
         else if (__dev_get_by_index(net, dev->ifindex))
                 goto err_uninit;
 
         /* Transfer changeable features to wanted_features and enable
          * software offloads (GSO and GRO).
          */
         dev->hw_features |= NETIF_F_SOFT_FEATURES;
         dev->features |= NETIF_F_SOFT_FEATURES;
         dev->wanted_features = dev->features & dev->hw_features;
 
         if (!(dev->flags & IFF_LOOPBACK)) {
                 dev->hw_features |= NETIF_F_NOCACHE_COPY;
         }
 
         /* Make NETIF_F_HIGHDMA inheritable to VLAN devices.
          */
         dev->vlan_features |= NETIF_F_HIGHDMA;
 
         /* Make NETIF_F_SG inheritable to tunnel devices.
          */
         dev->hw_enc_features |= NETIF_F_SG;
 
         /* Make NETIF_F_SG inheritable to MPLS.
          */
         dev->mpls_features |= NETIF_F_SG;
 
         ret = call_netdevice_notifiers(NETDEV_POST_INIT, dev);
         ret = notifier_to_errno(ret);
         if (ret)
                 goto err_uninit;
 
         //通过设备驱动模型向系统中添加 dev, 将 dev 变成一个内核对象,
         //继而linux 设备模型来操控当前的网络设备
         ret = netdev_register_kobject(dev);
         if (ret)
                 goto err_uninit;
         dev->reg_state = NETREG_REGISTERED;
 
         __netdev_update_features(dev);
 
         /*
          *      Default initial state at registry is that the
          *      device is present.
          */
 
         set_bit(__LINK_STATE_PRESENT, &dev->state);
 
         linkwatch_init_dev(dev);
 
         //
         dev_init_scheduler(dev);
         dev_hold(dev);
         //将 dev 加入几个特定命名空间的几个散列表中, 当网络子系统高层的代码需要发送数据包的时候, 能通过这几个散列表找到特定的网络设备
         list_netdevice(dev);
         add_device_randomness(dev->dev_addr, dev->addr_len);
 
         /* If the device has permanent device address, driver should
          * set dev_addr and also addr_assign_type should be set to
          * NET_ADDR_PERM (default value).
          */
         if (dev->addr_assign_type == NET_ADDR_PERM)
                 memcpy(dev->perm_addr, dev->dev_addr, dev->addr_len);
 
         /* Notify protocols, that a new device appeared. */
         //经过此处调用, dev->reg_state 成为了 NETREG_REGISTERED
         ret = call_netdevice_notifiers(NETDEV_REGISTER, dev);
         ret = notifier_to_errno(ret);
         if (ret) {
                 rollback_registered(dev);
                 dev->reg_state = NETREG_UNREGISTERED;
         }
         /*
          *      Prevent userspace races by waiting until the network
          *      device is fully setup before sending notifications.
          */
         if (!dev->rtnl_link_ops ||
             dev->rtnl_link_state == RTNL_LINK_INITIALIZED)
                 rtmsg_ifinfo(RTM_NEWLINK, dev, ~0U, GFP_KERNEL);
 
 out:
         return ret;
 
 err_uninit:
         if (dev->netdev_ops->ndo_uninit)
                 dev->netdev_ops->ndo_uninit(dev);
         goto out;
 }
 EXPORT_SYMBOL(register_netdevice);
 
 /**
  *      init_dummy_netdev       - init a dummy network device for NAPI
  *      @dev: device to init
  *
  *      This takes a network device structure and initialize the minimum
  *      amount of fields so it can be used to schedule NAPI polls without
  *      registering a full blown interface. This is to be used by drivers
  *      that need to tie several hardware interfaces to a single NAPI
  *      poll scheduler due to HW limitations.
  */
 int init_dummy_netdev(struct net_device *dev)
 {
         /* Clear everything. Note we don't initialize spinlocks
          * are they aren't supposed to be taken by any of the
          * NAPI code and this dummy netdev is supposed to be
          * only ever used for NAPI polls
          */
         memset(dev, 0, sizeof(struct net_device));
 
         /* make sure we BUG if trying to hit standard
          * register/unregister code path
          */
         dev->reg_state = NETREG_DUMMY;
 
         /* NAPI wants this */
         INIT_LIST_HEAD(&dev->napi_list);
 
         /* a dummy interface is started by default */
         set_bit(__LINK_STATE_PRESENT, &dev->state);
         set_bit(__LINK_STATE_START, &dev->state);
 
         /* Note : We dont allocate pcpu_refcnt for dummy devices,
          * because users of this 'device' dont need to change
          * its refcount.
          */
 
         return 0;
 }
 EXPORT_SYMBOL_GPL(init_dummy_netdev);
 
 
 /**
  *      register_netdev - register a network device
  *      @dev: device to register
  *
  *      Take a completed network device structure and add it to the kernel
  *      interfaces. A %NETDEV_REGISTER message is sent to the netdev notifier
  *      chain. 0 is returned on success. A negative errno code is returned
  *      on a failure to set up the device, or if the name is a duplicate.
  *
  *      This is a wrapper around register_netdevice that takes the rtnl semaphore
  *      and expands the device name if you passed a format string to
  *      alloc_netdev.
  */
 int register_netdev(struct net_device *dev)
 {
         int err;
 
         rtnl_lock();
         err = register_netdevice(dev);
         rtnl_unlock();
         return err;
 }
 EXPORT_SYMBOL(register_netdev);
 
 int netdev_refcnt_read(const struct net_device *dev)
 {
         int i, refcnt = 0;
 
         for_each_possible_cpu(i)
                 refcnt += *per_cpu_ptr(dev->pcpu_refcnt, i);
         return refcnt;
 }
 EXPORT_SYMBOL(netdev_refcnt_read);
 
 /**
  * netdev_wait_allrefs - wait until all references are gone.
  * @dev: target net_device
  *
  * This is called when unregistering network devices.
  *
  * Any protocol or device that holds a reference should register
  * for netdevice notification, and cleanup and put back the
  * reference if they receive an UNREGISTER event.
  * We can get stuck here if buggy protocols don't correctly
  * call dev_put.
  */
 static void netdev_wait_allrefs(struct net_device *dev)
 {
         unsigned long rebroadcast_time, warning_time;
         int refcnt;
 
         linkwatch_forget_dev(dev);
 
         rebroadcast_time = warning_time = jiffies;
         refcnt = netdev_refcnt_read(dev);
 
         while (refcnt != 0) {
                 if (time_after(jiffies, rebroadcast_time + 1 * HZ)) {
                         rtnl_lock();
 
                         /* Rebroadcast unregister notification */
                         call_netdevice_notifiers(NETDEV_UNREGISTER, dev);
 
                         __rtnl_unlock();
                         rcu_barrier();
                         rtnl_lock();
 
                         call_netdevice_notifiers(NETDEV_UNREGISTER_FINAL, dev);
                         if (test_bit(__LINK_STATE_LINKWATCH_PENDING,
                                      &dev->state)) {
                                 /* We must not have linkwatch events
                                  * pending on unregister. If this
                                  * happens, we simply run the queue
                                  * unscheduled, resulting in a noop
                                  * for this device.
                                  */
                                 linkwatch_run_queue();
                         }
 
                         __rtnl_unlock();
 
                         rebroadcast_time = jiffies;
                 }
 
                 msleep(250);
 
                 refcnt = netdev_refcnt_read(dev);
 
                 if (time_after(jiffies, warning_time + 10 * HZ)) {
                         pr_emerg("unregister_netdevice: waiting for %s to become free. Usage count = %d\n",
                                  dev->name, refcnt);
                         warning_time = jiffies;
                 }
         }
 }
 
 /* The sequence is:
  *
  *      rtnl_lock();
  *      ...
  *      register_netdevice(x1);
  *      register_netdevice(x2);
  *      ...
  *      unregister_netdevice(y1);
  *      unregister_netdevice(y2);
  *      ...
  *      rtnl_unlock();
  *      free_netdev(y1);
  *      free_netdev(y2);
  *
  * We are invoked by rtnl_unlock().
  * This allows us to deal with problems:
  * 1) We can delete sysfs objects which invoke hotplug
  *    without deadlocking with linkwatch via keventd.
  * 2) Since we run with the RTNL semaphore not held, we can sleep
  *    safely in order to wait for the netdev refcnt to drop to zero.
  *
  * We must not return until all unregister events added during
  * the interval the lock was held have been completed.
  */
 void netdev_run_todo(void)
 {
         struct list_head list;
 
         /* Snapshot list, allow later requests */
         list_replace_init(&net_todo_list, &list);
 
         __rtnl_unlock();
 
 
         /* Wait for rcu callbacks to finish before next phase */
         if (!list_empty(&list))
                 rcu_barrier();
 
         while (!list_empty(&list)) {
                 struct net_device *dev
                         = list_first_entry(&list, struct net_device, todo_list);
                 list_del(&dev->todo_list);
 
                 rtnl_lock();
                 call_netdevice_notifiers(NETDEV_UNREGISTER_FINAL, dev);
                 __rtnl_unlock();
 
                 if (unlikely(dev->reg_state != NETREG_UNREGISTERING)) {
                         pr_err("network todo '%s' but state %d\n",
                                dev->name, dev->reg_state);
                         dump_stack();
                         continue;
                 }
 
                 dev->reg_state = NETREG_UNREGISTERED;
 
                 on_each_cpu(flush_backlog, dev, 1);
 
                 netdev_wait_allrefs(dev);
 
                 /* paranoia */
                 BUG_ON(netdev_refcnt_read(dev));
                 BUG_ON(!list_empty(&dev->ptype_all));
                 BUG_ON(!list_empty(&dev->ptype_specific));
                 WARN_ON(rcu_access_pointer(dev->ip_ptr));
                 WARN_ON(rcu_access_pointer(dev->ip6_ptr));
                 WARN_ON(dev->dn_ptr);
 
                 if (dev->destructor)
                         dev->destructor(dev);
 
                 /* Report a network device has been unregistered */
                 rtnl_lock();
                 dev_net(dev)->dev_unreg_count--;
                 __rtnl_unlock();
                 wake_up(&netdev_unregistering_wq);
 
                 /* Free network device */
                 kobject_put(&dev->dev.kobj);
         }
 }
 
 /* Convert net_device_stats to rtnl_link_stats64.  They have the same
  * fields in the same order, with only the type differing.
  */
 void netdev_stats_to_stats64(struct rtnl_link_stats64 *stats64,
                              const struct net_device_stats *netdev_stats)
 {
 #if BITS_PER_LONG == 64
         BUILD_BUG_ON(sizeof(*stats64) != sizeof(*netdev_stats));
         memcpy(stats64, netdev_stats, sizeof(*stats64));
 #else
         size_t i, n = sizeof(*stats64) / sizeof(u64);
         const unsigned long *src = (const unsigned long *)netdev_stats;
         u64 *dst = (u64 *)stats64;
 
         BUILD_BUG_ON(sizeof(*netdev_stats) / sizeof(unsigned long) !=
                      sizeof(*stats64) / sizeof(u64));
         for (i = 0; i < n; i++)
                 dst[i] = src[i];
 #endif
 }
 EXPORT_SYMBOL(netdev_stats_to_stats64);
 
 /**
  *      dev_get_stats   - get network device statistics
  *      @dev: device to get statistics from
  *      @storage: place to store stats
  *
  *      Get network statistics from device. Return @storage.
  *      The device driver may provide its own method by setting
  *      dev->netdev_ops->get_stats64 or dev->netdev_ops->get_stats;
  *      otherwise the internal statistics structure is used.
  */
 struct rtnl_link_stats64 *dev_get_stats(struct net_device *dev,
                                         struct rtnl_link_stats64 *storage)
 {
         const struct net_device_ops *ops = dev->netdev_ops;
 
         if (ops->ndo_get_stats64) {
                 memset(storage, 0, sizeof(*storage));
                 ops->ndo_get_stats64(dev, storage);
         } else if (ops->ndo_get_stats) {
                 netdev_stats_to_stats64(storage, ops->ndo_get_stats(dev));
         } else {
                 netdev_stats_to_stats64(storage, &dev->stats);
         }
         storage->rx_dropped += atomic_long_read(&dev->rx_dropped);
         storage->tx_dropped += atomic_long_read(&dev->tx_dropped);
         return storage;
 }
 EXPORT_SYMBOL(dev_get_stats);
 
 struct netdev_queue *dev_ingress_queue_create(struct net_device *dev)
 {
         struct netdev_queue *queue = dev_ingress_queue(dev);
 
 #ifdef CONFIG_NET_CLS_ACT
         if (queue)
                 return queue;
         queue = kzalloc(sizeof(*queue), GFP_KERNEL);
         if (!queue)
                 return NULL;
         netdev_init_one_queue(dev, queue, NULL);
         RCU_INIT_POINTER(queue->qdisc, &noop_qdisc);
         queue->qdisc_sleeping = &noop_qdisc;
         rcu_assign_pointer(dev->ingress_queue, queue);
 #endif
         return queue;
 }
 
 static const struct ethtool_ops default_ethtool_ops;
 
 void netdev_set_default_ethtool_ops(struct net_device *dev,
                                     const struct ethtool_ops *ops)
 {
         if (dev->ethtool_ops == &default_ethtool_ops)
                 dev->ethtool_ops = ops;
 }
 EXPORT_SYMBOL_GPL(netdev_set_default_ethtool_ops);
 
 void netdev_freemem(struct net_device *dev)
 {
         char *addr = (char *)dev - dev->padded;
 
         kvfree(addr);
 }
 
 /**
  *      alloc_netdev_mqs - allocate network device
  *      @sizeof_priv:           size of private data to allocate space for
  *      @name:                  device name format string
  *      @name_assign_type:      origin of device name
  *      @setup:                 callback to initialize device
  *      @txqs:                  the number of TX subqueues to allocate
  *      @rxqs:                  the number of RX subqueues to allocate
  *
  *      Allocates a struct net_device with private data area for driver use
  *      and performs basic initialization.  Also allocates subqueue structs
  *      for each queue on the device.
  */
 struct net_device *alloc_netdev_mqs(int sizeof_priv, const char *name,
                 unsigned char name_assign_type,
                 void (*setup)(struct net_device *),
                 unsigned int txqs, unsigned int rxqs)
 {
         struct net_device *dev;
         size_t alloc_size;
         struct net_device *p;
 
         BUG_ON(strlen(name) >= sizeof(dev->name));
 
         if (txqs < 1) {
                 pr_err("alloc_netdev: Unable to allocate device with zero queues\n");
                 return NULL;
         }
 
 #ifdef CONFIG_SYSFS
         if (rxqs < 1) {
                 pr_err("alloc_netdev: Unable to allocate device with zero RX queues\n");
                 return NULL;
         }
 #endif
 
         alloc_size = sizeof(struct net_device);
         if (sizeof_priv) {
                 /* ensure 32-byte alignment of private area */
                 alloc_size = ALIGN(alloc_size, NETDEV_ALIGN);
                 alloc_size += sizeof_priv;
         }
         /* ensure 32-byte alignment of whole construct */
         alloc_size += NETDEV_ALIGN - 1;
 
         p = kzalloc(alloc_size, GFP_KERNEL | __GFP_NOWARN | __GFP_REPEAT);
         if (!p)
                 p = vzalloc(alloc_size);
         if (!p)
                 return NULL;
 
         dev = PTR_ALIGN(p, NETDEV_ALIGN);
         dev->padded = (char *)dev - (char *)p;
 
         dev->pcpu_refcnt = alloc_percpu(int);
         if (!dev->pcpu_refcnt)
                 goto free_dev;
 
         if (dev_addr_init(dev))
                 goto free_pcpu;
 
         dev_mc_init(dev);
         dev_uc_init(dev);
 
         dev_net_set(dev, &init_net);
 
         dev->gso_max_size = GSO_MAX_SIZE;
         dev->gso_max_segs = GSO_MAX_SEGS;
         dev->gso_min_segs = 0;
 
         INIT_LIST_HEAD(&dev->napi_list);
         INIT_LIST_HEAD(&dev->unreg_list);
         INIT_LIST_HEAD(&dev->close_list);
         INIT_LIST_HEAD(&dev->link_watch_list);
         INIT_LIST_HEAD(&dev->adj_list.upper);
         INIT_LIST_HEAD(&dev->adj_list.lower);
         INIT_LIST_HEAD(&dev->all_adj_list.upper);
         INIT_LIST_HEAD(&dev->all_adj_list.lower);
         INIT_LIST_HEAD(&dev->ptype_all);
         INIT_LIST_HEAD(&dev->ptype_specific);
         dev->priv_flags = IFF_XMIT_DST_RELEASE | IFF_XMIT_DST_RELEASE_PERM;
         setup(dev);
 
         dev->num_tx_queues = txqs;
         dev->real_num_tx_queues = txqs;
         if (netif_alloc_netdev_queues(dev))
                 goto free_all;
 
 #ifdef CONFIG_SYSFS
         dev->num_rx_queues = rxqs;
         dev->real_num_rx_queues = rxqs;
         if (netif_alloc_rx_queues(dev))
                 goto free_all;
 #endif
 
         strcpy(dev->name, name);
         dev->name_assign_type = name_assign_type;
         dev->group = INIT_NETDEV_GROUP;
         if (!dev->ethtool_ops)
                 dev->ethtool_ops = &default_ethtool_ops;
         return dev;
 
 free_all:
         free_netdev(dev);
         return NULL;
 
 free_pcpu:
         free_percpu(dev->pcpu_refcnt);
 free_dev:
         netdev_freemem(dev);
         return NULL;
 }
 EXPORT_SYMBOL(alloc_netdev_mqs);
 
 /**
  *      free_netdev - free network device
  *      @dev: device
  *
  *      This function does the last stage of destroying an allocated device
  *      interface. The reference to the device object is released.
  *      If this is the last reference then it will be freed.
  */
 void free_netdev(struct net_device *dev)
 {
         struct napi_struct *p, *n;
 
         netif_free_tx_queues(dev);
 #ifdef CONFIG_SYSFS
         kvfree(dev->_rx);
 #endif
 
         kfree(rcu_dereference_protected(dev->ingress_queue, 1));
 
         /* Flush device addresses */
         dev_addr_flush(dev);
 
         list_for_each_entry_safe(p, n, &dev->napi_list, dev_list)
                 netif_napi_del(p);
 
         free_percpu(dev->pcpu_refcnt);
         dev->pcpu_refcnt = NULL;
 
         /*  Compatibility with error handling in drivers */
         if (dev->reg_state == NETREG_UNINITIALIZED) {
                 netdev_freemem(dev);
                 return;
         }
 
         BUG_ON(dev->reg_state != NETREG_UNREGISTERED);
         dev->reg_state = NETREG_RELEASED;
 
         /* will free via device release */
         put_device(&dev->dev);
 }
 EXPORT_SYMBOL(free_netdev);
 
 /**
  *      synchronize_net -  Synchronize with packet receive processing
  *
  *      Wait for packets currently being received to be done.
  *      Does not block later packets from starting.
  */
 void synchronize_net(void)
 {
         might_sleep();
         if (rtnl_is_locked())
                 synchronize_rcu_expedited();
         else
                 synchronize_rcu();
 }
 EXPORT_SYMBOL(synchronize_net);
 
 /**
  *      unregister_netdevice_queue - remove device from the kernel
  *      @dev: device
  *      @head: list
  *
  *      This function shuts down a device interface and removes it
  *      from the kernel tables.
  *      If head not NULL, device is queued to be unregistered later.
  *
  *      Callers must hold the rtnl semaphore.  You may want
  *      unregister_netdev() instead of this.
  */
 
 void unregister_netdevice_queue(struct net_device *dev, struct list_head *head)
 {
         ASSERT_RTNL();
 
         if (head) {
                 list_move_tail(&dev->unreg_list, head);
         } else {
                 rollback_registered(dev);
                 /* Finish processing unregister after unlock */
                 net_set_todo(dev);
         }
 }
 EXPORT_SYMBOL(unregister_netdevice_queue);
 
 /**
  *      unregister_netdevice_many - unregister many devices
  *      @head: list of devices
  *
  *  Note: As most callers use a stack allocated list_head,
  *  we force a list_del() to make sure stack wont be corrupted later.
  */
 void unregister_netdevice_many(struct list_head *head)
 {
         struct net_device *dev;
 
         if (!list_empty(head)) {
                 rollback_registered_many(head);
                 list_for_each_entry(dev, head, unreg_list)
                         net_set_todo(dev);
                 list_del(head);
         }
 }
 EXPORT_SYMBOL(unregister_netdevice_many);
 
 /**
  *      unregister_netdev - remove device from the kernel
  *      @dev: device
  *
  *      This function shuts down a device interface and removes it
  *      from the kernel tables.
  *
  *      This is just a wrapper for unregister_netdevice that takes
  *      the rtnl semaphore.  In general you want to use this and not
  *      unregister_netdevice.
  */
 void unregister_netdev(struct net_device *dev)
 {
         rtnl_lock();
         unregister_netdevice(dev);
         rtnl_unlock();
 }
 EXPORT_SYMBOL(unregister_netdev);
 
 /**
  *      dev_change_net_namespace - move device to different nethost namespace
  *      @dev: device
  *      @net: network namespace
  *      @pat: If not NULL name pattern to try if the current device name
  *            is already taken in the destination network namespace.
  *
  *      This function shuts down a device interface and moves it
  *      to a new network namespace. On success 0 is returned, on
  *      a failure a netagive errno code is returned.
  *
  *      Callers must hold the rtnl semaphore.
  */
 
 int dev_change_net_namespace(struct net_device *dev, struct net *net, const char *pat)
 {
         int err;
 
         ASSERT_RTNL();
 
         /* Don't allow namespace local devices to be moved. */
         err = -EINVAL;
         if (dev->features & NETIF_F_NETNS_LOCAL)
                 goto out;
 
         /* Ensure the device has been registrered */
         if (dev->reg_state != NETREG_REGISTERED)
                 goto out;
 
         /* Get out if there is nothing todo */
         err = 0;
         if (net_eq(dev_net(dev), net))
                 goto out;
 
         /* Pick the destination device name, and ensure
          * we can use it in the destination network namespace.
          */
         err = -EEXIST;
         if (__dev_get_by_name(net, dev->name)) {
                 /* We get here if we can't use the current device name */
                 if (!pat)
                         goto out;
                 if (dev_get_valid_name(net, dev, pat) < 0)
                         goto out;
         }
 
         /*
          * And now a mini version of register_netdevice unregister_netdevice.
          */
 
         /* If device is running close it first. */
         dev_close(dev);
 
         /* And unlink it from device chain */
         err = -ENODEV;
         unlist_netdevice(dev);
 
         synchronize_net();
 
         /* Shutdown queueing discipline. */
         dev_shutdown(dev);
 
         /* Notify protocols, that we are about to destroy
            this device. They should clean all the things.
 
            Note that dev->reg_state stays at NETREG_REGISTERED.
            This is wanted because this way 8021q and macvlan know
            the device is just moving and can keep their slaves up.
         */
         call_netdevice_notifiers(NETDEV_UNREGISTER, dev);
         rcu_barrier();
         call_netdevice_notifiers(NETDEV_UNREGISTER_FINAL, dev);
         rtmsg_ifinfo(RTM_DELLINK, dev, ~0U, GFP_KERNEL);
 
         /*
          *      Flush the unicast and multicast chains
          */
         dev_uc_flush(dev);
         dev_mc_flush(dev);
 
         /* Send a netdev-removed uevent to the old namespace */
         kobject_uevent(&dev->dev.kobj, KOBJ_REMOVE);
         netdev_adjacent_del_links(dev);
 
         /* Actually switch the network namespace */
         dev_net_set(dev, net);
 
         /* If there is an ifindex conflict assign a new one */
         if (__dev_get_by_index(net, dev->ifindex))
                 dev->ifindex = dev_new_index(net);
 
         /* Send a netdev-add uevent to the new namespace */
         kobject_uevent(&dev->dev.kobj, KOBJ_ADD);
         netdev_adjacent_add_links(dev);
 
         /* Fixup kobjects */
         err = device_rename(&dev->dev, dev->name);
         WARN_ON(err);
 
         /* Add the device back in the hashes */
         list_netdevice(dev);
 
         /* Notify protocols, that a new device appeared. */
         call_netdevice_notifiers(NETDEV_REGISTER, dev);
 
         /*
          *      Prevent userspace races by waiting until the network
          *      device is fully setup before sending notifications.
          */
         rtmsg_ifinfo(RTM_NEWLINK, dev, ~0U, GFP_KERNEL);
 
         synchronize_net();
         err = 0;
 out:
         return err;
 }
 EXPORT_SYMBOL_GPL(dev_change_net_namespace);
 
 static int dev_cpu_callback(struct notifier_block *nfb,
                             unsigned long action,
                             void *ocpu)
 {
         struct sk_buff **list_skb;
         struct sk_buff *skb;
         unsigned int cpu, oldcpu = (unsigned long)ocpu;
         struct softnet_data *sd, *oldsd;
 
         if (action != CPU_DEAD && action != CPU_DEAD_FROZEN)
                 return NOTIFY_OK;
 
         local_irq_disable();
         cpu = smp_processor_id();
         sd = &per_cpu(softnet_data, cpu);
         oldsd = &per_cpu(softnet_data, oldcpu);
 
         /* Find end of our completion_queue. */
         list_skb = &sd->completion_queue;
         while (*list_skb)
                 list_skb = &(*list_skb)->next;
         /* Append completion queue from offline CPU. */
         *list_skb = oldsd->completion_queue;
         oldsd->completion_queue = NULL;
 
         /* Append output queue from offline CPU. */
         if (oldsd->output_queue) {
                 *sd->output_queue_tailp = oldsd->output_queue;
                 sd->output_queue_tailp = oldsd->output_queue_tailp;
                 oldsd->output_queue = NULL;
                 oldsd->output_queue_tailp = &oldsd->output_queue;
         }
         /* Append NAPI poll list from offline CPU, with one exception :
          * process_backlog() must be called by cpu owning percpu backlog.
          * We properly handle process_queue & input_pkt_queue later.
          */
         while (!list_empty(&oldsd->poll_list)) {
                 struct napi_struct *napi = list_first_entry(&oldsd->poll_list,
                                                             struct napi_struct,
                                                             poll_list);
 
                 list_del_init(&napi->poll_list);
                 if (napi->poll == process_backlog)
                         napi->state = 0;
                 else
                         ____napi_schedule(sd, napi);
         }
 
         raise_softirq_irqoff(NET_TX_SOFTIRQ);
         local_irq_enable();
 
         /* Process offline CPU's input_pkt_queue */
         while ((skb = __skb_dequeue(&oldsd->process_queue))) {
                 netif_rx_ni(skb);
                 input_queue_head_incr(oldsd);
         }
         while ((skb = skb_dequeue(&oldsd->input_pkt_queue))) {
                 netif_rx_ni(skb);
                 input_queue_head_incr(oldsd);
         }
 
         return NOTIFY_OK;
 }
 
 
 /**
  *      netdev_increment_features - increment feature set by one
  *      @all: current feature set
  *      @one: new feature set
  *      @mask: mask feature set
  *
  *      Computes a new feature set after adding a device with feature set
  *      @one to the master device with current feature set @all.  Will not
  *      enable anything that is off in @mask. Returns the new feature set.
  */
 netdev_features_t netdev_increment_features(netdev_features_t all,
         netdev_features_t one, netdev_features_t mask)
 {
         if (mask & NETIF_F_GEN_CSUM)
                 mask |= NETIF_F_ALL_CSUM;
         mask |= NETIF_F_VLAN_CHALLENGED;
 
         all |= one & (NETIF_F_ONE_FOR_ALL|NETIF_F_ALL_CSUM) & mask;
         all &= one | ~NETIF_F_ALL_FOR_ALL;
 
         /* If one device supports hw checksumming, set for all. */
         if (all & NETIF_F_GEN_CSUM)
                 all &= ~(NETIF_F_ALL_CSUM & ~NETIF_F_GEN_CSUM);
 
         return all;
 }
 EXPORT_SYMBOL(netdev_increment_features);
 
 static struct hlist_head * __net_init netdev_create_hash(void)
 {
         int i;
         struct hlist_head *hash;
 
         hash = kmalloc(sizeof(*hash) * NETDEV_HASHENTRIES, GFP_KERNEL);
         if (hash != NULL)
                 for (i = 0; i < NETDEV_HASHENTRIES; i++)
                         INIT_HLIST_HEAD(&hash[i]);
 
         return hash;
 }
 
 /* Initialize per network namespace state */
 static int __net_init netdev_init(struct net *net)
 {
         if (net != &init_net)
                 INIT_LIST_HEAD(&net->dev_base_head);
 
         net->dev_name_head = netdev_create_hash();
         if (net->dev_name_head == NULL)
                 goto err_name;
 
         net->dev_index_head = netdev_create_hash();
         if (net->dev_index_head == NULL)
                 goto err_idx;
 
         return 0;
 
 err_idx:
         kfree(net->dev_name_head);
 err_name:
         return -ENOMEM;
 }
 
 /**
  *      netdev_drivername - network driver for the device
  *      @dev: network device
  *
  *      Determine network driver for device.
  */
 const char *netdev_drivername(const struct net_device *dev)
 {
         const struct device_driver *driver;
         const struct device *parent;
         const char *empty = "";
 
         parent = dev->dev.parent;
         if (!parent)
                 return empty;
 
         driver = parent->driver;
         if (driver && driver->name)
                 return driver->name;
         return empty;
 }
 
 static void __netdev_printk(const char *level, const struct net_device *dev,
                             struct va_format *vaf)
 {
         if (dev && dev->dev.parent) {
                 dev_printk_emit(level[1] - '',
                                 dev->dev.parent,
                                 "%s %s %s%s: %pV",
                                 dev_driver_string(dev->dev.parent),
                                 dev_name(dev->dev.parent),
                                 netdev_name(dev), netdev_reg_state(dev),
                                 vaf);
         } else if (dev) {
                 printk("%s%s%s: %pV",
                        level, netdev_name(dev), netdev_reg_state(dev), vaf);
         } else {
                 printk("%s(NULL net_device): %pV", level, vaf);
         }
 }
 
 void netdev_printk(const char *level, const struct net_device *dev,
                    const char *format, ...)
 {
         struct va_format vaf;
         va_list args;
 
         va_start(args, format);
 
         vaf.fmt = format;
         vaf.va = &args;
 
         __netdev_printk(level, dev, &vaf);
 
         va_end(args);
 }
 EXPORT_SYMBOL(netdev_printk);
 
 #define define_netdev_printk_level(func, level)                 \
 void func(const struct net_device *dev, const char *fmt, ...)   \
 {                                                               \
         struct va_format vaf;                                   \
         va_list args;                                           \
                                                                 \
         va_start(args, fmt);                                    \
                                                                 \
         vaf.fmt = fmt;                                          \
         vaf.va = &args;                                         \
                                                                 \
         __netdev_printk(level, dev, &vaf);                      \
                                                                 \
         va_end(args);                                           \
 }                                                               \
 EXPORT_SYMBOL(func);
 
 define_netdev_printk_level(netdev_emerg, KERN_EMERG);
 define_netdev_printk_level(netdev_alert, KERN_ALERT);
 define_netdev_printk_level(netdev_crit, KERN_CRIT);
 define_netdev_printk_level(netdev_err, KERN_ERR);
 define_netdev_printk_level(netdev_warn, KERN_WARNING);
 define_netdev_printk_level(netdev_notice, KERN_NOTICE);
 define_netdev_printk_level(netdev_info, KERN_INFO);
 
 static void __net_exit netdev_exit(struct net *net)
 {
         kfree(net->dev_name_head);
         kfree(net->dev_index_head);
 }
 
 static struct pernet_operations __net_initdata netdev_net_ops = {
         .init = netdev_init,
         .exit = netdev_exit,
 };
 
 static void __net_exit default_device_exit(struct net *net)
 {
         struct net_device *dev, *aux;
         /*
          * Push all migratable network devices back to the
          * initial network namespace
          */
         rtnl_lock();
         for_each_netdev_safe(net, dev, aux) {
                 int err;
                 char fb_name[IFNAMSIZ];
 
                 /* Ignore unmoveable devices (i.e. loopback) */
                 if (dev->features & NETIF_F_NETNS_LOCAL)
                         continue;
 
                 /* Leave virtual devices for the generic cleanup */
                 if (dev->rtnl_link_ops)
                         continue;
 
                 /* Push remaining network devices to init_net */
                 snprintf(fb_name, IFNAMSIZ, "dev%d", dev->ifindex);
                 err = dev_change_net_namespace(dev, &init_net, fb_name);
                 if (err) {
                         pr_emerg("%s: failed to move %s to init_net: %d\n",
                                  __func__, dev->name, err);
                         BUG();
                 }
         }
         rtnl_unlock();
 }
 
 static void __net_exit rtnl_lock_unregistering(struct list_head *net_list)
 {
         /* Return with the rtnl_lock held when there are no network
          * devices unregistering in any network namespace in net_list.
          */
         struct net *net;
         bool unregistering;
         DEFINE_WAIT_FUNC(wait, woken_wake_function);
 
         add_wait_queue(&netdev_unregistering_wq, &wait);
         for (;;) {
                 unregistering = false;
                 rtnl_lock();
                 list_for_each_entry(net, net_list, exit_list) {
                         if (net->dev_unreg_count > 0) {
                                 unregistering = true;
                                 break;
                         }
                 }
                 if (!unregistering)
                         break;
                 __rtnl_unlock();
 
                 wait_woken(&wait, TASK_UNINTERRUPTIBLE, MAX_SCHEDULE_TIMEOUT);
         }
         remove_wait_queue(&netdev_unregistering_wq, &wait);
 }
 
 static void __net_exit default_device_exit_batch(struct list_head *net_list)
 {
         /* At exit all network devices most be removed from a network
          * namespace.  Do this in the reverse order of registration.
          * Do this across as many network namespaces as possible to
          * improve batching efficiency.
          */
         struct net_device *dev;
         struct net *net;
         LIST_HEAD(dev_kill_list);
 
         /* To prevent network device cleanup code from dereferencing
          * loopback devices or network devices that have been freed
          * wait here for all pending unregistrations to complete,
          * before unregistring the loopback device and allowing the
          * network namespace be freed.
          *
          * The netdev todo list containing all network devices
          * unregistrations that happen in default_device_exit_batch
          * will run in the rtnl_unlock() at the end of
          * default_device_exit_batch.
          */
         rtnl_lock_unregistering(net_list);
         list_for_each_entry(net, net_list, exit_list) {
                 for_each_netdev_reverse(net, dev) {
                         if (dev->rtnl_link_ops && dev->rtnl_link_ops->dellink)
                                 dev->rtnl_link_ops->dellink(dev, &dev_kill_list);
                         else
                                 unregister_netdevice_queue(dev, &dev_kill_list);
                 }
         }
         unregister_netdevice_many(&dev_kill_list);
         rtnl_unlock();
 }
 
 static struct pernet_operations __net_initdata default_device_ops = {
         .exit = default_device_exit,
         .exit_batch = default_device_exit_batch,
 };
 
 /*
  *      Initialize the DEV module. At boot time this walks the device list and
  *      unhooks any devices that fail to initialise (normally hardware not
  *      present) and leaves us with a valid list of present and active devices.
  *
  */
 
 /*
  *       This is called single threaded during boot, so no need
  *       to take the rtnl semaphore.
  */
 static int __init net_dev_init(void)
 {
         int i, rc = -ENOMEM;
 
         BUG_ON(!dev_boot_phase);
 
         if (dev_proc_init())
                 goto out;
 
         if (netdev_kobject_init())
                 goto out;
 
         INIT_LIST_HEAD(&ptype_all);
         for (i = 0; i < PTYPE_HASH_SIZE; i++)
                 INIT_LIST_HEAD(&ptype_base[i]);
 
         INIT_LIST_HEAD(&offload_base);
 
         if (register_pernet_subsys(&netdev_net_ops))
                 goto out;
 
         /*
          *      Initialise the packet receive queues.
          */
 
         for_each_possible_cpu(i) {
                 struct softnet_data *sd = &per_cpu(softnet_data, i);
 
                 skb_queue_head_init(&sd->input_pkt_queue);
                 skb_queue_head_init(&sd->process_queue);
                 INIT_LIST_HEAD(&sd->poll_list);
                 sd->output_queue_tailp = &sd->output_queue;
 #ifdef CONFIG_RPS
                 sd->csd.func = rps_trigger_softirq;
                 sd->csd.info = sd;
                 sd->cpu = i;
 #endif
 
                 sd->backlog.poll = process_backlog;
                 sd->backlog.weight = weight_p;
         }
 
         dev_boot_phase = 0;
 
         /* The loopback device is special if any other network devices
          * is present in a network namespace the loopback device must
          * be present. Since we now dynamically allocate and free the
          * loopback device ensure this invariant is maintained by
          * keeping the loopback device as the first device on the
          * list of network devices.  Ensuring the loopback devices
          * is the first device that appears and the last network device
          * that disappears.
          */
         if (register_pernet_device(&loopback_net_ops))
                 goto out;
 
         if (register_pernet_device(&default_device_ops))
                 goto out;
 
         open_softirq(NET_TX_SOFTIRQ, net_tx_action);
         open_softirq(NET_RX_SOFTIRQ, net_rx_action);
 
         hotcpu_notifier(dev_cpu_callback, 0);
         dst_init();
         rc = 0;
 out:
         return rc;
 }
 
 subsys_initcall(net_dev_init);
 
```

```
/*
 *              Linux/include/linux/etherdevice.h
 *
 * INET         An implementation of the TCP/IP protocol suite for the LINUX
 *              operating system.  NET  is implemented using the  BSD Socket
 *              interface as the means of communication with the user level.
 *
 *              Definitions for the Ethernet handlers.
 *
 * Version:     @(#)eth.h       1.0.4   05/13/93
 *
 * Authors:     Ross Biro
 *              Fred N. van Kempen, <waltje@uWalt.NL.Mugnet.ORG>
 *
 *              Relocated to include/linux where it belongs by Alan Cox 
 *                                                      <gw4pts@gw4pts.ampr.org>
 *
 *              This program is free software; you can redistribute it and/or
 *              modify it under the terms of the GNU General Public License
 *              as published by the Free Software Foundation; either version
 *              2 of the License, or (at your option) any later version.
 *
 */
#ifndef _LINUX_ETHERDEVICE_H
#define _LINUX_ETHERDEVICE_H

#include <linux/if_ether.h>
#include <linux/netdevice.h>
#include <linux/random.h>
#include <asm/unaligned.h>
#include <asm/bitsperlong.h>

#ifdef __KERNEL__
u32 eth_get_headlen(void *data, unsigned int max_len);
__be16 eth_type_trans(struct sk_buff *skb, struct net_device *dev);
extern const struct header_ops eth_header_ops;

int eth_header(struct sk_buff *skb, struct net_device *dev, unsigned short type,
               const void *daddr, const void *saddr, unsigned len);
int eth_header_parse(const struct sk_buff *skb, unsigned char *haddr);
int eth_header_cache(const struct neighbour *neigh, struct hh_cache *hh,
                     __be16 type);
void eth_header_cache_update(struct hh_cache *hh, const struct net_device *dev,
                             const unsigned char *haddr);
int eth_prepare_mac_addr_change(struct net_device *dev, void *p);
void eth_commit_mac_addr_change(struct net_device *dev, void *p);
int eth_mac_addr(struct net_device *dev, void *p);
int eth_change_mtu(struct net_device *dev, int new_mtu);
int eth_validate_addr(struct net_device *dev);

struct net_device *alloc_etherdev_mqs(int sizeof_priv, unsigned int txqs,
                                            unsigned int rxqs);
#define alloc_etherdev(sizeof_priv) alloc_etherdev_mq(sizeof_priv, 1)
#define alloc_etherdev_mq(sizeof_priv, count) alloc_etherdev_mqs(sizeof_priv, count, count)

struct sk_buff **eth_gro_receive(struct sk_buff **head,
                                 struct sk_buff *skb);
int eth_gro_complete(struct sk_buff *skb, int nhoff);

/* Reserved Ethernet Addresses per IEEE 802.1Q */
static const u8 eth_reserved_addr_base[ETH_ALEN] __aligned(2) =
{ 0x01, 0x80, 0xc2, 0x00, 0x00, 0x00 };

/**
 * is_link_local_ether_addr - Determine if given Ethernet address is link-local
 * @addr: Pointer to a six-byte array containing the Ethernet address
 *
 * Return true if address is link local reserved addr (01:80:c2:00:00:0X) per
 * IEEE 802.1Q 8.6.3 Frame filtering.
 *
 * Please note: addr must be aligned to u16.
 */
static inline bool is_link_local_ether_addr(const u8 *addr)
{
        __be16 *a = (__be16 *)addr;
        static const __be16 *b = (const __be16 *)eth_reserved_addr_base;
        static const __be16 m = cpu_to_be16(0xfff0);

#if defined(CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS)
        return (((*(const u32 *)addr) ^ (*(const u32 *)b)) |
                ((a[2] ^ b[2]) & m)) == 0;
#else
        return ((a[0] ^ b[0]) | (a[1] ^ b[1]) | ((a[2] ^ b[2]) & m)) == 0;
#endif
}

/**
 * is_zero_ether_addr - Determine if give Ethernet address is all zeros.
 * @addr: Pointer to a six-byte array containing the Ethernet address
 *
 * Return true if the address is all zeroes.
 *
 * Please note: addr must be aligned to u16.
 */
static inline bool is_zero_ether_addr(const u8 *addr)
{
#if defined(CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS)
        return ((*(const u32 *)addr) | (*(const u16 *)(addr + 4))) == 0;
#else
        return (*(const u16 *)(addr + 0) |
                *(const u16 *)(addr + 2) |
                *(const u16 *)(addr + 4)) == 0;
#endif
}

/**
 * is_multicast_ether_addr - Determine if the Ethernet address is a multicast.
 * @addr: Pointer to a six-byte array containing the Ethernet address
 *
 * Return true if the address is a multicast address.
 * By definition the broadcast address is also a multicast address.
 */
static inline bool is_multicast_ether_addr(const u8 *addr)
{
        return 0x01 & addr[0];
}

/**
 * is_local_ether_addr - Determine if the Ethernet address is locally-assigned one (IEEE 802).
 * @addr: Pointer to a six-byte array containing the Ethernet address
 *
 * Return true if the address is a local address.
 */
static inline bool is_local_ether_addr(const u8 *addr)
{
        return 0x02 & addr[0];
}

/**
 * is_broadcast_ether_addr - Determine if the Ethernet address is broadcast
 * @addr: Pointer to a six-byte array containing the Ethernet address
 *
 * Return true if the address is the broadcast address.
 *
 * Please note: addr must be aligned to u16.
 */
static inline bool is_broadcast_ether_addr(const u8 *addr)
{
        return (*(const u16 *)(addr + 0) &
                *(const u16 *)(addr + 2) &
                *(const u16 *)(addr + 4)) == 0xffff;
}

/**
 * is_unicast_ether_addr - Determine if the Ethernet address is unicast
 * @addr: Pointer to a six-byte array containing the Ethernet address
 *
 * Return true if the address is a unicast address.
 */
static inline bool is_unicast_ether_addr(const u8 *addr)
{
        return !is_multicast_ether_addr(addr);
}

/**
 * is_valid_ether_addr - Determine if the given Ethernet address is valid
 * @addr: Pointer to a six-byte array containing the Ethernet address
 *
 * Check that the Ethernet address (MAC) is not 00:00:00:00:00:00, is not
 * a multicast address, and is not FF:FF:FF:FF:FF:FF.
 *
 * Return true if the address is valid.
 *
 * Please note: addr must be aligned to u16.
 */
static inline bool is_valid_ether_addr(const u8 *addr)
{
        /* FF:FF:FF:FF:FF:FF is a multicast address so we don't need to
         * explicitly check for it here. */
        return !is_multicast_ether_addr(addr) && !is_zero_ether_addr(addr);
}

/**
 * eth_random_addr - Generate software assigned random Ethernet address
 * @addr: Pointer to a six-byte array containing the Ethernet address
 *
 * Generate a random Ethernet address (MAC) that is not multicast
 * and has the local assigned bit set.
 */
static inline void eth_random_addr(u8 *addr)
{
        get_random_bytes(addr, ETH_ALEN);
        addr[0] &= 0xfe;        /* clear multicast bit */
        addr[0] |= 0x02;        /* set local assignment bit (IEEE802) */
}

#define random_ether_addr(addr) eth_random_addr(addr)

/**
 * eth_broadcast_addr - Assign broadcast address
 * @addr: Pointer to a six-byte array containing the Ethernet address
 *
 * Assign the broadcast address to the given address array.
 */
static inline void eth_broadcast_addr(u8 *addr)
{
        memset(addr, 0xff, ETH_ALEN);
}

/**
 * eth_zero_addr - Assign zero address
 * @addr: Pointer to a six-byte array containing the Ethernet address
 *
 * Assign the zero address to the given address array.
 */
static inline void eth_zero_addr(u8 *addr)
{
        memset(addr, 0x00, ETH_ALEN);
}

/**
 * eth_hw_addr_random - Generate software assigned random Ethernet and
 * set device flag
 * @dev: pointer to net_device structure
 *
 * Generate a random Ethernet address (MAC) to be used by a net device
 * and set addr_assign_type so the state can be read by sysfs and be
 * used by userspace.
 */
static inline void eth_hw_addr_random(struct net_device *dev)
{
        dev->addr_assign_type = NET_ADDR_RANDOM;
        eth_random_addr(dev->dev_addr);
}

/**
 * ether_addr_copy - Copy an Ethernet address
 * @dst: Pointer to a six-byte array Ethernet address destination
 * @src: Pointer to a six-byte array Ethernet address source
 *
 * Please note: dst & src must both be aligned to u16.
 */
static inline void ether_addr_copy(u8 *dst, const u8 *src)
{
#if defined(CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS)
        *(u32 *)dst = *(const u32 *)src;
        *(u16 *)(dst + 4) = *(const u16 *)(src + 4);
#else
        u16 *a = (u16 *)dst;
        const u16 *b = (const u16 *)src;

        a[0] = b[0];
        a[1] = b[1];
        a[2] = b[2];
#endif
}

/**
 * eth_hw_addr_inherit - Copy dev_addr from another net_device
 * @dst: pointer to net_device to copy dev_addr to
 * @src: pointer to net_device to copy dev_addr from
 *
 * Copy the Ethernet address from one net_device to another along with
 * the address attributes (addr_assign_type).
 */
static inline void eth_hw_addr_inherit(struct net_device *dst,
                                       struct net_device *src)
{
        dst->addr_assign_type = src->addr_assign_type;
        ether_addr_copy(dst->dev_addr, src->dev_addr);
}

/**
 * ether_addr_equal - Compare two Ethernet addresses
 * @addr1: Pointer to a six-byte array containing the Ethernet address
 * @addr2: Pointer other six-byte array containing the Ethernet address
 *
 * Compare two Ethernet addresses, returns true if equal
 *
 * Please note: addr1 & addr2 must both be aligned to u16.
 */
static inline bool ether_addr_equal(const u8 *addr1, const u8 *addr2)
{
#if defined(CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS)
        u32 fold = ((*(const u32 *)addr1) ^ (*(const u32 *)addr2)) |
                   ((*(const u16 *)(addr1 + 4)) ^ (*(const u16 *)(addr2 + 4)));

        return fold == 0;
#else
        const u16 *a = (const u16 *)addr1;
        const u16 *b = (const u16 *)addr2;

        return ((a[0] ^ b[0]) | (a[1] ^ b[1]) | (a[2] ^ b[2])) == 0;
#endif
}

/**
 * ether_addr_equal_64bits - Compare two Ethernet addresses
 * @addr1: Pointer to an array of 8 bytes
 * @addr2: Pointer to an other array of 8 bytes
 *
 * Compare two Ethernet addresses, returns true if equal, false otherwise.
 *
 * The function doesn't need any conditional branches and possibly uses
 * word memory accesses on CPU allowing cheap unaligned memory reads.
 * arrays = { byte1, byte2, byte3, byte4, byte5, byte6, pad1, pad2 }
 *
 * Please note that alignment of addr1 & addr2 are only guaranteed to be 16 bits.
 */

static inline bool ether_addr_equal_64bits(const u8 addr1[6+2],
                                           const u8 addr2[6+2])
{
#if defined(CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS) && BITS_PER_LONG == 64
        u64 fold = (*(const u64 *)addr1) ^ (*(const u64 *)addr2);

#ifdef __BIG_ENDIAN
        return (fold >> 16) == 0;
#else
        return (fold << 16) == 0;
#endif
#else
        return ether_addr_equal(addr1, addr2);
#endif
}

/**
 * ether_addr_equal_unaligned - Compare two not u16 aligned Ethernet addresses
 * @addr1: Pointer to a six-byte array containing the Ethernet address
 * @addr2: Pointer other six-byte array containing the Ethernet address
 *
 * Compare two Ethernet addresses, returns true if equal
 *
 * Please note: Use only when any Ethernet address may not be u16 aligned.
 */
static inline bool ether_addr_equal_unaligned(const u8 *addr1, const u8 *addr2)
{
#if defined(CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS)
        return ether_addr_equal(addr1, addr2);
#else
        return memcmp(addr1, addr2, ETH_ALEN) == 0;
#endif
}

/**
 * is_etherdev_addr - Tell if given Ethernet address belongs to the device.
 * @dev: Pointer to a device structure
 * @addr: Pointer to a six-byte array containing the Ethernet address
 *
 * Compare passed address with all addresses of the device. Return true if the
 * address if one of the device addresses.
 *
 * Note that this function calls ether_addr_equal_64bits() so take care of
 * the right padding.
 */
static inline bool is_etherdev_addr(const struct net_device *dev,
                                    const u8 addr[6 + 2])
{
        struct netdev_hw_addr *ha;
        bool res = false;

        rcu_read_lock();
        for_each_dev_addr(dev, ha) {
                res = ether_addr_equal_64bits(addr, ha->addr);
                if (res)
                        break;
        }
        rcu_read_unlock();
        return res;
}
#endif  /* __KERNEL__ */

/**
 * compare_ether_header - Compare two Ethernet headers
 * @a: Pointer to Ethernet header
 * @b: Pointer to Ethernet header
 *
 * Compare two Ethernet headers, returns 0 if equal.
 * This assumes that the network header (i.e., IP header) is 4-byte
 * aligned OR the platform can handle unaligned access.  This is the
 * case for all packets coming into netif_receive_skb or similar
 * entry points.
 */

static inline unsigned long compare_ether_header(const void *a, const void *b)
{
#if defined(CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS) && BITS_PER_LONG == 64
        unsigned long fold;

        /*
         * We want to compare 14 bytes:
         *  [a0 ... a13] ^ [b0 ... b13]
         * Use two long XOR, ORed together, with an overlap of two bytes.
         *  [a0  a1  a2  a3  a4  a5  a6  a7 ] ^ [b0  b1  b2  b3  b4  b5  b6  b7 ] |
         *  [a6  a7  a8  a9  a10 a11 a12 a13] ^ [b6  b7  b8  b9  b10 b11 b12 b13]
         * This means the [a6 a7] ^ [b6 b7] part is done two times.
        */
        fold = *(unsigned long *)a ^ *(unsigned long *)b;
        fold |= *(unsigned long *)(a + 6) ^ *(unsigned long *)(b + 6);
        return fold;
#else
        u32 *a32 = (u32 *)((u8 *)a + 2);
        u32 *b32 = (u32 *)((u8 *)b + 2);

        return (*(u16 *)a ^ *(u16 *)b) | (a32[0] ^ b32[0]) |
               (a32[1] ^ b32[1]) | (a32[2] ^ b32[2]);
#endif
}

/**
 * eth_skb_pad - Pad buffer to mininum number of octets for Ethernet frame
 * @skb: Buffer to pad
 *
 * An Ethernet frame should have a minimum size of 60 bytes.  This function
 * takes short frames and pads them with zeros up to the 60 byte limit.
 */
static inline int eth_skb_pad(struct sk_buff *skb)
{
        return skb_put_padto(skb, ETH_ZLEN);
}

#endif  /* _LINUX_ETHERDEVICE_H */

```


```
/*
 *              Linux/net/ethernet/eth.c
 *
 * INET         An implementation of the TCP/IP protocol suite for the LINUX
 *              operating system.  INET is implemented using the  BSD Socket
 *              interface as the means of communication with the user level.
 *
 *              Ethernet-type device handling.
 *
 * Version:     @(#)eth.c       1.0.7   05/25/93
 *
 * Authors:     Ross Biro
 *              Fred N. van Kempen, <waltje@uWalt.NL.Mugnet.ORG>
 *              Mark Evans, <evansmp@uhura.aston.ac.uk>
 *              Florian  La Roche, <rzsfl@rz.uni-sb.de>
 *              Alan Cox, <gw4pts@gw4pts.ampr.org>
 *
 * Fixes:
 *              Mr Linux        : Arp problems
 *              Alan Cox        : Generic queue tidyup (very tiny here)
 *              Alan Cox        : eth_header ntohs should be htons
 *              Alan Cox        : eth_rebuild_header missing an htons and
 *                                minor other things.
 *              Tegge           : Arp bug fixes.
 *              Florian         : Removed many unnecessary functions, code cleanup
 *                                and changes for new arp and skbuff.
 *              Alan Cox        : Redid header building to reflect new format.
 *              Alan Cox        : ARP only when compiled with CONFIG_INET
 *              Greg Page       : 802.2 and SNAP stuff.
 *              Alan Cox        : MAC layer pointers/new format.
 *              Paul Gortmaker  : eth_copy_and_sum shouldn't csum padding.
 *              Alan Cox        : Protect against forwarding explosions with
 *                                older network drivers and IFF_ALLMULTI.
 *      Christer Weinigel       : Better rebuild header message.
 *             Andrew Morton    : 26Feb01: kill ether_setup() - use netdev_boot_setup().
 *
 *              This program is free software; you can redistribute it and/or
 *              modify it under the terms of the GNU General Public License
 *              as published by the Free Software Foundation; either version
 *              2 of the License, or (at your option) any later version.
 */
#include <linux/module.h>
#include <linux/types.h>
#include <linux/kernel.h>
#include <linux/string.h>
#include <linux/mm.h>
#include <linux/socket.h>
#include <linux/in.h>
#include <linux/inet.h>
#include <linux/ip.h>
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/skbuff.h>
#include <linux/errno.h>
#include <linux/init.h>
#include <linux/if_ether.h>
#include <net/dst.h>
#include <net/arp.h>
#include <net/sock.h>
#include <net/ipv6.h>
#include <net/ip.h>
#include <net/dsa.h>
#include <linux/uaccess.h>

__setup("ether=", netdev_boot_setup);

/**
 * eth_header - create the Ethernet header
 * @skb:        buffer to alter
 * @dev:        source device
 * @type:       Ethernet type field
 * @daddr: destination address (NULL leave destination address)
 * @saddr: source address (NULL use device source address)
 * @len:   packet length (<= skb->len)
 *
 *
 * Set the protocol type. For a packet of type ETH_P_802_3/2 we put the length
 * in here instead.
 */
int eth_header(struct sk_buff *skb, struct net_device *dev,
               unsigned short type,
               const void *daddr, const void *saddr, unsigned int len)
{
        struct ethhdr *eth = (struct ethhdr *)skb_push(skb, ETH_HLEN);

        if (type != ETH_P_802_3 && type != ETH_P_802_2)
                eth->h_proto = htons(type);
        else
                eth->h_proto = htons(len);

        /*
         *      Set the source hardware address.
         */

        if (!saddr)
                saddr = dev->dev_addr;
        memcpy(eth->h_source, saddr, ETH_ALEN);

        if (daddr) {
                memcpy(eth->h_dest, daddr, ETH_ALEN);
                return ETH_HLEN;
        }

        /*
         *      Anyway, the loopback-device should never use this function...
         */

        if (dev->flags & (IFF_LOOPBACK | IFF_NOARP)) {
                eth_zero_addr(eth->h_dest);
                return ETH_HLEN;
        }

        return -ETH_HLEN;
}
EXPORT_SYMBOL(eth_header);

/**
 * eth_get_headlen - determine the the length of header for an ethernet frame
 * @data: pointer to start of frame
 * @len: total length of frame
 *
 * Make a best effort attempt to pull the length for all of the headers for
 * a given frame in a linear buffer.
 */
u32 eth_get_headlen(void *data, unsigned int len)
{
        const struct ethhdr *eth = (const struct ethhdr *)data;
        struct flow_keys keys;

        /* this should never happen, but better safe than sorry */
        if (len < sizeof(*eth))
                return len;

        /* parse any remaining L2/L3 headers, check for L4 */
        if (!__skb_flow_dissect(NULL, &keys, data,
                                eth->h_proto, sizeof(*eth), len))
                return max_t(u32, keys.thoff, sizeof(*eth));

        /* parse for any L4 headers */
        return min_t(u32, __skb_get_poff(NULL, data, &keys, len), len);
}
EXPORT_SYMBOL(eth_get_headlen);

/**
 * eth_type_trans - determine the packet's protocol ID.
 * @skb: received socket data
 * @dev: receiving network device
 *
 * The rule here is that we
 * assume 802.3 if the type field is short enough to be a length.
 * This is normal practice and works for any 'now in use' protocol.
 */
__be16 eth_type_trans(struct sk_buff *skb, struct net_device *dev)
{
        unsigned short _service_access_point;
        const unsigned short *sap;
        const struct ethhdr *eth;

        skb->dev = dev;
        skb_reset_mac_header(skb);
        skb_pull_inline(skb, ETH_HLEN);
        eth = eth_hdr(skb);

        if (unlikely(is_multicast_ether_addr(eth->h_dest))) {
                if (ether_addr_equal_64bits(eth->h_dest, dev->broadcast))
                        skb->pkt_type = PACKET_BROADCAST;
                else
                        skb->pkt_type = PACKET_MULTICAST;
        }
        else if (unlikely(!ether_addr_equal_64bits(eth->h_dest,
                                                   dev->dev_addr)))
                skb->pkt_type = PACKET_OTHERHOST;

        /*
         * Some variants of DSA tagging don't have an ethertype field
         * at all, so we check here whether one of those tagging
         * variants has been configured on the receiving interface,
         * and if so, set skb->protocol without looking at the packet.
         */
        if (unlikely(netdev_uses_dsa(dev)))
                return htons(ETH_P_XDSA);

        if (likely(ntohs(eth->h_proto) >= ETH_P_802_3_MIN))
                return eth->h_proto;

        /*
         *      This is a magic hack to spot IPX packets. Older Novell breaks
         *      the protocol design and runs IPX over 802.3 without an 802.2 LLC
         *      layer. We look for FFFF which isn't a used 802.2 SSAP/DSAP. This
         *      won't work for fault tolerant netware but does for the rest.
         */
        sap = skb_header_pointer(skb, 0, sizeof(*sap), &_service_access_point);
        if (sap && *sap == 0xFFFF)
                return htons(ETH_P_802_3);

        /*
         *      Real 802.2 LLC
         */
        return htons(ETH_P_802_2);
}
EXPORT_SYMBOL(eth_type_trans);

/**
 * eth_header_parse - extract hardware address from packet
 * @skb: packet to extract header from
 * @haddr: destination buffer
 */
int eth_header_parse(const struct sk_buff *skb, unsigned char *haddr)
{
        const struct ethhdr *eth = eth_hdr(skb);
        memcpy(haddr, eth->h_source, ETH_ALEN);
        return ETH_ALEN;
}
EXPORT_SYMBOL(eth_header_parse);

/**
 * eth_header_cache - fill cache entry from neighbour
 * @neigh: source neighbour
 * @hh: destination cache entry
 * @type: Ethernet type field
 *
 * Create an Ethernet header template from the neighbour.
 */
int eth_header_cache(const struct neighbour *neigh, struct hh_cache *hh, __be16 type)
{
        struct ethhdr *eth;
        const struct net_device *dev = neigh->dev;

        eth = (struct ethhdr *)
            (((u8 *) hh->hh_data) + (HH_DATA_OFF(sizeof(*eth))));

        if (type == htons(ETH_P_802_3))
                return -1;

        eth->h_proto = type;
        memcpy(eth->h_source, dev->dev_addr, ETH_ALEN);
        memcpy(eth->h_dest, neigh->ha, ETH_ALEN);
        hh->hh_len = ETH_HLEN;
        return 0;
}
EXPORT_SYMBOL(eth_header_cache);

/**
 * eth_header_cache_update - update cache entry
 * @hh: destination cache entry
 * @dev: network device
 * @haddr: new hardware address
 *
 * Called by Address Resolution module to notify changes in address.
 */
void eth_header_cache_update(struct hh_cache *hh,
                             const struct net_device *dev,
                             const unsigned char *haddr)
{
        memcpy(((u8 *) hh->hh_data) + HH_DATA_OFF(sizeof(struct ethhdr)),
               haddr, ETH_ALEN);
}
EXPORT_SYMBOL(eth_header_cache_update);

/**
 * eth_prepare_mac_addr_change - prepare for mac change
 * @dev: network device
 * @p: socket address
 */
int eth_prepare_mac_addr_change(struct net_device *dev, void *p)
{
        struct sockaddr *addr = p;

        if (!(dev->priv_flags & IFF_LIVE_ADDR_CHANGE) && netif_running(dev))
                return -EBUSY;
        if (!is_valid_ether_addr(addr->sa_data))
                return -EADDRNOTAVAIL;
        return 0;
}
EXPORT_SYMBOL(eth_prepare_mac_addr_change);

/**
 * eth_commit_mac_addr_change - commit mac change
 * @dev: network device
 * @p: socket address
 */
void eth_commit_mac_addr_change(struct net_device *dev, void *p)
{
        struct sockaddr *addr = p;

        memcpy(dev->dev_addr, addr->sa_data, ETH_ALEN);
}
EXPORT_SYMBOL(eth_commit_mac_addr_change);

/**
 * eth_mac_addr - set new Ethernet hardware address
 * @dev: network device
 * @p: socket address
 *
 * Change hardware address of device.
 *
 * This doesn't change hardware matching, so needs to be overridden
 * for most real devices.
 */
int eth_mac_addr(struct net_device *dev, void *p)
{
        int ret;

        ret = eth_prepare_mac_addr_change(dev, p);
        if (ret < 0)
                return ret;
        eth_commit_mac_addr_change(dev, p);
        return 0;
}
EXPORT_SYMBOL(eth_mac_addr);

/**
 * eth_change_mtu - set new MTU size
 * @dev: network device
 * @new_mtu: new Maximum Transfer Unit
 *
 * Allow changing MTU size. Needs to be overridden for devices
 * supporting jumbo frames.
 */
int eth_change_mtu(struct net_device *dev, int new_mtu)
{
        if (new_mtu < 68 || new_mtu > ETH_DATA_LEN)
                return -EINVAL;
        dev->mtu = new_mtu;
        return 0;
}
EXPORT_SYMBOL(eth_change_mtu);

int eth_validate_addr(struct net_device *dev)
{
        if (!is_valid_ether_addr(dev->dev_addr))
                return -EADDRNOTAVAIL;

        return 0;
}
EXPORT_SYMBOL(eth_validate_addr);

const struct header_ops eth_header_ops ____cacheline_aligned = {
        .create         = eth_header,
        .parse          = eth_header_parse,
        .cache          = eth_header_cache,
        .cache_update   = eth_header_cache_update,
};

/**
 * ether_setup - setup Ethernet network device
 * @dev: network device
 *
 * Fill in the fields of the device structure with Ethernet-generic values.
 */
void ether_setup(struct net_device *dev)
{
        dev->header_ops         = &eth_header_ops;
        dev->type               = ARPHRD_ETHER;
        dev->hard_header_len    = ETH_HLEN;
        dev->mtu                = ETH_DATA_LEN;
        dev->addr_len           = ETH_ALEN;
        dev->tx_queue_len       = 1000; /* Ethernet wants good queues */
        dev->flags              = IFF_BROADCAST|IFF_MULTICAST;
        dev->priv_flags         |= IFF_TX_SKB_SHARING;

        eth_broadcast_addr(dev->broadcast);

}
EXPORT_SYMBOL(ether_setup);

/**
 * alloc_etherdev_mqs - Allocates and sets up an Ethernet device
 * @sizeof_priv: Size of additional driver-private structure to be allocated
 *      for this Ethernet device
 * @txqs: The number of TX queues this device has.
 * @rxqs: The number of RX queues this device has.
 *
 * Fill in the fields of the device structure with Ethernet-generic
 * values. Basically does everything except registering the device.
 *
 * Constructs a new net device, complete with a private data area of
 * size (sizeof_priv).  A 32-byte (not bit) alignment is enforced for
 * this private data area.
 */

struct net_device *alloc_etherdev_mqs(int sizeof_priv, unsigned int txqs,
                                      unsigned int rxqs)
{
        return alloc_netdev_mqs(sizeof_priv, "eth%d", NET_NAME_UNKNOWN,
                                ether_setup, txqs, rxqs);
}
EXPORT_SYMBOL(alloc_etherdev_mqs);

ssize_t sysfs_format_mac(char *buf, const unsigned char *addr, int len)
{
        return scnprintf(buf, PAGE_SIZE, "%*phC\n", len, addr);
}
EXPORT_SYMBOL(sysfs_format_mac);

struct sk_buff **eth_gro_receive(struct sk_buff **head,
                                 struct sk_buff *skb)
{
        struct sk_buff *p, **pp = NULL;
        struct ethhdr *eh, *eh2;
        unsigned int hlen, off_eth;
        const struct packet_offload *ptype;
        __be16 type;
        int flush = 1;

        off_eth = skb_gro_offset(skb);
        hlen = off_eth + sizeof(*eh);
        eh = skb_gro_header_fast(skb, off_eth);
        if (skb_gro_header_hard(skb, hlen)) {
                eh = skb_gro_header_slow(skb, hlen, off_eth);
                if (unlikely(!eh))
                        goto out;
        }

        flush = 0;

        for (p = *head; p; p = p->next) {
                if (!NAPI_GRO_CB(p)->same_flow)
                        continue;

                eh2 = (struct ethhdr *)(p->data + off_eth);
                if (compare_ether_header(eh, eh2)) {
                        NAPI_GRO_CB(p)->same_flow = 0;
                        continue;
                }
        }

        type = eh->h_proto;

        rcu_read_lock();
        ptype = gro_find_receive_by_type(type);
        if (ptype == NULL) {
                flush = 1;
                goto out_unlock;
        }

        skb_gro_pull(skb, sizeof(*eh));
        skb_gro_postpull_rcsum(skb, eh, sizeof(*eh));
        pp = ptype->callbacks.gro_receive(head, skb);

out_unlock:
        rcu_read_unlock();
out:
        NAPI_GRO_CB(skb)->flush |= flush;

        return pp;
}
EXPORT_SYMBOL(eth_gro_receive);

int eth_gro_complete(struct sk_buff *skb, int nhoff)
{
        struct ethhdr *eh = (struct ethhdr *)(skb->data + nhoff);
        __be16 type = eh->h_proto;
        struct packet_offload *ptype;
        int err = -ENOSYS;

        if (skb->encapsulation)
                skb_set_inner_mac_header(skb, nhoff);

        rcu_read_lock();
        ptype = gro_find_complete_by_type(type);
        if (ptype != NULL)
                err = ptype->callbacks.gro_complete(skb, nhoff +
                                                    sizeof(struct ethhdr));

        rcu_read_unlock();
        return err;
}
EXPORT_SYMBOL(eth_gro_complete);

static struct packet_offload eth_packet_offload __read_mostly = {
        .type = cpu_to_be16(ETH_P_TEB),
        .callbacks = {
                .gro_receive = eth_gro_receive,
                .gro_complete = eth_gro_complete,
        },
};

static int __init eth_offload_init(void)
{
        dev_add_offload(&eth_packet_offload);

        return 0;
}

fs_initcall(eth_offload_init);

```

```
/* 
 * drivers/base/core.c - core driver model code (device registration, etc)
 *
 * Copyright (c) 2002-3 Patrick Mochel
 * Copyright (c) 2002-3 Open Source Development Labs
 * Copyright (c) 2006 Greg Kroah-Hartman <gregkh@suse.de>
 * Copyright (c) 2006 Novell, Inc.
 *
 * This file is released under the GPLv2
 *
 */

#include <linux/device.h>
#include <linux/err.h>
#include <linux/fwnode.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/kdev_t.h>
#include <linux/notifier.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/genhd.h>
#include <linux/kallsyms.h>
#include <linux/mutex.h>
#include <linux/pm_runtime.h>
#include <linux/netdevice.h>
#include <linux/sysfs.h>

#include "base.h"
#include "power/power.h"

#ifdef CONFIG_SYSFS_DEPRECATED
#ifdef CONFIG_SYSFS_DEPRECATED_V2
long sysfs_deprecated = 1;
#else
long sysfs_deprecated = 0;
#endif
static int __init sysfs_deprecated_setup(char *arg)
{
        return kstrtol(arg, 10, &sysfs_deprecated);
}
early_param("sysfs.deprecated", sysfs_deprecated_setup);
#endif

int (*platform_notify)(struct device *dev) = NULL;
int (*platform_notify_remove)(struct device *dev) = NULL;
static struct kobject *dev_kobj;
struct kobject *sysfs_dev_char_kobj;
struct kobject *sysfs_dev_block_kobj;

static DEFINE_MUTEX(device_hotplug_lock);

void lock_device_hotplug(void)
{
        mutex_lock(&device_hotplug_lock);
}

void unlock_device_hotplug(void)
{
        mutex_unlock(&device_hotplug_lock);
}

int lock_device_hotplug_sysfs(void)
{
        if (mutex_trylock(&device_hotplug_lock))
                return 0;

        /* Avoid busy looping (5 ms of sleep should do). */
        msleep(5);
        return restart_syscall();
}

#ifdef CONFIG_BLOCK
static inline int device_is_not_partition(struct device *dev)
{
        return !(dev->type == &part_type);
}
#else
static inline int device_is_not_partition(struct device *dev)
{
        return 1;
}
#endif

/**
 * dev_driver_string - Return a device's driver name, if at all possible
 * @dev: struct device to get the name of
 *
 * Will return the device's driver's name if it is bound to a device.  If
 * the device is not bound to a driver, it will return the name of the bus
 * it is attached to.  If it is not attached to a bus either, an empty
 * string will be returned.
 */
const char *dev_driver_string(const struct device *dev)
{
        struct device_driver *drv;

        /* dev->driver can change to NULL underneath us because of unbinding,
         * so be careful about accessing it.  dev->bus and dev->class should
         * never change once they are set, so they don't need special care.
         */
        drv = ACCESS_ONCE(dev->driver);
        return drv ? drv->name :
                        (dev->bus ? dev->bus->name :
                        (dev->class ? dev->class->name : ""));
}
EXPORT_SYMBOL(dev_driver_string);

#define to_dev_attr(_attr) container_of(_attr, struct device_attribute, attr)

static ssize_t dev_attr_show(struct kobject *kobj, struct attribute *attr,
                             char *buf)
{
        struct device_attribute *dev_attr = to_dev_attr(attr);
        struct device *dev = kobj_to_dev(kobj);
        ssize_t ret = -EIO;

        if (dev_attr->show)
                ret = dev_attr->show(dev, dev_attr, buf);
        if (ret >= (ssize_t)PAGE_SIZE) {
                print_symbol("dev_attr_show: %s returned bad count\n",
                                (unsigned long)dev_attr->show);
        }
        return ret;
}

static ssize_t dev_attr_store(struct kobject *kobj, struct attribute *attr,
                              const char *buf, size_t count)
{
        struct device_attribute *dev_attr = to_dev_attr(attr);
        struct device *dev = kobj_to_dev(kobj);
        ssize_t ret = -EIO;

        if (dev_attr->store)
                ret = dev_attr->store(dev, dev_attr, buf, count);
        return ret;
}

static const struct sysfs_ops dev_sysfs_ops = {
        .show   = dev_attr_show,
        .store  = dev_attr_store,
};

#define to_ext_attr(x) container_of(x, struct dev_ext_attribute, attr)

ssize_t device_store_ulong(struct device *dev,
                           struct device_attribute *attr,
                           const char *buf, size_t size)
{
        struct dev_ext_attribute *ea = to_ext_attr(attr);
        char *end;
        unsigned long new = simple_strtoul(buf, &end, 0);
        if (end == buf)
                return -EINVAL;
        *(unsigned long *)(ea->var) = new;
        /* Always return full write size even if we didn't consume all */
        return size;
}
EXPORT_SYMBOL_GPL(device_store_ulong);

ssize_t device_show_ulong(struct device *dev,
                          struct device_attribute *attr,
                          char *buf)
{
        struct dev_ext_attribute *ea = to_ext_attr(attr);
        return snprintf(buf, PAGE_SIZE, "%lx\n", *(unsigned long *)(ea->var));
}
EXPORT_SYMBOL_GPL(device_show_ulong);

ssize_t device_store_int(struct device *dev,
                         struct device_attribute *attr,
                         const char *buf, size_t size)
{
        struct dev_ext_attribute *ea = to_ext_attr(attr);
        char *end;
        long new = simple_strtol(buf, &end, 0);
        if (end == buf || new > INT_MAX || new < INT_MIN)
                return -EINVAL;
        *(int *)(ea->var) = new;
        /* Always return full write size even if we didn't consume all */
        return size;
}
EXPORT_SYMBOL_GPL(device_store_int);

ssize_t device_show_int(struct device *dev,
                        struct device_attribute *attr,
                        char *buf)
{
        struct dev_ext_attribute *ea = to_ext_attr(attr);

        return snprintf(buf, PAGE_SIZE, "%d\n", *(int *)(ea->var));
}
EXPORT_SYMBOL_GPL(device_show_int);

ssize_t device_store_bool(struct device *dev, struct device_attribute *attr,
                          const char *buf, size_t size)
{
        struct dev_ext_attribute *ea = to_ext_attr(attr);

        if (strtobool(buf, ea->var) < 0)
                return -EINVAL;

        return size;
}
EXPORT_SYMBOL_GPL(device_store_bool);

ssize_t device_show_bool(struct device *dev, struct device_attribute *attr,
                         char *buf)
{
        struct dev_ext_attribute *ea = to_ext_attr(attr);

        return snprintf(buf, PAGE_SIZE, "%d\n", *(bool *)(ea->var));
}
EXPORT_SYMBOL_GPL(device_show_bool);

/**
 * device_release - free device structure.
 * @kobj: device's kobject.
 *
 * This is called once the reference count for the object
 * reaches 0. We forward the call to the device's release
 * method, which should handle actually freeing the structure.
 */
static void device_release(struct kobject *kobj)
{
        struct device *dev = kobj_to_dev(kobj);
        struct device_private *p = dev->p;

        /*
         * Some platform devices are driven without driver attached
         * and managed resources may have been acquired.  Make sure
         * all resources are released.
         *
         * Drivers still can add resources into device after device
         * is deleted but alive, so release devres here to avoid
         * possible memory leak.
         */
        devres_release_all(dev);

        if (dev->release)
                dev->release(dev);
        else if (dev->type && dev->type->release)
                dev->type->release(dev);
        else if (dev->class && dev->class->dev_release)
                dev->class->dev_release(dev);
        else
                WARN(1, KERN_ERR "Device '%s' does not have a release() "
                        "function, it is broken and must be fixed.\n",
                        dev_name(dev));
        kfree(p);
}

static const void *device_namespace(struct kobject *kobj)
{
        struct device *dev = kobj_to_dev(kobj);
        const void *ns = NULL;

        if (dev->class && dev->class->ns_type)
                ns = dev->class->namespace(dev);

        return ns;
}

static struct kobj_type device_ktype = {
        .release        = device_release,
        .sysfs_ops      = &dev_sysfs_ops,
        .namespace      = device_namespace,
};


static int dev_uevent_filter(struct kset *kset, struct kobject *kobj)
{
        struct kobj_type *ktype = get_ktype(kobj);

        if (ktype == &device_ktype) {
                struct device *dev = kobj_to_dev(kobj);
                if (dev->bus)
                        return 1;
                if (dev->class)
                        return 1;
        }
        return 0;
}

static const char *dev_uevent_name(struct kset *kset, struct kobject *kobj)
{
        struct device *dev = kobj_to_dev(kobj);

        if (dev->bus)
                return dev->bus->name;
        if (dev->class)
                return dev->class->name;
        return NULL;
}

static int dev_uevent(struct kset *kset, struct kobject *kobj,
                      struct kobj_uevent_env *env)
{
        struct device *dev = kobj_to_dev(kobj);
        int retval = 0;

        /* add device node properties if present */
        if (MAJOR(dev->devt)) {
                const char *tmp;
                const char *name;
                umode_t mode = 0;
                kuid_t uid = GLOBAL_ROOT_UID;
                kgid_t gid = GLOBAL_ROOT_GID;

                add_uevent_var(env, "MAJOR=%u", MAJOR(dev->devt));
                add_uevent_var(env, "MINOR=%u", MINOR(dev->devt));
                name = device_get_devnode(dev, &mode, &uid, &gid, &tmp);
                if (name) {
                        add_uevent_var(env, "DEVNAME=%s", name);
                        if (mode)
                                add_uevent_var(env, "DEVMODE=%#o", mode & 0777);
                        if (!uid_eq(uid, GLOBAL_ROOT_UID))
                                add_uevent_var(env, "DEVUID=%u", from_kuid(&init_user_ns, uid));
                        if (!gid_eq(gid, GLOBAL_ROOT_GID))
                                add_uevent_var(env, "DEVGID=%u", from_kgid(&init_user_ns, gid));
                        kfree(tmp);
                }
        }

        if (dev->type && dev->type->name)
                add_uevent_var(env, "DEVTYPE=%s", dev->type->name);

        if (dev->driver)
                add_uevent_var(env, "DRIVER=%s", dev->driver->name);

        /* Add common DT information about the device */
        of_device_uevent(dev, env);

        /* have the bus specific function add its stuff */
        if (dev->bus && dev->bus->uevent) {
                retval = dev->bus->uevent(dev, env);
                if (retval)
                        pr_debug("device: '%s': %s: bus uevent() returned %d\n",
                                 dev_name(dev), __func__, retval);
        }

        /* have the class specific function add its stuff */
        if (dev->class && dev->class->dev_uevent) {
                retval = dev->class->dev_uevent(dev, env);
                if (retval)
                        pr_debug("device: '%s': %s: class uevent() "
                                 "returned %d\n", dev_name(dev),
                                 __func__, retval);
        }

        /* have the device type specific function add its stuff */
        if (dev->type && dev->type->uevent) {
                retval = dev->type->uevent(dev, env);
                if (retval)
                        pr_debug("device: '%s': %s: dev_type uevent() "
                                 "returned %d\n", dev_name(dev),
                                 __func__, retval);
        }

        return retval;
}

static const struct kset_uevent_ops device_uevent_ops = {
        .filter =       dev_uevent_filter,
        .name =         dev_uevent_name,
        .uevent =       dev_uevent,
};

static ssize_t uevent_show(struct device *dev, struct device_attribute *attr,
                           char *buf)
{
        struct kobject *top_kobj;
        struct kset *kset;
        struct kobj_uevent_env *env = NULL;
        int i;
        size_t count = 0;
        int retval;

        /* search the kset, the device belongs to */
        top_kobj = &dev->kobj;
        while (!top_kobj->kset && top_kobj->parent)
                top_kobj = top_kobj->parent;
        if (!top_kobj->kset)
                goto out;

        kset = top_kobj->kset;
        if (!kset->uevent_ops || !kset->uevent_ops->uevent)
                goto out;

        /* respect filter */
        if (kset->uevent_ops && kset->uevent_ops->filter)
                if (!kset->uevent_ops->filter(kset, &dev->kobj))
                        goto out;

        env = kzalloc(sizeof(struct kobj_uevent_env), GFP_KERNEL);
        if (!env)
                return -ENOMEM;

        /* let the kset specific function add its keys */
        retval = kset->uevent_ops->uevent(kset, &dev->kobj, env);
        if (retval)
                goto out;

        /* copy keys to file */
        for (i = 0; i < env->envp_idx; i++)
                count += sprintf(&buf[count], "%s\n", env->envp[i]);
out:
        kfree(env);
        return count;
}

static ssize_t uevent_store(struct device *dev, struct device_attribute *attr,
                            const char *buf, size_t count)
{
        enum kobject_action action;

        if (kobject_action_type(buf, count, &action) == 0)
                kobject_uevent(&dev->kobj, action);
        else
                dev_err(dev, "uevent: unknown action-string\n");
        return count;
}
static DEVICE_ATTR_RW(uevent);

static ssize_t online_show(struct device *dev, struct device_attribute *attr,
                           char *buf)
{
        bool val;

        device_lock(dev);
        val = !dev->offline;
        device_unlock(dev);
        return sprintf(buf, "%u\n", val);
}

static ssize_t online_store(struct device *dev, struct device_attribute *attr,
                            const char *buf, size_t count)
{
        bool val;
        int ret;

        ret = strtobool(buf, &val);
        if (ret < 0)
                return ret;

        ret = lock_device_hotplug_sysfs();
        if (ret)
                return ret;

        ret = val ? device_online(dev) : device_offline(dev);
        unlock_device_hotplug();
        return ret < 0 ? ret : count;
}
static DEVICE_ATTR_RW(online);

int device_add_groups(struct device *dev, const struct attribute_group **groups)
{
        return sysfs_create_groups(&dev->kobj, groups);
}

void device_remove_groups(struct device *dev,
                          const struct attribute_group **groups)
{
        sysfs_remove_groups(&dev->kobj, groups);
}

static int device_add_attrs(struct device *dev)
{
        struct class *class = dev->class;
        const struct device_type *type = dev->type;
        int error;

        if (class) {
                error = device_add_groups(dev, class->dev_groups);
                if (error)
                        return error;
        }

        if (type) {
                error = device_add_groups(dev, type->groups);
                if (error)
                        goto err_remove_class_groups;
        }

        error = device_add_groups(dev, dev->groups);
        if (error)
                goto err_remove_type_groups;

        if (device_supports_offline(dev) && !dev->offline_disabled) {
                error = device_create_file(dev, &dev_attr_online);
                if (error)
                        goto err_remove_dev_groups;
        }

        return 0;

 err_remove_dev_groups:
        device_remove_groups(dev, dev->groups);
 err_remove_type_groups:
        if (type)
                device_remove_groups(dev, type->groups);
 err_remove_class_groups:
        if (class)
                device_remove_groups(dev, class->dev_groups);

        return error;
}

static void device_remove_attrs(struct device *dev)
{
        struct class *class = dev->class;
        const struct device_type *type = dev->type;

        device_remove_file(dev, &dev_attr_online);
        device_remove_groups(dev, dev->groups);

        if (type)
                device_remove_groups(dev, type->groups);

        if (class)
                device_remove_groups(dev, class->dev_groups);
}

static ssize_t dev_show(struct device *dev, struct device_attribute *attr,
                        char *buf)
{
        return print_dev_t(buf, dev->devt);
}
static DEVICE_ATTR_RO(dev);

/* /sys/devices/ */
struct kset *devices_kset;

/**
 * device_create_file - create sysfs attribute file for device.
 * @dev: device.
 * @attr: device attribute descriptor.
 */
int device_create_file(struct device *dev,
                       const struct device_attribute *attr)
{
        int error = 0;

        if (dev) {
                WARN(((attr->attr.mode & S_IWUGO) && !attr->store),
                        "Attribute %s: write permission without 'store'\n",
                        attr->attr.name);
                WARN(((attr->attr.mode & S_IRUGO) && !attr->show),
                        "Attribute %s: read permission without 'show'\n",
                        attr->attr.name);
                error = sysfs_create_file(&dev->kobj, &attr->attr);
        }

        return error;
}
EXPORT_SYMBOL_GPL(device_create_file);

/**
 * device_remove_file - remove sysfs attribute file.
 * @dev: device.
 * @attr: device attribute descriptor.
 */
void device_remove_file(struct device *dev,
                        const struct device_attribute *attr)
{
        if (dev)
                sysfs_remove_file(&dev->kobj, &attr->attr);
}
EXPORT_SYMBOL_GPL(device_remove_file);

/**
 * device_remove_file_self - remove sysfs attribute file from its own method.
 * @dev: device.
 * @attr: device attribute descriptor.
 *
 * See kernfs_remove_self() for details.
 */
bool device_remove_file_self(struct device *dev,
                             const struct device_attribute *attr)
{
        if (dev)
                return sysfs_remove_file_self(&dev->kobj, &attr->attr);
        else
                return false;
}
EXPORT_SYMBOL_GPL(device_remove_file_self);

/**
 * device_create_bin_file - create sysfs binary attribute file for device.
 * @dev: device.
 * @attr: device binary attribute descriptor.
 */
int device_create_bin_file(struct device *dev,
                           const struct bin_attribute *attr)
{
        int error = -EINVAL;
        if (dev)
                error = sysfs_create_bin_file(&dev->kobj, attr);
        return error;
}
EXPORT_SYMBOL_GPL(device_create_bin_file);

/**
 * device_remove_bin_file - remove sysfs binary attribute file
 * @dev: device.
 * @attr: device binary attribute descriptor.
 */
void device_remove_bin_file(struct device *dev,
                            const struct bin_attribute *attr)
{
        if (dev)
                sysfs_remove_bin_file(&dev->kobj, attr);
}
EXPORT_SYMBOL_GPL(device_remove_bin_file);

static void klist_children_get(struct klist_node *n)
{
        struct device_private *p = to_device_private_parent(n);
        struct device *dev = p->device;

        get_device(dev);
}

static void klist_children_put(struct klist_node *n)
{
        struct device_private *p = to_device_private_parent(n);
        struct device *dev = p->device;

        put_device(dev);
}

/**
 * device_initialize - init device structure.
 * @dev: device.
 *
 * This prepares the device for use by other layers by initializing
 * its fields.
 * It is the first half of device_register(), if called by
 * that function, though it can also be called separately, so one
 * may use @dev's fields. In particular, get_device()/put_device()
 * may be used for reference counting of @dev after calling this
 * function.
 *
 * All fields in @dev must be initialized by the caller to 0, except
 * for those explicitly set to some other value.  The simplest
 * approach is to use kzalloc() to allocate the structure containing
 * @dev.
 *
 * NOTE: Use put_device() to give up your reference instead of freeing
 * @dev directly once you have called this function.
 */
void device_initialize(struct device *dev)
{
        dev->kobj.kset = devices_kset;
        kobject_init(&dev->kobj, &device_ktype);
        INIT_LIST_HEAD(&dev->dma_pools);
        mutex_init(&dev->mutex);
        lockdep_set_novalidate_class(&dev->mutex);
        spin_lock_init(&dev->devres_lock);
        INIT_LIST_HEAD(&dev->devres_head);
        device_pm_init(dev);
        set_dev_node(dev, -1);
}
EXPORT_SYMBOL_GPL(device_initialize);

struct kobject *virtual_device_parent(struct device *dev)
{
        static struct kobject *virtual_dir = NULL;

        if (!virtual_dir)
                virtual_dir = kobject_create_and_add("virtual",
                                                     &devices_kset->kobj);

        return virtual_dir;
}

struct class_dir {
        struct kobject kobj;
        struct class *class;
};

#define to_class_dir(obj) container_of(obj, struct class_dir, kobj)

static void class_dir_release(struct kobject *kobj)
{
        struct class_dir *dir = to_class_dir(kobj);
        kfree(dir);
}

static const
struct kobj_ns_type_operations *class_dir_child_ns_type(struct kobject *kobj)
{
        struct class_dir *dir = to_class_dir(kobj);
        return dir->class->ns_type;
}

static struct kobj_type class_dir_ktype = {
        .release        = class_dir_release,
        .sysfs_ops      = &kobj_sysfs_ops,
        .child_ns_type  = class_dir_child_ns_type
};

static struct kobject *
class_dir_create_and_add(struct class *class, struct kobject *parent_kobj)
{
        struct class_dir *dir;
        int retval;

        dir = kzalloc(sizeof(*dir), GFP_KERNEL);
        if (!dir)
                return NULL;

        dir->class = class;
        kobject_init(&dir->kobj, &class_dir_ktype);

        dir->kobj.kset = &class->p->glue_dirs;

        retval = kobject_add(&dir->kobj, parent_kobj, "%s", class->name);
        if (retval < 0) {
                kobject_put(&dir->kobj);
                return NULL;
        }
        return &dir->kobj;
}

static DEFINE_MUTEX(gdp_mutex);

static struct kobject *get_device_parent(struct device *dev,
                                         struct device *parent)
{
        if (dev->class) {
                struct kobject *kobj = NULL;
                struct kobject *parent_kobj;
                struct kobject *k;

#ifdef CONFIG_BLOCK
                /* block disks show up in /sys/block */
                if (sysfs_deprecated && dev->class == &block_class) {
                        if (parent && parent->class == &block_class)
                                return &parent->kobj;
                        return &block_class.p->subsys.kobj;
                }
#endif

                /*
                 * If we have no parent, we live in "virtual".
                 * Class-devices with a non class-device as parent, live
                 * in a "glue" directory to prevent namespace collisions.
                 */
                if (parent == NULL)
                        parent_kobj = virtual_device_parent(dev);
                else if (parent->class && !dev->class->ns_type)
                        return &parent->kobj;
                else
                        parent_kobj = &parent->kobj;

                mutex_lock(&gdp_mutex);

                /* find our class-directory at the parent and reference it */
                spin_lock(&dev->class->p->glue_dirs.list_lock);
                list_for_each_entry(k, &dev->class->p->glue_dirs.list, entry)
                        if (k->parent == parent_kobj) {
                                kobj = kobject_get(k);
                                break;
                        }
                spin_unlock(&dev->class->p->glue_dirs.list_lock);
                if (kobj) {
                        mutex_unlock(&gdp_mutex);
                        return kobj;
                }

                /* or create a new class-directory at the parent device */
                k = class_dir_create_and_add(dev->class, parent_kobj);
                /* do not emit an uevent for this simple "glue" directory */
                mutex_unlock(&gdp_mutex);
                return k;
        }

        /* subsystems can specify a default root directory for their devices */
        if (!parent && dev->bus && dev->bus->dev_root)
                return &dev->bus->dev_root->kobj;

        if (parent)
                return &parent->kobj;
        return NULL;
}

static void cleanup_glue_dir(struct device *dev, struct kobject *glue_dir)
{
        /* see if we live in a "glue" directory */
        if (!glue_dir || !dev->class ||
            glue_dir->kset != &dev->class->p->glue_dirs)
                return;

        mutex_lock(&gdp_mutex);
        kobject_put(glue_dir);
        mutex_unlock(&gdp_mutex);
}

static void cleanup_device_parent(struct device *dev)
{
        cleanup_glue_dir(dev, dev->kobj.parent);
}

static int device_add_class_symlinks(struct device *dev)
{
        struct device_node *of_node = dev_of_node(dev);
        int error;

        if (of_node) {
                error = sysfs_create_link(&dev->kobj, &of_node->kobj,"of_node");
                if (error)
                        dev_warn(dev, "Error %d creating of_node link\n",error);
                /* An error here doesn't warrant bringing down the device */
        }

        if (!dev->class)
                return 0;

        error = sysfs_create_link(&dev->kobj,
                                  &dev->class->p->subsys.kobj,
                                  "subsystem");
        if (error)
                goto out_devnode;

        if (dev->parent && device_is_not_partition(dev)) {
                error = sysfs_create_link(&dev->kobj, &dev->parent->kobj,
                                          "device");
                if (error)
                        goto out_subsys;
        }

#ifdef CONFIG_BLOCK
        /* /sys/block has directories and does not need symlinks */
        if (sysfs_deprecated && dev->class == &block_class)
                return 0;
#endif

        /* link in the class directory pointing to the device */
        error = sysfs_create_link(&dev->class->p->subsys.kobj,
                                  &dev->kobj, dev_name(dev));
        if (error)
                goto out_device;

        return 0;

out_device:
        sysfs_remove_link(&dev->kobj, "device");

out_subsys:
        sysfs_remove_link(&dev->kobj, "subsystem");
out_devnode:
        sysfs_remove_link(&dev->kobj, "of_node");
        return error;
}

static void device_remove_class_symlinks(struct device *dev)
{
        if (dev_of_node(dev))
                sysfs_remove_link(&dev->kobj, "of_node");

        if (!dev->class)
                return;

        if (dev->parent && device_is_not_partition(dev))
                sysfs_remove_link(&dev->kobj, "device");
        sysfs_remove_link(&dev->kobj, "subsystem");
#ifdef CONFIG_BLOCK
        if (sysfs_deprecated && dev->class == &block_class)
                return;
#endif
        sysfs_delete_link(&dev->class->p->subsys.kobj, &dev->kobj, dev_name(dev));
}

/**
 * dev_set_name - set a device name
 * @dev: device
 * @fmt: format string for the device's name
 */
int dev_set_name(struct device *dev, const char *fmt, ...)
{
        va_list vargs;
        int err;

        va_start(vargs, fmt);
        err = kobject_set_name_vargs(&dev->kobj, fmt, vargs);
        va_end(vargs);
        return err;
}
EXPORT_SYMBOL_GPL(dev_set_name);

/**
 * device_to_dev_kobj - select a /sys/dev/ directory for the device
 * @dev: device
 *
 * By default we select char/ for new entries.  Setting class->dev_obj
 * to NULL prevents an entry from being created.  class->dev_kobj must
 * be set (or cleared) before any devices are registered to the class
 * otherwise device_create_sys_dev_entry() and
 * device_remove_sys_dev_entry() will disagree about the presence of
 * the link.
 */
static struct kobject *device_to_dev_kobj(struct device *dev)
{
        struct kobject *kobj;

        if (dev->class)
                kobj = dev->class->dev_kobj;
        else
                kobj = sysfs_dev_char_kobj;

        return kobj;
}

static int device_create_sys_dev_entry(struct device *dev)
{
        struct kobject *kobj = device_to_dev_kobj(dev);
        int error = 0;
        char devt_str[15];

        if (kobj) {
                format_dev_t(devt_str, dev->devt);
                error = sysfs_create_link(kobj, &dev->kobj, devt_str);
        }

        return error;
}

static void device_remove_sys_dev_entry(struct device *dev)
{
        struct kobject *kobj = device_to_dev_kobj(dev);
        char devt_str[15];

        if (kobj) {
                format_dev_t(devt_str, dev->devt);
                sysfs_remove_link(kobj, devt_str);
        }
}

int device_private_init(struct device *dev)
{
        dev->p = kzalloc(sizeof(*dev->p), GFP_KERNEL);
        if (!dev->p)
                return -ENOMEM;
        dev->p->device = dev;
        klist_init(&dev->p->klist_children, klist_children_get,
                   klist_children_put);
        INIT_LIST_HEAD(&dev->p->deferred_probe);
        return 0;
}

/**
 * device_add - add device to device hierarchy.
 * @dev: device.
 *
 * This is part 2 of device_register(), though may be called
 * separately _iff_ device_initialize() has been called separately.
 *
 * This adds @dev to the kobject hierarchy via kobject_add(), adds it
 * to the global and sibling lists for the device, then
 * adds it to the other relevant subsystems of the driver model.
 *
 * Do not call this routine or device_register() more than once for
 * any device structure.  The driver model core is not designed to work
 * with devices that get unregistered and then spring back to life.
 * (Among other things, it's very hard to guarantee that all references
 * to the previous incarnation of @dev have been dropped.)  Allocate
 * and register a fresh new struct device instead.
 *
 * NOTE: _Never_ directly free @dev after calling this function, even
 * if it returned an error! Always use put_device() to give up your
 * reference instead.
 */
int device_add(struct device *dev)
{
        struct device *parent = NULL;
        struct kobject *kobj;
        struct class_interface *class_intf;
        int error = -EINVAL;

        dev = get_device(dev);
        if (!dev)
                goto done;

        if (!dev->p) {
                error = device_private_init(dev);
                if (error)
                        goto done;
        }

        /*
         * for statically allocated devices, which should all be converted
         * some day, we need to initialize the name. We prevent reading back
         * the name, and force the use of dev_name()
         */
        if (dev->init_name) {
                dev_set_name(dev, "%s", dev->init_name);
                 dev->init_name = NULL;
         }
 
         /* subsystems can specify simple device enumeration */
         if (!dev_name(dev) && dev->bus && dev->bus->dev_name)
                 dev_set_name(dev, "%s%u", dev->bus->dev_name, dev->id);
 
         if (!dev_name(dev)) {
                 error = -EINVAL;
                 goto name_error;
         }
 
         pr_debug("device: '%s': %s\n", dev_name(dev), __func__);
 
         parent = get_device(dev->parent);
         kobj = get_device_parent(dev, parent);
         if (kobj)
                 dev->kobj.parent = kobj;
 
         /* use parent numa_node */
         if (parent)
                 set_dev_node(dev, dev_to_node(parent));
 
         /* first, register with generic layer. */
         /* we require the name to be set before, and pass NULL */
         error = kobject_add(&dev->kobj, dev->kobj.parent, NULL);
         if (error)
                 goto Error;
 
         /* notify platform of device entry */
         if (platform_notify)
                 platform_notify(dev);
 
         error = device_create_file(dev, &dev_attr_uevent);
         if (error)
                 goto attrError;
 
         error = device_add_class_symlinks(dev);
         if (error)
                 goto SymlinkError;
         error = device_add_attrs(dev);
         if (error)
                 goto AttrsError;
         error = bus_add_device(dev);
         if (error)
                 goto BusError;
         error = dpm_sysfs_add(dev);
         if (error)
                 goto DPMError;
         device_pm_add(dev);
 
         if (MAJOR(dev->devt)) {
                 error = device_create_file(dev, &dev_attr_dev);
                 if (error)
                         goto DevAttrError;
 
                 error = device_create_sys_dev_entry(dev);
                 if (error)
                         goto SysEntryError;
 
                 devtmpfs_create_node(dev);
         }
 
         /* Notify clients of device addition.  This call must come
          * after dpm_sysfs_add() and before kobject_uevent().
          */
         if (dev->bus)
                 blocking_notifier_call_chain(&dev->bus->p->bus_notifier,
                                              BUS_NOTIFY_ADD_DEVICE, dev);
 
         kobject_uevent(&dev->kobj, KOBJ_ADD);
         bus_probe_device(dev);
         if (parent)
                 klist_add_tail(&dev->p->knode_parent,
                                &parent->p->klist_children);
 
         if (dev->class) {
                 mutex_lock(&dev->class->p->mutex);
                 /* tie the class to the device */
                 klist_add_tail(&dev->knode_class,
                                &dev->class->p->klist_devices);
 
                 /* notify any interfaces that the device is here */
                 list_for_each_entry(class_intf,
                                     &dev->class->p->interfaces, node)
                         if (class_intf->add_dev)
                                 class_intf->add_dev(dev, class_intf);
                 mutex_unlock(&dev->class->p->mutex);
         }
 done:
         put_device(dev);
         return error;
  SysEntryError:
         if (MAJOR(dev->devt))
                 device_remove_file(dev, &dev_attr_dev);
  DevAttrError:
         device_pm_remove(dev);
         dpm_sysfs_remove(dev);
  DPMError:
         bus_remove_device(dev);
  BusError:
         device_remove_attrs(dev);
  AttrsError:
         device_remove_class_symlinks(dev);
  SymlinkError:
         device_remove_file(dev, &dev_attr_uevent);
  attrError:
         kobject_uevent(&dev->kobj, KOBJ_REMOVE);
         kobject_del(&dev->kobj);
  Error:
         cleanup_device_parent(dev);
         put_device(parent);
 name_error:
         kfree(dev->p);
         dev->p = NULL;
         goto done;
 }
 EXPORT_SYMBOL_GPL(device_add);
 
 /**
  * device_register - register a device with the system.
  * @dev: pointer to the device structure
  *
  * This happens in two clean steps - initialize the device
  * and add it to the system. The two steps can be called
  * separately, but this is the easiest and most common.
  * I.e. you should only call the two helpers separately if
  * have a clearly defined need to use and refcount the device
  * before it is added to the hierarchy.
  *
  * For more information, see the kerneldoc for device_initialize()
  * and device_add().
  *
  * NOTE: _Never_ directly free @dev after calling this function, even
  * if it returned an error! Always use put_device() to give up the
  * reference initialized in this function instead.
  */
 int device_register(struct device *dev)
 {
         device_initialize(dev);
         return device_add(dev);
 }
 EXPORT_SYMBOL_GPL(device_register);
 
 /**
  * get_device - increment reference count for device.
  * @dev: device.
  *
  * This simply forwards the call to kobject_get(), though
  * we do take care to provide for the case that we get a NULL
  * pointer passed in.
  */
 struct device *get_device(struct device *dev)
 {
         return dev ? kobj_to_dev(kobject_get(&dev->kobj)) : NULL;
 }
 EXPORT_SYMBOL_GPL(get_device);
 
 /**
  * put_device - decrement reference count.
  * @dev: device in question.
  */
 void put_device(struct device *dev)
 {
         /* might_sleep(); */
         if (dev)
                 kobject_put(&dev->kobj);
 }
 EXPORT_SYMBOL_GPL(put_device);
 
 /**
  * device_del - delete device from system.
  * @dev: device.
  *
  * This is the first part of the device unregistration
  * sequence. This removes the device from the lists we control
  * from here, has it removed from the other driver model
  * subsystems it was added to in device_add(), and removes it
  * from the kobject hierarchy.
  *
  * NOTE: this should be called manually _iff_ device_add() was
  * also called manually.
  */
 void device_del(struct device *dev)
 {
         struct device *parent = dev->parent;
         struct class_interface *class_intf;
 
         /* Notify clients of device removal.  This call must come
          * before dpm_sysfs_remove().
          */
         if (dev->bus)
                 blocking_notifier_call_chain(&dev->bus->p->bus_notifier,
                                              BUS_NOTIFY_DEL_DEVICE, dev);
         dpm_sysfs_remove(dev);
         if (parent)
                 klist_del(&dev->p->knode_parent);
         if (MAJOR(dev->devt)) {
                 devtmpfs_delete_node(dev);
                 device_remove_sys_dev_entry(dev);
                 device_remove_file(dev, &dev_attr_dev);
         }
         if (dev->class) {
                 device_remove_class_symlinks(dev);
 
                 mutex_lock(&dev->class->p->mutex);
                 /* notify any interfaces that the device is now gone */
                 list_for_each_entry(class_intf,
                                     &dev->class->p->interfaces, node)
                         if (class_intf->remove_dev)
                                 class_intf->remove_dev(dev, class_intf);
                 /* remove the device from the class list */
                 klist_del(&dev->knode_class);
                 mutex_unlock(&dev->class->p->mutex);
         }
         device_remove_file(dev, &dev_attr_uevent);
         device_remove_attrs(dev);
         bus_remove_device(dev);
         device_pm_remove(dev);
         driver_deferred_probe_del(dev);
 
         /* Notify the platform of the removal, in case they
          * need to do anything...
          */
         if (platform_notify_remove)
                 platform_notify_remove(dev);
         if (dev->bus)
                 blocking_notifier_call_chain(&dev->bus->p->bus_notifier,
                                              BUS_NOTIFY_REMOVED_DEVICE, dev);
         kobject_uevent(&dev->kobj, KOBJ_REMOVE);
         cleanup_device_parent(dev);
         kobject_del(&dev->kobj);
         put_device(parent);
 }
 EXPORT_SYMBOL_GPL(device_del);
 
 /**
  * device_unregister - unregister device from system.
  * @dev: device going away.
  *
  * We do this in two parts, like we do device_register(). First,
  * we remove it from all the subsystems with device_del(), then
  * we decrement the reference count via put_device(). If that
  * is the final reference count, the device will be cleaned up
  * via device_release() above. Otherwise, the structure will
  * stick around until the final reference to the device is dropped.
  */
 void device_unregister(struct device *dev)
 {
         pr_debug("device: '%s': %s\n", dev_name(dev), __func__);
         device_del(dev);
         put_device(dev);
 }
 EXPORT_SYMBOL_GPL(device_unregister);
 
 static struct device *next_device(struct klist_iter *i)
 {
         struct klist_node *n = klist_next(i);
         struct device *dev = NULL;
         struct device_private *p;
 
         if (n) {
                 p = to_device_private_parent(n);
                 dev = p->device;
         }
         return dev;
 }
 
 /**
  * device_get_devnode - path of device node file
  * @dev: device
  * @mode: returned file access mode
  * @uid: returned file owner
  * @gid: returned file group
  * @tmp: possibly allocated string
  *
  * Return the relative path of a possible device node.
  * Non-default names may need to allocate a memory to compose
  * a name. This memory is returned in tmp and needs to be
  * freed by the caller.
  */
 const char *device_get_devnode(struct device *dev,
                                umode_t *mode, kuid_t *uid, kgid_t *gid,
                                const char **tmp)
 {
         char *s;
 
         *tmp = NULL;
 
         /* the device type may provide a specific name */
         if (dev->type && dev->type->devnode)
                 *tmp = dev->type->devnode(dev, mode, uid, gid);
         if (*tmp)
                 return *tmp;
 
         /* the class may provide a specific name */
         if (dev->class && dev->class->devnode)
                 *tmp = dev->class->devnode(dev, mode);
         if (*tmp)
                 return *tmp;
 
         /* return name without allocation, tmp == NULL */
         if (strchr(dev_name(dev), '!') == NULL)
                 return dev_name(dev);
 
         /* replace '!' in the name with '/' */
         *tmp = kstrdup(dev_name(dev), GFP_KERNEL);
         if (!*tmp)
                 return NULL;
         while ((s = strchr(*tmp, '!')))
                 s[0] = '/';
         return *tmp;
 }
 
 /**
  * device_for_each_child - device child iterator.
  * @parent: parent struct device.
  * @fn: function to be called for each device.
  * @data: data for the callback.
  *
  * Iterate over @parent's child devices, and call @fn for each,
  * passing it @data.
  *
  * We check the return of @fn each time. If it returns anything
  * other than 0, we break out and return that value.
  */
 int device_for_each_child(struct device *parent, void *data,
                           int (*fn)(struct device *dev, void *data))
 {
         struct klist_iter i;
         struct device *child;
         int error = 0;
 
         if (!parent->p)
                 return 0;
 
         klist_iter_init(&parent->p->klist_children, &i);
         while ((child = next_device(&i)) && !error)
                 error = fn(child, data);
         klist_iter_exit(&i);
         return error;
 }
 EXPORT_SYMBOL_GPL(device_for_each_child);
 
 /**
  * device_find_child - device iterator for locating a particular device.
  * @parent: parent struct device
  * @match: Callback function to check device
  * @data: Data to pass to match function
  *
  * This is similar to the device_for_each_child() function above, but it
  * returns a reference to a device that is 'found' for later use, as
  * determined by the @match callback.
  *
  * The callback should return 0 if the device doesn't match and non-zero
  * if it does.  If the callback returns non-zero and a reference to the
  * current device can be obtained, this function will return to the caller
  * and not iterate over any more devices.
  *
  * NOTE: you will need to drop the reference with put_device() after use.
  */
 struct device *device_find_child(struct device *parent, void *data,
                                  int (*match)(struct device *dev, void *data))
 {
         struct klist_iter i;
         struct device *child;
 
         if (!parent)
                 return NULL;
 
         klist_iter_init(&parent->p->klist_children, &i);
         while ((child = next_device(&i)))
                 if (match(child, data) && get_device(child))
                         break;
         klist_iter_exit(&i);
         return child;
 }
 EXPORT_SYMBOL_GPL(device_find_child);
 
 int __init devices_init(void)
 {
         devices_kset = kset_create_and_add("devices", &device_uevent_ops, NULL);
         if (!devices_kset)
                 return -ENOMEM;
         dev_kobj = kobject_create_and_add("dev", NULL);
         if (!dev_kobj)
                 goto dev_kobj_err;
         sysfs_dev_block_kobj = kobject_create_and_add("block", dev_kobj);
         if (!sysfs_dev_block_kobj)
                 goto block_kobj_err;
         sysfs_dev_char_kobj = kobject_create_and_add("char", dev_kobj);
         if (!sysfs_dev_char_kobj)
                 goto char_kobj_err;
 
         return 0;
 
  char_kobj_err:
         kobject_put(sysfs_dev_block_kobj);
  block_kobj_err:
         kobject_put(dev_kobj);
  dev_kobj_err:
         kset_unregister(devices_kset);
         return -ENOMEM;
 }
 
 static int device_check_offline(struct device *dev, void *not_used)
 {
         int ret;
 
         ret = device_for_each_child(dev, NULL, device_check_offline);
         if (ret)
                 return ret;
 
         return device_supports_offline(dev) && !dev->offline ? -EBUSY : 0;
 }
 
 /**
  * device_offline - Prepare the device for hot-removal.
  * @dev: Device to be put offline.
  *
  * Execute the device bus type's .offline() callback, if present, to prepare
  * the device for a subsequent hot-removal.  If that succeeds, the device must
  * not be used until either it is removed or its bus type's .online() callback
  * is executed.
  *
  * Call under device_hotplug_lock.
  */
 int device_offline(struct device *dev)
 {
         int ret;
 
         if (dev->offline_disabled)
                 return -EPERM;
 
         ret = device_for_each_child(dev, NULL, device_check_offline);
         if (ret)
                 return ret;
 
         device_lock(dev);
         if (device_supports_offline(dev)) {
                 if (dev->offline) {
                         ret = 1;
                 } else {
                         ret = dev->bus->offline(dev);
                         if (!ret) {
                                 kobject_uevent(&dev->kobj, KOBJ_OFFLINE);
                                 dev->offline = true;
                         }
                 }
         }
         device_unlock(dev);
 
         return ret;
 }
 
 /**
  * device_online - Put the device back online after successful device_offline().
  * @dev: Device to be put back online.
  *
  * If device_offline() has been successfully executed for @dev, but the device
  * has not been removed subsequently, execute its bus type's .online() callback
  * to indicate that the device can be used again.
  *
  * Call under device_hotplug_lock.
  */
 int device_online(struct device *dev)
 {
         int ret = 0;
 
         device_lock(dev);
         if (device_supports_offline(dev)) {
                 if (dev->offline) {
                         ret = dev->bus->online(dev);
                         if (!ret) {
                                 kobject_uevent(&dev->kobj, KOBJ_ONLINE);
                                 dev->offline = false;
                         }
                 } else {
                         ret = 1;
                 }
         }
         device_unlock(dev);
 
         return ret;
 }
 
 struct root_device {
         struct device dev;
         struct module *owner;
 };
 
 static inline struct root_device *to_root_device(struct device *d)
 {
         return container_of(d, struct root_device, dev);
 }
 
 static void root_device_release(struct device *dev)
 {
         kfree(to_root_device(dev));
 }
 
 /**
  * __root_device_register - allocate and register a root device
  * @name: root device name
  * @owner: owner module of the root device, usually THIS_MODULE
  *
  * This function allocates a root device and registers it
  * using device_register(). In order to free the returned
  * device, use root_device_unregister().
  *
  * Root devices are dummy devices which allow other devices
  * to be grouped under /sys/devices. Use this function to
  * allocate a root device and then use it as the parent of
  * any device which should appear under /sys/devices/{name}
  *
  * The /sys/devices/{name} directory will also contain a
  * 'module' symlink which points to the @owner directory
  * in sysfs.
  *
  * Returns &struct device pointer on success, or ERR_PTR() on error.
  *
  * Note: You probably want to use root_device_register().
  */
 struct device *__root_device_register(const char *name, struct module *owner)
 {
         struct root_device *root;
         int err = -ENOMEM;
 
         root = kzalloc(sizeof(struct root_device), GFP_KERNEL);
         if (!root)
                 return ERR_PTR(err);
 
         err = dev_set_name(&root->dev, "%s", name);
         if (err) {
                 kfree(root);
                 return ERR_PTR(err);
         }
 
         root->dev.release = root_device_release;
 
         err = device_register(&root->dev);
         if (err) {
                 put_device(&root->dev);
                 return ERR_PTR(err);
         }
 
 #ifdef CONFIG_MODULES   /* gotta find a "cleaner" way to do this */
         if (owner) {
                 struct module_kobject *mk = &owner->mkobj;
 
                 err = sysfs_create_link(&root->dev.kobj, &mk->kobj, "module");
                 if (err) {
                         device_unregister(&root->dev);
                         return ERR_PTR(err);
                 }
                 root->owner = owner;
         }
 #endif
 
         return &root->dev;
 }
 EXPORT_SYMBOL_GPL(__root_device_register);
 
 /**
  * root_device_unregister - unregister and free a root device
  * @dev: device going away
  *
  * This function unregisters and cleans up a device that was created by
  * root_device_register().
  */
 void root_device_unregister(struct device *dev)
 {
         struct root_device *root = to_root_device(dev);
 
         if (root->owner)
                 sysfs_remove_link(&root->dev.kobj, "module");
 
         device_unregister(dev);
 }
 EXPORT_SYMBOL_GPL(root_device_unregister);
 
 
 static void device_create_release(struct device *dev)
 {
         pr_debug("device: '%s': %s\n", dev_name(dev), __func__);
         kfree(dev);
 }
 
 static struct device *
 device_create_groups_vargs(struct class *class, struct device *parent,
                            dev_t devt, void *drvdata,
                            const struct attribute_group **groups,
                            const char *fmt, va_list args)
 {
         struct device *dev = NULL;
         int retval = -ENODEV;
 
         if (class == NULL || IS_ERR(class))
                 goto error;
 
         dev = kzalloc(sizeof(*dev), GFP_KERNEL);
         if (!dev) {
                 retval = -ENOMEM;
                 goto error;
         }
 
         device_initialize(dev);
         dev->devt = devt;
         dev->class = class;
         dev->parent = parent;
         dev->groups = groups;
         dev->release = device_create_release;
         dev_set_drvdata(dev, drvdata);
 
         retval = kobject_set_name_vargs(&dev->kobj, fmt, args);
         if (retval)
                 goto error;
 
         retval = device_add(dev);
         if (retval)
                 goto error;
 
         return dev;
 
 error:
         put_device(dev);
         return ERR_PTR(retval);
 }
 
 /**
  * device_create_vargs - creates a device and registers it with sysfs
  * @class: pointer to the struct class that this device should be registered to
  * @parent: pointer to the parent struct device of this new device, if any
  * @devt: the dev_t for the char device to be added
  * @drvdata: the data to be added to the device for callbacks
  * @fmt: string for the device's name
  * @args: va_list for the device's name
  *
  * This function can be used by char device classes.  A struct device
  * will be created in sysfs, registered to the specified class.
  *
  * A "dev" file will be created, showing the dev_t for the device, if
  * the dev_t is not 0,0.
  * If a pointer to a parent struct device is passed in, the newly created
  * struct device will be a child of that device in sysfs.
  * The pointer to the struct device will be returned from the call.
  * Any further sysfs files that might be required can be created using this
  * pointer.
  *
  * Returns &struct device pointer on success, or ERR_PTR() on error.
  *
  * Note: the struct class passed to this function must have previously
  * been created with a call to class_create().
  */
 struct device *device_create_vargs(struct class *class, struct device *parent,
                                    dev_t devt, void *drvdata, const char *fmt,
                                    va_list args)
 {
         return device_create_groups_vargs(class, parent, devt, drvdata, NULL,
                                           fmt, args);
 }
 EXPORT_SYMBOL_GPL(device_create_vargs);
 
 /**
  * device_create - creates a device and registers it with sysfs
  * @class: pointer to the struct class that this device should be registered to
  * @parent: pointer to the parent struct device of this new device, if any
  * @devt: the dev_t for the char device to be added
  * @drvdata: the data to be added to the device for callbacks
  * @fmt: string for the device's name
  *
  * This function can be used by char device classes.  A struct device
  * will be created in sysfs, registered to the specified class.
  *
  * A "dev" file will be created, showing the dev_t for the device, if
  * the dev_t is not 0,0.
  * If a pointer to a parent struct device is passed in, the newly created
  * struct device will be a child of that device in sysfs.
  * The pointer to the struct device will be returned from the call.
  * Any further sysfs files that might be required can be created using this
  * pointer.
  *
  * Returns &struct device pointer on success, or ERR_PTR() on error.
  *
  * Note: the struct class passed to this function must have previously
  * been created with a call to class_create().
  */
 struct device *device_create(struct class *class, struct device *parent,
                              dev_t devt, void *drvdata, const char *fmt, ...)
 {
         va_list vargs;
         struct device *dev;
 
         va_start(vargs, fmt);
         dev = device_create_vargs(class, parent, devt, drvdata, fmt, vargs);
         va_end(vargs);
         return dev;
 }
 EXPORT_SYMBOL_GPL(device_create);
 
 /**
  * device_create_with_groups - creates a device and registers it with sysfs
  * @class: pointer to the struct class that this device should be registered to
  * @parent: pointer to the parent struct device of this new device, if any
  * @devt: the dev_t for the char device to be added
  * @drvdata: the data to be added to the device for callbacks
  * @groups: NULL-terminated list of attribute groups to be created
  * @fmt: string for the device's name
  *
  * This function can be used by char device classes.  A struct device
  * will be created in sysfs, registered to the specified class.
  * Additional attributes specified in the groups parameter will also
  * be created automatically.
  *
  * A "dev" file will be created, showing the dev_t for the device, if
  * the dev_t is not 0,0.
  * If a pointer to a parent struct device is passed in, the newly created
  * struct device will be a child of that device in sysfs.
  * The pointer to the struct device will be returned from the call.
  * Any further sysfs files that might be required can be created using this
  * pointer.
  *
  * Returns &struct device pointer on success, or ERR_PTR() on error.
  *
  * Note: the struct class passed to this function must have previously
  * been created with a call to class_create().
  */
 struct device *device_create_with_groups(struct class *class,
                                          struct device *parent, dev_t devt,
                                          void *drvdata,
                                          const struct attribute_group **groups,
                                          const char *fmt, ...)
 {
         va_list vargs;
         struct device *dev;
 
         va_start(vargs, fmt);
         dev = device_create_groups_vargs(class, parent, devt, drvdata, groups,
                                          fmt, vargs);
         va_end(vargs);
         return dev;
 }
 EXPORT_SYMBOL_GPL(device_create_with_groups);
 
 static int __match_devt(struct device *dev, const void *data)
 {
         const dev_t *devt = data;
 
         return dev->devt == *devt;
 }
 
 /**
  * device_destroy - removes a device that was created with device_create()
  * @class: pointer to the struct class that this device was registered with
  * @devt: the dev_t of the device that was previously registered
  *
  * This call unregisters and cleans up a device that was created with a
  * call to device_create().
  */
 void device_destroy(struct class *class, dev_t devt)
 {
         struct device *dev;
 
         dev = class_find_device(class, NULL, &devt, __match_devt);
         if (dev) {
                 put_device(dev);
                 device_unregister(dev);
         }
 }
 EXPORT_SYMBOL_GPL(device_destroy);
 
 /**
  * device_rename - renames a device
  * @dev: the pointer to the struct device to be renamed
  * @new_name: the new name of the device
  *
  * It is the responsibility of the caller to provide mutual
  * exclusion between two different calls of device_rename
  * on the same device to ensure that new_name is valid and
  * won't conflict with other devices.
  *
  * Note: Don't call this function.  Currently, the networking layer calls this
  * function, but that will change.  The following text from Kay Sievers offers
  * some insight:
  *
  * Renaming devices is racy at many levels, symlinks and other stuff are not
  * replaced atomically, and you get a "move" uevent, but it's not easy to
  * connect the event to the old and new device. Device nodes are not renamed at
  * all, there isn't even support for that in the kernel now.
  *
  * In the meantime, during renaming, your target name might be taken by another
  * driver, creating conflicts. Or the old name is taken directly after you
  * renamed it -- then you get events for the same DEVPATH, before you even see
  * the "move" event. It's just a mess, and nothing new should ever rely on
  * kernel device renaming. Besides that, it's not even implemented now for
  * other things than (driver-core wise very simple) network devices.
  *
  * We are currently about to change network renaming in udev to completely
  * disallow renaming of devices in the same namespace as the kernel uses,
  * because we can't solve the problems properly, that arise with swapping names
  * of multiple interfaces without races. Means, renaming of eth[0-9]* will only
  * be allowed to some other name than eth[0-9]*, for the aforementioned
  * reasons.
  *
  * Make up a "real" name in the driver before you register anything, or add
  * some other attributes for userspace to find the device, or use udev to add
  * symlinks -- but never rename kernel devices later, it's a complete mess. We
  * don't even want to get into that and try to implement the missing pieces in
  * the core. We really have other pieces to fix in the driver core mess. :)
  */
 int device_rename(struct device *dev, const char *new_name)
 {
         struct kobject *kobj = &dev->kobj;
         char *old_device_name = NULL;
         int error;
 
         dev = get_device(dev);
         if (!dev)
                 return -EINVAL;
 
         dev_dbg(dev, "renaming to %s\n", new_name);
 
         old_device_name = kstrdup(dev_name(dev), GFP_KERNEL);
         if (!old_device_name) {
                 error = -ENOMEM;
                 goto out;
         }
 
         if (dev->class) {
                 error = sysfs_rename_link_ns(&dev->class->p->subsys.kobj,
                                              kobj, old_device_name,
                                              new_name, kobject_namespace(kobj));
                 if (error)
                         goto out;
         }
 
         error = kobject_rename(kobj, new_name);
         if (error)
                 goto out;
 
 out:
         put_device(dev);
 
         kfree(old_device_name);
 
         return error;
 }
 EXPORT_SYMBOL_GPL(device_rename);
 
 static int device_move_class_links(struct device *dev,
                                    struct device *old_parent,
                                    struct device *new_parent)
 {
         int error = 0;
 
         if (old_parent)
                 sysfs_remove_link(&dev->kobj, "device");
         if (new_parent)
                 error = sysfs_create_link(&dev->kobj, &new_parent->kobj,
                                           "device");
         return error;
 }
 
 /**
  * device_move - moves a device to a new parent
  * @dev: the pointer to the struct device to be moved
  * @new_parent: the new parent of the device (can by NULL)
  * @dpm_order: how to reorder the dpm_list
  */
 int device_move(struct device *dev, struct device *new_parent,
                 enum dpm_order dpm_order)
 {
         int error;
         struct device *old_parent;
         struct kobject *new_parent_kobj;
 
         dev = get_device(dev);
         if (!dev)
                 return -EINVAL;
 
         device_pm_lock();
         new_parent = get_device(new_parent);
         new_parent_kobj = get_device_parent(dev, new_parent);
 
         pr_debug("device: '%s': %s: moving to '%s'\n", dev_name(dev),
                  __func__, new_parent ? dev_name(new_parent) : "<NULL>");
         error = kobject_move(&dev->kobj, new_parent_kobj);
         if (error) {
                 cleanup_glue_dir(dev, new_parent_kobj);
                 put_device(new_parent);
                 goto out;
         }
         old_parent = dev->parent;
         dev->parent = new_parent;
         if (old_parent)
                 klist_remove(&dev->p->knode_parent);
         if (new_parent) {
                 klist_add_tail(&dev->p->knode_parent,
                                &new_parent->p->klist_children);
                 set_dev_node(dev, dev_to_node(new_parent));
         }
 
         if (dev->class) {
                 error = device_move_class_links(dev, old_parent, new_parent);
                 if (error) {
                         /* We ignore errors on cleanup since we're hosed anyway... */
                         device_move_class_links(dev, new_parent, old_parent);
                         if (!kobject_move(&dev->kobj, &old_parent->kobj)) {
                                 if (new_parent)
                                         klist_remove(&dev->p->knode_parent);
                                 dev->parent = old_parent;
                                 if (old_parent) {
                                         klist_add_tail(&dev->p->knode_parent,
                                                        &old_parent->p->klist_children);
                                         set_dev_node(dev, dev_to_node(old_parent));
                                 }
                         }
                         cleanup_glue_dir(dev, new_parent_kobj);
                         put_device(new_parent);
                         goto out;
                 }
         }
         switch (dpm_order) {
         case DPM_ORDER_NONE:
                 break;
         case DPM_ORDER_DEV_AFTER_PARENT:
                 device_pm_move_after(dev, new_parent);
                 break;
         case DPM_ORDER_PARENT_BEFORE_DEV:
                 device_pm_move_before(new_parent, dev);
                 break;
         case DPM_ORDER_DEV_LAST:
                 device_pm_move_last(dev);
                 break;
         }
 
         put_device(old_parent);
 out:
         device_pm_unlock();
         put_device(dev);
         return error;
 }
 EXPORT_SYMBOL_GPL(device_move);
 
 /**
  * device_shutdown - call ->shutdown() on each device to shutdown.
  */
 void device_shutdown(void)
 {
         struct device *dev, *parent;
 
         spin_lock(&devices_kset->list_lock);
         /*
          * Walk the devices list backward, shutting down each in turn.
          * Beware that device unplug events may also start pulling
          * devices offline, even as the system is shutting down.
          */
         while (!list_empty(&devices_kset->list)) {
                 dev = list_entry(devices_kset->list.prev, struct device,
                                 kobj.entry);
 
                 /*
                  * hold reference count of device's parent to
                  * prevent it from being freed because parent's
                  * lock is to be held
                  */
                 parent = get_device(dev->parent);
                 get_device(dev);
                 /*
                  * Make sure the device is off the kset list, in the
                  * event that dev->*->shutdown() doesn't remove it.
                  */
                 list_del_init(&dev->kobj.entry);
                 spin_unlock(&devices_kset->list_lock);
 
                 /* hold lock to avoid race with probe/release */
                 if (parent)
                         device_lock(parent);
                 device_lock(dev);
 
                 /* Don't allow any more runtime suspends */
                 pm_runtime_get_noresume(dev);
                 pm_runtime_barrier(dev);
 
                 if (dev->bus && dev->bus->shutdown) {
                         if (initcall_debug)
                                 dev_info(dev, "shutdown\n");
                         dev->bus->shutdown(dev);
                 } else if (dev->driver && dev->driver->shutdown) {
                         if (initcall_debug)
                                 dev_info(dev, "shutdown\n");
                         dev->driver->shutdown(dev);
                 }
 
                 device_unlock(dev);
                 if (parent)
                         device_unlock(parent);
 
                 put_device(dev);
                 put_device(parent);
 
                 spin_lock(&devices_kset->list_lock);
         }
         spin_unlock(&devices_kset->list_lock);
 }
 
 /*
  * Device logging functions
  */
 
 #ifdef CONFIG_PRINTK
 static int
 create_syslog_header(const struct device *dev, char *hdr, size_t hdrlen)
 {
         const char *subsys;
         size_t pos = 0;
 
         if (dev->class)
                 subsys = dev->class->name;
         else if (dev->bus)
                 subsys = dev->bus->name;
         else
                 return 0;
 
         pos += snprintf(hdr + pos, hdrlen - pos, "SUBSYSTEM=%s", subsys);
         if (pos >= hdrlen)
                 goto overflow;
 
         /*
          * Add device identifier DEVICE=:
          *   b12:8         block dev_t
          *   c127:3        char dev_t
          *   n8            netdev ifindex
          *   +sound:card0  subsystem:devname
          */
         if (MAJOR(dev->devt)) {
                 char c;
 
                 if (strcmp(subsys, "block") == 0)
                         c = 'b';
                 else
                         c = 'c';
                 pos++;
                 pos += snprintf(hdr + pos, hdrlen - pos,
                                 "DEVICE=%c%u:%u",
                                 c, MAJOR(dev->devt), MINOR(dev->devt));
         } else if (strcmp(subsys, "net") == 0) {
                 struct net_device *net = to_net_dev(dev);
 
                 pos++;
                 pos += snprintf(hdr + pos, hdrlen - pos,
                                 "DEVICE=n%u", net->ifindex);
         } else {
                 pos++;
                 pos += snprintf(hdr + pos, hdrlen - pos,
                                 "DEVICE=+%s:%s", subsys, dev_name(dev));
         }
 
         if (pos >= hdrlen)
                 goto overflow;
 
         return pos;
 
 overflow:
         dev_WARN(dev, "device/subsystem name too long");
         return 0;
 }
 
 int dev_vprintk_emit(int level, const struct device *dev,
                      const char *fmt, va_list args)
 {
         char hdr[128];
         size_t hdrlen;
 
         hdrlen = create_syslog_header(dev, hdr, sizeof(hdr));
 
         return vprintk_emit(0, level, hdrlen ? hdr : NULL, hdrlen, fmt, args);
 }
 EXPORT_SYMBOL(dev_vprintk_emit);
 
 int dev_printk_emit(int level, const struct device *dev, const char *fmt, ...)
 {
         va_list args;
         int r;
 
         va_start(args, fmt);
 
         r = dev_vprintk_emit(level, dev, fmt, args);
 
         va_end(args);
 
         return r;
 }
 EXPORT_SYMBOL(dev_printk_emit);
 
 static void __dev_printk(const char *level, const struct device *dev,
                         struct va_format *vaf)
 {
         if (dev)
                 dev_printk_emit(level[1] - '', dev, "%s %s: %pV",
                                 dev_driver_string(dev), dev_name(dev), vaf);
         else
                 printk("%s(NULL device *): %pV", level, vaf);
 }
 
 void dev_printk(const char *level, const struct device *dev,
                 const char *fmt, ...)
 {
         struct va_format vaf;
         va_list args;
 
         va_start(args, fmt);
 
         vaf.fmt = fmt;
         vaf.va = &args;
 
         __dev_printk(level, dev, &vaf);
 
         va_end(args);
 }
 EXPORT_SYMBOL(dev_printk);
 
 #define define_dev_printk_level(func, kern_level)               \
 void func(const struct device *dev, const char *fmt, ...)       \
 {                                                               \
         struct va_format vaf;                                   \
         va_list args;                                           \
                                                                 \
         va_start(args, fmt);                                    \
                                                                 \
         vaf.fmt = fmt;                                          \
         vaf.va = &args;                                         \
                                                                 \
         __dev_printk(kern_level, dev, &vaf);                    \
                                                                 \
         va_end(args);                                           \
 }                                                               \
 EXPORT_SYMBOL(func);
 
 define_dev_printk_level(dev_emerg, KERN_EMERG);
 define_dev_printk_level(dev_alert, KERN_ALERT);
 define_dev_printk_level(dev_crit, KERN_CRIT);
 define_dev_printk_level(dev_err, KERN_ERR);
 define_dev_printk_level(dev_warn, KERN_WARNING);
 define_dev_printk_level(dev_notice, KERN_NOTICE);
 define_dev_printk_level(_dev_info, KERN_INFO);
 
 #endif
 
 static inline bool fwnode_is_primary(struct fwnode_handle *fwnode)
 {
         return fwnode && !IS_ERR(fwnode->secondary);
 }
 
 /**
  * set_primary_fwnode - Change the primary firmware node of a given device.
  * @dev: Device to handle.
  * @fwnode: New primary firmware node of the device.
  *
  * Set the device's firmware node pointer to @fwnode, but if a secondary
  * firmware node of the device is present, preserve it.
  */
 void set_primary_fwnode(struct device *dev, struct fwnode_handle *fwnode)
 {
         if (fwnode) {
                 struct fwnode_handle *fn = dev->fwnode;
 
                 if (fwnode_is_primary(fn))
                         fn = fn->secondary;
 
                 fwnode->secondary = fn;
                 dev->fwnode = fwnode;
         } else {
                 dev->fwnode = fwnode_is_primary(dev->fwnode) ?
                         dev->fwnode->secondary : NULL;
         }
 }
 EXPORT_SYMBOL_GPL(set_primary_fwnode);
 
 /**
  * set_secondary_fwnode - Change the secondary firmware node of a given device.
  * @dev: Device to handle.
  * @fwnode: New secondary firmware node of the device.
  *
  * If a primary firmware node of the device is present, set its secondary
  * pointer to @fwnode.  Otherwise, set the device's firmware node pointer to
  * @fwnode.
  */
 void set_secondary_fwnode(struct device *dev, struct fwnode_handle *fwnode)
 {
         if (fwnode)
                 fwnode->secondary = ERR_PTR(-ENODEV);
 
         if (fwnode_is_primary(dev->fwnode))
                 dev->fwnode->secondary = fwnode;
         else
                 dev->fwnode = fwnode;
 }
 
```

```
/*
 * net/sched/sch_generic.c      Generic packet scheduler routines.
 *
 *              This program is free software; you can redistribute it and/or
 *              modify it under the terms of the GNU General Public License
 *              as published by the Free Software Foundation; either version
 *              2 of the License, or (at your option) any later version.
 *
 * Authors:     Alexey Kuznetsov, <kuznet@ms2.inr.ac.ru>
 *              Jamal Hadi Salim, <hadi@cyberus.ca> 990601
 *              - Ingress support
 */

#include <linux/bitops.h>
#include <linux/module.h>
#include <linux/types.h>
#include <linux/kernel.h>
#include <linux/sched.h>
#include <linux/string.h>
#include <linux/errno.h>
#include <linux/netdevice.h>
#include <linux/skbuff.h>
#include <linux/rtnetlink.h>
#include <linux/init.h>
#include <linux/rcupdate.h>
#include <linux/list.h>
#include <linux/slab.h>
#include <linux/if_vlan.h>
#include <net/sch_generic.h>
#include <net/pkt_sched.h>
#include <net/dst.h>

/* Qdisc to use by default */
const struct Qdisc_ops *default_qdisc_ops = &pfifo_fast_ops;
EXPORT_SYMBOL(default_qdisc_ops);

/* Main transmission queue. */

/* Modifications to data participating in scheduling must be protected with
 * qdisc_lock(qdisc) spinlock.
 *
 * The idea is the following:
 * - enqueue, dequeue are serialized via qdisc root lock
 * - ingress filtering is also serialized via qdisc root lock
 * - updates to tree and tree walking are only done under the rtnl mutex.
 */

static inline int dev_requeue_skb(struct sk_buff *skb, struct Qdisc *q)
{
        q->gso_skb = skb;
        q->qstats.requeues++;
        q->q.qlen++;    /* it's still part of the queue */
        __netif_schedule(q);

        return 0;
}

static void try_bulk_dequeue_skb(struct Qdisc *q,
                                 struct sk_buff *skb,
                                 const struct netdev_queue *txq,
                                 int *packets)
{
        int bytelimit = qdisc_avail_bulklimit(txq) - skb->len;

        while (bytelimit > 0) {
                struct sk_buff *nskb = q->dequeue(q);

                if (!nskb)
                        break;

                bytelimit -= nskb->len; /* covers GSO len */
                skb->next = nskb;
                skb = nskb;
                (*packets)++; /* GSO counts as one pkt */
        }
        skb->next = NULL;
}

/* Note that dequeue_skb can possibly return a SKB list (via skb->next).
 * A requeued skb (via q->gso_skb) can also be a SKB list.
 */
static struct sk_buff *dequeue_skb(struct Qdisc *q, bool *validate,
                                   int *packets)
{
        struct sk_buff *skb = q->gso_skb;
        const struct netdev_queue *txq = q->dev_queue;

        *packets = 1;
        *validate = true;
        if (unlikely(skb)) {
                /* check the reason of requeuing without tx lock first */
                txq = skb_get_tx_queue(txq->dev, skb);
                if (!netif_xmit_frozen_or_stopped(txq)) {
                        q->gso_skb = NULL;
                        q->q.qlen--;
                } else
                        skb = NULL;
                /* skb in gso_skb were already validated */
                *validate = false;
        } else {
                if (!(q->flags & TCQ_F_ONETXQUEUE) ||
                    !netif_xmit_frozen_or_stopped(txq)) {
                        skb = q->dequeue(q);
                        if (skb && qdisc_may_bulk(q))
                                try_bulk_dequeue_skb(q, skb, txq, packets);
                }
        }
        return skb;
}

static inline int handle_dev_cpu_collision(struct sk_buff *skb,
                                           struct netdev_queue *dev_queue,
                                           struct Qdisc *q)
{
        int ret;

        if (unlikely(dev_queue->xmit_lock_owner == smp_processor_id())) {
                /*
                 * Same CPU holding the lock. It may be a transient
                 * configuration error, when hard_start_xmit() recurses. We
                 * detect it by checking xmit owner and drop the packet when
                 * deadloop is detected. Return OK to try the next skb.
                 */
                kfree_skb_list(skb);
                net_warn_ratelimited("Dead loop on netdevice %s, fix it urgently!\n",
                                     dev_queue->dev->name);
                ret = qdisc_qlen(q);
        } else {
                /*
                 * Another cpu is holding lock, requeue & delay xmits for
                 * some time.
                 */
                __this_cpu_inc(softnet_data.cpu_collision);
                ret = dev_requeue_skb(skb, q);
        }

        return ret;
}

/*
 * Transmit possibly several skbs, and handle the return status as
 * required. Holding the __QDISC___STATE_RUNNING bit guarantees that
 * only one CPU can execute this function.
 *
 * Returns to the caller:
 *                              0  - queue is empty or throttled.
 *                              >0 - queue is not empty.
 */
int sch_direct_xmit(struct sk_buff *skb, struct Qdisc *q,
                    struct net_device *dev, struct netdev_queue *txq,
                    spinlock_t *root_lock, bool validate)
{
        int ret = NETDEV_TX_BUSY;

        /* And release qdisc */
        spin_unlock(root_lock);

        /* Note that we validate skb (GSO, checksum, ...) outside of locks */
        if (validate)
                skb = validate_xmit_skb_list(skb, dev);

        if (skb) {
                HARD_TX_LOCK(dev, txq, smp_processor_id());
                if (!netif_xmit_frozen_or_stopped(txq))
                        skb = dev_hard_start_xmit(skb, dev, txq, &ret);

                HARD_TX_UNLOCK(dev, txq);
        }
        spin_lock(root_lock);

        if (dev_xmit_complete(ret)) {
                /* Driver sent out skb successfully or skb was consumed */
                ret = qdisc_qlen(q);
        } else if (ret == NETDEV_TX_LOCKED) {
                /* Driver try lock failed */
                ret = handle_dev_cpu_collision(skb, txq, q);
        } else {
                /* Driver returned NETDEV_TX_BUSY - requeue skb */
                if (unlikely(ret != NETDEV_TX_BUSY))
                        net_warn_ratelimited("BUG %s code %d qlen %d\n",
                                             dev->name, ret, q->q.qlen);

                ret = dev_requeue_skb(skb, q);
        }

        if (ret && netif_xmit_frozen_or_stopped(txq))
                ret = 0;

        return ret;
}

/*
 * NOTE: Called under qdisc_lock(q) with locally disabled BH.
 *
 * __QDISC___STATE_RUNNING guarantees only one CPU can process
 * this qdisc at a time. qdisc_lock(q) serializes queue accesses for
 * this queue.
 *
 *  netif_tx_lock serializes accesses to device driver.
 *
 *  qdisc_lock(q) and netif_tx_lock are mutually exclusive,
 *  if one is grabbed, another must be free.
 *
 * Note, that this procedure can be called by a watchdog timer
 *
 * Returns to the caller:
 *                              0  - queue is empty or throttled.
 *                              >0 - queue is not empty.
 *
 */
static inline int qdisc_restart(struct Qdisc *q, int *packets)
{
        struct netdev_queue *txq;
        struct net_device *dev;
        spinlock_t *root_lock;
        struct sk_buff *skb;
        bool validate;

        /* Dequeue packet */
        skb = dequeue_skb(q, &validate, packets);
        if (unlikely(!skb))
                return 0;

        root_lock = qdisc_lock(q);
        dev = qdisc_dev(q);
        txq = skb_get_tx_queue(dev, skb);

        return sch_direct_xmit(skb, q, dev, txq, root_lock, validate);
}

void __qdisc_run(struct Qdisc *q)
{
        int quota = weight_p;
        int packets;

        while (qdisc_restart(q, &packets)) {
                /*
                 * Ordered by possible occurrence: Postpone processing if
                 * 1. we've exceeded packet quota
                 * 2. another process needs the CPU;
                 */
                quota -= packets;
                if (quota <= 0 || need_resched()) {
                        __netif_schedule(q);
                        break;
                }
        }

        qdisc_run_end(q);
}

unsigned long dev_trans_start(struct net_device *dev)
{
        unsigned long val, res;
        unsigned int i;

        if (is_vlan_dev(dev))
                dev = vlan_dev_real_dev(dev);
        res = dev->trans_start;
        for (i = 0; i < dev->num_tx_queues; i++) {
                val = netdev_get_tx_queue(dev, i)->trans_start;
                if (val && time_after(val, res))
                        res = val;
        }
        dev->trans_start = res;

        return res;
}
EXPORT_SYMBOL(dev_trans_start);

static void dev_watchdog(unsigned long arg)
{
        struct net_device *dev = (struct net_device *)arg;

        netif_tx_lock(dev);
        if (!qdisc_tx_is_noop(dev)) {
                if (netif_device_present(dev) &&
                    netif_running(dev) &&
                    netif_carrier_ok(dev)) {
                        int some_queue_timedout = 0;
                        unsigned int i;
                        unsigned long trans_start;

                        for (i = 0; i < dev->num_tx_queues; i++) {
                                struct netdev_queue *txq;

                                txq = netdev_get_tx_queue(dev, i);
                                /*
                                 * old device drivers set dev->trans_start
                                 */
                                trans_start = txq->trans_start ? : dev->trans_start;
                                if (netif_xmit_stopped(txq) &&
                                    time_after(jiffies, (trans_start +
                                                         dev->watchdog_timeo))) {
                                        some_queue_timedout = 1;
                                        txq->trans_timeout++;
                                        break;
                                }
                        }

                        if (some_queue_timedout) {
                                WARN_ONCE(1, KERN_INFO "NETDEV WATCHDOG: %s (%s): transmit queue %u timed out\n",
                                       dev->name, netdev_drivername(dev), i);
                                dev->netdev_ops->ndo_tx_timeout(dev);
                        }
                        if (!mod_timer(&dev->watchdog_timer,
                                       round_jiffies(jiffies +
                                                     dev->watchdog_timeo)))
                                dev_hold(dev);
                }
        }
        netif_tx_unlock(dev);

        dev_put(dev);
}

void __netdev_watchdog_up(struct net_device *dev)
{
        if (dev->netdev_ops->ndo_tx_timeout) {
                if (dev->watchdog_timeo <= 0)
                        dev->watchdog_timeo = 5*HZ;
                if (!mod_timer(&dev->watchdog_timer,
                               round_jiffies(jiffies + dev->watchdog_timeo)))
                        dev_hold(dev);
        }
}

static void dev_watchdog_up(struct net_device *dev)
{
        __netdev_watchdog_up(dev);
}

static void dev_watchdog_down(struct net_device *dev)
{
        netif_tx_lock_bh(dev);
        if (del_timer(&dev->watchdog_timer))
                dev_put(dev);
        netif_tx_unlock_bh(dev);
}

/**
 *      netif_carrier_on - set carrier
 *      @dev: network device
 *
 * Device has detected that carrier.
 */
void netif_carrier_on(struct net_device *dev)
{
        if (test_and_clear_bit(__LINK_STATE_NOCARRIER, &dev->state)) {
                if (dev->reg_state == NETREG_UNINITIALIZED)
                        return;
                atomic_inc(&dev->carrier_changes);
                linkwatch_fire_event(dev);
                if (netif_running(dev))
                        __netdev_watchdog_up(dev);
        }
}
EXPORT_SYMBOL(netif_carrier_on);

/**
 *      netif_carrier_off - clear carrier
 *      @dev: network device
 *
 * Device has detected loss of carrier.
 */
void netif_carrier_off(struct net_device *dev)
{
        if (!test_and_set_bit(__LINK_STATE_NOCARRIER, &dev->state)) {
                if (dev->reg_state == NETREG_UNINITIALIZED)
                        return;
                atomic_inc(&dev->carrier_changes);
                linkwatch_fire_event(dev);
        }
}
EXPORT_SYMBOL(netif_carrier_off);

/* "NOOP" scheduler: the best scheduler, recommended for all interfaces
   under all circumstances. It is difficult to invent anything faster or
   cheaper.
 */

static int noop_enqueue(struct sk_buff *skb, struct Qdisc *qdisc)
{
        kfree_skb(skb);
        return NET_XMIT_CN;
}

static struct sk_buff *noop_dequeue(struct Qdisc *qdisc)
{
        return NULL;
}

struct Qdisc_ops noop_qdisc_ops __read_mostly = {
        .id             =       "noop",
        .priv_size      =       0,
        .enqueue        =       noop_enqueue,
        .dequeue        =       noop_dequeue,
        .peek           =       noop_dequeue,
        .owner          =       THIS_MODULE,
};

static struct netdev_queue noop_netdev_queue = {
        .qdisc          =       &noop_qdisc,
        .qdisc_sleeping =       &noop_qdisc,
};

struct Qdisc noop_qdisc = {
        .enqueue        =       noop_enqueue,
        .dequeue        =       noop_dequeue,
        .flags          =       TCQ_F_BUILTIN,
        .ops            =       &noop_qdisc_ops,
        .list           =       LIST_HEAD_INIT(noop_qdisc.list),
        .q.lock         =       __SPIN_LOCK_UNLOCKED(noop_qdisc.q.lock),
        .dev_queue      =       &noop_netdev_queue,
        .busylock       =       __SPIN_LOCK_UNLOCKED(noop_qdisc.busylock),
};
EXPORT_SYMBOL(noop_qdisc);

static struct Qdisc_ops noqueue_qdisc_ops __read_mostly = {
        .id             =       "noqueue",
        .priv_size      =       0,
        .enqueue        =       noop_enqueue,
        .dequeue        =       noop_dequeue,
        .peek           =       noop_dequeue,
        .owner          =       THIS_MODULE,
};

static struct Qdisc noqueue_qdisc;
static struct netdev_queue noqueue_netdev_queue = {
        .qdisc          =       &noqueue_qdisc,
        .qdisc_sleeping =       &noqueue_qdisc,
};

static struct Qdisc noqueue_qdisc = {
        .enqueue        =       NULL,
        .dequeue        =       noop_dequeue,
        .flags          =       TCQ_F_BUILTIN,
        .ops            =       &noqueue_qdisc_ops,
        .list           =       LIST_HEAD_INIT(noqueue_qdisc.list),
        .q.lock         =       __SPIN_LOCK_UNLOCKED(noqueue_qdisc.q.lock),
        .dev_queue      =       &noqueue_netdev_queue,
        .busylock       =       __SPIN_LOCK_UNLOCKED(noqueue_qdisc.busylock),
};


static const u8 prio2band[TC_PRIO_MAX + 1] = {
        1, 2, 2, 2, 1, 2, 0, 0 , 1, 1, 1, 1, 1, 1, 1, 1
};

/* 3-band FIFO queue: old style, but should be a bit faster than
   generic prio+fifo combination.
 */

#define PFIFO_FAST_BANDS 3

/*
 * Private data for a pfifo_fast scheduler containing:
 *      - queues for the three band
 *      - bitmap indicating which of the bands contain skbs
 */
struct pfifo_fast_priv {
        u32 bitmap;
        struct sk_buff_head q[PFIFO_FAST_BANDS];
};

/*
 * Convert a bitmap to the first band number where an skb is queued, where:
 *      bitmap=0 means there are no skbs on any band.
 *      bitmap=1 means there is an skb on band 0.
 *      bitmap=7 means there are skbs on all 3 bands, etc.
 */
static const int bitmap2band[] = {-1, 0, 1, 0, 2, 0, 1, 0};

static inline struct sk_buff_head *band2list(struct pfifo_fast_priv *priv,
                                             int band)
{
        return priv->q + band;
}

static int pfifo_fast_enqueue(struct sk_buff *skb, struct Qdisc *qdisc)
{
        if (skb_queue_len(&qdisc->q) < qdisc_dev(qdisc)->tx_queue_len) {
                int band = prio2band[skb->priority & TC_PRIO_MAX];
                struct pfifo_fast_priv *priv = qdisc_priv(qdisc);
                struct sk_buff_head *list = band2list(priv, band);

                priv->bitmap |= (1 << band);
                qdisc->q.qlen++;
                return __qdisc_enqueue_tail(skb, qdisc, list);
        }

        return qdisc_drop(skb, qdisc);
}

static struct sk_buff *pfifo_fast_dequeue(struct Qdisc *qdisc)
{
        struct pfifo_fast_priv *priv = qdisc_priv(qdisc);
        int band = bitmap2band[priv->bitmap];

        if (likely(band >= 0)) {
                struct sk_buff_head *list = band2list(priv, band);
                struct sk_buff *skb = __qdisc_dequeue_head(qdisc, list);

                qdisc->q.qlen--;
                if (skb_queue_empty(list))
                        priv->bitmap &= ~(1 << band);

                return skb;
        }

        return NULL;
}

static struct sk_buff *pfifo_fast_peek(struct Qdisc *qdisc)
{
        struct pfifo_fast_priv *priv = qdisc_priv(qdisc);
        int band = bitmap2band[priv->bitmap];

        if (band >= 0) {
                struct sk_buff_head *list = band2list(priv, band);

                return skb_peek(list);
        }

        return NULL;
}

static void pfifo_fast_reset(struct Qdisc *qdisc)
{
        int prio;
        struct pfifo_fast_priv *priv = qdisc_priv(qdisc);

        for (prio = 0; prio < PFIFO_FAST_BANDS; prio++)
                __qdisc_reset_queue(qdisc, band2list(priv, prio));

        priv->bitmap = 0;
        qdisc->qstats.backlog = 0;
        qdisc->q.qlen = 0;
}

static int pfifo_fast_dump(struct Qdisc *qdisc, struct sk_buff *skb)
{
        struct tc_prio_qopt opt = { .bands = PFIFO_FAST_BANDS };

        memcpy(&opt.priomap, prio2band, TC_PRIO_MAX + 1);
        if (nla_put(skb, TCA_OPTIONS, sizeof(opt), &opt))
                goto nla_put_failure;
        return skb->len;

nla_put_failure:
        return -1;
}

static int pfifo_fast_init(struct Qdisc *qdisc, struct nlattr *opt)
{
        int prio;
        struct pfifo_fast_priv *priv = qdisc_priv(qdisc);

        for (prio = 0; prio < PFIFO_FAST_BANDS; prio++)
                __skb_queue_head_init(band2list(priv, prio));

        /* Can by-pass the queue discipline */
        qdisc->flags |= TCQ_F_CAN_BYPASS;
        return 0;
}

struct Qdisc_ops pfifo_fast_ops __read_mostly = {
        .id             =       "pfifo_fast",
        .priv_size      =       sizeof(struct pfifo_fast_priv),
        .enqueue        =       pfifo_fast_enqueue,
        .dequeue        =       pfifo_fast_dequeue,
        .peek           =       pfifo_fast_peek,
        .init           =       pfifo_fast_init,
        .reset          =       pfifo_fast_reset,
        .dump           =       pfifo_fast_dump,
        .owner          =       THIS_MODULE,
};

static struct lock_class_key qdisc_tx_busylock;

struct Qdisc *qdisc_alloc(struct netdev_queue *dev_queue,
                          const struct Qdisc_ops *ops)
{
        void *p;
        struct Qdisc *sch;
        unsigned int size = QDISC_ALIGN(sizeof(*sch)) + ops->priv_size;
        int err = -ENOBUFS;
        struct net_device *dev = dev_queue->dev;

        p = kzalloc_node(size, GFP_KERNEL,
                         netdev_queue_numa_node_read(dev_queue));

        if (!p)
                goto errout;
        sch = (struct Qdisc *) QDISC_ALIGN((unsigned long) p);
        /* if we got non aligned memory, ask more and do alignment ourself */
        if (sch != p) {
                kfree(p);
                p = kzalloc_node(size + QDISC_ALIGNTO - 1, GFP_KERNEL,
                                 netdev_queue_numa_node_read(dev_queue));
                if (!p)
                        goto errout;
                sch = (struct Qdisc *) QDISC_ALIGN((unsigned long) p);
                sch->padded = (char *) sch - (char *) p;
        }
        INIT_LIST_HEAD(&sch->list);
        skb_queue_head_init(&sch->q);

        spin_lock_init(&sch->busylock);
        lockdep_set_class(&sch->busylock,
                          dev->qdisc_tx_busylock ?: &qdisc_tx_busylock);

        sch->ops = ops;
        sch->enqueue = ops->enqueue;
        sch->dequeue = ops->dequeue;
        sch->dev_queue = dev_queue;
        dev_hold(dev);
        atomic_set(&sch->refcnt, 1);

        return sch;
errout:
        return ERR_PTR(err);
}

struct Qdisc *qdisc_create_dflt(struct netdev_queue *dev_queue,
                                const struct Qdisc_ops *ops,
                                unsigned int parentid)
{
        struct Qdisc *sch;

        if (!try_module_get(ops->owner))
                goto errout;

        sch = qdisc_alloc(dev_queue, ops);
        if (IS_ERR(sch))
                goto errout;
        sch->parent = parentid;

        if (!ops->init || ops->init(sch, NULL) == 0)
                return sch;

        qdisc_destroy(sch);
errout:
        return NULL;
}
EXPORT_SYMBOL(qdisc_create_dflt);

/* Under qdisc_lock(qdisc) and BH! */

void qdisc_reset(struct Qdisc *qdisc)
{
        const struct Qdisc_ops *ops = qdisc->ops;

        if (ops->reset)
                ops->reset(qdisc);

        if (qdisc->gso_skb) {
                kfree_skb_list(qdisc->gso_skb);
                qdisc->gso_skb = NULL;
                qdisc->q.qlen = 0;
        }
}
EXPORT_SYMBOL(qdisc_reset);

static void qdisc_rcu_free(struct rcu_head *head)
{
        struct Qdisc *qdisc = container_of(head, struct Qdisc, rcu_head);

        if (qdisc_is_percpu_stats(qdisc))
                free_percpu(qdisc->cpu_bstats);

        kfree((char *) qdisc - qdisc->padded);
}

void qdisc_destroy(struct Qdisc *qdisc)
{
        const struct Qdisc_ops  *ops = qdisc->ops;

        if (qdisc->flags & TCQ_F_BUILTIN ||
            !atomic_dec_and_test(&qdisc->refcnt))
                return;

#ifdef CONFIG_NET_SCHED
        qdisc_list_del(qdisc);

        qdisc_put_stab(rtnl_dereference(qdisc->stab));
#endif
        gen_kill_estimator(&qdisc->bstats, &qdisc->rate_est);
        if (ops->reset)
                ops->reset(qdisc);
        if (ops->destroy)
                ops->destroy(qdisc);

        module_put(ops->owner);
        dev_put(qdisc_dev(qdisc));

        kfree_skb_list(qdisc->gso_skb);
        /*
         * gen_estimator est_timer() might access qdisc->q.lock,
         * wait a RCU grace period before freeing qdisc.
         */
        call_rcu(&qdisc->rcu_head, qdisc_rcu_free);
}
EXPORT_SYMBOL(qdisc_destroy);

/* Attach toplevel qdisc to device queue. */
struct Qdisc *dev_graft_qdisc(struct netdev_queue *dev_queue,
                              struct Qdisc *qdisc)
{
        struct Qdisc *oqdisc = dev_queue->qdisc_sleeping;
        spinlock_t *root_lock;

        root_lock = qdisc_lock(oqdisc);
        spin_lock_bh(root_lock);

        /* Prune old scheduler */
        if (oqdisc && atomic_read(&oqdisc->refcnt) <= 1)
                qdisc_reset(oqdisc);

        /* ... and graft new one */
        if (qdisc == NULL)
                qdisc = &noop_qdisc;
        dev_queue->qdisc_sleeping = qdisc;
        rcu_assign_pointer(dev_queue->qdisc, &noop_qdisc);

        spin_unlock_bh(root_lock);

        return oqdisc;
}
EXPORT_SYMBOL(dev_graft_qdisc);

static void attach_one_default_qdisc(struct net_device *dev,
                                     struct netdev_queue *dev_queue,
                                     void *_unused)
{
        struct Qdisc *qdisc = &noqueue_qdisc;

        if (dev->tx_queue_len) {
                qdisc = qdisc_create_dflt(dev_queue,
                                          default_qdisc_ops, TC_H_ROOT);
                if (!qdisc) {
                        netdev_info(dev, "activation failed\n");
                        return;
                }
                if (!netif_is_multiqueue(dev))
                        qdisc->flags |= TCQ_F_ONETXQUEUE;
        }
        dev_queue->qdisc_sleeping = qdisc;
}

static void attach_default_qdiscs(struct net_device *dev)
{
        struct netdev_queue *txq;
        struct Qdisc *qdisc;

        txq = netdev_get_tx_queue(dev, 0);

        if (!netif_is_multiqueue(dev) || dev->tx_queue_len == 0) {
                netdev_for_each_tx_queue(dev, attach_one_default_qdisc, NULL);
                dev->qdisc = txq->qdisc_sleeping;
                atomic_inc(&dev->qdisc->refcnt);
        } else {
                qdisc = qdisc_create_dflt(txq, &mq_qdisc_ops, TC_H_ROOT);
                if (qdisc) {
                        dev->qdisc = qdisc;
                        qdisc->ops->attach(qdisc);
                }
        }
}

static void transition_one_qdisc(struct net_device *dev,
                                 struct netdev_queue *dev_queue,
                                 void *_need_watchdog)
{
        struct Qdisc *new_qdisc = dev_queue->qdisc_sleeping;
        int *need_watchdog_p = _need_watchdog;

        if (!(new_qdisc->flags & TCQ_F_BUILTIN))
                clear_bit(__QDISC_STATE_DEACTIVATED, &new_qdisc->state);

        rcu_assign_pointer(dev_queue->qdisc, new_qdisc);
        if (need_watchdog_p && new_qdisc != &noqueue_qdisc) {
                dev_queue->trans_start = 0;
                *need_watchdog_p = 1;
        }
}

void dev_activate(struct net_device *dev)
{
        int need_watchdog;

        /* No queueing discipline is attached to device;
         * create default one for devices, which need queueing
         * and noqueue_qdisc for virtual interfaces
         */

        if (dev->qdisc == &noop_qdisc)
                attach_default_qdiscs(dev);

        if (!netif_carrier_ok(dev))
                /* Delay activation until next carrier-on event */
                return;

        need_watchdog = 0;
        netdev_for_each_tx_queue(dev, transition_one_qdisc, &need_watchdog);
        if (dev_ingress_queue(dev))
                transition_one_qdisc(dev, dev_ingress_queue(dev), NULL);

        if (need_watchdog) {
                dev->trans_start = jiffies;
                dev_watchdog_up(dev);
        }
}
EXPORT_SYMBOL(dev_activate);

static void dev_deactivate_queue(struct net_device *dev,
                                 struct netdev_queue *dev_queue,
                                 void *_qdisc_default)
{
        struct Qdisc *qdisc_default = _qdisc_default;
        struct Qdisc *qdisc;

        qdisc = rtnl_dereference(dev_queue->qdisc);
        if (qdisc) {
                spin_lock_bh(qdisc_lock(qdisc));

                if (!(qdisc->flags & TCQ_F_BUILTIN))
                        set_bit(__QDISC_STATE_DEACTIVATED, &qdisc->state);

                rcu_assign_pointer(dev_queue->qdisc, qdisc_default);
                qdisc_reset(qdisc);

                spin_unlock_bh(qdisc_lock(qdisc));
        }
}

static bool some_qdisc_is_busy(struct net_device *dev)
{
        unsigned int i;

        for (i = 0; i < dev->num_tx_queues; i++) {
                struct netdev_queue *dev_queue;
                spinlock_t *root_lock;
                struct Qdisc *q;
                int val;

                dev_queue = netdev_get_tx_queue(dev, i);
                q = dev_queue->qdisc_sleeping;
                root_lock = qdisc_lock(q);

                spin_lock_bh(root_lock);

                val = (qdisc_is_running(q) ||
                       test_bit(__QDISC_STATE_SCHED, &q->state));

                spin_unlock_bh(root_lock);

                if (val)
                        return true;
        }
        return false;
}

/**
 *      dev_deactivate_many - deactivate transmissions on several devices
 *      @head: list of devices to deactivate
 *
 *      This function returns only when all outstanding transmissions
 *      have completed, unless all devices are in dismantle phase.
 */
void dev_deactivate_many(struct list_head *head)
{
        struct net_device *dev;
        bool sync_needed = false;

        list_for_each_entry(dev, head, close_list) {
                netdev_for_each_tx_queue(dev, dev_deactivate_queue,
                                         &noop_qdisc);
                if (dev_ingress_queue(dev))
                        dev_deactivate_queue(dev, dev_ingress_queue(dev),
                                             &noop_qdisc);

                dev_watchdog_down(dev);
                sync_needed |= !dev->dismantle;
        }

        /* Wait for outstanding qdisc-less dev_queue_xmit calls.
         * This is avoided if all devices are in dismantle phase :
         * Caller will call synchronize_net() for us
         */
        if (sync_needed)
                synchronize_net();

        /* Wait for outstanding qdisc_run calls. */
        list_for_each_entry(dev, head, close_list)
                while (some_qdisc_is_busy(dev))
                        yield();
}

void dev_deactivate(struct net_device *dev)
{
        LIST_HEAD(single);

        list_add(&dev->close_list, &single);
        dev_deactivate_many(&single);
        list_del(&single);
}
EXPORT_SYMBOL(dev_deactivate);

static void dev_init_scheduler_queue(struct net_device *dev,
                                     struct netdev_queue *dev_queue,
                                     void *_qdisc)
{
        struct Qdisc *qdisc = _qdisc;

        rcu_assign_pointer(dev_queue->qdisc, qdisc);
        dev_queue->qdisc_sleeping = qdisc;
}

void dev_init_scheduler(struct net_device *dev)
{
        dev->qdisc = &noop_qdisc;
        netdev_for_each_tx_queue(dev, dev_init_scheduler_queue, &noop_qdisc);
        if (dev_ingress_queue(dev))
                dev_init_scheduler_queue(dev, dev_ingress_queue(dev), &noop_qdisc);

        setup_timer(&dev->watchdog_timer, dev_watchdog, (unsigned long)dev);
}

static void shutdown_scheduler_queue(struct net_device *dev,
                                     struct netdev_queue *dev_queue,
                                     void *_qdisc_default)
{
        struct Qdisc *qdisc = dev_queue->qdisc_sleeping;
        struct Qdisc *qdisc_default = _qdisc_default;

        if (qdisc) {
                rcu_assign_pointer(dev_queue->qdisc, qdisc_default);
                dev_queue->qdisc_sleeping = qdisc_default;

                qdisc_destroy(qdisc);
        }
}

void dev_shutdown(struct net_device *dev)
{
        netdev_for_each_tx_queue(dev, shutdown_scheduler_queue, &noop_qdisc);
        if (dev_ingress_queue(dev))
                shutdown_scheduler_queue(dev, dev_ingress_queue(dev), &noop_qdisc);
        qdisc_destroy(dev->qdisc);
        dev->qdisc = &noop_qdisc;

        WARN_ON(timer_pending(&dev->watchdog_timer));
}

void psched_ratecfg_precompute(struct psched_ratecfg *r,
                               const struct tc_ratespec *conf,
                               u64 rate64)
{
        memset(r, 0, sizeof(*r));
        r->overhead = conf->overhead;
        r->rate_bytes_ps = max_t(u64, conf->rate, rate64);
        r->linklayer = (conf->linklayer & TC_LINKLAYER_MASK);
        r->mult = 1;
        /*
         * The deal here is to replace a divide by a reciprocal one
         * in fast path (a reciprocal divide is a multiply and a shift)
         *
         * Normal formula would be :
         *  time_in_ns = (NSEC_PER_SEC * len) / rate_bps
         *
         * We compute mult/shift to use instead :
         *  time_in_ns = (len * mult) >> shift;
         *
         * We try to get the highest possible mult value for accuracy,
         * but have to make sure no overflows will ever happen.
         */
        if (r->rate_bytes_ps > 0) {
                u64 factor = NSEC_PER_SEC;

                for (;;) {
                        r->mult = div64_u64(factor, r->rate_bytes_ps);
                        if (r->mult & (1U << 31) || factor & (1ULL << 63))
                                break;
                        factor <<= 1;
                        r->shift++;
                }
        }
}
EXPORT_SYMBOL(psched_ratecfg_precompute);

```

```
	Linux/include/net/sch_generic.h

#ifndef __NET_SCHED_GENERIC_H
#define __NET_SCHED_GENERIC_H

#include <linux/netdevice.h>
#include <linux/types.h>
#include <linux/rcupdate.h>
#include <linux/pkt_sched.h>
#include <linux/pkt_cls.h>
#include <linux/percpu.h>
#include <linux/dynamic_queue_limits.h>
#include <net/gen_stats.h>
#include <net/rtnetlink.h>

struct Qdisc_ops;
struct qdisc_walker;
struct tcf_walker;
struct module;

struct qdisc_rate_table {
        struct tc_ratespec rate;
        u32             data[256];
        struct qdisc_rate_table *next;
        int             refcnt;
};

enum qdisc_state_t {
        __QDISC_STATE_SCHED,
        __QDISC_STATE_DEACTIVATED,
        __QDISC_STATE_THROTTLED,
};

/*
 * following bits are only changed while qdisc lock is held
 */
enum qdisc___state_t {
        __QDISC___STATE_RUNNING = 1,
};

struct qdisc_size_table {
        struct rcu_head         rcu;
        struct list_head        list;
        struct tc_sizespec      szopts;
        int                     refcnt;
        u16                     data[];
};

struct Qdisc {
        int                     (*enqueue)(struct sk_buff *skb, struct Qdisc *dev);
        struct sk_buff *        (*dequeue)(struct Qdisc *dev);
        unsigned int            flags;
#define TCQ_F_BUILTIN           1
#define TCQ_F_INGRESS           2
#define TCQ_F_CAN_BYPASS        4
#define TCQ_F_MQROOT            8
#define TCQ_F_ONETXQUEUE        0x10 /* dequeue_skb() can assume all skbs are for
                                      * q->dev_queue : It can test
                                      * netif_xmit_frozen_or_stopped() before
                                      * dequeueing next packet.
                                      * Its true for MQ/MQPRIO slaves, or non
                                      * multiqueue device.
                                      */
#define TCQ_F_WARN_NONWC        (1 << 16)
#define TCQ_F_CPUSTATS          0x20 /* run using percpu statistics */
        u32                     limit;
        const struct Qdisc_ops  *ops;
        struct qdisc_size_table __rcu *stab;
        struct list_head        list;
        u32                     handle;
        u32                     parent;
        int                     (*reshape_fail)(struct sk_buff *skb,
                                        struct Qdisc *q);

        void                    *u32_node;

        /* This field is deprecated, but it is still used by CBQ
         * and it will live until better solution will be invented.
         */
        struct Qdisc            *__parent;
        struct netdev_queue     *dev_queue;

        struct gnet_stats_rate_est64    rate_est;
        struct gnet_stats_basic_cpu __percpu *cpu_bstats;
        struct gnet_stats_queue __percpu *cpu_qstats;

        struct Qdisc            *next_sched;
        struct sk_buff          *gso_skb;
        /*
         * For performance sake on SMP, we put highly modified fields at the end
         */
        unsigned long           state;
        struct sk_buff_head     q;
        struct gnet_stats_basic_packed bstats;
        unsigned int            __state;
        struct gnet_stats_queue qstats;
        struct rcu_head         rcu_head;
        int                     padded;
        atomic_t                refcnt;

        spinlock_t              busylock ____cacheline_aligned_in_smp;
};

static inline bool qdisc_is_running(const struct Qdisc *qdisc)
{
        return (qdisc->__state & __QDISC___STATE_RUNNING) ? true : false;
}

static inline bool qdisc_run_begin(struct Qdisc *qdisc)
{
        if (qdisc_is_running(qdisc))
                return false;
        qdisc->__state |= __QDISC___STATE_RUNNING;
        return true;
}

static inline void qdisc_run_end(struct Qdisc *qdisc)
{
        qdisc->__state &= ~__QDISC___STATE_RUNNING;
}

static inline bool qdisc_may_bulk(const struct Qdisc *qdisc)
{
        return qdisc->flags & TCQ_F_ONETXQUEUE;
}

static inline int qdisc_avail_bulklimit(const struct netdev_queue *txq)
{
#ifdef CONFIG_BQL
        /* Non-BQL migrated drivers will return 0, too. */
        return dql_avail(&txq->dql);
#else
        return 0;
#endif
}

static inline bool qdisc_is_throttled(const struct Qdisc *qdisc)
{
        return test_bit(__QDISC_STATE_THROTTLED, &qdisc->state) ? true : false;
}

static inline void qdisc_throttled(struct Qdisc *qdisc)
{
        set_bit(__QDISC_STATE_THROTTLED, &qdisc->state);
}

static inline void qdisc_unthrottled(struct Qdisc *qdisc)
{
        clear_bit(__QDISC_STATE_THROTTLED, &qdisc->state);
}

struct Qdisc_class_ops {
        /* Child qdisc manipulation */
        struct netdev_queue *   (*select_queue)(struct Qdisc *, struct tcmsg *);
        int                     (*graft)(struct Qdisc *, unsigned long cl,
                                        struct Qdisc *, struct Qdisc **);
        struct Qdisc *          (*leaf)(struct Qdisc *, unsigned long cl);
        void                    (*qlen_notify)(struct Qdisc *, unsigned long);

        /* Class manipulation routines */
        unsigned long           (*get)(struct Qdisc *, u32 classid);
        void                    (*put)(struct Qdisc *, unsigned long);
        int                     (*change)(struct Qdisc *, u32, u32,
                                        struct nlattr **, unsigned long *);
        int                     (*delete)(struct Qdisc *, unsigned long);
        void                    (*walk)(struct Qdisc *, struct qdisc_walker * arg);

        /* Filter manipulation */
        struct tcf_proto __rcu ** (*tcf_chain)(struct Qdisc *, unsigned long);
        unsigned long           (*bind_tcf)(struct Qdisc *, unsigned long,
                                        u32 classid);
        void                    (*unbind_tcf)(struct Qdisc *, unsigned long);

        /* rtnetlink specific */
        int                     (*dump)(struct Qdisc *, unsigned long,
                                        struct sk_buff *skb, struct tcmsg*);
        int                     (*dump_stats)(struct Qdisc *, unsigned long,
                                        struct gnet_dump *);
};

struct Qdisc_ops {
        struct Qdisc_ops        *next;
        const struct Qdisc_class_ops    *cl_ops;
        char                    id[IFNAMSIZ];
        int                     priv_size;

        int                     (*enqueue)(struct sk_buff *, struct Qdisc *);
        struct sk_buff *        (*dequeue)(struct Qdisc *);
        struct sk_buff *        (*peek)(struct Qdisc *);
        unsigned int            (*drop)(struct Qdisc *);

        int                     (*init)(struct Qdisc *, struct nlattr *arg);
        void                    (*reset)(struct Qdisc *);
        void                    (*destroy)(struct Qdisc *);
        int                     (*change)(struct Qdisc *, struct nlattr *arg);
        void                    (*attach)(struct Qdisc *);

        int                     (*dump)(struct Qdisc *, struct sk_buff *);
        int                     (*dump_stats)(struct Qdisc *, struct gnet_dump *);

        struct module           *owner;
};


struct tcf_result {
        unsigned long   class;
        u32             classid;
};

struct tcf_proto_ops {
        struct list_head        head;
        char                    kind[IFNAMSIZ];

        int                     (*classify)(struct sk_buff *,
                                            const struct tcf_proto *,
                                            struct tcf_result *);
        int                     (*init)(struct tcf_proto*);
        bool                    (*destroy)(struct tcf_proto*, bool);

        unsigned long           (*get)(struct tcf_proto*, u32 handle);
        int                     (*change)(struct net *net, struct sk_buff *,
                                        struct tcf_proto*, unsigned long,
                                        u32 handle, struct nlattr **,
                                        unsigned long *, bool);
        int                     (*delete)(struct tcf_proto*, unsigned long);
        void                    (*walk)(struct tcf_proto*, struct tcf_walker *arg);

        /* rtnetlink specific */
        int                     (*dump)(struct net*, struct tcf_proto*, unsigned long,
                                        struct sk_buff *skb, struct tcmsg*);

        struct module           *owner;
};

struct tcf_proto {
        /* Fast access part */
        struct tcf_proto __rcu  *next;
        void __rcu              *root;
        int                     (*classify)(struct sk_buff *,
                                            const struct tcf_proto *,
                                            struct tcf_result *);
        __be16                  protocol;

        /* All the rest */
        u32                     prio;
        u32                     classid;
        struct Qdisc            *q;
        void                    *data;
        const struct tcf_proto_ops      *ops;
        struct rcu_head         rcu;
};

struct qdisc_skb_cb {
        unsigned int            pkt_len;
        u16                     slave_dev_queue_mapping;
        u16                     _pad;
#define QDISC_CB_PRIV_LEN 20
        unsigned char           data[QDISC_CB_PRIV_LEN];
};

static inline void qdisc_cb_private_validate(const struct sk_buff *skb, int sz)
{
        struct qdisc_skb_cb *qcb;

        BUILD_BUG_ON(sizeof(skb->cb) < offsetof(struct qdisc_skb_cb, data) + sz);
        BUILD_BUG_ON(sizeof(qcb->data) < sz);
}

static inline int qdisc_qlen(const struct Qdisc *q)
{
        return q->q.qlen;
}

static inline struct qdisc_skb_cb *qdisc_skb_cb(const struct sk_buff *skb)
{
        return (struct qdisc_skb_cb *)skb->cb;
}

static inline spinlock_t *qdisc_lock(struct Qdisc *qdisc)
{
        return &qdisc->q.lock;
}

static inline struct Qdisc *qdisc_root(const struct Qdisc *qdisc)
{
        struct Qdisc *q = rcu_dereference_rtnl(qdisc->dev_queue->qdisc);

        return q;
}

static inline struct Qdisc *qdisc_root_sleeping(const struct Qdisc *qdisc)
{
        return qdisc->dev_queue->qdisc_sleeping;
}

/* The qdisc root lock is a mechanism by which to top level
 * of a qdisc tree can be locked from any qdisc node in the
 * forest.  This allows changing the configuration of some
 * aspect of the qdisc tree while blocking out asynchronous
 * qdisc access in the packet processing paths.
 *
 * It is only legal to do this when the root will not change
 * on us.  Otherwise we'll potentially lock the wrong qdisc
 * root.  This is enforced by holding the RTNL semaphore, which
 * all users of this lock accessor must do.
 */
static inline spinlock_t *qdisc_root_lock(const struct Qdisc *qdisc)
{
        struct Qdisc *root = qdisc_root(qdisc);

        ASSERT_RTNL();
        return qdisc_lock(root);
}

static inline spinlock_t *qdisc_root_sleeping_lock(const struct Qdisc *qdisc)
{
        struct Qdisc *root = qdisc_root_sleeping(qdisc);

        ASSERT_RTNL();
        return qdisc_lock(root);
}

static inline struct net_device *qdisc_dev(const struct Qdisc *qdisc)
{
        return qdisc->dev_queue->dev;
}

static inline void sch_tree_lock(const struct Qdisc *q)
{
        spin_lock_bh(qdisc_root_sleeping_lock(q));
}

static inline void sch_tree_unlock(const struct Qdisc *q)
{
        spin_unlock_bh(qdisc_root_sleeping_lock(q));
}

#define tcf_tree_lock(tp)       sch_tree_lock((tp)->q)
#define tcf_tree_unlock(tp)     sch_tree_unlock((tp)->q)

extern struct Qdisc noop_qdisc;
extern struct Qdisc_ops noop_qdisc_ops;
extern struct Qdisc_ops pfifo_fast_ops;
extern struct Qdisc_ops mq_qdisc_ops;
extern const struct Qdisc_ops *default_qdisc_ops;

struct Qdisc_class_common {
        u32                     classid;
        struct hlist_node       hnode;
};

struct Qdisc_class_hash {
        struct hlist_head       *hash;
        unsigned int            hashsize;
        unsigned int            hashmask;
        unsigned int            hashelems;
};

static inline unsigned int qdisc_class_hash(u32 id, u32 mask)
{
        id ^= id >> 8;
        id ^= id >> 4;
        return id & mask;
}

static inline struct Qdisc_class_common *
qdisc_class_find(const struct Qdisc_class_hash *hash, u32 id)
{
        struct Qdisc_class_common *cl;
        unsigned int h;

        h = qdisc_class_hash(id, hash->hashmask);
        hlist_for_each_entry(cl, &hash->hash[h], hnode) {
                if (cl->classid == id)
                        return cl;
        }
        return NULL;
}

int qdisc_class_hash_init(struct Qdisc_class_hash *);
void qdisc_class_hash_insert(struct Qdisc_class_hash *,
                             struct Qdisc_class_common *);
void qdisc_class_hash_remove(struct Qdisc_class_hash *,
                             struct Qdisc_class_common *);
void qdisc_class_hash_grow(struct Qdisc *, struct Qdisc_class_hash *);
void qdisc_class_hash_destroy(struct Qdisc_class_hash *);

void dev_init_scheduler(struct net_device *dev);
void dev_shutdown(struct net_device *dev);
void dev_activate(struct net_device *dev);
void dev_deactivate(struct net_device *dev);
void dev_deactivate_many(struct list_head *head);
struct Qdisc *dev_graft_qdisc(struct netdev_queue *dev_queue,
                              struct Qdisc *qdisc);
void qdisc_reset(struct Qdisc *qdisc);
void qdisc_destroy(struct Qdisc *qdisc);
void qdisc_tree_decrease_qlen(struct Qdisc *qdisc, unsigned int n);
struct Qdisc *qdisc_alloc(struct netdev_queue *dev_queue,
                          const struct Qdisc_ops *ops);
struct Qdisc *qdisc_create_dflt(struct netdev_queue *dev_queue,
                                const struct Qdisc_ops *ops, u32 parentid);
void __qdisc_calculate_pkt_len(struct sk_buff *skb,
                               const struct qdisc_size_table *stab);
bool tcf_destroy(struct tcf_proto *tp, bool force);
void tcf_destroy_chain(struct tcf_proto __rcu **fl);

/* Reset all TX qdiscs greater then index of a device.  */
static inline void qdisc_reset_all_tx_gt(struct net_device *dev, unsigned int i)
{
        struct Qdisc *qdisc;

        for (; i < dev->num_tx_queues; i++) {
                qdisc = rtnl_dereference(netdev_get_tx_queue(dev, i)->qdisc);
                if (qdisc) {
                        spin_lock_bh(qdisc_lock(qdisc));
                        qdisc_reset(qdisc);
                        spin_unlock_bh(qdisc_lock(qdisc));
                }
        }
}

static inline void qdisc_reset_all_tx(struct net_device *dev)
{
        qdisc_reset_all_tx_gt(dev, 0);
}

/* Are all TX queues of the device empty?  */
static inline bool qdisc_all_tx_empty(const struct net_device *dev)
{
        unsigned int i;

        rcu_read_lock();
        for (i = 0; i < dev->num_tx_queues; i++) {
                struct netdev_queue *txq = netdev_get_tx_queue(dev, i);
                const struct Qdisc *q = rcu_dereference(txq->qdisc);

                if (q->q.qlen) {
                        rcu_read_unlock();
                        return false;
                }
        }
        rcu_read_unlock();
        return true;
}

/* Are any of the TX qdiscs changing?  */
static inline bool qdisc_tx_changing(const struct net_device *dev)
{
        unsigned int i;

        for (i = 0; i < dev->num_tx_queues; i++) {
                struct netdev_queue *txq = netdev_get_tx_queue(dev, i);
                if (rcu_access_pointer(txq->qdisc) != txq->qdisc_sleeping)
                        return true;
        }
        return false;
}

/* Is the device using the noop qdisc on all queues?  */
static inline bool qdisc_tx_is_noop(const struct net_device *dev)
{
        unsigned int i;

        for (i = 0; i < dev->num_tx_queues; i++) {
                struct netdev_queue *txq = netdev_get_tx_queue(dev, i);
                if (rcu_access_pointer(txq->qdisc) != &noop_qdisc)
                        return false;
        }
        return true;
}

static inline unsigned int qdisc_pkt_len(const struct sk_buff *skb)
{
        return qdisc_skb_cb(skb)->pkt_len;
}

/* additional qdisc xmit flags (NET_XMIT_MASK in linux/netdevice.h) */
enum net_xmit_qdisc_t {
        __NET_XMIT_STOLEN = 0x00010000,
        __NET_XMIT_BYPASS = 0x00020000,
};

#ifdef CONFIG_NET_CLS_ACT
#define net_xmit_drop_count(e)  ((e) & __NET_XMIT_STOLEN ? 0 : 1)
#else
#define net_xmit_drop_count(e)  (1)
#endif

static inline void qdisc_calculate_pkt_len(struct sk_buff *skb,
                                           const struct Qdisc *sch)
{
#ifdef CONFIG_NET_SCHED
        struct qdisc_size_table *stab = rcu_dereference_bh(sch->stab);

        if (stab)
                __qdisc_calculate_pkt_len(skb, stab);
#endif
}

static inline int qdisc_enqueue(struct sk_buff *skb, struct Qdisc *sch)
{
        qdisc_calculate_pkt_len(skb, sch);
        return sch->enqueue(skb, sch);
}

static inline int qdisc_enqueue_root(struct sk_buff *skb, struct Qdisc *sch)
{
        qdisc_skb_cb(skb)->pkt_len = skb->len;
        return qdisc_enqueue(skb, sch) & NET_XMIT_MASK;
}

static inline bool qdisc_is_percpu_stats(const struct Qdisc *q)
{
        return q->flags & TCQ_F_CPUSTATS;
}

static inline void bstats_update(struct gnet_stats_basic_packed *bstats,
                                 const struct sk_buff *skb)
{
        bstats->bytes += qdisc_pkt_len(skb);
        bstats->packets += skb_is_gso(skb) ? skb_shinfo(skb)->gso_segs : 1;
}

static inline void qdisc_bstats_update_cpu(struct Qdisc *sch,
                                           const struct sk_buff *skb)
{
        struct gnet_stats_basic_cpu *bstats =
                                this_cpu_ptr(sch->cpu_bstats);

        u64_stats_update_begin(&bstats->syncp);
        bstats_update(&bstats->bstats, skb);
        u64_stats_update_end(&bstats->syncp);
}

static inline void qdisc_bstats_update(struct Qdisc *sch,
                                       const struct sk_buff *skb)
{
        bstats_update(&sch->bstats, skb);
}

static inline void qdisc_qstats_backlog_dec(struct Qdisc *sch,
                                            const struct sk_buff *skb)
{
        sch->qstats.backlog -= qdisc_pkt_len(skb);
}

static inline void qdisc_qstats_backlog_inc(struct Qdisc *sch,
                                            const struct sk_buff *skb)
{
        sch->qstats.backlog += qdisc_pkt_len(skb);
}

static inline void __qdisc_qstats_drop(struct Qdisc *sch, int count)
{
        sch->qstats.drops += count;
}

static inline void qdisc_qstats_drop(struct Qdisc *sch)
{
        sch->qstats.drops++;
}

static inline void qdisc_qstats_drop_cpu(struct Qdisc *sch)
{
        struct gnet_stats_queue *qstats = this_cpu_ptr(sch->cpu_qstats);

        qstats->drops++;
}

static inline void qdisc_qstats_overlimit(struct Qdisc *sch)
{
        sch->qstats.overlimits++;
}

static inline int __qdisc_enqueue_tail(struct sk_buff *skb, struct Qdisc *sch,
                                       struct sk_buff_head *list)
{
        __skb_queue_tail(list, skb);
        qdisc_qstats_backlog_inc(sch, skb);

        return NET_XMIT_SUCCESS;
}

static inline int qdisc_enqueue_tail(struct sk_buff *skb, struct Qdisc *sch)
{
        return __qdisc_enqueue_tail(skb, sch, &sch->q);
}

static inline struct sk_buff *__qdisc_dequeue_head(struct Qdisc *sch,
                                                   struct sk_buff_head *list)
{
        struct sk_buff *skb = __skb_dequeue(list);

        if (likely(skb != NULL)) {
                qdisc_qstats_backlog_dec(sch, skb);
                qdisc_bstats_update(sch, skb);
        }

        return skb;
}

static inline struct sk_buff *qdisc_dequeue_head(struct Qdisc *sch)
{
        return __qdisc_dequeue_head(sch, &sch->q);
}

static inline unsigned int __qdisc_queue_drop_head(struct Qdisc *sch,
                                              struct sk_buff_head *list)
{
        struct sk_buff *skb = __skb_dequeue(list);

        if (likely(skb != NULL)) {
                unsigned int len = qdisc_pkt_len(skb);
                qdisc_qstats_backlog_dec(sch, skb);
                kfree_skb(skb);
                return len;
        }

        return 0;
}

static inline unsigned int qdisc_queue_drop_head(struct Qdisc *sch)
{
        return __qdisc_queue_drop_head(sch, &sch->q);
}

static inline struct sk_buff *__qdisc_dequeue_tail(struct Qdisc *sch,
                                                   struct sk_buff_head *list)
{
        struct sk_buff *skb = __skb_dequeue_tail(list);

        if (likely(skb != NULL))
                qdisc_qstats_backlog_dec(sch, skb);

        return skb;
}

static inline struct sk_buff *qdisc_dequeue_tail(struct Qdisc *sch)
{
        return __qdisc_dequeue_tail(sch, &sch->q);
}

static inline struct sk_buff *qdisc_peek_head(struct Qdisc *sch)
{
        return skb_peek(&sch->q);
}

/* generic pseudo peek method for non-work-conserving qdisc */
static inline struct sk_buff *qdisc_peek_dequeued(struct Qdisc *sch)
{
        /* we can reuse ->gso_skb because peek isn't called for root qdiscs */
        if (!sch->gso_skb) {
                sch->gso_skb = sch->dequeue(sch);
                if (sch->gso_skb)
                        /* it's still part of the queue */
                        sch->q.qlen++;
        }

        return sch->gso_skb;
}

/* use instead of qdisc->dequeue() for all qdiscs queried with ->peek() */
static inline struct sk_buff *qdisc_dequeue_peeked(struct Qdisc *sch)
{
        struct sk_buff *skb = sch->gso_skb;

        if (skb) {
                sch->gso_skb = NULL;
                sch->q.qlen--;
        } else {
                skb = sch->dequeue(sch);
        }

        return skb;
}

static inline void __qdisc_reset_queue(struct Qdisc *sch,
                                       struct sk_buff_head *list)
{
        /*
         * We do not know the backlog in bytes of this list, it
         * is up to the caller to correct it
         */
        __skb_queue_purge(list);
}

static inline void qdisc_reset_queue(struct Qdisc *sch)
{
        __qdisc_reset_queue(sch, &sch->q);
        sch->qstats.backlog = 0;
}

static inline unsigned int __qdisc_queue_drop(struct Qdisc *sch,
                                              struct sk_buff_head *list)
{
        struct sk_buff *skb = __qdisc_dequeue_tail(sch, list);

        if (likely(skb != NULL)) {
                unsigned int len = qdisc_pkt_len(skb);
                kfree_skb(skb);
                return len;
        }

        return 0;
}

static inline unsigned int qdisc_queue_drop(struct Qdisc *sch)
{
        return __qdisc_queue_drop(sch, &sch->q);
}

static inline int qdisc_drop(struct sk_buff *skb, struct Qdisc *sch)
{
        kfree_skb(skb);
        qdisc_qstats_drop(sch);

        return NET_XMIT_DROP;
}

static inline int qdisc_reshape_fail(struct sk_buff *skb, struct Qdisc *sch)
{
        qdisc_qstats_drop(sch);

#ifdef CONFIG_NET_CLS_ACT
        if (sch->reshape_fail == NULL || sch->reshape_fail(skb, sch))
                goto drop;

        return NET_XMIT_SUCCESS;

drop:
#endif
        kfree_skb(skb);
        return NET_XMIT_DROP;
}

/* Length to Time (L2T) lookup in a qdisc_rate_table, to determine how
   long it will take to send a packet given its size.
 */
static inline u32 qdisc_l2t(struct qdisc_rate_table* rtab, unsigned int pktlen)
{
        int slot = pktlen + rtab->rate.cell_align + rtab->rate.overhead;
        if (slot < 0)
                slot = 0;
        slot >>= rtab->rate.cell_log;
        if (slot > 255)
                return rtab->data[255]*(slot >> 8) + rtab->data[slot & 0xFF];
        return rtab->data[slot];
}

#ifdef CONFIG_NET_CLS_ACT
static inline struct sk_buff *skb_act_clone(struct sk_buff *skb, gfp_t gfp_mask,
                                            int action)
{
        struct sk_buff *n;

        n = skb_clone(skb, gfp_mask);

        if (n) {
                n->tc_verd = SET_TC_VERD(n->tc_verd, 0);
                n->tc_verd = CLR_TC_OK2MUNGE(n->tc_verd);
                n->tc_verd = CLR_TC_MUNGED(n->tc_verd);
        }
        return n;
}
#endif

struct psched_ratecfg {
        u64     rate_bytes_ps; /* bytes per second */
        u32     mult;
        u16     overhead;
        u8      linklayer;
        u8      shift;
};

static inline u64 psched_l2t_ns(const struct psched_ratecfg *r,
                                unsigned int len)
{
        len += r->overhead;

        if (unlikely(r->linklayer == TC_LINKLAYER_ATM))
                return ((u64)(DIV_ROUND_UP(len,48)*53) * r->mult) >> r->shift;

        return ((u64)len * r->mult) >> r->shift;
}

void psched_ratecfg_precompute(struct psched_ratecfg *r,
                               const struct tc_ratespec *conf,
                               u64 rate64);

static inline void psched_ratecfg_getrate(struct tc_ratespec *res,
                                          const struct psched_ratecfg *r)
{
        memset(res, 0, sizeof(*res));

        /* legacy struct tc_ratespec has a 32bit @rate field
         * Qdisc using 64bit rate should add new attributes
         * in order to maintain compatibility.
         */
        res->rate = min_t(u64, r->rate_bytes_ps, ~0U);

        res->overhead = r->overhead;
        res->linklayer = (r->linklayer & TC_LINKLAYER_MASK);
}

#endif

```
