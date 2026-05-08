# Bot per desconnectar l'ordinador i altres dispositius

Aquest és un bot de Telegram programat en Python que permet controlar la xarxa local des d'un dispositiu mòbil. 

## Funcionalitats principals

1.  **Control del propi ordenador**: Bloqueja l'accés a internet de l'ordinador on corre el bot, però manté la connexió amb els servidors de Telegram perquè el bot continuï funcionant.
2.  **Control de tercers (ARP Spoofing)**: Permet "kickejar" (tallar la connexió) a altres dispositius de la mateixa xarxa local enviant paquets ARP falsos.

## Requisits previs

1.  Necessites tenir **Python 3** instal·lat.
2.  Un token de bot de Telegram (@BotFather).
3.  Executar el bot amb permisos d'administrador (**sudo**) per poder manipular `iptables` i enviar paquets de xarxa a baix nivell.
4.  Llibreries necessàries: `pyTelegramBotAPI`, `scapy`.

## Instal·lació

1.  Instal·la les dependències:
    ```bash
    pip install -r requirements.txt
    ```
2.  Configura el `bot.py`:
    - Canvia `BOT_TOKEN` pel teu token.
    - Posa el teu `ADMIN_ID` per seguretat.
    <img width="582" height="130" alt="image" src="https://github.com/user-attachments/assets/03c5c73e-84e0-4cee-8d50-85dedda9a17a" />


## Comandes disponibles

<img width="361" height="150" alt="image" src="https://github.com/user-attachments/assets/eda0634a-f296-41a4-8310-856555ae701c" />

- /bloquejar — Bloqueja internet (excepte Telegram).

- /desbloquejar — Restaura internet.

- /estat — Mostra estat i horaris.

- /afegir_horari HH:MM HH:MM — Afegeix un interval de temps (per exemple: /afegir_horari 18:00 20:30).

- /treure_horari N — Elimina l'horari número N de la llista.

- /netejar_horaris — Elimina tots els horaris guardats.

## Ús

Executa el bot amb:

```bash
sudo python3 bot.py
```
