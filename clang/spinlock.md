

基本原理就是等待锁的线程如果在给定的时间内没有获取到锁, 那么它就会主动的放弃 CPU , 给其他等待CPU的线程一个运行的机会.

``` c lang
int spinlock_internal(pthread_spinlock_t *lock) {

    int ret = 0;
    __asm__ ("n"
            “1:tlock; decl %0nt”
            “jne 2fnt”
            “movl $0, %1nt”
            “jmp 4fnt”
            “n”
            “.subsection 2nt”
            “.align 16nt”
            “2:tmovl $5, %%ecxnt”
            “3:trep; nopnt”
            “cmpl $0, %0nt”
            “jg 1bnt”
            “decl %%ecxnt”
            “jnz 3bnt”
            “jmp 5fnt”
            “.previousnt”
            “5:tmovl $1, %1nt”
            “4:tnop”
            : “=m” (*lock), “=r”(ret) : “m” (*lock) : “%ecx”);
    return ret;

}

int nongreedy_spinlock(pthread_spinlock_t *lock) {

    int rc = 0;

    rc = spinlock_internal(lock);
    while (rc) {
        sched_yield();
        rc = spinlock_internal(lock);
    }
    return 0;
}
```
