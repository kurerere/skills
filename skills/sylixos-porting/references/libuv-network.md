# libuv 网络行为

仅用于对应 libuv 版本。与通用连接诊断配合时参阅 [socket-errors.md](socket-errors.md)。下面是历史问题线索，须重建当前因果证据。

## 非阻塞状态不一致

历史记录提到 SOCK_NONBLOCK/accept4 路径可能只修改 lwIP 状态，而 VFS O_NONBLOCK 未同步。当前应检查创建/accept 返回值、fcntl 状态、实际阻塞行为和 SDK 实现，不能假定所有版本都存在该问题。

若证实该路径失效，可评估 libuv 显式 nonblock/cloexec 设置；分别确认每个接口受支持并检查失败返回值，不把非阻塞问题扩展成无条件改写所有描述符。

事件后端选择取决于当前实现。检查 POLLIN/POLLOUT、超时、唤醒和错误语义；不默认认定 poll 一定经 pselect 实现，也不靠伪造就绪或缩短轮询间隔掩盖故障。

验证 TCP、UDP 及实际受影响的描述符，覆盖读写、accept、关闭、超时、错误路径和空闲 CPU 行为。

## 连接就绪但 SO_ERROR 仍为 EINPROGRESS

记录 connect、就绪事件、SO_ERROR 与套接字状态的时间顺序。旧适配曾用 getpeername 辅助确认连接，但不能把一次查询成功直接当成任何 SDK 上的完整连接证明。

只有当前源码与目标证据支持该完成语义时才采用相应适配。保留其他错误；覆盖连接成功、拒绝、重置、超时、取消和查询失败，确认失败不会被当作成功。
