#!/usr/bin/env python3
"""
SPDX-License-Identifier: BSD-3-Clause
This file is part of pyocd_remote, https://github.com/patrislav1/pyocd_remote
Copyright (C) 2020 Patrick Huesmann <info@patrick-huesmann.de>
"""

from paramiko import SSHClient
from scp import SCPClient
from sshtunnel import SSHTunnelForwarder

import argparse
import sys
import os

PYOCD_CMD = ['python3', '-m', 'pyocd']
FILES_LIST = ['pyocd.yml', 'SAM4L.pack.zip']

def ssh_connect(ssh_user, remote_host, remote_port):
    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.connect(remote_host, port=remote_port, username=ssh_user)
    return ssh


def scp_files(ssh, opt=None):
    scp = SCPClient(ssh.get_transport())
    scp.put(FILES_LIST)
    if opt:
        scp.put(opt)
    scp.close()


def pyocd_run(ssh, args, tunnel):
    if type(args) is not list:  
        args = [args]

    _, _, stderr = ssh.exec_command(' '.join(PYOCD_CMD + args))

    # Forward remote stderr to local stderr
    while True:
        line = stderr.readline()
        if not line:
            break
        print(line, end='', file=sys.stderr)

        # Wait for pyocd to finish starting up:
        # Cortex-debug will connect as soon as the tunnel is up on localhost,
        # we have to make sure pyocd is already listening on the other side.
        if tunnel is not None and 'GDB server started' in line:
            tunnel.start()

    if tunnel is not None:
        tunnel.stop()
        tunnel.close()


def tunnel_create(ssh_user, remote_host, remote_ssh_port, tunnel_ports):
    server = SSHTunnelForwarder(
        ssh_address_or_host=(remote_host, remote_ssh_port),
        ssh_username=ssh_user,
        local_bind_addresses=[('127.0.0.1', p) for p in tunnel_ports],
        remote_bind_addresses=[('127.0.0.1', p) for p in tunnel_ports]
    )

    # Workaround for server.close() hanging
    # https://github.com/pahaz/sshtunnel/issues/138#issuecomment-678689972
    server.daemon_forward_servers = True
    server.daemon_transport = True
    return server


def pyocd_remote(ssh_user, remote_host, remote_ssh_port, pyocd_args):
    fpath = None

    # If we want to flash, scp the file to remote and forward its basename to pyocd
    if pyocd_args[0] == 'flash':
        tmp = pyocd_args[1:]

        # Find flash file name
        for i, a in enumerate(tmp):
            if a.startswith('-') or (i > 0 and tmp[i-1].startswith('-')):
                continue
            fpath = a
            break
        if not fpath:
            print(f'File for flash subcommand not found in {pyocd_args}', file=sys.stderr)
            sys.exit(-1)

        # Forward basename to pyocd
        pyocd_args[pyocd_args.index(fpath)] = os.path.basename(fpath)

    tunnel = None

    # If we want to run gdbserver, then extract port and telnet_port numbers
    # and create a tunnel to those ports
    if pyocd_args[0] == 'gdbserver':
        gdb_port, telnet_port = 3333, 4444
        for i, a in enumerate(pyocd_args):
            if a in ['-p', '--port']:
                gdb_port = int(pyocd_args[i+1])
            if a in ['-t', '--telnet-port']:
                telnet_port = int(pyocd_args[i+1])

        print(f'Creating tunnel for ports {gdb_port, telnet_port}', file=sys.stderr)
        tunnel = tunnel_create(ssh_user, remote_host, remote_ssh_port, [gdb_port, telnet_port])

    ssh = ssh_connect(ssh_user, remote_host, remote_ssh_port)
    scp_files(ssh, opt=fpath)
    pyocd_run(ssh, pyocd_args, tunnel)
    ssh.close()


def main():
    # Don't use argparse - we want to pass args transparently to pyocd
    if len(sys.argv) < 5:
        print(f'usage: {sys.argv[0]} ssh_user remote_host remote_ssh_port pyocd_args', file=sys.stderr)
        sys.exit(-1)

    pyocd_remote(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:])

if __name__ == '__main__':
    main()
