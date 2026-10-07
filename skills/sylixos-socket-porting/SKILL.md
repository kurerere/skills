---
name: sylixos-socket-porting
description: Diagnose and resolve SylixOS socket error code mismatches, non-blocking connect failures, Event full (1503) error leaks, and POSIX errno mapping issues when porting Unix/POSIX network tools to SylixOS.
---

# SylixOS Socket Porting & Errno Adaptation

This records a historical sbase/cmd_relic compatibility workaround. Before applying any mapping below, confirm the same kernel path and reproduce the same error on the current SDK and target. `1503` describes an event/semaphore condition; it does not by itself prove that a connection was refused. Do not apply these mappings globally or to unrelated errno values. Preserve the raw error and document the target-specific evidence.

Guideline for diagnosing and fixing socket errors, non-blocking `connect()` issues, and SylixOS internal kernel error leakage (`ERROR_EVENT_FULL`, `ERROR_THREAD_WAIT_TIMEOUT`) when porting POSIX network programs to SylixOS.

## Core Problem: Internal Kernel Error Leakage

### Symptoms
When a socket connection fails (e.g. port closed, host unreachable, connection timed out), utilities like `nc`, `curl`, or custom socket clients output internal SylixOS kernel errors instead of POSIX network messages:
- `connect to <ip> port <port> (tcp) failed: Event full` (instead of `Connection refused`)
- `connect to <ip> port <port> (tcp) failed: Invalid event`
- `strerror(errno)` returns non-standard kernel strings.

### Root Cause
1. **Asynchronous Polling & Semaphore Contention**:
   - SylixOS implements `poll()` / `ppoll()` via `pselect()`.
   - During socket wakeup and thread synchronization, the kernel's binary semaphore management (`SemaphoreBRelease`) invokes `_ErrorHandle(ERROR_EVENT_FULL)` (code `1503`) if the semaphore counter is already full.
   - This sets the thread's TLS `errno` to `1503`.
2. **`poll()` / `getsockopt()` Return Behavior**:
   - `poll()` returns positive on socket event (e.g. connection completed or error occurred) without clearing or resetting `errno`.
   - Non-blocking `lwip_connect` failure records the current thread `errno` into `psock->SOCK_iSoErr`. If `errno` was previously contaminated by internal semaphore/event operations, `getsockopt(..., SO_ERROR, &optval, ...)` retrieves `1503` instead of standard POSIX `ECONNREFUSED` (111).
3. **`strerror()` Lookup**:
   - SylixOS `strerror()` handles both POSIX errno (1-133) and kernel error codes (>=300). Code `1503` is translated directly to `"Event full"`.

---

## Standard Fix & Code Pattern

### 1. Sockerr Compatibility Helper (`compat.h`)

Define a helper to map SylixOS kernel-level error codes to standard POSIX networking error codes:

```c
#include <errno.h>

static inline int sylixos_fix_sockerr(int err) {
    if (err == 1503) { /* ERROR_EVENT_FULL */
        return ECONNREFUSED;
    }
    if (err == 506) {  /* ERROR_THREAD_WAIT_TIMEOUT */
        return ETIMEDOUT;
    }
    return err;
}
```

### 2. Non-blocking `connect()` Adaptation (`timeout_connect`)

Wrap `getsockopt(..., SO_ERROR, ...)` and connection error handling with `sylixos_fix_sockerr`:

```c
int timeout_connect(int s, const struct sockaddr *name, socklen_t namelen) {
    struct pollfd pfd;
    socklen_t     optlen;
    int           optval;
    int           ret;

    if ((ret = connect(s, name, namelen)) != 0 && errno == EINPROGRESS) {
        pfd.fd     = s;
        pfd.events = POLLOUT;
        if ((ret = poll(&pfd, 1, timeout)) == 1) {
            optlen = sizeof(optval);
            if ((ret = getsockopt(s, SOL_SOCKET, SO_ERROR, &optval, &optlen)) == 0) {
                optval = sylixos_fix_sockerr(optval);
                errno  = optval;
                ret    = (optval == 0) ? 0 : -1;
            }
        } else if (ret == 0) {
            errno = ETIMEDOUT;
            ret   = -1;
        } else {
            err(1, "poll failed");
        }
    }

    if (ret != 0) {
        errno = sylixos_fix_sockerr(errno);
    }

    return ret;
}
```

### 3. Unified Error Formatting (`err.h`)

Ensure all `warn()`, `err()`, and `strerror()` calls format corrected socket error messages:

```c
static inline const char *sbase_strerror(int errnum) {
    return strerror(sylixos_fix_sockerr(errnum));
}

static inline void warn(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    if (fmt != NULL) {
        vfprintf(stderr, fmt, ap);
        fprintf(stderr, ": ");
    }
    va_end(ap);
    fprintf(stderr, "%s\n", sbase_strerror(errno));
}
```

---

## Error Code Mapping Reference

| SylixOS Kernel Error | Numeric Value | Description in SylixOS | POSIX Equivalent | Expected User Message |
|:---|:---|:---|:---|:---|
| `ERROR_EVENT_FULL` | `1503` | `"Event full"` | `ECONNREFUSED` (`111`) | `"Connection refused"` |
| `ERROR_THREAD_WAIT_TIMEOUT` | `506` | `"Thread wait timeout"` | `ETIMEDOUT` (`110`) | `"Connection timed out"` |
| `ERROR_EVENT_NULL` | `1502` | `"Invalid event"` | `ECONNABORTED` (`103`) | `"Software caused connection abort"` |

---

## Verification Checklist

1. **Active Listening Port Check**:
   - `nc -zv <target_ip> <open_port>` -> reports connection succeeded / `open`.
2. **Closed Port Check**:
   - `nc -zv <target_ip> <closed_port>` -> reports `failed: Connection refused` (not `failed: Event full`).
3. **Unreachable IP / Blackhole Port Check**:
   - `nc -w 2 -zv <unreachable_ip> <port>` -> reports `failed: Connection timed out`.
