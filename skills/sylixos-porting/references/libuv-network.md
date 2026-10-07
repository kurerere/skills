# libuv network recipes

## Synchronize socket and VFS nonblocking state

**Signature:** sockets created with `SOCK_NONBLOCK` or `accept4(...,
SOCK_NONBLOCK)` still block because SylixOS updates lwIP `FIONBIO` but not the
VFS descriptor's `O_NONBLOCK` flag.

**Recipe:** On SylixOS, bypass the socket/accept nonblocking fast paths and call
libuv's explicit `uv__nonblock()` and `uv__cloexec()` setup so `fcntl(F_SETFL,
O_NONBLOCK)` updates the descriptor state observed by libuv.

Keep native `posix-poll`: the SylixOS implementation is backed by `pselect()`
and understands its composite `POLLIN` mask. Artificial `POLLOUT`, truncated
timeouts, or a periodic wakeup loop change semantics and add CPU churn.

**Validation:** Exercise TCP, UDP, pipe, and file event flow; require idle loops
without a 20 ms wakeup cadence and blocked operations to return control to the
event loop.

## Confirm an in-progress connection without hiding real errors

**Signature:** an asynchronously connected lwIP socket is reported failed
because `SO_ERROR` transiently remains `EINPROGRESS` after readiness.

**Recipe:** Only for `SO_ERROR == EINPROGRESS`, call `getpeername()` and accept
the connection when that confirms a peer. Return every other socket error
unchanged.

**Validation:** Successful connections complete, while closed-port cases still
surface `ECONNREFUSED` or `ECONNRESET`.
