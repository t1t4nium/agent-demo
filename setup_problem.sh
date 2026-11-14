#!/usr/bin/env bash
# Provoque un problème contrôlé et réversible sur la VM AlmaLinux (via SSH) :
# 1. remplit le disque racine jusqu'à ~88% (fichier /tmp/demo-filler.dat)
# 2. arrête le service nginx
# Tout est annulable avec reset.sh
# S'exécute depuis le HOST. Compte SSH : almalinux + sudo sans mot de passe.
set -euo pipefail

SSH_TARGET="${SSH_TARGET:-almalinux@192.168.122.173}"
SERVICE="${SERVICE:-nginx}"
FILLER=/tmp/demo-filler.dat
TARGET_PCT=88

rsh() { ssh -o BatchMode=yes -o ConnectTimeout=8 "$SSH_TARGET" "$@"; }

echo "== Installation du problème sur la VM ($SSH_TARGET) =="

# 1. lecture de l'usage disque de la VM
df_out=$(rsh "sudo -n df -P /")
used_pct=$(echo "$df_out" | awk 'NR==2 {gsub("%","",$5); print $5}')
avail_kb=$(echo "$df_out" | awk 'NR==2 {print $4}')
total_kb=$(echo "$df_out" | awk 'NR==2 {print $2}')

echo "Usage actuel : ${used_pct}% (disponible : $((avail_kb/1024)) Mo)"

want_used_kb=$(( total_kb * TARGET_PCT / 100 ))
cur_used_kb=$(( total_kb - avail_kb ))
add_kb=$(( want_used_kb - cur_used_kb ))

if (( add_kb > 0 )); then
  add_mb=$(( add_kb / 1024 ))
  echo "Ajout de ${add_mb} Mo pour atteindre ~${TARGET_PCT}%"
  rsh "sudo -n dd if=/dev/zero of=$FILLER bs=1M count=$add_mb status=none; sync"
else
  echo "Déjà à ${TARGET_PCT}% ou plus, rien à ajouter."
fi

echo "Usage après remplissage :"
rsh "sudo -n df -h /"

# 2. arrêt du service
echo "Arrêt de $SERVICE"
rsh "sudo -n systemctl stop $SERVICE" || true
svc_state=$(rsh "sudo -n systemctl is-active $SERVICE 2>/dev/null" || true)
echo "État : ${svc_state:-inconnu}"

echo
echo "Problème installé. Lance : python3 agent.py"
