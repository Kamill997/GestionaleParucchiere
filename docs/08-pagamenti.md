# Pagamenti e Presenze

## Perché questo approccio

Rispetto a un'integrazione di pagamento online completa, per questo progetto si è scelto un approccio più semplice: **il pagamento avviene fuori dall'app** (contanti, POS fisico, bonifico), e il gestionale si limita a **registrarne l'esito** insieme alla presenza effettiva del cliente all'appuntamento.

## Tracciamento pagamento

Ogni prenotazione ha un campo **stato pagamento** (`non_pagato` / `pagato`), impostato manualmente dall'operatore o dall'amministratore dopo l'incasso reale. L'importo si ricava dal prezzo del servizio associato alla prenotazione (con possibilità di modificarlo manualmente per sconti/eccezioni).

## Tracciamento presenza

| Stato | Significato |
|---|---|
| `da_verificare` | Stato di default finché l'appuntamento non è passato |
| `presente` | Il cliente si è presentato |
| `non_presente` | Il cliente non si è presentato (no-show) |

## Politica no-show

1. **Conteggio** — il sistema conta quante volte lo stesso indirizzo email (o numero di telefono, per chi prenota come ospite senza account) è stato marcato `non_presente`
2. **Soglia** — al raggiungimento di **2-3 no-show** (soglia configurabile in `Settings`)
3. **Azione automatica**: email di avviso + blocco delle prenotazioni future
4. **Sblocco** — manuale da parte dell'amministratore

## Dashboard guadagni (lato Amministratore)

- **Guadagni totali** per periodo, sommando il prezzo delle prenotazioni con `stato_pagamento = pagato`
- **Guadagni per cliente** — somma storica per cliente, utile per individuare i clienti di maggior valore
- **Guadagni per servizio/categoria** e **per operatore**
- **Tasso di no-show** e elenco dei clienti vicini alla soglia di blocco

## Nota per il futuro

Se in futuro si volesse offrire un pagamento online (es. una caparra), significherebbe aggiungere un provider come Stripe con Payment Intent e webhook — non necessario per la versione attuale.

## Checklist

- [ ] Campo stato pagamento sulla prenotazione, impostabile manualmente da operatore/amministratore
- [ ] Campo stato presenza sulla prenotazione, con i tre stati definiti
- [ ] Conteggio no-show per email/telefono (anche per prenotazioni senza account)
- [ ] Soglia di no-show configurabile (default 2-3)
- [ ] Email automatica di avviso al raggiungimento della soglia
- [ ] Blocco automatico di nuove prenotazioni da email/telefono bloccati
- [ ] Sblocco manuale disponibile per l'amministratore
- [ ] Dashboard guadagni basata sui dati marcati manualmente (totale, per cliente, per servizio, per operatore)
