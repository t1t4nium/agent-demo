# Démo agent d'astreinte

Remédiation de niveau 1 : un agent IA local (modèle 27B) qui diagnostique
et répare tout seul un problème sur une VM Linux : disque plein + service
`nginx` en panne.

Le raisonnement et la donnée restent sur place (souveraineté) et l'agent
opère à distance via SSH comme le ferait un opérateur.

## Architecture

- Le modèle (27B) et `agent.py` tournent sur le **HOST** KVM/QEMU.
- Les outils (`df`, `systemctl`, `journalctl`, `rm`) s'exécutent sur la
  **VM AlmaLinux**, via **SSH** avec le compte `almalinux` + `sudo`.
- L'agent agit donc à distance sur la VM, comme un agent d'astreinte.

```
host (agent + modèle 27B)  --SSH (almalinux + sudo)-->  VM AlmaLinux
```

## Fichiers

- `tools.py` : les 5 outils, exécutés sur la VM via SSH + sudo.
- `agent.py` : la boucle de l'agent (parle à l'API du modèle, sur le host).
- `system_prompt.txt` : le runbook que le modèle suit.
- `setup_problem.sh` : installe le problème (via SSH + sudo).
- `reset.sh` : annule le problème (via SSH + sudo).
- `NETWORK.md` : exposer nginx de la VM sur le réseau local (192.168.1.0/24).

## Prérequis

### 1. SSH sans mot de passe (host -> VM, compte almalinux)

```bash
ssh-copy-id almalinux@192.168.122.173
ssh almalinux@192.168.122.173 "echo ok"
```

### 2. sudo sans mot de passe pour almalinux (sur la VM)

```bash
# version simple (VM de test) :
echo 'almalinux ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/almalinux-nopasswd

# version restreinte (plus sûre) :
echo 'almalinux ALL=(ALL) NOPASSWD: /usr/bin/df, /usr/bin/systemctl, /usr/bin/journalctl, /usr/bin/rm, /usr/bin/dd, /usr/bin/sync' | sudo tee /etc/sudoers.d/almalinux-nopasswd

sudo chmod 440 /etc/sudoers.d/almalinux-nopasswd
```

Vérifier (depuis le host) :

```bash
ssh almalinux@192.168.122.173 'sudo -n true' && echo "sudo sans mot de passe OK"
```

### 3. Le modèle et les outils

- Python 3 sur le host (bibliothèque standard seulement).
- Le modèle Qwen 27B servi en API compatible OpenAI sur le host ([llama.cpp](https://github.com/t1t4nium/local-llm/tree/main/RTX-3060-12G-llama.cpp)).

## Configuration

```bash
export SSH_TARGET=almalinux@192.168.122.173
export AGENT_MODEL=/etc/llama/models/qwen3.8-27b-q3.gguf
export LLM_BASE_URL=http://127.0.0.1:8080
```

## Mise en route (depuis le host)

1. Tester le modèle :
   ```bash
   curl http://127.0.0.1:8080/v1/chat/completions \
     -d '{"model":"/etc/llama/models/qwen3.8-27b-q3.gguf","messages":[{"role":"user","content":"ok"}]}'
   ```
2. Installer le problème : `bash setup_problem.sh`
3. Lancer l'agent : `python3 agent.py`
4. Remettre à zéro : `bash reset.sh`

## Exposer nginx sur le réseau local (optionnel)

Voir `NETWORK.md` (redirection de port ou réseau ponté).

## Avertissement

Lire `DISCLAIMER.md`.
