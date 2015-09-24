
##用宏实现状态机

#define STATES                                  \
    STATE(VOID, 1 << 0)                         \
    STATE(BACKOFF, 1 << 1)                      \
    STATE(CONNECTING, 1 << 2)                   \
    STATE(ACTIVE, 1 << 3)                       \
    STATE(IDLE, 1 << 4)                         \
    STATE(DISCONNECTED, 1 << 5)

enum state {
#define STATE(NAME, VALUE) S_##NAME = VALUE,
    STATES
#undef STATE
};

static const char *
state_name(enum state state)
{
    switch (state) {
#define STATE(NAME, VALUE) case S_##NAME: return #NAME;
        STATES
#undef STATE
    }
    return "***ERROR***";
}

static unsigned int timeout_VOID(rconn *rc) {
    return 1 << 0;
}

static unsigned int timeout_BACKOFF(rconn *rc) {
    return 1 << 1;
}

static unsigned int timeout_CONNECTING(rconn *rc) {
    return 1 << 2;
}

static unsigned int timeout_ACTIEV(rconn *rc) {
    return 1 << 3;
}

static unsigned int timeout_IDLE(rconn *rc) {
    return 1 << 4;
}

static unsigned int timeout_DISCONNECTED(rconn *rc) {
    return 1 << 5;
}

static unsigned int timeout(const struct rconn *rc)
{
    switch (rc->state) {
#define STATE(NAME, VALUE) case S_##NAME: return timeout_##NAME(rc);
        STATES
#undef STATE
    default:
        0;
    }
}

stactic void run_VOID(const struct rconn *rc) {
    if (timeout(rc)) {
    } else {
        do_work()
    }
}

stactic void run_BACKOFF(const struct rconn *rc) {
    if (timeout(rc)) {
    } else {
        do_work()
    }
}

stactic void run_CONNECTING(const struct rconn *rc) {
    if (timeout(rc)) {
    } else {
        do_work()
    }
}

stactic void run_ACTIVE(const struct rconn *rc) {
    if (timeout(rc)) {
    } else {
        do_work()
    }
}

stactic void run_IDLE(const struct rconn *rc) {
    if (timeout(rc)) {
    } else {
        do_work()
    }
}

stactic void run_DISCONNECTED(const struct rconn *rc) {
    if (timeout(rc)) {
    } else {
        do_work()
    }
}

void run() {
    switch (rc->state) {
#define STATE(NAME, VALUE) case S_##NAME: run_##NAME(rc); break;
           STATES
#undef STATE
    default:
        OVS_NOT_REACHED();
    }
}


###参考

* https://gcc.gnu.org/onlinedocs/cpp/Macros.html#Macros
* Openvswitch Source Code

