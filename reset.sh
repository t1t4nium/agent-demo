#!/usr/bin/env bash
# Annule le problème installé par setup_problem.sh (via SSH vers la VM) :
# supprime le fichier de remplissage et redémarre nginx.
set -euo pipefail

SSH_TARGET="${SSH_TARGET:-almalinux@192.168.122.173}"
SERVICE="${SERVICE:-nginx}"
FILLER=/tmp/demo-filler.dat

rsh() { ssh -o BatchMode=yes -o ConnectTimeout=8 "$SSH_TARGET" "$@"; }

echo "== Remise à zéro de la VM ($SSH_TARGET) =="

echo "Suppression du fichier de remplissage..."
rsh "sudo -n rm -f $FILLER"

echo "Redémarrage de $SERVICE..."
rsh "sudo -n systemctl restart $SERVICE" || true

svc_state=$(rsh "sudo -n systemctl is-active $SERVICE 2>/dev/null" || true)
echo "État final de $SERVICE : ${svc_state:-inconnu}"
rsh "sudo -n df -h /"
echo "Terminé."
