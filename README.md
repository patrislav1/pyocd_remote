# pyocd_remote

Remote execution wrapper for [PyOCD](https://github.com/pyocd/pyOCD).

This tool runs `pyocd` on a remote SSH server and does additional copying / tunneling, so it looks like `pyocd` is running locally.
Usage:
```
pyocd_remote user@host:port [--cmd pyocd_executable] [pyocd_args ...]
```

## Prerequisites

For this tool to work, the local SSH client needs to be authorized at the remote server using a public key, and the remote server needs to be in the list of known hosts.

## Examples

```
pyocd_remote user@host:port erase --chip
```
Erases the chip connected to the remote host.

```
pyocd_remote user@host:port flash image.bin
```
Copies `image.bin` to the remote host, then flashes it there.

```
pyocd_remote user@host:port gdbserver --port 50000
```
Starts a gdbserver on the remote host and creates a tunnel, so it looks like a local gdbserver to the debugger.
