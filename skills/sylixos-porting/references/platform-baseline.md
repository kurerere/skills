# Platform baseline & API compatibility

Guide for selecting a porting baseline and resolving platform-level API differences between SylixOS and FreeBSD/Linux/POSIX/RTOS.

## 1. Porting baseline selection

When porting third-party C/C++ libraries or runtime components to SylixOS, select the upstream baseline in the following priority order:

| Upstream feature | Recommended baseline | Rationale & porting focus |
| :--- | :--- | :--- |
| **FreeBSD support** | **FreeBSD** (Preferred) | SylixOS shares BSD heritage in its network stack and design philosophy; POSIX/BSD API semantics align most closely, minimizing delta. |
| **RTOS support** | **RTOS** (FreeRTOS / VxWorks) | Embedded resource constraints, task lifecycle models, and HAL abstractions map cleanly to SylixOS. |
| **POSIX compliance only** | **POSIX baseline** | SylixOS provides comprehensive POSIX PSE52/PSE53 conformance; standard POSIX code compiles directly with minimal shim. |
| **Linux only** | **Linux** | Direct port from Linux. Must adapt Linux-specific mechanisms: `epoll`, `hugetlbfs`, `pagemap`, UIO/VFIO, scheduler constants, and `optarg`. |

---

## 2. SylixOS vs FreeBSD API diffs

| Feature / Domain | FreeBSD | SylixOS adaptation | Implementation guide |
| :--- | :--- | :--- | :--- |
| **Event notification** | `kqueue` / `kevent` | `select` / `poll` | SylixOS does not support `kqueue`. Migrate event loop to POSIX `poll`/`select`, or use an abstraction layer like `libuv`/`libevent`. |
| **CPU set type** | `cpuset_t` | `cpu_set_t` | Typedef alias or rename: `typedef cpu_set_t cpuset_t;`. |
| **Thread ID** | `thr_self()` | `pthread_self()` | Replace with standard POSIX `pthread_self()`. |
| **Thread naming** | `pthread_set_name_np()` | `pthread_setname_np()` | API signature difference: SylixOS follows glibc/POSIX `pthread_setname_np(thread, name)`. |
| **CPU count** | `sysctl(HW_NCPU)` | `sysconf(_SC_NPROCESSORS_ONLN)` | Query online CPUs via POSIX standard `sysconf(_SC_NPROCESSORS_ONLN)`. |
| **System config** | `sysctlbyname()` | `sysconf()` / build constants | SylixOS lacks BSD `sysctlbyname`. Use `sysconf()` for runtime parameters or static headers for build options. |
| **Contiguous memory** | `contigmem` driver | `mmap(MAP_ANONYMOUS)` / DMA kernel API | Use anonymous `mmap` for user space allocations; invoke SylixOS kernel DMA allocators for hardware-contiguous buffers. |
| **I/O privileges** | `/dev/io` | MMIO mapping | Non-x86 architectures (e.g. ARM64) use memory-mapped I/O (MMIO); direct port I/O nodes do not exist. |
| **File locking** | `flock()` | `fcntl(fd, F_SETLK, ...)` | Replace BSD `flock` with POSIX `fcntl` record locking. |
| **Core dump control** | `MADV_NOCORE` | No-op macro | SylixOS does not support `MADV_NOCORE`. Define as 0 / no-op: `#define MADV_NOCORE 0`. |

---

## 3. SylixOS vs Linux API diffs

| Feature / Domain | Linux | SylixOS adaptation | Implementation guide |
| :--- | :--- | :--- | :--- |
| **Event notification** | `epoll` (`epoll_create`/`ctl`/`wait`) | `select` / `poll` | SylixOS does not implement native `epoll`. Switch to `poll`/`select` or compile with `epoll-shim`. |
| **Huge pages** | `hugetlbfs` / `MAP_HUGETLB` | `mmap(MAP_ANONYMOUS)` | SylixOS memory model does not expose `MAP_HUGETLB`. Fall back to standard anonymous mmap. |
| **Physical address query** | `/proc/self/pagemap` | Dedicated kernel driver | SylixOS procfs lacks `pagemap`. Virtual-to-physical address translation requires kernel driver support. |
| **User space I/O** | `/dev/uioN` (UIO) | SylixOS character driver | SylixOS does not support Linux UIO framework. Implement a SylixOS native driver instead. |
| **Device passthrough** | `/dev/vfio` (VFIO) | Kernel driver / DMA mapping | SylixOS does not implement VFIO. Manage IOMMU/device access inside kernel drivers. |
| **Thread naming** | `pthread_setname_np()` | `pthread_setname_np()` | Same signature, but enforce SylixOS task name length limit (typically <= 31 characters). |
| **Core dump exclusion** | `MADV_DONTDUMP` | No-op macro | SylixOS ignores memory dump exclusion flags. Define `#define MADV_DONTDUMP 0`. |
| **Command-line `optarg`** | `extern char *optarg;` | Thread-local macro | In SylixOS `<unistd.h>`, `optarg` expands to a thread-local getter macro. An explicit `extern char *optarg;` in user code produces a syntax or symbol conflict; remove the declaration or include `<unistd.h>` directly. |
| **Scheduling policy** | `SCHED_OTHER` distinct value | `SCHED_OTHER == SCHED_RR` | In SylixOS, `#define SCHED_OTHER SCHED_RR`. Switch-case blocks handling both `case SCHED_OTHER:` and `case SCHED_RR:` fail with duplicate case errors; guard with `#if SCHED_OTHER != SCHED_RR`. |

---

## 4. Adaptation patterns

### 4.1 Guarding `optarg` declarations
```c
#if defined(__SYLIXOS__)
# include <unistd.h>
#else
extern char *optarg;
extern int optind, opterr, optopt;
#endif
```

### 4.2 Handling `SCHED_OTHER` duplicate cases
```c
switch (policy) {
case SCHED_FIFO:
    /* Handle FIFO */
    break;
case SCHED_RR:
    /* Handle RR */
    break;
#if defined(SCHED_OTHER) && (SCHED_OTHER != SCHED_RR)
case SCHED_OTHER:
    /* Linux distinct OTHER */
    break;
#endif
default:
    break;
}
```

### 4.3 Fallbacks for `madvise` flags
```c
#ifndef MADV_DONTDUMP
# define MADV_DONTDUMP 0
#endif
#ifndef MADV_NOCORE
# define MADV_NOCORE 0
#endif
```

### 4.4 BSD `flock()` shim via POSIX `fcntl`
```c
#if defined(__SYLIXOS__)
#include <fcntl.h>
static inline int sylixos_flock(int fd, int operation) {
    struct flock fl;
    fl.fl_whence = SEEK_SET;
    fl.fl_start = 0;
    fl.fl_len = 0;
    if (operation & LOCK_EX) fl.fl_type = F_WRLCK;
    else if (operation & LOCK_SH) fl.fl_type = F_RDLCK;
    else if (operation & LOCK_UN) fl.fl_type = F_UNLCK;
    else return -1;
    return fcntl(fd, (operation & LOCK_NB) ? F_SETLK : F_SETLKW, &fl);
}
#define flock(fd, op) sylixos_flock(fd, op)
#endif
```
