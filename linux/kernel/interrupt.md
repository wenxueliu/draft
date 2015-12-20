
FROM :https://github.com/illumos/illumos-gate/blob/master/usr/src/uts/i86pc/os/intr.c#L28-#L438

/*
* To understand the present state of interrupt handling on i86pc, we must
* first consider the history of interrupt controllers and our way of handling
* interrupts.
*
* History of Interrupt Controllers on i86pc
* -----------------------------------------
*
* Intel 8259 and 8259A
*
* The first interrupt controller that attained widespread use on i86pc was
* the Intel 8259(A) Programmable Interrupt Controller that first saw use with
* the 8086. It took up to 8 interrupt sources and combined them into one
* output wire. Up to 8 8259s could be slaved together providing up to 64 IRQs.
* With the switch to the 8259A, level mode interrupts became possible. For a
* long time on i86pc the 8259A was the only way to handle interrupts and it
* had its own set of quirks. The 8259A and its corresponding interval timer
* the 8254 are programmed using outb and inb instructions.
*
* Intel Advanced Programmable Interrupt Controller (APIC)
*
* Starting around the time of the introduction of the P6 family
* microarchitecture (i686) Intel introduced a new interrupt controller.
* Instead of having the series of slaved 8259A devices, Intel opted to outfit
* each processor with a Local APIC (lapic) and to outfit the system with at
* least one, but potentially more, I/O APICs (ioapic). The lapics and ioapics
* initially communicated over a dedicated bus, but this has since been
* replaced. Each physical core and even hyperthread currently contains its
* own local apic, which is not shared. There are a few exceptions for
* hyperthreads, but that does not usually concern us.
*
* Instead of talking directly to 8259 for status, sending End Of Interrupt
* (EOI), etc. a microprocessor now communicates directly to the lapic. This
* also allows for each microprocessor to be able to have independent controls.
* The programming method is different from the 8259. Consumers map the lapic
* registers into uncacheable memory to read and manipulate the state.
*
* The number of addressable interrupt vectors was increased to 256. However
* vectors 0-31 are reserved for the processor exception handling, leaving the
* remaining vectors for general use. In addition to hardware generated
* interrupts, the lapic provides a way for generating inter-processor
* interrupts (IPI) which are the basis for CPU cross calls and CPU pokes.
*
* AMD ended up implementing the Intel APIC architecture in lieu of their work
* with Cyrix.
*
* Intel x2apic
*
* The x2apic is an extension to the lapic which started showing up around the
* same time as the Sandy Bridge chipsets. It provides a new programming mode
* as well as new features. The goal of the x2apic is to solve a few problems
* with the previous generation of lapic and the x2apic is backwards compatible
* with the previous programming and model. The only downsides to using the
* backwards compatibility is that you are not able to take advantage of the new
* x2apic features.
*
* o The APIC ID is increased from an 8-bit value to a 32-bit value. This
* increases the maximum number of addressable physical processors beyond
* 256. This new ID is assembled in a similar manner as the information that
* is obtainable by the extended cpuid topology leaves.
*
* o A new means of generating IPIs was introduced.
*
* o Instead of memory mapping the registers, the x2apic only allows for
* programming it through a series of wrmsrs. This has important semantic
* side effects. Recall that the registers were previously all mapped to
* uncachable memory which meant that all operations to the local apic were
* serializing instructions. With the switch to using wrmsrs this has been
* relaxed and these operations can no longer be assumed to be serializing
* instructions.
*
* Note for the rest of this we are only going to concern ourselves with the
* apic and x2apic which practically all of i86pc has been using now for
* quite some time.
*
* Interrupt Priority Levels
* -------------------------
*
* On i86pc systems there are a total of fifteen interrupt priority levels
* (ipls) which range from 1-15. Level 0 is for normal processing and
* non-interrupt processing. To manipulate these values the family of spl
* functions (which date back to UNIX on the PDP-11) are used. Specifically,
* splr() to raise the priority level and splx() to lower it. One should not
* generally call setspl() directly.
*
* Both i86pc and the supported SPARC platforms honor the same conventions for
* the meaning behind these IPLs. The most important IPL is the platform's
* LOCK_LEVEL (0xa on i86pc). If a thread is above LOCK_LEVEL it _must_ not
* sleep on any synchronization object. The only allowed synchronization
* primitive is a mutex that has been specifically initialized to be a spin
* lock (see mutex_init(9F)). Another important level is DISP_LEVEL (0xb on
* i86pc). You must be at DISP_LEVEL if you want to control the dispatcher.
* The XC_HI_PIL is the highest level (0xf) and is used during cross-calls.
*
* Each interrupt that is registered in the system fires at a specific IPL.
* Generally most interrupts fire below LOCK_LEVEL.
*
* PSM Drivers
* -----------
*
* We currently have three sets of PSM (platform specific module) drivers
* available. uppc, pcplusmp, and apix. uppc (uni-processor PC) is the original
* driver that interacts with the 8259A and 8254. In general, it is not used
* anymore given the prevalence of the apic.
*
* The system prefers to use the apix driver over the pcplusmp driver. The apix
* driver requires HW support for an x2apic. If there is no x2apic HW, apix
* will not be used. In general we prefer using the apix driver over the
* pcplusmp driver because it gives us much more flexibility with respect to
* interrupts. In the apix driver each local apic has its own independent set
* of interrupts, whereas the pcplusmp driver only has a single global set of
* interrupts. This is why pcplusmp only supports a finite number of interrupts
* per IPL -- generally 16, often less. The apix driver supports using either
* the x2apic or the local apic programing modes. The programming mode does not
* change the number of interrupts available, just the number of processors
* that we can address. For the apix driver, the x2apic mode is enabled if the
* system supports interrupt re-mapping, otherwise the module manages the
* x2apic in local mode.
*
* When there is no x2apic present, we default back to the pcplusmp PSM driver.
* In general, this is not problematic unless you have more than 256
* processors in the machine or you do not have enough interrupts available.
*
* Controlling Interrupt Generation on i86pc
* -----------------------------------------
*
* There are two different ways to manipulate which interrupts will be
* generated on i86pc. Each offers different degrees of control.
*
* The first is through the flags register (eflags and rflags on i386 and amd64
* respectively). The IF bit determines whether or not interrupts are enabled
* or disabled. This is manipulated in one of several ways. The most common way
* is through the cli and sti instructions. These clear the IF flag and set it,
* respectively, for the current processor. The other common way is through the
* use of the intr_clear and intr_restore functions.
*
* Assuming interrupts are not blocked by the IF flag, then the second form is
* through the Processor-Priority Register (PPR). The PPR is used to determine
* whether or not a pending interrupt should be delivered. If the ipl of the
* new interrupt is higher than the current value in the PPR, then the lapic
* will either deliver it immediately (if interrupts are not in progress) or it
* will deliver it once the current interrupt processing has issued an EOI. The
* highest unmasked interrupt will be the one delivered.
*
* The PPR register is based upon the max of the following two registers in the
* lapic, the TPR register (also known as CR8 on amd64) that can be used to
* mask interrupt levels, and the current vector. Because the pcplusmp module
* always sets TPR appropriately early in the do_interrupt path, we can usually
* just think that the PPR is the TPR. The pcplusmp module also issues an EOI
* once it has set the TPR, so higher priority interrupts can come in while
* we're servicing a lower priority interrupt.
*
* Handling Interrupts
* -------------------
*
* Interrupts can be broken down into three categories based on priority and
* source:
*
* o High level interrupts
* o Low level hardware interrupts
* o Low level software interrupts
*
* High Level Interrupts
*
* High level interrupts encompasses both hardware-sourced and software-sourced
* interrupts. Examples of high level hardware interrupts include the serial
* console. High level software-sourced interrupts are still delivered through
* the local apic through IPIs. This is primarily cross calls.
*
* When a high level interrupt comes in, we will raise the SPL and then pin the
* current lwp to the processor. We will use its lwp, but our own interrupt
* stack and process the high level interrupt in-situ. These handlers are
* designed to be very short in nature and cannot go to sleep, only block on a
* spin lock. If the interrupt has a lot of work to do, it must generate a
* low-priority software interrupt that will be processed later.
*
* Low level hardware interrupts
*
* Low level hardware interrupts start off like their high-level cousins. The
* current CPU contains a number of kernel threads (kthread_t) that can be used
* to process low level interrupts. These are shared between both low level
* hardware and software interrupts. Note that while we run with our
* kthread_t, we borrow the pinned threads lwp_t until such a time as we hit a
* synchronization object. If we hit one and need to sleep, then the scheduler
* will instead create the rest of what we need.
*
* Low level software interrupts
*
* Low level software interrupts are handled in a similar way as hardware
* interrupts, but the notification vector is different. Each CPU has a bitmask
* of pending software interrupts. We can notify a CPU to process software
* interrupts through a specific trap vector as well as through several
* checks that are performed throughout the code. These checks will look at
* processing software interrupts as we lower our spl.
*
* We attempt to process the highest pending software interrupt that we can
* which is greater than our current IPL. If none currently exist, then we move
* on. We process a software interrupt in a similar fashion to a hardware
* interrupt.
*
* Traditional Interrupt Flow
* --------------------------
*
* The following diagram tracks the flow of the traditional uppc and pcplusmp
* interrupt handlers. The apix driver has its own version of do_interrupt().
* We come into the interrupt handler with all interrupts masked by the IF
* flag. This is because we set up the handler using an interrupt-gate, which
* is defined architecturally to have cleared the IF flag for us.
*
* +--------------+ +----------------+ +-----------+
* | _interrupt() |--->| do_interrupt() |--->| *setlvl() |
* +--------------+ +----------------+ +-----------+
* | | |
* | | |
* low-level| | | softint
* HW int | | +---------------------------------------+
* +--------------+ | | |
* | intr_thread_ |<-----+ | hi-level int |
* | prolog() | | +----------+ |
* +--------------+ +--->| hilevel_ | Not on intr stack |
* | | intr_ |-----------------+ |
* | | prolog() | | |
* +------------+ +----------+ | |
* | switch_sp_ | | On intr v |
* | and_call() | | Stack +------------+ |
* +------------+ | | switch_sp_ | |
* | v | and_call() | |
* v +-----------+ +------------+ |
* +-----------+ | dispatch_ | | |
* | dispatch_ | +-------------------| hilevel() |<------------+ |
* | hardint() | | +-----------+ |
* +-----------+ | |
* | v |
* | +-----+ +----------------------+ +-----+ hi-level |
* +---->| sti |->| av_dispatch_autovect |->| cli |---------+ |
* +-----+ +----------------------+ +-----+ | |
* | | | |
* v | | |
* +----------+ | | |
* | for each | | | |
* | handler | | | |
* | *intr() | | v |
* +--------------+ +----------+ | +----------------+ |
* | intr_thread_ | low-level | | hilevel_intr_ | |
* | epilog() |<-------------------------------+ | epilog() | |
* +--------------+ +----------------+ |
* | | | |
* | +----------------------v v---------------------+ |
* | +------------+ |
* | +---------------------->| *setlvlx() | |
* | | +------------+ |
* | | | |
* | | v |
* | | +--------+ +------------------+ +-------------+ |
* | | | return |<----| softint pending? |----->| dosoftint() |<-----+
* | | +--------+ no +------------------+ yes +-------------+
* | | ^ | |
* | | | softint pil too low | |
* | | +--------------------------------------+ |
* | | v
* | | +-----------+ +------------+ +-----------+
* | | | dispatch_ |<-----| switch_sp_ |<---------| *setspl() |
* | | | softint() | | and_call() | +-----------+
* | | +-----------+ +------------+
* | | |
* | | v
* | | +-----+ +----------------------+ +-----+ +------------+
* | | | sti |->| av_dispatch_autovect |->| cli |->| dosoftint_ |
* | | +-----+ +----------------------+ +-----+ | epilog() |
* | | +------------+
* | | | |
* | +----------------------------------------------------+ |
* v |
* +-----------+ |
* | interrupt | |
* | thread |<---------------------------------------------------+
* | blocked |
* +-----------+
* |
* v
* +----------------+ +------------+ +-----------+ +-------+ +---------+
* | set_base_spl() |->| *setlvlx() |->| splhigh() |->| sti() |->| swtch() |
* +----------------+ +------------+ +-----------+ +-------+ +---------+
*
* Calls made on Interrupt Stacks and Epilogue routines
*
* We use the switch_sp_and_call() assembly routine to switch our sp to the
* interrupt stacks and then call the appropriate dispatch function. In the
* case of interrupts which may block, softints and hardints, we always ensure
* that we are still on the interrupt thread when we call the epilog routine.
* This is not just important, it's necessary. If the interrupt thread blocked,
* we won't return from our switch_sp_and_call() function and instead we'll go
* through and set ourselves up to swtch() directly.
*
* New Interrupt Flow
* ------------------
*
* The apix module has its own interrupt path. This is done for various
* reasons. The first is that rather than having global interrupt vectors, we
* now have per-cpu vectors.
*
* The other substantial change is that the apix design does not use the TPR to
* mask interrupts below the current level. In fact, except for one special
* case, it does not use the TPR at all. Instead, it only uses the IF flag
* (cli/sti) to either block all interrupts or allow any interrupts to come in.
* The design is such that when interrupts are allowed to come in, if we are
* currently servicing a higher priority interupt, the new interrupt is treated
* as pending and serviced later. Specifically, in the pcplusmp module's
* apic_intr_enter() the code masks interrupts at or below the current
* IPL using the TPR before sending EOI, whereas the apix module's
* apix_intr_enter() simply sends EOI.
*
* The one special case where the apix code uses the TPR is when it calls
* through the apic_reg_ops function pointer apic_write_task_reg in
* apix_init_intr() to initially mask all levels and then finally to enable all
* levels.
*
* Recall that we come into the interrupt handler with all interrupts masked
* by the IF flag. This is because we set up the handler using an
* interrupt-gate which is defined architecturally to have cleared the IF flag
* for us.
*
* +--------------+ +---------------------+
* | _interrupt() |--->| apix_do_interrupt() |
* +--------------+ +---------------------+
* |
* hard int? +----+--------+ softint?
* | | (but no low-level looping)
* +-----------+ |
* | *setlvl() | |
* +---------+ +-----------+ +----------------------------------+
* |apix_add_| check IPL | |
* |pending_ |<-------------+------+----------------------+ |
* |hardint()| low-level int| hi-level int| |
* +---------+ v v |
* | check IPL +-----------------+ +---------------+ |
* +--+-----+ | apix_intr_ | | apix_hilevel_ | |
* | | | thread_prolog() | | intr_prolog() | |
* | return +-----------------+ +---------------+ |
* | | | On intr |
* | +------------+ | stack? +------------+ |
* | | switch_sp_ | +---------| switch_sp_ | |
* | | and_call() | | | and_call() | |
* | +------------+ | +------------+ |
* | | | | |
* | +----------------+ +----------------+ |
* | | apix_dispatch_ | | apix_dispatch_ | |
* | | lowlevel() | | hilevel() | |
* | +----------------+ +----------------+ |
* | | | |
* | v v |
* | +-------------------------+ |
* | |apix_dispatch_by_vector()|----+ |
* | +-------------------------+ | |
* | !XC_HI_PIL| | | | |
* | +---+ +-------+ +---+ | |
* | |sti| |*intr()| |cli| | |
* | +---+ +-------+ +---+ | hi-level? |
* | +---------------------------+----+ |
* | v low-level? v |
* | +----------------+ +----------------+ |
* | | apix_intr_ | | apix_hilevel_ | |
* | | thread_epilog()| | intr_epilog() | |
* | +----------------+ +----------------+ |
* | | | |
* | v-----------------+--------------------------------+ |
* | +------------+ |
* | | *setlvlx() | +----------------------------------------------------+
* | +------------+ |
* | | | +--------------------------------+ low
* v v v------+ v | level
* +------------------+ +------------------+ +-----------+ | pending?
* | apix_do_pending_ |----->| apix_do_pending_ |----->| apix_do_ |--+
* | hilevel() | | hardint() | | softint() | |
* +------------------+ +------------------+ +-----------+ return
* | | |
* | while pending | while pending | while pending
* | hi-level | low-level | softint
* | | |
* +---------------+ +-----------------+ +-----------------+
* | apix_hilevel_ | | apix_intr_ | | apix_do_ |
* | intr_prolog() | | thread_prolog() | | softint_prolog()|
* +---------------+ +-----------------+ +-----------------+
* | On intr | |
* | stack? +------------+ +------------+ +------------+
* +--------| switch_sp_ | | switch_sp_ | | switch_sp_ |
* | | and_call() | | and_call() | | and_call() |
* | +------------+ +------------+ +------------+
* | | | |
* +------------------+ +------------------+ +------------------------+
* | apix_dispatch_ | | apix_dispatch_ | | apix_dispatch_softint()|
* | pending_hilevel()| | pending_hardint()| +------------------------+
* +------------------+ +------------------+ | | | |
* | | | | | | | |
* | +----------------+ | +----------------+ | | | |
* | | apix_hilevel_ | | | apix_intr_ | | | | |
* | | intr_epilog() | | | thread_epilog()| | | | |
* | +----------------+ | +----------------+ | | | |
* | | | | | | | |
* | +------------+ | +----------+ +------+ | | |
* | | *setlvlx() | | |*setlvlx()| | | | |
* | +------------+ | +----------+ | +----------+ | +---------+
* | | +---+ |av_ | +---+ |apix_do_ |
* +---------------------------------+ |sti| |dispatch_ | |cli| |softint_ |
* | apix_dispatch_pending_autovect()| +---+ |softvect()| +---+ |epilog() |
* +---------------------------------+ +----------+ +---------+
* |!XC_HI_PIL | | | |
* +---+ +-------+ +---+ +----------+ +-------+
* |sti| |*intr()| |cli| |apix_post_| |*intr()|
* +---+ +-------+ +---+ |hardint() | +-------+
* +----------+
*/
