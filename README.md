# pyocd_remote

Remote execution wrapper for [PyOCD](https://github.com/pyocd/pyOCD).

This tool runs `pyocd` on a remote SSH server and does additional copying / tunneling, so it looks like `pyocd` is running locally.
Usage:
```
pyocd_remote user@host:port [pyocd_args ...]
```

* `pyocd_remote ... flash` will scp the flash file to the remote server before running pyocd there.
* `pyocd_remote ... gdbserver` will create a tunnel so it looks like a local gdbserver instance to the debugger.

For this tool to work, the local SSH client needs to be authorized at the remote server using a public key, and the remote server needs to be in the list of known hosts.
