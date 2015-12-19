
```
  1 #ifndef _FLEX_ARRAY_H
  2 #define _FLEX_ARRAY_H
  3 
  4 #include <linux/types.h>
  5 #include <linux/reciprocal_div.h>
  6 #include <asm/page.h>
  7 
  8 #define FLEX_ARRAY_PART_SIZE PAGE_SIZE
  9 #define FLEX_ARRAY_BASE_SIZE PAGE_SIZE
 10 
 11 struct flex_array_part;
 12 
 13 /*
 14  * This is meant to replace cases where an array-like
 15  * structure has gotten too big to fit into kmalloc()
 16  * and the developer is getting tempted to use
 17  * vmalloc().
 18  */
 19 
 20 struct flex_array {
 21         union {
 22                 struct {
 23                         int element_size;
 24                         int total_nr_elements;
 25                         int elems_per_part;
 26                         struct reciprocal_value reciprocal_elems;
 27                         struct flex_array_part *parts[];
 28                 };
 29                 /*
 30                  * This little trick makes sure that
 31                  * sizeof(flex_array) == PAGE_SIZE
 32                  */
 33                 char padding[FLEX_ARRAY_BASE_SIZE];
 34         };
 35 };
 36 
 37 /* Number of bytes left in base struct flex_array, excluding metadata */
 38 #define FLEX_ARRAY_BASE_BYTES_LEFT                                      \
 39         (FLEX_ARRAY_BASE_SIZE - offsetof(struct flex_array, parts))
 40 
 41 /* Number of pointers in base to struct flex_array_part pages */
 42 #define FLEX_ARRAY_NR_BASE_PTRS                                         \
 43         (FLEX_ARRAY_BASE_BYTES_LEFT / sizeof(struct flex_array_part *))
 44 
 45 /* Number of elements of size that fit in struct flex_array_part */
 46 #define FLEX_ARRAY_ELEMENTS_PER_PART(size)                              \
 47         (FLEX_ARRAY_PART_SIZE / size)
 48 
 49 /*
 50  * Defines a statically allocated flex array and ensures its parameters are
 51  * valid.
 52  */
 53 #define DEFINE_FLEX_ARRAY(__arrayname, __element_size, __total)         \
 54         struct flex_array __arrayname = { { {                           \
 55                 .element_size = (__element_size),                       \
 56                 .total_nr_elements = (__total),                         \
 57         } } };                                                          \
 58         static inline void __arrayname##_invalid_parameter(void)        \
 59         {                                                               \
 60                 BUILD_BUG_ON((__total) > FLEX_ARRAY_NR_BASE_PTRS *      \
 61                         FLEX_ARRAY_ELEMENTS_PER_PART(__element_size));  \
 62         }
 63 
 64 struct flex_array *flex_array_alloc(int element_size, unsigned int total,
 65                 gfp_t flags);
 66 int flex_array_prealloc(struct flex_array *fa, unsigned int start,
 67                 unsigned int nr_elements, gfp_t flags);
 68 void flex_array_free(struct flex_array *fa);
 69 void flex_array_free_parts(struct flex_array *fa);
 70 int flex_array_put(struct flex_array *fa, unsigned int element_nr, void *src,
 71                 gfp_t flags);
 72 int flex_array_clear(struct flex_array *fa, unsigned int element_nr);
 73 void *flex_array_get(struct flex_array *fa, unsigned int element_nr);
 74 int flex_array_shrink(struct flex_array *fa);
 75 
 76 #define flex_array_put_ptr(fa, nr, src, gfp) \
 77         flex_array_put(fa, nr, (void *)&(src), gfp)
 78 
 79 void *flex_array_get_ptr(struct flex_array *fa, unsigned int element_nr);
 80 
 81 #endif /* _FLEX_ARRAY_H */
 82 
```

```
  1 /*
  2  * Flexible array managed in PAGE_SIZE parts
  3  *
  4  * This program is free software; you can redistribute it and/or modify
  5  * it under the terms of the GNU General Public License as published by
  6  * the Free Software Foundation; either version 2 of the License, or
  7  * (at your option) any later version.
  8  *
  9  * This program is distributed in the hope that it will be useful,
 10  * but WITHOUT ANY WARRANTY; without even the implied warranty of
 11  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 12  * GNU General Public License for more details.
 13  *
 14  * You should have received a copy of the GNU General Public License
 15  * along with this program; if not, write to the Free Software
 16  * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 17  *
 18  * Copyright IBM Corporation, 2009
 19  *
 20  * Author: Dave Hansen <dave@linux.vnet.ibm.com>
 21  */
 22 
 23 #include <linux/flex_array.h>
 24 #include <linux/slab.h>
 25 #include <linux/stddef.h>
 26 #include <linux/export.h>
 27 #include <linux/reciprocal_div.h>
 28 
 29 struct flex_array_part {
 30         char elements[FLEX_ARRAY_PART_SIZE];
 31 };
 32 
 33 /*
 34  * If a user requests an allocation which is small
 35  * enough, we may simply use the space in the
 36  * flex_array->parts[] array to store the user
 37  * data.
 38  */
 39 static inline int elements_fit_in_base(struct flex_array *fa)
 40 {
 41         int data_size = fa->element_size * fa->total_nr_elements;
 42         if (data_size <= FLEX_ARRAY_BASE_BYTES_LEFT)
 43                 return 1;
 44         return 0;
 45 }
 46 
 47 /**
 48  * flex_array_alloc - allocate a new flexible array
 49  * @element_size:       the size of individual elements in the array
 50  * @total:              total number of elements that this should hold
 51  * @flags:              page allocation flags to use for base array
 52  *
 53  * Note: all locking must be provided by the caller.
 54  *
 55  * @total is used to size internal structures.  If the user ever
 56  * accesses any array indexes >=@total, it will produce errors.
 57  *
 58  * The maximum number of elements is defined as: the number of
 59  * elements that can be stored in a page times the number of
 60  * page pointers that we can fit in the base structure or (using
 61  * integer math):
 62  *
 63  *      (PAGE_SIZE/element_size) * (PAGE_SIZE-8)/sizeof(void *)
 64  *
 65  * Here's a table showing example capacities.  Note that the maximum
 66  * index that the get/put() functions is just nr_objects-1.   This
 67  * basically means that you get 4MB of storage on 32-bit and 2MB on
 68  * 64-bit.
 69  *
 70  *
 71  * Element size | Objects | Objects |
 72  * PAGE_SIZE=4k |  32-bit |  64-bit |
 73  * ---------------------------------|
 74  *      1 bytes | 4177920 | 2088960 |
 75  *      2 bytes | 2088960 | 1044480 |
 76  *      3 bytes | 1392300 |  696150 |
 77  *      4 bytes | 1044480 |  522240 |
 78  *     32 bytes |  130560 |   65408 |
 79  *     33 bytes |  126480 |   63240 |
 80  *   2048 bytes |    2040 |    1020 |
 81  *   2049 bytes |    1020 |     510 |
 82  *       void * | 1044480 |  261120 |
 83  *
 84  * Since 64-bit pointers are twice the size, we lose half the
 85  * capacity in the base structure.  Also note that no effort is made
 86  * to efficiently pack objects across page boundaries.
 87  */
 88 struct flex_array *flex_array_alloc(int element_size, unsigned int total,
 89                                         gfp_t flags)
 90 {
 91         struct flex_array *ret;
 92         int elems_per_part = 0;
 93         int max_size = 0;
 94         struct reciprocal_value reciprocal_elems = { 0 };
 95 
 96         if (element_size) {
 97                 elems_per_part = FLEX_ARRAY_ELEMENTS_PER_PART(element_size);
 98                 reciprocal_elems = reciprocal_value(elems_per_part);
 99                 max_size = FLEX_ARRAY_NR_BASE_PTRS * elems_per_part;
100         }
101 
102         /* max_size will end up 0 if element_size > PAGE_SIZE */
103         if (total > max_size)
104                 return NULL;
105         ret = kzalloc(sizeof(struct flex_array), flags);
106         if (!ret)
107                 return NULL;
108         ret->element_size = element_size;
109         ret->total_nr_elements = total;
110         ret->elems_per_part = elems_per_part;
111         ret->reciprocal_elems = reciprocal_elems;
112         if (elements_fit_in_base(ret) && !(flags & __GFP_ZERO))
113                 memset(&ret->parts[0], FLEX_ARRAY_FREE,
114                                                 FLEX_ARRAY_BASE_BYTES_LEFT);
115         return ret;
116 }
117 EXPORT_SYMBOL(flex_array_alloc);
118 
119 static int fa_element_to_part_nr(struct flex_array *fa,
120                                         unsigned int element_nr)
121 {
122         /*
123          * if element_size == 0 we don't get here, so we never touch
124          * the zeroed fa->reciprocal_elems, which would yield invalid
125          * results
126          */
127         return reciprocal_divide(element_nr, fa->reciprocal_elems);
128 }
129 
130 /**
131  * flex_array_free_parts - just free the second-level pages
132  * @fa:         the flex array from which to free parts
133  *
134  * This is to be used in cases where the base 'struct flex_array'
135  * has been statically allocated and should not be free.
136  */
137 void flex_array_free_parts(struct flex_array *fa)
138 {
139         int part_nr;
140 
141         if (elements_fit_in_base(fa))
142                 return;
143         for (part_nr = 0; part_nr < FLEX_ARRAY_NR_BASE_PTRS; part_nr++)
144                 kfree(fa->parts[part_nr]);
145 }
146 EXPORT_SYMBOL(flex_array_free_parts);
147 
148 void flex_array_free(struct flex_array *fa)
149 {
150         flex_array_free_parts(fa);
151         kfree(fa);
152 }
153 EXPORT_SYMBOL(flex_array_free);
154 
155 static unsigned int index_inside_part(struct flex_array *fa,
156                                         unsigned int element_nr,
157                                         unsigned int part_nr)
158 {
159         unsigned int part_offset;
160 
161         part_offset = element_nr - part_nr * fa->elems_per_part;
162         return part_offset * fa->element_size;
163 }
164 
165 static struct flex_array_part *
166 __fa_get_part(struct flex_array *fa, int part_nr, gfp_t flags)
167 {
168         struct flex_array_part *part = fa->parts[part_nr];
169         if (!part) {
170                 part = kmalloc(sizeof(struct flex_array_part), flags);
171                 if (!part)
172                         return NULL;
173                 if (!(flags & __GFP_ZERO))
174                         memset(part, FLEX_ARRAY_FREE,
175                                 sizeof(struct flex_array_part));
176                 fa->parts[part_nr] = part;
177         }
178         return part;
179 }
180 
181 /**
182  * flex_array_put - copy data into the array at @element_nr
183  * @fa:         the flex array to copy data into
184  * @element_nr: index of the position in which to insert
185  *              the new element.
186  * @src:        address of data to copy into the array
187  * @flags:      page allocation flags to use for array expansion
188  *
189  *
190  * Note that this *copies* the contents of @src into
191  * the array.  If you are trying to store an array of
192  * pointers, make sure to pass in &ptr instead of ptr.
193  * You may instead wish to use the flex_array_put_ptr()
194  * helper function.
195  *
196  * Locking must be provided by the caller.
197  */
198 int flex_array_put(struct flex_array *fa, unsigned int element_nr, void *src,
199                         gfp_t flags)
200 {
201         int part_nr = 0;
202         struct flex_array_part *part;
203         void *dst;
204 
205         if (element_nr >= fa->total_nr_elements)
206                 return -ENOSPC;
207         if (!fa->element_size)
208                 return 0;
209         if (elements_fit_in_base(fa))
210                 part = (struct flex_array_part *)&fa->parts[0];
211         else {
212                 part_nr = fa_element_to_part_nr(fa, element_nr);
213                 part = __fa_get_part(fa, part_nr, flags);
214                 if (!part)
215                         return -ENOMEM;
216         }
217         dst = &part->elements[index_inside_part(fa, element_nr, part_nr)];
218         memcpy(dst, src, fa->element_size);
219         return 0;
220 }
221 EXPORT_SYMBOL(flex_array_put);
222 
223 /**
224  * flex_array_clear - clear element in array at @element_nr
225  * @fa:         the flex array of the element.
226  * @element_nr: index of the position to clear.
227  *
228  * Locking must be provided by the caller.
229  */
230 int flex_array_clear(struct flex_array *fa, unsigned int element_nr)
231 {
232         int part_nr = 0;
233         struct flex_array_part *part;
234         void *dst;
235 
236         if (element_nr >= fa->total_nr_elements)
237                 return -ENOSPC;
238         if (!fa->element_size)
239                 return 0;
240         if (elements_fit_in_base(fa))
241                 part = (struct flex_array_part *)&fa->parts[0];
242         else {
243                 part_nr = fa_element_to_part_nr(fa, element_nr);
244                 part = fa->parts[part_nr];
245                 if (!part)
246                         return -EINVAL;
247         }
248         dst = &part->elements[index_inside_part(fa, element_nr, part_nr)];
249         memset(dst, FLEX_ARRAY_FREE, fa->element_size);
250         return 0;
251 }
252 EXPORT_SYMBOL(flex_array_clear);
253 
254 /**
255  * flex_array_prealloc - guarantee that array space exists
256  * @fa:                 the flex array for which to preallocate parts
257  * @start:              index of first array element for which space is allocated
258  * @nr_elements:        number of elements for which space is allocated
259  * @flags:              page allocation flags
260  *
261  * This will guarantee that no future calls to flex_array_put()
262  * will allocate memory.  It can be used if you are expecting to
263  * be holding a lock or in some atomic context while writing
264  * data into the array.
265  *
266  * Locking must be provided by the caller.
267  */
268 int flex_array_prealloc(struct flex_array *fa, unsigned int start,
269                         unsigned int nr_elements, gfp_t flags)
270 {
271         int start_part;
272         int end_part;
273         int part_nr;
274         unsigned int end;
275         struct flex_array_part *part;
276 
277         if (!start && !nr_elements)
278                 return 0;
279         if (start >= fa->total_nr_elements)
280                 return -ENOSPC;
281         if (!nr_elements)
282                 return 0;
283 
284         end = start + nr_elements - 1;
285 
286         if (end >= fa->total_nr_elements)
287                 return -ENOSPC;
288         if (!fa->element_size)
289                 return 0;
290         if (elements_fit_in_base(fa))
291                 return 0;
292         start_part = fa_element_to_part_nr(fa, start);
293         end_part = fa_element_to_part_nr(fa, end);
294         for (part_nr = start_part; part_nr <= end_part; part_nr++) {
295                 part = __fa_get_part(fa, part_nr, flags);
296                 if (!part)
297                         return -ENOMEM;
298         }
299         return 0;
300 }
301 EXPORT_SYMBOL(flex_array_prealloc);
302 
303 /**
304  * flex_array_get - pull data back out of the array
305  * @fa:         the flex array from which to extract data
306  * @element_nr: index of the element to fetch from the array
307  *
308  * Returns a pointer to the data at index @element_nr.  Note
309  * that this is a copy of the data that was passed in.  If you
310  * are using this to store pointers, you'll get back &ptr.  You
311  * may instead wish to use the flex_array_get_ptr helper.
312  *
313  * Locking must be provided by the caller.
314  */
315 void *flex_array_get(struct flex_array *fa, unsigned int element_nr)
316 {
317         int part_nr = 0;
318         struct flex_array_part *part;
319 
320         if (!fa->element_size)
321                 return NULL;
322         if (element_nr >= fa->total_nr_elements)
323                 return NULL;
324         if (elements_fit_in_base(fa))
325                 part = (struct flex_array_part *)&fa->parts[0];
326         else {
327                 part_nr = fa_element_to_part_nr(fa, element_nr);
328                 part = fa->parts[part_nr];
329                 if (!part)
330                         return NULL;
331         }
332         return &part->elements[index_inside_part(fa, element_nr, part_nr)];
333 }
334 EXPORT_SYMBOL(flex_array_get);
335 
336 /**
337  * flex_array_get_ptr - pull a ptr back out of the array
338  * @fa:         the flex array from which to extract data
339  * @element_nr: index of the element to fetch from the array
340  *
341  * Returns the pointer placed in the flex array at element_nr using
342  * flex_array_put_ptr().  This function should not be called if the
343  * element in question was not set using the _put_ptr() helper.
344  */
345 void *flex_array_get_ptr(struct flex_array *fa, unsigned int element_nr)
346 {
347         void **tmp;
348 
349         tmp = flex_array_get(fa, element_nr);
350         if (!tmp)
351                 return NULL;
352 
353         return *tmp;
354 }
355 EXPORT_SYMBOL(flex_array_get_ptr);
356 
357 static int part_is_free(struct flex_array_part *part)
358 {
359         int i;
360 
361         for (i = 0; i < sizeof(struct flex_array_part); i++)
362                 if (part->elements[i] != FLEX_ARRAY_FREE)
363                         return 0;
364         return 1;
365 }
366 
367 /**
368  * flex_array_shrink - free unused second-level pages
369  * @fa:         the flex array to shrink
370  *
371  * Frees all second-level pages that consist solely of unused
372  * elements.  Returns the number of pages freed.
373  *
374  * Locking must be provided by the caller.
375  */
376 int flex_array_shrink(struct flex_array *fa)
377 {
378         struct flex_array_part *part;
379         int part_nr;
380         int ret = 0;
381 
382         if (!fa->total_nr_elements || !fa->element_size)
383                 return 0;
384         if (elements_fit_in_base(fa))
385                 return ret;
386         for (part_nr = 0; part_nr < FLEX_ARRAY_NR_BASE_PTRS; part_nr++) {
387                 part = fa->parts[part_nr];
388                 if (!part)
389                         continue;
390                 if (part_is_free(part)) {
391                         fa->parts[part_nr] = NULL;
392                         kfree(part);
393                         ret++;
394                 }
395         }
396         return ret;
397 }
398 EXPORT_SYMBOL(flex_array_shrink);
399 
```
