# Bot de control de connectivitat
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
-  Canvia `BOT_TOKEN` pel teu token.
-  Posa el teu `ADMIN_ID` per seguretat.
    <img width="582" height="130" alt="image" src="https://github.com/user-attachments/assets/03c5c73e-84e0-4cee-8d50-85dedda9a17a" />


## Comandes disponibles

<img width="361" height="150" alt="image" src="https://github.com/user-attachments/assets/eda0634a-f296-41a4-8310-856555ae701c" />

- /bloquejar: Activa el protocol de restricció. Tallarà l'accés a internet de tot el sistema, permetent exclusivament el trànsit de dades per a l'aplicació Telegram.

- /desbloquejar: Desactiva qualsevol restricció activa i restaura la connexió total a internet de manera instantània.

El bot permet automatitzar els bloquejos mitjançant intervals de temps definits per l'usuari:

- /estat: Proporciona un resum detallat de la situació actual (si internet està bloquejat o no) i llista tots els intervals horaris que s'han programat fins al moment.

- /afegir_horari [Inici] [Final]: Permet registrar un nou interval de bloqueig automàtic.

Exemple d'ús: /afegir_horari 18:00 20:30 (el sistema es bloquejarà cada dia en aquesta franja).

- /treure_horari [N]: S'utilitza per eliminar un interval específic de la llista. Cal substituir la N pel número de l'índex que es mostra en consultar l'estat.

- /netejar_horaris: Acció global per esborrar tota la configuració de programació actual i deixar el calendari buit.

## Ús

Executa el bot amb:

bash
sudo ./venv/bin/python bot_nou.py

<img width="675" height="48" alt="image" src="https://github.com/user-attachments/assets/7a76a4af-d4fb-4090-8b12-2233079e089f" />
