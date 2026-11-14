# Exposer NGINX de la VM sur le réseau local (192.168.1.0/24)

## Contexte

- VM AlmaLinux : `192.168.122.173`, sur le réseau NAT par défaut de libvirt
  (`virbr0`, `192.168.122.0/24`), joignable seulement depuis l'hôte.
- Hôte KVM : une interface (`eno1`, `192.168.1.32`) sur le LAN `192.168.1.0/24`.
- But : que les machines du LAN joignent le serveur nginx (port 80) de la VM.

## Vérifier d'abord dans la VM

1. nginx écoute sur toutes les interfaces :
   ```bash
   ssh almalinux@192.168.122.173 'sudo -n ss -tlnp | grep :80'
   ```
   Attendu : `0.0.0.0:80` ou `*:80`.

2. Tester en local sur la VM :
   ```bash
   ssh almalinux@192.168.122.173 'curl -s -o /dev/null -w "%{http_code}\n" http://localhost/'
   ```
   Attendu : `200`.

## Redirection de port sur l'hôte

On redirige un port de l'hôte (ex: 8081) vers la VM :80. L'IP de la VM ne
change pas, `SSH_TARGET` reste valable.

### Activer le forwarding IP

```bash
sudo sysctl -w net.ipv4.ip_forward=1 # libvirt l'active déjà normalement
sysctl net.ipv4.ip_forward
```

### Ajouter les règles iptables

```bash
sudo iptables -t nat -I PREROUTING -p tcp -d 192.168.1.32 --dport 8081 -j DNAT --to-destination 192.168.122.173:80
sudo iptables -I FORWARD -p tcp -d 192.168.122.173 --dport 80 -j ACCEPT
sudo iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
```

Ces règles sont perdues au redémarrage.
