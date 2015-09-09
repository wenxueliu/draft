
###all_pages 与 kmalloc vmalloc 的区别

系统初始化分配 DMA, NORMAL, 而 HIGHMEM 后续根据需要分配

###固定物理内存分配

伙伴系统

alloc_pages


##可变物理内存分配

目的: 小内存(小于 4K), 频繁内存申请与释放

cache_cache -> kmem_cache -> slab

**cache_cache**

    cache_sieze
    malloc_sizes

**kmame_cache**

    cache_size
    malloc_sizes

**slab**

    slabs_partial
    slabs_full
    slabs_free

**kmalloc**

    kmalloc
    kfree

    kmem_cache_create
    kmem_cache_init
    cache_chain


###虚拟内存分配

##参考

* 深入linux设备驱动程序内核机制

##附录

/* linux/gfp.h */

  1 #ifndef __LINUX_GFP_H
  2 #define __LINUX_GFP_H
  3 
  4 #include <linux/mmdebug.h>
  5 #include <linux/mmzone.h>
  6 #include <linux/stddef.h>
  7 #include <linux/linkage.h>
  8 #include <linux/topology.h>
  9 
 10 struct vm_area_struct;
 11 
 12 /* Plain integer GFP bitmasks. Do not use this directly. */
 13 #define ___GFP_DMA              0x01u
 14 #define ___GFP_HIGHMEM          0x02u
 15 #define ___GFP_DMA32            0x04u
 16 #define ___GFP_MOVABLE          0x08u
 17 #define ___GFP_WAIT             0x10u
 18 #define ___GFP_HIGH             0x20u
 19 #define ___GFP_IO               0x40u
 20 #define ___GFP_FS               0x80u
 21 #define ___GFP_COLD             0x100u
 22 #define ___GFP_NOWARN           0x200u
 23 #define ___GFP_REPEAT           0x400u
 24 #define ___GFP_NOFAIL           0x800u
 25 #define ___GFP_NORETRY          0x1000u
 26 #define ___GFP_MEMALLOC         0x2000u
 27 #define ___GFP_COMP             0x4000u
 28 #define ___GFP_ZERO             0x8000u
 29 #define ___GFP_NOMEMALLOC       0x10000u
 30 #define ___GFP_HARDWALL         0x20000u
 31 #define ___GFP_THISNODE         0x40000u
 32 #define ___GFP_RECLAIMABLE      0x80000u
 33 #define ___GFP_NOACCOUNT        0x100000u
 34 #define ___GFP_NOTRACK          0x200000u
 35 #define ___GFP_NO_KSWAPD        0x400000u
 36 #define ___GFP_OTHER_NODE       0x800000u
 37 #define ___GFP_WRITE            0x1000000u
 38 /* If the above are modified, __GFP_BITS_SHIFT may need updating */
 39 
 40 /*
 41  * GFP bitmasks..
 42  *
 43  * Zone modifiers (see linux/mmzone.h - low three bits)
 44  *
 45  * Do not put any conditional on these. If necessary modify the definitions
 46  * without the underscores and use them consistently. The definitions here may
 47  * be used in bit comparisons.
 48  */
 49 #define __GFP_DMA       ((__force gfp_t)___GFP_DMA)
 50 #define __GFP_HIGHMEM   ((__force gfp_t)___GFP_HIGHMEM)
 51 #define __GFP_DMA32     ((__force gfp_t)___GFP_DMA32)
 52 #define __GFP_MOVABLE   ((__force gfp_t)___GFP_MOVABLE)  /* Page is movable */
 53 #define GFP_ZONEMASK    (__GFP_DMA|__GFP_HIGHMEM|__GFP_DMA32|__GFP_MOVABLE)
 54 /*
 55  * Action modifiers - doesn't change the zoning
 56  *
 57  * __GFP_REPEAT: Try hard to allocate the memory, but the allocation attempt
 58  * _might_ fail.  This depends upon the particular VM implementation.
 59  *
 60  * __GFP_NOFAIL: The VM implementation _must_ retry infinitely: the caller
 61  * cannot handle allocation failures. New users should be evaluated carefully
 62  * (and the flag should be used only when there is no reasonable failure policy)
 63  * but it is definitely preferable to use the flag rather than opencode endless
 64  * loop around allocator.
 65  *
 66  * __GFP_NORETRY: The VM implementation must not retry indefinitely.
 67  *
 68  * __GFP_MOVABLE: Flag that this page will be movable by the page migration
 69  * mechanism or reclaimed
 70  */
 71 #define __GFP_WAIT      ((__force gfp_t)___GFP_WAIT)    /* Can wait and reschedule? */
 72 #define __GFP_HIGH      ((__force gfp_t)___GFP_HIGH)    /* Should access emergency pools? */
 73 #define __GFP_IO        ((__force gfp_t)___GFP_IO)      /* Can start physical IO? */
 74 #define __GFP_FS        ((__force gfp_t)___GFP_FS)      /* Can call down to low-level FS? */
 75 #define __GFP_COLD      ((__force gfp_t)___GFP_COLD)    /* Cache-cold page required */
 76 #define __GFP_NOWARN    ((__force gfp_t)___GFP_NOWARN)  /* Suppress page allocation failure warning */
 77 #define __GFP_REPEAT    ((__force gfp_t)___GFP_REPEAT)  /* See above */
 78 #define __GFP_NOFAIL    ((__force gfp_t)___GFP_NOFAIL)  /* See above */
 79 #define __GFP_NORETRY   ((__force gfp_t)___GFP_NORETRY) /* See above */
 80 #define __GFP_MEMALLOC  ((__force gfp_t)___GFP_MEMALLOC)/* Allow access to emergency reserves */
 81 #define __GFP_COMP      ((__force gfp_t)___GFP_COMP)    /* Add compound page metadata */
 82 #define __GFP_ZERO      ((__force gfp_t)___GFP_ZERO)    /* Return zeroed page on success */
 83 #define __GFP_NOMEMALLOC ((__force gfp_t)___GFP_NOMEMALLOC) /* Don't use emergency reserves.
 84                                                          * This takes precedence over the
 85                                                          * __GFP_MEMALLOC flag if both are
 86                                                          * set
 87                                                          */
 88 #define __GFP_HARDWALL   ((__force gfp_t)___GFP_HARDWALL) /* Enforce hardwall cpuset memory allocs */
 89 #define __GFP_THISNODE  ((__force gfp_t)___GFP_THISNODE)/* No fallback, no policies */
 90 #define __GFP_RECLAIMABLE ((__force gfp_t)___GFP_RECLAIMABLE) /* Page is reclaimable */
 91 #define __GFP_NOACCOUNT ((__force gfp_t)___GFP_NOACCOUNT) /* Don't account to kmemcg */
 92 #define __GFP_NOTRACK   ((__force gfp_t)___GFP_NOTRACK)  /* Don't track with kmemcheck */
 93 
 94 #define __GFP_NO_KSWAPD ((__force gfp_t)___GFP_NO_KSWAPD)
 95 #define __GFP_OTHER_NODE ((__force gfp_t)___GFP_OTHER_NODE) /* On behalf of other node */
 96 #define __GFP_WRITE     ((__force gfp_t)___GFP_WRITE)   /* Allocator intends to dirty page */
 97 
 98 /*
 99  * This may seem redundant, but it's a way of annotating false positives vs.
100  * allocations that simply cannot be supported (e.g. page tables).
101  */
102 #define __GFP_NOTRACK_FALSE_POSITIVE (__GFP_NOTRACK)
103 
104 #define __GFP_BITS_SHIFT 25     /* Room for N __GFP_FOO bits */
105 #define __GFP_BITS_MASK ((__force gfp_t)((1 << __GFP_BITS_SHIFT) - 1))
106 
107 /* This equals 0, but use constants in case they ever change */
108 #define GFP_NOWAIT      (GFP_ATOMIC & ~__GFP_HIGH)
109 /* GFP_ATOMIC means both !wait (__GFP_WAIT not set) and use emergency pool */
110 #define GFP_ATOMIC      (__GFP_HIGH)
111 #define GFP_NOIO        (__GFP_WAIT)
112 #define GFP_NOFS        (__GFP_WAIT | __GFP_IO)
113 #define GFP_KERNEL      (__GFP_WAIT | __GFP_IO | __GFP_FS)
114 #define GFP_TEMPORARY   (__GFP_WAIT | __GFP_IO | __GFP_FS | \
115                          __GFP_RECLAIMABLE)
116 #define GFP_USER        (__GFP_WAIT | __GFP_IO | __GFP_FS | __GFP_HARDWALL)
117 #define GFP_HIGHUSER    (GFP_USER | __GFP_HIGHMEM)
118 #define GFP_HIGHUSER_MOVABLE    (GFP_HIGHUSER | __GFP_MOVABLE)
119 #define GFP_IOFS        (__GFP_IO | __GFP_FS)
120 #define GFP_TRANSHUGE   (GFP_HIGHUSER_MOVABLE | __GFP_COMP | \
121                          __GFP_NOMEMALLOC | __GFP_NORETRY | __GFP_NOWARN | \
122                          __GFP_NO_KSWAPD)
123 
124 /* This mask makes up all the page movable related flags */
125 #define GFP_MOVABLE_MASK (__GFP_RECLAIMABLE|__GFP_MOVABLE)
126 
127 /* Control page allocator reclaim behavior */
128 #define GFP_RECLAIM_MASK (__GFP_WAIT|__GFP_HIGH|__GFP_IO|__GFP_FS|\
129                         __GFP_NOWARN|__GFP_REPEAT|__GFP_NOFAIL|\
130                         __GFP_NORETRY|__GFP_MEMALLOC|__GFP_NOMEMALLOC)
131 
132 /* Control slab gfp mask during early boot */
133 #define GFP_BOOT_MASK (__GFP_BITS_MASK & ~(__GFP_WAIT|__GFP_IO|__GFP_FS))
134 
135 /* Control allocation constraints */
136 #define GFP_CONSTRAINT_MASK (__GFP_HARDWALL|__GFP_THISNODE)
137 
138 /* Do not use these with a slab allocator */
139 #define GFP_SLAB_BUG_MASK (__GFP_DMA32|__GFP_HIGHMEM|~__GFP_BITS_MASK)
140 
141 /* Flag - indicates that the buffer will be suitable for DMA.  Ignored on some
142    platforms, used as appropriate on others */
143 
144 #define GFP_DMA         __GFP_DMA
145 
146 /* 4GB DMA on some platforms */
147 #define GFP_DMA32       __GFP_DMA32
148 
149 /* Convert GFP flags to their corresponding migrate type */
150 static inline int gfpflags_to_migratetype(const gfp_t gfp_flags)
151 {
152         WARN_ON((gfp_flags & GFP_MOVABLE_MASK) == GFP_MOVABLE_MASK);
153 
154         if (unlikely(page_group_by_mobility_disabled))
155                 return MIGRATE_UNMOVABLE;
156 
157         /* Group based on mobility */
158         return (((gfp_flags & __GFP_MOVABLE) != 0) << 1) |
159                 ((gfp_flags & __GFP_RECLAIMABLE) != 0);
160 }
161 
162 #ifdef CONFIG_HIGHMEM
163 #define OPT_ZONE_HIGHMEM ZONE_HIGHMEM
164 #else
165 #define OPT_ZONE_HIGHMEM ZONE_NORMAL
166 #endif
167 
168 #ifdef CONFIG_ZONE_DMA
169 #define OPT_ZONE_DMA ZONE_DMA
170 #else
171 #define OPT_ZONE_DMA ZONE_NORMAL
172 #endif
173 
174 #ifdef CONFIG_ZONE_DMA32
175 #define OPT_ZONE_DMA32 ZONE_DMA32
176 #else
177 #define OPT_ZONE_DMA32 ZONE_NORMAL
178 #endif
179 
180 /*
181  * GFP_ZONE_TABLE is a word size bitstring that is used for looking up the
182  * zone to use given the lowest 4 bits of gfp_t. Entries are ZONE_SHIFT long
183  * and there are 16 of them to cover all possible combinations of
184  * __GFP_DMA, __GFP_DMA32, __GFP_MOVABLE and __GFP_HIGHMEM.
185  *
186  * The zone fallback order is MOVABLE=>HIGHMEM=>NORMAL=>DMA32=>DMA.
187  * But GFP_MOVABLE is not only a zone specifier but also an allocation
188  * policy. Therefore __GFP_MOVABLE plus another zone selector is valid.
189  * Only 1 bit of the lowest 3 bits (DMA,DMA32,HIGHMEM) can be set to "1".
190  *
191  *       bit       result
192  *       =================
193  *       0x0    => NORMAL
194  *       0x1    => DMA or NORMAL
195  *       0x2    => HIGHMEM or NORMAL
196  *       0x3    => BAD (DMA+HIGHMEM)
197  *       0x4    => DMA32 or DMA or NORMAL
198  *       0x5    => BAD (DMA+DMA32)
199  *       0x6    => BAD (HIGHMEM+DMA32)
200  *       0x7    => BAD (HIGHMEM+DMA32+DMA)
201  *       0x8    => NORMAL (MOVABLE+0)
202  *       0x9    => DMA or NORMAL (MOVABLE+DMA)
203  *       0xa    => MOVABLE (Movable is valid only if HIGHMEM is set too)
204  *       0xb    => BAD (MOVABLE+HIGHMEM+DMA)
205  *       0xc    => DMA32 (MOVABLE+DMA32)
206  *       0xd    => BAD (MOVABLE+DMA32+DMA)
207  *       0xe    => BAD (MOVABLE+DMA32+HIGHMEM)
208  *       0xf    => BAD (MOVABLE+DMA32+HIGHMEM+DMA)
209  *
210  * ZONES_SHIFT must be <= 2 on 32 bit platforms.
211  */
212 
213 #if 16 * ZONES_SHIFT > BITS_PER_LONG
214 #error ZONES_SHIFT too large to create GFP_ZONE_TABLE integer
215 #endif
216 
217 #define GFP_ZONE_TABLE ( \
218         (ZONE_NORMAL << 0 * ZONES_SHIFT)                                      \
219         | (OPT_ZONE_DMA << ___GFP_DMA * ZONES_SHIFT)                          \
220         | (OPT_ZONE_HIGHMEM << ___GFP_HIGHMEM * ZONES_SHIFT)                  \
221         | (OPT_ZONE_DMA32 << ___GFP_DMA32 * ZONES_SHIFT)                      \
222         | (ZONE_NORMAL << ___GFP_MOVABLE * ZONES_SHIFT)                       \
223         | (OPT_ZONE_DMA << (___GFP_MOVABLE | ___GFP_DMA) * ZONES_SHIFT)       \
224         | (ZONE_MOVABLE << (___GFP_MOVABLE | ___GFP_HIGHMEM) * ZONES_SHIFT)   \
225         | (OPT_ZONE_DMA32 << (___GFP_MOVABLE | ___GFP_DMA32) * ZONES_SHIFT)   \
226 )
227 
228 /*
229  * GFP_ZONE_BAD is a bitmap for all combinations of __GFP_DMA, __GFP_DMA32
230  * __GFP_HIGHMEM and __GFP_MOVABLE that are not permitted. One flag per
231  * entry starting with bit 0. Bit is set if the combination is not
232  * allowed.
233  */
234 #define GFP_ZONE_BAD ( \
235         1 << (___GFP_DMA | ___GFP_HIGHMEM)                                    \
236         | 1 << (___GFP_DMA | ___GFP_DMA32)                                    \
237         | 1 << (___GFP_DMA32 | ___GFP_HIGHMEM)                                \
238         | 1 << (___GFP_DMA | ___GFP_DMA32 | ___GFP_HIGHMEM)                   \
239         | 1 << (___GFP_MOVABLE | ___GFP_HIGHMEM | ___GFP_DMA)                 \
240         | 1 << (___GFP_MOVABLE | ___GFP_DMA32 | ___GFP_DMA)                   \
241         | 1 << (___GFP_MOVABLE | ___GFP_DMA32 | ___GFP_HIGHMEM)               \
242         | 1 << (___GFP_MOVABLE | ___GFP_DMA32 | ___GFP_DMA | ___GFP_HIGHMEM)  \
243 )
244 
245 static inline enum zone_type gfp_zone(gfp_t flags)
246 {
247         enum zone_type z;
248         int bit = (__force int) (flags & GFP_ZONEMASK);
249 
250         z = (GFP_ZONE_TABLE >> (bit * ZONES_SHIFT)) &
251                                          ((1 << ZONES_SHIFT) - 1);
252         VM_BUG_ON((GFP_ZONE_BAD >> bit) & 1);
253         return z;
254 }
255 
256 /*
257  * There is only one page-allocator function, and two main namespaces to
258  * it. The alloc_page*() variants return 'struct page *' and as such
259  * can allocate highmem pages, the *get*page*() variants return
260  * virtual kernel addresses to the allocated page(s).
261  */
262 
263 static inline int gfp_zonelist(gfp_t flags)
264 {
265         if (IS_ENABLED(CONFIG_NUMA) && unlikely(flags & __GFP_THISNODE))
266                 return 1;
267 
268         return 0;
269 }
270 
271 /*
272  * We get the zone list from the current node and the gfp_mask.
273  * This zone list contains a maximum of MAXNODES*MAX_NR_ZONES zones.
274  * There are two zonelists per node, one for all zones with memory and
275  * one containing just zones from the node the zonelist belongs to.
276  *
277  * For the normal case of non-DISCONTIGMEM systems the NODE_DATA() gets
278  * optimized to &contig_page_data at compile-time.
279  */
280 static inline struct zonelist *node_zonelist(int nid, gfp_t flags)
281 {
282         return NODE_DATA(nid)->node_zonelists + gfp_zonelist(flags);
283 }
284 
285 #ifndef HAVE_ARCH_FREE_PAGE
286 static inline void arch_free_page(struct page *page, int order) { }
287 #endif
288 #ifndef HAVE_ARCH_ALLOC_PAGE
289 static inline void arch_alloc_page(struct page *page, int order) { }
290 #endif
291 
292 struct page *
293 __alloc_pages_nodemask(gfp_t gfp_mask, unsigned int order,
294                        struct zonelist *zonelist, nodemask_t *nodemask);
295 
296 static inline struct page *
297 __alloc_pages(gfp_t gfp_mask, unsigned int order,
298                 struct zonelist *zonelist)
299 {
300         return __alloc_pages_nodemask(gfp_mask, order, zonelist, NULL);
301 }
302 
303 static inline struct page *alloc_pages_node(int nid, gfp_t gfp_mask,
304                                                 unsigned int order)
305 {
306         /* Unknown node is current node */
307         if (nid < 0)
308                 nid = numa_node_id();
309 
310         return __alloc_pages(gfp_mask, order, node_zonelist(nid, gfp_mask));
311 }
312 
313 static inline struct page *alloc_pages_exact_node(int nid, gfp_t gfp_mask,
314                                                 unsigned int order)
315 {
316         VM_BUG_ON(nid < 0 || nid >= MAX_NUMNODES || !node_online(nid));
317 
318         return __alloc_pages(gfp_mask, order, node_zonelist(nid, gfp_mask));
319 }
320 
321 #ifdef CONFIG_NUMA
322 extern struct page *alloc_pages_current(gfp_t gfp_mask, unsigned order);
323 
324 static inline struct page *
325 alloc_pages(gfp_t gfp_mask, unsigned int order)
326 {
327         return alloc_pages_current(gfp_mask, order);
328 }
329 extern struct page *alloc_pages_vma(gfp_t gfp_mask, int order,
330                         struct vm_area_struct *vma, unsigned long addr,
331                         int node, bool hugepage);
332 #define alloc_hugepage_vma(gfp_mask, vma, addr, order)  \
333         alloc_pages_vma(gfp_mask, order, vma, addr, numa_node_id(), true)
334 #else
335 #define alloc_pages(gfp_mask, order) \
336                 alloc_pages_node(numa_node_id(), gfp_mask, order)
337 #define alloc_pages_vma(gfp_mask, order, vma, addr, node, false)\
338         alloc_pages(gfp_mask, order)
339 #define alloc_hugepage_vma(gfp_mask, vma, addr, order)  \
340         alloc_pages(gfp_mask, order)
341 #endif
342 #define alloc_page(gfp_mask) alloc_pages(gfp_mask, 0)
343 #define alloc_page_vma(gfp_mask, vma, addr)                     \
344         alloc_pages_vma(gfp_mask, 0, vma, addr, numa_node_id(), false)
345 #define alloc_page_vma_node(gfp_mask, vma, addr, node)          \
346         alloc_pages_vma(gfp_mask, 0, vma, addr, node, false)
347 
348 extern struct page *alloc_kmem_pages(gfp_t gfp_mask, unsigned int order);
349 extern struct page *alloc_kmem_pages_node(int nid, gfp_t gfp_mask,
350                                           unsigned int order);
351 
352 extern unsigned long __get_free_pages(gfp_t gfp_mask, unsigned int order);
353 extern unsigned long get_zeroed_page(gfp_t gfp_mask);
354 
355 void *alloc_pages_exact(size_t size, gfp_t gfp_mask);
356 void free_pages_exact(void *virt, size_t size);
357 /* This is different from alloc_pages_exact_node !!! */
358 void * __meminit alloc_pages_exact_nid(int nid, size_t size, gfp_t gfp_mask);
359 
360 #define __get_free_page(gfp_mask) \
361                 __get_free_pages((gfp_mask), 0)
362 
363 #define __get_dma_pages(gfp_mask, order) \
364                 __get_free_pages((gfp_mask) | GFP_DMA, (order))
365 
366 extern void __free_pages(struct page *page, unsigned int order);
367 extern void free_pages(unsigned long addr, unsigned int order);
368 extern void free_hot_cold_page(struct page *page, bool cold);
369 extern void free_hot_cold_page_list(struct list_head *list, bool cold);
370 
371 extern void __free_kmem_pages(struct page *page, unsigned int order);
372 extern void free_kmem_pages(unsigned long addr, unsigned int order);
373 
374 #define __free_page(page) __free_pages((page), 0)
375 #define free_page(addr) free_pages((addr), 0)
376 
377 void page_alloc_init(void);
378 void drain_zone_pages(struct zone *zone, struct per_cpu_pages *pcp);
379 void drain_all_pages(struct zone *zone);
380 void drain_local_pages(struct zone *zone);
381 
382 /*
383  * gfp_allowed_mask is set to GFP_BOOT_MASK during early boot to restrict what
384  * GFP flags are used before interrupts are enabled. Once interrupts are
385  * enabled, it is set to __GFP_BITS_MASK while the system is running. During
386  * hibernation, it is used by PM to avoid I/O during memory allocation while
387  * devices are suspended.
388  */
389 extern gfp_t gfp_allowed_mask;
390 
391 /* Returns true if the gfp_mask allows use of ALLOC_NO_WATERMARK */
392 bool gfp_pfmemalloc_allowed(gfp_t gfp_mask);
393 
394 extern void pm_restrict_gfp_mask(void);
395 extern void pm_restore_gfp_mask(void);
396 
397 #ifdef CONFIG_PM_SLEEP
398 extern bool pm_suspended_storage(void);
399 #else
400 static inline bool pm_suspended_storage(void)
401 {
402         return false;
403 }
404 #endif /* CONFIG_PM_SLEEP */
405 
406 #ifdef CONFIG_CMA
407 
408 /* The below functions must be run on a range from a single zone. */
409 extern int alloc_contig_range(unsigned long start, unsigned long end,
410                               unsigned migratetype);
411 extern void free_contig_range(unsigned long pfn, unsigned nr_pages);
412 
413 /* CMA stuff */
414 extern void init_cma_reserved_pageblock(struct page *page);
415 
416 #endif
417 
418 #endif /* __LINUX_GFP_H */
419 

/*slab.h*/
  1 /*
  2  * Written by Mark Hemment, 1996 (markhe@nextd.demon.co.uk).
  3  *
  4  * (C) SGI 2006, Christoph Lameter
  5  *      Cleaned up and restructured to ease the addition of alternative
  6  *      implementations of SLAB allocators.
  7  * (C) Linux Foundation 2008-2013
  8  *      Unified interface for all slab allocators
  9  */
 10 
 11 #ifndef _LINUX_SLAB_H
 12 #define _LINUX_SLAB_H
 13 
 14 #include <linux/gfp.h>
 15 #include <linux/types.h>
 16 #include <linux/workqueue.h>
 17 
 18 
 19 /*
 20  * Flags to pass to kmem_cache_create().
 21  * The ones marked DEBUG are only valid if CONFIG_DEBUG_SLAB is set.
 22  */
 23 #define SLAB_DEBUG_FREE         0x00000100UL    /* DEBUG: Perform (expensive) checks on free */
 24 #define SLAB_RED_ZONE           0x00000400UL    /* DEBUG: Red zone objs in a cache */
 25 #define SLAB_POISON             0x00000800UL    /* DEBUG: Poison objects */
 26 #define SLAB_HWCACHE_ALIGN      0x00002000UL    /* Align objs on cache lines */
 27 #define SLAB_CACHE_DMA          0x00004000UL    /* Use GFP_DMA memory */
 28 #define SLAB_STORE_USER         0x00010000UL    /* DEBUG: Store the last owner for bug hunting */
 29 #define SLAB_PANIC              0x00040000UL    /* Panic if kmem_cache_create() fails */
 30 /*
 31  * SLAB_DESTROY_BY_RCU - **WARNING** READ THIS!
 32  *
 33  * This delays freeing the SLAB page by a grace period, it does _NOT_
 34  * delay object freeing. This means that if you do kmem_cache_free()
 35  * that memory location is free to be reused at any time. Thus it may
 36  * be possible to see another object there in the same RCU grace period.
 37  *
 38  * This feature only ensures the memory location backing the object
 39  * stays valid, the trick to using this is relying on an independent
 40  * object validation pass. Something like:
 41  *
 42  *  rcu_read_lock()
 43  * again:
 44  *  obj = lockless_lookup(key);
 45  *  if (obj) {
 46  *    if (!try_get_ref(obj)) // might fail for free objects
 47  *      goto again;
 48  *
 49  *    if (obj->key != key) { // not the object we expected
 50  *      put_ref(obj);
 51  *      goto again;
 52  *    }
 53  *  }
 54  *  rcu_read_unlock();
 55  *
 56  * This is useful if we need to approach a kernel structure obliquely,
 57  * from its address obtained without the usual locking. We can lock
 58  * the structure to stabilize it and check it's still at the given address,
 59  * only if we can be sure that the memory has not been meanwhile reused
 60  * for some other kind of object (which our subsystem's lock might corrupt).
 61  *
 62  * rcu_read_lock before reading the address, then rcu_read_unlock after
 63  * taking the spinlock within the structure expected at that address.
 64  */
 65 #define SLAB_DESTROY_BY_RCU     0x00080000UL    /* Defer freeing slabs to RCU */
 66 #define SLAB_MEM_SPREAD         0x00100000UL    /* Spread some memory over cpuset */
 67 #define SLAB_TRACE              0x00200000UL    /* Trace allocations and frees */
 68 
 69 /* Flag to prevent checks on free */
 70 #ifdef CONFIG_DEBUG_OBJECTS
 71 # define SLAB_DEBUG_OBJECTS     0x00400000UL
 72 #else
 73 # define SLAB_DEBUG_OBJECTS     0x00000000UL
 74 #endif
 75 
 76 #define SLAB_NOLEAKTRACE        0x00800000UL    /* Avoid kmemleak tracing */
 77 
 78 /* Don't track use of uninitialized memory */
 79 #ifdef CONFIG_KMEMCHECK
 80 # define SLAB_NOTRACK           0x01000000UL
 81 #else
 82 # define SLAB_NOTRACK           0x00000000UL
 83 #endif
 84 #ifdef CONFIG_FAILSLAB
 85 # define SLAB_FAILSLAB          0x02000000UL    /* Fault injection mark */
 86 #else
 87 # define SLAB_FAILSLAB          0x00000000UL
 88 #endif
 89 
 90 /* The following flags affect the page allocator grouping pages by mobility */
 91 #define SLAB_RECLAIM_ACCOUNT    0x00020000UL            /* Objects are reclaimable */
 92 #define SLAB_TEMPORARY          SLAB_RECLAIM_ACCOUNT    /* Objects are short-lived */
 93 /*
 94  * ZERO_SIZE_PTR will be returned for zero sized kmalloc requests.
 95  *
 96  * Dereferencing ZERO_SIZE_PTR will lead to a distinct access fault.
 97  *
 98  * ZERO_SIZE_PTR can be passed to kfree though in the same way that NULL can.
 99  * Both make kfree a no-op.
100  */
101 #define ZERO_SIZE_PTR ((void *)16)
102 
103 #define ZERO_OR_NULL_PTR(x) ((unsigned long)(x) <= \
104                                 (unsigned long)ZERO_SIZE_PTR)
105 
106 #include <linux/kmemleak.h>
107 #include <linux/kasan.h>
108 
109 struct mem_cgroup;
110 /*
111  * struct kmem_cache related prototypes
112  */
113 void __init kmem_cache_init(void);
114 int slab_is_available(void);
115 
116 struct kmem_cache *kmem_cache_create(const char *, size_t, size_t,
117                         unsigned long,
118                         void (*)(void *));
119 void kmem_cache_destroy(struct kmem_cache *);
120 int kmem_cache_shrink(struct kmem_cache *);
121 
122 void memcg_create_kmem_cache(struct mem_cgroup *, struct kmem_cache *);
123 void memcg_deactivate_kmem_caches(struct mem_cgroup *);
124 void memcg_destroy_kmem_caches(struct mem_cgroup *);
125 
126 /*
127  * Please use this macro to create slab caches. Simply specify the
128  * name of the structure and maybe some flags that are listed above.
129  *
130  * The alignment of the struct determines object alignment. If you
131  * f.e. add ____cacheline_aligned_in_smp to the struct declaration
132  * then the objects will be properly aligned in SMP configurations.
133  */
134 #define KMEM_CACHE(__struct, __flags) kmem_cache_create(#__struct,\
135                 sizeof(struct __struct), __alignof__(struct __struct),\
136                 (__flags), NULL)
137 
138 /*
139  * Common kmalloc functions provided by all allocators
140  */
141 void * __must_check __krealloc(const void *, size_t, gfp_t);
142 void * __must_check krealloc(const void *, size_t, gfp_t);
143 void kfree(const void *);
144 void kzfree(const void *);
145 size_t ksize(const void *);
146 
147 /*
148  * Some archs want to perform DMA into kmalloc caches and need a guaranteed
149  * alignment larger than the alignment of a 64-bit integer.
150  * Setting ARCH_KMALLOC_MINALIGN in arch headers allows that.
151  */
152 #if defined(ARCH_DMA_MINALIGN) && ARCH_DMA_MINALIGN > 8
153 #define ARCH_KMALLOC_MINALIGN ARCH_DMA_MINALIGN
154 #define KMALLOC_MIN_SIZE ARCH_DMA_MINALIGN
155 #define KMALLOC_SHIFT_LOW ilog2(ARCH_DMA_MINALIGN)
156 #else
157 #define ARCH_KMALLOC_MINALIGN __alignof__(unsigned long long)
158 #endif
159 
160 /*
161  * Kmalloc array related definitions
162  */
163 
164 #ifdef CONFIG_SLAB
165 /*
166  * The largest kmalloc size supported by the SLAB allocators is
167  * 32 megabyte (2^25) or the maximum allocatable page order if that is
168  * less than 32 MB.
169  *
170  * WARNING: Its not easy to increase this value since the allocators have
171  * to do various tricks to work around compiler limitations in order to
172  * ensure proper constant folding.
173  */
174 #define KMALLOC_SHIFT_HIGH      ((MAX_ORDER + PAGE_SHIFT - 1) <= 25 ? \
175                                 (MAX_ORDER + PAGE_SHIFT - 1) : 25)
176 #define KMALLOC_SHIFT_MAX       KMALLOC_SHIFT_HIGH
177 #ifndef KMALLOC_SHIFT_LOW
178 #define KMALLOC_SHIFT_LOW       5
179 #endif
180 #endif
181 
182 #ifdef CONFIG_SLUB
183 /*
184  * SLUB directly allocates requests fitting in to an order-1 page
185  * (PAGE_SIZE*2).  Larger requests are passed to the page allocator.
186  */
187 #define KMALLOC_SHIFT_HIGH      (PAGE_SHIFT + 1)
188 #define KMALLOC_SHIFT_MAX       (MAX_ORDER + PAGE_SHIFT)
189 #ifndef KMALLOC_SHIFT_LOW
190 #define KMALLOC_SHIFT_LOW       3
191 #endif
192 #endif
193 
194 #ifdef CONFIG_SLOB
195 /*
196  * SLOB passes all requests larger than one page to the page allocator.
197  * No kmalloc array is necessary since objects of different sizes can
198  * be allocated from the same page.
199  */
200 #define KMALLOC_SHIFT_HIGH      PAGE_SHIFT
201 #define KMALLOC_SHIFT_MAX       30
202 #ifndef KMALLOC_SHIFT_LOW
203 #define KMALLOC_SHIFT_LOW       3
204 #endif
205 #endif
206 
207 /* Maximum allocatable size */
208 #define KMALLOC_MAX_SIZE        (1UL << KMALLOC_SHIFT_MAX)
209 /* Maximum size for which we actually use a slab cache */
210 #define KMALLOC_MAX_CACHE_SIZE  (1UL << KMALLOC_SHIFT_HIGH)
211 /* Maximum order allocatable via the slab allocagtor */
212 #define KMALLOC_MAX_ORDER       (KMALLOC_SHIFT_MAX - PAGE_SHIFT)
213 
214 /*
215  * Kmalloc subsystem.
216  */
217 #ifndef KMALLOC_MIN_SIZE
218 #define KMALLOC_MIN_SIZE (1 << KMALLOC_SHIFT_LOW)
219 #endif
220 
221 /*
222  * This restriction comes from byte sized index implementation.
223  * Page size is normally 2^12 bytes and, in this case, if we want to use
224  * byte sized index which can represent 2^8 entries, the size of the object
225  * should be equal or greater to 2^12 / 2^8 = 2^4 = 16.
226  * If minimum size of kmalloc is less than 16, we use it as minimum object
227  * size and give up to use byte sized index.
228  */
229 #define SLAB_OBJ_MIN_SIZE      (KMALLOC_MIN_SIZE < 16 ? \
230                                (KMALLOC_MIN_SIZE) : 16)
231 
232 #ifndef CONFIG_SLOB
233 extern struct kmem_cache *kmalloc_caches[KMALLOC_SHIFT_HIGH + 1];
234 #ifdef CONFIG_ZONE_DMA
235 extern struct kmem_cache *kmalloc_dma_caches[KMALLOC_SHIFT_HIGH + 1];
236 #endif
237 
238 /*
239  * Figure out which kmalloc slab an allocation of a certain size
240  * belongs to.
241  * 0 = zero alloc
242  * 1 =  65 .. 96 bytes
243  * 2 = 120 .. 192 bytes
244  * n = 2^(n-1) .. 2^n -1
245  */
246 static __always_inline int kmalloc_index(size_t size)
247 {
248         if (!size)
249                 return 0;
250 
251         if (size <= KMALLOC_MIN_SIZE)
252                 return KMALLOC_SHIFT_LOW;
253 
254         if (KMALLOC_MIN_SIZE <= 32 && size > 64 && size <= 96)
255                 return 1;
256         if (KMALLOC_MIN_SIZE <= 64 && size > 128 && size <= 192)
257                 return 2;
258         if (size <=          8) return 3;
259         if (size <=         16) return 4;
260         if (size <=         32) return 5;
261         if (size <=         64) return 6;
262         if (size <=        128) return 7;
263         if (size <=        256) return 8;
264         if (size <=        512) return 9;
265         if (size <=       1024) return 10;
266         if (size <=   2 * 1024) return 11;
267         if (size <=   4 * 1024) return 12;
268         if (size <=   8 * 1024) return 13;
269         if (size <=  16 * 1024) return 14;
270         if (size <=  32 * 1024) return 15;
271         if (size <=  64 * 1024) return 16;
272         if (size <= 128 * 1024) return 17;
273         if (size <= 256 * 1024) return 18;
274         if (size <= 512 * 1024) return 19;
275         if (size <= 1024 * 1024) return 20;
276         if (size <=  2 * 1024 * 1024) return 21;
277         if (size <=  4 * 1024 * 1024) return 22;
278         if (size <=  8 * 1024 * 1024) return 23;
279         if (size <=  16 * 1024 * 1024) return 24;
280         if (size <=  32 * 1024 * 1024) return 25;
281         if (size <=  64 * 1024 * 1024) return 26;
282         BUG();
283 
284         /* Will never be reached. Needed because the compiler may complain */
285         return -1;
286 }
287 #endif /* !CONFIG_SLOB */
288 
289 void *__kmalloc(size_t size, gfp_t flags);
290 void *kmem_cache_alloc(struct kmem_cache *, gfp_t flags);
291 void kmem_cache_free(struct kmem_cache *, void *);
292 
293 #ifdef CONFIG_NUMA
294 void *__kmalloc_node(size_t size, gfp_t flags, int node);
295 void *kmem_cache_alloc_node(struct kmem_cache *, gfp_t flags, int node);
296 #else
297 static __always_inline void *__kmalloc_node(size_t size, gfp_t flags, int node)
298 {
299         return __kmalloc(size, flags);
300 }
301 
302 static __always_inline void *kmem_cache_alloc_node(struct kmem_cache *s, gfp_t flags, int node)
303 {
304         return kmem_cache_alloc(s, flags);
305 }
306 #endif
307 
308 #ifdef CONFIG_TRACING
309 extern void *kmem_cache_alloc_trace(struct kmem_cache *, gfp_t, size_t);
310 
311 #ifdef CONFIG_NUMA
312 extern void *kmem_cache_alloc_node_trace(struct kmem_cache *s,
313                                            gfp_t gfpflags,
314                                            int node, size_t size);
315 #else
316 static __always_inline void *
317 kmem_cache_alloc_node_trace(struct kmem_cache *s,
318                               gfp_t gfpflags,
319                               int node, size_t size)
320 {
321         return kmem_cache_alloc_trace(s, gfpflags, size);
322 }
323 #endif /* CONFIG_NUMA */
324 
325 #else /* CONFIG_TRACING */
326 static __always_inline void *kmem_cache_alloc_trace(struct kmem_cache *s,
327                 gfp_t flags, size_t size)
328 {
329         void *ret = kmem_cache_alloc(s, flags);
330 
331         kasan_kmalloc(s, ret, size);
332         return ret;
333 }
334 
335 static __always_inline void *
336 kmem_cache_alloc_node_trace(struct kmem_cache *s,
337                               gfp_t gfpflags,
338                               int node, size_t size)
339 {
340         void *ret = kmem_cache_alloc_node(s, gfpflags, node);
341 
342         kasan_kmalloc(s, ret, size);
343         return ret;
344 }
345 #endif /* CONFIG_TRACING */
346 
347 extern void *kmalloc_order(size_t size, gfp_t flags, unsigned int order);
348 
349 #ifdef CONFIG_TRACING
350 extern void *kmalloc_order_trace(size_t size, gfp_t flags, unsigned int order);
351 #else
352 static __always_inline void *
353 kmalloc_order_trace(size_t size, gfp_t flags, unsigned int order)
354 {
355         return kmalloc_order(size, flags, order);
356 }
357 #endif
358 
359 static __always_inline void *kmalloc_large(size_t size, gfp_t flags)
360 {
361         unsigned int order = get_order(size);
362         return kmalloc_order_trace(size, flags, order);
363 }
364 
365 /**
366  * kmalloc - allocate memory
367  * @size: how many bytes of memory are required.
368  * @flags: the type of memory to allocate.
369  *
370  * kmalloc is the normal method of allocating memory
371  * for objects smaller than page size in the kernel.
372  *
373  * The @flags argument may be one of:
374  *
375  * %GFP_USER - Allocate memory on behalf of user.  May sleep.
376  *
377  * %GFP_KERNEL - Allocate normal kernel ram.  May sleep.
378  *
379  * %GFP_ATOMIC - Allocation will not sleep.  May use emergency pools.
380  *   For example, use this inside interrupt handlers.
381  *
382  * %GFP_HIGHUSER - Allocate pages from high memory.
383  *
384  * %GFP_NOIO - Do not do any I/O at all while trying to get memory.
385  *
386  * %GFP_NOFS - Do not make any fs calls while trying to get memory.
387  *
388  * %GFP_NOWAIT - Allocation will not sleep.
389  *
390  * %__GFP_THISNODE - Allocate node-local memory only.
391  *
392  * %GFP_DMA - Allocation suitable for DMA.
393  *   Should only be used for kmalloc() caches. Otherwise, use a
394  *   slab created with SLAB_DMA.
395  *
396  * Also it is possible to set different flags by OR'ing
397  * in one or more of the following additional @flags:
398  *
399  * %__GFP_COLD - Request cache-cold pages instead of
400  *   trying to return cache-warm pages.
401  *
402  * %__GFP_HIGH - This allocation has high priority and may use emergency pools.
403  *
404  * %__GFP_NOFAIL - Indicate that this allocation is in no way allowed to fail
405  *   (think twice before using).
406  *
407  * %__GFP_NORETRY - If memory is not immediately available,
408  *   then give up at once.
409  *
410  * %__GFP_NOWARN - If allocation fails, don't issue any warnings.
411  *
412  * %__GFP_REPEAT - If allocation fails initially, try once more before failing.
413  *
414  * There are other flags available as well, but these are not intended
415  * for general use, and so are not documented here. For a full list of
416  * potential flags, always refer to linux/gfp.h.
417  */
418 static __always_inline void *kmalloc(size_t size, gfp_t flags)
419 {
420         if (__builtin_constant_p(size)) {
421                 if (size > KMALLOC_MAX_CACHE_SIZE)
422                         return kmalloc_large(size, flags);
423 #ifndef CONFIG_SLOB
424                 if (!(flags & GFP_DMA)) {
425                         int index = kmalloc_index(size);
426 
427                         if (!index)
428                                 return ZERO_SIZE_PTR;
429 
430                         return kmem_cache_alloc_trace(kmalloc_caches[index],
431                                         flags, size);
432                 }
433 #endif
434         }
435         return __kmalloc(size, flags);
436 }
437 
438 /*
439  * Determine size used for the nth kmalloc cache.
440  * return size or 0 if a kmalloc cache for that
441  * size does not exist
442  */
443 static __always_inline int kmalloc_size(int n)
444 {
445 #ifndef CONFIG_SLOB
446         if (n > 2)
447                 return 1 << n;
448 
449         if (n == 1 && KMALLOC_MIN_SIZE <= 32)
450                 return 96;
451 
452         if (n == 2 && KMALLOC_MIN_SIZE <= 64)
453                 return 192;
454 #endif
455         return 0;
456 }
457 
458 static __always_inline void *kmalloc_node(size_t size, gfp_t flags, int node)
459 {
460 #ifndef CONFIG_SLOB
461         if (__builtin_constant_p(size) &&
462                 size <= KMALLOC_MAX_CACHE_SIZE && !(flags & GFP_DMA)) {
463                 int i = kmalloc_index(size);
464 
465                 if (!i)
466                         return ZERO_SIZE_PTR;
467 
468                 return kmem_cache_alloc_node_trace(kmalloc_caches[i],
469                                                 flags, node, size);
470         }
471 #endif
472         return __kmalloc_node(size, flags, node);
473 }
474 
475 /*
476  * Setting ARCH_SLAB_MINALIGN in arch headers allows a different alignment.
477  * Intended for arches that get misalignment faults even for 64 bit integer
478  * aligned buffers.
479  */
480 #ifndef ARCH_SLAB_MINALIGN
481 #define ARCH_SLAB_MINALIGN __alignof__(unsigned long long)
482 #endif
483 
484 struct memcg_cache_array {
485         struct rcu_head rcu;
486         struct kmem_cache *entries[0];
487 };
488 
489 /*
490  * This is the main placeholder for memcg-related information in kmem caches.
491  * Both the root cache and the child caches will have it. For the root cache,
492  * this will hold a dynamically allocated array large enough to hold
493  * information about the currently limited memcgs in the system. To allow the
494  * array to be accessed without taking any locks, on relocation we free the old
495  * version only after a grace period.
496  *
497  * Child caches will hold extra metadata needed for its operation. Fields are:
498  *
499  * @memcg: pointer to the memcg this cache belongs to
500  * @root_cache: pointer to the global, root cache, this cache was derived from
501  *
502  * Both root and child caches of the same kind are linked into a list chained
503  * through @list.
504  */
505 struct memcg_cache_params {
506         bool is_root_cache;
507         struct list_head list;
508         union {
509                 struct memcg_cache_array __rcu *memcg_caches;
510                 struct {
511                         struct mem_cgroup *memcg;
512                         struct kmem_cache *root_cache;
513                 };
514         };
515 };
516 
517 int memcg_update_all_caches(int num_memcgs);
518 
519 /**
520  * kmalloc_array - allocate memory for an array.
521  * @n: number of elements.
522  * @size: element size.
523  * @flags: the type of memory to allocate (see kmalloc).
524  */
525 static inline void *kmalloc_array(size_t n, size_t size, gfp_t flags)
526 {
527         if (size != 0 && n > SIZE_MAX / size)
528                 return NULL;
529         return __kmalloc(n * size, flags);
530 }
531 
532 /**
533  * kcalloc - allocate memory for an array. The memory is set to zero.
534  * @n: number of elements.
535  * @size: element size.
536  * @flags: the type of memory to allocate (see kmalloc).
537  */
538 static inline void *kcalloc(size_t n, size_t size, gfp_t flags)
539 {
540         return kmalloc_array(n, size, flags | __GFP_ZERO);
541 }
542 
543 /*
544  * kmalloc_track_caller is a special version of kmalloc that records the
545  * calling function of the routine calling it for slab leak tracking instead
546  * of just the calling function (confusing, eh?).
547  * It's useful when the call to kmalloc comes from a widely-used standard
548  * allocator where we care about the real place the memory allocation
549  * request comes from.
550  */
551 extern void *__kmalloc_track_caller(size_t, gfp_t, unsigned long);
552 #define kmalloc_track_caller(size, flags) \
553         __kmalloc_track_caller(size, flags, _RET_IP_)
554 
555 #ifdef CONFIG_NUMA
556 extern void *__kmalloc_node_track_caller(size_t, gfp_t, int, unsigned long);
557 #define kmalloc_node_track_caller(size, flags, node) \
558         __kmalloc_node_track_caller(size, flags, node, \
559                         _RET_IP_)
560 
561 #else /* CONFIG_NUMA */
562 
563 #define kmalloc_node_track_caller(size, flags, node) \
564         kmalloc_track_caller(size, flags)
565 
566 #endif /* CONFIG_NUMA */
567 
568 /*
569  * Shortcuts
570  */
571 static inline void *kmem_cache_zalloc(struct kmem_cache *k, gfp_t flags)
572 {
573         return kmem_cache_alloc(k, flags | __GFP_ZERO);
574 }
575 
576 /**
577  * kzalloc - allocate memory. The memory is set to zero.
578  * @size: how many bytes of memory are required.
579  * @flags: the type of memory to allocate (see kmalloc).
580  */
581 static inline void *kzalloc(size_t size, gfp_t flags)
582 {
583         return kmalloc(size, flags | __GFP_ZERO);
584 }
585 
586 /**
587  * kzalloc_node - allocate zeroed memory from a particular memory node.
588  * @size: how many bytes of memory are required.
589  * @flags: the type of memory to allocate (see kmalloc).
590  * @node: memory node from which to allocate
591  */
592 static inline void *kzalloc_node(size_t size, gfp_t flags, int node)
593 {
594         return kmalloc_node(size, flags | __GFP_ZERO, node);
595 }
596 
597 unsigned int kmem_cache_size(struct kmem_cache *s);
598 void __init kmem_cache_init_late(void);
599 
600 #endif  /* _LINUX_SLAB_H */
601 


/* sla_common.c */
  1 /*
  2  * Slab allocator functions that are independent of the allocator strategy
  3  *
  4  * (C) 2012 Christoph Lameter <cl@linux.com>
  5  */
  6 #include <linux/slab.h>
  7 
  8 #include <linux/mm.h>
  9 #include <linux/poison.h>
 10 #include <linux/interrupt.h>
 11 #include <linux/memory.h>
 12 #include <linux/compiler.h>
 13 #include <linux/module.h>
 14 #include <linux/cpu.h>
 15 #include <linux/uaccess.h>
 16 #include <linux/seq_file.h>
 17 #include <linux/proc_fs.h>
 18 #include <asm/cacheflush.h>
 19 #include <asm/tlbflush.h>
 20 #include <asm/page.h>
 21 #include <linux/memcontrol.h>
 22 
 23 #define CREATE_TRACE_POINTS
 24 #include <trace/events/kmem.h>
 25 
 26 #include "slab.h"
 27 
 28 enum slab_state slab_state;
 29 LIST_HEAD(slab_caches);
 30 DEFINE_MUTEX(slab_mutex);
 31 struct kmem_cache *kmem_cache;
 32 
 33 /*
 34  * Set of flags that will prevent slab merging
 35  */
 36 #define SLAB_NEVER_MERGE (SLAB_RED_ZONE | SLAB_POISON | SLAB_STORE_USER | \
 37                 SLAB_TRACE | SLAB_DESTROY_BY_RCU | SLAB_NOLEAKTRACE | \
 38                 SLAB_FAILSLAB)
 39 
 40 #define SLAB_MERGE_SAME (SLAB_DEBUG_FREE | SLAB_RECLAIM_ACCOUNT | \
 41                 SLAB_CACHE_DMA | SLAB_NOTRACK)
 42 
 43 /*
 44  * Merge control. If this is set then no merging of slab caches will occur.
 45  * (Could be removed. This was introduced to pacify the merge skeptics.)
 46  */
 47 static int slab_nomerge;
 48 
 49 static int __init setup_slab_nomerge(char *str)
 50 {
 51         slab_nomerge = 1;
 52         return 1;
 53 }
 54 
 55 #ifdef CONFIG_SLUB
 56 __setup_param("slub_nomerge", slub_nomerge, setup_slab_nomerge, 0);
 57 #endif
 58 
 59 __setup("slab_nomerge", setup_slab_nomerge);
 60 
 61 /*
 62  * Determine the size of a slab object
 63  */
 64 unsigned int kmem_cache_size(struct kmem_cache *s)
 65 {
 66         return s->object_size;
 67 }
 68 EXPORT_SYMBOL(kmem_cache_size);
 69 
 70 #ifdef CONFIG_DEBUG_VM
 71 static int kmem_cache_sanity_check(const char *name, size_t size)
 72 {
 73         struct kmem_cache *s = NULL;
 74 
 75         if (!name || in_interrupt() || size < sizeof(void *) ||
 76                 size > KMALLOC_MAX_SIZE) {
 77                 pr_err("kmem_cache_create(%s) integrity check failed\n", name);
 78                 return -EINVAL;
 79         }
 80 
 81         list_for_each_entry(s, &slab_caches, list) {
 82                 char tmp;
 83                 int res;
 84 
 85                 /*
 86                  * This happens when the module gets unloaded and doesn't
 87                  * destroy its slab cache and no-one else reuses the vmalloc
 88                  * area of the module.  Print a warning.
 89                  */
 90                 res = probe_kernel_address(s->name, tmp);
 91                 if (res) {
 92                         pr_err("Slab cache with size %d has lost its name\n",
 93                                s->object_size);
 94                         continue;
 95                 }
 96         }
 97 
 98         WARN_ON(strchr(name, ' '));     /* It confuses parsers */
 99         return 0;
100 }
101 #else
102 static inline int kmem_cache_sanity_check(const char *name, size_t size)
103 {
104         return 0;
105 }
106 #endif
107 
108 #ifdef CONFIG_MEMCG_KMEM
109 void slab_init_memcg_params(struct kmem_cache *s)
110 {
111         s->memcg_params.is_root_cache = true;
112         INIT_LIST_HEAD(&s->memcg_params.list);
113         RCU_INIT_POINTER(s->memcg_params.memcg_caches, NULL);
114 }
115 
116 static int init_memcg_params(struct kmem_cache *s,
117                 struct mem_cgroup *memcg, struct kmem_cache *root_cache)
118 {
119         struct memcg_cache_array *arr;
120 
121         if (memcg) {
122                 s->memcg_params.is_root_cache = false;
123                 s->memcg_params.memcg = memcg;
124                 s->memcg_params.root_cache = root_cache;
125                 return 0;
126         }
127 
128         slab_init_memcg_params(s);
129 
130         if (!memcg_nr_cache_ids)
131                 return 0;
132 
133         arr = kzalloc(sizeof(struct memcg_cache_array) +
134                       memcg_nr_cache_ids * sizeof(void *),
135                       GFP_KERNEL);
136         if (!arr)
137                 return -ENOMEM;
138 
139         RCU_INIT_POINTER(s->memcg_params.memcg_caches, arr);
140         return 0;
141 }
142 
143 static void destroy_memcg_params(struct kmem_cache *s)
144 {
145         if (is_root_cache(s))
146                 kfree(rcu_access_pointer(s->memcg_params.memcg_caches));
147 }
148 
149 static int update_memcg_params(struct kmem_cache *s, int new_array_size)
150 {
151         struct memcg_cache_array *old, *new;
152 
153         if (!is_root_cache(s))
154                 return 0;
155 
156         new = kzalloc(sizeof(struct memcg_cache_array) +
157                       new_array_size * sizeof(void *), GFP_KERNEL);
158         if (!new)
159                 return -ENOMEM;
160 
161         old = rcu_dereference_protected(s->memcg_params.memcg_caches,
162                                         lockdep_is_held(&slab_mutex));
163         if (old)
164                 memcpy(new->entries, old->entries,
165                        memcg_nr_cache_ids * sizeof(void *));
166 
167         rcu_assign_pointer(s->memcg_params.memcg_caches, new);
168         if (old)
169                 kfree_rcu(old, rcu);
170         return 0;
171 }
172 
173 int memcg_update_all_caches(int num_memcgs)
174 {
175         struct kmem_cache *s;
176         int ret = 0;
177 
178         mutex_lock(&slab_mutex);
179         list_for_each_entry(s, &slab_caches, list) {
180                 ret = update_memcg_params(s, num_memcgs);
181                 /*
182                  * Instead of freeing the memory, we'll just leave the caches
183                  * up to this point in an updated state.
184                  */
185                 if (ret)
186                         break;
187         }
188         mutex_unlock(&slab_mutex);
189         return ret;
190 }
191 #else
192 static inline int init_memcg_params(struct kmem_cache *s,
193                 struct mem_cgroup *memcg, struct kmem_cache *root_cache)
194 {
195         return 0;
196 }
197 
198 static inline void destroy_memcg_params(struct kmem_cache *s)
199 {
200 }
201 #endif /* CONFIG_MEMCG_KMEM */
202 
203 /*
204  * Find a mergeable slab cache
205  */
206 int slab_unmergeable(struct kmem_cache *s)
207 {
208         if (slab_nomerge || (s->flags & SLAB_NEVER_MERGE))
209                 return 1;
210 
211         if (!is_root_cache(s))
212                 return 1;
213 
214         if (s->ctor)
215                 return 1;
216 
217         /*
218          * We may have set a slab to be unmergeable during bootstrap.
219          */
220         if (s->refcount < 0)
221                 return 1;
222 
223         return 0;
224 }
225 
226 struct kmem_cache *find_mergeable(size_t size, size_t align,
227                 unsigned long flags, const char *name, void (*ctor)(void *))
228 {
229         struct kmem_cache *s;
230 
231         if (slab_nomerge || (flags & SLAB_NEVER_MERGE))
232                 return NULL;
233 
234         if (ctor)
235                 return NULL;
236 
237         size = ALIGN(size, sizeof(void *));
238         align = calculate_alignment(flags, align, size);
239         size = ALIGN(size, align);
240         flags = kmem_cache_flags(size, flags, name, NULL);
241 
242         list_for_each_entry_reverse(s, &slab_caches, list) {
243                 if (slab_unmergeable(s))
244                         continue;
245 
246                 if (size > s->size)
247                         continue;
248 
249                 if ((flags & SLAB_MERGE_SAME) != (s->flags & SLAB_MERGE_SAME))
250                         continue;
251                 /*
252                  * Check if alignment is compatible.
253                  * Courtesy of Adrian Drzewiecki
254                  */
255                 if ((s->size & ~(align - 1)) != s->size)
256                         continue;
257 
258                 if (s->size - size >= sizeof(void *))
259                         continue;
260 
261                 if (IS_ENABLED(CONFIG_SLAB) && align &&
262                         (align > s->align || s->align % align))
263                         continue;
264 
265                 return s;
266         }
267         return NULL;
268 }
269 
270 /*
271  * Figure out what the alignment of the objects will be given a set of
272  * flags, a user specified alignment and the size of the objects.
273  */
274 unsigned long calculate_alignment(unsigned long flags,
275                 unsigned long align, unsigned long size)
276 {
277         /*
278          * If the user wants hardware cache aligned objects then follow that
279          * suggestion if the object is sufficiently large.
280          *
281          * The hardware cache alignment cannot override the specified
282          * alignment though. If that is greater then use it.
283          */
284         if (flags & SLAB_HWCACHE_ALIGN) {
285                 unsigned long ralign = cache_line_size();
286                 while (size <= ralign / 2)
287                         ralign /= 2;
288                 align = max(align, ralign);
289         }
290 
291         if (align < ARCH_SLAB_MINALIGN)
292                 align = ARCH_SLAB_MINALIGN;
293 
294         return ALIGN(align, sizeof(void *));
295 }
296 
297 static struct kmem_cache *
298 do_kmem_cache_create(const char *name, size_t object_size, size_t size,
299                      size_t align, unsigned long flags, void (*ctor)(void *),
300                      struct mem_cgroup *memcg, struct kmem_cache *root_cache)
301 {
302         struct kmem_cache *s;
303         int err;
304 
305         err = -ENOMEM;
306         s = kmem_cache_zalloc(kmem_cache, GFP_KERNEL);
307         if (!s)
308                 goto out;
309 
310         s->name = name;
311         s->object_size = object_size;
312         s->size = size;
313         s->align = align;
314         s->ctor = ctor;
315 
316         err = init_memcg_params(s, memcg, root_cache);
317         if (err)
318                 goto out_free_cache;
319 
320         err = __kmem_cache_create(s, flags);
321         if (err)
322                 goto out_free_cache;
323 
324         s->refcount = 1;
325         list_add(&s->list, &slab_caches);
326 out:
327         if (err)
328                 return ERR_PTR(err);
329         return s;
330 
331 out_free_cache:
332         destroy_memcg_params(s);
333         kmem_cache_free(kmem_cache, s);
334         goto out;
335 }
336 
337 /*
338  * kmem_cache_create - Create a cache.
339  * @name: A string which is used in /proc/slabinfo to identify this cache.
340  * @size: The size of objects to be created in this cache.
341  * @align: The required alignment for the objects.
342  * @flags: SLAB flags
343  * @ctor: A constructor for the objects.
344  *
345  * Returns a ptr to the cache on success, NULL on failure.
346  * Cannot be called within a interrupt, but can be interrupted.
347  * The @ctor is run when new pages are allocated by the cache.
348  *
349  * The flags are
350  *
351  * %SLAB_POISON - Poison the slab with a known test pattern (a5a5a5a5)
352  * to catch references to uninitialised memory.
353  *
354  * %SLAB_RED_ZONE - Insert `Red' zones around the allocated memory to check
355  * for buffer overruns.
356  *
357  * %SLAB_HWCACHE_ALIGN - Align the objects in this cache to a hardware
358  * cacheline.  This can be beneficial if you're counting cycles as closely
359  * as davem.
360  */
361 struct kmem_cache *
362 kmem_cache_create(const char *name, size_t size, size_t align,
363                   unsigned long flags, void (*ctor)(void *))
364 {
365         struct kmem_cache *s;
366         const char *cache_name;
367         int err;
368 
369         get_online_cpus();
370         get_online_mems();
371         memcg_get_cache_ids();
372 
373         mutex_lock(&slab_mutex);
374 
375         err = kmem_cache_sanity_check(name, size);
376         if (err) {
377                 s = NULL;       /* suppress uninit var warning */
378                 goto out_unlock;
379         }
380 
381         /*
382          * Some allocators will constraint the set of valid flags to a subset
383          * of all flags. We expect them to define CACHE_CREATE_MASK in this
384          * case, and we'll just provide them with a sanitized version of the
385          * passed flags.
386          */
387         flags &= CACHE_CREATE_MASK;
388 
389         s = __kmem_cache_alias(name, size, align, flags, ctor);
390         if (s)
391                 goto out_unlock;
392 
393         cache_name = kstrdup_const(name, GFP_KERNEL);
394         if (!cache_name) {
395                 err = -ENOMEM;
396                 goto out_unlock;
397         }
398 
399         s = do_kmem_cache_create(cache_name, size, size,
400                                  calculate_alignment(flags, align, size),
401                                  flags, ctor, NULL, NULL);
402         if (IS_ERR(s)) {
403                 err = PTR_ERR(s);
404                 kfree_const(cache_name);
405         }
406 
407 out_unlock:
408         mutex_unlock(&slab_mutex);
409 
410         memcg_put_cache_ids();
411         put_online_mems();
412         put_online_cpus();
413 
414         if (err) {
415                 if (flags & SLAB_PANIC)
416                         panic("kmem_cache_create: Failed to create slab '%s'. Error %d\n",
417                                 name, err);
418                 else {
419                         printk(KERN_WARNING "kmem_cache_create(%s) failed with error %d",
420                                 name, err);
421                         dump_stack();
422                 }
423                 return NULL;
424         }
425         return s;
426 }
427 EXPORT_SYMBOL(kmem_cache_create);
428 
429 static int do_kmem_cache_shutdown(struct kmem_cache *s,
430                 struct list_head *release, bool *need_rcu_barrier)
431 {
432         if (__kmem_cache_shutdown(s) != 0) {
433                 printk(KERN_ERR "kmem_cache_destroy %s: "
434                        "Slab cache still has objects\n", s->name);
435                 dump_stack();
436                 return -EBUSY;
437         }
438 
439         if (s->flags & SLAB_DESTROY_BY_RCU)
440                 *need_rcu_barrier = true;
441 
442 #ifdef CONFIG_MEMCG_KMEM
443         if (!is_root_cache(s))
444                 list_del(&s->memcg_params.list);
445 #endif
446         list_move(&s->list, release);
447         return 0;
448 }
449 
450 static void do_kmem_cache_release(struct list_head *release,
451                                   bool need_rcu_barrier)
452 {
453         struct kmem_cache *s, *s2;
454 
455         if (need_rcu_barrier)
456                 rcu_barrier();
457 
458         list_for_each_entry_safe(s, s2, release, list) {
459 #ifdef SLAB_SUPPORTS_SYSFS
460                 sysfs_slab_remove(s);
461 #else
462                 slab_kmem_cache_release(s);
463 #endif
464         }
465 }
466 
467 #ifdef CONFIG_MEMCG_KMEM
468 /*
469  * memcg_create_kmem_cache - Create a cache for a memory cgroup.
470  * @memcg: The memory cgroup the new cache is for.
471  * @root_cache: The parent of the new cache.
472  *
473  * This function attempts to create a kmem cache that will serve allocation
474  * requests going from @memcg to @root_cache. The new cache inherits properties
475  * from its parent.
476  */
477 void memcg_create_kmem_cache(struct mem_cgroup *memcg,
478                              struct kmem_cache *root_cache)
479 {
480         static char memcg_name_buf[NAME_MAX + 1]; /* protected by slab_mutex */
481         struct cgroup_subsys_state *css = mem_cgroup_css(memcg);
482         struct memcg_cache_array *arr;
483         struct kmem_cache *s = NULL;
484         char *cache_name;
485         int idx;
486 
487         get_online_cpus();
488         get_online_mems();
489 
490         mutex_lock(&slab_mutex);
491 
492         /*
493          * The memory cgroup could have been deactivated while the cache
494          * creation work was pending.
495          */
496         if (!memcg_kmem_is_active(memcg))
497                 goto out_unlock;
498 
499         idx = memcg_cache_id(memcg);
500         arr = rcu_dereference_protected(root_cache->memcg_params.memcg_caches,
501                                         lockdep_is_held(&slab_mutex));
502 
503         /*
504          * Since per-memcg caches are created asynchronously on first
505          * allocation (see memcg_kmem_get_cache()), several threads can try to
506          * create the same cache, but only one of them may succeed.
507          */
508         if (arr->entries[idx])
509                 goto out_unlock;
510 
511         cgroup_name(css->cgroup, memcg_name_buf, sizeof(memcg_name_buf));
512         cache_name = kasprintf(GFP_KERNEL, "%s(%d:%s)", root_cache->name,
513                                css->id, memcg_name_buf);
514         if (!cache_name)
515                 goto out_unlock;
516 
517         s = do_kmem_cache_create(cache_name, root_cache->object_size,
518                                  root_cache->size, root_cache->align,
519                                  root_cache->flags, root_cache->ctor,
520                                  memcg, root_cache);
521         /*
522          * If we could not create a memcg cache, do not complain, because
523          * that's not critical at all as we can always proceed with the root
524          * cache.
525          */
526         if (IS_ERR(s)) {
527                 kfree(cache_name);
528                 goto out_unlock;
529         }
530 
531         list_add(&s->memcg_params.list, &root_cache->memcg_params.list);
532 
533         /*
534          * Since readers won't lock (see cache_from_memcg_idx()), we need a
535          * barrier here to ensure nobody will see the kmem_cache partially
536          * initialized.
537          */
538         smp_wmb();
539         arr->entries[idx] = s;
540 
541 out_unlock:
542         mutex_unlock(&slab_mutex);
543 
544         put_online_mems();
545         put_online_cpus();
546 }
547 
548 void memcg_deactivate_kmem_caches(struct mem_cgroup *memcg)
549 {
550         int idx;
551         struct memcg_cache_array *arr;
552         struct kmem_cache *s, *c;
553 
554         idx = memcg_cache_id(memcg);
555 
556         get_online_cpus();
557         get_online_mems();
558 
559         mutex_lock(&slab_mutex);
560         list_for_each_entry(s, &slab_caches, list) {
561                 if (!is_root_cache(s))
562                         continue;
563 
564                 arr = rcu_dereference_protected(s->memcg_params.memcg_caches,
565                                                 lockdep_is_held(&slab_mutex));
566                 c = arr->entries[idx];
567                 if (!c)
568                         continue;
569 
570                 __kmem_cache_shrink(c, true);
571                 arr->entries[idx] = NULL;
572         }
573         mutex_unlock(&slab_mutex);
574 
575         put_online_mems();
576         put_online_cpus();
577 }
578 
579 void memcg_destroy_kmem_caches(struct mem_cgroup *memcg)
580 {
581         LIST_HEAD(release);
582         bool need_rcu_barrier = false;
583         struct kmem_cache *s, *s2;
584 
585         get_online_cpus();
586         get_online_mems();
587 
588         mutex_lock(&slab_mutex);
589         list_for_each_entry_safe(s, s2, &slab_caches, list) {
590                 if (is_root_cache(s) || s->memcg_params.memcg != memcg)
591                         continue;
592                 /*
593                  * The cgroup is about to be freed and therefore has no charges
594                  * left. Hence, all its caches must be empty by now.
595                  */
596                 BUG_ON(do_kmem_cache_shutdown(s, &release, &need_rcu_barrier));
597         }
598         mutex_unlock(&slab_mutex);
599 
600         put_online_mems();
601         put_online_cpus();
602 
603         do_kmem_cache_release(&release, need_rcu_barrier);
604 }
605 #endif /* CONFIG_MEMCG_KMEM */
606 
607 void slab_kmem_cache_release(struct kmem_cache *s)
608 {
609         destroy_memcg_params(s);
610         kfree_const(s->name);
611         kmem_cache_free(kmem_cache, s);
612 }
613 
614 void kmem_cache_destroy(struct kmem_cache *s)
615 {
616         struct kmem_cache *c, *c2;
617         LIST_HEAD(release);
618         bool need_rcu_barrier = false;
619         bool busy = false;
620 
621         BUG_ON(!is_root_cache(s));
622 
623         get_online_cpus();
624         get_online_mems();
625 
626         mutex_lock(&slab_mutex);
627 
628         s->refcount--;
629         if (s->refcount)
630                 goto out_unlock;
631 
632         for_each_memcg_cache_safe(c, c2, s) {
633                 if (do_kmem_cache_shutdown(c, &release, &need_rcu_barrier))
634                         busy = true;
635         }
636 
637         if (!busy)
638                 do_kmem_cache_shutdown(s, &release, &need_rcu_barrier);
639 
640 out_unlock:
641         mutex_unlock(&slab_mutex);
642 
643         put_online_mems();
644         put_online_cpus();
645 
646         do_kmem_cache_release(&release, need_rcu_barrier);
647 }
648 EXPORT_SYMBOL(kmem_cache_destroy);
649 
650 /**
651  * kmem_cache_shrink - Shrink a cache.
652  * @cachep: The cache to shrink.
653  *
654  * Releases as many slabs as possible for a cache.
655  * To help debugging, a zero exit status indicates all slabs were released.
656  */
657 int kmem_cache_shrink(struct kmem_cache *cachep)
658 {
659         int ret;
660 
661         get_online_cpus();
662         get_online_mems();
663         ret = __kmem_cache_shrink(cachep, false);
664         put_online_mems();
665         put_online_cpus();
666         return ret;
667 }
668 EXPORT_SYMBOL(kmem_cache_shrink);
669 
670 int slab_is_available(void)
671 {
672         return slab_state >= UP;
673 }
674 
675 #ifndef CONFIG_SLOB
676 /* Create a cache during boot when no slab services are available yet */
677 void __init create_boot_cache(struct kmem_cache *s, const char *name, size_t size,
678                 unsigned long flags)
679 {
680         int err;
681 
682         s->name = name;
683         s->size = s->object_size = size;
684         s->align = calculate_alignment(flags, ARCH_KMALLOC_MINALIGN, size);
685 
686         slab_init_memcg_params(s);
687 
688         err = __kmem_cache_create(s, flags);
689 
690         if (err)
691                 panic("Creation of kmalloc slab %s size=%zu failed. Reason %d\n",
692                                         name, size, err);
693 
694         s->refcount = -1;       /* Exempt from merging for now */
695 }
696 
697 struct kmem_cache *__init create_kmalloc_cache(const char *name, size_t size,
698                                 unsigned long flags)
699 {
700         struct kmem_cache *s = kmem_cache_zalloc(kmem_cache, GFP_NOWAIT);
701 
702         if (!s)
703                 panic("Out of memory when creating slab %s\n", name);
704 
705         create_boot_cache(s, name, size, flags);
706         list_add(&s->list, &slab_caches);
707         s->refcount = 1;
708         return s;
709 }
710 
711 struct kmem_cache *kmalloc_caches[KMALLOC_SHIFT_HIGH + 1];
712 EXPORT_SYMBOL(kmalloc_caches);
713 
714 #ifdef CONFIG_ZONE_DMA
715 struct kmem_cache *kmalloc_dma_caches[KMALLOC_SHIFT_HIGH + 1];
716 EXPORT_SYMBOL(kmalloc_dma_caches);
717 #endif
718 
719 /*
720  * Conversion table for small slabs sizes / 8 to the index in the
721  * kmalloc array. This is necessary for slabs < 192 since we have non power
722  * of two cache sizes there. The size of larger slabs can be determined using
723  * fls.
724  */
725 static s8 size_index[24] = {
726         3,      /* 8 */
727         4,      /* 16 */
728         5,      /* 24 */
729         5,      /* 32 */
730         6,      /* 40 */
731         6,      /* 48 */
732         6,      /* 56 */
733         6,      /* 64 */
734         1,      /* 72 */
735         1,      /* 80 */
736         1,      /* 88 */
737         1,      /* 96 */
738         7,      /* 104 */
739         7,      /* 112 */
740         7,      /* 120 */
741         7,      /* 128 */
742         2,      /* 136 */
743         2,      /* 144 */
744         2,      /* 152 */
745         2,      /* 160 */
746         2,      /* 168 */
747         2,      /* 176 */
748         2,      /* 184 */
749         2       /* 192 */
750 };
751 
752 static inline int size_index_elem(size_t bytes)
753 {
754         return (bytes - 1) / 8;
755 }
756 
757 /*
758  * Find the kmem_cache structure that serves a given size of
759  * allocation
760  */
761 struct kmem_cache *kmalloc_slab(size_t size, gfp_t flags)
762 {
763         int index;
764 
765         if (unlikely(size > KMALLOC_MAX_SIZE)) {
766                 WARN_ON_ONCE(!(flags & __GFP_NOWARN));
767                 return NULL;
768         }
769 
770         if (size <= 192) {
771                 if (!size)
772                         return ZERO_SIZE_PTR;
773 
774                 index = size_index[size_index_elem(size)];
775         } else
776                 index = fls(size - 1);
777 
778 #ifdef CONFIG_ZONE_DMA
779         if (unlikely((flags & GFP_DMA)))
780                 return kmalloc_dma_caches[index];
781 
782 #endif
783         return kmalloc_caches[index];
784 }
785 
786 /*
787  * Create the kmalloc array. Some of the regular kmalloc arrays
788  * may already have been created because they were needed to
789  * enable allocations for slab creation.
790  */
791 void __init create_kmalloc_caches(unsigned long flags)
792 {
793         int i;
794 
795         /*
796          * Patch up the size_index table if we have strange large alignment
797          * requirements for the kmalloc array. This is only the case for
798          * MIPS it seems. The standard arches will not generate any code here.
799          *
800          * Largest permitted alignment is 256 bytes due to the way we
801          * handle the index determination for the smaller caches.
802          *
803          * Make sure that nothing crazy happens if someone starts tinkering
804          * around with ARCH_KMALLOC_MINALIGN
805          */
806         BUILD_BUG_ON(KMALLOC_MIN_SIZE > 256 ||
807                 (KMALLOC_MIN_SIZE & (KMALLOC_MIN_SIZE - 1)));
808 
809         for (i = 8; i < KMALLOC_MIN_SIZE; i += 8) {
810                 int elem = size_index_elem(i);
811 
812                 if (elem >= ARRAY_SIZE(size_index))
813                         break;
814                 size_index[elem] = KMALLOC_SHIFT_LOW;
815         }
816 
817         if (KMALLOC_MIN_SIZE >= 64) {
818                 /*
819                  * The 96 byte size cache is not used if the alignment
820                  * is 64 byte.
821                  */
822                 for (i = 64 + 8; i <= 96; i += 8)
823                         size_index[size_index_elem(i)] = 7;
824 
825         }
826 
827         if (KMALLOC_MIN_SIZE >= 128) {
828                 /*
829                  * The 192 byte sized cache is not used if the alignment
830                  * is 128 byte. Redirect kmalloc to use the 256 byte cache
831                  * instead.
832                  */
833                 for (i = 128 + 8; i <= 192; i += 8)
834                         size_index[size_index_elem(i)] = 8;
835         }
836         for (i = KMALLOC_SHIFT_LOW; i <= KMALLOC_SHIFT_HIGH; i++) {
837                 if (!kmalloc_caches[i]) {
838                         kmalloc_caches[i] = create_kmalloc_cache(NULL,
839                                                         1 << i, flags);
840                 }
841 
842                 /*
843                  * Caches that are not of the two-to-the-power-of size.
844                  * These have to be created immediately after the
845                  * earlier power of two caches
846                  */
847                 if (KMALLOC_MIN_SIZE <= 32 && !kmalloc_caches[1] && i == 6)
848                         kmalloc_caches[1] = create_kmalloc_cache(NULL, 96, flags);
849 
850                 if (KMALLOC_MIN_SIZE <= 64 && !kmalloc_caches[2] && i == 7)
851                         kmalloc_caches[2] = create_kmalloc_cache(NULL, 192, flags);
852         }
853 
854         /* Kmalloc array is now usable */
855         slab_state = UP;
856 
857         for (i = 0; i <= KMALLOC_SHIFT_HIGH; i++) {
858                 struct kmem_cache *s = kmalloc_caches[i];
859                 char *n;
860 
861                 if (s) {
862                         n = kasprintf(GFP_NOWAIT, "kmalloc-%d", kmalloc_size(i));
863 
864                         BUG_ON(!n);
865                         s->name = n;
866                 }
867         }
868 
869 #ifdef CONFIG_ZONE_DMA
870         for (i = 0; i <= KMALLOC_SHIFT_HIGH; i++) {
871                 struct kmem_cache *s = kmalloc_caches[i];
872 
873                 if (s) {
874                         int size = kmalloc_size(i);
875                         char *n = kasprintf(GFP_NOWAIT,
876                                  "dma-kmalloc-%d", size);
877 
878                         BUG_ON(!n);
879                         kmalloc_dma_caches[i] = create_kmalloc_cache(n,
880                                 size, SLAB_CACHE_DMA | flags);
881                 }
882         }
883 #endif
884 }
885 #endif /* !CONFIG_SLOB */
886 
887 /*
888  * To avoid unnecessary overhead, we pass through large allocation requests
889  * directly to the page allocator. We use __GFP_COMP, because we will need to
890  * know the allocation order to free the pages properly in kfree.
891  */
892 void *kmalloc_order(size_t size, gfp_t flags, unsigned int order)
893 {
894         void *ret;
895         struct page *page;
896 
897         flags |= __GFP_COMP;
898         page = alloc_kmem_pages(flags, order);
899         ret = page ? page_address(page) : NULL;
900         kmemleak_alloc(ret, size, 1, flags);
901         kasan_kmalloc_large(ret, size);
902         return ret;
903 }
904 EXPORT_SYMBOL(kmalloc_order);
905 
906 #ifdef CONFIG_TRACING
907 void *kmalloc_order_trace(size_t size, gfp_t flags, unsigned int order)
908 {
909         void *ret = kmalloc_order(size, flags, order);
910         trace_kmalloc(_RET_IP_, ret, size, PAGE_SIZE << order, flags);
911         return ret;
912 }
913 EXPORT_SYMBOL(kmalloc_order_trace);
914 #endif
915 
916 #ifdef CONFIG_SLABINFO
917 
918 #ifdef CONFIG_SLAB
919 #define SLABINFO_RIGHTS (S_IWUSR | S_IRUSR)
920 #else
921 #define SLABINFO_RIGHTS S_IRUSR
922 #endif
923 
924 static void print_slabinfo_header(struct seq_file *m)
925 {
926         /*
927          * Output format version, so at least we can change it
928          * without _too_ many complaints.
929          */
930 #ifdef CONFIG_DEBUG_SLAB
931         seq_puts(m, "slabinfo - version: 2.1 (statistics)\n");
932 #else
933         seq_puts(m, "slabinfo - version: 2.1\n");
934 #endif
935         seq_puts(m, "# name            <active_objs> <num_objs> <objsize> "
936                  "<objperslab> <pagesperslab>");
937         seq_puts(m, " : tunables <limit> <batchcount> <sharedfactor>");
938         seq_puts(m, " : slabdata <active_slabs> <num_slabs> <sharedavail>");
939 #ifdef CONFIG_DEBUG_SLAB
940         seq_puts(m, " : globalstat <listallocs> <maxobjs> <grown> <reaped> "
941                  "<error> <maxfreeable> <nodeallocs> <remotefrees> <alienoverflow>");
942         seq_puts(m, " : cpustat <allochit> <allocmiss> <freehit> <freemiss>");
943 #endif
944         seq_putc(m, '\n');
945 }
946 
947 void *slab_start(struct seq_file *m, loff_t *pos)
948 {
949         mutex_lock(&slab_mutex);
950         return seq_list_start(&slab_caches, *pos);
951 }
952 
953 void *slab_next(struct seq_file *m, void *p, loff_t *pos)
954 {
955         return seq_list_next(p, &slab_caches, pos);
956 }
957 
958 void slab_stop(struct seq_file *m, void *p)
959 {
960         mutex_unlock(&slab_mutex);
961 }
962 
963 static void
964 memcg_accumulate_slabinfo(struct kmem_cache *s, struct slabinfo *info)
965 {
966         struct kmem_cache *c;
967         struct slabinfo sinfo;
968 
969         if (!is_root_cache(s))
970                 return;
971 
972         for_each_memcg_cache(c, s) {
973                 memset(&sinfo, 0, sizeof(sinfo));
974                 get_slabinfo(c, &sinfo);
975 
976                 info->active_slabs += sinfo.active_slabs;
977                 info->num_slabs += sinfo.num_slabs;
978                 info->shared_avail += sinfo.shared_avail;
979                 info->active_objs += sinfo.active_objs;
980                 info->num_objs += sinfo.num_objs;
981         }
982 }
983 
984 static void cache_show(struct kmem_cache *s, struct seq_file *m)
985 {
986         struct slabinfo sinfo;
987 
988         memset(&sinfo, 0, sizeof(sinfo));
989         get_slabinfo(s, &sinfo);
990 
991         memcg_accumulate_slabinfo(s, &sinfo);
992 
993         seq_printf(m, "%-17s %6lu %6lu %6u %4u %4d",
994                    cache_name(s), sinfo.active_objs, sinfo.num_objs, s->size,
995                    sinfo.objects_per_slab, (1 << sinfo.cache_order));
996 
997         seq_printf(m, " : tunables %4u %4u %4u",
998                    sinfo.limit, sinfo.batchcount, sinfo.shared);
999         seq_printf(m, " : slabdata %6lu %6lu %6lu",
1000                    sinfo.active_slabs, sinfo.num_slabs, sinfo.shared_avail);
1001         slabinfo_show_stats(m, s);
1002         seq_putc(m, '\n');
1003 }
1004 
1005 static int slab_show(struct seq_file *m, void *p)
1006 {
1007         struct kmem_cache *s = list_entry(p, struct kmem_cache, list);
1008 
1009         if (p == slab_caches.next)
1010                 print_slabinfo_header(m);
1011         if (is_root_cache(s))
1012                 cache_show(s, m);
1013         return 0;
1014 }
1015 
1016 #ifdef CONFIG_MEMCG_KMEM
1017 int memcg_slab_show(struct seq_file *m, void *p)
1018 {
1019         struct kmem_cache *s = list_entry(p, struct kmem_cache, list);
1020         struct mem_cgroup *memcg = mem_cgroup_from_css(seq_css(m));
1021 
1022         if (p == slab_caches.next)
1023                 print_slabinfo_header(m);
1024         if (!is_root_cache(s) && s->memcg_params.memcg == memcg)
1025                 cache_show(s, m);
1026         return 0;
1027 }
1028 #endif
1029 
1030 /*
1031  * slabinfo_op - iterator that generates /proc/slabinfo
1032  *
1033  * Output layout:
1034  * cache-name
1035  * num-active-objs
1036  * total-objs
1037  * object size
1038  * num-active-slabs
1039  * total-slabs
1040  * num-pages-per-slab
1041  * + further values on SMP and with statistics enabled
1042  */
1043 static const struct seq_operations slabinfo_op = {
1044         .start = slab_start,
1045         .next = slab_next,
1046         .stop = slab_stop,
1047         .show = slab_show,
1048 };
1049 
1050 static int slabinfo_open(struct inode *inode, struct file *file)
1051 {
1052         return seq_open(file, &slabinfo_op);
1053 }
1054 
1055 static const struct file_operations proc_slabinfo_operations = {
1056         .open           = slabinfo_open,
1057         .read           = seq_read,
1058         .write          = slabinfo_write,
1059         .llseek         = seq_lseek,
1060         .release        = seq_release,
1061 };
1062 
1063 static int __init slab_proc_init(void)
1064 {
1065         proc_create("slabinfo", SLABINFO_RIGHTS, NULL,
1066                                                 &proc_slabinfo_operations);
1067         return 0;
1068 }
1069 module_init(slab_proc_init);
1070 #endif /* CONFIG_SLABINFO */
1071 
1072 static __always_inline void *__do_krealloc(const void *p, size_t new_size,
1073                                            gfp_t flags)
1074 {
1075         void *ret;
1076         size_t ks = 0;
1077 
1078         if (p)
1079                 ks = ksize(p);
1080 
1081         if (ks >= new_size) {
1082                 kasan_krealloc((void *)p, new_size);
1083                 return (void *)p;
1084         }
1085 
1086         ret = kmalloc_track_caller(new_size, flags);
1087         if (ret && p)
1088                 memcpy(ret, p, ks);
1089 
1090         return ret;
1091 }
1092 
1093 /**
1094  * __krealloc - like krealloc() but don't free @p.
1095  * @p: object to reallocate memory for.
1096  * @new_size: how many bytes of memory are required.
1097  * @flags: the type of memory to allocate.
1098  *
1099  * This function is like krealloc() except it never frees the originally
1100  * allocated buffer. Use this if you don't want to free the buffer immediately
1101  * like, for example, with RCU.
1102  */
1103 void *__krealloc(const void *p, size_t new_size, gfp_t flags)
1104 {
1105         if (unlikely(!new_size))
1106                 return ZERO_SIZE_PTR;
1107 
1108         return __do_krealloc(p, new_size, flags);
1109 
1110 }
1111 EXPORT_SYMBOL(__krealloc);
1112 
1113 /**
1114  * krealloc - reallocate memory. The contents will remain unchanged.
1115  * @p: object to reallocate memory for.
1116  * @new_size: how many bytes of memory are required.
1117  * @flags: the type of memory to allocate.
1118  *
1119  * The contents of the object pointed to are preserved up to the
1120  * lesser of the new and old sizes.  If @p is %NULL, krealloc()
1121  * behaves exactly like kmalloc().  If @new_size is 0 and @p is not a
1122  * %NULL pointer, the object pointed to is freed.
1123  */
1124 void *krealloc(const void *p, size_t new_size, gfp_t flags)
1125 {
1126         void *ret;
1127 
1128         if (unlikely(!new_size)) {
1129                 kfree(p);
1130                 return ZERO_SIZE_PTR;
1131         }
1132 
1133         ret = __do_krealloc(p, new_size, flags);
1134         if (ret && p != ret)
1135                 kfree(p);
1136 
1137         return ret;
1138 }
1139 EXPORT_SYMBOL(krealloc);
1140 
1141 /**
1142  * kzfree - like kfree but zero memory
1143  * @p: object to free memory of
1144  *
1145  * The memory of the object @p points to is zeroed before freed.
1146  * If @p is %NULL, kzfree() does nothing.
1147  *
1148  * Note: this function zeroes the whole allocated buffer which can be a good
1149  * deal bigger than the requested buffer size passed to kmalloc(). So be
1150  * careful when using this function in performance sensitive code.
1151  */
1152 void kzfree(const void *p)
1153 {
1154         size_t ks;
1155         void *mem = (void *)p;
1156 
1157         if (unlikely(ZERO_OR_NULL_PTR(mem)))
1158                 return;
1159         ks = ksize(mem);
1160         memset(mem, 0, ks);
1161         kfree(mem);
1162 }
1163 EXPORT_SYMBOL(kzfree);
1164 
1165 /* Tracepoints definitions. */
1166 EXPORT_TRACEPOINT_SYMBOL(kmalloc);
1167 EXPORT_TRACEPOINT_SYMBOL(kmem_cache_alloc);
1168 EXPORT_TRACEPOINT_SYMBOL(kmalloc_node);
1169 EXPORT_TRACEPOINT_SYMBOL(kmem_cache_alloc_node);
1170 EXPORT_TRACEPOINT_SYMBOL(kfree);
1171 EXPORT_TRACEPOINT_SYMBOL(kmem_cache_free);
1172 

/* linux/slab_def.h */
  1 #ifndef _LINUX_SLAB_DEF_H
  2 #define _LINUX_SLAB_DEF_H
  3 
  4 #include <linux/reciprocal_div.h>
  5 
  6 /*
  7  * Definitions unique to the original Linux SLAB allocator.
  8  */
  9 
 10 struct kmem_cache {
 11         struct array_cache __percpu *cpu_cache;
 12 
 13 /* 1) Cache tunables. Protected by slab_mutex */
 14         unsigned int batchcount;
 15         unsigned int limit;
 16         unsigned int shared;
 17 
 18         unsigned int size;
 19         struct reciprocal_value reciprocal_buffer_size;
 20 /* 2) touched by every alloc & free from the backend */
 21 
 22         unsigned int flags;             /* constant flags */
 23         unsigned int num;               /* # of objs per slab */
 24 
 25 /* 3) cache_grow/shrink */
 26         /* order of pgs per slab (2^n) */
 27         unsigned int gfporder;
 28 
 29         /* force GFP flags, e.g. GFP_DMA */
 30         gfp_t allocflags;
 31 
 32         size_t colour;                  /* cache colouring range */
 33         unsigned int colour_off;        /* colour offset */
 34         struct kmem_cache *freelist_cache;
 35         unsigned int freelist_size;
 36 
 37         /* constructor func */
 38         void (*ctor)(void *obj);
 39 
 40 /* 4) cache creation/removal */
 41         const char *name;
 42         struct list_head list;
 43         int refcount;
 44         int object_size;
 45         int align;
 46 
 47 /* 5) statistics */
 48 #ifdef CONFIG_DEBUG_SLAB
 49         unsigned long num_active;
 50         unsigned long num_allocations;
 51         unsigned long high_mark;
 52         unsigned long grown;
 53         unsigned long reaped;
 54         unsigned long errors;
 55         unsigned long max_freeable;
 56         unsigned long node_allocs;
 57         unsigned long node_frees;
 58         unsigned long node_overflow;
 59         atomic_t allochit;
 60         atomic_t allocmiss;
 61         atomic_t freehit;
 62         atomic_t freemiss;
 63 
 64         /*
 65          * If debugging is enabled, then the allocator can add additional
 66          * fields and/or padding to every object. size contains the total
 67          * object size including these internal fields, the following two
 68          * variables contain the offset to the user object and its size.
 69          */
 70         int obj_offset;
 71 #endif /* CONFIG_DEBUG_SLAB */
 72 #ifdef CONFIG_MEMCG_KMEM
 73         struct memcg_cache_params memcg_params;
 74 #endif
 75 
 76         struct kmem_cache_node *node[MAX_NUMNODES];
 77 };
 78 
 79 #endif  /* _LINUX_SLAB_DEF_H */
 80 


/* mm/slab.c */
  1 /*
  2  * linux/mm/slab.c
  3  * Written by Mark Hemment, 1996/97.
  4  * (markhe@nextd.demon.co.uk)
  5  *
  6  * kmem_cache_destroy() + some cleanup - 1999 Andrea Arcangeli
  7  *
  8  * Major cleanup, different bufctl logic, per-cpu arrays
  9  *      (c) 2000 Manfred Spraul
 10  *
 11  * Cleanup, make the head arrays unconditional, preparation for NUMA
 12  *      (c) 2002 Manfred Spraul
 13  *
 14  * An implementation of the Slab Allocator as described in outline in;
 15  *      UNIX Internals: The New Frontiers by Uresh Vahalia
 16  *      Pub: Prentice Hall      ISBN 0-13-101908-2
 17  * or with a little more detail in;
 18  *      The Slab Allocator: An Object-Caching Kernel Memory Allocator
 19  *      Jeff Bonwick (Sun Microsystems).
 20  *      Presented at: USENIX Summer 1994 Technical Conference
 21  *
 22  * The memory is organized in caches, one cache for each object type.
 23  * (e.g. inode_cache, dentry_cache, buffer_head, vm_area_struct)
 24  * Each cache consists out of many slabs (they are small (usually one
 25  * page long) and always contiguous), and each slab contains multiple
 26  * initialized objects.
 27  *
 28  * This means, that your constructor is used only for newly allocated
 29  * slabs and you must pass objects with the same initializations to
 30  * kmem_cache_free.
 31  *
 32  * Each cache can only support one memory type (GFP_DMA, GFP_HIGHMEM,
 33  * normal). If you need a special memory type, then must create a new
 34  * cache for that memory type.
 35  *
 36  * In order to reduce fragmentation, the slabs are sorted in 3 groups:
 37  *   full slabs with 0 free objects
 38  *   partial slabs
 39  *   empty slabs with no allocated objects
 40  *
 41  * If partial slabs exist, then new allocations come from these slabs,
 42  * otherwise from empty slabs or new slabs are allocated.
 43  *
 44  * kmem_cache_destroy() CAN CRASH if you try to allocate from the cache
 45  * during kmem_cache_destroy(). The caller must prevent concurrent allocs.
 46  *
 47  * Each cache has a short per-cpu head array, most allocs
 48  * and frees go into that array, and if that array overflows, then 1/2
 49  * of the entries in the array are given back into the global cache.
 50  * The head array is strictly LIFO and should improve the cache hit rates.
 51  * On SMP, it additionally reduces the spinlock operations.
 52  *
 53  * The c_cpuarray may not be read with enabled local interrupts -
 54  * it's changed with a smp_call_function().
 55  *
 56  * SMP synchronization:
 57  *  constructors and destructors are called without any locking.
 58  *  Several members in struct kmem_cache and struct slab never change, they
 59  *      are accessed without any locking.
 60  *  The per-cpu arrays are never accessed from the wrong cpu, no locking,
 61  *      and local interrupts are disabled so slab code is preempt-safe.
 62  *  The non-constant members are protected with a per-cache irq spinlock.
 63  *
 64  * Many thanks to Mark Hemment, who wrote another per-cpu slab patch
 65  * in 2000 - many ideas in the current implementation are derived from
 66  * his patch.
 67  *
 68  * Further notes from the original documentation:
 69  *
 70  * 11 April '97.  Started multi-threading - markhe
 71  *      The global cache-chain is protected by the mutex 'slab_mutex'.
 72  *      The sem is only needed when accessing/extending the cache-chain, which
 73  *      can never happen inside an interrupt (kmem_cache_create(),
 74  *      kmem_cache_shrink() and kmem_cache_reap()).
 75  *
 76  *      At present, each engine can be growing a cache.  This should be blocked.
 77  *
 78  * 15 March 2005. NUMA slab allocator.
 79  *      Shai Fultheim <shai@scalex86.org>.
 80  *      Shobhit Dayal <shobhit@calsoftinc.com>
 81  *      Alok N Kataria <alokk@calsoftinc.com>
 82  *      Christoph Lameter <christoph@lameter.com>
 83  *
 84  *      Modified the slab allocator to be node aware on NUMA systems.
 85  *      Each node has its own list of partial, free and full slabs.
 86  *      All object allocations for a node occur from node specific slab lists.
 87  */
 88 
 89 #include        <linux/slab.h>
 90 #include        <linux/mm.h>
 91 #include        <linux/poison.h>
 92 #include        <linux/swap.h>
 93 #include        <linux/cache.h>
 94 #include        <linux/interrupt.h>
 95 #include        <linux/init.h>
 96 #include        <linux/compiler.h>
 97 #include        <linux/cpuset.h>
 98 #include        <linux/proc_fs.h>
 99 #include        <linux/seq_file.h>
100 #include        <linux/notifier.h>
101 #include        <linux/kallsyms.h>
102 #include        <linux/cpu.h>
103 #include        <linux/sysctl.h>
104 #include        <linux/module.h>
105 #include        <linux/rcupdate.h>
106 #include        <linux/string.h>
107 #include        <linux/uaccess.h>
108 #include        <linux/nodemask.h>
109 #include        <linux/kmemleak.h>
110 #include        <linux/mempolicy.h>
111 #include        <linux/mutex.h>
112 #include        <linux/fault-inject.h>
113 #include        <linux/rtmutex.h>
114 #include        <linux/reciprocal_div.h>
115 #include        <linux/debugobjects.h>
116 #include        <linux/kmemcheck.h>
117 #include        <linux/memory.h>
118 #include        <linux/prefetch.h>
119 
120 #include        <net/sock.h>
121 
122 #include        <asm/cacheflush.h>
123 #include        <asm/tlbflush.h>
124 #include        <asm/page.h>
125 
126 #include <trace/events/kmem.h>
127 
128 #include        "internal.h"
129 
130 #include        "slab.h"
131 
132 /*
133  * DEBUG        - 1 for kmem_cache_create() to honour; SLAB_RED_ZONE & SLAB_POISON.
134  *                0 for faster, smaller code (especially in the critical paths).
135  *
136  * STATS        - 1 to collect stats for /proc/slabinfo.
137  *                0 for faster, smaller code (especially in the critical paths).
138  *
139  * FORCED_DEBUG - 1 enables SLAB_RED_ZONE and SLAB_POISON (if possible)
140  */
141 
142 #ifdef CONFIG_DEBUG_SLAB
143 #define DEBUG           1
144 #define STATS           1
145 #define FORCED_DEBUG    1
146 #else
147 #define DEBUG           0
148 #define STATS           0
149 #define FORCED_DEBUG    0
150 #endif
151 
152 /* Shouldn't this be in a header file somewhere? */
153 #define BYTES_PER_WORD          sizeof(void *)
154 #define REDZONE_ALIGN           max(BYTES_PER_WORD, __alignof__(unsigned long long))
155 
156 #ifndef ARCH_KMALLOC_FLAGS
157 #define ARCH_KMALLOC_FLAGS SLAB_HWCACHE_ALIGN
158 #endif
159 
160 #define FREELIST_BYTE_INDEX (((PAGE_SIZE >> BITS_PER_BYTE) \
161                                 <= SLAB_OBJ_MIN_SIZE) ? 1 : 0)
162 
163 #if FREELIST_BYTE_INDEX
164 typedef unsigned char freelist_idx_t;
165 #else
166 typedef unsigned short freelist_idx_t;
167 #endif
168 
169 #define SLAB_OBJ_MAX_NUM ((1 << sizeof(freelist_idx_t) * BITS_PER_BYTE) - 1)
170 
171 /*
172  * true if a page was allocated from pfmemalloc reserves for network-based
173  * swap
174  */
175 static bool pfmemalloc_active __read_mostly;
176 
177 /*
178  * struct array_cache
179  *
180  * Purpose:
181  * - LIFO ordering, to hand out cache-warm objects from _alloc
182  * - reduce the number of linked list operations
183  * - reduce spinlock operations
184  *
185  * The limit is stored in the per-cpu structure to reduce the data cache
186  * footprint.
187  *
188  */
189 struct array_cache {
190         unsigned int avail;
191         unsigned int limit;
192         unsigned int batchcount;
193         unsigned int touched;
194         void *entry[];  /*
195                          * Must have this definition in here for the proper
196                          * alignment of array_cache. Also simplifies accessing
197                          * the entries.
198                          *
199                          * Entries should not be directly dereferenced as
200                          * entries belonging to slabs marked pfmemalloc will
201                          * have the lower bits set SLAB_OBJ_PFMEMALLOC
202                          */
203 };
204 
205 struct alien_cache {
206         spinlock_t lock;
207         struct array_cache ac;
208 };
209 
210 #define SLAB_OBJ_PFMEMALLOC     1
211 static inline bool is_obj_pfmemalloc(void *objp)
212 {
213         return (unsigned long)objp & SLAB_OBJ_PFMEMALLOC;
214 }
215 
216 static inline void set_obj_pfmemalloc(void **objp)
217 {
218         *objp = (void *)((unsigned long)*objp | SLAB_OBJ_PFMEMALLOC);
219         return;
220 }
221 
222 static inline void clear_obj_pfmemalloc(void **objp)
223 {
224         *objp = (void *)((unsigned long)*objp & ~SLAB_OBJ_PFMEMALLOC);
225 }
226 
227 /*
228  * bootstrap: The caches do not work without cpuarrays anymore, but the
229  * cpuarrays are allocated from the generic caches...
230  */
231 #define BOOT_CPUCACHE_ENTRIES   1
232 struct arraycache_init {
233         struct array_cache cache;
234         void *entries[BOOT_CPUCACHE_ENTRIES];
235 };
236 
237 /*
238  * Need this for bootstrapping a per node allocator.
239  */
240 #define NUM_INIT_LISTS (2 * MAX_NUMNODES)
241 static struct kmem_cache_node __initdata init_kmem_cache_node[NUM_INIT_LISTS];
242 #define CACHE_CACHE 0
243 #define SIZE_NODE (MAX_NUMNODES)
244 
245 static int drain_freelist(struct kmem_cache *cache,
246                         struct kmem_cache_node *n, int tofree);
247 static void free_block(struct kmem_cache *cachep, void **objpp, int len,
248                         int node, struct list_head *list);
249 static void slabs_destroy(struct kmem_cache *cachep, struct list_head *list);
250 static int enable_cpucache(struct kmem_cache *cachep, gfp_t gfp);
251 static void cache_reap(struct work_struct *unused);
252 
253 static int slab_early_init = 1;
254 
255 #define INDEX_NODE kmalloc_index(sizeof(struct kmem_cache_node))
256 
257 static void kmem_cache_node_init(struct kmem_cache_node *parent)
258 {
259         INIT_LIST_HEAD(&parent->slabs_full);
260         INIT_LIST_HEAD(&parent->slabs_partial);
261         INIT_LIST_HEAD(&parent->slabs_free);
262         parent->shared = NULL;
263         parent->alien = NULL;
264         parent->colour_next = 0;
265         spin_lock_init(&parent->list_lock);
266         parent->free_objects = 0;
267         parent->free_touched = 0;
268 }
269 
270 #define MAKE_LIST(cachep, listp, slab, nodeid)                          \
271         do {                                                            \
272                 INIT_LIST_HEAD(listp);                                  \
273                 list_splice(&get_node(cachep, nodeid)->slab, listp);    \
274         } while (0)
275 
276 #define MAKE_ALL_LISTS(cachep, ptr, nodeid)                             \
277         do {                                                            \
278         MAKE_LIST((cachep), (&(ptr)->slabs_full), slabs_full, nodeid);  \
279         MAKE_LIST((cachep), (&(ptr)->slabs_partial), slabs_partial, nodeid); \
280         MAKE_LIST((cachep), (&(ptr)->slabs_free), slabs_free, nodeid);  \
281         } while (0)
282 
283 #define CFLGS_OFF_SLAB          (0x80000000UL)
284 #define OFF_SLAB(x)     ((x)->flags & CFLGS_OFF_SLAB)
285 
286 #define BATCHREFILL_LIMIT       16
287 /*
288  * Optimization question: fewer reaps means less probability for unnessary
289  * cpucache drain/refill cycles.
290  *
291  * OTOH the cpuarrays can contain lots of objects,
292  * which could lock up otherwise freeable slabs.
293  */
294 #define REAPTIMEOUT_AC          (2*HZ)
295 #define REAPTIMEOUT_NODE        (4*HZ)
296 
297 #if STATS
298 #define STATS_INC_ACTIVE(x)     ((x)->num_active++)
299 #define STATS_DEC_ACTIVE(x)     ((x)->num_active--)
300 #define STATS_INC_ALLOCED(x)    ((x)->num_allocations++)
301 #define STATS_INC_GROWN(x)      ((x)->grown++)
302 #define STATS_ADD_REAPED(x,y)   ((x)->reaped += (y))
303 #define STATS_SET_HIGH(x)                                               \
304         do {                                                            \
305                 if ((x)->num_active > (x)->high_mark)                   \
306                         (x)->high_mark = (x)->num_active;               \
307         } while (0)
308 #define STATS_INC_ERR(x)        ((x)->errors++)
309 #define STATS_INC_NODEALLOCS(x) ((x)->node_allocs++)
310 #define STATS_INC_NODEFREES(x)  ((x)->node_frees++)
311 #define STATS_INC_ACOVERFLOW(x)   ((x)->node_overflow++)
312 #define STATS_SET_FREEABLE(x, i)                                        \
313         do {                                                            \
314                 if ((x)->max_freeable < i)                              \
315                         (x)->max_freeable = i;                          \
316         } while (0)
317 #define STATS_INC_ALLOCHIT(x)   atomic_inc(&(x)->allochit)
318 #define STATS_INC_ALLOCMISS(x)  atomic_inc(&(x)->allocmiss)
319 #define STATS_INC_FREEHIT(x)    atomic_inc(&(x)->freehit)
320 #define STATS_INC_FREEMISS(x)   atomic_inc(&(x)->freemiss)
321 #else
322 #define STATS_INC_ACTIVE(x)     do { } while (0)
323 #define STATS_DEC_ACTIVE(x)     do { } while (0)
324 #define STATS_INC_ALLOCED(x)    do { } while (0)
325 #define STATS_INC_GROWN(x)      do { } while (0)
326 #define STATS_ADD_REAPED(x,y)   do { (void)(y); } while (0)
327 #define STATS_SET_HIGH(x)       do { } while (0)
328 #define STATS_INC_ERR(x)        do { } while (0)
329 #define STATS_INC_NODEALLOCS(x) do { } while (0)
330 #define STATS_INC_NODEFREES(x)  do { } while (0)
331 #define STATS_INC_ACOVERFLOW(x)   do { } while (0)
332 #define STATS_SET_FREEABLE(x, i) do { } while (0)
333 #define STATS_INC_ALLOCHIT(x)   do { } while (0)
334 #define STATS_INC_ALLOCMISS(x)  do { } while (0)
335 #define STATS_INC_FREEHIT(x)    do { } while (0)
336 #define STATS_INC_FREEMISS(x)   do { } while (0)
337 #endif
338 
339 #if DEBUG
340 
341 /*
342  * memory layout of objects:
343  * 0            : objp
344  * 0 .. cachep->obj_offset - BYTES_PER_WORD - 1: padding. This ensures that
345  *              the end of an object is aligned with the end of the real
346  *              allocation. Catches writes behind the end of the allocation.
347  * cachep->obj_offset - BYTES_PER_WORD .. cachep->obj_offset - 1:
348  *              redzone word.
349  * cachep->obj_offset: The real object.
350  * cachep->size - 2* BYTES_PER_WORD: redzone word [BYTES_PER_WORD long]
351  * cachep->size - 1* BYTES_PER_WORD: last caller address
352  *                                      [BYTES_PER_WORD long]
353  */
354 static int obj_offset(struct kmem_cache *cachep)
355 {
356         return cachep->obj_offset;
357 }
358 
359 static unsigned long long *dbg_redzone1(struct kmem_cache *cachep, void *objp)
360 {
361         BUG_ON(!(cachep->flags & SLAB_RED_ZONE));
362         return (unsigned long long*) (objp + obj_offset(cachep) -
363                                       sizeof(unsigned long long));
364 }
365 
366 static unsigned long long *dbg_redzone2(struct kmem_cache *cachep, void *objp)
367 {
368         BUG_ON(!(cachep->flags & SLAB_RED_ZONE));
369         if (cachep->flags & SLAB_STORE_USER)
370                 return (unsigned long long *)(objp + cachep->size -
371                                               sizeof(unsigned long long) -
372                                               REDZONE_ALIGN);
373         return (unsigned long long *) (objp + cachep->size -
374                                        sizeof(unsigned long long));
375 }
376 
377 static void **dbg_userword(struct kmem_cache *cachep, void *objp)
378 {
379         BUG_ON(!(cachep->flags & SLAB_STORE_USER));
380         return (void **)(objp + cachep->size - BYTES_PER_WORD);
381 }
382 
383 #else
384 
385 #define obj_offset(x)                   0
386 #define dbg_redzone1(cachep, objp)      ({BUG(); (unsigned long long *)NULL;})
387 #define dbg_redzone2(cachep, objp)      ({BUG(); (unsigned long long *)NULL;})
388 #define dbg_userword(cachep, objp)      ({BUG(); (void **)NULL;})
389 
390 #endif
391 
392 #define OBJECT_FREE (0)
393 #define OBJECT_ACTIVE (1)
394 
395 #ifdef CONFIG_DEBUG_SLAB_LEAK
396 
397 static void set_obj_status(struct page *page, int idx, int val)
398 {
399         int freelist_size;
400         char *status;
401         struct kmem_cache *cachep = page->slab_cache;
402 
403         freelist_size = cachep->num * sizeof(freelist_idx_t);
404         status = (char *)page->freelist + freelist_size;
405         status[idx] = val;
406 }
407 
408 static inline unsigned int get_obj_status(struct page *page, int idx)
409 {
410         int freelist_size;
411         char *status;
412         struct kmem_cache *cachep = page->slab_cache;
413 
414         freelist_size = cachep->num * sizeof(freelist_idx_t);
415         status = (char *)page->freelist + freelist_size;
416 
417         return status[idx];
418 }
419 
420 #else
421 static inline void set_obj_status(struct page *page, int idx, int val) {}
422 
423 #endif
424 
425 /*
426  * Do not go above this order unless 0 objects fit into the slab or
427  * overridden on the command line.
428  */
429 #define SLAB_MAX_ORDER_HI       1
430 #define SLAB_MAX_ORDER_LO       0
431 static int slab_max_order = SLAB_MAX_ORDER_LO;
432 static bool slab_max_order_set __initdata;
433 
434 static inline struct kmem_cache *virt_to_cache(const void *obj)
435 {
436         struct page *page = virt_to_head_page(obj);
437         return page->slab_cache;
438 }
439 
440 static inline void *index_to_obj(struct kmem_cache *cache, struct page *page,
441                                  unsigned int idx)
442 {
443         return page->s_mem + cache->size * idx;
444 }
445 
446 /*
447  * We want to avoid an expensive divide : (offset / cache->size)
448  *   Using the fact that size is a constant for a particular cache,
449  *   we can replace (offset / cache->size) by
450  *   reciprocal_divide(offset, cache->reciprocal_buffer_size)
451  */
452 static inline unsigned int obj_to_index(const struct kmem_cache *cache,
453                                         const struct page *page, void *obj)
454 {
455         u32 offset = (obj - page->s_mem);
456         return reciprocal_divide(offset, cache->reciprocal_buffer_size);
457 }
458 
459 /* internal cache of cache description objs */
460 static struct kmem_cache kmem_cache_boot = {
461         .batchcount = 1,
462         .limit = BOOT_CPUCACHE_ENTRIES,
463         .shared = 1,
464         .size = sizeof(struct kmem_cache),
465         .name = "kmem_cache",
466 };
467 
468 #define BAD_ALIEN_MAGIC 0x01020304ul
469 
470 static DEFINE_PER_CPU(struct delayed_work, slab_reap_work);
471 
472 static inline struct array_cache *cpu_cache_get(struct kmem_cache *cachep)
473 {
474         return this_cpu_ptr(cachep->cpu_cache);
475 }
476 
477 static size_t calculate_freelist_size(int nr_objs, size_t align)
478 {
479         size_t freelist_size;
480 
481         freelist_size = nr_objs * sizeof(freelist_idx_t);
482         if (IS_ENABLED(CONFIG_DEBUG_SLAB_LEAK))
483                 freelist_size += nr_objs * sizeof(char);
484 
485         if (align)
486                 freelist_size = ALIGN(freelist_size, align);
487 
488         return freelist_size;
489 }
490 
491 static int calculate_nr_objs(size_t slab_size, size_t buffer_size,
492                                 size_t idx_size, size_t align)
493 {
494         int nr_objs;
495         size_t remained_size;
496         size_t freelist_size;
497         int extra_space = 0;
498 
499         if (IS_ENABLED(CONFIG_DEBUG_SLAB_LEAK))
500                 extra_space = sizeof(char);
501         /*
502          * Ignore padding for the initial guess. The padding
503          * is at most @align-1 bytes, and @buffer_size is at
504          * least @align. In the worst case, this result will
505          * be one greater than the number of objects that fit
506          * into the memory allocation when taking the padding
507          * into account.
508          */
509         nr_objs = slab_size / (buffer_size + idx_size + extra_space);
510 
511         /*
512          * This calculated number will be either the right
513          * amount, or one greater than what we want.
514          */
515         remained_size = slab_size - nr_objs * buffer_size;
516         freelist_size = calculate_freelist_size(nr_objs, align);
517         if (remained_size < freelist_size)
518                 nr_objs--;
519 
520         return nr_objs;
521 }
522 
523 /*
524  * Calculate the number of objects and left-over bytes for a given buffer size.
525  */
526 static void cache_estimate(unsigned long gfporder, size_t buffer_size,
527                            size_t align, int flags, size_t *left_over,
528                            unsigned int *num)
529 {
530         int nr_objs;
531         size_t mgmt_size;
532         size_t slab_size = PAGE_SIZE << gfporder;
533 
534         /*
535          * The slab management structure can be either off the slab or
536          * on it. For the latter case, the memory allocated for a
537          * slab is used for:
538          *
539          * - One unsigned int for each object
540          * - Padding to respect alignment of @align
541          * - @buffer_size bytes for each object
542          *
543          * If the slab management structure is off the slab, then the
544          * alignment will already be calculated into the size. Because
545          * the slabs are all pages aligned, the objects will be at the
546          * correct alignment when allocated.
547          */
548         if (flags & CFLGS_OFF_SLAB) {
549                 mgmt_size = 0;
550                 nr_objs = slab_size / buffer_size;
551 
552         } else {
553                 nr_objs = calculate_nr_objs(slab_size, buffer_size,
554                                         sizeof(freelist_idx_t), align);
555                 mgmt_size = calculate_freelist_size(nr_objs, align);
556         }
557         *num = nr_objs;
558         *left_over = slab_size - nr_objs*buffer_size - mgmt_size;
559 }
560 
561 #if DEBUG
562 #define slab_error(cachep, msg) __slab_error(__func__, cachep, msg)
563 
564 static void __slab_error(const char *function, struct kmem_cache *cachep,
565                         char *msg)
566 {
567         printk(KERN_ERR "slab error in %s(): cache `%s': %s\n",
568                function, cachep->name, msg);
569         dump_stack();
570         add_taint(TAINT_BAD_PAGE, LOCKDEP_NOW_UNRELIABLE);
571 }
572 #endif
573 
574 /*
575  * By default on NUMA we use alien caches to stage the freeing of
576  * objects allocated from other nodes. This causes massive memory
577  * inefficiencies when using fake NUMA setup to split memory into a
578  * large number of small nodes, so it can be disabled on the command
579  * line
580   */
581 
582 static int use_alien_caches __read_mostly = 1;
583 static int __init noaliencache_setup(char *s)
584 {
585         use_alien_caches = 0;
586         return 1;
587 }
588 __setup("noaliencache", noaliencache_setup);
589 
590 static int __init slab_max_order_setup(char *str)
591 {
592         get_option(&str, &slab_max_order);
593         slab_max_order = slab_max_order < 0 ? 0 :
594                                 min(slab_max_order, MAX_ORDER - 1);
595         slab_max_order_set = true;
596 
597         return 1;
598 }
599 __setup("slab_max_order=", slab_max_order_setup);
600 
601 #ifdef CONFIG_NUMA
602 /*
603  * Special reaping functions for NUMA systems called from cache_reap().
604  * These take care of doing round robin flushing of alien caches (containing
605  * objects freed on different nodes from which they were allocated) and the
606  * flushing of remote pcps by calling drain_node_pages.
607  */
608 static DEFINE_PER_CPU(unsigned long, slab_reap_node);
609 
610 static void init_reap_node(int cpu)
611 {
612         int node;
613 
614         node = next_node(cpu_to_mem(cpu), node_online_map);
615         if (node == MAX_NUMNODES)
616                 node = first_node(node_online_map);
617 
618         per_cpu(slab_reap_node, cpu) = node;
619 }
620 
621 static void next_reap_node(void)
622 {
623         int node = __this_cpu_read(slab_reap_node);
624 
625         node = next_node(node, node_online_map);
626         if (unlikely(node >= MAX_NUMNODES))
627                 node = first_node(node_online_map);
628         __this_cpu_write(slab_reap_node, node);
629 }
630 
631 #else
632 #define init_reap_node(cpu) do { } while (0)
633 #define next_reap_node(void) do { } while (0)
634 #endif
635 
636 /*
637  * Initiate the reap timer running on the target CPU.  We run at around 1 to 2Hz
638  * via the workqueue/eventd.
639  * Add the CPU number into the expiration time to minimize the possibility of
640  * the CPUs getting into lockstep and contending for the global cache chain
641  * lock.
642  */
643 static void start_cpu_timer(int cpu)
644 {
645         struct delayed_work *reap_work = &per_cpu(slab_reap_work, cpu);
646 
647         /*
648          * When this gets called from do_initcalls via cpucache_init(),
649          * init_workqueues() has already run, so keventd will be setup
650          * at that time.
651          */
652         if (keventd_up() && reap_work->work.func == NULL) {
653                 init_reap_node(cpu);
654                 INIT_DEFERRABLE_WORK(reap_work, cache_reap);
655                 schedule_delayed_work_on(cpu, reap_work,
656                                         __round_jiffies_relative(HZ, cpu));
657         }
658 }
659 
660 static void init_arraycache(struct array_cache *ac, int limit, int batch)
661 {
662         /*
663          * The array_cache structures contain pointers to free object.
664          * However, when such objects are allocated or transferred to another
665          * cache the pointers are not cleared and they could be counted as
666          * valid references during a kmemleak scan. Therefore, kmemleak must
667          * not scan such objects.
668          */
669         kmemleak_no_scan(ac);
670         if (ac) {
671                 ac->avail = 0;
672                 ac->limit = limit;
673                 ac->batchcount = batch;
674                 ac->touched = 0;
675         }
676 }
677 
678 static struct array_cache *alloc_arraycache(int node, int entries,
679                                             int batchcount, gfp_t gfp)
680 {
681         size_t memsize = sizeof(void *) * entries + sizeof(struct array_cache);
682         struct array_cache *ac = NULL;
683 
684         ac = kmalloc_node(memsize, gfp, node);
685         init_arraycache(ac, entries, batchcount);
686         return ac;
687 }
688 
689 static inline bool is_slab_pfmemalloc(struct page *page)
690 {
691         return PageSlabPfmemalloc(page);
692 }
693 
694 /* Clears pfmemalloc_active if no slabs have pfmalloc set */
695 static void recheck_pfmemalloc_active(struct kmem_cache *cachep,
696                                                 struct array_cache *ac)
697 {
698         struct kmem_cache_node *n = get_node(cachep, numa_mem_id());
699         struct page *page;
700         unsigned long flags;
701 
702         if (!pfmemalloc_active)
703                 return;
704 
705         spin_lock_irqsave(&n->list_lock, flags);
706         list_for_each_entry(page, &n->slabs_full, lru)
707                 if (is_slab_pfmemalloc(page))
708                         goto out;
709 
710         list_for_each_entry(page, &n->slabs_partial, lru)
711                 if (is_slab_pfmemalloc(page))
712                         goto out;
713 
714         list_for_each_entry(page, &n->slabs_free, lru)
715                 if (is_slab_pfmemalloc(page))
716                         goto out;
717 
718         pfmemalloc_active = false;
719 out:
720         spin_unlock_irqrestore(&n->list_lock, flags);
721 }
722 
723 static void *__ac_get_obj(struct kmem_cache *cachep, struct array_cache *ac,
724                                                 gfp_t flags, bool force_refill)
725 {
726         int i;
727         void *objp = ac->entry[--ac->avail];
728 
729         /* Ensure the caller is allowed to use objects from PFMEMALLOC slab */
730         if (unlikely(is_obj_pfmemalloc(objp))) {
731                 struct kmem_cache_node *n;
732 
733                 if (gfp_pfmemalloc_allowed(flags)) {
734                         clear_obj_pfmemalloc(&objp);
735                         return objp;
736                 }
737 
738                 /* The caller cannot use PFMEMALLOC objects, find another one */
739                 for (i = 0; i < ac->avail; i++) {
740                         /* If a !PFMEMALLOC object is found, swap them */
741                         if (!is_obj_pfmemalloc(ac->entry[i])) {
742                                 objp = ac->entry[i];
743                                 ac->entry[i] = ac->entry[ac->avail];
744                                 ac->entry[ac->avail] = objp;
745                                 return objp;
746                         }
747                 }
748 
749                 /*
750                  * If there are empty slabs on the slabs_free list and we are
751                  * being forced to refill the cache, mark this one !pfmemalloc.
752                  */
753                 n = get_node(cachep, numa_mem_id());
754                 if (!list_empty(&n->slabs_free) && force_refill) {
755                         struct page *page = virt_to_head_page(objp);
756                         ClearPageSlabPfmemalloc(page);
757                         clear_obj_pfmemalloc(&objp);
758                         recheck_pfmemalloc_active(cachep, ac);
759                         return objp;
760                 }
761 
762                 /* No !PFMEMALLOC objects available */
763                 ac->avail++;
764                 objp = NULL;
765         }
766 
767         return objp;
768 }
769 
770 static inline void *ac_get_obj(struct kmem_cache *cachep,
771                         struct array_cache *ac, gfp_t flags, bool force_refill)
772 {
773         void *objp;
774 
775         if (unlikely(sk_memalloc_socks()))
776                 objp = __ac_get_obj(cachep, ac, flags, force_refill);
777         else
778                 objp = ac->entry[--ac->avail];
779 
780         return objp;
781 }
782 
783 static noinline void *__ac_put_obj(struct kmem_cache *cachep,
784                         struct array_cache *ac, void *objp)
785 {
786         if (unlikely(pfmemalloc_active)) {
787                 /* Some pfmemalloc slabs exist, check if this is one */
788                 struct page *page = virt_to_head_page(objp);
789                 if (PageSlabPfmemalloc(page))
790                         set_obj_pfmemalloc(&objp);
791         }
792 
793         return objp;
794 }
795 
796 static inline void ac_put_obj(struct kmem_cache *cachep, struct array_cache *ac,
797                                                                 void *objp)
798 {
799         if (unlikely(sk_memalloc_socks()))
800                 objp = __ac_put_obj(cachep, ac, objp);
801 
802         ac->entry[ac->avail++] = objp;
803 }
804 
805 /*
806  * Transfer objects in one arraycache to another.
807  * Locking must be handled by the caller.
808  *
809  * Return the number of entries transferred.
810  */
811 static int transfer_objects(struct array_cache *to,
812                 struct array_cache *from, unsigned int max)
813 {
814         /* Figure out how many entries to transfer */
815         int nr = min3(from->avail, max, to->limit - to->avail);
816 
817         if (!nr)
818                 return 0;
819 
820         memcpy(to->entry + to->avail, from->entry + from->avail -nr,
821                         sizeof(void *) *nr);
822 
823         from->avail -= nr;
824         to->avail += nr;
825         return nr;
826 }
827 
828 #ifndef CONFIG_NUMA
829 
830 #define drain_alien_cache(cachep, alien) do { } while (0)
831 #define reap_alien(cachep, n) do { } while (0)
832 
833 static inline struct alien_cache **alloc_alien_cache(int node,
834                                                 int limit, gfp_t gfp)
835 {
836         return (struct alien_cache **)BAD_ALIEN_MAGIC;
837 }
838 
839 static inline void free_alien_cache(struct alien_cache **ac_ptr)
840 {
841 }
842 
843 static inline int cache_free_alien(struct kmem_cache *cachep, void *objp)
844 {
845         return 0;
846 }
847 
848 static inline void *alternate_node_alloc(struct kmem_cache *cachep,
849                 gfp_t flags)
850 {
851         return NULL;
852 }
853 
854 static inline void *____cache_alloc_node(struct kmem_cache *cachep,
855                  gfp_t flags, int nodeid)
856 {
857         return NULL;
858 }
859 
860 static inline gfp_t gfp_exact_node(gfp_t flags)
861 {
862         return flags;
863 }
864 
865 #else   /* CONFIG_NUMA */
866 
867 static void *____cache_alloc_node(struct kmem_cache *, gfp_t, int);
868 static void *alternate_node_alloc(struct kmem_cache *, gfp_t);
869 
870 static struct alien_cache *__alloc_alien_cache(int node, int entries,
871                                                 int batch, gfp_t gfp)
872 {
873         size_t memsize = sizeof(void *) * entries + sizeof(struct alien_cache);
874         struct alien_cache *alc = NULL;
875 
876         alc = kmalloc_node(memsize, gfp, node);
877         init_arraycache(&alc->ac, entries, batch);
878         spin_lock_init(&alc->lock);
879         return alc;
880 }
881 
882 static struct alien_cache **alloc_alien_cache(int node, int limit, gfp_t gfp)
883 {
884         struct alien_cache **alc_ptr;
885         size_t memsize = sizeof(void *) * nr_node_ids;
886         int i;
887 
888         if (limit > 1)
889                 limit = 12;
890         alc_ptr = kzalloc_node(memsize, gfp, node);
891         if (!alc_ptr)
892                 return NULL;
893 
894         for_each_node(i) {
895                 if (i == node || !node_online(i))
896                         continue;
897                 alc_ptr[i] = __alloc_alien_cache(node, limit, 0xbaadf00d, gfp);
898                 if (!alc_ptr[i]) {
899                         for (i--; i >= 0; i--)
900                                 kfree(alc_ptr[i]);
901                         kfree(alc_ptr);
902                         return NULL;
903                 }
904         }
905         return alc_ptr;
906 }
907 
908 static void free_alien_cache(struct alien_cache **alc_ptr)
909 {
910         int i;
911 
912         if (!alc_ptr)
913                 return;
914         for_each_node(i)
915             kfree(alc_ptr[i]);
916         kfree(alc_ptr);
917 }
918 
919 static void __drain_alien_cache(struct kmem_cache *cachep,
920                                 struct array_cache *ac, int node,
921                                 struct list_head *list)
922 {
923         struct kmem_cache_node *n = get_node(cachep, node);
924 
925         if (ac->avail) {
926                 spin_lock(&n->list_lock);
927                 /*
928                  * Stuff objects into the remote nodes shared array first.
929                  * That way we could avoid the overhead of putting the objects
930                  * into the free lists and getting them back later.
931                  */
932                 if (n->shared)
933                         transfer_objects(n->shared, ac, ac->limit);
934 
935                 free_block(cachep, ac->entry, ac->avail, node, list);
936                 ac->avail = 0;
937                 spin_unlock(&n->list_lock);
938         }
939 }
940 
941 /*
942  * Called from cache_reap() to regularly drain alien caches round robin.
943  */
944 static void reap_alien(struct kmem_cache *cachep, struct kmem_cache_node *n)
945 {
946         int node = __this_cpu_read(slab_reap_node);
947 
948         if (n->alien) {
949                 struct alien_cache *alc = n->alien[node];
950                 struct array_cache *ac;
951 
952                 if (alc) {
953                         ac = &alc->ac;
954                         if (ac->avail && spin_trylock_irq(&alc->lock)) {
955                                 LIST_HEAD(list);
956 
957                                 __drain_alien_cache(cachep, ac, node, &list);
958                                 spin_unlock_irq(&alc->lock);
959                                 slabs_destroy(cachep, &list);
960                         }
961                 }
962         }
963 }
964 
965 static void drain_alien_cache(struct kmem_cache *cachep,
966                                 struct alien_cache **alien)
967 {
968         int i = 0;
969         struct alien_cache *alc;
970         struct array_cache *ac;
971         unsigned long flags;
972 
973         for_each_online_node(i) {
974                 alc = alien[i];
975                 if (alc) {
976                         LIST_HEAD(list);
977 
978                         ac = &alc->ac;
979                         spin_lock_irqsave(&alc->lock, flags);
980                         __drain_alien_cache(cachep, ac, i, &list);
981                         spin_unlock_irqrestore(&alc->lock, flags);
982                         slabs_destroy(cachep, &list);
983                 }
984         }
985 }
986 
987 static int __cache_free_alien(struct kmem_cache *cachep, void *objp,
988                                 int node, int page_node)
989 {
990         struct kmem_cache_node *n;
991         struct alien_cache *alien = NULL;
992         struct array_cache *ac;
993         LIST_HEAD(list);
994 
995         n = get_node(cachep, node);
996         STATS_INC_NODEFREES(cachep);
997         if (n->alien && n->alien[page_node]) {
998                 alien = n->alien[page_node];
999                 ac = &alien->ac;
1000                 spin_lock(&alien->lock);
1001                 if (unlikely(ac->avail == ac->limit)) {
1002                         STATS_INC_ACOVERFLOW(cachep);
1003                         __drain_alien_cache(cachep, ac, page_node, &list);
1004                 }
1005                 ac_put_obj(cachep, ac, objp);
1006                 spin_unlock(&alien->lock);
1007                 slabs_destroy(cachep, &list);
1008         } else {
1009                 n = get_node(cachep, page_node);
1010                 spin_lock(&n->list_lock);
1011                 free_block(cachep, &objp, 1, page_node, &list);
1012                 spin_unlock(&n->list_lock);
1013                 slabs_destroy(cachep, &list);
1014         }
1015         return 1;
1016 }
1017 
1018 static inline int cache_free_alien(struct kmem_cache *cachep, void *objp)
1019 {
1020         int page_node = page_to_nid(virt_to_page(objp));
1021         int node = numa_mem_id();
1022         /*
1023          * Make sure we are not freeing a object from another node to the array
1024          * cache on this cpu.
1025          */
1026         if (likely(node == page_node))
1027                 return 0;
1028 
1029         return __cache_free_alien(cachep, objp, node, page_node);
1030 }
1031 
1032 /*
1033  * Construct gfp mask to allocate from a specific node but do not invoke reclaim
1034  * or warn about failures.
1035  */
1036 static inline gfp_t gfp_exact_node(gfp_t flags)
1037 {
1038         return (flags | __GFP_THISNODE | __GFP_NOWARN) & ~__GFP_WAIT;
1039 }
1040 #endif
1041 
1042 /*
1043  * Allocates and initializes node for a node on each slab cache, used for
1044  * either memory or cpu hotplug.  If memory is being hot-added, the kmem_cache_node
1045  * will be allocated off-node since memory is not yet online for the new node.
1046  * When hotplugging memory or a cpu, existing node are not replaced if
1047  * already in use.
1048  *
1049  * Must hold slab_mutex.
1050  */
1051 static int init_cache_node_node(int node)
1052 {
1053         struct kmem_cache *cachep;
1054         struct kmem_cache_node *n;
1055         const size_t memsize = sizeof(struct kmem_cache_node);
1056 
1057         list_for_each_entry(cachep, &slab_caches, list) {
1058                 /*
1059                  * Set up the kmem_cache_node for cpu before we can
1060                  * begin anything. Make sure some other cpu on this
1061                  * node has not already allocated this
1062                  */
1063                 n = get_node(cachep, node);
1064                 if (!n) {
1065                         n = kmalloc_node(memsize, GFP_KERNEL, node);
1066                         if (!n)
1067                                 return -ENOMEM;
1068                         kmem_cache_node_init(n);
1069                         n->next_reap = jiffies + REAPTIMEOUT_NODE +
1070                             ((unsigned long)cachep) % REAPTIMEOUT_NODE;
1071 
1072                         /*
1073                          * The kmem_cache_nodes don't come and go as CPUs
1074                          * come and go.  slab_mutex is sufficient
1075                          * protection here.
1076                          */
1077                         cachep->node[node] = n;
1078                 }
1079 
1080                 spin_lock_irq(&n->list_lock);
1081                 n->free_limit =
1082                         (1 + nr_cpus_node(node)) *
1083                         cachep->batchcount + cachep->num;
1084                 spin_unlock_irq(&n->list_lock);
1085         }
1086         return 0;
1087 }
1088 
1089 static inline int slabs_tofree(struct kmem_cache *cachep,
1090                                                 struct kmem_cache_node *n)
1091 {
1092         return (n->free_objects + cachep->num - 1) / cachep->num;
1093 }
1094 
1095 static void cpuup_canceled(long cpu)
1096 {
1097         struct kmem_cache *cachep;
1098         struct kmem_cache_node *n = NULL;
1099         int node = cpu_to_mem(cpu);
1100         const struct cpumask *mask = cpumask_of_node(node);
1101 
1102         list_for_each_entry(cachep, &slab_caches, list) {
1103                 struct array_cache *nc;
1104                 struct array_cache *shared;
1105                 struct alien_cache **alien;
1106                 LIST_HEAD(list);
1107 
1108                 n = get_node(cachep, node);
1109                 if (!n)
1110                         continue;
1111 
1112                 spin_lock_irq(&n->list_lock);
1113 
1114                 /* Free limit for this kmem_cache_node */
1115                 n->free_limit -= cachep->batchcount;
1116 
1117                 /* cpu is dead; no one can alloc from it. */
1118                 nc = per_cpu_ptr(cachep->cpu_cache, cpu);
1119                 if (nc) {
1120                         free_block(cachep, nc->entry, nc->avail, node, &list);
1121                         nc->avail = 0;
1122                 }
1123 
1124                 if (!cpumask_empty(mask)) {
1125                         spin_unlock_irq(&n->list_lock);
1126                         goto free_slab;
1127                 }
1128 
1129                 shared = n->shared;
1130                 if (shared) {
1131                         free_block(cachep, shared->entry,
1132                                    shared->avail, node, &list);
1133                         n->shared = NULL;
1134                 }
1135 
1136                 alien = n->alien;
1137                 n->alien = NULL;
1138 
1139                 spin_unlock_irq(&n->list_lock);
1140 
1141                 kfree(shared);
1142                 if (alien) {
1143                         drain_alien_cache(cachep, alien);
1144                         free_alien_cache(alien);
1145                 }
1146 
1147 free_slab:
1148                 slabs_destroy(cachep, &list);
1149         }
1150         /*
1151          * In the previous loop, all the objects were freed to
1152          * the respective cache's slabs,  now we can go ahead and
1153          * shrink each nodelist to its limit.
1154          */
1155         list_for_each_entry(cachep, &slab_caches, list) {
1156                 n = get_node(cachep, node);
1157                 if (!n)
1158                         continue;
1159                 drain_freelist(cachep, n, slabs_tofree(cachep, n));
1160         }
1161 }
1162 
1163 static int cpuup_prepare(long cpu)
1164 {
1165         struct kmem_cache *cachep;
1166         struct kmem_cache_node *n = NULL;
1167         int node = cpu_to_mem(cpu);
1168         int err;
1169 
1170         /*
1171          * We need to do this right in the beginning since
1172          * alloc_arraycache's are going to use this list.
1173          * kmalloc_node allows us to add the slab to the right
1174          * kmem_cache_node and not this cpu's kmem_cache_node
1175          */
1176         err = init_cache_node_node(node);
1177         if (err < 0)
1178                 goto bad;
1179 
1180         /*
1181          * Now we can go ahead with allocating the shared arrays and
1182          * array caches
1183          */
1184         list_for_each_entry(cachep, &slab_caches, list) {
1185                 struct array_cache *shared = NULL;
1186                 struct alien_cache **alien = NULL;
1187 
1188                 if (cachep->shared) {
1189                         shared = alloc_arraycache(node,
1190                                 cachep->shared * cachep->batchcount,
1191                                 0xbaadf00d, GFP_KERNEL);
1192                         if (!shared)
1193                                 goto bad;
1194                 }
1195                 if (use_alien_caches) {
1196                         alien = alloc_alien_cache(node, cachep->limit, GFP_KERNEL);
1197                         if (!alien) {
1198                                 kfree(shared);
1199                                 goto bad;
1200                         }
1201                 }
1202                 n = get_node(cachep, node);
1203                 BUG_ON(!n);
1204 
1205                 spin_lock_irq(&n->list_lock);
1206                 if (!n->shared) {
1207                         /*
1208                          * We are serialised from CPU_DEAD or
1209                          * CPU_UP_CANCELLED by the cpucontrol lock
1210                          */
1211                         n->shared = shared;
1212                         shared = NULL;
1213                 }
1214 #ifdef CONFIG_NUMA
1215                 if (!n->alien) {
1216                         n->alien = alien;
1217                         alien = NULL;
1218                 }
1219 #endif
1220                 spin_unlock_irq(&n->list_lock);
1221                 kfree(shared);
1222                 free_alien_cache(alien);
1223         }
1224 
1225         return 0;
1226 bad:
1227         cpuup_canceled(cpu);
1228         return -ENOMEM;
1229 }
1230 
1231 static int cpuup_callback(struct notifier_block *nfb,
1232                                     unsigned long action, void *hcpu)
1233 {
1234         long cpu = (long)hcpu;
1235         int err = 0;
1236 
1237         switch (action) {
1238         case CPU_UP_PREPARE:
1239         case CPU_UP_PREPARE_FROZEN:
1240                 mutex_lock(&slab_mutex);
1241                 err = cpuup_prepare(cpu);
1242                 mutex_unlock(&slab_mutex);
1243                 break;
1244         case CPU_ONLINE:
1245         case CPU_ONLINE_FROZEN:
1246                 start_cpu_timer(cpu);
1247                 break;
1248 #ifdef CONFIG_HOTPLUG_CPU
1249         case CPU_DOWN_PREPARE:
1250         case CPU_DOWN_PREPARE_FROZEN:
1251                 /*
1252                  * Shutdown cache reaper. Note that the slab_mutex is
1253                  * held so that if cache_reap() is invoked it cannot do
1254                  * anything expensive but will only modify reap_work
1255                  * and reschedule the timer.
1256                 */
1257                 cancel_delayed_work_sync(&per_cpu(slab_reap_work, cpu));
1258                 /* Now the cache_reaper is guaranteed to be not running. */
1259                 per_cpu(slab_reap_work, cpu).work.func = NULL;
1260                 break;
1261         case CPU_DOWN_FAILED:
1262         case CPU_DOWN_FAILED_FROZEN:
1263                 start_cpu_timer(cpu);
1264                 break;
1265         case CPU_DEAD:
1266         case CPU_DEAD_FROZEN:
1267                 /*
1268                  * Even if all the cpus of a node are down, we don't free the
1269                  * kmem_cache_node of any cache. This to avoid a race between
1270                  * cpu_down, and a kmalloc allocation from another cpu for
1271                  * memory from the node of the cpu going down.  The node
1272                  * structure is usually allocated from kmem_cache_create() and
1273                  * gets destroyed at kmem_cache_destroy().
1274                  */
1275                 /* fall through */
1276 #endif
1277         case CPU_UP_CANCELED:
1278         case CPU_UP_CANCELED_FROZEN:
1279                 mutex_lock(&slab_mutex);
1280                 cpuup_canceled(cpu);
1281                 mutex_unlock(&slab_mutex);
1282                 break;
1283         }
1284         return notifier_from_errno(err);
1285 }
1286 
1287 static struct notifier_block cpucache_notifier = {
1288         &cpuup_callback, NULL, 0
1289 };
1290 
1291 #if defined(CONFIG_NUMA) && defined(CONFIG_MEMORY_HOTPLUG)
1292 /*
1293  * Drains freelist for a node on each slab cache, used for memory hot-remove.
1294  * Returns -EBUSY if all objects cannot be drained so that the node is not
1295  * removed.
1296  *
1297  * Must hold slab_mutex.
1298  */
1299 static int __meminit drain_cache_node_node(int node)
1300 {
1301         struct kmem_cache *cachep;
1302         int ret = 0;
1303 
1304         list_for_each_entry(cachep, &slab_caches, list) {
1305                 struct kmem_cache_node *n;
1306 
1307                 n = get_node(cachep, node);
1308                 if (!n)
1309                         continue;
1310 
1311                 drain_freelist(cachep, n, slabs_tofree(cachep, n));
1312 
1313                 if (!list_empty(&n->slabs_full) ||
1314                     !list_empty(&n->slabs_partial)) {
1315                         ret = -EBUSY;
1316                         break;
1317                 }
1318         }
1319         return ret;
1320 }
1321 
1322 static int __meminit slab_memory_callback(struct notifier_block *self,
1323                                         unsigned long action, void *arg)
1324 {
1325         struct memory_notify *mnb = arg;
1326         int ret = 0;
1327         int nid;
1328 
1329         nid = mnb->status_change_nid;
1330         if (nid < 0)
1331                 goto out;
1332 
1333         switch (action) {
1334         case MEM_GOING_ONLINE:
1335                 mutex_lock(&slab_mutex);
1336                 ret = init_cache_node_node(nid);
1337                 mutex_unlock(&slab_mutex);
1338                 break;
1339         case MEM_GOING_OFFLINE:
1340                 mutex_lock(&slab_mutex);
1341                 ret = drain_cache_node_node(nid);
1342                 mutex_unlock(&slab_mutex);
1343                 break;
1344         case MEM_ONLINE:
1345         case MEM_OFFLINE:
1346         case MEM_CANCEL_ONLINE:
1347         case MEM_CANCEL_OFFLINE:
1348                 break;
1349         }
1350 out:
1351         return notifier_from_errno(ret);
1352 }
1353 #endif /* CONFIG_NUMA && CONFIG_MEMORY_HOTPLUG */
1354 
1355 /*
1356  * swap the static kmem_cache_node with kmalloced memory
1357  */
1358 static void __init init_list(struct kmem_cache *cachep, struct kmem_cache_node *list,
1359                                 int nodeid)
1360 {
1361         struct kmem_cache_node *ptr;
1362 
1363         ptr = kmalloc_node(sizeof(struct kmem_cache_node), GFP_NOWAIT, nodeid);
1364         BUG_ON(!ptr);
1365 
1366         memcpy(ptr, list, sizeof(struct kmem_cache_node));
1367         /*
1368          * Do not assume that spinlocks can be initialized via memcpy:
1369          */
1370         spin_lock_init(&ptr->list_lock);
1371 
1372         MAKE_ALL_LISTS(cachep, ptr, nodeid);
1373         cachep->node[nodeid] = ptr;
1374 }
1375 
1376 /*
1377  * For setting up all the kmem_cache_node for cache whose buffer_size is same as
1378  * size of kmem_cache_node.
1379  */
1380 static void __init set_up_node(struct kmem_cache *cachep, int index)
1381 {
1382         int node;
1383 
1384         for_each_online_node(node) {
1385                 cachep->node[node] = &init_kmem_cache_node[index + node];
1386                 cachep->node[node]->next_reap = jiffies +
1387                     REAPTIMEOUT_NODE +
1388                     ((unsigned long)cachep) % REAPTIMEOUT_NODE;
1389         }
1390 }
1391 
1392 /*
1393  * Initialisation.  Called after the page allocator have been initialised and
1394  * before smp_init().
1395  */
1396 void __init kmem_cache_init(void)
1397 {
1398         int i;
1399 
1400         BUILD_BUG_ON(sizeof(((struct page *)NULL)->lru) <
1401                                         sizeof(struct rcu_head));
1402         kmem_cache = &kmem_cache_boot;
1403 
1404         if (num_possible_nodes() == 1)
1405                 use_alien_caches = 0;
1406 
1407         for (i = 0; i < NUM_INIT_LISTS; i++)
1408                 kmem_cache_node_init(&init_kmem_cache_node[i]);
1409 
1410         /*
1411          * Fragmentation resistance on low memory - only use bigger
1412          * page orders on machines with more than 32MB of memory if
1413          * not overridden on the command line.
1414          */
1415         if (!slab_max_order_set && totalram_pages > (32 << 20) >> PAGE_SHIFT)
1416                 slab_max_order = SLAB_MAX_ORDER_HI;
1417 
1418         /* Bootstrap is tricky, because several objects are allocated
1419          * from caches that do not exist yet:
1420          * 1) initialize the kmem_cache cache: it contains the struct
1421          *    kmem_cache structures of all caches, except kmem_cache itself:
1422          *    kmem_cache is statically allocated.
1423          *    Initially an __init data area is used for the head array and the
1424          *    kmem_cache_node structures, it's replaced with a kmalloc allocated
1425          *    array at the end of the bootstrap.
1426          * 2) Create the first kmalloc cache.
1427          *    The struct kmem_cache for the new cache is allocated normally.
1428          *    An __init data area is used for the head array.
1429          * 3) Create the remaining kmalloc caches, with minimally sized
1430          *    head arrays.
1431          * 4) Replace the __init data head arrays for kmem_cache and the first
1432          *    kmalloc cache with kmalloc allocated arrays.
1433          * 5) Replace the __init data for kmem_cache_node for kmem_cache and
1434          *    the other cache's with kmalloc allocated memory.
1435          * 6) Resize the head arrays of the kmalloc caches to their final sizes.
1436          */
1437 
1438         /* 1) create the kmem_cache */
1439 
1440         /*
1441          * struct kmem_cache size depends on nr_node_ids & nr_cpu_ids
1442          */
1443         create_boot_cache(kmem_cache, "kmem_cache",
1444                 offsetof(struct kmem_cache, node) +
1445                                   nr_node_ids * sizeof(struct kmem_cache_node *),
1446                                   SLAB_HWCACHE_ALIGN);
1447         list_add(&kmem_cache->list, &slab_caches);
1448         slab_state = PARTIAL;
1449 
1450         /*
1451          * Initialize the caches that provide memory for the  kmem_cache_node
1452          * structures first.  Without this, further allocations will bug.
1453          */
1454         kmalloc_caches[INDEX_NODE] = create_kmalloc_cache("kmalloc-node",
1455                                 kmalloc_size(INDEX_NODE), ARCH_KMALLOC_FLAGS);
1456         slab_state = PARTIAL_NODE;
1457 
1458         slab_early_init = 0;
1459 
1460         /* 5) Replace the bootstrap kmem_cache_node */
1461         {
1462                 int nid;
1463 
1464                 for_each_online_node(nid) {
1465                         init_list(kmem_cache, &init_kmem_cache_node[CACHE_CACHE + nid], nid);
1466 
1467                         init_list(kmalloc_caches[INDEX_NODE],
1468                                           &init_kmem_cache_node[SIZE_NODE + nid], nid);
1469                 }
1470         }
1471 
1472         create_kmalloc_caches(ARCH_KMALLOC_FLAGS);
1473 }
1474 
1475 void __init kmem_cache_init_late(void)
1476 {
1477         struct kmem_cache *cachep;
1478 
1479         slab_state = UP;
1480 
1481         /* 6) resize the head arrays to their final sizes */
1482         mutex_lock(&slab_mutex);
1483         list_for_each_entry(cachep, &slab_caches, list)
1484                 if (enable_cpucache(cachep, GFP_NOWAIT))
1485                         BUG();
1486         mutex_unlock(&slab_mutex);
1487 
1488         /* Done! */
1489         slab_state = FULL;
1490 
1491         /*
1492          * Register a cpu startup notifier callback that initializes
1493          * cpu_cache_get for all new cpus
1494          */
1495         register_cpu_notifier(&cpucache_notifier);
1496 
1497 #ifdef CONFIG_NUMA
1498         /*
1499          * Register a memory hotplug callback that initializes and frees
1500          * node.
1501          */
1502         hotplug_memory_notifier(slab_memory_callback, SLAB_CALLBACK_PRI);
1503 #endif
1504 
1505         /*
1506          * The reap timers are started later, with a module init call: That part
1507          * of the kernel is not yet operational.
1508          */
1509 }
1510 
1511 static int __init cpucache_init(void)
1512 {
1513         int cpu;
1514 
1515         /*
1516          * Register the timers that return unneeded pages to the page allocator
1517          */
1518         for_each_online_cpu(cpu)
1519                 start_cpu_timer(cpu);
1520 
1521         /* Done! */
1522         slab_state = FULL;
1523         return 0;
1524 }
1525 __initcall(cpucache_init);
1526 
1527 static noinline void
1528 slab_out_of_memory(struct kmem_cache *cachep, gfp_t gfpflags, int nodeid)
1529 {
1530 #if DEBUG
1531         struct kmem_cache_node *n;
1532         struct page *page;
1533         unsigned long flags;
1534         int node;
1535         static DEFINE_RATELIMIT_STATE(slab_oom_rs, DEFAULT_RATELIMIT_INTERVAL,
1536                                       DEFAULT_RATELIMIT_BURST);
1537 
1538         if ((gfpflags & __GFP_NOWARN) || !__ratelimit(&slab_oom_rs))
1539                 return;
1540 
1541         printk(KERN_WARNING
1542                 "SLAB: Unable to allocate memory on node %d (gfp=0x%x)\n",
1543                 nodeid, gfpflags);
1544         printk(KERN_WARNING "  cache: %s, object size: %d, order: %d\n",
1545                 cachep->name, cachep->size, cachep->gfporder);
1546 
1547         for_each_kmem_cache_node(cachep, node, n) {
1548                 unsigned long active_objs = 0, num_objs = 0, free_objects = 0;
1549                 unsigned long active_slabs = 0, num_slabs = 0;
1550 
1551                 spin_lock_irqsave(&n->list_lock, flags);
1552                 list_for_each_entry(page, &n->slabs_full, lru) {
1553                         active_objs += cachep->num;
1554                         active_slabs++;
1555                 }
1556                 list_for_each_entry(page, &n->slabs_partial, lru) {
1557                         active_objs += page->active;
1558                         active_slabs++;
1559                 }
1560                 list_for_each_entry(page, &n->slabs_free, lru)
1561                         num_slabs++;
1562 
1563                 free_objects += n->free_objects;
1564                 spin_unlock_irqrestore(&n->list_lock, flags);
1565 
1566                 num_slabs += active_slabs;
1567                 num_objs = num_slabs * cachep->num;
1568                 printk(KERN_WARNING
1569                         "  node %d: slabs: %ld/%ld, objs: %ld/%ld, free: %ld\n",
1570                         node, active_slabs, num_slabs, active_objs, num_objs,
1571                         free_objects);
1572         }
1573 #endif
1574 }
1575 
1576 /*
1577  * Interface to system's page allocator. No need to hold the
1578  * kmem_cache_node ->list_lock.
1579  *
1580  * If we requested dmaable memory, we will get it. Even if we
1581  * did not request dmaable memory, we might get it, but that
1582  * would be relatively rare and ignorable.
1583  */
1584 static struct page *kmem_getpages(struct kmem_cache *cachep, gfp_t flags,
1585                                                                 int nodeid)
1586 {
1587         struct page *page;
1588         int nr_pages;
1589 
1590         flags |= cachep->allocflags;
1591         if (cachep->flags & SLAB_RECLAIM_ACCOUNT)
1592                 flags |= __GFP_RECLAIMABLE;
1593 
1594         if (memcg_charge_slab(cachep, flags, cachep->gfporder))
1595                 return NULL;
1596 
1597         page = alloc_pages_exact_node(nodeid, flags | __GFP_NOTRACK, cachep->gfporder);
1598         if (!page) {
1599                 memcg_uncharge_slab(cachep, cachep->gfporder);
1600                 slab_out_of_memory(cachep, flags, nodeid);
1601                 return NULL;
1602         }
1603 
1604         /* Record if ALLOC_NO_WATERMARKS was set when allocating the slab */
1605         if (unlikely(page->pfmemalloc))
1606                 pfmemalloc_active = true;
1607 
1608         nr_pages = (1 << cachep->gfporder);
1609         if (cachep->flags & SLAB_RECLAIM_ACCOUNT)
1610                 add_zone_page_state(page_zone(page),
1611                         NR_SLAB_RECLAIMABLE, nr_pages);
1612         else
1613                 add_zone_page_state(page_zone(page),
1614                         NR_SLAB_UNRECLAIMABLE, nr_pages);
1615         __SetPageSlab(page);
1616         if (page->pfmemalloc)
1617                 SetPageSlabPfmemalloc(page);
1618 
1619         if (kmemcheck_enabled && !(cachep->flags & SLAB_NOTRACK)) {
1620                 kmemcheck_alloc_shadow(page, cachep->gfporder, flags, nodeid);
1621 
1622                 if (cachep->ctor)
1623                         kmemcheck_mark_uninitialized_pages(page, nr_pages);
1624                 else
1625                         kmemcheck_mark_unallocated_pages(page, nr_pages);
1626         }
1627 
1628         return page;
1629 }
1630 
1631 /*
1632  * Interface to system's page release.
1633  */
1634 static void kmem_freepages(struct kmem_cache *cachep, struct page *page)
1635 {
1636         const unsigned long nr_freed = (1 << cachep->gfporder);
1637 
1638         kmemcheck_free_shadow(page, cachep->gfporder);
1639 
1640         if (cachep->flags & SLAB_RECLAIM_ACCOUNT)
1641                 sub_zone_page_state(page_zone(page),
1642                                 NR_SLAB_RECLAIMABLE, nr_freed);
1643         else
1644                 sub_zone_page_state(page_zone(page),
1645                                 NR_SLAB_UNRECLAIMABLE, nr_freed);
1646 
1647         BUG_ON(!PageSlab(page));
1648         __ClearPageSlabPfmemalloc(page);
1649         __ClearPageSlab(page);
1650         page_mapcount_reset(page);
1651         page->mapping = NULL;
1652 
1653         if (current->reclaim_state)
1654                 current->reclaim_state->reclaimed_slab += nr_freed;
1655         __free_pages(page, cachep->gfporder);
1656         memcg_uncharge_slab(cachep, cachep->gfporder);
1657 }
1658 
1659 static void kmem_rcu_free(struct rcu_head *head)
1660 {
1661         struct kmem_cache *cachep;
1662         struct page *page;
1663 
1664         page = container_of(head, struct page, rcu_head);
1665         cachep = page->slab_cache;
1666 
1667         kmem_freepages(cachep, page);
1668 }
1669 
1670 #if DEBUG
1671 
1672 #ifdef CONFIG_DEBUG_PAGEALLOC
1673 static void store_stackinfo(struct kmem_cache *cachep, unsigned long *addr,
1674                             unsigned long caller)
1675 {
1676         int size = cachep->object_size;
1677 
1678         addr = (unsigned long *)&((char *)addr)[obj_offset(cachep)];
1679 
1680         if (size < 5 * sizeof(unsigned long))
1681                 return;
1682 
1683         *addr++ = 0x12345678;
1684         *addr++ = caller;
1685         *addr++ = smp_processor_id();
1686         size -= 3 * sizeof(unsigned long);
1687         {
1688                 unsigned long *sptr = &caller;
1689                 unsigned long svalue;
1690 
1691                 while (!kstack_end(sptr)) {
1692                         svalue = *sptr++;
1693                         if (kernel_text_address(svalue)) {
1694                                 *addr++ = svalue;
1695                                 size -= sizeof(unsigned long);
1696                                 if (size <= sizeof(unsigned long))
1697                                         break;
1698                         }
1699                 }
1700 
1701         }
1702         *addr++ = 0x87654321;
1703 }
1704 #endif
1705 
1706 static void poison_obj(struct kmem_cache *cachep, void *addr, unsigned char val)
1707 {
1708         int size = cachep->object_size;
1709         addr = &((char *)addr)[obj_offset(cachep)];
1710 
1711         memset(addr, val, size);
1712         *(unsigned char *)(addr + size - 1) = POISON_END;
1713 }
1714 
1715 static void dump_line(char *data, int offset, int limit)
1716 {
1717         int i;
1718         unsigned char error = 0;
1719         int bad_count = 0;
1720 
1721         printk(KERN_ERR "%03x: ", offset);
1722         for (i = 0; i < limit; i++) {
1723                 if (data[offset + i] != POISON_FREE) {
1724                         error = data[offset + i];
1725                         bad_count++;
1726                 }
1727         }
1728         print_hex_dump(KERN_CONT, "", 0, 16, 1,
1729                         &data[offset], limit, 1);
1730 
1731         if (bad_count == 1) {
1732                 error ^= POISON_FREE;
1733                 if (!(error & (error - 1))) {
1734                         printk(KERN_ERR "Single bit error detected. Probably "
1735                                         "bad RAM.\n");
1736 #ifdef CONFIG_X86
1737                         printk(KERN_ERR "Run memtest86+ or a similar memory "
1738                                         "test tool.\n");
1739 #else
1740                         printk(KERN_ERR "Run a memory test tool.\n");
1741 #endif
1742                 }
1743         }
1744 }
1745 #endif
1746 
1747 #if DEBUG
1748 
1749 static void print_objinfo(struct kmem_cache *cachep, void *objp, int lines)
1750 {
1751         int i, size;
1752         char *realobj;
1753 
1754         if (cachep->flags & SLAB_RED_ZONE) {
1755                 printk(KERN_ERR "Redzone: 0x%llx/0x%llx.\n",
1756                         *dbg_redzone1(cachep, objp),
1757                         *dbg_redzone2(cachep, objp));
1758         }
1759 
1760         if (cachep->flags & SLAB_STORE_USER) {
1761                 printk(KERN_ERR "Last user: [<%p>](%pSR)\n",
1762                        *dbg_userword(cachep, objp),
1763                        *dbg_userword(cachep, objp));
1764         }
1765         realobj = (char *)objp + obj_offset(cachep);
1766         size = cachep->object_size;
1767         for (i = 0; i < size && lines; i += 16, lines--) {
1768                 int limit;
1769                 limit = 16;
1770                 if (i + limit > size)
1771                         limit = size - i;
1772                 dump_line(realobj, i, limit);
1773         }
1774 }
1775 
1776 static void check_poison_obj(struct kmem_cache *cachep, void *objp)
1777 {
1778         char *realobj;
1779         int size, i;
1780         int lines = 0;
1781 
1782         realobj = (char *)objp + obj_offset(cachep);
1783         size = cachep->object_size;
1784 
1785         for (i = 0; i < size; i++) {
1786                 char exp = POISON_FREE;
1787                 if (i == size - 1)
1788                         exp = POISON_END;
1789                 if (realobj[i] != exp) {
1790                         int limit;
1791                         /* Mismatch ! */
1792                         /* Print header */
1793                         if (lines == 0) {
1794                                 printk(KERN_ERR
1795                                         "Slab corruption (%s): %s start=%p, len=%d\n",
1796                                         print_tainted(), cachep->name, realobj, size);
1797                                 print_objinfo(cachep, objp, 0);
1798                         }
1799                         /* Hexdump the affected line */
1800                         i = (i / 16) * 16;
1801                         limit = 16;
1802                         if (i + limit > size)
1803                                 limit = size - i;
1804                         dump_line(realobj, i, limit);
1805                         i += 16;
1806                         lines++;
1807                         /* Limit to 5 lines */
1808                         if (lines > 5)
1809                                 break;
1810                 }
1811         }
1812         if (lines != 0) {
1813                 /* Print some data about the neighboring objects, if they
1814                  * exist:
1815                  */
1816                 struct page *page = virt_to_head_page(objp);
1817                 unsigned int objnr;
1818 
1819                 objnr = obj_to_index(cachep, page, objp);
1820                 if (objnr) {
1821                         objp = index_to_obj(cachep, page, objnr - 1);
1822                         realobj = (char *)objp + obj_offset(cachep);
1823                         printk(KERN_ERR "Prev obj: start=%p, len=%d\n",
1824                                realobj, size);
1825                         print_objinfo(cachep, objp, 2);
1826                 }
1827                 if (objnr + 1 < cachep->num) {
1828                         objp = index_to_obj(cachep, page, objnr + 1);
1829                         realobj = (char *)objp + obj_offset(cachep);
1830                         printk(KERN_ERR "Next obj: start=%p, len=%d\n",
1831                                realobj, size);
1832                         print_objinfo(cachep, objp, 2);
1833                 }
1834         }
1835 }
1836 #endif
1837 
1838 #if DEBUG
1839 static void slab_destroy_debugcheck(struct kmem_cache *cachep,
1840                                                 struct page *page)
1841 {
1842         int i;
1843         for (i = 0; i < cachep->num; i++) {
1844                 void *objp = index_to_obj(cachep, page, i);
1845 
1846                 if (cachep->flags & SLAB_POISON) {
1847 #ifdef CONFIG_DEBUG_PAGEALLOC
1848                         if (cachep->size % PAGE_SIZE == 0 &&
1849                                         OFF_SLAB(cachep))
1850                                 kernel_map_pages(virt_to_page(objp),
1851                                         cachep->size / PAGE_SIZE, 1);
1852                         else
1853                                 check_poison_obj(cachep, objp);
1854 #else
1855                         check_poison_obj(cachep, objp);
1856 #endif
1857                 }
1858                 if (cachep->flags & SLAB_RED_ZONE) {
1859                         if (*dbg_redzone1(cachep, objp) != RED_INACTIVE)
1860                                 slab_error(cachep, "start of a freed object "
1861                                            "was overwritten");
1862                         if (*dbg_redzone2(cachep, objp) != RED_INACTIVE)
1863                                 slab_error(cachep, "end of a freed object "
1864                                            "was overwritten");
1865                 }
1866         }
1867 }
1868 #else
1869 static void slab_destroy_debugcheck(struct kmem_cache *cachep,
1870                                                 struct page *page)
1871 {
1872 }
1873 #endif
1874 
1875 /**
1876  * slab_destroy - destroy and release all objects in a slab
1877  * @cachep: cache pointer being destroyed
1878  * @page: page pointer being destroyed
1879  *
1880  * Destroy all the objs in a slab page, and release the mem back to the system.
1881  * Before calling the slab page must have been unlinked from the cache. The
1882  * kmem_cache_node ->list_lock is not held/needed.
1883  */
1884 static void slab_destroy(struct kmem_cache *cachep, struct page *page)
1885 {
1886         void *freelist;
1887 
1888         freelist = page->freelist;
1889         slab_destroy_debugcheck(cachep, page);
1890         if (unlikely(cachep->flags & SLAB_DESTROY_BY_RCU)) {
1891                 struct rcu_head *head;
1892 
1893                 /*
1894                  * RCU free overloads the RCU head over the LRU.
1895                  * slab_page has been overloeaded over the LRU,
1896                  * however it is not used from now on so that
1897                  * we can use it safely.
1898                  */
1899                 head = (void *)&page->rcu_head;
1900                 call_rcu(head, kmem_rcu_free);
1901 
1902         } else {
1903                 kmem_freepages(cachep, page);
1904         }
1905 
1906         /*
1907          * From now on, we don't use freelist
1908          * although actual page can be freed in rcu context
1909          */
1910         if (OFF_SLAB(cachep))
1911                 kmem_cache_free(cachep->freelist_cache, freelist);
1912 }
1913 
1914 static void slabs_destroy(struct kmem_cache *cachep, struct list_head *list)
1915 {
1916         struct page *page, *n;
1917 
1918         list_for_each_entry_safe(page, n, list, lru) {
1919                 list_del(&page->lru);
1920                 slab_destroy(cachep, page);
1921         }
1922 }
1923 
1924 /**
1925  * calculate_slab_order - calculate size (page order) of slabs
1926  * @cachep: pointer to the cache that is being created
1927  * @size: size of objects to be created in this cache.
1928  * @align: required alignment for the objects.
1929  * @flags: slab allocation flags
1930  *
1931  * Also calculates the number of objects per slab.
1932  *
1933  * This could be made much more intelligent.  For now, try to avoid using
1934  * high order pages for slabs.  When the gfp() functions are more friendly
1935  * towards high-order requests, this should be changed.
1936  */
1937 static size_t calculate_slab_order(struct kmem_cache *cachep,
1938                         size_t size, size_t align, unsigned long flags)
1939 {
1940         unsigned long offslab_limit;
1941         size_t left_over = 0;
1942         int gfporder;
1943 
1944         for (gfporder = 0; gfporder <= KMALLOC_MAX_ORDER; gfporder++) {
1945                 unsigned int num;
1946                 size_t remainder;
1947 
1948                 cache_estimate(gfporder, size, align, flags, &remainder, &num);
1949                 if (!num)
1950                         continue;
1951 
1952                 /* Can't handle number of objects more than SLAB_OBJ_MAX_NUM */
1953                 if (num > SLAB_OBJ_MAX_NUM)
1954                         break;
1955 
1956                 if (flags & CFLGS_OFF_SLAB) {
1957                         size_t freelist_size_per_obj = sizeof(freelist_idx_t);
1958                         /*
1959                          * Max number of objs-per-slab for caches which
1960                          * use off-slab slabs. Needed to avoid a possible
1961                          * looping condition in cache_grow().
1962                          */
1963                         if (IS_ENABLED(CONFIG_DEBUG_SLAB_LEAK))
1964                                 freelist_size_per_obj += sizeof(char);
1965                         offslab_limit = size;
1966                         offslab_limit /= freelist_size_per_obj;
1967 
1968                         if (num > offslab_limit)
1969                                 break;
1970                 }
1971 
1972                 /* Found something acceptable - save it away */
1973                 cachep->num = num;
1974                 cachep->gfporder = gfporder;
1975                 left_over = remainder;
1976 
1977                 /*
1978                  * A VFS-reclaimable slab tends to have most allocations
1979                  * as GFP_NOFS and we really don't want to have to be allocating
1980                  * higher-order pages when we are unable to shrink dcache.
1981                  */
1982                 if (flags & SLAB_RECLAIM_ACCOUNT)
1983                         break;
1984 
1985                 /*
1986                  * Large number of objects is good, but very large slabs are
1987                  * currently bad for the gfp()s.
1988                  */
1989                 if (gfporder >= slab_max_order)
1990                         break;
1991 
1992                 /*
1993                  * Acceptable internal fragmentation?
1994                  */
1995                 if (left_over * 8 <= (PAGE_SIZE << gfporder))
1996                         break;
1997         }
1998         return left_over;
1999 }
2000 
2001 static struct array_cache __percpu *alloc_kmem_cache_cpus(
2002                 struct kmem_cache *cachep, int entries, int batchcount)
2003 {
2004         int cpu;
2005         size_t size;
2006         struct array_cache __percpu *cpu_cache;
2007 
2008         size = sizeof(void *) * entries + sizeof(struct array_cache);
2009         cpu_cache = __alloc_percpu(size, sizeof(void *));
2010 
2011         if (!cpu_cache)
2012                 return NULL;
2013 
2014         for_each_possible_cpu(cpu) {
2015                 init_arraycache(per_cpu_ptr(cpu_cache, cpu),
2016                                 entries, batchcount);
2017         }
2018 
2019         return cpu_cache;
2020 }
2021 
2022 static int __init_refok setup_cpu_cache(struct kmem_cache *cachep, gfp_t gfp)
2023 {
2024         if (slab_state >= FULL)
2025                 return enable_cpucache(cachep, gfp);
2026 
2027         cachep->cpu_cache = alloc_kmem_cache_cpus(cachep, 1, 1);
2028         if (!cachep->cpu_cache)
2029                 return 1;
2030 
2031         if (slab_state == DOWN) {
2032                 /* Creation of first cache (kmem_cache). */
2033                 set_up_node(kmem_cache, CACHE_CACHE);
2034         } else if (slab_state == PARTIAL) {
2035                 /* For kmem_cache_node */
2036                 set_up_node(cachep, SIZE_NODE);
2037         } else {
2038                 int node;
2039 
2040                 for_each_online_node(node) {
2041                         cachep->node[node] = kmalloc_node(
2042                                 sizeof(struct kmem_cache_node), gfp, node);
2043                         BUG_ON(!cachep->node[node]);
2044                         kmem_cache_node_init(cachep->node[node]);
2045                 }
2046         }
2047 
2048         cachep->node[numa_mem_id()]->next_reap =
2049                         jiffies + REAPTIMEOUT_NODE +
2050                         ((unsigned long)cachep) % REAPTIMEOUT_NODE;
2051 
2052         cpu_cache_get(cachep)->avail = 0;
2053         cpu_cache_get(cachep)->limit = BOOT_CPUCACHE_ENTRIES;
2054         cpu_cache_get(cachep)->batchcount = 1;
2055         cpu_cache_get(cachep)->touched = 0;
2056         cachep->batchcount = 1;
2057         cachep->limit = BOOT_CPUCACHE_ENTRIES;
2058         return 0;
2059 }
2060 
2061 unsigned long kmem_cache_flags(unsigned long object_size,
2062         unsigned long flags, const char *name,
2063         void (*ctor)(void *))
2064 {
2065         return flags;
2066 }
2067 
2068 struct kmem_cache *
2069 __kmem_cache_alias(const char *name, size_t size, size_t align,
2070                    unsigned long flags, void (*ctor)(void *))
2071 {
2072         struct kmem_cache *cachep;
2073 
2074         cachep = find_mergeable(size, align, flags, name, ctor);
2075         if (cachep) {
2076                 cachep->refcount++;
2077 
2078                 /*
2079                  * Adjust the object sizes so that we clear
2080                  * the complete object on kzalloc.
2081                  */
2082                 cachep->object_size = max_t(int, cachep->object_size, size);
2083         }
2084         return cachep;
2085 }
2086 
2087 /**
2088  * __kmem_cache_create - Create a cache.
2089  * @cachep: cache management descriptor
2090  * @flags: SLAB flags
2091  *
2092  * Returns a ptr to the cache on success, NULL on failure.
2093  * Cannot be called within a int, but can be interrupted.
2094  * The @ctor is run when new pages are allocated by the cache.
2095  *
2096  * The flags are
2097  *
2098  * %SLAB_POISON - Poison the slab with a known test pattern (a5a5a5a5)
2099  * to catch references to uninitialised memory.
2100  *
2101  * %SLAB_RED_ZONE - Insert `Red' zones around the allocated memory to check
2102  * for buffer overruns.
2103  *
2104  * %SLAB_HWCACHE_ALIGN - Align the objects in this cache to a hardware
2105  * cacheline.  This can be beneficial if you're counting cycles as closely
2106  * as davem.
2107  */
2108 int
2109 __kmem_cache_create (struct kmem_cache *cachep, unsigned long flags)
2110 {
2111         size_t left_over, freelist_size;
2112         size_t ralign = BYTES_PER_WORD;
2113         gfp_t gfp;
2114         int err;
2115         size_t size = cachep->size;
2116 
2117 #if DEBUG
2118 #if FORCED_DEBUG
2119         /*
2120          * Enable redzoning and last user accounting, except for caches with
2121          * large objects, if the increased size would increase the object size
2122          * above the next power of two: caches with object sizes just above a
2123          * power of two have a significant amount of internal fragmentation.
2124          */
2125         if (size < 4096 || fls(size - 1) == fls(size-1 + REDZONE_ALIGN +
2126                                                 2 * sizeof(unsigned long long)))
2127                 flags |= SLAB_RED_ZONE | SLAB_STORE_USER;
2128         if (!(flags & SLAB_DESTROY_BY_RCU))
2129                 flags |= SLAB_POISON;
2130 #endif
2131         if (flags & SLAB_DESTROY_BY_RCU)
2132                 BUG_ON(flags & SLAB_POISON);
2133 #endif
2134 
2135         /*
2136          * Check that size is in terms of words.  This is needed to avoid
2137          * unaligned accesses for some archs when redzoning is used, and makes
2138          * sure any on-slab bufctl's are also correctly aligned.
2139          */
2140         if (size & (BYTES_PER_WORD - 1)) {
2141                 size += (BYTES_PER_WORD - 1);
2142                 size &= ~(BYTES_PER_WORD - 1);
2143         }
2144 
2145         if (flags & SLAB_RED_ZONE) {
2146                 ralign = REDZONE_ALIGN;
2147                 /* If redzoning, ensure that the second redzone is suitably
2148                  * aligned, by adjusting the object size accordingly. */
2149                 size += REDZONE_ALIGN - 1;
2150                 size &= ~(REDZONE_ALIGN - 1);
2151         }
2152 
2153         /* 3) caller mandated alignment */
2154         if (ralign < cachep->align) {
2155                 ralign = cachep->align;
2156         }
2157         /* disable debug if necessary */
2158         if (ralign > __alignof__(unsigned long long))
2159                 flags &= ~(SLAB_RED_ZONE | SLAB_STORE_USER);
2160         /*
2161          * 4) Store it.
2162          */
2163         cachep->align = ralign;
2164 
2165         if (slab_is_available())
2166                 gfp = GFP_KERNEL;
2167         else
2168                 gfp = GFP_NOWAIT;
2169 
2170 #if DEBUG
2171 
2172         /*
2173          * Both debugging options require word-alignment which is calculated
2174          * into align above.
2175          */
2176         if (flags & SLAB_RED_ZONE) {
2177                 /* add space for red zone words */
2178                 cachep->obj_offset += sizeof(unsigned long long);
2179                 size += 2 * sizeof(unsigned long long);
2180         }
2181         if (flags & SLAB_STORE_USER) {
2182                 /* user store requires one word storage behind the end of
2183                  * the real object. But if the second red zone needs to be
2184                  * aligned to 64 bits, we must allow that much space.
2185                  */
2186                 if (flags & SLAB_RED_ZONE)
2187                         size += REDZONE_ALIGN;
2188                 else
2189                         size += BYTES_PER_WORD;
2190         }
2191 #if FORCED_DEBUG && defined(CONFIG_DEBUG_PAGEALLOC)
2192         if (size >= kmalloc_size(INDEX_NODE + 1)
2193             && cachep->object_size > cache_line_size()
2194             && ALIGN(size, cachep->align) < PAGE_SIZE) {
2195                 cachep->obj_offset += PAGE_SIZE - ALIGN(size, cachep->align);
2196                 size = PAGE_SIZE;
2197         }
2198 #endif
2199 #endif
2200 
2201         /*
2202          * Determine if the slab management is 'on' or 'off' slab.
2203          * (bootstrapping cannot cope with offslab caches so don't do
2204          * it too early on. Always use on-slab management when
2205          * SLAB_NOLEAKTRACE to avoid recursive calls into kmemleak)
2206          */
2207         if ((size >= (PAGE_SIZE >> 5)) && !slab_early_init &&
2208             !(flags & SLAB_NOLEAKTRACE))
2209                 /*
2210                  * Size is large, assume best to place the slab management obj
2211                  * off-slab (should allow better packing of objs).
2212                  */
2213                 flags |= CFLGS_OFF_SLAB;
2214 
2215         size = ALIGN(size, cachep->align);
2216         /*
2217          * We should restrict the number of objects in a slab to implement
2218          * byte sized index. Refer comment on SLAB_OBJ_MIN_SIZE definition.
2219          */
2220         if (FREELIST_BYTE_INDEX && size < SLAB_OBJ_MIN_SIZE)
2221                 size = ALIGN(SLAB_OBJ_MIN_SIZE, cachep->align);
2222 
2223         left_over = calculate_slab_order(cachep, size, cachep->align, flags);
2224 
2225         if (!cachep->num)
2226                 return -E2BIG;
2227 
2228         freelist_size = calculate_freelist_size(cachep->num, cachep->align);
2229 
2230         /*
2231          * If the slab has been placed off-slab, and we have enough space then
2232          * move it on-slab. This is at the expense of any extra colouring.
2233          */
2234         if (flags & CFLGS_OFF_SLAB && left_over >= freelist_size) {
2235                 flags &= ~CFLGS_OFF_SLAB;
2236                 left_over -= freelist_size;
2237         }
2238 
2239         if (flags & CFLGS_OFF_SLAB) {
2240                 /* really off slab. No need for manual alignment */
2241                 freelist_size = calculate_freelist_size(cachep->num, 0);
2242 
2243 #ifdef CONFIG_PAGE_POISONING
2244                 /* If we're going to use the generic kernel_map_pages()
2245                  * poisoning, then it's going to smash the contents of
2246                  * the redzone and userword anyhow, so switch them off.
2247                  */
2248                 if (size % PAGE_SIZE == 0 && flags & SLAB_POISON)
2249                         flags &= ~(SLAB_RED_ZONE | SLAB_STORE_USER);
2250 #endif
2251         }
2252 
2253         cachep->colour_off = cache_line_size();
2254         /* Offset must be a multiple of the alignment. */
2255         if (cachep->colour_off < cachep->align)
2256                 cachep->colour_off = cachep->align;
2257         cachep->colour = left_over / cachep->colour_off;
2258         cachep->freelist_size = freelist_size;
2259         cachep->flags = flags;
2260         cachep->allocflags = __GFP_COMP;
2261         if (CONFIG_ZONE_DMA_FLAG && (flags & SLAB_CACHE_DMA))
2262                 cachep->allocflags |= GFP_DMA;
2263         cachep->size = size;
2264         cachep->reciprocal_buffer_size = reciprocal_value(size);
2265 
2266         if (flags & CFLGS_OFF_SLAB) {
2267                 cachep->freelist_cache = kmalloc_slab(freelist_size, 0u);
2268                 /*
2269                  * This is a possibility for one of the kmalloc_{dma,}_caches.
2270                  * But since we go off slab only for object size greater than
2271                  * PAGE_SIZE/8, and kmalloc_{dma,}_caches get created
2272                  * in ascending order,this should not happen at all.
2273                  * But leave a BUG_ON for some lucky dude.
2274                  */
2275                 BUG_ON(ZERO_OR_NULL_PTR(cachep->freelist_cache));
2276         }
2277 
2278         err = setup_cpu_cache(cachep, gfp);
2279         if (err) {
2280                 __kmem_cache_shutdown(cachep);
2281                 return err;
2282         }
2283 
2284         return 0;
2285 }
2286 
2287 #if DEBUG
2288 static void check_irq_off(void)
2289 {
2290         BUG_ON(!irqs_disabled());
2291 }
2292 
2293 static void check_irq_on(void)
2294 {
2295         BUG_ON(irqs_disabled());
2296 }
2297 
2298 static void check_spinlock_acquired(struct kmem_cache *cachep)
2299 {
2300 #ifdef CONFIG_SMP
2301         check_irq_off();
2302         assert_spin_locked(&get_node(cachep, numa_mem_id())->list_lock);
2303 #endif
2304 }
2305 
2306 static void check_spinlock_acquired_node(struct kmem_cache *cachep, int node)
2307 {
2308 #ifdef CONFIG_SMP
2309         check_irq_off();
2310         assert_spin_locked(&get_node(cachep, node)->list_lock);
2311 #endif
2312 }
2313 
2314 #else
2315 #define check_irq_off() do { } while(0)
2316 #define check_irq_on()  do { } while(0)
2317 #define check_spinlock_acquired(x) do { } while(0)
2318 #define check_spinlock_acquired_node(x, y) do { } while(0)
2319 #endif
2320 
2321 static void drain_array(struct kmem_cache *cachep, struct kmem_cache_node *n,
2322                         struct array_cache *ac,
2323                         int force, int node);
2324 
2325 static void do_drain(void *arg)
2326 {
2327         struct kmem_cache *cachep = arg;
2328         struct array_cache *ac;
2329         int node = numa_mem_id();
2330         struct kmem_cache_node *n;
2331         LIST_HEAD(list);
2332 
2333         check_irq_off();
2334         ac = cpu_cache_get(cachep);
2335         n = get_node(cachep, node);
2336         spin_lock(&n->list_lock);
2337         free_block(cachep, ac->entry, ac->avail, node, &list);
2338         spin_unlock(&n->list_lock);
2339         slabs_destroy(cachep, &list);
2340         ac->avail = 0;
2341 }
2342 
2343 static void drain_cpu_caches(struct kmem_cache *cachep)
2344 {
2345         struct kmem_cache_node *n;
2346         int node;
2347 
2348         on_each_cpu(do_drain, cachep, 1);
2349         check_irq_on();
2350         for_each_kmem_cache_node(cachep, node, n)
2351                 if (n->alien)
2352                         drain_alien_cache(cachep, n->alien);
2353 
2354         for_each_kmem_cache_node(cachep, node, n)
2355                 drain_array(cachep, n, n->shared, 1, node);
2356 }
2357 
2358 /*
2359  * Remove slabs from the list of free slabs.
2360  * Specify the number of slabs to drain in tofree.
2361  *
2362  * Returns the actual number of slabs released.
2363  */
2364 static int drain_freelist(struct kmem_cache *cache,
2365                         struct kmem_cache_node *n, int tofree)
2366 {
2367         struct list_head *p;
2368         int nr_freed;
2369         struct page *page;
2370 
2371         nr_freed = 0;
2372         while (nr_freed < tofree && !list_empty(&n->slabs_free)) {
2373 
2374                 spin_lock_irq(&n->list_lock);
2375                 p = n->slabs_free.prev;
2376                 if (p == &n->slabs_free) {
2377                         spin_unlock_irq(&n->list_lock);
2378                         goto out;
2379                 }
2380 
2381                 page = list_entry(p, struct page, lru);
2382 #if DEBUG
2383                 BUG_ON(page->active);
2384 #endif
2385                 list_del(&page->lru);
2386                 /*
2387                  * Safe to drop the lock. The slab is no longer linked
2388                  * to the cache.
2389                  */
2390                 n->free_objects -= cache->num;
2391                 spin_unlock_irq(&n->list_lock);
2392                 slab_destroy(cache, page);
2393                 nr_freed++;
2394         }
2395 out:
2396         return nr_freed;
2397 }
2398 
2399 int __kmem_cache_shrink(struct kmem_cache *cachep, bool deactivate)
2400 {
2401         int ret = 0;
2402         int node;
2403         struct kmem_cache_node *n;
2404 
2405         drain_cpu_caches(cachep);
2406 
2407         check_irq_on();
2408         for_each_kmem_cache_node(cachep, node, n) {
2409                 drain_freelist(cachep, n, slabs_tofree(cachep, n));
2410 
2411                 ret += !list_empty(&n->slabs_full) ||
2412                         !list_empty(&n->slabs_partial);
2413         }
2414         return (ret ? 1 : 0);
2415 }
2416 
2417 int __kmem_cache_shutdown(struct kmem_cache *cachep)
2418 {
2419         int i;
2420         struct kmem_cache_node *n;
2421         int rc = __kmem_cache_shrink(cachep, false);
2422 
2423         if (rc)
2424                 return rc;
2425 
2426         free_percpu(cachep->cpu_cache);
2427 
2428         /* NUMA: free the node structures */
2429         for_each_kmem_cache_node(cachep, i, n) {
2430                 kfree(n->shared);
2431                 free_alien_cache(n->alien);
2432                 kfree(n);
2433                 cachep->node[i] = NULL;
2434         }
2435         return 0;
2436 }
2437 
2438 /*
2439  * Get the memory for a slab management obj.
2440  *
2441  * For a slab cache when the slab descriptor is off-slab, the
2442  * slab descriptor can't come from the same cache which is being created,
2443  * Because if it is the case, that means we defer the creation of
2444  * the kmalloc_{dma,}_cache of size sizeof(slab descriptor) to this point.
2445  * And we eventually call down to __kmem_cache_create(), which
2446  * in turn looks up in the kmalloc_{dma,}_caches for the disired-size one.
2447  * This is a "chicken-and-egg" problem.
2448  *
2449  * So the off-slab slab descriptor shall come from the kmalloc_{dma,}_caches,
2450  * which are all initialized during kmem_cache_init().
2451  */
2452 static void *alloc_slabmgmt(struct kmem_cache *cachep,
2453                                    struct page *page, int colour_off,
2454                                    gfp_t local_flags, int nodeid)
2455 {
2456         void *freelist;
2457         void *addr = page_address(page);
2458 
2459         if (OFF_SLAB(cachep)) {
2460                 /* Slab management obj is off-slab. */
2461                 freelist = kmem_cache_alloc_node(cachep->freelist_cache,
2462                                               local_flags, nodeid);
2463                 if (!freelist)
2464                         return NULL;
2465         } else {
2466                 freelist = addr + colour_off;
2467                 colour_off += cachep->freelist_size;
2468         }
2469         page->active = 0;
2470         page->s_mem = addr + colour_off;
2471         return freelist;
2472 }
2473 
2474 static inline freelist_idx_t get_free_obj(struct page *page, unsigned int idx)
2475 {
2476         return ((freelist_idx_t *)page->freelist)[idx];
2477 }
2478 
2479 static inline void set_free_obj(struct page *page,
2480                                         unsigned int idx, freelist_idx_t val)
2481 {
2482         ((freelist_idx_t *)(page->freelist))[idx] = val;
2483 }
2484 
2485 static void cache_init_objs(struct kmem_cache *cachep,
2486                             struct page *page)
2487 {
2488         int i;
2489 
2490         for (i = 0; i < cachep->num; i++) {
2491                 void *objp = index_to_obj(cachep, page, i);
2492 #if DEBUG
2493                 /* need to poison the objs? */
2494                 if (cachep->flags & SLAB_POISON)
2495                         poison_obj(cachep, objp, POISON_FREE);
2496                 if (cachep->flags & SLAB_STORE_USER)
2497                         *dbg_userword(cachep, objp) = NULL;
2498 
2499                 if (cachep->flags & SLAB_RED_ZONE) {
2500                         *dbg_redzone1(cachep, objp) = RED_INACTIVE;
2501                         *dbg_redzone2(cachep, objp) = RED_INACTIVE;
2502                 }
2503                 /*
2504                  * Constructors are not allowed to allocate memory from the same
2505                  * cache which they are a constructor for.  Otherwise, deadlock.
2506                  * They must also be threaded.
2507                  */
2508                 if (cachep->ctor && !(cachep->flags & SLAB_POISON))
2509                         cachep->ctor(objp + obj_offset(cachep));
2510 
2511                 if (cachep->flags & SLAB_RED_ZONE) {
2512                         if (*dbg_redzone2(cachep, objp) != RED_INACTIVE)
2513                                 slab_error(cachep, "constructor overwrote the"
2514                                            " end of an object");
2515                         if (*dbg_redzone1(cachep, objp) != RED_INACTIVE)
2516                                 slab_error(cachep, "constructor overwrote the"
2517                                            " start of an object");
2518                 }
2519                 if ((cachep->size % PAGE_SIZE) == 0 &&
2520                             OFF_SLAB(cachep) && cachep->flags & SLAB_POISON)
2521                         kernel_map_pages(virt_to_page(objp),
2522                                          cachep->size / PAGE_SIZE, 0);
2523 #else
2524                 if (cachep->ctor)
2525                         cachep->ctor(objp);
2526 #endif
2527                 set_obj_status(page, i, OBJECT_FREE);
2528                 set_free_obj(page, i, i);
2529         }
2530 }
2531 
2532 static void kmem_flagcheck(struct kmem_cache *cachep, gfp_t flags)
2533 {
2534         if (CONFIG_ZONE_DMA_FLAG) {
2535                 if (flags & GFP_DMA)
2536                         BUG_ON(!(cachep->allocflags & GFP_DMA));
2537                 else
2538                         BUG_ON(cachep->allocflags & GFP_DMA);
2539         }
2540 }
2541 
2542 static void *slab_get_obj(struct kmem_cache *cachep, struct page *page,
2543                                 int nodeid)
2544 {
2545         void *objp;
2546 
2547         objp = index_to_obj(cachep, page, get_free_obj(page, page->active));
2548         page->active++;
2549 #if DEBUG
2550         WARN_ON(page_to_nid(virt_to_page(objp)) != nodeid);
2551 #endif
2552 
2553         return objp;
2554 }
2555 
2556 static void slab_put_obj(struct kmem_cache *cachep, struct page *page,
2557                                 void *objp, int nodeid)
2558 {
2559         unsigned int objnr = obj_to_index(cachep, page, objp);
2560 #if DEBUG
2561         unsigned int i;
2562 
2563         /* Verify that the slab belongs to the intended node */
2564         WARN_ON(page_to_nid(virt_to_page(objp)) != nodeid);
2565 
2566         /* Verify double free bug */
2567         for (i = page->active; i < cachep->num; i++) {
2568                 if (get_free_obj(page, i) == objnr) {
2569                         printk(KERN_ERR "slab: double free detected in cache "
2570                                         "'%s', objp %p\n", cachep->name, objp);
2571                         BUG();
2572                 }
2573         }
2574 #endif
2575         page->active--;
2576         set_free_obj(page, page->active, objnr);
2577 }
2578 
2579 /*
2580  * Map pages beginning at addr to the given cache and slab. This is required
2581  * for the slab allocator to be able to lookup the cache and slab of a
2582  * virtual address for kfree, ksize, and slab debugging.
2583  */
2584 static void slab_map_pages(struct kmem_cache *cache, struct page *page,
2585                            void *freelist)
2586 {
2587         page->slab_cache = cache;
2588         page->freelist = freelist;
2589 }
2590 
2591 /*
2592  * Grow (by 1) the number of slabs within a cache.  This is called by
2593  * kmem_cache_alloc() when there are no active objs left in a cache.
2594  */
2595 static int cache_grow(struct kmem_cache *cachep,
2596                 gfp_t flags, int nodeid, struct page *page)
2597 {
2598         void *freelist;
2599         size_t offset;
2600         gfp_t local_flags;
2601         struct kmem_cache_node *n;
2602 
2603         /*
2604          * Be lazy and only check for valid flags here,  keeping it out of the
2605          * critical path in kmem_cache_alloc().
2606          */
2607         if (unlikely(flags & GFP_SLAB_BUG_MASK)) {
2608                 pr_emerg("gfp: %u\n", flags & GFP_SLAB_BUG_MASK);
2609                 BUG();
2610         }
2611         local_flags = flags & (GFP_CONSTRAINT_MASK|GFP_RECLAIM_MASK);
2612 
2613         /* Take the node list lock to change the colour_next on this node */
2614         check_irq_off();
2615         n = get_node(cachep, nodeid);
2616         spin_lock(&n->list_lock);
2617 
2618         /* Get colour for the slab, and cal the next value. */
2619         offset = n->colour_next;
2620         n->colour_next++;
2621         if (n->colour_next >= cachep->colour)
2622                 n->colour_next = 0;
2623         spin_unlock(&n->list_lock);
2624 
2625         offset *= cachep->colour_off;
2626 
2627         if (local_flags & __GFP_WAIT)
2628                 local_irq_enable();
2629 
2630         /*
2631          * The test for missing atomic flag is performed here, rather than
2632          * the more obvious place, simply to reduce the critical path length
2633          * in kmem_cache_alloc(). If a caller is seriously mis-behaving they
2634          * will eventually be caught here (where it matters).
2635          */
2636         kmem_flagcheck(cachep, flags);
2637 
2638         /*
2639          * Get mem for the objs.  Attempt to allocate a physical page from
2640          * 'nodeid'.
2641          */
2642         if (!page)
2643                 page = kmem_getpages(cachep, local_flags, nodeid);
2644         if (!page)
2645                 goto failed;
2646 
2647         /* Get slab management. */
2648         freelist = alloc_slabmgmt(cachep, page, offset,
2649                         local_flags & ~GFP_CONSTRAINT_MASK, nodeid);
2650         if (!freelist)
2651                 goto opps1;
2652 
2653         slab_map_pages(cachep, page, freelist);
2654 
2655         cache_init_objs(cachep, page);
2656 
2657         if (local_flags & __GFP_WAIT)
2658                 local_irq_disable();
2659         check_irq_off();
2660         spin_lock(&n->list_lock);
2661 
2662         /* Make slab active. */
2663         list_add_tail(&page->lru, &(n->slabs_free));
2664         STATS_INC_GROWN(cachep);
2665         n->free_objects += cachep->num;
2666         spin_unlock(&n->list_lock);
2667         return 1;
2668 opps1:
2669         kmem_freepages(cachep, page);
2670 failed:
2671         if (local_flags & __GFP_WAIT)
2672                 local_irq_disable();
2673         return 0;
2674 }
2675 
2676 #if DEBUG
2677 
2678 /*
2679  * Perform extra freeing checks:
2680  * - detect bad pointers.
2681  * - POISON/RED_ZONE checking
2682  */
2683 static void kfree_debugcheck(const void *objp)
2684 {
2685         if (!virt_addr_valid(objp)) {
2686                 printk(KERN_ERR "kfree_debugcheck: out of range ptr %lxh.\n",
2687                        (unsigned long)objp);
2688                 BUG();
2689         }
2690 }
2691 
2692 static inline void verify_redzone_free(struct kmem_cache *cache, void *obj)
2693 {
2694         unsigned long long redzone1, redzone2;
2695 
2696         redzone1 = *dbg_redzone1(cache, obj);
2697         redzone2 = *dbg_redzone2(cache, obj);
2698 
2699         /*
2700          * Redzone is ok.
2701          */
2702         if (redzone1 == RED_ACTIVE && redzone2 == RED_ACTIVE)
2703                 return;
2704 
2705         if (redzone1 == RED_INACTIVE && redzone2 == RED_INACTIVE)
2706                 slab_error(cache, "double free detected");
2707         else
2708                 slab_error(cache, "memory outside object was overwritten");
2709 
2710         printk(KERN_ERR "%p: redzone 1:0x%llx, redzone 2:0x%llx.\n",
2711                         obj, redzone1, redzone2);
2712 }
2713 
2714 static void *cache_free_debugcheck(struct kmem_cache *cachep, void *objp,
2715                                    unsigned long caller)
2716 {
2717         unsigned int objnr;
2718         struct page *page;
2719 
2720         BUG_ON(virt_to_cache(objp) != cachep);
2721 
2722         objp -= obj_offset(cachep);
2723         kfree_debugcheck(objp);
2724         page = virt_to_head_page(objp);
2725 
2726         if (cachep->flags & SLAB_RED_ZONE) {
2727                 verify_redzone_free(cachep, objp);
2728                 *dbg_redzone1(cachep, objp) = RED_INACTIVE;
2729                 *dbg_redzone2(cachep, objp) = RED_INACTIVE;
2730         }
2731         if (cachep->flags & SLAB_STORE_USER)
2732                 *dbg_userword(cachep, objp) = (void *)caller;
2733 
2734         objnr = obj_to_index(cachep, page, objp);
2735 
2736         BUG_ON(objnr >= cachep->num);
2737         BUG_ON(objp != index_to_obj(cachep, page, objnr));
2738 
2739         set_obj_status(page, objnr, OBJECT_FREE);
2740         if (cachep->flags & SLAB_POISON) {
2741 #ifdef CONFIG_DEBUG_PAGEALLOC
2742                 if ((cachep->size % PAGE_SIZE)==0 && OFF_SLAB(cachep)) {
2743                         store_stackinfo(cachep, objp, caller);
2744                         kernel_map_pages(virt_to_page(objp),
2745                                          cachep->size / PAGE_SIZE, 0);
2746                 } else {
2747                         poison_obj(cachep, objp, POISON_FREE);
2748                 }
2749 #else
2750                 poison_obj(cachep, objp, POISON_FREE);
2751 #endif
2752         }
2753         return objp;
2754 }
2755 
2756 #else
2757 #define kfree_debugcheck(x) do { } while(0)
2758 #define cache_free_debugcheck(x,objp,z) (objp)
2759 #endif
2760 
2761 static void *cache_alloc_refill(struct kmem_cache *cachep, gfp_t flags,
2762                                                         bool force_refill)
2763 {
2764         int batchcount;
2765         struct kmem_cache_node *n;
2766         struct array_cache *ac;
2767         int node;
2768 
2769         check_irq_off();
2770         node = numa_mem_id();
2771         if (unlikely(force_refill))
2772                 goto force_grow;
2773 retry:
2774         ac = cpu_cache_get(cachep);
2775         batchcount = ac->batchcount;
2776         if (!ac->touched && batchcount > BATCHREFILL_LIMIT) {
2777                 /*
2778                  * If there was little recent activity on this cache, then
2779                  * perform only a partial refill.  Otherwise we could generate
2780                  * refill bouncing.
2781                  */
2782                 batchcount = BATCHREFILL_LIMIT;
2783         }
2784         n = get_node(cachep, node);
2785 
2786         BUG_ON(ac->avail > 0 || !n);
2787         spin_lock(&n->list_lock);
2788 
2789         /* See if we can refill from the shared array */
2790         if (n->shared && transfer_objects(ac, n->shared, batchcount)) {
2791                 n->shared->touched = 1;
2792                 goto alloc_done;
2793         }
2794 
2795         while (batchcount > 0) {
2796                 struct list_head *entry;
2797                 struct page *page;
2798                 /* Get slab alloc is to come from. */
2799                 entry = n->slabs_partial.next;
2800                 if (entry == &n->slabs_partial) {
2801                         n->free_touched = 1;
2802                         entry = n->slabs_free.next;
2803                         if (entry == &n->slabs_free)
2804                                 goto must_grow;
2805                 }
2806 
2807                 page = list_entry(entry, struct page, lru);
2808                 check_spinlock_acquired(cachep);
2809 
2810                 /*
2811                  * The slab was either on partial or free list so
2812                  * there must be at least one object available for
2813                  * allocation.
2814                  */
2815                 BUG_ON(page->active >= cachep->num);
2816 
2817                 while (page->active < cachep->num && batchcount--) {
2818                         STATS_INC_ALLOCED(cachep);
2819                         STATS_INC_ACTIVE(cachep);
2820                         STATS_SET_HIGH(cachep);
2821 
2822                         ac_put_obj(cachep, ac, slab_get_obj(cachep, page,
2823                                                                         node));
2824                 }
2825 
2826                 /* move slabp to correct slabp list: */
2827                 list_del(&page->lru);
2828                 if (page->active == cachep->num)
2829                         list_add(&page->lru, &n->slabs_full);
2830                 else
2831                         list_add(&page->lru, &n->slabs_partial);
2832         }
2833 
2834 must_grow:
2835         n->free_objects -= ac->avail;
2836 alloc_done:
2837         spin_unlock(&n->list_lock);
2838 
2839         if (unlikely(!ac->avail)) {
2840                 int x;
2841 force_grow:
2842                 x = cache_grow(cachep, gfp_exact_node(flags), node, NULL);
2843 
2844                 /* cache_grow can reenable interrupts, then ac could change. */
2845                 ac = cpu_cache_get(cachep);
2846                 node = numa_mem_id();
2847 
2848                 /* no objects in sight? abort */
2849                 if (!x && (ac->avail == 0 || force_refill))
2850                         return NULL;
2851 
2852                 if (!ac->avail)         /* objects refilled by interrupt? */
2853                         goto retry;
2854         }
2855         ac->touched = 1;
2856 
2857         return ac_get_obj(cachep, ac, flags, force_refill);
2858 }
2859 
2860 static inline void cache_alloc_debugcheck_before(struct kmem_cache *cachep,
2861                                                 gfp_t flags)
2862 {
2863         might_sleep_if(flags & __GFP_WAIT);
2864 #if DEBUG
2865         kmem_flagcheck(cachep, flags);
2866 #endif
2867 }
2868 
2869 #if DEBUG
2870 static void *cache_alloc_debugcheck_after(struct kmem_cache *cachep,
2871                                 gfp_t flags, void *objp, unsigned long caller)
2872 {
2873         struct page *page;
2874 
2875         if (!objp)
2876                 return objp;
2877         if (cachep->flags & SLAB_POISON) {
2878 #ifdef CONFIG_DEBUG_PAGEALLOC
2879                 if ((cachep->size % PAGE_SIZE) == 0 && OFF_SLAB(cachep))
2880                         kernel_map_pages(virt_to_page(objp),
2881                                          cachep->size / PAGE_SIZE, 1);
2882                 else
2883                         check_poison_obj(cachep, objp);
2884 #else
2885                 check_poison_obj(cachep, objp);
2886 #endif
2887                 poison_obj(cachep, objp, POISON_INUSE);
2888         }
2889         if (cachep->flags & SLAB_STORE_USER)
2890                 *dbg_userword(cachep, objp) = (void *)caller;
2891 
2892         if (cachep->flags & SLAB_RED_ZONE) {
2893                 if (*dbg_redzone1(cachep, objp) != RED_INACTIVE ||
2894                                 *dbg_redzone2(cachep, objp) != RED_INACTIVE) {
2895                         slab_error(cachep, "double free, or memory outside"
2896                                                 " object was overwritten");
2897                         printk(KERN_ERR
2898                                 "%p: redzone 1:0x%llx, redzone 2:0x%llx\n",
2899                                 objp, *dbg_redzone1(cachep, objp),
2900                                 *dbg_redzone2(cachep, objp));
2901                 }
2902                 *dbg_redzone1(cachep, objp) = RED_ACTIVE;
2903                 *dbg_redzone2(cachep, objp) = RED_ACTIVE;
2904         }
2905 
2906         page = virt_to_head_page(objp);
2907         set_obj_status(page, obj_to_index(cachep, page, objp), OBJECT_ACTIVE);
2908         objp += obj_offset(cachep);
2909         if (cachep->ctor && cachep->flags & SLAB_POISON)
2910                 cachep->ctor(objp);
2911         if (ARCH_SLAB_MINALIGN &&
2912             ((unsigned long)objp & (ARCH_SLAB_MINALIGN-1))) {
2913                 printk(KERN_ERR "0x%p: not aligned to ARCH_SLAB_MINALIGN=%d\n",
2914                        objp, (int)ARCH_SLAB_MINALIGN);
2915         }
2916         return objp;
2917 }
2918 #else
2919 #define cache_alloc_debugcheck_after(a,b,objp,d) (objp)
2920 #endif
2921 
2922 static bool slab_should_failslab(struct kmem_cache *cachep, gfp_t flags)
2923 {
2924         if (unlikely(cachep == kmem_cache))
2925                 return false;
2926 
2927         return should_failslab(cachep->object_size, flags, cachep->flags);
2928 }
2929 
2930 static inline void *____cache_alloc(struct kmem_cache *cachep, gfp_t flags)
2931 {
2932         void *objp;
2933         struct array_cache *ac;
2934         bool force_refill = false;
2935 
2936         check_irq_off();
2937 
2938         ac = cpu_cache_get(cachep);
2939         if (likely(ac->avail)) {
2940                 ac->touched = 1;
2941                 objp = ac_get_obj(cachep, ac, flags, false);
2942 
2943                 /*
2944                  * Allow for the possibility all avail objects are not allowed
2945                  * by the current flags
2946                  */
2947                 if (objp) {
2948                         STATS_INC_ALLOCHIT(cachep);
2949                         goto out;
2950                 }
2951                 force_refill = true;
2952         }
2953 
2954         STATS_INC_ALLOCMISS(cachep);
2955         objp = cache_alloc_refill(cachep, flags, force_refill);
2956         /*
2957          * the 'ac' may be updated by cache_alloc_refill(),
2958          * and kmemleak_erase() requires its correct value.
2959          */
2960         ac = cpu_cache_get(cachep);
2961 
2962 out:
2963         /*
2964          * To avoid a false negative, if an object that is in one of the
2965          * per-CPU caches is leaked, we need to make sure kmemleak doesn't
2966          * treat the array pointers as a reference to the object.
2967          */
2968         if (objp)
2969                 kmemleak_erase(&ac->entry[ac->avail]);
2970         return objp;
2971 }
2972 
2973 #ifdef CONFIG_NUMA
2974 /*
2975  * Try allocating on another node if PFA_SPREAD_SLAB is a mempolicy is set.
2976  *
2977  * If we are in_interrupt, then process context, including cpusets and
2978  * mempolicy, may not apply and should not be used for allocation policy.
2979  */
2980 static void *alternate_node_alloc(struct kmem_cache *cachep, gfp_t flags)
2981 {
2982         int nid_alloc, nid_here;
2983 
2984         if (in_interrupt() || (flags & __GFP_THISNODE))
2985                 return NULL;
2986         nid_alloc = nid_here = numa_mem_id();
2987         if (cpuset_do_slab_mem_spread() && (cachep->flags & SLAB_MEM_SPREAD))
2988                 nid_alloc = cpuset_slab_spread_node();
2989         else if (current->mempolicy)
2990                 nid_alloc = mempolicy_slab_node();
2991         if (nid_alloc != nid_here)
2992                 return ____cache_alloc_node(cachep, flags, nid_alloc);
2993         return NULL;
2994 }
2995 
2996 /*
2997  * Fallback function if there was no memory available and no objects on a
2998  * certain node and fall back is permitted. First we scan all the
2999  * available node for available objects. If that fails then we
3000  * perform an allocation without specifying a node. This allows the page
3001  * allocator to do its reclaim / fallback magic. We then insert the
3002  * slab into the proper nodelist and then allocate from it.
3003  */
3004 static void *fallback_alloc(struct kmem_cache *cache, gfp_t flags)
3005 {
3006         struct zonelist *zonelist;
3007         gfp_t local_flags;
3008         struct zoneref *z;
3009         struct zone *zone;
3010         enum zone_type high_zoneidx = gfp_zone(flags);
3011         void *obj = NULL;
3012         int nid;
3013         unsigned int cpuset_mems_cookie;
3014 
3015         if (flags & __GFP_THISNODE)
3016                 return NULL;
3017 
3018         local_flags = flags & (GFP_CONSTRAINT_MASK|GFP_RECLAIM_MASK);
3019 
3020 retry_cpuset:
3021         cpuset_mems_cookie = read_mems_allowed_begin();
3022         zonelist = node_zonelist(mempolicy_slab_node(), flags);
3023 
3024 retry:
3025         /*
3026          * Look through allowed nodes for objects available
3027          * from existing per node queues.
3028          */
3029         for_each_zone_zonelist(zone, z, zonelist, high_zoneidx) {
3030                 nid = zone_to_nid(zone);
3031 
3032                 if (cpuset_zone_allowed(zone, flags) &&
3033                         get_node(cache, nid) &&
3034                         get_node(cache, nid)->free_objects) {
3035                                 obj = ____cache_alloc_node(cache,
3036                                         gfp_exact_node(flags), nid);
3037                                 if (obj)
3038                                         break;
3039                 }
3040         }
3041 
3042         if (!obj) {
3043                 /*
3044                  * This allocation will be performed within the constraints
3045                  * of the current cpuset / memory policy requirements.
3046                  * We may trigger various forms of reclaim on the allowed
3047                  * set and go into memory reserves if necessary.
3048                  */
3049                 struct page *page;
3050 
3051                 if (local_flags & __GFP_WAIT)
3052                         local_irq_enable();
3053                 kmem_flagcheck(cache, flags);
3054                 page = kmem_getpages(cache, local_flags, numa_mem_id());
3055                 if (local_flags & __GFP_WAIT)
3056                         local_irq_disable();
3057                 if (page) {
3058                         /*
3059                          * Insert into the appropriate per node queues
3060                          */
3061                         nid = page_to_nid(page);
3062                         if (cache_grow(cache, flags, nid, page)) {
3063                                 obj = ____cache_alloc_node(cache,
3064                                         gfp_exact_node(flags), nid);
3065                                 if (!obj)
3066                                         /*
3067                                          * Another processor may allocate the
3068                                          * objects in the slab since we are
3069                                          * not holding any locks.
3070                                          */
3071                                         goto retry;
3072                         } else {
3073                                 /* cache_grow already freed obj */
3074                                 obj = NULL;
3075                         }
3076                 }
3077         }
3078 
3079         if (unlikely(!obj && read_mems_allowed_retry(cpuset_mems_cookie)))
3080                 goto retry_cpuset;
3081         return obj;
3082 }
3083 
3084 /*
3085  * A interface to enable slab creation on nodeid
3086  */
3087 static void *____cache_alloc_node(struct kmem_cache *cachep, gfp_t flags,
3088                                 int nodeid)
3089 {
3090         struct list_head *entry;
3091         struct page *page;
3092         struct kmem_cache_node *n;
3093         void *obj;
3094         int x;
3095 
3096         VM_BUG_ON(nodeid < 0 || nodeid >= MAX_NUMNODES);
3097         n = get_node(cachep, nodeid);
3098         BUG_ON(!n);
3099 
3100 retry:
3101         check_irq_off();
3102         spin_lock(&n->list_lock);
3103         entry = n->slabs_partial.next;
3104         if (entry == &n->slabs_partial) {
3105                 n->free_touched = 1;
3106                 entry = n->slabs_free.next;
3107                 if (entry == &n->slabs_free)
3108                         goto must_grow;
3109         }
3110 
3111         page = list_entry(entry, struct page, lru);
3112         check_spinlock_acquired_node(cachep, nodeid);
3113 
3114         STATS_INC_NODEALLOCS(cachep);
3115         STATS_INC_ACTIVE(cachep);
3116         STATS_SET_HIGH(cachep);
3117 
3118         BUG_ON(page->active == cachep->num);
3119 
3120         obj = slab_get_obj(cachep, page, nodeid);
3121         n->free_objects--;
3122         /* move slabp to correct slabp list: */
3123         list_del(&page->lru);
3124 
3125         if (page->active == cachep->num)
3126                 list_add(&page->lru, &n->slabs_full);
3127         else
3128                 list_add(&page->lru, &n->slabs_partial);
3129 
3130         spin_unlock(&n->list_lock);
3131         goto done;
3132 
3133 must_grow:
3134         spin_unlock(&n->list_lock);
3135         x = cache_grow(cachep, gfp_exact_node(flags), nodeid, NULL);
3136         if (x)
3137                 goto retry;
3138 
3139         return fallback_alloc(cachep, flags);
3140 
3141 done:
3142         return obj;
3143 }
3144 
3145 static __always_inline void *
3146 slab_alloc_node(struct kmem_cache *cachep, gfp_t flags, int nodeid,
3147                    unsigned long caller)
3148 {
3149         unsigned long save_flags;
3150         void *ptr;
3151         int slab_node = numa_mem_id();
3152 
3153         flags &= gfp_allowed_mask;
3154 
3155         lockdep_trace_alloc(flags);
3156 
3157         if (slab_should_failslab(cachep, flags))
3158                 return NULL;
3159 
3160         cachep = memcg_kmem_get_cache(cachep, flags);
3161 
3162         cache_alloc_debugcheck_before(cachep, flags);
3163         local_irq_save(save_flags);
3164 
3165         if (nodeid == NUMA_NO_NODE)
3166                 nodeid = slab_node;
3167 
3168         if (unlikely(!get_node(cachep, nodeid))) {
3169                 /* Node not bootstrapped yet */
3170                 ptr = fallback_alloc(cachep, flags);
3171                 goto out;
3172         }
3173 
3174         if (nodeid == slab_node) {
3175                 /*
3176                  * Use the locally cached objects if possible.
3177                  * However ____cache_alloc does not allow fallback
3178                  * to other nodes. It may fail while we still have
3179                  * objects on other nodes available.
3180                  */
3181                 ptr = ____cache_alloc(cachep, flags);
3182                 if (ptr)
3183                         goto out;
3184         }
3185         /* ___cache_alloc_node can fall back to other nodes */
3186         ptr = ____cache_alloc_node(cachep, flags, nodeid);
3187   out:
3188         local_irq_restore(save_flags);
3189         ptr = cache_alloc_debugcheck_after(cachep, flags, ptr, caller);
3190         kmemleak_alloc_recursive(ptr, cachep->object_size, 1, cachep->flags,
3191                                  flags);
3192 
3193         if (likely(ptr)) {
3194                 kmemcheck_slab_alloc(cachep, flags, ptr, cachep->object_size);
3195                 if (unlikely(flags & __GFP_ZERO))
3196                         memset(ptr, 0, cachep->object_size);
3197         }
3198 
3199         memcg_kmem_put_cache(cachep);
3200         return ptr;
3201 }
3202 
3203 static __always_inline void *
3204 __do_cache_alloc(struct kmem_cache *cache, gfp_t flags)
3205 {
3206         void *objp;
3207 
3208         if (current->mempolicy || cpuset_do_slab_mem_spread()) {
3209                 objp = alternate_node_alloc(cache, flags);
3210                 if (objp)
3211                         goto out;
3212         }
3213         objp = ____cache_alloc(cache, flags);
3214 
3215         /*
3216          * We may just have run out of memory on the local node.
3217          * ____cache_alloc_node() knows how to locate memory on other nodes
3218          */
3219         if (!objp)
3220                 objp = ____cache_alloc_node(cache, flags, numa_mem_id());
3221 
3222   out:
3223         return objp;
3224 }
3225 #else
3226 
3227 static __always_inline void *
3228 __do_cache_alloc(struct kmem_cache *cachep, gfp_t flags)
3229 {
3230         return ____cache_alloc(cachep, flags);
3231 }
3232 
3233 #endif /* CONFIG_NUMA */
3234 
3235 static __always_inline void *
3236 slab_alloc(struct kmem_cache *cachep, gfp_t flags, unsigned long caller)
3237 {
3238         unsigned long save_flags;
3239         void *objp;
3240 
3241         flags &= gfp_allowed_mask;
3242 
3243         lockdep_trace_alloc(flags);
3244 
3245         if (slab_should_failslab(cachep, flags))
3246                 return NULL;
3247 
3248         cachep = memcg_kmem_get_cache(cachep, flags);
3249 
3250         cache_alloc_debugcheck_before(cachep, flags);
3251         local_irq_save(save_flags);
3252         objp = __do_cache_alloc(cachep, flags);
3253         local_irq_restore(save_flags);
3254         objp = cache_alloc_debugcheck_after(cachep, flags, objp, caller);
3255         kmemleak_alloc_recursive(objp, cachep->object_size, 1, cachep->flags,
3256                                  flags);
3257         prefetchw(objp);
3258 
3259         if (likely(objp)) {
3260                 kmemcheck_slab_alloc(cachep, flags, objp, cachep->object_size);
3261                 if (unlikely(flags & __GFP_ZERO))
3262                         memset(objp, 0, cachep->object_size);
3263         }
3264 
3265         memcg_kmem_put_cache(cachep);
3266         return objp;
3267 }
3268 
3269 /*
3270  * Caller needs to acquire correct kmem_cache_node's list_lock
3271  * @list: List of detached free slabs should be freed by caller
3272  */
3273 static void free_block(struct kmem_cache *cachep, void **objpp,
3274                         int nr_objects, int node, struct list_head *list)
3275 {
3276         int i;
3277         struct kmem_cache_node *n = get_node(cachep, node);
3278 
3279         for (i = 0; i < nr_objects; i++) {
3280                 void *objp;
3281                 struct page *page;
3282 
3283                 clear_obj_pfmemalloc(&objpp[i]);
3284                 objp = objpp[i];
3285 
3286                 page = virt_to_head_page(objp);
3287                 list_del(&page->lru);
3288                 check_spinlock_acquired_node(cachep, node);
3289                 slab_put_obj(cachep, page, objp, node);
3290                 STATS_DEC_ACTIVE(cachep);
3291                 n->free_objects++;
3292 
3293                 /* fixup slab chains */
3294                 if (page->active == 0) {
3295                         if (n->free_objects > n->free_limit) {
3296                                 n->free_objects -= cachep->num;
3297                                 list_add_tail(&page->lru, list);
3298                         } else {
3299                                 list_add(&page->lru, &n->slabs_free);
3300                         }
3301                 } else {
3302                         /* Unconditionally move a slab to the end of the
3303                          * partial list on free - maximum time for the
3304                          * other objects to be freed, too.
3305                          */
3306                         list_add_tail(&page->lru, &n->slabs_partial);
3307                 }
3308         }
3309 }
3310 
3311 static void cache_flusharray(struct kmem_cache *cachep, struct array_cache *ac)
3312 {
3313         int batchcount;
3314         struct kmem_cache_node *n;
3315         int node = numa_mem_id();
3316         LIST_HEAD(list);
3317 
3318         batchcount = ac->batchcount;
3319 #if DEBUG
3320         BUG_ON(!batchcount || batchcount > ac->avail);
3321 #endif
3322         check_irq_off();
3323         n = get_node(cachep, node);
3324         spin_lock(&n->list_lock);
3325         if (n->shared) {
3326                 struct array_cache *shared_array = n->shared;
3327                 int max = shared_array->limit - shared_array->avail;
3328                 if (max) {
3329                         if (batchcount > max)
3330                                 batchcount = max;
3331                         memcpy(&(shared_array->entry[shared_array->avail]),
3332                                ac->entry, sizeof(void *) * batchcount);
3333                         shared_array->avail += batchcount;
3334                         goto free_done;
3335                 }
3336         }
3337 
3338         free_block(cachep, ac->entry, batchcount, node, &list);
3339 free_done:
3340 #if STATS
3341         {
3342                 int i = 0;
3343                 struct list_head *p;
3344 
3345                 p = n->slabs_free.next;
3346                 while (p != &(n->slabs_free)) {
3347                         struct page *page;
3348 
3349                         page = list_entry(p, struct page, lru);
3350                         BUG_ON(page->active);
3351 
3352                         i++;
3353                         p = p->next;
3354                 }
3355                 STATS_SET_FREEABLE(cachep, i);
3356         }
3357 #endif
3358         spin_unlock(&n->list_lock);
3359         slabs_destroy(cachep, &list);
3360         ac->avail -= batchcount;
3361         memmove(ac->entry, &(ac->entry[batchcount]), sizeof(void *)*ac->avail);
3362 }
3363 
3364 /*
3365  * Release an obj back to its cache. If the obj has a constructed state, it must
3366  * be in this state _before_ it is released.  Called with disabled ints.
3367  */
3368 static inline void __cache_free(struct kmem_cache *cachep, void *objp,
3369                                 unsigned long caller)
3370 {
3371         struct array_cache *ac = cpu_cache_get(cachep);
3372 
3373         check_irq_off();
3374         kmemleak_free_recursive(objp, cachep->flags);
3375         objp = cache_free_debugcheck(cachep, objp, caller);
3376 
3377         kmemcheck_slab_free(cachep, objp, cachep->object_size);
3378 
3379         /*
3380          * Skip calling cache_free_alien() when the platform is not numa.
3381          * This will avoid cache misses that happen while accessing slabp (which
3382          * is per page memory  reference) to get nodeid. Instead use a global
3383          * variable to skip the call, which is mostly likely to be present in
3384          * the cache.
3385          */
3386         if (nr_online_nodes > 1 && cache_free_alien(cachep, objp))
3387                 return;
3388 
3389         if (ac->avail < ac->limit) {
3390                 STATS_INC_FREEHIT(cachep);
3391         } else {
3392                 STATS_INC_FREEMISS(cachep);
3393                 cache_flusharray(cachep, ac);
3394         }
3395 
3396         ac_put_obj(cachep, ac, objp);
3397 }
3398 
3399 /**
3400  * kmem_cache_alloc - Allocate an object
3401  * @cachep: The cache to allocate from.
3402  * @flags: See kmalloc().
3403  *
3404  * Allocate an object from this cache.  The flags are only relevant
3405  * if the cache has no available objects.
3406  */
3407 void *kmem_cache_alloc(struct kmem_cache *cachep, gfp_t flags)
3408 {
3409         void *ret = slab_alloc(cachep, flags, _RET_IP_);
3410 
3411         trace_kmem_cache_alloc(_RET_IP_, ret,
3412                                cachep->object_size, cachep->size, flags);
3413 
3414         return ret;
3415 }
3416 EXPORT_SYMBOL(kmem_cache_alloc);
3417 
3418 #ifdef CONFIG_TRACING
3419 void *
3420 kmem_cache_alloc_trace(struct kmem_cache *cachep, gfp_t flags, size_t size)
3421 {
3422         void *ret;
3423 
3424         ret = slab_alloc(cachep, flags, _RET_IP_);
3425 
3426         trace_kmalloc(_RET_IP_, ret,
3427                       size, cachep->size, flags);
3428         return ret;
3429 }
3430 EXPORT_SYMBOL(kmem_cache_alloc_trace);
3431 #endif
3432 
3433 #ifdef CONFIG_NUMA
3434 /**
3435  * kmem_cache_alloc_node - Allocate an object on the specified node
3436  * @cachep: The cache to allocate from.
3437  * @flags: See kmalloc().
3438  * @nodeid: node number of the target node.
3439  *
3440  * Identical to kmem_cache_alloc but it will allocate memory on the given
3441  * node, which can improve the performance for cpu bound structures.
3442  *
3443  * Fallback to other node is possible if __GFP_THISNODE is not set.
3444  */
3445 void *kmem_cache_alloc_node(struct kmem_cache *cachep, gfp_t flags, int nodeid)
3446 {
3447         void *ret = slab_alloc_node(cachep, flags, nodeid, _RET_IP_);
3448 
3449         trace_kmem_cache_alloc_node(_RET_IP_, ret,
3450                                     cachep->object_size, cachep->size,
3451                                     flags, nodeid);
3452 
3453         return ret;
3454 }
3455 EXPORT_SYMBOL(kmem_cache_alloc_node);
3456 
3457 #ifdef CONFIG_TRACING
3458 void *kmem_cache_alloc_node_trace(struct kmem_cache *cachep,
3459                                   gfp_t flags,
3460                                   int nodeid,
3461                                   size_t size)
3462 {
3463         void *ret;
3464 
3465         ret = slab_alloc_node(cachep, flags, nodeid, _RET_IP_);
3466 
3467         trace_kmalloc_node(_RET_IP_, ret,
3468                            size, cachep->size,
3469                            flags, nodeid);
3470         return ret;
3471 }
3472 EXPORT_SYMBOL(kmem_cache_alloc_node_trace);
3473 #endif
3474 
3475 static __always_inline void *
3476 __do_kmalloc_node(size_t size, gfp_t flags, int node, unsigned long caller)
3477 {
3478         struct kmem_cache *cachep;
3479 
3480         cachep = kmalloc_slab(size, flags);
3481         if (unlikely(ZERO_OR_NULL_PTR(cachep)))
3482                 return cachep;
3483         return kmem_cache_alloc_node_trace(cachep, flags, node, size);
3484 }
3485 
3486 void *__kmalloc_node(size_t size, gfp_t flags, int node)
3487 {
3488         return __do_kmalloc_node(size, flags, node, _RET_IP_);
3489 }
3490 EXPORT_SYMBOL(__kmalloc_node);
3491 
3492 void *__kmalloc_node_track_caller(size_t size, gfp_t flags,
3493                 int node, unsigned long caller)
3494 {
3495         return __do_kmalloc_node(size, flags, node, caller);
3496 }
3497 EXPORT_SYMBOL(__kmalloc_node_track_caller);
3498 #endif /* CONFIG_NUMA */
3499 
3500 /**
3501  * __do_kmalloc - allocate memory
3502  * @size: how many bytes of memory are required.
3503  * @flags: the type of memory to allocate (see kmalloc).
3504  * @caller: function caller for debug tracking of the caller
3505  */
3506 static __always_inline void *__do_kmalloc(size_t size, gfp_t flags,
3507                                           unsigned long caller)
3508 {
3509         struct kmem_cache *cachep;
3510         void *ret;
3511 
3512         cachep = kmalloc_slab(size, flags);
3513         if (unlikely(ZERO_OR_NULL_PTR(cachep)))
3514                 return cachep;
3515         ret = slab_alloc(cachep, flags, caller);
3516 
3517         trace_kmalloc(caller, ret,
3518                       size, cachep->size, flags);
3519 
3520         return ret;
3521 }
3522 
3523 void *__kmalloc(size_t size, gfp_t flags)
3524 {
3525         return __do_kmalloc(size, flags, _RET_IP_);
3526 }
3527 EXPORT_SYMBOL(__kmalloc);
3528 
3529 void *__kmalloc_track_caller(size_t size, gfp_t flags, unsigned long caller)
3530 {
3531         return __do_kmalloc(size, flags, caller);
3532 }
3533 EXPORT_SYMBOL(__kmalloc_track_caller);
3534 
3535 /**
3536  * kmem_cache_free - Deallocate an object
3537  * @cachep: The cache the allocation was from.
3538  * @objp: The previously allocated object.
3539  *
3540  * Free an object which was previously allocated from this
3541  * cache.
3542  */
3543 void kmem_cache_free(struct kmem_cache *cachep, void *objp)
3544 {
3545         unsigned long flags;
3546         cachep = cache_from_obj(cachep, objp);
3547         if (!cachep)
3548                 return;
3549 
3550         local_irq_save(flags);
3551         debug_check_no_locks_freed(objp, cachep->object_size);
3552         if (!(cachep->flags & SLAB_DEBUG_OBJECTS))
3553                 debug_check_no_obj_freed(objp, cachep->object_size);
3554         __cache_free(cachep, objp, _RET_IP_);
3555         local_irq_restore(flags);
3556 
3557         trace_kmem_cache_free(_RET_IP_, objp);
3558 }
3559 EXPORT_SYMBOL(kmem_cache_free);
3560 
3561 /**
3562  * kfree - free previously allocated memory
3563  * @objp: pointer returned by kmalloc.
3564  *
3565  * If @objp is NULL, no operation is performed.
3566  *
3567  * Don't free memory not originally allocated by kmalloc()
3568  * or you will run into trouble.
3569  */
3570 void kfree(const void *objp)
3571 {
3572         struct kmem_cache *c;
3573         unsigned long flags;
3574 
3575         trace_kfree(_RET_IP_, objp);
3576 
3577         if (unlikely(ZERO_OR_NULL_PTR(objp)))
3578                 return;
3579         local_irq_save(flags);
3580         kfree_debugcheck(objp);
3581         c = virt_to_cache(objp);
3582         debug_check_no_locks_freed(objp, c->object_size);
3583 
3584         debug_check_no_obj_freed(objp, c->object_size);
3585         __cache_free(c, (void *)objp, _RET_IP_);
3586         local_irq_restore(flags);
3587 }
3588 EXPORT_SYMBOL(kfree);
3589 
3590 /*
3591  * This initializes kmem_cache_node or resizes various caches for all nodes.
3592  */
3593 static int alloc_kmem_cache_node(struct kmem_cache *cachep, gfp_t gfp)
3594 {
3595         int node;
3596         struct kmem_cache_node *n;
3597         struct array_cache *new_shared;
3598         struct alien_cache **new_alien = NULL;
3599 
3600         for_each_online_node(node) {
3601 
3602                 if (use_alien_caches) {
3603                         new_alien = alloc_alien_cache(node, cachep->limit, gfp);
3604                         if (!new_alien)
3605                                 goto fail;
3606                 }
3607 
3608                 new_shared = NULL;
3609                 if (cachep->shared) {
3610                         new_shared = alloc_arraycache(node,
3611                                 cachep->shared*cachep->batchcount,
3612                                         0xbaadf00d, gfp);
3613                         if (!new_shared) {
3614                                 free_alien_cache(new_alien);
3615                                 goto fail;
3616                         }
3617                 }
3618 
3619                 n = get_node(cachep, node);
3620                 if (n) {
3621                         struct array_cache *shared = n->shared;
3622                         LIST_HEAD(list);
3623 
3624                         spin_lock_irq(&n->list_lock);
3625 
3626                         if (shared)
3627                                 free_block(cachep, shared->entry,
3628                                                 shared->avail, node, &list);
3629 
3630                         n->shared = new_shared;
3631                         if (!n->alien) {
3632                                 n->alien = new_alien;
3633                                 new_alien = NULL;
3634                         }
3635                         n->free_limit = (1 + nr_cpus_node(node)) *
3636                                         cachep->batchcount + cachep->num;
3637                         spin_unlock_irq(&n->list_lock);
3638                         slabs_destroy(cachep, &list);
3639                         kfree(shared);
3640                         free_alien_cache(new_alien);
3641                         continue;
3642                 }
3643                 n = kmalloc_node(sizeof(struct kmem_cache_node), gfp, node);
3644                 if (!n) {
3645                         free_alien_cache(new_alien);
3646                         kfree(new_shared);
3647                         goto fail;
3648                 }
3649 
3650                 kmem_cache_node_init(n);
3651                 n->next_reap = jiffies + REAPTIMEOUT_NODE +
3652                                 ((unsigned long)cachep) % REAPTIMEOUT_NODE;
3653                 n->shared = new_shared;
3654                 n->alien = new_alien;
3655                 n->free_limit = (1 + nr_cpus_node(node)) *
3656                                         cachep->batchcount + cachep->num;
3657                 cachep->node[node] = n;
3658         }
3659         return 0;
3660 
3661 fail:
3662         if (!cachep->list.next) {
3663                 /* Cache is not active yet. Roll back what we did */
3664                 node--;
3665                 while (node >= 0) {
3666                         n = get_node(cachep, node);
3667                         if (n) {
3668                                 kfree(n->shared);
3669                                 free_alien_cache(n->alien);
3670                                 kfree(n);
3671                                 cachep->node[node] = NULL;
3672                         }
3673                         node--;
3674                 }
3675         }
3676         return -ENOMEM;
3677 }
3678 
3679 /* Always called with the slab_mutex held */
3680 static int __do_tune_cpucache(struct kmem_cache *cachep, int limit,
3681                                 int batchcount, int shared, gfp_t gfp)
3682 {
3683         struct array_cache __percpu *cpu_cache, *prev;
3684         int cpu;
3685 
3686         cpu_cache = alloc_kmem_cache_cpus(cachep, limit, batchcount);
3687         if (!cpu_cache)
3688                 return -ENOMEM;
3689 
3690         prev = cachep->cpu_cache;
3691         cachep->cpu_cache = cpu_cache;
3692         kick_all_cpus_sync();
3693 
3694         check_irq_on();
3695         cachep->batchcount = batchcount;
3696         cachep->limit = limit;
3697         cachep->shared = shared;
3698 
3699         if (!prev)
3700                 goto alloc_node;
3701 
3702         for_each_online_cpu(cpu) {
3703                 LIST_HEAD(list);
3704                 int node;
3705                 struct kmem_cache_node *n;
3706                 struct array_cache *ac = per_cpu_ptr(prev, cpu);
3707 
3708                 node = cpu_to_mem(cpu);
3709                 n = get_node(cachep, node);
3710                 spin_lock_irq(&n->list_lock);
3711                 free_block(cachep, ac->entry, ac->avail, node, &list);
3712                 spin_unlock_irq(&n->list_lock);
3713                 slabs_destroy(cachep, &list);
3714         }
3715         free_percpu(prev);
3716 
3717 alloc_node:
3718         return alloc_kmem_cache_node(cachep, gfp);
3719 }
3720 
3721 static int do_tune_cpucache(struct kmem_cache *cachep, int limit,
3722                                 int batchcount, int shared, gfp_t gfp)
3723 {
3724         int ret;
3725         struct kmem_cache *c;
3726 
3727         ret = __do_tune_cpucache(cachep, limit, batchcount, shared, gfp);
3728 
3729         if (slab_state < FULL)
3730                 return ret;
3731 
3732         if ((ret < 0) || !is_root_cache(cachep))
3733                 return ret;
3734 
3735         lockdep_assert_held(&slab_mutex);
3736         for_each_memcg_cache(c, cachep) {
3737                 /* return value determined by the root cache only */
3738                 __do_tune_cpucache(c, limit, batchcount, shared, gfp);
3739         }
3740 
3741         return ret;
3742 }
3743 
3744 /* Called with slab_mutex held always */
3745 static int enable_cpucache(struct kmem_cache *cachep, gfp_t gfp)
3746 {
3747         int err;
3748         int limit = 0;
3749         int shared = 0;
3750         int batchcount = 0;
3751 
3752         if (!is_root_cache(cachep)) {
3753                 struct kmem_cache *root = memcg_root_cache(cachep);
3754                 limit = root->limit;
3755                 shared = root->shared;
3756                 batchcount = root->batchcount;
3757         }
3758 
3759         if (limit && shared && batchcount)
3760                 goto skip_setup;
3761         /*
3762          * The head array serves three purposes:
3763          * - create a LIFO ordering, i.e. return objects that are cache-warm
3764          * - reduce the number of spinlock operations.
3765          * - reduce the number of linked list operations on the slab and
3766          *   bufctl chains: array operations are cheaper.
3767          * The numbers are guessed, we should auto-tune as described by
3768          * Bonwick.
3769          */
3770         if (cachep->size > 131072)
3771                 limit = 1;
3772         else if (cachep->size > PAGE_SIZE)
3773                 limit = 8;
3774         else if (cachep->size > 1024)
3775                 limit = 24;
3776         else if (cachep->size > 256)
3777                 limit = 54;
3778         else
3779                 limit = 120;
3780 
3781         /*
3782          * CPU bound tasks (e.g. network routing) can exhibit cpu bound
3783          * allocation behaviour: Most allocs on one cpu, most free operations
3784          * on another cpu. For these cases, an efficient object passing between
3785          * cpus is necessary. This is provided by a shared array. The array
3786          * replaces Bonwick's magazine layer.
3787          * On uniprocessor, it's functionally equivalent (but less efficient)
3788          * to a larger limit. Thus disabled by default.
3789          */
3790         shared = 0;
3791         if (cachep->size <= PAGE_SIZE && num_possible_cpus() > 1)
3792                 shared = 8;
3793 
3794 #if DEBUG
3795         /*
3796          * With debugging enabled, large batchcount lead to excessively long
3797          * periods with disabled local interrupts. Limit the batchcount
3798          */
3799         if (limit > 32)
3800                 limit = 32;
3801 #endif
3802         batchcount = (limit + 1) / 2;
3803 skip_setup:
3804         err = do_tune_cpucache(cachep, limit, batchcount, shared, gfp);
3805         if (err)
3806                 printk(KERN_ERR "enable_cpucache failed for %s, error %d.\n",
3807                        cachep->name, -err);
3808         return err;
3809 }
3810 
3811 /*
3812  * Drain an array if it contains any elements taking the node lock only if
3813  * necessary. Note that the node listlock also protects the array_cache
3814  * if drain_array() is used on the shared array.
3815  */
3816 static void drain_array(struct kmem_cache *cachep, struct kmem_cache_node *n,
3817                          struct array_cache *ac, int force, int node)
3818 {
3819         LIST_HEAD(list);
3820         int tofree;
3821 
3822         if (!ac || !ac->avail)
3823                 return;
3824         if (ac->touched && !force) {
3825                 ac->touched = 0;
3826         } else {
3827                 spin_lock_irq(&n->list_lock);
3828                 if (ac->avail) {
3829                         tofree = force ? ac->avail : (ac->limit + 4) / 5;
3830                         if (tofree > ac->avail)
3831                                 tofree = (ac->avail + 1) / 2;
3832                         free_block(cachep, ac->entry, tofree, node, &list);
3833                         ac->avail -= tofree;
3834                         memmove(ac->entry, &(ac->entry[tofree]),
3835                                 sizeof(void *) * ac->avail);
3836                 }
3837                 spin_unlock_irq(&n->list_lock);
3838                 slabs_destroy(cachep, &list);
3839         }
3840 }
3841 
3842 /**
3843  * cache_reap - Reclaim memory from caches.
3844  * @w: work descriptor
3845  *
3846  * Called from workqueue/eventd every few seconds.
3847  * Purpose:
3848  * - clear the per-cpu caches for this CPU.
3849  * - return freeable pages to the main free memory pool.
3850  *
3851  * If we cannot acquire the cache chain mutex then just give up - we'll try
3852  * again on the next iteration.
3853  */
3854 static void cache_reap(struct work_struct *w)
3855 {
3856         struct kmem_cache *searchp;
3857         struct kmem_cache_node *n;
3858         int node = numa_mem_id();
3859         struct delayed_work *work = to_delayed_work(w);
3860 
3861         if (!mutex_trylock(&slab_mutex))
3862                 /* Give up. Setup the next iteration. */
3863                 goto out;
3864 
3865         list_for_each_entry(searchp, &slab_caches, list) {
3866                 check_irq_on();
3867 
3868                 /*
3869                  * We only take the node lock if absolutely necessary and we
3870                  * have established with reasonable certainty that
3871                  * we can do some work if the lock was obtained.
3872                  */
3873                 n = get_node(searchp, node);
3874 
3875                 reap_alien(searchp, n);
3876 
3877                 drain_array(searchp, n, cpu_cache_get(searchp), 0, node);
3878 
3879                 /*
3880                  * These are racy checks but it does not matter
3881                  * if we skip one check or scan twice.
3882                  */
3883                 if (time_after(n->next_reap, jiffies))
3884                         goto next;
3885 
3886                 n->next_reap = jiffies + REAPTIMEOUT_NODE;
3887 
3888                 drain_array(searchp, n, n->shared, 0, node);
3889 
3890                 if (n->free_touched)
3891                         n->free_touched = 0;
3892                 else {
3893                         int freed;
3894 
3895                         freed = drain_freelist(searchp, n, (n->free_limit +
3896                                 5 * searchp->num - 1) / (5 * searchp->num));
3897                         STATS_ADD_REAPED(searchp, freed);
3898                 }
3899 next:
3900                 cond_resched();
3901         }
3902         check_irq_on();
3903         mutex_unlock(&slab_mutex);
3904         next_reap_node();
3905 out:
3906         /* Set up the next iteration */
3907         schedule_delayed_work(work, round_jiffies_relative(REAPTIMEOUT_AC));
3908 }
3909 
3910 #ifdef CONFIG_SLABINFO
3911 void get_slabinfo(struct kmem_cache *cachep, struct slabinfo *sinfo)
3912 {
3913         struct page *page;
3914         unsigned long active_objs;
3915         unsigned long num_objs;
3916         unsigned long active_slabs = 0;
3917         unsigned long num_slabs, free_objects = 0, shared_avail = 0;
3918         const char *name;
3919         char *error = NULL;
3920         int node;
3921         struct kmem_cache_node *n;
3922 
3923         active_objs = 0;
3924         num_slabs = 0;
3925         for_each_kmem_cache_node(cachep, node, n) {
3926 
3927                 check_irq_on();
3928                 spin_lock_irq(&n->list_lock);
3929 
3930                 list_for_each_entry(page, &n->slabs_full, lru) {
3931                         if (page->active != cachep->num && !error)
3932                                 error = "slabs_full accounting error";
3933                         active_objs += cachep->num;
3934                         active_slabs++;
3935                 }
3936                 list_for_each_entry(page, &n->slabs_partial, lru) {
3937                         if (page->active == cachep->num && !error)
3938                                 error = "slabs_partial accounting error";
3939                         if (!page->active && !error)
3940                                 error = "slabs_partial accounting error";
3941                         active_objs += page->active;
3942                         active_slabs++;
3943                 }
3944                 list_for_each_entry(page, &n->slabs_free, lru) {
3945                         if (page->active && !error)
3946                                 error = "slabs_free accounting error";
3947                         num_slabs++;
3948                 }
3949                 free_objects += n->free_objects;
3950                 if (n->shared)
3951                         shared_avail += n->shared->avail;
3952 
3953                 spin_unlock_irq(&n->list_lock);
3954         }
3955         num_slabs += active_slabs;
3956         num_objs = num_slabs * cachep->num;
3957         if (num_objs - active_objs != free_objects && !error)
3958                 error = "free_objects accounting error";
3959 
3960         name = cachep->name;
3961         if (error)
3962                 printk(KERN_ERR "slab: cache %s error: %s\n", name, error);
3963 
3964         sinfo->active_objs = active_objs;
3965         sinfo->num_objs = num_objs;
3966         sinfo->active_slabs = active_slabs;
3967         sinfo->num_slabs = num_slabs;
3968         sinfo->shared_avail = shared_avail;
3969         sinfo->limit = cachep->limit;
3970         sinfo->batchcount = cachep->batchcount;
3971         sinfo->shared = cachep->shared;
3972         sinfo->objects_per_slab = cachep->num;
3973         sinfo->cache_order = cachep->gfporder;
3974 }
3975 
3976 void slabinfo_show_stats(struct seq_file *m, struct kmem_cache *cachep)
3977 {
3978 #if STATS
3979         {                       /* node stats */
3980                 unsigned long high = cachep->high_mark;
3981                 unsigned long allocs = cachep->num_allocations;
3982                 unsigned long grown = cachep->grown;
3983                 unsigned long reaped = cachep->reaped;
3984                 unsigned long errors = cachep->errors;
3985                 unsigned long max_freeable = cachep->max_freeable;
3986                 unsigned long node_allocs = cachep->node_allocs;
3987                 unsigned long node_frees = cachep->node_frees;
3988                 unsigned long overflows = cachep->node_overflow;
3989 
3990                 seq_printf(m, " : globalstat %7lu %6lu %5lu %4lu "
3991                            "%4lu %4lu %4lu %4lu %4lu",
3992                            allocs, high, grown,
3993                            reaped, errors, max_freeable, node_allocs,
3994                            node_frees, overflows);
3995         }
3996         /* cpu stats */
3997         {
3998                 unsigned long allochit = atomic_read(&cachep->allochit);
3999                 unsigned long allocmiss = atomic_read(&cachep->allocmiss);
4000                 unsigned long freehit = atomic_read(&cachep->freehit);
4001                 unsigned long freemiss = atomic_read(&cachep->freemiss);
4002 
4003                 seq_printf(m, " : cpustat %6lu %6lu %6lu %6lu",
4004                            allochit, allocmiss, freehit, freemiss);
4005         }
4006 #endif
4007 }
4008 
4009 #define MAX_SLABINFO_WRITE 128
4010 /**
4011  * slabinfo_write - Tuning for the slab allocator
4012  * @file: unused
4013  * @buffer: user buffer
4014  * @count: data length
4015  * @ppos: unused
4016  */
4017 ssize_t slabinfo_write(struct file *file, const char __user *buffer,
4018                        size_t count, loff_t *ppos)
4019 {
4020         char kbuf[MAX_SLABINFO_WRITE + 1], *tmp;
4021         int limit, batchcount, shared, res;
4022         struct kmem_cache *cachep;
4023 
4024         if (count > MAX_SLABINFO_WRITE)
4025                 return -EINVAL;
4026         if (copy_from_user(&kbuf, buffer, count))
4027                 return -EFAULT;
4028         kbuf[MAX_SLABINFO_WRITE] = '\0';
4029 
4030         tmp = strchr(kbuf, ' ');
4031         if (!tmp)
4032                 return -EINVAL;
4033         *tmp = '\0';
4034         tmp++;
4035         if (sscanf(tmp, " %d %d %d", &limit, &batchcount, &shared) != 3)
4036                 return -EINVAL;
4037 
4038         /* Find the cache in the chain of caches. */
4039         mutex_lock(&slab_mutex);
4040         res = -EINVAL;
4041         list_for_each_entry(cachep, &slab_caches, list) {
4042                 if (!strcmp(cachep->name, kbuf)) {
4043                         if (limit < 1 || batchcount < 1 ||
4044                                         batchcount > limit || shared < 0) {
4045                                 res = 0;
4046                         } else {
4047                                 res = do_tune_cpucache(cachep, limit,
4048                                                        batchcount, shared,
4049                                                        GFP_KERNEL);
4050                         }
4051                         break;
4052                 }
4053         }
4054         mutex_unlock(&slab_mutex);
4055         if (res >= 0)
4056                 res = count;
4057         return res;
4058 }
4059 
4060 #ifdef CONFIG_DEBUG_SLAB_LEAK
4061 
4062 static inline int add_caller(unsigned long *n, unsigned long v)
4063 {
4064         unsigned long *p;
4065         int l;
4066         if (!v)
4067                 return 1;
4068         l = n[1];
4069         p = n + 2;
4070         while (l) {
4071                 int i = l/2;
4072                 unsigned long *q = p + 2 * i;
4073                 if (*q == v) {
4074                         q[1]++;
4075                         return 1;
4076                 }
4077                 if (*q > v) {
4078                         l = i;
4079                 } else {
4080                         p = q + 2;
4081                         l -= i + 1;
4082                 }
4083         }
4084         if (++n[1] == n[0])
4085                 return 0;
4086         memmove(p + 2, p, n[1] * 2 * sizeof(unsigned long) - ((void *)p - (void *)n));
4087         p[0] = v;
4088         p[1] = 1;
4089         return 1;
4090 }
4091 
4092 static void handle_slab(unsigned long *n, struct kmem_cache *c,
4093                                                 struct page *page)
4094 {
4095         void *p;
4096         int i;
4097 
4098         if (n[0] == n[1])
4099                 return;
4100         for (i = 0, p = page->s_mem; i < c->num; i++, p += c->size) {
4101                 if (get_obj_status(page, i) != OBJECT_ACTIVE)
4102                         continue;
4103 
4104                 if (!add_caller(n, (unsigned long)*dbg_userword(c, p)))
4105                         return;
4106         }
4107 }
4108 
4109 static void show_symbol(struct seq_file *m, unsigned long address)
4110 {
4111 #ifdef CONFIG_KALLSYMS
4112         unsigned long offset, size;
4113         char modname[MODULE_NAME_LEN], name[KSYM_NAME_LEN];
4114 
4115         if (lookup_symbol_attrs(address, &size, &offset, modname, name) == 0) {
4116                 seq_printf(m, "%s+%#lx/%#lx", name, offset, size);
4117                 if (modname[0])
4118                         seq_printf(m, " [%s]", modname);
4119                 return;
4120         }
4121 #endif
4122         seq_printf(m, "%p", (void *)address);
4123 }
4124 
4125 static int leaks_show(struct seq_file *m, void *p)
4126 {
4127         struct kmem_cache *cachep = list_entry(p, struct kmem_cache, list);
4128         struct page *page;
4129         struct kmem_cache_node *n;
4130         const char *name;
4131         unsigned long *x = m->private;
4132         int node;
4133         int i;
4134 
4135         if (!(cachep->flags & SLAB_STORE_USER))
4136                 return 0;
4137         if (!(cachep->flags & SLAB_RED_ZONE))
4138                 return 0;
4139 
4140         /* OK, we can do it */
4141 
4142         x[1] = 0;
4143 
4144         for_each_kmem_cache_node(cachep, node, n) {
4145 
4146                 check_irq_on();
4147                 spin_lock_irq(&n->list_lock);
4148 
4149                 list_for_each_entry(page, &n->slabs_full, lru)
4150                         handle_slab(x, cachep, page);
4151                 list_for_each_entry(page, &n->slabs_partial, lru)
4152                         handle_slab(x, cachep, page);
4153                 spin_unlock_irq(&n->list_lock);
4154         }
4155         name = cachep->name;
4156         if (x[0] == x[1]) {
4157                 /* Increase the buffer size */
4158                 mutex_unlock(&slab_mutex);
4159                 m->private = kzalloc(x[0] * 4 * sizeof(unsigned long), GFP_KERNEL);
4160                 if (!m->private) {
4161                         /* Too bad, we are really out */
4162                         m->private = x;
4163                         mutex_lock(&slab_mutex);
4164                         return -ENOMEM;
4165                 }
4166                 *(unsigned long *)m->private = x[0] * 2;
4167                 kfree(x);
4168                 mutex_lock(&slab_mutex);
4169                 /* Now make sure this entry will be retried */
4170                 m->count = m->size;
4171                 return 0;
4172         }
4173         for (i = 0; i < x[1]; i++) {
4174                 seq_printf(m, "%s: %lu ", name, x[2*i+3]);
4175                 show_symbol(m, x[2*i+2]);
4176                 seq_putc(m, '\n');
4177         }
4178 
4179         return 0;
4180 }
4181 
4182 static const struct seq_operations slabstats_op = {
4183         .start = slab_start,
4184         .next = slab_next,
4185         .stop = slab_stop,
4186         .show = leaks_show,
4187 };
4188 
4189 static int slabstats_open(struct inode *inode, struct file *file)
4190 {
4191         unsigned long *n;
4192 
4193         n = __seq_open_private(file, &slabstats_op, PAGE_SIZE);
4194         if (!n)
4195                 return -ENOMEM;
4196 
4197         *n = PAGE_SIZE / (2 * sizeof(unsigned long));
4198 
4199         return 0;
4200 }
4201 
4202 static const struct file_operations proc_slabstats_operations = {
4203         .open           = slabstats_open,
4204         .read           = seq_read,
4205         .llseek         = seq_lseek,
4206         .release        = seq_release_private,
4207 };
4208 #endif
4209 
4210 static int __init slab_proc_init(void)
4211 {
4212 #ifdef CONFIG_DEBUG_SLAB_LEAK
4213         proc_create("slab_allocators", 0, NULL, &proc_slabstats_operations);
4214 #endif
4215         return 0;
4216 }
4217 module_init(slab_proc_init);
4218 #endif
4219 
4220 /**
4221  * ksize - get the actual amount of memory allocated for a given object
4222  * @objp: Pointer to the object
4223  *
4224  * kmalloc may internally round up allocations and return more memory
4225  * than requested. ksize() can be used to determine the actual amount of
4226  * memory allocated. The caller may use this additional memory, even though
4227  * a smaller amount of memory was initially specified with the kmalloc call.
4228  * The caller must guarantee that objp points to a valid object previously
4229  * allocated with either kmalloc() or kmem_cache_alloc(). The object
4230  * must not be freed during the duration of the call.
4231  */
4232 size_t ksize(const void *objp)
4233 {
4234         BUG_ON(!objp);
4235         if (unlikely(objp == ZERO_SIZE_PTR))
4236                 return 0;
4237 
4238         return virt_to_cache(objp)->object_size;
4239 }
4240 EXPORT_SYMBOL(ksize);
4241 
