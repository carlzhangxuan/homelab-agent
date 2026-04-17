import os
import paramiko


def ssh_run(ip: str, user: str, key_path: str, cmd: str, stdin_data: str = "") -> str:
    key_path = os.path.expanduser(key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, key_filename=key_path, timeout=30)
    stdin, stdout, _ = client.exec_command(cmd)
    if stdin_data:
        stdin.write(stdin_data)
        stdin.channel.shutdown_write()
    out = stdout.read().decode()
    client.close()
    return out
