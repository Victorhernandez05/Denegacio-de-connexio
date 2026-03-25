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

## Comandes disponibles

-   `/start` o `/help`: Mostra el menú d'ajuda.
-   `/desconnectar`: Bloqueja internet a l'ordinador local (excepte Telegram).
-   `/connectar`: Restaura internet a l'ordinador local.
-   `/dispositius`: Escaneja la xarxa local i mostra els dispositius connectats.
-   `/kick <IP>`: Talla la connexió del dispositiu amb la IP especificada.
-   `/unkick <IP>`: Restaura la connexió del dispositiu anteriorment kickejat.
-   `/kickejats`: Mostra la llista de dispositius que estan sent bloquejats actualment.

## Ús

Executa el bot amb:

```bash
sudo python3 bot.py
```
