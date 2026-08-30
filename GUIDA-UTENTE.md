# Guida all'uso — Gestionale Salone

Questa guida copre le operazioni quotidiane per i tre tipi di utenti
dell'app: **Amministratore**, **Operatrice** e **Cliente**.

> Tutte le password di demo sono `demo-password-123`.
> In produzione usare password sicure.

---

## Per il Cliente

### Registrarsi

1. Aprire il sito e cliccare **"Non hai un account?"** nella pagina di login
2. Inserire email, password e nome
3. Al primo accesso si viene reindirizzati alla **Dashboard**

### Prenotare un appuntamento

1. Cliccare **"Prenota"** nella barra laterale
2. Scegliere il **servizio** dal menu (vengono mostrati durata e prezzo)
3. Scegliere l'**operatrice** preferita
4. Selezionare il **giorno** — gli slot liberi compaiono in tempo reale
5. Cliccare sull'orario desiderato, poi su **"Conferma prenotazione"**
6. Arriva una **email di conferma** automatica

### Vedere e cancellare le prenotazioni

- Cliccare **"Le mie prenotazioni"** nella barra laterale
- Per cancellare: cliccare l'icona **×** accanto alla prenotazione
  - Gratuito fino a **24 ore prima** (configurabile dall'Amministratore)
  - Oltre quel termine: contattare il salone direttamente

### Notifiche

- Il **campanello** 🔅 in alto a destra mostra le notifiche non lette
- Aprirlo e cliccare **"Attiva"** per ricevere notifiche push anche con il browser chiuso
- Le notifiche arrivano per: conferma, cancellazione da parte del salone, promemoria 24h prima

---

## Per l'Operatrice

### Accedere al calendario

- Nella **Dashboard** si vede un riepilogo KPI del giorno
- Cliccare **"Gestione prenotazioni"** per la vista completa

### Gestione presenze (dopo l'appuntamento)

Nella pagina Gestione prenotazioni, per ogni appuntamento passato:

| Icona | Azione |
|---|---|
| ✓ verde | Segna il cliente come **presente** |
| 👤× | Segna il cliente come **non presentato** (no-show) |

> Dopo 3 no-show (soglia predefinita) il cliente viene bloccato automaticamente.

### Gestione pagamenti

- Cliccare sul badge **"Da pagare"** accanto a una prenotazione per segnare il pagamento avvenuto
- Il badge diventa verde **"Pagato"**
- Solo staff può modificare lo stato di pagamento

---

## Per l'Amministratore

### Gestione del catalogo servizi

- **"Servizi"** → pulsante **"Nuovo servizio"** → inserire nome, categoria, durata e prezzo
- Per modificare o disattivare un servizio: icona matita o cestino nella riga
- Un servizio disattivato non compare più nelle prenotazioni future ma lo storico è preservato

### Gestione dello staff

- **"Operatori"** → **"Nuovo operatore"** → scegliere un account utente esistente
- Le disponibilità settimanali si configurano dall'interfaccia (lun-ven, sab...)

### Gestione clienti

- **"Clienti"** → vista di tutti i clienti registrati e ospiti
- Le **note preferenze** (colore abituale, allergie ecc.) sono visibili solo allo staff
- **Sbloccare un cliente**: dopo troppi no-show un cliente viene bloccato; cliccare il pulsante **"Sblocca"** sul suo record

### Import/Export clienti

- **"Importa"**: carica un file CSV o Excel con le colonne `nome, email, telefono, note_preferenze`
  - Scarica prima il **template** con il link "Scarica il template CSV"
  - Il sistema deduplica per email: aggiorna se già esistente, crea se nuovo
  - Il report finale mostra righe create, aggiornate ed eventuali errori
- **"Esporta"**: scarica i clienti visibili in tabella (rispetta la ricerca attiva)

### Gestione utenti e ruoli

- **"Utenti e ruoli"** → **"Nuovo utente"** → scegliere email, password e ruoli
- Ruoli disponibili: **Cliente**, **Operatore**, **Amministratore**
- Per cambiare password: modificare l'utente e inserire la nuova password (se lasciata vuota, resta quella precedente)
- Per sospendere un utente: modificarlo e impostare lo stato su **"Sospeso"**

### Dashboard KPI e guadagni

La Dashboard mostra:

| KPI | Descrizione |
|---|---|
| Prenotazioni oggi | Appuntamenti confermati nella giornata |
| Prenotazioni (7 giorni) | Vista settimanale |
| Tasso occupazione | % di slot usati oggi vs disponibili |
| Fatturato (7 giorni) | Solo prenotazioni pagate |
| Tasso no-show | % di mancate presentazioni (storico) |
| Per servizio / operatore | Guadagni dettagliati degli ultimi 7 giorni |
| Top clienti | I 10 clienti con maggior fatturato (storico) |
| Vicini al blocco | Clienti a un no-show dalla soglia |

### Impostazioni

- **"Impostazioni"** nella barra laterale (solo Amministratore)
- Cliccare il valore per modificarlo inline, **Invio** per salvare, **Esc** per annullare

| Impostazione | Default | Descrizione |
|---|---|---|
| `buffer_minuti_prenotazioni` | 10 | Minuti di pausa tra un appuntamento e il successivo |
| `intervallo_slot_minuti` | 15 | Granularità degli orari proposti al cliente |
| `ore_preavviso_cancellazione` | 24 | Ore minime per cancellare gratuitamente |
| `soglia_no_show` | 3 | Mancate presentazioni prima del blocco automatico |

---

## Installare l'app (PWA)

Il gestionale è installabile come app nativa su telefono e computer:

- **Android/Chrome**: cliccare **"Installa app"** nel menu in alto a destra
- **iPhone/Safari**: cliccare l'icona **Condividi** → **"Aggiungi a schermata Home"**
- **Desktop Chrome/Edge**: icona di installazione nella barra degli indirizzi

Una volta installata, l'app funziona anche con connessione assente (le azioni che richiedono la rete mostrano un avviso).
