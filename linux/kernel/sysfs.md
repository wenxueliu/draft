

##附录

``` 
/*
 * fs/sysfs/symlink.c - operations for initializing and mounting sysfs
 *
 * Copyright (c) 2001-3 Patrick Mochel
 * Copyright (c) 2007 SUSE Linux Products GmbH
 * Copyright (c) 2007 Tejun Heo <teheo@suse.de>
 *
 * This file is released under the GPLv2.
 *
 * Please see Documentation/filesystems/sysfs.txt for more information.
 */

#define DEBUG

#include <linux/fs.h>
#include <linux/magic.h>
#include <linux/mount.h>
#include <linux/init.h>
#include <linux/user_namespace.h>

#include "sysfs.h"

static struct kernfs_root *sysfs_root;
struct kernfs_node *sysfs_root_kn;

static struct dentry *sysfs_mount(struct file_system_type *fs_type,
        int flags, const char *dev_name, void *data)
{
        struct dentry *root;
        void *ns;
        bool new_sb;

        if (!(flags & MS_KERNMOUNT)) {
                if (!capable(CAP_SYS_ADMIN) && !fs_fully_visible(fs_type))
                        return ERR_PTR(-EPERM);

                if (!kobj_ns_current_may_mount(KOBJ_NS_TYPE_NET))
                        return ERR_PTR(-EPERM);
        }

        ns = kobj_ns_grab_current(KOBJ_NS_TYPE_NET);
        root = kernfs_mount_ns(fs_type, flags, sysfs_root,
                                SYSFS_MAGIC, &new_sb, ns);
        if (IS_ERR(root) || !new_sb)
                kobj_ns_drop(KOBJ_NS_TYPE_NET, ns);
        return root;
}

static void sysfs_kill_sb(struct super_block *sb)
{
        void *ns = (void *)kernfs_super_ns(sb);

        kernfs_kill_sb(sb);
        kobj_ns_drop(KOBJ_NS_TYPE_NET, ns);
}

static struct file_system_type sysfs_fs_type = {
        .name           = "sysfs",
        .mount          = sysfs_mount,
        .kill_sb        = sysfs_kill_sb,
        .fs_flags       = FS_USERNS_MOUNT,
};

int __init sysfs_init(void)
{
        int err;

        sysfs_root = kernfs_create_root(NULL, KERNFS_ROOT_EXTRA_OPEN_PERM_CHECK,
                                        NULL);
        if (IS_ERR(sysfs_root))
                return PTR_ERR(sysfs_root);

        sysfs_root_kn = sysfs_root->kn;

        err = register_filesystem(&sysfs_fs_type);
        if (err) {
                kernfs_destroy_root(sysfs_root);
                return err;
        }

        return 0;
}

```

```
/*
 * sysfs.h - definitions for the device driver filesystem
 *
 * Copyright (c) 2001,2002 Patrick Mochel
 * Copyright (c) 2004 Silicon Graphics, Inc.
 * Copyright (c) 2007 SUSE Linux Products GmbH
 * Copyright (c) 2007 Tejun Heo <teheo@suse.de>
 *
 * Please see Documentation/filesystems/sysfs.txt for more information.
 */

#ifndef _SYSFS_H_
#define _SYSFS_H_

#include <linux/kernfs.h>
#include <linux/compiler.h>
#include <linux/errno.h>
#include <linux/list.h>
#include <linux/lockdep.h>
#include <linux/kobject_ns.h>
#include <linux/stat.h>
#include <linux/atomic.h>

struct kobject;
struct module;
struct bin_attribute;
enum kobj_ns_type;

struct attribute {
        const char              *name;
        umode_t                 mode;
#ifdef CONFIG_DEBUG_LOCK_ALLOC
        bool                    ignore_lockdep:1;
        struct lock_class_key   *key;
        struct lock_class_key   skey;
#endif
};

/**
 *      sysfs_attr_init - initialize a dynamically allocated sysfs attribute
 *      @attr: struct attribute to initialize
 *
 *      Initialize a dynamically allocated struct attribute so we can
 *      make lockdep happy.  This is a new requirement for attributes
 *      and initially this is only needed when lockdep is enabled.
 *      Lockdep gives a nice error when your attribute is added to
 *      sysfs if you don't have this.
 */
#ifdef CONFIG_DEBUG_LOCK_ALLOC
#define sysfs_attr_init(attr)                           \
do {                                                    \
        static struct lock_class_key __key;             \
                                                        \
        (attr)->key = &__key;                           \
} while (0)
#else
#define sysfs_attr_init(attr) do {} while (0)
#endif

/**
 * struct attribute_group - data structure used to declare an attribute group.
 * @name:       Optional: Attribute group name
 *              If specified, the attribute group will be created in
 *              a new subdirectory with this name.
 * @is_visible: Optional: Function to return permissions associated with an
 *              attribute of the group. Will be called repeatedly for each
 *              attribute in the group. Only read/write permissions as well as
 *              SYSFS_PREALLOC are accepted. Must return 0 if an attribute is
 *              not visible. The returned value will replace static permissions
 *              defined in struct attribute or struct bin_attribute.
 * @attrs:      Pointer to NULL terminated list of attributes.
 * @bin_attrs:  Pointer to NULL terminated list of binary attributes.
 *              Either attrs or bin_attrs or both must be provided.
 */
struct attribute_group {
        const char              *name;
        umode_t                 (*is_visible)(struct kobject *,
                                              struct attribute *, int);
        struct attribute        **attrs;
        struct bin_attribute    **bin_attrs;
};

/**
 * Use these macros to make defining attributes easier. See include/linux/device.h
 * for examples..
 */

#define SYSFS_PREALLOC 010000

#define __ATTR(_name, _mode, _show, _store) {                           \
        .attr = {.name = __stringify(_name),                            \
                 .mode = VERIFY_OCTAL_PERMISSIONS(_mode) },             \
        .show   = _show,                                                \
        .store  = _store,                                               \
}

#define __ATTR_PREALLOC(_name, _mode, _show, _store) {                  \
        .attr = {.name = __stringify(_name),                            \
                 .mode = SYSFS_PREALLOC | VERIFY_OCTAL_PERMISSIONS(_mode) },\
        .show   = _show,                                                \
        .store  = _store,                                               \
}

#define __ATTR_RO(_name) {                                              \
        .attr   = { .name = __stringify(_name), .mode = S_IRUGO },      \
        .show   = _name##_show,                                         \
}

#define __ATTR_WO(_name) {                                              \
        .attr   = { .name = __stringify(_name), .mode = S_IWUSR },      \
        .store  = _name##_store,                                        \
}

#define __ATTR_RW(_name) __ATTR(_name, (S_IWUSR | S_IRUGO),             \
                         _name##_show, _name##_store)

#define __ATTR_NULL { .attr = { .name = NULL } }

#ifdef CONFIG_DEBUG_LOCK_ALLOC
#define __ATTR_IGNORE_LOCKDEP(_name, _mode, _show, _store) {    \
        .attr = {.name = __stringify(_name), .mode = _mode,     \
                        .ignore_lockdep = true },               \
        .show           = _show,                                \
        .store          = _store,                               \
}
#else
#define __ATTR_IGNORE_LOCKDEP   __ATTR
#endif

#define __ATTRIBUTE_GROUPS(_name)                               \
static const struct attribute_group *_name##_groups[] = {       \
        &_name##_group,                                         \
        NULL,                                                   \
}

#define ATTRIBUTE_GROUPS(_name)                                 \
static const struct attribute_group _name##_group = {           \
        .attrs = _name##_attrs,                                 \
};                                                              \
__ATTRIBUTE_GROUPS(_name)

struct file;
struct vm_area_struct;

struct bin_attribute {
        struct attribute        attr;
        size_t                  size;
        void                    *private;
        ssize_t (*read)(struct file *, struct kobject *, struct bin_attribute *,
                        char *, loff_t, size_t);
        ssize_t (*write)(struct file *, struct kobject *, struct bin_attribute *,
                         char *, loff_t, size_t);
        int (*mmap)(struct file *, struct kobject *, struct bin_attribute *attr,
                    struct vm_area_struct *vma);
};

/**
 *      sysfs_bin_attr_init - initialize a dynamically allocated bin_attribute
 *      @attr: struct bin_attribute to initialize
 *
 *      Initialize a dynamically allocated struct bin_attribute so we
 *      can make lockdep happy.  This is a new requirement for
 *      attributes and initially this is only needed when lockdep is
 *      enabled.  Lockdep gives a nice error when your attribute is
 *      added to sysfs if you don't have this.
 */
#define sysfs_bin_attr_init(bin_attr) sysfs_attr_init(&(bin_attr)->attr)

/* macros to create static binary attributes easier */
#define __BIN_ATTR(_name, _mode, _read, _write, _size) {                \
        .attr = { .name = __stringify(_name), .mode = _mode },          \
        .read   = _read,                                                \
        .write  = _write,                                               \
        .size   = _size,                                                \
}

#define __BIN_ATTR_RO(_name, _size) {                                   \
        .attr   = { .name = __stringify(_name), .mode = S_IRUGO },      \
        .read   = _name##_read,                                         \
        .size   = _size,                                                \
}

#define __BIN_ATTR_RW(_name, _size) __BIN_ATTR(_name,                   \
                                   (S_IWUSR | S_IRUGO), _name##_read,   \
                                   _name##_write, _size)

#define __BIN_ATTR_NULL __ATTR_NULL

#define BIN_ATTR(_name, _mode, _read, _write, _size)                    \
struct bin_attribute bin_attr_##_name = __BIN_ATTR(_name, _mode, _read, \
                                        _write, _size)

#define BIN_ATTR_RO(_name, _size)                                       \
struct bin_attribute bin_attr_##_name = __BIN_ATTR_RO(_name, _size)

#define BIN_ATTR_RW(_name, _size)                                       \
struct bin_attribute bin_attr_##_name = __BIN_ATTR_RW(_name, _size)

struct sysfs_ops {
        ssize_t (*show)(struct kobject *, struct attribute *, char *);
        ssize_t (*store)(struct kobject *, struct attribute *, const char *, size_t);
};

#ifdef CONFIG_SYSFS

int __must_check sysfs_create_dir_ns(struct kobject *kobj, const void *ns);
void sysfs_remove_dir(struct kobject *kobj);
int __must_check sysfs_rename_dir_ns(struct kobject *kobj, const char *new_name,
                                     const void *new_ns);
int __must_check sysfs_move_dir_ns(struct kobject *kobj,
                                   struct kobject *new_parent_kobj,
                                   const void *new_ns);

int __must_check sysfs_create_file_ns(struct kobject *kobj,
                                      const struct attribute *attr,
                                      const void *ns);
int __must_check sysfs_create_files(struct kobject *kobj,
                                   const struct attribute **attr);
int __must_check sysfs_chmod_file(struct kobject *kobj,
                                  const struct attribute *attr, umode_t mode);
void sysfs_remove_file_ns(struct kobject *kobj, const struct attribute *attr,
                          const void *ns);
bool sysfs_remove_file_self(struct kobject *kobj, const struct attribute *attr);
void sysfs_remove_files(struct kobject *kobj, const struct attribute **attr);

int __must_check sysfs_create_bin_file(struct kobject *kobj,
                                       const struct bin_attribute *attr);
void sysfs_remove_bin_file(struct kobject *kobj,
                           const struct bin_attribute *attr);

int __must_check sysfs_create_link(struct kobject *kobj, struct kobject *target,
                                   const char *name);
int __must_check sysfs_create_link_nowarn(struct kobject *kobj,
                                          struct kobject *target,
                                          const char *name);
void sysfs_remove_link(struct kobject *kobj, const char *name);

int sysfs_rename_link_ns(struct kobject *kobj, struct kobject *target,
                         const char *old_name, const char *new_name,
                         const void *new_ns);

void sysfs_delete_link(struct kobject *dir, struct kobject *targ,
                        const char *name);

int __must_check sysfs_create_group(struct kobject *kobj,
                                    const struct attribute_group *grp);
int __must_check sysfs_create_groups(struct kobject *kobj,
                                     const struct attribute_group **groups);
int sysfs_update_group(struct kobject *kobj,
                       const struct attribute_group *grp);
void sysfs_remove_group(struct kobject *kobj,
                        const struct attribute_group *grp);
void sysfs_remove_groups(struct kobject *kobj,
                         const struct attribute_group **groups);
int sysfs_add_file_to_group(struct kobject *kobj,
                        const struct attribute *attr, const char *group);
void sysfs_remove_file_from_group(struct kobject *kobj,
                        const struct attribute *attr, const char *group);
int sysfs_merge_group(struct kobject *kobj,
                       const struct attribute_group *grp);
void sysfs_unmerge_group(struct kobject *kobj,
                       const struct attribute_group *grp);
int sysfs_add_link_to_group(struct kobject *kobj, const char *group_name,
                            struct kobject *target, const char *link_name);
void sysfs_remove_link_from_group(struct kobject *kobj, const char *group_name,
                                  const char *link_name);

void sysfs_notify(struct kobject *kobj, const char *dir, const char *attr);

int __must_check sysfs_init(void);

static inline void sysfs_enable_ns(struct kernfs_node *kn)
{
        return kernfs_enable_ns(kn);
}

#else /* CONFIG_SYSFS */

static inline int sysfs_create_dir_ns(struct kobject *kobj, const void *ns)
{
        return 0;
}

static inline void sysfs_remove_dir(struct kobject *kobj)
{
}

static inline int sysfs_rename_dir_ns(struct kobject *kobj,
                                      const char *new_name, const void *new_ns)
{
        return 0;
}

static inline int sysfs_move_dir_ns(struct kobject *kobj,
                                    struct kobject *new_parent_kobj,
                                    const void *new_ns)
{
        return 0;
}

static inline int sysfs_create_file_ns(struct kobject *kobj,
                                       const struct attribute *attr,
                                       const void *ns)
{
        return 0;
}

static inline int sysfs_create_files(struct kobject *kobj,
                                    const struct attribute **attr)
{
        return 0;
}

static inline int sysfs_chmod_file(struct kobject *kobj,
                                   const struct attribute *attr, umode_t mode)
{
        return 0;
}

static inline void sysfs_remove_file_ns(struct kobject *kobj,
                                        const struct attribute *attr,
                                        const void *ns)
{
}

static inline bool sysfs_remove_file_self(struct kobject *kobj,
                                          const struct attribute *attr)
{
        return false;
}

static inline void sysfs_remove_files(struct kobject *kobj,
                                     const struct attribute **attr)
{
}

static inline int sysfs_create_bin_file(struct kobject *kobj,
                                        const struct bin_attribute *attr)
{
        return 0;
}

static inline void sysfs_remove_bin_file(struct kobject *kobj,
                                         const struct bin_attribute *attr)
{
}

static inline int sysfs_create_link(struct kobject *kobj,
                                    struct kobject *target, const char *name)
{
        return 0;
}

static inline int sysfs_create_link_nowarn(struct kobject *kobj,
                                           struct kobject *target,
                                           const char *name)
{
        return 0;
}

static inline void sysfs_remove_link(struct kobject *kobj, const char *name)
{
}

static inline int sysfs_rename_link_ns(struct kobject *k, struct kobject *t,
                                       const char *old_name,
                                       const char *new_name, const void *ns)
{
        return 0;
}

static inline void sysfs_delete_link(struct kobject *k, struct kobject *t,
                                     const char *name)
{
}

static inline int sysfs_create_group(struct kobject *kobj,
                                     const struct attribute_group *grp)
{
        return 0;
}

static inline int sysfs_create_groups(struct kobject *kobj,
                                      const struct attribute_group **groups)
{
        return 0;
}

static inline int sysfs_update_group(struct kobject *kobj,
                                const struct attribute_group *grp)
{
        return 0;
}

static inline void sysfs_remove_group(struct kobject *kobj,
                                      const struct attribute_group *grp)
{
}

static inline void sysfs_remove_groups(struct kobject *kobj,
                                       const struct attribute_group **groups)
{
}

static inline int sysfs_add_file_to_group(struct kobject *kobj,
                const struct attribute *attr, const char *group)
{
        return 0;
}

static inline void sysfs_remove_file_from_group(struct kobject *kobj,
                const struct attribute *attr, const char *group)
{
}

static inline int sysfs_merge_group(struct kobject *kobj,
                       const struct attribute_group *grp)
{
        return 0;
}

static inline void sysfs_unmerge_group(struct kobject *kobj,
                       const struct attribute_group *grp)
{
}

static inline int sysfs_add_link_to_group(struct kobject *kobj,
                const char *group_name, struct kobject *target,
                const char *link_name)
{
        return 0;
}

static inline void sysfs_remove_link_from_group(struct kobject *kobj,
                const char *group_name, const char *link_name)
{
}

static inline void sysfs_notify(struct kobject *kobj, const char *dir,
                                const char *attr)
{
}

static inline int __must_check sysfs_init(void)
{
        return 0;
}

static inline void sysfs_enable_ns(struct kernfs_node *kn)
{
}

#endif /* CONFIG_SYSFS */

static inline int __must_check sysfs_create_file(struct kobject *kobj,
                                                 const struct attribute *attr)
{
        return sysfs_create_file_ns(kobj, attr, NULL);
}

static inline void sysfs_remove_file(struct kobject *kobj,
                                     const struct attribute *attr)
{
        sysfs_remove_file_ns(kobj, attr, NULL);
}

static inline int sysfs_rename_link(struct kobject *kobj, struct kobject *target,
                                    const char *old_name, const char *new_name)
{
        return sysfs_rename_link_ns(kobj, target, old_name, new_name, NULL);
}

static inline void sysfs_notify_dirent(struct kernfs_node *kn)
{
        kernfs_notify(kn);
}

static inline struct kernfs_node *sysfs_get_dirent(struct kernfs_node *parent,
                                                   const unsigned char *name)
{
        return kernfs_find_and_get(parent, name);
}

static inline struct kernfs_node *sysfs_get(struct kernfs_node *kn)
{
        kernfs_get(kn);
        return kn;
}

static inline void sysfs_put(struct kernfs_node *kn)
{
        kernfs_put(kn);
}

#endif /* _SYSFS_H_ */

```

```
/*
 * bus.c - bus driver management
 *
 * Copyright (c) 2002-3 Patrick Mochel
 * Copyright (c) 2002-3 Open Source Development Labs
 * Copyright (c) 2007 Greg Kroah-Hartman <gregkh@suse.de>
 * Copyright (c) 2007 Novell Inc.
 *
 * This file is released under the GPLv2
 *
 */

#include <linux/device.h>
#include <linux/module.h>
#include <linux/errno.h>
#include <linux/slab.h>
#include <linux/init.h>
#include <linux/string.h>
#include <linux/mutex.h>
#include <linux/sysfs.h>
#include "base.h"
#include "power/power.h"

/* /sys/devices/system */
static struct kset *system_kset;

#define to_bus_attr(_attr) container_of(_attr, struct bus_attribute, attr)

/*
 * sysfs bindings for drivers
 */

#define to_drv_attr(_attr) container_of(_attr, struct driver_attribute, attr)


static int __must_check bus_rescan_devices_helper(struct device *dev,
                                                void *data);

static struct bus_type *bus_get(struct bus_type *bus)
{
        if (bus) {
                kset_get(&bus->p->subsys);
                return bus;
        }
        return NULL;
}

static void bus_put(struct bus_type *bus)
{
        if (bus)
                kset_put(&bus->p->subsys);
}

static ssize_t drv_attr_show(struct kobject *kobj, struct attribute *attr,
                             char *buf)
{
        struct driver_attribute *drv_attr = to_drv_attr(attr);
        struct driver_private *drv_priv = to_driver(kobj);
        ssize_t ret = -EIO;

        if (drv_attr->show)
                ret = drv_attr->show(drv_priv->driver, buf);
        return ret;
}

static ssize_t drv_attr_store(struct kobject *kobj, struct attribute *attr,
                              const char *buf, size_t count)
{
        struct driver_attribute *drv_attr = to_drv_attr(attr);
        struct driver_private *drv_priv = to_driver(kobj);
        ssize_t ret = -EIO;

        if (drv_attr->store)
                ret = drv_attr->store(drv_priv->driver, buf, count);
        return ret;
}

static const struct sysfs_ops driver_sysfs_ops = {
        .show   = drv_attr_show,
        .store  = drv_attr_store,
};

static void driver_release(struct kobject *kobj)
{
        struct driver_private *drv_priv = to_driver(kobj);

        pr_debug("driver: '%s': %s\n", kobject_name(kobj), __func__);
        kfree(drv_priv);
}

static struct kobj_type driver_ktype = {
        .sysfs_ops      = &driver_sysfs_ops,
        .release        = driver_release,
};

/*
 * sysfs bindings for buses
 */
static ssize_t bus_attr_show(struct kobject *kobj, struct attribute *attr,
                             char *buf)
{
        struct bus_attribute *bus_attr = to_bus_attr(attr);
        struct subsys_private *subsys_priv = to_subsys_private(kobj);
        ssize_t ret = 0;

        if (bus_attr->show)
                ret = bus_attr->show(subsys_priv->bus, buf);
        return ret;
}

static ssize_t bus_attr_store(struct kobject *kobj, struct attribute *attr,
                              const char *buf, size_t count)
{
        struct bus_attribute *bus_attr = to_bus_attr(attr);
        struct subsys_private *subsys_priv = to_subsys_private(kobj);
        ssize_t ret = 0;

        if (bus_attr->store)
                ret = bus_attr->store(subsys_priv->bus, buf, count);
        return ret;
}

static const struct sysfs_ops bus_sysfs_ops = {
        .show   = bus_attr_show,
        .store  = bus_attr_store,
};

int bus_create_file(struct bus_type *bus, struct bus_attribute *attr)
{
        int error;
        if (bus_get(bus)) {
                error = sysfs_create_file(&bus->p->subsys.kobj, &attr->attr);
                bus_put(bus);
        } else
                error = -EINVAL;
        return error;
}
EXPORT_SYMBOL_GPL(bus_create_file);

void bus_remove_file(struct bus_type *bus, struct bus_attribute *attr)
{
        if (bus_get(bus)) {
                sysfs_remove_file(&bus->p->subsys.kobj, &attr->attr);
                bus_put(bus);
        }
}
EXPORT_SYMBOL_GPL(bus_remove_file);

static void bus_release(struct kobject *kobj)
{
        struct subsys_private *priv =
                container_of(kobj, typeof(*priv), subsys.kobj);
        struct bus_type *bus = priv->bus;

        kfree(priv);
        bus->p = NULL;
}

static struct kobj_type bus_ktype = {
        .sysfs_ops      = &bus_sysfs_ops,
        .release        = bus_release,
};

static int bus_uevent_filter(struct kset *kset, struct kobject *kobj)
{
        struct kobj_type *ktype = get_ktype(kobj);

        if (ktype == &bus_ktype)
                return 1;
        return 0;
}

static const struct kset_uevent_ops bus_uevent_ops = {
        .filter = bus_uevent_filter,
};

static struct kset *bus_kset;

/* Manually detach a device from its associated driver. */
static ssize_t unbind_store(struct device_driver *drv, const char *buf,
                            size_t count)
{
        struct bus_type *bus = bus_get(drv->bus);
        struct device *dev;
        int err = -ENODEV;

        dev = bus_find_device_by_name(bus, NULL, buf);
        if (dev && dev->driver == drv) {
                if (dev->parent)        /* Needed for USB */
                        device_lock(dev->parent);
                device_release_driver(dev);
                if (dev->parent)
                        device_unlock(dev->parent);
                err = count;
        }
        put_device(dev);
        bus_put(bus);
        return err;
}
static DRIVER_ATTR_WO(unbind);

/*
 * Manually attach a device to a driver.
 * Note: the driver must want to bind to the device,
 * it is not possible to override the driver's id table.
 */
static ssize_t bind_store(struct device_driver *drv, const char *buf,
                          size_t count)
{
        struct bus_type *bus = bus_get(drv->bus);
        struct device *dev;
        int err = -ENODEV;

        dev = bus_find_device_by_name(bus, NULL, buf);
        if (dev && dev->driver == NULL && driver_match_device(drv, dev)) {
                if (dev->parent)        /* Needed for USB */
                        device_lock(dev->parent);
                device_lock(dev);
                err = driver_probe_device(drv, dev);
                device_unlock(dev);
                if (dev->parent)
                        device_unlock(dev->parent);

                if (err > 0) {
                        /* success */
                        err = count;
                } else if (err == 0) {
                        /* driver didn't accept device */
                        err = -ENODEV;
                }
        }
        put_device(dev);
        bus_put(bus);
        return err;
}
static DRIVER_ATTR_WO(bind);

static ssize_t show_drivers_autoprobe(struct bus_type *bus, char *buf)
{
        return sprintf(buf, "%d\n", bus->p->drivers_autoprobe);
}

static ssize_t store_drivers_autoprobe(struct bus_type *bus,
                                       const char *buf, size_t count)
{
        if (buf[0] == '')
                bus->p->drivers_autoprobe = 0;
        else
                bus->p->drivers_autoprobe = 1;
        return count;
}

static ssize_t store_drivers_probe(struct bus_type *bus,
                                   const char *buf, size_t count)
{
        struct device *dev;
        int err = -EINVAL;

        dev = bus_find_device_by_name(bus, NULL, buf);
        if (!dev)
                return -ENODEV;
        if (bus_rescan_devices_helper(dev, NULL) == 0)
                err = count;
        put_device(dev);
        return err;
}

static struct device *next_device(struct klist_iter *i)
{
        struct klist_node *n = klist_next(i);
        struct device *dev = NULL;
        struct device_private *dev_prv;

        if (n) {
                dev_prv = to_device_private_bus(n);
                dev = dev_prv->device;
        }
        return dev;
}

/**
 * bus_for_each_dev - device iterator.
 * @bus: bus type.
 * @start: device to start iterating from.
 * @data: data for the callback.
 * @fn: function to be called for each device.
 *
 * Iterate over @bus's list of devices, and call @fn for each,
 * passing it @data. If @start is not NULL, we use that device to
 * begin iterating from.
 *
 * We check the return of @fn each time. If it returns anything
 * other than 0, we break out and return that value.
 *
 * NOTE: The device that returns a non-zero value is not retained
 * in any way, nor is its refcount incremented. If the caller needs
 * to retain this data, it should do so, and increment the reference
 * count in the supplied callback.
 */
int bus_for_each_dev(struct bus_type *bus, struct device *start,
                     void *data, int (*fn)(struct device *, void *))
{
        struct klist_iter i;
        struct device *dev;
        int error = 0;

        if (!bus || !bus->p)
                return -EINVAL;

        klist_iter_init_node(&bus->p->klist_devices, &i,
                             (start ? &start->p->knode_bus : NULL));
        while ((dev = next_device(&i)) && !error)
                error = fn(dev, data);
        klist_iter_exit(&i);
        return error;
}
EXPORT_SYMBOL_GPL(bus_for_each_dev);

/**
 * bus_find_device - device iterator for locating a particular device.
 * @bus: bus type
 * @start: Device to begin with
 * @data: Data to pass to match function
 * @match: Callback function to check device
 *
 * This is similar to the bus_for_each_dev() function above, but it
 * returns a reference to a device that is 'found' for later use, as
 * determined by the @match callback.
 *
 * The callback should return 0 if the device doesn't match and non-zero
 * if it does.  If the callback returns non-zero, this function will
 * return to the caller and not iterate over any more devices.
 */
struct device *bus_find_device(struct bus_type *bus,
                               struct device *start, void *data,
                               int (*match)(struct device *dev, void *data))
{
        struct klist_iter i;
        struct device *dev;

        if (!bus || !bus->p)
                return NULL;

        klist_iter_init_node(&bus->p->klist_devices, &i,
                             (start ? &start->p->knode_bus : NULL));
        while ((dev = next_device(&i)))
                if (match(dev, data) && get_device(dev))
                        break;
        klist_iter_exit(&i);
        return dev;
}
EXPORT_SYMBOL_GPL(bus_find_device);

static int match_name(struct device *dev, void *data)
{
        const char *name = data;

        return sysfs_streq(name, dev_name(dev));
}

/**
 * bus_find_device_by_name - device iterator for locating a particular device of a specific name
 * @bus: bus type
 * @start: Device to begin with
 * @name: name of the device to match
 *
 * This is similar to the bus_find_device() function above, but it handles
 * searching by a name automatically, no need to write another strcmp matching
 * function.
 */
struct device *bus_find_device_by_name(struct bus_type *bus,
                                       struct device *start, const char *name)
{
        return bus_find_device(bus, start, (void *)name, match_name);
}
EXPORT_SYMBOL_GPL(bus_find_device_by_name);

/**
 * subsys_find_device_by_id - find a device with a specific enumeration number
 * @subsys: subsystem
 * @id: index 'id' in struct device
 * @hint: device to check first
 *
 * Check the hint's next object and if it is a match return it directly,
 * otherwise, fall back to a full list search. Either way a reference for
 * the returned object is taken.
 */
struct device *subsys_find_device_by_id(struct bus_type *subsys, unsigned int id,
                                        struct device *hint)
{
        struct klist_iter i;
        struct device *dev;

        if (!subsys)
                return NULL;

        if (hint) {
                klist_iter_init_node(&subsys->p->klist_devices, &i, &hint->p->knode_bus);
                dev = next_device(&i);
                if (dev && dev->id == id && get_device(dev)) {
                        klist_iter_exit(&i);
                        return dev;
                }
                klist_iter_exit(&i);
        }

        klist_iter_init_node(&subsys->p->klist_devices, &i, NULL);
        while ((dev = next_device(&i))) {
                if (dev->id == id && get_device(dev)) {
                        klist_iter_exit(&i);
                        return dev;
                }
        }
        klist_iter_exit(&i);
        return NULL;
}
EXPORT_SYMBOL_GPL(subsys_find_device_by_id);

static struct device_driver *next_driver(struct klist_iter *i)
{
        struct klist_node *n = klist_next(i);
        struct driver_private *drv_priv;

        if (n) {
                drv_priv = container_of(n, struct driver_private, knode_bus);
                return drv_priv->driver;
        }
        return NULL;
}

/**
 * bus_for_each_drv - driver iterator
 * @bus: bus we're dealing with.
 * @start: driver to start iterating on.
 * @data: data to pass to the callback.
 * @fn: function to call for each driver.
 *
 * This is nearly identical to the device iterator above.
 * We iterate over each driver that belongs to @bus, and call
 * @fn for each. If @fn returns anything but 0, we break out
 * and return it. If @start is not NULL, we use it as the head
 * of the list.
 *
 * NOTE: we don't return the driver that returns a non-zero
 * value, nor do we leave the reference count incremented for that
 * driver. If the caller needs to know that info, it must set it
 * in the callback. It must also be sure to increment the refcount
 * so it doesn't disappear before returning to the caller.
 */
int bus_for_each_drv(struct bus_type *bus, struct device_driver *start,
                     void *data, int (*fn)(struct device_driver *, void *))
{
        struct klist_iter i;
        struct device_driver *drv;
        int error = 0;

        if (!bus)
                return -EINVAL;

        klist_iter_init_node(&bus->p->klist_drivers, &i,
                             start ? &start->p->knode_bus : NULL);
        while ((drv = next_driver(&i)) && !error)
                error = fn(drv, data);
        klist_iter_exit(&i);
        return error;
}
EXPORT_SYMBOL_GPL(bus_for_each_drv);

static int device_add_attrs(struct bus_type *bus, struct device *dev)
{
        int error = 0;
        int i;

        if (!bus->dev_attrs)
                return 0;

        for (i = 0; bus->dev_attrs[i].attr.name; i++) {
                error = device_create_file(dev, &bus->dev_attrs[i]);
                if (error) {
                        while (--i >= 0)
                                device_remove_file(dev, &bus->dev_attrs[i]);
                        break;
                }
        }
        return error;
}

static void device_remove_attrs(struct bus_type *bus, struct device *dev)
{
        int i;

        if (bus->dev_attrs) {
                for (i = 0; bus->dev_attrs[i].attr.name; i++)
                        device_remove_file(dev, &bus->dev_attrs[i]);
        }
}

/**
 * bus_add_device - add device to bus
 * @dev: device being added
 *
 * - Add device's bus attributes.
 * - Create links to device's bus.
 * - Add the device to its bus's list of devices.
 */
int bus_add_device(struct device *dev)
{
        struct bus_type *bus = bus_get(dev->bus);
        int error = 0;

        if (bus) {
                pr_debug("bus: '%s': add device %s\n", bus->name, dev_name(dev));
                error = device_add_attrs(bus, dev);
                if (error)
                        goto out_put;
                error = device_add_groups(dev, bus->dev_groups);
                if (error)
                        goto out_id;
                error = sysfs_create_link(&bus->p->devices_kset->kobj,
                                                &dev->kobj, dev_name(dev));
                if (error)
                        goto out_groups;
                error = sysfs_create_link(&dev->kobj,
                                &dev->bus->p->subsys.kobj, "subsystem");
                if (error)
                        goto out_subsys;
                klist_add_tail(&dev->p->knode_bus, &bus->p->klist_devices);
        }
        return 0;

out_subsys:
        sysfs_remove_link(&bus->p->devices_kset->kobj, dev_name(dev));
out_groups:
        device_remove_groups(dev, bus->dev_groups);
out_id:
        device_remove_attrs(bus, dev);
out_put:
        bus_put(dev->bus);
        return error;
}

/**
 * bus_probe_device - probe drivers for a new device
 * @dev: device to probe
 *
 * - Automatically probe for a driver if the bus allows it.
 */
void bus_probe_device(struct device *dev)
{
        struct bus_type *bus = dev->bus;
        struct subsys_interface *sif;
        int ret;

        if (!bus)
                return;

        if (bus->p->drivers_autoprobe) {
                ret = device_attach(dev);
                WARN_ON(ret < 0);
        }

        mutex_lock(&bus->p->mutex);
        list_for_each_entry(sif, &bus->p->interfaces, node)
                if (sif->add_dev)
                        sif->add_dev(dev, sif);
        mutex_unlock(&bus->p->mutex);
}

/**
 * bus_remove_device - remove device from bus
 * @dev: device to be removed
 *
 * - Remove device from all interfaces.
 * - Remove symlink from bus' directory.
 * - Delete device from bus's list.
 * - Detach from its driver.
 * - Drop reference taken in bus_add_device().
 */
void bus_remove_device(struct device *dev)
{
        struct bus_type *bus = dev->bus;
        struct subsys_interface *sif;

        if (!bus)
                return;

        mutex_lock(&bus->p->mutex);
        list_for_each_entry(sif, &bus->p->interfaces, node)
                if (sif->remove_dev)
                        sif->remove_dev(dev, sif);
        mutex_unlock(&bus->p->mutex);

        sysfs_remove_link(&dev->kobj, "subsystem");
        sysfs_remove_link(&dev->bus->p->devices_kset->kobj,
                          dev_name(dev));
        device_remove_attrs(dev->bus, dev);
        device_remove_groups(dev, dev->bus->dev_groups);
        if (klist_node_attached(&dev->p->knode_bus))
                klist_del(&dev->p->knode_bus);

        pr_debug("bus: '%s': remove device %s\n",
                 dev->bus->name, dev_name(dev));
        device_release_driver(dev);
        bus_put(dev->bus);
}

static int __must_check add_bind_files(struct device_driver *drv)
{
        int ret;

        ret = driver_create_file(drv, &driver_attr_unbind);
        if (ret == 0) {
                ret = driver_create_file(drv, &driver_attr_bind);
                if (ret)
                        driver_remove_file(drv, &driver_attr_unbind);
        }
        return ret;
}

static void remove_bind_files(struct device_driver *drv)
{
        driver_remove_file(drv, &driver_attr_bind);
        driver_remove_file(drv, &driver_attr_unbind);
}

static BUS_ATTR(drivers_probe, S_IWUSR, NULL, store_drivers_probe);
static BUS_ATTR(drivers_autoprobe, S_IWUSR | S_IRUGO,
                show_drivers_autoprobe, store_drivers_autoprobe);

static int add_probe_files(struct bus_type *bus)
{
        int retval;

        retval = bus_create_file(bus, &bus_attr_drivers_probe);
        if (retval)
                goto out;

        retval = bus_create_file(bus, &bus_attr_drivers_autoprobe);
        if (retval)
                bus_remove_file(bus, &bus_attr_drivers_probe);
out:
        return retval;
}

static void remove_probe_files(struct bus_type *bus)
{
        bus_remove_file(bus, &bus_attr_drivers_autoprobe);
        bus_remove_file(bus, &bus_attr_drivers_probe);
}

static ssize_t uevent_store(struct device_driver *drv, const char *buf,
                            size_t count)
{
        enum kobject_action action;

        if (kobject_action_type(buf, count, &action) == 0)
                kobject_uevent(&drv->p->kobj, action);
        return count;
}
static DRIVER_ATTR_WO(uevent);

/**
 * bus_add_driver - Add a driver to the bus.
 * @drv: driver.
 */
int bus_add_driver(struct device_driver *drv)
{
        struct bus_type *bus;
        struct driver_private *priv;
        int error = 0;

        bus = bus_get(drv->bus);
        if (!bus)
                return -EINVAL;

        pr_debug("bus: '%s': add driver %s\n", bus->name, drv->name);

        priv = kzalloc(sizeof(*priv), GFP_KERNEL);
        if (!priv) {
                error = -ENOMEM;
                goto out_put_bus;
        }
        klist_init(&priv->klist_devices, NULL, NULL);
        priv->driver = drv;
        drv->p = priv;
        priv->kobj.kset = bus->p->drivers_kset;
        error = kobject_init_and_add(&priv->kobj, &driver_ktype, NULL,
                                     "%s", drv->name);
        if (error)
                goto out_unregister;

        klist_add_tail(&priv->knode_bus, &bus->p->klist_drivers);
        if (drv->bus->p->drivers_autoprobe) {
                error = driver_attach(drv);
                if (error)
                        goto out_unregister;
        }
        module_add_driver(drv->owner, drv);

        error = driver_create_file(drv, &driver_attr_uevent);
        if (error) {
                printk(KERN_ERR "%s: uevent attr (%s) failed\n",
                        __func__, drv->name);
        }
        error = driver_add_groups(drv, bus->drv_groups);
        if (error) {
                /* How the hell do we get out of this pickle? Give up */
                printk(KERN_ERR "%s: driver_create_groups(%s) failed\n",
                        __func__, drv->name);
        }

        if (!drv->suppress_bind_attrs) {
                error = add_bind_files(drv);
                if (error) {
                        /* Ditto */
                        printk(KERN_ERR "%s: add_bind_files(%s) failed\n",
                                __func__, drv->name);
                }
        }

        return 0;

out_unregister:
        kobject_put(&priv->kobj);
        kfree(drv->p);
        drv->p = NULL;
out_put_bus:
        bus_put(bus);
        return error;
}

/**
 * bus_remove_driver - delete driver from bus's knowledge.
 * @drv: driver.
 *
 * Detach the driver from the devices it controls, and remove
 * it from its bus's list of drivers. Finally, we drop the reference
 * to the bus we took in bus_add_driver().
 */
void bus_remove_driver(struct device_driver *drv)
{
        if (!drv->bus)
                return;

        if (!drv->suppress_bind_attrs)
                remove_bind_files(drv);
        driver_remove_groups(drv, drv->bus->drv_groups);
        driver_remove_file(drv, &driver_attr_uevent);
        klist_remove(&drv->p->knode_bus);
        pr_debug("bus: '%s': remove driver %s\n", drv->bus->name, drv->name);
        driver_detach(drv);
        module_remove_driver(drv);
        kobject_put(&drv->p->kobj);
        bus_put(drv->bus);
}

/* Helper for bus_rescan_devices's iter */
static int __must_check bus_rescan_devices_helper(struct device *dev,
                                                  void *data)
{
        int ret = 0;

        if (!dev->driver) {
                if (dev->parent)        /* Needed for USB */
                        device_lock(dev->parent);
                ret = device_attach(dev);
                if (dev->parent)
                        device_unlock(dev->parent);
        }
        return ret < 0 ? ret : 0;
}

/**
 * bus_rescan_devices - rescan devices on the bus for possible drivers
 * @bus: the bus to scan.
 *
 * This function will look for devices on the bus with no driver
 * attached and rescan it against existing drivers to see if it matches
 * any by calling device_attach() for the unbound devices.
 */
int bus_rescan_devices(struct bus_type *bus)
{
        return bus_for_each_dev(bus, NULL, NULL, bus_rescan_devices_helper);
}
EXPORT_SYMBOL_GPL(bus_rescan_devices);

/**
 * device_reprobe - remove driver for a device and probe for a new driver
 * @dev: the device to reprobe
 *
 * This function detaches the attached driver (if any) for the given
 * device and restarts the driver probing process.  It is intended
 * to use if probing criteria changed during a devices lifetime and
 * driver attachment should change accordingly.
 */
int device_reprobe(struct device *dev)
{
        if (dev->driver) {
                if (dev->parent)        /* Needed for USB */
                        device_lock(dev->parent);
                device_release_driver(dev);
                if (dev->parent)
                        device_unlock(dev->parent);
        }
        return bus_rescan_devices_helper(dev, NULL);
}
EXPORT_SYMBOL_GPL(device_reprobe);

/**
 * find_bus - locate bus by name.
 * @name: name of bus.
 *
 * Call kset_find_obj() to iterate over list of buses to
 * find a bus by name. Return bus if found.
 *
 * Note that kset_find_obj increments bus' reference count.
 */
#if 0
struct bus_type *find_bus(char *name)
{
        struct kobject *k = kset_find_obj(bus_kset, name);
        return k ? to_bus(k) : NULL;
}
#endif  /*  0  */

static int bus_add_groups(struct bus_type *bus,
                          const struct attribute_group **groups)
{
        return sysfs_create_groups(&bus->p->subsys.kobj, groups);
}

static void bus_remove_groups(struct bus_type *bus,
                              const struct attribute_group **groups)
{
        sysfs_remove_groups(&bus->p->subsys.kobj, groups);
}

static void klist_devices_get(struct klist_node *n)
{
        struct device_private *dev_prv = to_device_private_bus(n);
        struct device *dev = dev_prv->device;

        get_device(dev);
}

static void klist_devices_put(struct klist_node *n)
{
        struct device_private *dev_prv = to_device_private_bus(n);
        struct device *dev = dev_prv->device;

        put_device(dev);
}

static ssize_t bus_uevent_store(struct bus_type *bus,
                                const char *buf, size_t count)
{
        enum kobject_action action;

        if (kobject_action_type(buf, count, &action) == 0)
                kobject_uevent(&bus->p->subsys.kobj, action);
        return count;
}
static BUS_ATTR(uevent, S_IWUSR, NULL, bus_uevent_store);

/**
 * bus_register - register a driver-core subsystem
 * @bus: bus to register
 *
 * Once we have that, we register the bus with the kobject
 * infrastructure, then register the children subsystems it has:
 * the devices and drivers that belong to the subsystem.
 */
int bus_register(struct bus_type *bus)
{
        int retval;
        struct subsys_private *priv;
        struct lock_class_key *key = &bus->lock_key;

        priv = kzalloc(sizeof(struct subsys_private), GFP_KERNEL);
        if (!priv)
                return -ENOMEM;

        priv->bus = bus;
        bus->p = priv;

        BLOCKING_INIT_NOTIFIER_HEAD(&priv->bus_notifier);

        retval = kobject_set_name(&priv->subsys.kobj, "%s", bus->name);
        if (retval)
                goto out;

        priv->subsys.kobj.kset = bus_kset;
        priv->subsys.kobj.ktype = &bus_ktype;
        priv->drivers_autoprobe = 1;

        retval = kset_register(&priv->subsys);
        if (retval)
                goto out;

        retval = bus_create_file(bus, &bus_attr_uevent);
        if (retval)
                goto bus_uevent_fail;

        priv->devices_kset = kset_create_and_add("devices", NULL,
                                                 &priv->subsys.kobj);
        if (!priv->devices_kset) {
                retval = -ENOMEM;
                goto bus_devices_fail;
        }

        priv->drivers_kset = kset_create_and_add("drivers", NULL,
                                                 &priv->subsys.kobj);
        if (!priv->drivers_kset) {
                retval = -ENOMEM;
                goto bus_drivers_fail;
        }

        INIT_LIST_HEAD(&priv->interfaces);
        __mutex_init(&priv->mutex, "subsys mutex", key);
        klist_init(&priv->klist_devices, klist_devices_get, klist_devices_put);
        klist_init(&priv->klist_drivers, NULL, NULL);

        retval = add_probe_files(bus);
        if (retval)
                goto bus_probe_files_fail;

        retval = bus_add_groups(bus, bus->bus_groups);
        if (retval)
                goto bus_groups_fail;

        pr_debug("bus: '%s': registered\n", bus->name);
        return 0;

bus_groups_fail:
        remove_probe_files(bus);
bus_probe_files_fail:
        kset_unregister(bus->p->drivers_kset);
bus_drivers_fail:
        kset_unregister(bus->p->devices_kset);
bus_devices_fail:
        bus_remove_file(bus, &bus_attr_uevent);
bus_uevent_fail:
        kset_unregister(&bus->p->subsys);
out:
        kfree(bus->p);
        bus->p = NULL;
        return retval;
}
EXPORT_SYMBOL_GPL(bus_register);

/**
 * bus_unregister - remove a bus from the system
 * @bus: bus.
 *
 * Unregister the child subsystems and the bus itself.
 * Finally, we call bus_put() to release the refcount
 */
void bus_unregister(struct bus_type *bus)
{
        pr_debug("bus: '%s': unregistering\n", bus->name);
        if (bus->dev_root)
                device_unregister(bus->dev_root);
        bus_remove_groups(bus, bus->bus_groups);
        remove_probe_files(bus);
        kset_unregister(bus->p->drivers_kset);
        kset_unregister(bus->p->devices_kset);
        bus_remove_file(bus, &bus_attr_uevent);
        kset_unregister(&bus->p->subsys);
}
EXPORT_SYMBOL_GPL(bus_unregister);

int bus_register_notifier(struct bus_type *bus, struct notifier_block *nb)
{
        return blocking_notifier_chain_register(&bus->p->bus_notifier, nb);
}
EXPORT_SYMBOL_GPL(bus_register_notifier);

int bus_unregister_notifier(struct bus_type *bus, struct notifier_block *nb)
{
        return blocking_notifier_chain_unregister(&bus->p->bus_notifier, nb);
}
EXPORT_SYMBOL_GPL(bus_unregister_notifier);

struct kset *bus_get_kset(struct bus_type *bus)
{
        return &bus->p->subsys;
}
EXPORT_SYMBOL_GPL(bus_get_kset);

struct klist *bus_get_device_klist(struct bus_type *bus)
{
        return &bus->p->klist_devices;
}
EXPORT_SYMBOL_GPL(bus_get_device_klist);

/*
 * Yes, this forcibly breaks the klist abstraction temporarily.  It
 * just wants to sort the klist, not change reference counts and
 * take/drop locks rapidly in the process.  It does all this while
  * holding the lock for the list, so objects can't otherwise be
  * added/removed while we're swizzling.
  */
 static void device_insertion_sort_klist(struct device *a, struct list_head *list,
                                         int (*compare)(const struct device *a,
                                                         const struct device *b))
 {
         struct list_head *pos;
         struct klist_node *n;
         struct device_private *dev_prv;
         struct device *b;
 
         list_for_each(pos, list) {
                 n = container_of(pos, struct klist_node, n_node);
                 dev_prv = to_device_private_bus(n);
                 b = dev_prv->device;
                 if (compare(a, b) <= 0) {
                         list_move_tail(&a->p->knode_bus.n_node,
                                        &b->p->knode_bus.n_node);
                         return;
                 }
         }
         list_move_tail(&a->p->knode_bus.n_node, list);
 }
 
 void bus_sort_breadthfirst(struct bus_type *bus,
                            int (*compare)(const struct device *a,
                                           const struct device *b))
 {
         LIST_HEAD(sorted_devices);
         struct list_head *pos, *tmp;
         struct klist_node *n;
         struct device_private *dev_prv;
         struct device *dev;
         struct klist *device_klist;
 
         device_klist = bus_get_device_klist(bus);
 
         spin_lock(&device_klist->k_lock);
         list_for_each_safe(pos, tmp, &device_klist->k_list) {
                 n = container_of(pos, struct klist_node, n_node);
                 dev_prv = to_device_private_bus(n);
                 dev = dev_prv->device;
                 device_insertion_sort_klist(dev, &sorted_devices, compare);
         }
         list_splice(&sorted_devices, &device_klist->k_list);
         spin_unlock(&device_klist->k_lock);
 }
 EXPORT_SYMBOL_GPL(bus_sort_breadthfirst);
 
 /**
  * subsys_dev_iter_init - initialize subsys device iterator
  * @iter: subsys iterator to initialize
  * @subsys: the subsys we wanna iterate over
  * @start: the device to start iterating from, if any
  * @type: device_type of the devices to iterate over, NULL for all
  *
  * Initialize subsys iterator @iter such that it iterates over devices
  * of @subsys.  If @start is set, the list iteration will start there,
  * otherwise if it is NULL, the iteration starts at the beginning of
  * the list.
  */
 void subsys_dev_iter_init(struct subsys_dev_iter *iter, struct bus_type *subsys,
                           struct device *start, const struct device_type *type)
 {
         struct klist_node *start_knode = NULL;
 
         if (start)
                 start_knode = &start->p->knode_bus;
         klist_iter_init_node(&subsys->p->klist_devices, &iter->ki, start_knode);
         iter->type = type;
 }
 EXPORT_SYMBOL_GPL(subsys_dev_iter_init);
 
 /**
  * subsys_dev_iter_next - iterate to the next device
  * @iter: subsys iterator to proceed
  *
  * Proceed @iter to the next device and return it.  Returns NULL if
  * iteration is complete.
  *
  * The returned device is referenced and won't be released till
  * iterator is proceed to the next device or exited.  The caller is
  * free to do whatever it wants to do with the device including
  * calling back into subsys code.
  */
 struct device *subsys_dev_iter_next(struct subsys_dev_iter *iter)
 {
         struct klist_node *knode;
         struct device *dev;
 
         for (;;) {
                 knode = klist_next(&iter->ki);
                 if (!knode)
                         return NULL;
                 dev = container_of(knode, struct device_private, knode_bus)->device;
                 if (!iter->type || iter->type == dev->type)
                         return dev;
         }
 }
 EXPORT_SYMBOL_GPL(subsys_dev_iter_next);
 
 /**
  * subsys_dev_iter_exit - finish iteration
  * @iter: subsys iterator to finish
  *
  * Finish an iteration.  Always call this function after iteration is
  * complete whether the iteration ran till the end or not.
  */
 void subsys_dev_iter_exit(struct subsys_dev_iter *iter)
 {
         klist_iter_exit(&iter->ki);
 }
 EXPORT_SYMBOL_GPL(subsys_dev_iter_exit);
 
 int subsys_interface_register(struct subsys_interface *sif)
 {
         struct bus_type *subsys;
         struct subsys_dev_iter iter;
         struct device *dev;
 
         if (!sif || !sif->subsys)
                 return -ENODEV;
 
         subsys = bus_get(sif->subsys);
         if (!subsys)
                 return -EINVAL;
 
         mutex_lock(&subsys->p->mutex);
         list_add_tail(&sif->node, &subsys->p->interfaces);
         if (sif->add_dev) {
                 subsys_dev_iter_init(&iter, subsys, NULL, NULL);
                 while ((dev = subsys_dev_iter_next(&iter)))
                         sif->add_dev(dev, sif);
                 subsys_dev_iter_exit(&iter);
         }
         mutex_unlock(&subsys->p->mutex);
 
         return 0;
 }
 EXPORT_SYMBOL_GPL(subsys_interface_register);
 
 void subsys_interface_unregister(struct subsys_interface *sif)
 {
         struct bus_type *subsys;
         struct subsys_dev_iter iter;
         struct device *dev;
 
         if (!sif || !sif->subsys)
                 return;
 
         subsys = sif->subsys;
 
         mutex_lock(&subsys->p->mutex);
         list_del_init(&sif->node);
         if (sif->remove_dev) {
                 subsys_dev_iter_init(&iter, subsys, NULL, NULL);
                 while ((dev = subsys_dev_iter_next(&iter)))
                         sif->remove_dev(dev, sif);
                 subsys_dev_iter_exit(&iter);
         }
         mutex_unlock(&subsys->p->mutex);
 
         bus_put(subsys);
 }
 EXPORT_SYMBOL_GPL(subsys_interface_unregister);
 
 static void system_root_device_release(struct device *dev)
 {
         kfree(dev);
 }
 
 static int subsys_register(struct bus_type *subsys,
                            const struct attribute_group **groups,
                            struct kobject *parent_of_root)
 {
         struct device *dev;
         int err;
 
         err = bus_register(subsys);
         if (err < 0)
                 return err;
 
         dev = kzalloc(sizeof(struct device), GFP_KERNEL);
         if (!dev) {
                 err = -ENOMEM;
                 goto err_dev;
         }
 
         err = dev_set_name(dev, "%s", subsys->name);
         if (err < 0)
                 goto err_name;
 
         dev->kobj.parent = parent_of_root;
         dev->groups = groups;
         dev->release = system_root_device_release;
 
         err = device_register(dev);
         if (err < 0)
                 goto err_dev_reg;
 
         subsys->dev_root = dev;
         return 0;
 
 err_dev_reg:
         put_device(dev);
         dev = NULL;
 err_name:
         kfree(dev);
 err_dev:
         bus_unregister(subsys);
         return err;
 }
 
 /**
  * subsys_system_register - register a subsystem at /sys/devices/system/
  * @subsys: system subsystem
  * @groups: default attributes for the root device
  *
  * All 'system' subsystems have a /sys/devices/system/<name> root device
  * with the name of the subsystem. The root device can carry subsystem-
  * wide attributes. All registered devices are below this single root
  * device and are named after the subsystem with a simple enumeration
  * number appended. The registered devices are not explicitly named;
  * only 'id' in the device needs to be set.
  *
  * Do not use this interface for anything new, it exists for compatibility
  * with bad ideas only. New subsystems should use plain subsystems; and
  * add the subsystem-wide attributes should be added to the subsystem
  * directory itself and not some create fake root-device placed in
  * /sys/devices/system/<name>.
  */
 int subsys_system_register(struct bus_type *subsys,
                            const struct attribute_group **groups)
 {
         return subsys_register(subsys, groups, &system_kset->kobj);
 }
 EXPORT_SYMBOL_GPL(subsys_system_register);
 
 /**
  * subsys_virtual_register - register a subsystem at /sys/devices/virtual/
  * @subsys: virtual subsystem
  * @groups: default attributes for the root device
  *
  * All 'virtual' subsystems have a /sys/devices/system/<name> root device
  * with the name of the subystem.  The root device can carry subsystem-wide
  * attributes.  All registered devices are below this single root device.
  * There's no restriction on device naming.  This is for kernel software
  * constructs which need sysfs interface.
  */
 int subsys_virtual_register(struct bus_type *subsys,
                             const struct attribute_group **groups)
 {
         struct kobject *virtual_dir;
 
         virtual_dir = virtual_device_parent(NULL);
         if (!virtual_dir)
                 return -ENOMEM;
 
         return subsys_register(subsys, groups, virtual_dir);
 }
 EXPORT_SYMBOL_GPL(subsys_virtual_register);
 
 int __init buses_init(void)
 {
         bus_kset = kset_create_and_add("bus", &bus_uevent_ops, NULL);
         if (!bus_kset)
                 return -ENOMEM;
 
         system_kset = kset_create_and_add("system", NULL, &devices_kset->kobj);
         if (!system_kset)
                 return -ENOMEM;
 
         return 0;
 }
 
```

```
/*
 * device.h - generic, centralized driver model
 *
 * Copyright (c) 2001-2003 Patrick Mochel <mochel@osdl.org>
 * Copyright (c) 2004-2009 Greg Kroah-Hartman <gregkh@suse.de>
 * Copyright (c) 2008-2009 Novell Inc.
 *
 * This file is released under the GPLv2
 *
 * See Documentation/driver-model/ for more information.
 */

#ifndef _DEVICE_H_
#define _DEVICE_H_

#include <linux/ioport.h>
#include <linux/kobject.h>
#include <linux/klist.h>
#include <linux/list.h>
#include <linux/lockdep.h>
#include <linux/compiler.h>
#include <linux/types.h>
#include <linux/mutex.h>
#include <linux/pinctrl/devinfo.h>
#include <linux/pm.h>
#include <linux/atomic.h>
#include <linux/ratelimit.h>
#include <linux/uidgid.h>
#include <linux/gfp.h>
#include <asm/device.h>

struct device;
struct device_private;
struct device_driver;
struct driver_private;
struct module;
struct class;
struct subsys_private;
struct bus_type;
struct device_node;
struct fwnode_handle;
struct iommu_ops;
struct iommu_group;

struct bus_attribute {
        struct attribute        attr;
        ssize_t (*show)(struct bus_type *bus, char *buf);
        ssize_t (*store)(struct bus_type *bus, const char *buf, size_t count);
};

#define BUS_ATTR(_name, _mode, _show, _store)   \
        struct bus_attribute bus_attr_##_name = __ATTR(_name, _mode, _show, _store)
#define BUS_ATTR_RW(_name) \
        struct bus_attribute bus_attr_##_name = __ATTR_RW(_name)
#define BUS_ATTR_RO(_name) \
        struct bus_attribute bus_attr_##_name = __ATTR_RO(_name)

extern int __must_check bus_create_file(struct bus_type *,
                                        struct bus_attribute *);
extern void bus_remove_file(struct bus_type *, struct bus_attribute *);

/**
 * struct bus_type - The bus type of the device
 *
 * @name:       The name of the bus.
 * @dev_name:   Used for subsystems to enumerate devices like ("foo%u", dev->id).
 * @dev_root:   Default device to use as the parent.
 * @dev_attrs:  Default attributes of the devices on the bus.
 * @bus_groups: Default attributes of the bus.
 * @dev_groups: Default attributes of the devices on the bus.
 * @drv_groups: Default attributes of the device drivers on the bus.
 * @match:      Called, perhaps multiple times, whenever a new device or driver
 *              is added for this bus. It should return a nonzero value if the
 *              given device can be handled by the given driver.
 * @uevent:     Called when a device is added, removed, or a few other things
 *              that generate uevents to add the environment variables.
 * @probe:      Called when a new device or driver add to this bus, and callback
 *              the specific driver's probe to initial the matched device.
 * @remove:     Called when a device removed from this bus.
 * @shutdown:   Called at shut-down time to quiesce the device.
 *
 * @online:     Called to put the device back online (after offlining it).
 * @offline:    Called to put the device offline for hot-removal. May fail.
 *
 * @suspend:    Called when a device on this bus wants to go to sleep mode.
 * @resume:     Called to bring a device on this bus out of sleep mode.
 * @pm:         Power management operations of this bus, callback the specific
 *              device driver's pm-ops.
 * @iommu_ops:  IOMMU specific operations for this bus, used to attach IOMMU
 *              driver implementations to a bus and allow the driver to do
 *              bus-specific setup
 * @p:          The private data of the driver core, only the driver core can
 *              touch this.
 * @lock_key:   Lock class key for use by the lock validator
 *
 * A bus is a channel between the processor and one or more devices. For the
 * purposes of the device model, all devices are connected via a bus, even if
 * it is an internal, virtual, "platform" bus. Buses can plug into each other.
 * A USB controller is usually a PCI device, for example. The device model
 * represents the actual connections between buses and the devices they control.
 * A bus is represented by the bus_type structure. It contains the name, the
 * default attributes, the bus' methods, PM operations, and the driver core's
 * private data.
 */
struct bus_type {
        const char              *name;
        const char              *dev_name;
        struct device           *dev_root;
        struct device_attribute *dev_attrs;     /* use dev_groups instead */
        const struct attribute_group **bus_groups;
        const struct attribute_group **dev_groups;
        const struct attribute_group **drv_groups;

        int (*match)(struct device *dev, struct device_driver *drv);
        int (*uevent)(struct device *dev, struct kobj_uevent_env *env);
        int (*probe)(struct device *dev);
        int (*remove)(struct device *dev);
        void (*shutdown)(struct device *dev);

        int (*online)(struct device *dev);
        int (*offline)(struct device *dev);

        int (*suspend)(struct device *dev, pm_message_t state);
        int (*resume)(struct device *dev);

        const struct dev_pm_ops *pm;

        const struct iommu_ops *iommu_ops;

        struct subsys_private *p;
        struct lock_class_key lock_key;
};

extern int __must_check bus_register(struct bus_type *bus);

extern void bus_unregister(struct bus_type *bus);

extern int __must_check bus_rescan_devices(struct bus_type *bus);

/* iterator helpers for buses */
struct subsys_dev_iter {
        struct klist_iter               ki;
        const struct device_type        *type;
};
void subsys_dev_iter_init(struct subsys_dev_iter *iter,
                         struct bus_type *subsys,
                         struct device *start,
                         const struct device_type *type);
struct device *subsys_dev_iter_next(struct subsys_dev_iter *iter);
void subsys_dev_iter_exit(struct subsys_dev_iter *iter);

int bus_for_each_dev(struct bus_type *bus, struct device *start, void *data,
                     int (*fn)(struct device *dev, void *data));
struct device *bus_find_device(struct bus_type *bus, struct device *start,
                               void *data,
                               int (*match)(struct device *dev, void *data));
struct device *bus_find_device_by_name(struct bus_type *bus,
                                       struct device *start,
                                       const char *name);
struct device *subsys_find_device_by_id(struct bus_type *bus, unsigned int id,
                                        struct device *hint);
int bus_for_each_drv(struct bus_type *bus, struct device_driver *start,
                     void *data, int (*fn)(struct device_driver *, void *));
void bus_sort_breadthfirst(struct bus_type *bus,
                           int (*compare)(const struct device *a,
                                          const struct device *b));
/*
 * Bus notifiers: Get notified of addition/removal of devices
 * and binding/unbinding of drivers to devices.
 * In the long run, it should be a replacement for the platform
 * notify hooks.
 */
struct notifier_block;

extern int bus_register_notifier(struct bus_type *bus,
                                 struct notifier_block *nb);
extern int bus_unregister_notifier(struct bus_type *bus,
                                   struct notifier_block *nb);

/* All 4 notifers below get called with the target struct device *
 * as an argument. Note that those functions are likely to be called
 * with the device lock held in the core, so be careful.
 */
#define BUS_NOTIFY_ADD_DEVICE           0x00000001 /* device added */
#define BUS_NOTIFY_DEL_DEVICE           0x00000002 /* device to be removed */
#define BUS_NOTIFY_REMOVED_DEVICE       0x00000003 /* device removed */
#define BUS_NOTIFY_BIND_DRIVER          0x00000004 /* driver about to be
                                                      bound */
#define BUS_NOTIFY_BOUND_DRIVER         0x00000005 /* driver bound to device */
#define BUS_NOTIFY_UNBIND_DRIVER        0x00000006 /* driver about to be
                                                      unbound */
#define BUS_NOTIFY_UNBOUND_DRIVER       0x00000007 /* driver is unbound
                                                      from the device */

extern struct kset *bus_get_kset(struct bus_type *bus);
extern struct klist *bus_get_device_klist(struct bus_type *bus);

/**
 * struct device_driver - The basic device driver structure
 * @name:       Name of the device driver.
 * @bus:        The bus which the device of this driver belongs to.
 * @owner:      The module owner.
 * @mod_name:   Used for built-in modules.
 * @suppress_bind_attrs: Disables bind/unbind via sysfs.
 * @of_match_table: The open firmware table.
 * @acpi_match_table: The ACPI match table.
 * @probe:      Called to query the existence of a specific device,
 *              whether this driver can work with it, and bind the driver
 *              to a specific device.
 * @remove:     Called when the device is removed from the system to
 *              unbind a device from this driver.
 * @shutdown:   Called at shut-down time to quiesce the device.
 * @suspend:    Called to put the device to sleep mode. Usually to a
 *              low power state.
 * @resume:     Called to bring a device from sleep mode.
 * @groups:     Default attributes that get created by the driver core
 *              automatically.
 * @pm:         Power management operations of the device which matched
 *              this driver.
 * @p:          Driver core's private data, no one other than the driver
 *              core can touch this.
 *
 * The device driver-model tracks all of the drivers known to the system.
 * The main reason for this tracking is to enable the driver core to match
 * up drivers with new devices. Once drivers are known objects within the
 * system, however, a number of other things become possible. Device drivers
 * can export information and configuration variables that are independent
 * of any specific device.
 */
struct device_driver {
        const char              *name;
        struct bus_type         *bus;

        struct module           *owner;
        const char              *mod_name;      /* used for built-in modules */

        bool suppress_bind_attrs;       /* disables bind/unbind via sysfs */

        const struct of_device_id       *of_match_table;
        const struct acpi_device_id     *acpi_match_table;

        int (*probe) (struct device *dev);
        int (*remove) (struct device *dev);
        void (*shutdown) (struct device *dev);
        int (*suspend) (struct device *dev, pm_message_t state);
        int (*resume) (struct device *dev);
        const struct attribute_group **groups;

        const struct dev_pm_ops *pm;

        struct driver_private *p;
};


extern int __must_check driver_register(struct device_driver *drv);
extern void driver_unregister(struct device_driver *drv);

extern struct device_driver *driver_find(const char *name,
                                         struct bus_type *bus);
extern int driver_probe_done(void);
extern void wait_for_device_probe(void);


/* sysfs interface for exporting driver attributes */

struct driver_attribute {
        struct attribute attr;
        ssize_t (*show)(struct device_driver *driver, char *buf);
        ssize_t (*store)(struct device_driver *driver, const char *buf,
                         size_t count);
};

#define DRIVER_ATTR(_name, _mode, _show, _store) \
        struct driver_attribute driver_attr_##_name = __ATTR(_name, _mode, _show, _store)
#define DRIVER_ATTR_RW(_name) \
        struct driver_attribute driver_attr_##_name = __ATTR_RW(_name)
#define DRIVER_ATTR_RO(_name) \
        struct driver_attribute driver_attr_##_name = __ATTR_RO(_name)
#define DRIVER_ATTR_WO(_name) \
        struct driver_attribute driver_attr_##_name = __ATTR_WO(_name)

extern int __must_check driver_create_file(struct device_driver *driver,
                                        const struct driver_attribute *attr);
extern void driver_remove_file(struct device_driver *driver,
                               const struct driver_attribute *attr);

extern int __must_check driver_for_each_device(struct device_driver *drv,
                                               struct device *start,
                                               void *data,
                                               int (*fn)(struct device *dev,
                                                         void *));
struct device *driver_find_device(struct device_driver *drv,
                                  struct device *start, void *data,
                                  int (*match)(struct device *dev, void *data));

/**
 * struct subsys_interface - interfaces to device functions
 * @name:       name of the device function
 * @subsys:     subsytem of the devices to attach to
 * @node:       the list of functions registered at the subsystem
 * @add_dev:    device hookup to device function handler
 * @remove_dev: device hookup to device function handler
 *
 * Simple interfaces attached to a subsystem. Multiple interfaces can
 * attach to a subsystem and its devices. Unlike drivers, they do not
 * exclusively claim or control devices. Interfaces usually represent
 * a specific functionality of a subsystem/class of devices.
 */
struct subsys_interface {
        const char *name;
        struct bus_type *subsys;
        struct list_head node;
        int (*add_dev)(struct device *dev, struct subsys_interface *sif);
        int (*remove_dev)(struct device *dev, struct subsys_interface *sif);
};

int subsys_interface_register(struct subsys_interface *sif);
void subsys_interface_unregister(struct subsys_interface *sif);

int subsys_system_register(struct bus_type *subsys,
                           const struct attribute_group **groups);
int subsys_virtual_register(struct bus_type *subsys,
                            const struct attribute_group **groups);

/**
 * struct class - device classes
 * @name:       Name of the class.
 * @owner:      The module owner.
 * @class_attrs: Default attributes of this class.
 * @dev_groups: Default attributes of the devices that belong to the class.
 * @dev_kobj:   The kobject that represents this class and links it into the hierarchy.
 * @dev_uevent: Called when a device is added, removed from this class, or a
 *              few other things that generate uevents to add the environment
 *              variables.
 * @devnode:    Callback to provide the devtmpfs.
 * @class_release: Called to release this class.
 * @dev_release: Called to release the device.
 * @suspend:    Used to put the device to sleep mode, usually to a low power
 *              state.
 * @resume:     Used to bring the device from the sleep mode.
 * @ns_type:    Callbacks so sysfs can detemine namespaces.
 * @namespace:  Namespace of the device belongs to this class.
 * @pm:         The default device power management operations of this class.
 * @p:          The private data of the driver core, no one other than the
 *              driver core can touch this.
 *
 * A class is a higher-level view of a device that abstracts out low-level
 * implementation details. Drivers may see a SCSI disk or an ATA disk, but,
 * at the class level, they are all simply disks. Classes allow user space
 * to work with devices based on what they do, rather than how they are
 * connected or how they work.
 */
struct class {
        const char              *name;
        struct module           *owner;

        struct class_attribute          *class_attrs;
        const struct attribute_group    **dev_groups;
        struct kobject                  *dev_kobj;

        int (*dev_uevent)(struct device *dev, struct kobj_uevent_env *env);
        char *(*devnode)(struct device *dev, umode_t *mode);

        void (*class_release)(struct class *class);
        void (*dev_release)(struct device *dev);

        int (*suspend)(struct device *dev, pm_message_t state);
        int (*resume)(struct device *dev);

        const struct kobj_ns_type_operations *ns_type;
        const void *(*namespace)(struct device *dev);

        const struct dev_pm_ops *pm;

        struct subsys_private *p;
};

struct class_dev_iter {
        struct klist_iter               ki;
        const struct device_type        *type;
};

extern struct kobject *sysfs_dev_block_kobj;
extern struct kobject *sysfs_dev_char_kobj;
extern int __must_check __class_register(struct class *class,
                                         struct lock_class_key *key);
extern void class_unregister(struct class *class);

/* This is a #define to keep the compiler from merging different
 * instances of the __key variable */
#define class_register(class)                   \
({                                              \
        static struct lock_class_key __key;     \
        __class_register(class, &__key);        \
})

struct class_compat;
struct class_compat *class_compat_register(const char *name);
void class_compat_unregister(struct class_compat *cls);
int class_compat_create_link(struct class_compat *cls, struct device *dev,
                             struct device *device_link);
void class_compat_remove_link(struct class_compat *cls, struct device *dev,
                              struct device *device_link);

extern void class_dev_iter_init(struct class_dev_iter *iter,
                                struct class *class,
                                struct device *start,
                                const struct device_type *type);
extern struct device *class_dev_iter_next(struct class_dev_iter *iter);
extern void class_dev_iter_exit(struct class_dev_iter *iter);

extern int class_for_each_device(struct class *class, struct device *start,
                                 void *data,
                                 int (*fn)(struct device *dev, void *data));
extern struct device *class_find_device(struct class *class,
                                        struct device *start, const void *data,
                                        int (*match)(struct device *, const void *));

struct class_attribute {
        struct attribute attr;
        ssize_t (*show)(struct class *class, struct class_attribute *attr,
                        char *buf);
        ssize_t (*store)(struct class *class, struct class_attribute *attr,
                        const char *buf, size_t count);
};

#define CLASS_ATTR(_name, _mode, _show, _store) \
        struct class_attribute class_attr_##_name = __ATTR(_name, _mode, _show, _store)
#define CLASS_ATTR_RW(_name) \
        struct class_attribute class_attr_##_name = __ATTR_RW(_name)
#define CLASS_ATTR_RO(_name) \
        struct class_attribute class_attr_##_name = __ATTR_RO(_name)

extern int __must_check class_create_file_ns(struct class *class,
                                             const struct class_attribute *attr,
                                             const void *ns);
extern void class_remove_file_ns(struct class *class,
                                 const struct class_attribute *attr,
                                 const void *ns);

static inline int __must_check class_create_file(struct class *class,
                                        const struct class_attribute *attr)
{
        return class_create_file_ns(class, attr, NULL);
}

static inline void class_remove_file(struct class *class,
                                     const struct class_attribute *attr)
{
        return class_remove_file_ns(class, attr, NULL);
}

/* Simple class attribute that is just a static string */
struct class_attribute_string {
        struct class_attribute attr;
        char *str;
};

/* Currently read-only only */
#define _CLASS_ATTR_STRING(_name, _mode, _str) \
        { __ATTR(_name, _mode, show_class_attr_string, NULL), _str }
#define CLASS_ATTR_STRING(_name, _mode, _str) \
        struct class_attribute_string class_attr_##_name = \
                _CLASS_ATTR_STRING(_name, _mode, _str)

extern ssize_t show_class_attr_string(struct class *class, struct class_attribute *attr,
                        char *buf);

struct class_interface {
        struct list_head        node;
        struct class            *class;

        int (*add_dev)          (struct device *, struct class_interface *);
        void (*remove_dev)      (struct device *, struct class_interface *);
};

extern int __must_check class_interface_register(struct class_interface *);
extern void class_interface_unregister(struct class_interface *);

extern struct class * __must_check __class_create(struct module *owner,
                                                  const char *name,
                                                  struct lock_class_key *key);
extern void class_destroy(struct class *cls);

/* This is a #define to keep the compiler from merging different
 * instances of the __key variable */
#define class_create(owner, name)               \
({                                              \
        static struct lock_class_key __key;     \
        __class_create(owner, name, &__key);    \
})

/*
 * The type of device, "struct device" is embedded in. A class
 * or bus can contain devices of different types
 * like "partitions" and "disks", "mouse" and "event".
 * This identifies the device type and carries type-specific
 * information, equivalent to the kobj_type of a kobject.
 * If "name" is specified, the uevent will contain it in
 * the DEVTYPE variable.
 */
struct device_type {
        const char *name;
        const struct attribute_group **groups;
        int (*uevent)(struct device *dev, struct kobj_uevent_env *env);
        char *(*devnode)(struct device *dev, umode_t *mode,
                         kuid_t *uid, kgid_t *gid);
        void (*release)(struct device *dev);

        const struct dev_pm_ops *pm;
};

/* interface for exporting device attributes */
struct device_attribute {
        struct attribute        attr;
        ssize_t (*show)(struct device *dev, struct device_attribute *attr,
                        char *buf);
        ssize_t (*store)(struct device *dev, struct device_attribute *attr,
                         const char *buf, size_t count);
};

struct dev_ext_attribute {
        struct device_attribute attr;
        void *var;
};

ssize_t device_show_ulong(struct device *dev, struct device_attribute *attr,
                          char *buf);
ssize_t device_store_ulong(struct device *dev, struct device_attribute *attr,
                           const char *buf, size_t count);
ssize_t device_show_int(struct device *dev, struct device_attribute *attr,
                        char *buf);
ssize_t device_store_int(struct device *dev, struct device_attribute *attr,
                         const char *buf, size_t count);
ssize_t device_show_bool(struct device *dev, struct device_attribute *attr,
                        char *buf);
ssize_t device_store_bool(struct device *dev, struct device_attribute *attr,
                         const char *buf, size_t count);

#define DEVICE_ATTR(_name, _mode, _show, _store) \
        struct device_attribute dev_attr_##_name = __ATTR(_name, _mode, _show, _store)
#define DEVICE_ATTR_RW(_name) \
        struct device_attribute dev_attr_##_name = __ATTR_RW(_name)
#define DEVICE_ATTR_RO(_name) \
        struct device_attribute dev_attr_##_name = __ATTR_RO(_name)
#define DEVICE_ATTR_WO(_name) \
        struct device_attribute dev_attr_##_name = __ATTR_WO(_name)
#define DEVICE_ULONG_ATTR(_name, _mode, _var) \
        struct dev_ext_attribute dev_attr_##_name = \
                { __ATTR(_name, _mode, device_show_ulong, device_store_ulong), &(_var) }
#define DEVICE_INT_ATTR(_name, _mode, _var) \
        struct dev_ext_attribute dev_attr_##_name = \
                { __ATTR(_name, _mode, device_show_int, device_store_int), &(_var) }
#define DEVICE_BOOL_ATTR(_name, _mode, _var) \
        struct dev_ext_attribute dev_attr_##_name = \
                { __ATTR(_name, _mode, device_show_bool, device_store_bool), &(_var) }
#define DEVICE_ATTR_IGNORE_LOCKDEP(_name, _mode, _show, _store) \
        struct device_attribute dev_attr_##_name =              \
                __ATTR_IGNORE_LOCKDEP(_name, _mode, _show, _store)

extern int device_create_file(struct device *device,
                              const struct device_attribute *entry);
extern void device_remove_file(struct device *dev,
                               const struct device_attribute *attr);
extern bool device_remove_file_self(struct device *dev,
                                    const struct device_attribute *attr);
extern int __must_check device_create_bin_file(struct device *dev,
                                        const struct bin_attribute *attr);
extern void device_remove_bin_file(struct device *dev,
                                   const struct bin_attribute *attr);

/* device resource management */
typedef void (*dr_release_t)(struct device *dev, void *res);
typedef int (*dr_match_t)(struct device *dev, void *res, void *match_data);

#ifdef CONFIG_DEBUG_DEVRES
extern void *__devres_alloc(dr_release_t release, size_t size, gfp_t gfp,
                             const char *name);
#define devres_alloc(release, size, gfp) \
        __devres_alloc(release, size, gfp, #release)
#else
extern void *devres_alloc(dr_release_t release, size_t size, gfp_t gfp);
#endif
extern void devres_for_each_res(struct device *dev, dr_release_t release,
                                dr_match_t match, void *match_data,
                                void (*fn)(struct device *, void *, void *),
                                void *data);
extern void devres_free(void *res);
extern void devres_add(struct device *dev, void *res);
extern void *devres_find(struct device *dev, dr_release_t release,
                         dr_match_t match, void *match_data);
extern void *devres_get(struct device *dev, void *new_res,
                        dr_match_t match, void *match_data);
extern void *devres_remove(struct device *dev, dr_release_t release,
                           dr_match_t match, void *match_data);
extern int devres_destroy(struct device *dev, dr_release_t release,
                          dr_match_t match, void *match_data);
extern int devres_release(struct device *dev, dr_release_t release,
                          dr_match_t match, void *match_data);

/* devres group */
extern void * __must_check devres_open_group(struct device *dev, void *id,
                                             gfp_t gfp);
extern void devres_close_group(struct device *dev, void *id);
extern void devres_remove_group(struct device *dev, void *id);
extern int devres_release_group(struct device *dev, void *id);

/* managed devm_k.alloc/kfree for device drivers */
extern void *devm_kmalloc(struct device *dev, size_t size, gfp_t gfp);
extern char *devm_kvasprintf(struct device *dev, gfp_t gfp, const char *fmt,
                             va_list ap);
extern __printf(3, 4)
char *devm_kasprintf(struct device *dev, gfp_t gfp, const char *fmt, ...);
static inline void *devm_kzalloc(struct device *dev, size_t size, gfp_t gfp)
{
        return devm_kmalloc(dev, size, gfp | __GFP_ZERO);
}
static inline void *devm_kmalloc_array(struct device *dev,
                                       size_t n, size_t size, gfp_t flags)
{
        if (size != 0 && n > SIZE_MAX / size)
                return NULL;
        return devm_kmalloc(dev, n * size, flags);
}
static inline void *devm_kcalloc(struct device *dev,
                                 size_t n, size_t size, gfp_t flags)
{
        return devm_kmalloc_array(dev, n, size, flags | __GFP_ZERO);
}
extern void devm_kfree(struct device *dev, void *p);
extern char *devm_kstrdup(struct device *dev, const char *s, gfp_t gfp);
extern void *devm_kmemdup(struct device *dev, const void *src, size_t len,
                          gfp_t gfp);

extern unsigned long devm_get_free_pages(struct device *dev,
                                         gfp_t gfp_mask, unsigned int order);
extern void devm_free_pages(struct device *dev, unsigned long addr);

void __iomem *devm_ioremap_resource(struct device *dev, struct resource *res);

/* allows to add/remove a custom action to devres stack */
int devm_add_action(struct device *dev, void (*action)(void *), void *data);
void devm_remove_action(struct device *dev, void (*action)(void *), void *data);

struct device_dma_parameters {
        /*
         * a low level driver may set these to teach IOMMU code about
         * sg limitations.
         */
        unsigned int max_segment_size;
        unsigned long segment_boundary_mask;
};

/**
 * struct device - The basic device structure
 * @parent:     The device's "parent" device, the device to which it is attached.
 *              In most cases, a parent device is some sort of bus or host
 *              controller. If parent is NULL, the device, is a top-level device,
 *              which is not usually what you want.
 * @p:          Holds the private data of the driver core portions of the device.
 *              See the comment of the struct device_private for detail.
 * @kobj:       A top-level, abstract class from which other classes are derived.
 * @init_name:  Initial name of the device.
 * @type:       The type of device.
 *              This identifies the device type and carries type-specific
 *              information.
 * @mutex:      Mutex to synchronize calls to its driver.
 * @bus:        Type of bus device is on.
 * @driver:     Which driver has allocated this
 * @platform_data: Platform data specific to the device.
 *              Example: For devices on custom boards, as typical of embedded
 *              and SOC based hardware, Linux often uses platform_data to point
 *              to board-specific structures describing devices and how they
 *              are wired.  That can include what ports are available, chip
 *              variants, which GPIO pins act in what additional roles, and so
 *              on.  This shrinks the "Board Support Packages" (BSPs) and
 *              minimizes board-specific #ifdefs in drivers.
 * @driver_data: Private pointer for driver specific info.
 * @power:      For device power management.
 *              See Documentation/power/devices.txt for details.
 * @pm_domain:  Provide callbacks that are executed during system suspend,
 *              hibernation, system resume and during runtime PM transitions
 *              along with subsystem-level and driver-level callbacks.
 * @pins:       For device pin management.
 *              See Documentation/pinctrl.txt for details.
 * @numa_node:  NUMA node this device is close to.
 * @dma_mask:   Dma mask (if dma'ble device).
 * @coherent_dma_mask: Like dma_mask, but for alloc_coherent mapping as not all
 *              hardware supports 64-bit addresses for consistent allocations
 *              such descriptors.
 * @dma_pfn_offset: offset of DMA memory range relatively of RAM
 * @dma_parms:  A low level driver may set these to teach IOMMU code about
 *              segment limitations.
 * @dma_pools:  Dma pools (if dma'ble device).
 * @dma_mem:    Internal for coherent mem override.
 * @cma_area:   Contiguous memory area for dma allocations
 * @archdata:   For arch-specific additions.
 * @of_node:    Associated device tree node.
 * @fwnode:     Associated device node supplied by platform firmware.
 * @devt:       For creating the sysfs "dev".
 * @id:         device instance
 * @devres_lock: Spinlock to protect the resource of the device.
 * @devres_head: The resources list of the device.
 * @knode_class: The node used to add the device to the class list.
 * @class:      The class of the device.
 * @groups:     Optional attribute groups.
 * @release:    Callback to free the device after all references have
 *              gone away. This should be set by the allocator of the
 *              device (i.e. the bus driver that discovered the device).
 * @iommu_group: IOMMU group the device belongs to.
 *
 * @offline_disabled: If set, the device is permanently online.
 * @offline:    Set after successful invocation of bus type's .offline().
 *
 * At the lowest level, every device in a Linux system is represented by an
 * instance of struct device. The device structure contains the information
 * that the device model core needs to model the system. Most subsystems,
 * however, track additional information about the devices they host. As a
 * result, it is rare for devices to be represented by bare device structures;
 * instead, that structure, like kobject structures, is usually embedded within
 * a higher-level representation of the device.
 */
struct device {
        struct device           *parent;

        struct device_private   *p;

        struct kobject kobj;
        const char              *init_name; /* initial name of the device */
        const struct device_type *type;

        struct mutex            mutex;  /* mutex to synchronize calls to
                                         * its driver.
                                         */

        struct bus_type *bus;           /* type of bus device is on */
        struct device_driver *driver;   /* which driver has allocated this
                                           device */
        void            *platform_data; /* Platform specific data, device
                                           core doesn't touch it */
        void            *driver_data;   /* Driver data, set and get with
                                           dev_set/get_drvdata */
        struct dev_pm_info      power;
        struct dev_pm_domain    *pm_domain;

#ifdef CONFIG_PINCTRL
        struct dev_pin_info     *pins;
#endif

#ifdef CONFIG_NUMA
        int             numa_node;      /* NUMA node this device is close to */
#endif
        u64             *dma_mask;      /* dma mask (if dma'able device) */
        u64             coherent_dma_mask;/* Like dma_mask, but for
                                             alloc_coherent mappings as
                                             not all hardware supports
                                             64 bit addresses for consistent
                                             allocations such descriptors. */
        unsigned long   dma_pfn_offset;

        struct device_dma_parameters *dma_parms;

        struct list_head        dma_pools;      /* dma pools (if dma'ble) */

        struct dma_coherent_mem *dma_mem; /* internal for coherent mem
                                             override */
#ifdef CONFIG_DMA_CMA
        struct cma *cma_area;           /* contiguous memory area for dma
                                           allocations */
#endif
        /* arch specific additions */
        struct dev_archdata     archdata;

        struct device_node      *of_node; /* associated device tree node */
        struct fwnode_handle    *fwnode; /* firmware device node */

        dev_t                   devt;   /* dev_t, creates the sysfs "dev" */
        u32                     id;     /* device instance */

        spinlock_t              devres_lock;
        struct list_head        devres_head;

        struct klist_node       knode_class;
        struct class            *class;
        const struct attribute_group **groups;  /* optional groups */

        void    (*release)(struct device *dev);
        struct iommu_group      *iommu_group;

        bool                    offline_disabled:1;
        bool                    offline:1;
};

static inline struct device *kobj_to_dev(struct kobject *kobj)
{
        return container_of(kobj, struct device, kobj);
}

/* Get the wakeup routines, which depend on struct device */
#include <linux/pm_wakeup.h>

static inline const char *dev_name(const struct device *dev)
{
        /* Use the init name until the kobject becomes available */
        if (dev->init_name)
                return dev->init_name;

        return kobject_name(&dev->kobj);
}

extern __printf(2, 3)
int dev_set_name(struct device *dev, const char *name, ...);

#ifdef CONFIG_NUMA
static inline int dev_to_node(struct device *dev)
{
        return dev->numa_node;
}
static inline void set_dev_node(struct device *dev, int node)
{
        dev->numa_node = node;
}
#else
static inline int dev_to_node(struct device *dev)
{
        return -1;
}
static inline void set_dev_node(struct device *dev, int node)
{
}
#endif

static inline void *dev_get_drvdata(const struct device *dev)
{
        return dev->driver_data;
}

static inline void dev_set_drvdata(struct device *dev, void *data)
{
        dev->driver_data = data;
}

static inline struct pm_subsys_data *dev_to_psd(struct device *dev)
{
        return dev ? dev->power.subsys_data : NULL;
}

static inline unsigned int dev_get_uevent_suppress(const struct device *dev)
{
        return dev->kobj.uevent_suppress;
}

static inline void dev_set_uevent_suppress(struct device *dev, int val)
{
        dev->kobj.uevent_suppress = val;
}

static inline int device_is_registered(struct device *dev)
{
        return dev->kobj.state_in_sysfs;
}

static inline void device_enable_async_suspend(struct device *dev)
{
        if (!dev->power.is_prepared)
                dev->power.async_suspend = true;
}

static inline void device_disable_async_suspend(struct device *dev)
{
        if (!dev->power.is_prepared)
                dev->power.async_suspend = false;
}

static inline bool device_async_suspend_enabled(struct device *dev)
{
        return !!dev->power.async_suspend;
}

static inline void pm_suspend_ignore_children(struct device *dev, bool enable)
{
        dev->power.ignore_children = enable;
}

static inline void dev_pm_syscore_device(struct device *dev, bool val)
{
#ifdef CONFIG_PM_SLEEP
        dev->power.syscore = val;
#endif
}

static inline void device_lock(struct device *dev)
{
        mutex_lock(&dev->mutex);
}

static inline int device_trylock(struct device *dev)
{
        return mutex_trylock(&dev->mutex);
}

static inline void device_unlock(struct device *dev)
{
        mutex_unlock(&dev->mutex);
}

static inline void device_lock_assert(struct device *dev)
{
        lockdep_assert_held(&dev->mutex);
}

static inline struct device_node *dev_of_node(struct device *dev)
{
        if (!IS_ENABLED(CONFIG_OF))
                return NULL;
        return dev->of_node;
}

void driver_init(void);

/*
 * High level routines for use by the bus drivers
 */
extern int __must_check device_register(struct device *dev);
extern void device_unregister(struct device *dev);
extern void device_initialize(struct device *dev);
extern int __must_check device_add(struct device *dev);
extern void device_del(struct device *dev);
extern int device_for_each_child(struct device *dev, void *data,
                     int (*fn)(struct device *dev, void *data));
extern struct device *device_find_child(struct device *dev, void *data,
                                int (*match)(struct device *dev, void *data));
extern int device_rename(struct device *dev, const char *new_name);
extern int device_move(struct device *dev, struct device *new_parent,
                       enum dpm_order dpm_order);
extern const char *device_get_devnode(struct device *dev,
                                      umode_t *mode, kuid_t *uid, kgid_t *gid,
                                      const char **tmp);

static inline bool device_supports_offline(struct device *dev)
{
        return dev->bus && dev->bus->offline && dev->bus->online;
}

extern void lock_device_hotplug(void);
extern void unlock_device_hotplug(void);
extern int lock_device_hotplug_sysfs(void);
extern int device_offline(struct device *dev);
extern int device_online(struct device *dev);
extern void set_primary_fwnode(struct device *dev, struct fwnode_handle *fwnode);
extern void set_secondary_fwnode(struct device *dev, struct fwnode_handle *fwnode);

/*
 * Root device objects for grouping under /sys/devices
 */
extern struct device *__root_device_register(const char *name,
                                             struct module *owner);

/* This is a macro to avoid include problems with THIS_MODULE */
#define root_device_register(name) \
        __root_device_register(name, THIS_MODULE)

extern void root_device_unregister(struct device *root);

static inline void *dev_get_platdata(const struct device *dev)
{
        return dev->platform_data;
}

/*
 * Manual binding of a device to driver. See drivers/base/bus.c
 * for information on use.
 */
extern int __must_check device_bind_driver(struct device *dev);
extern void device_release_driver(struct device *dev);
extern int  __must_check device_attach(struct device *dev);
extern int __must_check driver_attach(struct device_driver *drv);
extern int __must_check device_reprobe(struct device *dev);

/*
 * Easy functions for dynamically creating devices on the fly
 */
extern struct device *device_create_vargs(struct class *cls,
                                          struct device *parent,
                                          dev_t devt,
                                          void *drvdata,
                                          const char *fmt,
                                          va_list vargs);
extern __printf(5, 6)
struct device *device_create(struct class *cls, struct device *parent,
                             dev_t devt, void *drvdata,
                             const char *fmt, ...);
extern __printf(6, 7)
struct device *device_create_with_groups(struct class *cls,
                             struct device *parent, dev_t devt, void *drvdata,
                             const struct attribute_group **groups,
                             const char *fmt, ...);
extern void device_destroy(struct class *cls, dev_t devt);

 /*
  * Platform "fixup" functions - allow the platform to have their say
  * about devices and actions that the general device layer doesn't
  * know about.
  */
 /* Notify platform of device discovery */
 extern int (*platform_notify)(struct device *dev);
 
 extern int (*platform_notify_remove)(struct device *dev);
 
 
 /*
  * get_device - atomically increment the reference count for the device.
  *
  */
 extern struct device *get_device(struct device *dev);
 extern void put_device(struct device *dev);
 
 #ifdef CONFIG_DEVTMPFS
 extern int devtmpfs_create_node(struct device *dev);
 extern int devtmpfs_delete_node(struct device *dev);
 extern int devtmpfs_mount(const char *mntdir);
 #else
 static inline int devtmpfs_create_node(struct device *dev) { return 0; }
 static inline int devtmpfs_delete_node(struct device *dev) { return 0; }
 static inline int devtmpfs_mount(const char *mountpoint) { return 0; }
 #endif
 
 /* drivers/base/power/shutdown.c */
 extern void device_shutdown(void);
 
 /* debugging and troubleshooting/diagnostic helpers. */
 extern const char *dev_driver_string(const struct device *dev);
 
 
 #ifdef CONFIG_PRINTK
 
 extern __printf(3, 0)
 int dev_vprintk_emit(int level, const struct device *dev,
                      const char *fmt, va_list args);
 extern __printf(3, 4)
 int dev_printk_emit(int level, const struct device *dev, const char *fmt, ...);
 
 extern __printf(3, 4)
 void dev_printk(const char *level, const struct device *dev,
                 const char *fmt, ...);
 extern __printf(2, 3)
 void dev_emerg(const struct device *dev, const char *fmt, ...);
 extern __printf(2, 3)
 void dev_alert(const struct device *dev, const char *fmt, ...);
 extern __printf(2, 3)
 void dev_crit(const struct device *dev, const char *fmt, ...);
 extern __printf(2, 3)
 void dev_err(const struct device *dev, const char *fmt, ...);
 extern __printf(2, 3)
 void dev_warn(const struct device *dev, const char *fmt, ...);
 extern __printf(2, 3)
 void dev_notice(const struct device *dev, const char *fmt, ...);
 extern __printf(2, 3)
 void _dev_info(const struct device *dev, const char *fmt, ...);
 
 #else
 
 static inline __printf(3, 0)
 int dev_vprintk_emit(int level, const struct device *dev,
                      const char *fmt, va_list args)
 { return 0; }
 static inline __printf(3, 4)
 int dev_printk_emit(int level, const struct device *dev, const char *fmt, ...)
 { return 0; }
 
 static inline void __dev_printk(const char *level, const struct device *dev,
                                 struct va_format *vaf)
 {}
 static inline __printf(3, 4)
 void dev_printk(const char *level, const struct device *dev,
                 const char *fmt, ...)
 {}
 
 static inline __printf(2, 3)
 void dev_emerg(const struct device *dev, const char *fmt, ...)
 {}
 static inline __printf(2, 3)
 void dev_crit(const struct device *dev, const char *fmt, ...)
 {}
 static inline __printf(2, 3)
 void dev_alert(const struct device *dev, const char *fmt, ...)
 {}
 static inline __printf(2, 3)
 void dev_err(const struct device *dev, const char *fmt, ...)
 {}
 static inline __printf(2, 3)
 void dev_warn(const struct device *dev, const char *fmt, ...)
 {}
 static inline __printf(2, 3)
 void dev_notice(const struct device *dev, const char *fmt, ...)
 {}
 static inline __printf(2, 3)
 void _dev_info(const struct device *dev, const char *fmt, ...)
 {}
 
 #endif
 
 /*
  * Stupid hackaround for existing uses of non-printk uses dev_info
  *
  * Note that the definition of dev_info below is actually _dev_info
  * and a macro is used to avoid redefining dev_info
  */
 
 #define dev_info(dev, fmt, arg...) _dev_info(dev, fmt, ##arg)
 
 #if defined(CONFIG_DYNAMIC_DEBUG)
 #define dev_dbg(dev, format, ...)                    \
 do {                                                 \
         dynamic_dev_dbg(dev, format, ##__VA_ARGS__); \
 } while (0)
 #elif defined(DEBUG)
 #define dev_dbg(dev, format, arg...)            \
         dev_printk(KERN_DEBUG, dev, format, ##arg)
 #else
 #define dev_dbg(dev, format, arg...)                            \
 ({                                                              \
         if (0)                                                  \
                 dev_printk(KERN_DEBUG, dev, format, ##arg);     \
 })
 #endif
 
 #ifdef CONFIG_PRINTK
 #define dev_level_once(dev_level, dev, fmt, ...)                        \
 do {                                                                    \
         static bool __print_once __read_mostly;                         \
                                                                         \
         if (!__print_once) {                                            \
                 __print_once = true;                                    \
                 dev_level(dev, fmt, ##__VA_ARGS__);                     \
         }                                                               \
 } while (0)
 #else
 #define dev_level_once(dev_level, dev, fmt, ...)                        \
 do {                                                                    \
         if (0)                                                          \
                 dev_level(dev, fmt, ##__VA_ARGS__);                     \
 } while (0)
 #endif
 
 #define dev_emerg_once(dev, fmt, ...)                                   \
         dev_level_once(dev_emerg, dev, fmt, ##__VA_ARGS__)
 #define dev_alert_once(dev, fmt, ...)                                   \
         dev_level_once(dev_alert, dev, fmt, ##__VA_ARGS__)
 #define dev_crit_once(dev, fmt, ...)                                    \
         dev_level_once(dev_crit, dev, fmt, ##__VA_ARGS__)
 #define dev_err_once(dev, fmt, ...)                                     \
         dev_level_once(dev_err, dev, fmt, ##__VA_ARGS__)
 #define dev_warn_once(dev, fmt, ...)                                    \
         dev_level_once(dev_warn, dev, fmt, ##__VA_ARGS__)
 #define dev_notice_once(dev, fmt, ...)                                  \
         dev_level_once(dev_notice, dev, fmt, ##__VA_ARGS__)
 #define dev_info_once(dev, fmt, ...)                                    \
         dev_level_once(dev_info, dev, fmt, ##__VA_ARGS__)
 #define dev_dbg_once(dev, fmt, ...)                                     \
         dev_level_once(dev_dbg, dev, fmt, ##__VA_ARGS__)
 
 #define dev_level_ratelimited(dev_level, dev, fmt, ...)                 \
 do {                                                                    \
         static DEFINE_RATELIMIT_STATE(_rs,                              \
                                       DEFAULT_RATELIMIT_INTERVAL,       \
                                       DEFAULT_RATELIMIT_BURST);         \
         if (__ratelimit(&_rs))                                          \
                 dev_level(dev, fmt, ##__VA_ARGS__);                     \
 } while (0)
 
 #define dev_emerg_ratelimited(dev, fmt, ...)                            \
         dev_level_ratelimited(dev_emerg, dev, fmt, ##__VA_ARGS__)
 #define dev_alert_ratelimited(dev, fmt, ...)                            \
         dev_level_ratelimited(dev_alert, dev, fmt, ##__VA_ARGS__)
 #define dev_crit_ratelimited(dev, fmt, ...)                             \
         dev_level_ratelimited(dev_crit, dev, fmt, ##__VA_ARGS__)
 #define dev_err_ratelimited(dev, fmt, ...)                              \
         dev_level_ratelimited(dev_err, dev, fmt, ##__VA_ARGS__)
 #define dev_warn_ratelimited(dev, fmt, ...)                             \
         dev_level_ratelimited(dev_warn, dev, fmt, ##__VA_ARGS__)
 #define dev_notice_ratelimited(dev, fmt, ...)                           \
         dev_level_ratelimited(dev_notice, dev, fmt, ##__VA_ARGS__)
 #define dev_info_ratelimited(dev, fmt, ...)                             \
         dev_level_ratelimited(dev_info, dev, fmt, ##__VA_ARGS__)
 #if defined(CONFIG_DYNAMIC_DEBUG)
 /* descriptor check is first to prevent flooding with "callbacks suppressed" */
 #define dev_dbg_ratelimited(dev, fmt, ...)                              \
 do {                                                                    \
         static DEFINE_RATELIMIT_STATE(_rs,                              \
                                       DEFAULT_RATELIMIT_INTERVAL,       \
                                       DEFAULT_RATELIMIT_BURST);         \
         DEFINE_DYNAMIC_DEBUG_METADATA(descriptor, fmt);                 \
         if (unlikely(descriptor.flags & _DPRINTK_FLAGS_PRINT) &&        \
             __ratelimit(&_rs))                                          \
                 __dynamic_dev_dbg(&descriptor, dev, fmt,                \
                                   ##__VA_ARGS__);                       \
 } while (0)
 #elif defined(DEBUG)
 #define dev_dbg_ratelimited(dev, fmt, ...)                              \
 do {                                                                    \
         static DEFINE_RATELIMIT_STATE(_rs,                              \
                                       DEFAULT_RATELIMIT_INTERVAL,       \
                                       DEFAULT_RATELIMIT_BURST);         \
         if (__ratelimit(&_rs))                                          \
                 dev_printk(KERN_DEBUG, dev, fmt, ##__VA_ARGS__);        \
 } while (0)
 #else
 #define dev_dbg_ratelimited(dev, fmt, ...)                      \
         no_printk(KERN_DEBUG pr_fmt(fmt), ##__VA_ARGS__)
 #endif
 
 #ifdef VERBOSE_DEBUG
 #define dev_vdbg        dev_dbg
 #else
 #define dev_vdbg(dev, format, arg...)                           \
 ({                                                              \
         if (0)                                                  \
                 dev_printk(KERN_DEBUG, dev, format, ##arg);     \
 })
 #endif
 
 /*
  * dev_WARN*() acts like dev_printk(), but with the key difference of
  * using WARN/WARN_ONCE to include file/line information and a backtrace.
  */
 #define dev_WARN(dev, format, arg...) \
         WARN(1, "%s %s: " format, dev_driver_string(dev), dev_name(dev), ## arg);
 
 #define dev_WARN_ONCE(dev, condition, format, arg...) \
         WARN_ONCE(condition, "%s %s: " format, \
                         dev_driver_string(dev), dev_name(dev), ## arg)
 
 /* Create alias, so I can be autoloaded. */
 #define MODULE_ALIAS_CHARDEV(major,minor) \
         MODULE_ALIAS("char-major-" __stringify(major) "-" __stringify(minor))
 #define MODULE_ALIAS_CHARDEV_MAJOR(major) \
         MODULE_ALIAS("char-major-" __stringify(major) "-*")
 
 #ifdef CONFIG_SYSFS_DEPRECATED
 extern long sysfs_deprecated;
 #else
 #define sysfs_deprecated 0
 #endif
 
 /**
  * module_driver() - Helper macro for drivers that don't do anything
  * special in module init/exit. This eliminates a lot of boilerplate.
  * Each module may only use this macro once, and calling it replaces
  * module_init() and module_exit().
  *
  * @__driver: driver name
  * @__register: register function for this driver type
  * @__unregister: unregister function for this driver type
  * @...: Additional arguments to be passed to __register and __unregister.
  *
  * Use this macro to construct bus specific macros for registering
  * drivers, and do not use it on its own.
  */
 #define module_driver(__driver, __register, __unregister, ...) \
 static int __init __driver##_init(void) \
 { \
         return __register(&(__driver) , ##__VA_ARGS__); \
 } \
 module_init(__driver##_init); \
 static void __exit __driver##_exit(void) \
 { \
         __unregister(&(__driver) , ##__VA_ARGS__); \
 } \
 module_exit(__driver##_exit);
 
 #endif /* _DEVICE_H_ */
 
```

```
/*
 * sysfs.h - definitions for the device driver filesystem
 *
 * Copyright (c) 2001,2002 Patrick Mochel
 * Copyright (c) 2004 Silicon Graphics, Inc.
 * Copyright (c) 2007 SUSE Linux Products GmbH
 * Copyright (c) 2007 Tejun Heo <teheo@suse.de>
 *
 * Please see Documentation/filesystems/sysfs.txt for more information.
 */

#ifndef _SYSFS_H_
#define _SYSFS_H_

#include <linux/kernfs.h>
#include <linux/compiler.h>
#include <linux/errno.h>
#include <linux/list.h>
#include <linux/lockdep.h>
#include <linux/kobject_ns.h>
#include <linux/stat.h>
#include <linux/atomic.h>

struct kobject;
struct module;
struct bin_attribute;
enum kobj_ns_type;

struct attribute {
        const char              *name;
        umode_t                 mode;
#ifdef CONFIG_DEBUG_LOCK_ALLOC
        bool                    ignore_lockdep:1;
        struct lock_class_key   *key;
        struct lock_class_key   skey;
#endif
};

/**
 *      sysfs_attr_init - initialize a dynamically allocated sysfs attribute
 *      @attr: struct attribute to initialize
 *
 *      Initialize a dynamically allocated struct attribute so we can
 *      make lockdep happy.  This is a new requirement for attributes
 *      and initially this is only needed when lockdep is enabled.
 *      Lockdep gives a nice error when your attribute is added to
 *      sysfs if you don't have this.
 */
#ifdef CONFIG_DEBUG_LOCK_ALLOC
#define sysfs_attr_init(attr)                           \
do {                                                    \
        static struct lock_class_key __key;             \
                                                        \
        (attr)->key = &__key;                           \
} while (0)
#else
#define sysfs_attr_init(attr) do {} while (0)
#endif

/**
 * struct attribute_group - data structure used to declare an attribute group.
 * @name:       Optional: Attribute group name
 *              If specified, the attribute group will be created in
 *              a new subdirectory with this name.
 * @is_visible: Optional: Function to return permissions associated with an
 *              attribute of the group. Will be called repeatedly for each
 *              attribute in the group. Only read/write permissions as well as
 *              SYSFS_PREALLOC are accepted. Must return 0 if an attribute is
 *              not visible. The returned value will replace static permissions
 *              defined in struct attribute or struct bin_attribute.
 * @attrs:      Pointer to NULL terminated list of attributes.
 * @bin_attrs:  Pointer to NULL terminated list of binary attributes.
 *              Either attrs or bin_attrs or both must be provided.
 */
struct attribute_group {
        const char              *name;
        umode_t                 (*is_visible)(struct kobject *,
                                              struct attribute *, int);
        struct attribute        **attrs;
        struct bin_attribute    **bin_attrs;
};

/**
 * Use these macros to make defining attributes easier. See include/linux/device.h
 * for examples..
 */

#define SYSFS_PREALLOC 010000

#define __ATTR(_name, _mode, _show, _store) {                           \
        .attr = {.name = __stringify(_name),                            \
                 .mode = VERIFY_OCTAL_PERMISSIONS(_mode) },             \
        .show   = _show,                                                \
        .store  = _store,                                               \
}

#define __ATTR_PREALLOC(_name, _mode, _show, _store) {                  \
        .attr = {.name = __stringify(_name),                            \
                 .mode = SYSFS_PREALLOC | VERIFY_OCTAL_PERMISSIONS(_mode) },\
        .show   = _show,                                                \
        .store  = _store,                                               \
}

#define __ATTR_RO(_name) {                                              \
        .attr   = { .name = __stringify(_name), .mode = S_IRUGO },      \
        .show   = _name##_show,                                         \
}

#define __ATTR_WO(_name) {                                              \
        .attr   = { .name = __stringify(_name), .mode = S_IWUSR },      \
        .store  = _name##_store,                                        \
}

#define __ATTR_RW(_name) __ATTR(_name, (S_IWUSR | S_IRUGO),             \
                         _name##_show, _name##_store)

#define __ATTR_NULL { .attr = { .name = NULL } }

#ifdef CONFIG_DEBUG_LOCK_ALLOC
#define __ATTR_IGNORE_LOCKDEP(_name, _mode, _show, _store) {    \
        .attr = {.name = __stringify(_name), .mode = _mode,     \
                        .ignore_lockdep = true },               \
        .show           = _show,                                \
        .store          = _store,                               \
}
#else
#define __ATTR_IGNORE_LOCKDEP   __ATTR
#endif

#define __ATTRIBUTE_GROUPS(_name)                               \
static const struct attribute_group *_name##_groups[] = {       \
        &_name##_group,                                         \
        NULL,                                                   \
}

#define ATTRIBUTE_GROUPS(_name)                                 \
static const struct attribute_group _name##_group = {           \
        .attrs = _name##_attrs,                                 \
};                                                              \
__ATTRIBUTE_GROUPS(_name)

struct file;
struct vm_area_struct;

struct bin_attribute {
        struct attribute        attr;
        size_t                  size;
        void                    *private;
        ssize_t (*read)(struct file *, struct kobject *, struct bin_attribute *,
                        char *, loff_t, size_t);
        ssize_t (*write)(struct file *, struct kobject *, struct bin_attribute *,
                         char *, loff_t, size_t);
        int (*mmap)(struct file *, struct kobject *, struct bin_attribute *attr,
                    struct vm_area_struct *vma);
};

/**
 *      sysfs_bin_attr_init - initialize a dynamically allocated bin_attribute
 *      @attr: struct bin_attribute to initialize
 *
 *      Initialize a dynamically allocated struct bin_attribute so we
 *      can make lockdep happy.  This is a new requirement for
 *      attributes and initially this is only needed when lockdep is
 *      enabled.  Lockdep gives a nice error when your attribute is
 *      added to sysfs if you don't have this.
 */
#define sysfs_bin_attr_init(bin_attr) sysfs_attr_init(&(bin_attr)->attr)

/* macros to create static binary attributes easier */
#define __BIN_ATTR(_name, _mode, _read, _write, _size) {                \
        .attr = { .name = __stringify(_name), .mode = _mode },          \
        .read   = _read,                                                \
        .write  = _write,                                               \
        .size   = _size,                                                \
}

#define __BIN_ATTR_RO(_name, _size) {                                   \
        .attr   = { .name = __stringify(_name), .mode = S_IRUGO },      \
        .read   = _name##_read,                                         \
        .size   = _size,                                                \
}

#define __BIN_ATTR_RW(_name, _size) __BIN_ATTR(_name,                   \
                                   (S_IWUSR | S_IRUGO), _name##_read,   \
                                   _name##_write, _size)

#define __BIN_ATTR_NULL __ATTR_NULL

#define BIN_ATTR(_name, _mode, _read, _write, _size)                    \
struct bin_attribute bin_attr_##_name = __BIN_ATTR(_name, _mode, _read, \
                                        _write, _size)

#define BIN_ATTR_RO(_name, _size)                                       \
struct bin_attribute bin_attr_##_name = __BIN_ATTR_RO(_name, _size)

#define BIN_ATTR_RW(_name, _size)                                       \
struct bin_attribute bin_attr_##_name = __BIN_ATTR_RW(_name, _size)

struct sysfs_ops {
        ssize_t (*show)(struct kobject *, struct attribute *, char *);
        ssize_t (*store)(struct kobject *, struct attribute *, const char *, size_t);
};

#ifdef CONFIG_SYSFS

int __must_check sysfs_create_dir_ns(struct kobject *kobj, const void *ns);
void sysfs_remove_dir(struct kobject *kobj);
int __must_check sysfs_rename_dir_ns(struct kobject *kobj, const char *new_name,
                                     const void *new_ns);
int __must_check sysfs_move_dir_ns(struct kobject *kobj,
                                   struct kobject *new_parent_kobj,
                                   const void *new_ns);

int __must_check sysfs_create_file_ns(struct kobject *kobj,
                                      const struct attribute *attr,
                                      const void *ns);
int __must_check sysfs_create_files(struct kobject *kobj,
                                   const struct attribute **attr);
int __must_check sysfs_chmod_file(struct kobject *kobj,
                                  const struct attribute *attr, umode_t mode);
void sysfs_remove_file_ns(struct kobject *kobj, const struct attribute *attr,
                          const void *ns);
bool sysfs_remove_file_self(struct kobject *kobj, const struct attribute *attr);
void sysfs_remove_files(struct kobject *kobj, const struct attribute **attr);

int __must_check sysfs_create_bin_file(struct kobject *kobj,
                                       const struct bin_attribute *attr);
void sysfs_remove_bin_file(struct kobject *kobj,
                           const struct bin_attribute *attr);

int __must_check sysfs_create_link(struct kobject *kobj, struct kobject *target,
                                   const char *name);
int __must_check sysfs_create_link_nowarn(struct kobject *kobj,
                                          struct kobject *target,
                                          const char *name);
void sysfs_remove_link(struct kobject *kobj, const char *name);

int sysfs_rename_link_ns(struct kobject *kobj, struct kobject *target,
                         const char *old_name, const char *new_name,
                         const void *new_ns);

void sysfs_delete_link(struct kobject *dir, struct kobject *targ,
                        const char *name);

int __must_check sysfs_create_group(struct kobject *kobj,
                                    const struct attribute_group *grp);
int __must_check sysfs_create_groups(struct kobject *kobj,
                                     const struct attribute_group **groups);
int sysfs_update_group(struct kobject *kobj,
                       const struct attribute_group *grp);
void sysfs_remove_group(struct kobject *kobj,
                        const struct attribute_group *grp);
void sysfs_remove_groups(struct kobject *kobj,
                         const struct attribute_group **groups);
int sysfs_add_file_to_group(struct kobject *kobj,
                        const struct attribute *attr, const char *group);
void sysfs_remove_file_from_group(struct kobject *kobj,
                        const struct attribute *attr, const char *group);
int sysfs_merge_group(struct kobject *kobj,
                       const struct attribute_group *grp);
void sysfs_unmerge_group(struct kobject *kobj,
                       const struct attribute_group *grp);
int sysfs_add_link_to_group(struct kobject *kobj, const char *group_name,
                            struct kobject *target, const char *link_name);
void sysfs_remove_link_from_group(struct kobject *kobj, const char *group_name,
                                  const char *link_name);

void sysfs_notify(struct kobject *kobj, const char *dir, const char *attr);

int __must_check sysfs_init(void);

static inline void sysfs_enable_ns(struct kernfs_node *kn)
{
        return kernfs_enable_ns(kn);
}

#else /* CONFIG_SYSFS */

static inline int sysfs_create_dir_ns(struct kobject *kobj, const void *ns)
{
        return 0;
}

static inline void sysfs_remove_dir(struct kobject *kobj)
{
}

static inline int sysfs_rename_dir_ns(struct kobject *kobj,
                                      const char *new_name, const void *new_ns)
{
        return 0;
}

static inline int sysfs_move_dir_ns(struct kobject *kobj,
                                    struct kobject *new_parent_kobj,
                                    const void *new_ns)
{
        return 0;
}

static inline int sysfs_create_file_ns(struct kobject *kobj,
                                       const struct attribute *attr,
                                       const void *ns)
{
        return 0;
}

static inline int sysfs_create_files(struct kobject *kobj,
                                    const struct attribute **attr)
{
        return 0;
}

static inline int sysfs_chmod_file(struct kobject *kobj,
                                   const struct attribute *attr, umode_t mode)
{
        return 0;
}

static inline void sysfs_remove_file_ns(struct kobject *kobj,
                                        const struct attribute *attr,
                                        const void *ns)
{
}

static inline bool sysfs_remove_file_self(struct kobject *kobj,
                                          const struct attribute *attr)
{
        return false;
}

static inline void sysfs_remove_files(struct kobject *kobj,
                                     const struct attribute **attr)
{
}

static inline int sysfs_create_bin_file(struct kobject *kobj,
                                        const struct bin_attribute *attr)
{
        return 0;
}

static inline void sysfs_remove_bin_file(struct kobject *kobj,
                                         const struct bin_attribute *attr)
{
}

static inline int sysfs_create_link(struct kobject *kobj,
                                    struct kobject *target, const char *name)
{
        return 0;
}

static inline int sysfs_create_link_nowarn(struct kobject *kobj,
                                           struct kobject *target,
                                           const char *name)
{
        return 0;
}

static inline void sysfs_remove_link(struct kobject *kobj, const char *name)
{
}

static inline int sysfs_rename_link_ns(struct kobject *k, struct kobject *t,
                                       const char *old_name,
                                       const char *new_name, const void *ns)
{
        return 0;
}

static inline void sysfs_delete_link(struct kobject *k, struct kobject *t,
                                     const char *name)
{
}

static inline int sysfs_create_group(struct kobject *kobj,
                                     const struct attribute_group *grp)
{
        return 0;
}

static inline int sysfs_create_groups(struct kobject *kobj,
                                      const struct attribute_group **groups)
{
        return 0;
}

static inline int sysfs_update_group(struct kobject *kobj,
                                const struct attribute_group *grp)
{
        return 0;
}

static inline void sysfs_remove_group(struct kobject *kobj,
                                      const struct attribute_group *grp)
{
}

static inline void sysfs_remove_groups(struct kobject *kobj,
                                       const struct attribute_group **groups)
{
}

static inline int sysfs_add_file_to_group(struct kobject *kobj,
                const struct attribute *attr, const char *group)
{
        return 0;
}

static inline void sysfs_remove_file_from_group(struct kobject *kobj,
                const struct attribute *attr, const char *group)
{
}

static inline int sysfs_merge_group(struct kobject *kobj,
                       const struct attribute_group *grp)
{
        return 0;
}

static inline void sysfs_unmerge_group(struct kobject *kobj,
                       const struct attribute_group *grp)
{
}

static inline int sysfs_add_link_to_group(struct kobject *kobj,
                const char *group_name, struct kobject *target,
                const char *link_name)
{
        return 0;
}

static inline void sysfs_remove_link_from_group(struct kobject *kobj,
                const char *group_name, const char *link_name)
{
}

static inline void sysfs_notify(struct kobject *kobj, const char *dir,
                                const char *attr)
{
}

static inline int __must_check sysfs_init(void)
{
        return 0;
}

static inline void sysfs_enable_ns(struct kernfs_node *kn)
{
}

#endif /* CONFIG_SYSFS */

static inline int __must_check sysfs_create_file(struct kobject *kobj,
                                                 const struct attribute *attr)
{
        return sysfs_create_file_ns(kobj, attr, NULL);
}

static inline void sysfs_remove_file(struct kobject *kobj,
                                     const struct attribute *attr)
{
        sysfs_remove_file_ns(kobj, attr, NULL);
}

static inline int sysfs_rename_link(struct kobject *kobj, struct kobject *target,
                                    const char *old_name, const char *new_name)
{
        return sysfs_rename_link_ns(kobj, target, old_name, new_name, NULL);
}

static inline void sysfs_notify_dirent(struct kernfs_node *kn)
{
        kernfs_notify(kn);
}

static inline struct kernfs_node *sysfs_get_dirent(struct kernfs_node *parent,
                                                   const unsigned char *name)
{
        return kernfs_find_and_get(parent, name);
}

static inline struct kernfs_node *sysfs_get(struct kernfs_node *kn)
{
        kernfs_get(kn);
        return kn;
}

static inline void sysfs_put(struct kernfs_node *kn)
{
        kernfs_put(kn);
}

#endif /* _SYSFS_H_ */

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
         //容纳所有 devices 的　klist
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
 * drivers/base/dd.c - The core device/driver interactions.
 *
 * This file contains the (sometimes tricky) code that controls the
 * interactions between devices and drivers, which primarily includes
 * driver binding and unbinding.
 *
 * All of this code used to exist in drivers/base/bus.c, but was
 * relocated to here in the name of compartmentalization (since it wasn't
 * strictly code just for the 'struct bus_type'.
 *
 * Copyright (c) 2002-5 Patrick Mochel
 * Copyright (c) 2002-3 Open Source Development Labs
 * Copyright (c) 2007-2009 Greg Kroah-Hartman <gregkh@suse.de>
 * Copyright (c) 2007-2009 Novell Inc.
 *
 * This file is released under the GPLv2
 */

#include <linux/device.h>
#include <linux/delay.h>
#include <linux/module.h>
#include <linux/kthread.h>
#include <linux/wait.h>
#include <linux/async.h>
#include <linux/pm_runtime.h>
#include <linux/pinctrl/devinfo.h>

#include "base.h"
#include "power/power.h"

/*
 * Deferred Probe infrastructure.
 *
 * Sometimes driver probe order matters, but the kernel doesn't always have
 * dependency information which means some drivers will get probed before a
 * resource it depends on is available.  For example, an SDHCI driver may
 * first need a GPIO line from an i2c GPIO controller before it can be
 * initialized.  If a required resource is not available yet, a driver can
 * request probing to be deferred by returning -EPROBE_DEFER from its probe hook
 *
 * Deferred probe maintains two lists of devices, a pending list and an active
 * list.  A driver returning -EPROBE_DEFER causes the device to be added to the
 * pending list.  A successful driver probe will trigger moving all devices
 * from the pending to the active list so that the workqueue will eventually
 * retry them.
 *
 * The deferred_probe_mutex must be held any time the deferred_probe_*_list
 * of the (struct device*)->p->deferred_probe pointers are manipulated
 */
static DEFINE_MUTEX(deferred_probe_mutex);
static LIST_HEAD(deferred_probe_pending_list);
static LIST_HEAD(deferred_probe_active_list);
static struct workqueue_struct *deferred_wq;
static atomic_t deferred_trigger_count = ATOMIC_INIT(0);

/*
 * deferred_probe_work_func() - Retry probing devices in the active list.
 */
static void deferred_probe_work_func(struct work_struct *work)
{
        struct device *dev;
        struct device_private *private;
        /*
         * This block processes every device in the deferred 'active' list.
         * Each device is removed from the active list and passed to
         * bus_probe_device() to re-attempt the probe.  The loop continues
         * until every device in the active list is removed and retried.
         *
         * Note: Once the device is removed from the list and the mutex is
         * released, it is possible for the device get freed by another thread
         * and cause a illegal pointer dereference.  This code uses
         * get/put_device() to ensure the device structure cannot disappear
         * from under our feet.
         */
        mutex_lock(&deferred_probe_mutex);
        while (!list_empty(&deferred_probe_active_list)) {
                private = list_first_entry(&deferred_probe_active_list,
                                        typeof(*dev->p), deferred_probe);
                dev = private->device;
                list_del_init(&private->deferred_probe);

                get_device(dev);

                /*
                 * Drop the mutex while probing each device; the probe path may
                 * manipulate the deferred list
                 */
                mutex_unlock(&deferred_probe_mutex);

                /*
                 * Force the device to the end of the dpm_list since
                 * the PM code assumes that the order we add things to
                 * the list is a good order for suspend but deferred
                 * probe makes that very unsafe.
                 */
                device_pm_lock();
                device_pm_move_last(dev);
                device_pm_unlock();

                dev_dbg(dev, "Retrying from deferred list\n");
                bus_probe_device(dev);

                mutex_lock(&deferred_probe_mutex);

                put_device(dev);
        }
        mutex_unlock(&deferred_probe_mutex);
}
static DECLARE_WORK(deferred_probe_work, deferred_probe_work_func);

static void driver_deferred_probe_add(struct device *dev)
{
        mutex_lock(&deferred_probe_mutex);
        if (list_empty(&dev->p->deferred_probe)) {
                dev_dbg(dev, "Added to deferred list\n");
                list_add_tail(&dev->p->deferred_probe, &deferred_probe_pending_list);
        }
        mutex_unlock(&deferred_probe_mutex);
}

void driver_deferred_probe_del(struct device *dev)
{
        mutex_lock(&deferred_probe_mutex);
        if (!list_empty(&dev->p->deferred_probe)) {
                dev_dbg(dev, "Removed from deferred list\n");
                list_del_init(&dev->p->deferred_probe);
        }
        mutex_unlock(&deferred_probe_mutex);
}

static bool driver_deferred_probe_enable = false;
/**
 * driver_deferred_probe_trigger() - Kick off re-probing deferred devices
 *
 * This functions moves all devices from the pending list to the active
 * list and schedules the deferred probe workqueue to process them.  It
 * should be called anytime a driver is successfully bound to a device.
 *
 * Note, there is a race condition in multi-threaded probe. In the case where
 * more than one device is probing at the same time, it is possible for one
 * probe to complete successfully while another is about to defer. If the second
 * depends on the first, then it will get put on the pending list after the
 * trigger event has already occured and will be stuck there.
 *
 * The atomic 'deferred_trigger_count' is used to determine if a successful
 * trigger has occurred in the midst of probing a driver. If the trigger count
 * changes in the midst of a probe, then deferred processing should be triggered
 * again.
 */
static void driver_deferred_probe_trigger(void)
{
        if (!driver_deferred_probe_enable)
                return;

        /*
         * A successful probe means that all the devices in the pending list
         * should be triggered to be reprobed.  Move all the deferred devices
         * into the active list so they can be retried by the workqueue
         */
        mutex_lock(&deferred_probe_mutex);
        atomic_inc(&deferred_trigger_count);
        list_splice_tail_init(&deferred_probe_pending_list,
                              &deferred_probe_active_list);
        mutex_unlock(&deferred_probe_mutex);

        /*
         * Kick the re-probe thread.  It may already be scheduled, but it is
         * safe to kick it again.
         */
        queue_work(deferred_wq, &deferred_probe_work);
}

/**
 * deferred_probe_initcall() - Enable probing of deferred devices
 *
 * We don't want to get in the way when the bulk of drivers are getting probed.
 * Instead, this initcall makes sure that deferred probing is delayed until
 * late_initcall time.
 */
static int deferred_probe_initcall(void)
{
        deferred_wq = create_singlethread_workqueue("deferwq");
        if (WARN_ON(!deferred_wq))
                return -ENOMEM;

        driver_deferred_probe_enable = true;
        driver_deferred_probe_trigger();
        /* Sort as many dependencies as possible before exiting initcalls */
        flush_workqueue(deferred_wq);
        return 0;
}
late_initcall(deferred_probe_initcall);

static void driver_bound(struct device *dev)
{
        if (klist_node_attached(&dev->p->knode_driver)) {
                printk(KERN_WARNING "%s: device %s already bound\n",
                        __func__, kobject_name(&dev->kobj));
                return;
        }

        pr_debug("driver: '%s': %s: bound to device '%s'\n", dev->driver->name,
                 __func__, dev_name(dev));

        klist_add_tail(&dev->p->knode_driver, &dev->driver->p->klist_devices);

        /*
         * Make sure the device is no longer in one of the deferred lists and
         * kick off retrying all pending devices
         */
        driver_deferred_probe_del(dev);
        driver_deferred_probe_trigger();

        if (dev->bus)
                blocking_notifier_call_chain(&dev->bus->p->bus_notifier,
                                             BUS_NOTIFY_BOUND_DRIVER, dev);
}

static int driver_sysfs_add(struct device *dev)
{
        int ret;

        if (dev->bus)
                blocking_notifier_call_chain(&dev->bus->p->bus_notifier,
                                             BUS_NOTIFY_BIND_DRIVER, dev);

        ret = sysfs_create_link(&dev->driver->p->kobj, &dev->kobj,
                          kobject_name(&dev->kobj));
        if (ret == 0) {
                ret = sysfs_create_link(&dev->kobj, &dev->driver->p->kobj,
                                        "driver");
                if (ret)
                        sysfs_remove_link(&dev->driver->p->kobj,
                                        kobject_name(&dev->kobj));
        }
        return ret;
}

static void driver_sysfs_remove(struct device *dev)
{
        struct device_driver *drv = dev->driver;

        if (drv) {
                sysfs_remove_link(&drv->p->kobj, kobject_name(&dev->kobj));
                sysfs_remove_link(&dev->kobj, "driver");
        }
}

/**
 * device_bind_driver - bind a driver to one device.
 * @dev: device.
 *
 * Allow manual attachment of a driver to a device.
 * Caller must have already set @dev->driver.
 *
 * Note that this does not modify the bus reference count
 * nor take the bus's rwsem. Please verify those are accounted
 * for before calling this. (It is ok to call with no other effort
 * from a driver's probe() method.)
 *
 * This function must be called with the device lock held.
 */
int device_bind_driver(struct device *dev)
{
        int ret;

        ret = driver_sysfs_add(dev);
        if (!ret)
                driver_bound(dev);
        return ret;
}
EXPORT_SYMBOL_GPL(device_bind_driver);

static atomic_t probe_count = ATOMIC_INIT(0);
static DECLARE_WAIT_QUEUE_HEAD(probe_waitqueue);

static int really_probe(struct device *dev, struct device_driver *drv)
{
        int ret = 0;
        int local_trigger_count = atomic_read(&deferred_trigger_count);

        atomic_inc(&probe_count);
        pr_debug("bus: '%s': %s: probing driver %s with device %s\n",
                 drv->bus->name, __func__, drv->name, dev_name(dev));
        WARN_ON(!list_empty(&dev->devres_head));

        dev->driver = drv;

        /* If using pinctrl, bind pins now before probing */
        ret = pinctrl_bind_pins(dev);
        if (ret)
                goto probe_failed;

        if (driver_sysfs_add(dev)) {
                printk(KERN_ERR "%s: driver_sysfs_add(%s) failed\n",
                        __func__, dev_name(dev));
                goto probe_failed;
        }

        if (dev->pm_domain && dev->pm_domain->activate) {
                ret = dev->pm_domain->activate(dev);
                if (ret)
                        goto probe_failed;
        }

        if (dev->bus->probe) {
                ret = dev->bus->probe(dev);
                if (ret)
                        goto probe_failed;
        } else if (drv->probe) {
                ret = drv->probe(dev);
                if (ret)
                        goto probe_failed;
        }

        if (dev->pm_domain && dev->pm_domain->sync)
                dev->pm_domain->sync(dev);

        driver_bound(dev);
        ret = 1;
        pr_debug("bus: '%s': %s: bound device %s to driver %s\n",
                 drv->bus->name, __func__, dev_name(dev), drv->name);
        goto done;

probe_failed:
        devres_release_all(dev);
        driver_sysfs_remove(dev);
        dev->driver = NULL;
        dev_set_drvdata(dev, NULL);
        if (dev->pm_domain && dev->pm_domain->dismiss)
                dev->pm_domain->dismiss(dev);

        switch (ret) {
        case -EPROBE_DEFER:
                /* Driver requested deferred probing */
                dev_dbg(dev, "Driver %s requests probe deferral\n", drv->name);
                driver_deferred_probe_add(dev);
                /* Did a trigger occur while probing? Need to re-trigger if yes */
                if (local_trigger_count != atomic_read(&deferred_trigger_count))
                        driver_deferred_probe_trigger();
                break;
        case -ENODEV:
        case -ENXIO:
                pr_debug("%s: probe of %s rejects match %d\n",
                         drv->name, dev_name(dev), ret);
                break;
        default:
                /* driver matched but the probe failed */
                printk(KERN_WARNING
                       "%s: probe of %s failed with error %d\n",
                       drv->name, dev_name(dev), ret);
        }
        /*
         * Ignore errors returned by ->probe so that the next driver can try
         * its luck.
         */
        ret = 0;
done:
        atomic_dec(&probe_count);
        wake_up(&probe_waitqueue);
        return ret;
}

/**
 * driver_probe_done
 * Determine if the probe sequence is finished or not.
 *
 * Should somehow figure out how to use a semaphore, not an atomic variable...
 */
int driver_probe_done(void)
{
        pr_debug("%s: probe_count = %d\n", __func__,
                 atomic_read(&probe_count));
        if (atomic_read(&probe_count))
                return -EBUSY;
        return 0;
}

/**
 * wait_for_device_probe
 * Wait for device probing to be completed.
 */
void wait_for_device_probe(void)
{
        /* wait for the known devices to complete their probing */
        wait_event(probe_waitqueue, atomic_read(&probe_count) == 0);
        async_synchronize_full();
}
EXPORT_SYMBOL_GPL(wait_for_device_probe);

/**
 * driver_probe_device - attempt to bind device & driver together
 * @drv: driver to bind a device to
 * @dev: device to try to bind to the driver
 *
 * This function returns -ENODEV if the device is not registered,
 * 1 if the device is bound successfully and 0 otherwise.
 *
 * This function must be called with @dev lock held.  When called for a
 * USB interface, @dev->parent lock must be held as well.
 */
int driver_probe_device(struct device_driver *drv, struct device *dev)
{
        int ret = 0;

        if (!device_is_registered(dev))
                return -ENODEV;

        pr_debug("bus: '%s': %s: matched device %s with driver %s\n",
                 drv->bus->name, __func__, dev_name(dev), drv->name);

        pm_runtime_barrier(dev);
        ret = really_probe(dev, drv);
        pm_request_idle(dev);

        return ret;
}

static int __device_attach(struct device_driver *drv, void *data)
{
        struct device *dev = data;

        if (!driver_match_device(drv, dev))
                return 0;

        return driver_probe_device(drv, dev);
}

/**
 * device_attach - try to attach device to a driver.
 * @dev: device.
 *
 * Walk the list of drivers that the bus has and call
 * driver_probe_device() for each pair. If a compatible
 * pair is found, break out and return.
 *
 * Returns 1 if the device was bound to a driver;
 * 0 if no matching driver was found;
 * -ENODEV if the device is not registered.
 *
 * When called for a USB interface, @dev->parent lock must be held.
 */
int device_attach(struct device *dev)
{
        int ret = 0;

        device_lock(dev);
        if (dev->driver) {
                if (klist_node_attached(&dev->p->knode_driver)) {
                        ret = 1;
                        goto out_unlock;
                }
                ret = device_bind_driver(dev);
                if (ret == 0)
                        ret = 1;
                else {
                        dev->driver = NULL;
                        ret = 0;
                }
        } else {
                ret = bus_for_each_drv(dev->bus, NULL, dev, __device_attach);
                pm_request_idle(dev);
        }
out_unlock:
        device_unlock(dev);
        return ret;
}
EXPORT_SYMBOL_GPL(device_attach);

static int __driver_attach(struct device *dev, void *data)
{
        struct device_driver *drv = data;

        /*
         * Lock device and try to bind to it. We drop the error
         * here and always return 0, because we need to keep trying
         * to bind to devices and some drivers will return an error
         * simply if it didn't support the device.
         *
         * driver_probe_device() will spit a warning if there
         * is an error.
         */

        if (!driver_match_device(drv, dev))
                return 0;

        if (dev->parent)        /* Needed for USB */
                device_lock(dev->parent);
        device_lock(dev);
        if (!dev->driver)
                driver_probe_device(drv, dev);
        device_unlock(dev);
        if (dev->parent)
                device_unlock(dev->parent);

        return 0;
}

/**
 * driver_attach - try to bind driver to devices.
 * @drv: driver.
 *
 * Walk the list of devices that the bus has on it and try to
 * match the driver with each one.  If driver_probe_device()
 * returns 0 and the @dev->driver is set, we've found a
 * compatible pair.
 */
int driver_attach(struct device_driver *drv)
{
        return bus_for_each_dev(drv->bus, NULL, drv, __driver_attach);
}
EXPORT_SYMBOL_GPL(driver_attach);

/*
 * __device_release_driver() must be called with @dev lock held.
 * When called for a USB interface, @dev->parent lock must be held as well.
 */
static void __device_release_driver(struct device *dev)
{
        struct device_driver *drv;

        drv = dev->driver;
        if (drv) {
                pm_runtime_get_sync(dev);

                driver_sysfs_remove(dev);

                if (dev->bus)
                        blocking_notifier_call_chain(&dev->bus->p->bus_notifier,
                                                     BUS_NOTIFY_UNBIND_DRIVER,
                                                     dev);

                pm_runtime_put_sync(dev);

                if (dev->bus && dev->bus->remove)
                        dev->bus->remove(dev);
                else if (drv->remove)
                        drv->remove(dev);
                devres_release_all(dev);
                dev->driver = NULL;
                dev_set_drvdata(dev, NULL);
                if (dev->pm_domain && dev->pm_domain->dismiss)
                        dev->pm_domain->dismiss(dev);

                klist_remove(&dev->p->knode_driver);
                if (dev->bus)
                        blocking_notifier_call_chain(&dev->bus->p->bus_notifier,
                                                     BUS_NOTIFY_UNBOUND_DRIVER,
                                                     dev);

        }
}

/**
 * device_release_driver - manually detach device from driver.
 * @dev: device.
 *
 * Manually detach device from driver.
 * When called for a USB interface, @dev->parent lock must be held.
 */
void device_release_driver(struct device *dev)
{
        /*
         * If anyone calls device_release_driver() recursively from
         * within their ->remove callback for the same device, they
         * will deadlock right here.
         */
        device_lock(dev);
        __device_release_driver(dev);
        device_unlock(dev);
}
EXPORT_SYMBOL_GPL(device_release_driver);

/**
 * driver_detach - detach driver from all devices it controls.
 * @drv: driver.
 */
void driver_detach(struct device_driver *drv)
{
        struct device_private *dev_prv;
        struct device *dev;

        for (;;) {
                spin_lock(&drv->p->klist_devices.k_lock);
                if (list_empty(&drv->p->klist_devices.k_list)) {
                        spin_unlock(&drv->p->klist_devices.k_lock);
                        break;
                }
                dev_prv = list_entry(drv->p->klist_devices.k_list.prev,
                                     struct device_private,
                                     knode_driver.n_node);
                dev = dev_prv->device;
                get_device(dev);
                spin_unlock(&drv->p->klist_devices.k_lock);

                if (dev->parent)        /* Needed for USB */
                        device_lock(dev->parent);
                device_lock(dev);
                if (dev->driver == drv)
                        __device_release_driver(dev);
                device_unlock(dev);
                if (dev->parent)
                        device_unlock(dev->parent);
                put_device(dev);
        }
}

```

```
/*
 * driver.c - centralized device driver management
 *
 * Copyright (c) 2002-3 Patrick Mochel
 * Copyright (c) 2002-3 Open Source Development Labs
 * Copyright (c) 2007 Greg Kroah-Hartman <gregkh@suse.de>
 * Copyright (c) 2007 Novell Inc.
 *
 * This file is released under the GPLv2
 *
 */

#include <linux/device.h>
#include <linux/module.h>
#include <linux/errno.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/sysfs.h>
#include "base.h"

static struct device *next_device(struct klist_iter *i)
{
        struct klist_node *n = klist_next(i);
        struct device *dev = NULL;
        struct device_private *dev_prv;

        if (n) {
                dev_prv = to_device_private_driver(n);
                dev = dev_prv->device;
        }
        return dev;
}

/**
 * driver_for_each_device - Iterator for devices bound to a driver.
 * @drv: Driver we're iterating.
 * @start: Device to begin with
 * @data: Data to pass to the callback.
 * @fn: Function to call for each device.
 *
 * Iterate over the @drv's list of devices calling @fn for each one.
 */
int driver_for_each_device(struct device_driver *drv, struct device *start,
                           void *data, int (*fn)(struct device *, void *))
{
        struct klist_iter i;
        struct device *dev;
        int error = 0;

        if (!drv)
                return -EINVAL;

        klist_iter_init_node(&drv->p->klist_devices, &i,
                             start ? &start->p->knode_driver : NULL);
        while ((dev = next_device(&i)) && !error)
                error = fn(dev, data);
        klist_iter_exit(&i);
        return error;
}
EXPORT_SYMBOL_GPL(driver_for_each_device);

/**
 * driver_find_device - device iterator for locating a particular device.
 * @drv: The device's driver
 * @start: Device to begin with
 * @data: Data to pass to match function
 * @match: Callback function to check device
 *
 * This is similar to the driver_for_each_device() function above, but
 * it returns a reference to a device that is 'found' for later use, as
 * determined by the @match callback.
 *
 * The callback should return 0 if the device doesn't match and non-zero
 * if it does.  If the callback returns non-zero, this function will
 * return to the caller and not iterate over any more devices.
 */
struct device *driver_find_device(struct device_driver *drv,
                                  struct device *start, void *data,
                                  int (*match)(struct device *dev, void *data))
{
        struct klist_iter i;
        struct device *dev;

        if (!drv || !drv->p)
                return NULL;

        klist_iter_init_node(&drv->p->klist_devices, &i,
                             (start ? &start->p->knode_driver : NULL));
        while ((dev = next_device(&i)))
                if (match(dev, data) && get_device(dev))
                        break;
        klist_iter_exit(&i);
        return dev;
}
EXPORT_SYMBOL_GPL(driver_find_device);

/**
 * driver_create_file - create sysfs file for driver.
 * @drv: driver.
 * @attr: driver attribute descriptor.
 */
int driver_create_file(struct device_driver *drv,
                       const struct driver_attribute *attr)
{
        int error;

        if (drv)
                error = sysfs_create_file(&drv->p->kobj, &attr->attr);
        else
                error = -EINVAL;
        return error;
}
EXPORT_SYMBOL_GPL(driver_create_file);

/**
 * driver_remove_file - remove sysfs file for driver.
 * @drv: driver.
 * @attr: driver attribute descriptor.
 */
void driver_remove_file(struct device_driver *drv,
                        const struct driver_attribute *attr)
{
        if (drv)
                sysfs_remove_file(&drv->p->kobj, &attr->attr);
}
EXPORT_SYMBOL_GPL(driver_remove_file);

int driver_add_groups(struct device_driver *drv,
                      const struct attribute_group **groups)
{
        return sysfs_create_groups(&drv->p->kobj, groups);
}

void driver_remove_groups(struct device_driver *drv,
                          const struct attribute_group **groups)
{
        sysfs_remove_groups(&drv->p->kobj, groups);
}

/**
 * driver_register - register driver with bus
 * @drv: driver to register
 *
 * We pass off most of the work to the bus_add_driver() call,
 * since most of the things we have to do deal with the bus
 * structures.
 */
int driver_register(struct device_driver *drv)
{
        int ret;
        struct device_driver *other;

        BUG_ON(!drv->bus->p);

        if ((drv->bus->probe && drv->probe) ||
            (drv->bus->remove && drv->remove) ||
            (drv->bus->shutdown && drv->shutdown))
                printk(KERN_WARNING "Driver '%s' needs updating - please use "
                        "bus_type methods\n", drv->name);

        other = driver_find(drv->name, drv->bus);
        if (other) {
                printk(KERN_ERR "Error: Driver '%s' is already registered, "
                        "aborting...\n", drv->name);
                return -EBUSY;
        }

        ret = bus_add_driver(drv);
        if (ret)
                return ret;
        ret = driver_add_groups(drv, drv->groups);
        if (ret) {
                bus_remove_driver(drv);
                return ret;
        }
        kobject_uevent(&drv->p->kobj, KOBJ_ADD);

        return ret;
}
EXPORT_SYMBOL_GPL(driver_register);

/**
 * driver_unregister - remove driver from system.
 * @drv: driver.
 *
 * Again, we pass off most of the work to the bus-level call.
 */
void driver_unregister(struct device_driver *drv)
{
        if (!drv || !drv->p) {
                WARN(1, "Unexpected driver unregister!\n");
                return;
        }
        driver_remove_groups(drv, drv->groups);
        bus_remove_driver(drv);
}
EXPORT_SYMBOL_GPL(driver_unregister);

/**
 * driver_find - locate driver on a bus by its name.
 * @name: name of the driver.
 * @bus: bus to scan for the driver.
 *
 * Call kset_find_obj() to iterate over list of drivers on
 * a bus to find driver by name. Return driver if found.
 *
 * This routine provides no locking to prevent the driver it returns
 * from being unregistered or unloaded while the caller is using it.
 * The caller is responsible for preventing this.
 */
struct device_driver *driver_find(const char *name, struct bus_type *bus)
{
        struct kobject *k = kset_find_obj(bus->p->drivers_kset, name);
        struct driver_private *priv;

        if (k) {
                /* Drop reference added by kset_find_obj() */
                kobject_put(k);
                priv = to_driver(k);
                return priv->driver;
        }
        return NULL;
}
EXPORT_SYMBOL_GPL(driver_find);






/*
 * class.c - basic device class management
 *
 * Copyright (c) 2002-3 Patrick Mochel
 * Copyright (c) 2002-3 Open Source Development Labs
 * Copyright (c) 2003-2004 Greg Kroah-Hartman
 * Copyright (c) 2003-2004 IBM Corp.
 *
 * This file is released under the GPLv2
 *
 */

#include <linux/device.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/string.h>
#include <linux/kdev_t.h>
#include <linux/err.h>
#include <linux/slab.h>
#include <linux/genhd.h>
#include <linux/mutex.h>
#include "base.h"

#define to_class_attr(_attr) container_of(_attr, struct class_attribute, attr)

static ssize_t class_attr_show(struct kobject *kobj, struct attribute *attr,
                               char *buf)
{
        struct class_attribute *class_attr = to_class_attr(attr);
        struct subsys_private *cp = to_subsys_private(kobj);
        ssize_t ret = -EIO;

        if (class_attr->show)
                ret = class_attr->show(cp->class, class_attr, buf);
        return ret;
}

static ssize_t class_attr_store(struct kobject *kobj, struct attribute *attr,
                                const char *buf, size_t count)
{
        struct class_attribute *class_attr = to_class_attr(attr);
        struct subsys_private *cp = to_subsys_private(kobj);
        ssize_t ret = -EIO;

        if (class_attr->store)
                ret = class_attr->store(cp->class, class_attr, buf, count);
        return ret;
}

static void class_release(struct kobject *kobj)
{
        struct subsys_private *cp = to_subsys_private(kobj);
        struct class *class = cp->class;

        pr_debug("class '%s': release.\n", class->name);

        if (class->class_release)
                class->class_release(class);
        else
                pr_debug("class '%s' does not have a release() function, "
                         "be careful\n", class->name);

        kfree(cp);
}

static const struct kobj_ns_type_operations *class_child_ns_type(struct kobject *kobj)
{
        struct subsys_private *cp = to_subsys_private(kobj);
        struct class *class = cp->class;

        return class->ns_type;
}

static const struct sysfs_ops class_sysfs_ops = {
        .show      = class_attr_show,
        .store     = class_attr_store,
};

static struct kobj_type class_ktype = {
        .sysfs_ops      = &class_sysfs_ops,
        .release        = class_release,
        .child_ns_type  = class_child_ns_type,
};

/* Hotplug events for classes go to the class subsys */
static struct kset *class_kset;


int class_create_file_ns(struct class *cls, const struct class_attribute *attr,
                         const void *ns)
{
        int error;

        if (cls)
                error = sysfs_create_file_ns(&cls->p->subsys.kobj,
                                             &attr->attr, ns);
        else
                error = -EINVAL;
        return error;
}

void class_remove_file_ns(struct class *cls, const struct class_attribute *attr,
                          const void *ns)
{
        if (cls)
                sysfs_remove_file_ns(&cls->p->subsys.kobj, &attr->attr, ns);
}

static struct class *class_get(struct class *cls)
{
        if (cls)
                kset_get(&cls->p->subsys);
        return cls;
}

static void class_put(struct class *cls)
{
        if (cls)
                kset_put(&cls->p->subsys);
}

static int add_class_attrs(struct class *cls)
{
        int i;
        int error = 0;

        if (cls->class_attrs) {
                for (i = 0; cls->class_attrs[i].attr.name; i++) {
                        error = class_create_file(cls, &cls->class_attrs[i]);
                        if (error)
                                goto error;
                }
        }
done:
        return error;
error:
        while (--i >= 0)
                class_remove_file(cls, &cls->class_attrs[i]);
        goto done;
}

static void remove_class_attrs(struct class *cls)
{
        int i;

        if (cls->class_attrs) {
                for (i = 0; cls->class_attrs[i].attr.name; i++)
                        class_remove_file(cls, &cls->class_attrs[i]);
        }
}

static void klist_class_dev_get(struct klist_node *n)
{
        struct device *dev = container_of(n, struct device, knode_class);

        get_device(dev);
}

static void klist_class_dev_put(struct klist_node *n)
{
        struct device *dev = container_of(n, struct device, knode_class);

        put_device(dev);
}

int __class_register(struct class *cls, struct lock_class_key *key)
{
        struct subsys_private *cp;
        int error;

        pr_debug("device class '%s': registering\n", cls->name);

        cp = kzalloc(sizeof(*cp), GFP_KERNEL);
        if (!cp)
                return -ENOMEM;
        klist_init(&cp->klist_devices, klist_class_dev_get, klist_class_dev_put);
        INIT_LIST_HEAD(&cp->interfaces);
        kset_init(&cp->glue_dirs);
        __mutex_init(&cp->mutex, "subsys mutex", key);
        error = kobject_set_name(&cp->subsys.kobj, "%s", cls->name);
        if (error) {
                kfree(cp);
                return error;
        }

        /* set the default /sys/dev directory for devices of this class */
        if (!cls->dev_kobj)
                cls->dev_kobj = sysfs_dev_char_kobj;

#if defined(CONFIG_BLOCK)
        /* let the block class directory show up in the root of sysfs */
        if (!sysfs_deprecated || cls != &block_class)
                cp->subsys.kobj.kset = class_kset;
#else
        cp->subsys.kobj.kset = class_kset;
#endif
        cp->subsys.kobj.ktype = &class_ktype;
        cp->class = cls;
        cls->p = cp;

        error = kset_register(&cp->subsys);
        if (error) {
                kfree(cp);
                return error;
        }
        error = add_class_attrs(class_get(cls));
        class_put(cls);
        return error;
}
EXPORT_SYMBOL_GPL(__class_register);

void class_unregister(struct class *cls)
{
        pr_debug("device class '%s': unregistering\n", cls->name);
        remove_class_attrs(cls);
        kset_unregister(&cls->p->subsys);
}

static void class_create_release(struct class *cls)
{
        pr_debug("%s called for %s\n", __func__, cls->name);
        kfree(cls);
}

/**
 * class_create - create a struct class structure
 * @owner: pointer to the module that is to "own" this struct class
 * @name: pointer to a string for the name of this class.
 * @key: the lock_class_key for this class; used by mutex lock debugging
 *
 * This is used to create a struct class pointer that can then be used
 * in calls to device_create().
 *
 * Returns &struct class pointer on success, or ERR_PTR() on error.
 *
 * Note, the pointer created here is to be destroyed when finished by
 * making a call to class_destroy().
 */
struct class *__class_create(struct module *owner, const char *name,
                             struct lock_class_key *key)
{
        struct class *cls;
        int retval;

        cls = kzalloc(sizeof(*cls), GFP_KERNEL);
        if (!cls) {
                retval = -ENOMEM;
                goto error;
        }

        cls->name = name;
        cls->owner = owner;
        cls->class_release = class_create_release;

        retval = __class_register(cls, key);
        if (retval)
                goto error;

        return cls;

error:
        kfree(cls);
        return ERR_PTR(retval);
}
EXPORT_SYMBOL_GPL(__class_create);

/**
 * class_destroy - destroys a struct class structure
 * @cls: pointer to the struct class that is to be destroyed
 *
 * Note, the pointer to be destroyed must have been created with a call
 * to class_create().
 */
void class_destroy(struct class *cls)
{
        if ((cls == NULL) || (IS_ERR(cls)))
                return;

        class_unregister(cls);
}

/**
 * class_dev_iter_init - initialize class device iterator
 * @iter: class iterator to initialize
 * @class: the class we wanna iterate over
 * @start: the device to start iterating from, if any
 * @type: device_type of the devices to iterate over, NULL for all
 *
 * Initialize class iterator @iter such that it iterates over devices
 * of @class.  If @start is set, the list iteration will start there,
 * otherwise if it is NULL, the iteration starts at the beginning of
 * the list.
 */
void class_dev_iter_init(struct class_dev_iter *iter, struct class *class,
                         struct device *start, const struct device_type *type)
{
        struct klist_node *start_knode = NULL;

        if (start)
                start_knode = &start->knode_class;
        klist_iter_init_node(&class->p->klist_devices, &iter->ki, start_knode);
        iter->type = type;
}
EXPORT_SYMBOL_GPL(class_dev_iter_init);

/**
 * class_dev_iter_next - iterate to the next device
 * @iter: class iterator to proceed
 *
 * Proceed @iter to the next device and return it.  Returns NULL if
 * iteration is complete.
 *
 * The returned device is referenced and won't be released till
 * iterator is proceed to the next device or exited.  The caller is
 * free to do whatever it wants to do with the device including
 * calling back into class code.
 */
struct device *class_dev_iter_next(struct class_dev_iter *iter)
{
        struct klist_node *knode;
        struct device *dev;

        while (1) {
                knode = klist_next(&iter->ki);
                if (!knode)
                        return NULL;
                dev = container_of(knode, struct device, knode_class);
                if (!iter->type || iter->type == dev->type)
                        return dev;
        }
}
EXPORT_SYMBOL_GPL(class_dev_iter_next);

/**
 * class_dev_iter_exit - finish iteration
 * @iter: class iterator to finish
 *
 * Finish an iteration.  Always call this function after iteration is
 * complete whether the iteration ran till the end or not.
 */
void class_dev_iter_exit(struct class_dev_iter *iter)
{
        klist_iter_exit(&iter->ki);
}
EXPORT_SYMBOL_GPL(class_dev_iter_exit);

/**
 * class_for_each_device - device iterator
 * @class: the class we're iterating
 * @start: the device to start with in the list, if any.
 * @data: data for the callback
 * @fn: function to be called for each device
 *
 * Iterate over @class's list of devices, and call @fn for each,
 * passing it @data.  If @start is set, the list iteration will start
 * there, otherwise if it is NULL, the iteration starts at the
 * beginning of the list.
 *
 * We check the return of @fn each time. If it returns anything
 * other than 0, we break out and return that value.
 *
 * @fn is allowed to do anything including calling back into class
 * code.  There's no locking restriction.
 */
int class_for_each_device(struct class *class, struct device *start,
                          void *data, int (*fn)(struct device *, void *))
{
        struct class_dev_iter iter;
        struct device *dev;
        int error = 0;

        if (!class)
                return -EINVAL;
        if (!class->p) {
                WARN(1, "%s called for class '%s' before it was initialized",
                     __func__, class->name);
                return -EINVAL;
        }

        class_dev_iter_init(&iter, class, start, NULL);
        while ((dev = class_dev_iter_next(&iter))) {
                error = fn(dev, data);
                if (error)
                        break;
        }
        class_dev_iter_exit(&iter);

        return error;
}
EXPORT_SYMBOL_GPL(class_for_each_device);

/**
 * class_find_device - device iterator for locating a particular device
 * @class: the class we're iterating
 * @start: Device to begin with
 * @data: data for the match function
 * @match: function to check device
 *
 * This is similar to the class_for_each_dev() function above, but it
 * returns a reference to a device that is 'found' for later use, as
 * determined by the @match callback.
 *
 * The callback should return 0 if the device doesn't match and non-zero
 * if it does.  If the callback returns non-zero, this function will
 * return to the caller and not iterate over any more devices.
 *
 * Note, you will need to drop the reference with put_device() after use.
 *
 * @fn is allowed to do anything including calling back into class
 * code.  There's no locking restriction.
 */
struct device *class_find_device(struct class *class, struct device *start,
                                 const void *data,
                                 int (*match)(struct device *, const void *))
{
        struct class_dev_iter iter;
        struct device *dev;

        if (!class)
                return NULL;
        if (!class->p) {
                WARN(1, "%s called for class '%s' before it was initialized",
                     __func__, class->name);
                return NULL;
        }

        class_dev_iter_init(&iter, class, start, NULL);
        while ((dev = class_dev_iter_next(&iter))) {
                if (match(dev, data)) {
                        get_device(dev);
                        break;
                }
        }
        class_dev_iter_exit(&iter);

        return dev;
}
EXPORT_SYMBOL_GPL(class_find_device);

int class_interface_register(struct class_interface *class_intf)
{
        struct class *parent;
        struct class_dev_iter iter;
        struct device *dev;

        if (!class_intf || !class_intf->class)
                return -ENODEV;

        parent = class_get(class_intf->class);
        if (!parent)
                return -EINVAL;

        mutex_lock(&parent->p->mutex);
        list_add_tail(&class_intf->node, &parent->p->interfaces);
        if (class_intf->add_dev) {
                class_dev_iter_init(&iter, parent, NULL, NULL);
                while ((dev = class_dev_iter_next(&iter)))
                        class_intf->add_dev(dev, class_intf);
                class_dev_iter_exit(&iter);
        }
        mutex_unlock(&parent->p->mutex);

        return 0;
}

void class_interface_unregister(struct class_interface *class_intf)
{
        struct class *parent = class_intf->class;
        struct class_dev_iter iter;
        struct device *dev;

        if (!parent)
                return;

        mutex_lock(&parent->p->mutex);
        list_del_init(&class_intf->node);
        if (class_intf->remove_dev) {
                class_dev_iter_init(&iter, parent, NULL, NULL);
                while ((dev = class_dev_iter_next(&iter)))
                        class_intf->remove_dev(dev, class_intf);
                class_dev_iter_exit(&iter);
        }
        mutex_unlock(&parent->p->mutex);

        class_put(parent);
}

ssize_t show_class_attr_string(struct class *class,
                               struct class_attribute *attr, char *buf)
{
        struct class_attribute_string *cs;

        cs = container_of(attr, struct class_attribute_string, attr);
        return snprintf(buf, PAGE_SIZE, "%s\n", cs->str);
}

EXPORT_SYMBOL_GPL(show_class_attr_string);

struct class_compat {
        struct kobject *kobj;
};

/**
 * class_compat_register - register a compatibility class
 * @name: the name of the class
 *
 * Compatibility class are meant as a temporary user-space compatibility
 * workaround when converting a family of class devices to a bus devices.
 */
struct class_compat *class_compat_register(const char *name)
{
        struct class_compat *cls;

        cls = kmalloc(sizeof(struct class_compat), GFP_KERNEL);
        if (!cls)
                return NULL;
        cls->kobj = kobject_create_and_add(name, &class_kset->kobj);
        if (!cls->kobj) {
                kfree(cls);
                return NULL;
        }
        return cls;
}
EXPORT_SYMBOL_GPL(class_compat_register);

/**
 * class_compat_unregister - unregister a compatibility class
 * @cls: the class to unregister
 */
void class_compat_unregister(struct class_compat *cls)
{
        kobject_put(cls->kobj);
        kfree(cls);
}
EXPORT_SYMBOL_GPL(class_compat_unregister);

/**
 * class_compat_create_link - create a compatibility class device link to
 *                            a bus device
 * @cls: the compatibility class
 * @dev: the target bus device
 * @device_link: an optional device to which a "device" link should be created
 */
int class_compat_create_link(struct class_compat *cls, struct device *dev,
                             struct device *device_link)
{
        int error;

        error = sysfs_create_link(cls->kobj, &dev->kobj, dev_name(dev));
        if (error)
                return error;

        /*
         * Optionally add a "device" link (typically to the parent), as a
         * class device would have one and we want to provide as much
         * backwards compatibility as possible.
         */
        if (device_link) {
                error = sysfs_create_link(&dev->kobj, &device_link->kobj,
                                          "device");
                if (error)
                        sysfs_remove_link(cls->kobj, dev_name(dev));
        }

        return error;
}
EXPORT_SYMBOL_GPL(class_compat_create_link);

/**
 * class_compat_remove_link - remove a compatibility class device link to
 *                            a bus device
 * @cls: the compatibility class
 * @dev: the target bus device
 * @device_link: an optional device to which a "device" link was previously
 *               created
 */
void class_compat_remove_link(struct class_compat *cls, struct device *dev,
                              struct device *device_link)
{
        if (device_link)
                sysfs_remove_link(&dev->kobj, "device");
        sysfs_remove_link(cls->kobj, dev_name(dev));
}
EXPORT_SYMBOL_GPL(class_compat_remove_link);

int __init classes_init(void)
{
        class_kset = kset_create_and_add("class", NULL, NULL);
        if (!class_kset)
                return -ENOMEM;
        return 0;
}

EXPORT_SYMBOL_GPL(class_create_file_ns);
EXPORT_SYMBOL_GPL(class_remove_file_ns);
EXPORT_SYMBOL_GPL(class_unregister);
EXPORT_SYMBOL_GPL(class_destroy);

EXPORT_SYMBOL_GPL(class_interface_register);
EXPORT_SYMBOL_GPL(class_interface_unregister);

```
