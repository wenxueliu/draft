  1 /*
  2         kmod, the new module loader (replaces kerneld)
  3         Kirk Petersen
  4 
  5         Reorganized not to be a daemon by Adam Richter, with guidance
  6         from Greg Zornetzer.
  7 
  8         Modified to avoid chroot and file sharing problems.
  9         Mikael Pettersson
 10 
 11         Limit the concurrent number of kmod modprobes to catch loops from
 12         "modprobe needs a service that is in a module".
 13         Keith Owens <kaos@ocs.com.au> December 1999
 14 
 15         Unblock all signals when we exec a usermode process.
 16         Shuu Yamaguchi <shuu@wondernetworkresources.com> December 2000
 17 
 18         call_usermodehelper wait flag, and remove exec_usermodehelper.
 19         Rusty Russell <rusty@rustcorp.com.au>  Jan 2003
 20 */
 21 #include <linux/module.h>
 22 #include <linux/sched.h>
 23 #include <linux/syscalls.h>
 24 #include <linux/unistd.h>
 25 #include <linux/kmod.h>
 26 #include <linux/slab.h>
 27 #include <linux/completion.h>
 28 #include <linux/cred.h>
 29 #include <linux/file.h>
 30 #include <linux/fdtable.h>
 31 #include <linux/workqueue.h>
 32 #include <linux/security.h>
 33 #include <linux/mount.h>
 34 #include <linux/kernel.h>
 35 #include <linux/init.h>
 36 #include <linux/resource.h>
 37 #include <linux/notifier.h>
 38 #include <linux/suspend.h>
 39 #include <linux/rwsem.h>
 40 #include <linux/ptrace.h>
 41 #include <linux/async.h>
 42 #include <asm/uaccess.h>
 43 
 44 #include <trace/events/module.h>
 45 
 46 extern int max_threads;
 47 
 48 static struct workqueue_struct *khelper_wq;
 49 
 50 #define CAP_BSET        (void *)1
 51 #define CAP_PI          (void *)2
 52 
 53 static kernel_cap_t usermodehelper_bset = CAP_FULL_SET;
 54 static kernel_cap_t usermodehelper_inheritable = CAP_FULL_SET;
 55 static DEFINE_SPINLOCK(umh_sysctl_lock);
 56 static DECLARE_RWSEM(umhelper_sem);
 57 
 58 #ifdef CONFIG_MODULES
 59 
 60 /*
 61         modprobe_path is set via /proc/sys.
 62 */
 63 char modprobe_path[KMOD_PATH_LEN] = "/sbin/modprobe";
 64 
 65 static void free_modprobe_argv(struct subprocess_info *info)
 66 {
 67         kfree(info->argv[3]); /* check call_modprobe() */
 68         kfree(info->argv);
 69 }
 70 
 71 static int call_modprobe(char *module_name, int wait)
 72 {
 73         struct subprocess_info *info;
 74         static char *envp[] = {
 75                 "HOME=/",
 76                 "TERM=linux",
 77                 "PATH=/sbin:/usr/sbin:/bin:/usr/bin",
 78                 NULL
 79         };
 80 
 81         char **argv = kmalloc(sizeof(char *[5]), GFP_KERNEL);
 82         if (!argv)
 83                 goto out;
 84 
 85         module_name = kstrdup(module_name, GFP_KERNEL);
 86         if (!module_name)
 87                 goto free_argv;
 88 
 89         argv[0] = modprobe_path;
 90         argv[1] = "-q";
 91         argv[2] = "--";
 92         argv[3] = module_name;  /* check free_modprobe_argv() */
 93         argv[4] = NULL;
 94 
 95         info = call_usermodehelper_setup(modprobe_path, argv, envp, GFP_KERNEL,
 96                                          NULL, free_modprobe_argv, NULL);
 97         if (!info)
 98                 goto free_module_name;
 99 
100         return call_usermodehelper_exec(info, wait | UMH_KILLABLE);
101 
102 free_module_name:
103         kfree(module_name);
104 free_argv:
105         kfree(argv);
106 out:
107         return -ENOMEM;
108 }
109 
110 /**
111  * __request_module - try to load a kernel module
112  * @wait: wait (or not) for the operation to complete
113  * @fmt: printf style format string for the name of the module
114  * @...: arguments as specified in the format string
115  *
116  * Load a module using the user mode module loader. The function returns
117  * zero on success or a negative errno code on failure. Note that a
118  * successful module load does not mean the module did not then unload
119  * and exit on an error of its own. Callers must check that the service
120  * they requested is now available not blindly invoke it.
121  *
122  * If module auto-loading support is disabled then this function
123  * becomes a no-operation.
124  */
125 int __request_module(bool wait, const char *fmt, ...)
126 {
127         va_list args;
128         char module_name[MODULE_NAME_LEN];
129         unsigned int max_modprobes;
130         int ret;
131         static atomic_t kmod_concurrent = ATOMIC_INIT(0);
132 #define MAX_KMOD_CONCURRENT 50  /* Completely arbitrary value - KAO */
133         static int kmod_loop_msg;
134 
135         /*
136          * We don't allow synchronous module loading from async.  Module
137          * init may invoke async_synchronize_full() which will end up
138          * waiting for this task which already is waiting for the module
139          * loading to complete, leading to a deadlock.
140          */
141         WARN_ON_ONCE(wait && current_is_async());
142 
143         if (!modprobe_path[0])
144                 return 0;
145 
146         va_start(args, fmt);
147         ret = vsnprintf(module_name, MODULE_NAME_LEN, fmt, args);
148         va_end(args);
149         if (ret >= MODULE_NAME_LEN)
150                 return -ENAMETOOLONG;
151 
152         ret = security_kernel_module_request(module_name);
153         if (ret)
154                 return ret;
155 
156         /* If modprobe needs a service that is in a module, we get a recursive
157          * loop.  Limit the number of running kmod threads to max_threads/2 or
158          * MAX_KMOD_CONCURRENT, whichever is the smaller.  A cleaner method
159          * would be to run the parents of this process, counting how many times
160          * kmod was invoked.  That would mean accessing the internals of the
161          * process tables to get the command line, proc_pid_cmdline is static
162          * and it is not worth changing the proc code just to handle this case. 
163          * KAO.
164          *
165          * "trace the ppid" is simple, but will fail if someone's
166          * parent exits.  I think this is as good as it gets. --RR
167          */
168         max_modprobes = min(max_threads/2, MAX_KMOD_CONCURRENT);
169         atomic_inc(&kmod_concurrent);
170         if (atomic_read(&kmod_concurrent) > max_modprobes) {
171                 /* We may be blaming an innocent here, but unlikely */
172                 if (kmod_loop_msg < 5) {
173                         printk(KERN_ERR
174                                "request_module: runaway loop modprobe %s\n",
175                                module_name);
176                         kmod_loop_msg++;
177                 }
178                 atomic_dec(&kmod_concurrent);
179                 return -ENOMEM;
180         }
181 
182         trace_module_request(module_name, wait, _RET_IP_);
183 
184         ret = call_modprobe(module_name, wait ? UMH_WAIT_PROC : UMH_WAIT_EXEC);
185 
186         atomic_dec(&kmod_concurrent);
187         return ret;
188 }
189 EXPORT_SYMBOL(__request_module);
190 #endif /* CONFIG_MODULES */
191 
192 static void call_usermodehelper_freeinfo(struct subprocess_info *info)
193 {
194         if (info->cleanup)
195                 (*info->cleanup)(info);
196         kfree(info);
197 }
198 
199 static void umh_complete(struct subprocess_info *sub_info)
200 {
201         struct completion *comp = xchg(&sub_info->complete, NULL);
202         /*
203          * See call_usermodehelper_exec(). If xchg() returns NULL
204          * we own sub_info, the UMH_KILLABLE caller has gone away
205          * or the caller used UMH_NO_WAIT.
206          */
207         if (comp)
208                 complete(comp);
209         else
210                 call_usermodehelper_freeinfo(sub_info);
211 }
212 
213 /*
214  * This is the task which runs the usermode application
215  */
216 static int ____call_usermodehelper(void *data)
217 {
218         struct subprocess_info *sub_info = data;
219         struct cred *new;
220         int retval;
221 
222         spin_lock_irq(&current->sighand->siglock);
223         flush_signal_handlers(current, 1);
224         spin_unlock_irq(&current->sighand->siglock);
225 
226         /* We can run anywhere, unlike our parent keventd(). */
227         set_cpus_allowed_ptr(current, cpu_all_mask);
228 
229         /*
230          * Our parent is keventd, which runs with elevated scheduling priority.
231          * Avoid propagating that into the userspace child.
232          */
233         set_user_nice(current, 0);
234 
235         retval = -ENOMEM;
236         new = prepare_kernel_cred(current);
237         if (!new)
238                 goto out;
239 
240         spin_lock(&umh_sysctl_lock);
241         new->cap_bset = cap_intersect(usermodehelper_bset, new->cap_bset);
242         new->cap_inheritable = cap_intersect(usermodehelper_inheritable,
243                                              new->cap_inheritable);
244         spin_unlock(&umh_sysctl_lock);
245 
246         if (sub_info->init) {
247                 retval = sub_info->init(sub_info, new);
248                 if (retval) {
249                         abort_creds(new);
250                         goto out;
251                 }
252         }
253 
254         commit_creds(new);
255 
256         retval = do_execve(getname_kernel(sub_info->path),
257                            (const char __user *const __user *)sub_info->argv,
258                            (const char __user *const __user *)sub_info->envp);
259 out:
260         sub_info->retval = retval;
261         /* wait_for_helper() will call umh_complete if UHM_WAIT_PROC. */
262         if (!(sub_info->wait & UMH_WAIT_PROC))
263                 umh_complete(sub_info);
264         if (!retval)
265                 return 0;
266         do_exit(0);
267 }
268 
269 /* Keventd can't block, but this (a child) can. */
270 static int wait_for_helper(void *data)
271 {
272         struct subprocess_info *sub_info = data;
273         pid_t pid;
274 
275         /* If SIGCLD is ignored sys_wait4 won't populate the status. */
276         kernel_sigaction(SIGCHLD, SIG_DFL);
277         pid = kernel_thread(____call_usermodehelper, sub_info, SIGCHLD);
278         if (pid < 0) {
279                 sub_info->retval = pid;
280         } else {
281                 int ret = -ECHILD;
282                 /*
283                  * Normally it is bogus to call wait4() from in-kernel because
284                  * wait4() wants to write the exit code to a userspace address.
285                  * But wait_for_helper() always runs as keventd, and put_user()
286                  * to a kernel address works OK for kernel threads, due to their
287                  * having an mm_segment_t which spans the entire address space.
288                  *
289                  * Thus the __user pointer cast is valid here.
290                  */
291                 sys_wait4(pid, (int __user *)&ret, 0, NULL);
292 
293                 /*
294                  * If ret is 0, either ____call_usermodehelper failed and the
295                  * real error code is already in sub_info->retval or
296                  * sub_info->retval is 0 anyway, so don't mess with it then.
297                  */
298                 if (ret)
299                         sub_info->retval = ret;
300         }
301 
302         umh_complete(sub_info);
303         do_exit(0);
304 }
305 
306 /* This is run by khelper thread  */
307 static void __call_usermodehelper(struct work_struct *work)
308 {
309         struct subprocess_info *sub_info =
310                 container_of(work, struct subprocess_info, work);
311         pid_t pid;
312 
313         if (sub_info->wait & UMH_WAIT_PROC)
314                 pid = kernel_thread(wait_for_helper, sub_info,
315                                     CLONE_FS | CLONE_FILES | SIGCHLD);
316         else
317                 pid = kernel_thread(____call_usermodehelper, sub_info,
318                                     SIGCHLD);
319 
320         if (pid < 0) {
321                 sub_info->retval = pid;
322                 umh_complete(sub_info);
323         }
324 }
325 
326 /*
327  * If set, call_usermodehelper_exec() will exit immediately returning -EBUSY
328  * (used for preventing user land processes from being created after the user
329  * land has been frozen during a system-wide hibernation or suspend operation).
330  * Should always be manipulated under umhelper_sem acquired for write.
331  */
332 static enum umh_disable_depth usermodehelper_disabled = UMH_DISABLED;
333 
334 /* Number of helpers running */
335 static atomic_t running_helpers = ATOMIC_INIT(0);
336 
337 /*
338  * Wait queue head used by usermodehelper_disable() to wait for all running
339  * helpers to finish.
340  */
341 static DECLARE_WAIT_QUEUE_HEAD(running_helpers_waitq);
342 
343 /*
344  * Used by usermodehelper_read_lock_wait() to wait for usermodehelper_disabled
345  * to become 'false'.
346  */
347 static DECLARE_WAIT_QUEUE_HEAD(usermodehelper_disabled_waitq);
348 
349 /*
350  * Time to wait for running_helpers to become zero before the setting of
351  * usermodehelper_disabled in usermodehelper_disable() fails
352  */
353 #define RUNNING_HELPERS_TIMEOUT (5 * HZ)
354 
355 int usermodehelper_read_trylock(void)
356 {
357         DEFINE_WAIT(wait);
358         int ret = 0;
359 
360         down_read(&umhelper_sem);
361         for (;;) {
362                 prepare_to_wait(&usermodehelper_disabled_waitq, &wait,
363                                 TASK_INTERRUPTIBLE);
364                 if (!usermodehelper_disabled)
365                         break;
366 
367                 if (usermodehelper_disabled == UMH_DISABLED)
368                         ret = -EAGAIN;
369 
370                 up_read(&umhelper_sem);
371 
372                 if (ret)
373                         break;
374 
375                 schedule();
376                 try_to_freeze();
377 
378                 down_read(&umhelper_sem);
379         }
380         finish_wait(&usermodehelper_disabled_waitq, &wait);
381         return ret;
382 }
383 EXPORT_SYMBOL_GPL(usermodehelper_read_trylock);
384 
385 long usermodehelper_read_lock_wait(long timeout)
386 {
387         DEFINE_WAIT(wait);
388 
389         if (timeout < 0)
390                 return -EINVAL;
391 
392         down_read(&umhelper_sem);
393         for (;;) {
394                 prepare_to_wait(&usermodehelper_disabled_waitq, &wait,
395                                 TASK_UNINTERRUPTIBLE);
396                 if (!usermodehelper_disabled)
397                         break;
398 
399                 up_read(&umhelper_sem);
400 
401                 timeout = schedule_timeout(timeout);
402                 if (!timeout)
403                         break;
404 
405                 down_read(&umhelper_sem);
406         }
407         finish_wait(&usermodehelper_disabled_waitq, &wait);
408         return timeout;
409 }
410 EXPORT_SYMBOL_GPL(usermodehelper_read_lock_wait);
411 
412 void usermodehelper_read_unlock(void)
413 {
414         up_read(&umhelper_sem);
415 }
416 EXPORT_SYMBOL_GPL(usermodehelper_read_unlock);
417 
418 /**
419  * __usermodehelper_set_disable_depth - Modify usermodehelper_disabled.
420  * @depth: New value to assign to usermodehelper_disabled.
421  *
422  * Change the value of usermodehelper_disabled (under umhelper_sem locked for
423  * writing) and wakeup tasks waiting for it to change.
424  */
425 void __usermodehelper_set_disable_depth(enum umh_disable_depth depth)
426 {
427         down_write(&umhelper_sem);
428         usermodehelper_disabled = depth;
429         wake_up(&usermodehelper_disabled_waitq);
430         up_write(&umhelper_sem);
431 }
432 
433 /**
434  * __usermodehelper_disable - Prevent new helpers from being started.
435  * @depth: New value to assign to usermodehelper_disabled.
436  *
437  * Set usermodehelper_disabled to @depth and wait for running helpers to exit.
438  */
439 int __usermodehelper_disable(enum umh_disable_depth depth)
440 {
441         long retval;
442 
443         if (!depth)
444                 return -EINVAL;
445 
446         down_write(&umhelper_sem);
447         usermodehelper_disabled = depth;
448         up_write(&umhelper_sem);
449 
450         /*
451          * From now on call_usermodehelper_exec() won't start any new
452          * helpers, so it is sufficient if running_helpers turns out to
453          * be zero at one point (it may be increased later, but that
454          * doesn't matter).
455          */
456         retval = wait_event_timeout(running_helpers_waitq,
457                                         atomic_read(&running_helpers) == 0,
458                                         RUNNING_HELPERS_TIMEOUT);
459         if (retval)
460                 return 0;
461 
462         __usermodehelper_set_disable_depth(UMH_ENABLED);
463         return -EAGAIN;
464 }
465 
466 static void helper_lock(void)
467 {
468         atomic_inc(&running_helpers);
469         smp_mb__after_atomic();
470 }
471 
472 static void helper_unlock(void)
473 {
474         if (atomic_dec_and_test(&running_helpers))
475                 wake_up(&running_helpers_waitq);
476 }
477 
478 /**
479  * call_usermodehelper_setup - prepare to call a usermode helper
480  * @path: path to usermode executable
481  * @argv: arg vector for process
482  * @envp: environment for process
483  * @gfp_mask: gfp mask for memory allocation
484  * @cleanup: a cleanup function
485  * @init: an init function
486  * @data: arbitrary context sensitive data
487  *
488  * Returns either %NULL on allocation failure, or a subprocess_info
489  * structure.  This should be passed to call_usermodehelper_exec to
490  * exec the process and free the structure.
491  *
492  * The init function is used to customize the helper process prior to
493  * exec.  A non-zero return code causes the process to error out, exit,
494  * and return the failure to the calling process
495  *
496  * The cleanup function is just before ethe subprocess_info is about to
497  * be freed.  This can be used for freeing the argv and envp.  The
498  * Function must be runnable in either a process context or the
499  * context in which call_usermodehelper_exec is called.
500  */
501 struct subprocess_info *call_usermodehelper_setup(char *path, char **argv,
502                 char **envp, gfp_t gfp_mask,
503                 int (*init)(struct subprocess_info *info, struct cred *new),
504                 void (*cleanup)(struct subprocess_info *info),
505                 void *data)
506 {
507         struct subprocess_info *sub_info;
508         sub_info = kzalloc(sizeof(struct subprocess_info), gfp_mask);
509         if (!sub_info)
510                 goto out;
511 
512         INIT_WORK(&sub_info->work, __call_usermodehelper);
513         sub_info->path = path;
514         sub_info->argv = argv;
515         sub_info->envp = envp;
516 
517         sub_info->cleanup = cleanup;
518         sub_info->init = init;
519         sub_info->data = data;
520   out:
521         return sub_info;
522 }
523 EXPORT_SYMBOL(call_usermodehelper_setup);
524 
525 /**
526  * call_usermodehelper_exec - start a usermode application
527  * @sub_info: information about the subprocessa
528  * @wait: wait for the application to finish and return status.
529  *        when UMH_NO_WAIT don't wait at all, but you get no useful error back
530  *        when the program couldn't be exec'ed. This makes it safe to call
531  *        from interrupt context.
532  *
533  * Runs a user-space application.  The application is started
534  * asynchronously if wait is not set, and runs as a child of keventd.
535  * (ie. it runs with full root capabilities).
536  */
537 int call_usermodehelper_exec(struct subprocess_info *sub_info, int wait)
538 {
539         DECLARE_COMPLETION_ONSTACK(done);
540         int retval = 0;
541 
542         if (!sub_info->path) {
543                 call_usermodehelper_freeinfo(sub_info);
544                 return -EINVAL;
545         }
546         helper_lock();
547         if (!khelper_wq || usermodehelper_disabled) {
548                 retval = -EBUSY;
549                 goto out;
550         }
551         /*
552          * Set the completion pointer only if there is a waiter.
553          * This makes it possible to use umh_complete to free
554          * the data structure in case of UMH_NO_WAIT.
555          */
556         sub_info->complete = (wait == UMH_NO_WAIT) ? NULL : &done;
557         sub_info->wait = wait;
558 
559         queue_work(khelper_wq, &sub_info->work);
560         if (wait == UMH_NO_WAIT)        /* task has freed sub_info */
561                 goto unlock;
562 
563         if (wait & UMH_KILLABLE) {
564                 retval = wait_for_completion_killable(&done);
565                 if (!retval)
566                         goto wait_done;
567 
568                 /* umh_complete() will see NULL and free sub_info */
569                 if (xchg(&sub_info->complete, NULL))
570                         goto unlock;
571                 /* fallthrough, umh_complete() was already called */
572         }
573 
574         wait_for_completion(&done);
575 wait_done:
576         retval = sub_info->retval;
577 out:
578         call_usermodehelper_freeinfo(sub_info);
579 unlock:
580         helper_unlock();
581         return retval;
582 }
583 EXPORT_SYMBOL(call_usermodehelper_exec);
584 
585 /**
586  * call_usermodehelper() - prepare and start a usermode application
587  * @path: path to usermode executable
588  * @argv: arg vector for process
589  * @envp: environment for process
590  * @wait: wait for the application to finish and return status.
591  *        when UMH_NO_WAIT don't wait at all, but you get no useful error back
592  *        when the program couldn't be exec'ed. This makes it safe to call
593  *        from interrupt context.
594  *
595  * This function is the equivalent to use call_usermodehelper_setup() and
596  * call_usermodehelper_exec().
597  */
598 int call_usermodehelper(char *path, char **argv, char **envp, int wait)
599 {
600         struct subprocess_info *info;
601         gfp_t gfp_mask = (wait == UMH_NO_WAIT) ? GFP_ATOMIC : GFP_KERNEL;
602 
603         info = call_usermodehelper_setup(path, argv, envp, gfp_mask,
604                                          NULL, NULL, NULL);
605         if (info == NULL)
606                 return -ENOMEM;
607 
608         return call_usermodehelper_exec(info, wait);
609 }
610 EXPORT_SYMBOL(call_usermodehelper);
611 
612 static int proc_cap_handler(struct ctl_table *table, int write,
613                          void __user *buffer, size_t *lenp, loff_t *ppos)
614 {
615         struct ctl_table t;
616         unsigned long cap_array[_KERNEL_CAPABILITY_U32S];
617         kernel_cap_t new_cap;
618         int err, i;
619 
620         if (write && (!capable(CAP_SETPCAP) ||
621                       !capable(CAP_SYS_MODULE)))
622                 return -EPERM;
623 
624         /*
625          * convert from the global kernel_cap_t to the ulong array to print to
626          * userspace if this is a read.
627          */
628         spin_lock(&umh_sysctl_lock);
629         for (i = 0; i < _KERNEL_CAPABILITY_U32S; i++)  {
630                 if (table->data == CAP_BSET)
631                         cap_array[i] = usermodehelper_bset.cap[i];
632                 else if (table->data == CAP_PI)
633                         cap_array[i] = usermodehelper_inheritable.cap[i];
634                 else
635                         BUG();
636         }
637         spin_unlock(&umh_sysctl_lock);
638 
639         t = *table;
640         t.data = &cap_array;
641 
642         /*
643          * actually read or write and array of ulongs from userspace.  Remember
644          * these are least significant 32 bits first
645          */
646         err = proc_doulongvec_minmax(&t, write, buffer, lenp, ppos);
647         if (err < 0)
648                 return err;
649 
650         /*
651          * convert from the sysctl array of ulongs to the kernel_cap_t
652          * internal representation
653          */
654         for (i = 0; i < _KERNEL_CAPABILITY_U32S; i++)
655                 new_cap.cap[i] = cap_array[i];
656 
657         /*
658          * Drop everything not in the new_cap (but don't add things)
659          */
660         spin_lock(&umh_sysctl_lock);
661         if (write) {
662                 if (table->data == CAP_BSET)
663                         usermodehelper_bset = cap_intersect(usermodehelper_bset, new_cap);
664                 if (table->data == CAP_PI)
665                         usermodehelper_inheritable = cap_intersect(usermodehelper_inheritable, new_cap);
666         }
667         spin_unlock(&umh_sysctl_lock);
668 
669         return 0;
670 }
671 
672 struct ctl_table usermodehelper_table[] = {
673         {
674                 .procname       = "bset",
675                 .data           = CAP_BSET,
676                 .maxlen         = _KERNEL_CAPABILITY_U32S * sizeof(unsigned long),
677                 .mode           = 0600,
678                 .proc_handler   = proc_cap_handler,
679         },
680         {
681                 .procname       = "inheritable",
682                 .data           = CAP_PI,
683                 .maxlen         = _KERNEL_CAPABILITY_U32S * sizeof(unsigned long),
684                 .mode           = 0600,
685                 .proc_handler   = proc_cap_handler,
686         },
687         { }
688 };
689 
690 void __init usermodehelper_init(void)
691 {
692         khelper_wq = create_singlethread_workqueue("khelper");
693         BUG_ON(!khelper_wq);
694 }
695 
