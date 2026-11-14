#!/usr/bin/env python3
"""Outils d'astreinte - commandes exécutées sur la VM AlmaLinux via SSH.

L'agent et le modèle tournent sur le HOST KVM/QEMU ; ils atteignent la VM
par SSH avec le compte `almalinux`, et exécutent les commandes avec `sudo`
sans mot de passe.

    export SSH_TARGET=almalinux@192.168.122.173

Prérequis :
- clé SSH sans mot de passe host -> VM (BatchMode=yes échoue sinon) ;
- sudo NOPASSWD pour `almalinux` (sinon `sudo -n` échoue immédiatement).
"""

import os
import subprocess

SSH_TARGET = os.environ.get("SSH_TARGET", "almalinux@192.168.122.173")
SERVICE = "nginx"

def _run(cmd):
    # `sudo -n` : jamais de demande de mot de passe (échoue vite si absent)
    remote = f"sudo -n {cmd}"
    full = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", SSH_TARGET, remote]
    try:
        p = subprocess.run(full, capture_output=True, text=True, timeout=30)
        return (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except FileNotFoundError:
        return "ssh introuvable"

def check_disk():
    out = _run("df -h /")
    return f"usage du disque racine :\n{out}"

def check_service():
    out = _run(f"systemctl is-active {SERVICE}")
    return f"état du service {SERVICE} : {out or 'inconnu'}"

def read_logs():
    out = _run(f"journalctl -u {SERVICE} -n 30 --no-pager")
    return f"dernières lignes de logs de {SERVICE} :\n{out}"

def clean_temp():
    _run("rm -f /tmp/demo-filler.dat")
    out = _run("df -h /")
    return f"fichier temporaire supprimé. usage disque maintenant :\n{out}"

def restart_service():
    _run(f"systemctl restart {SERVICE}")
    out = _run(f"systemctl is-active {SERVICE}")
    return f"redémarrage de {SERVICE} effectué. état : {out or 'inconnu'}"
