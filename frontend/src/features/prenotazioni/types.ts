export type StatoPrenotazione = 'confermata' | 'cancellata' | 'completata'
export type StatoPagamento = 'non_pagato' | 'pagato'
export type StatoPresenza = 'da_verificare' | 'presente' | 'non_presente'

export interface ServizioAggiuntivoDettaglio {
  id: string
  nome: string
  prezzo: string
  durata_minuti: number
}

export interface Prenotazione {
  id: string
  cliente: string
  cliente_nome: string
  operatore: string
  operatore_nome: string
  servizio: string
  servizio_nome: string
  servizi_aggiuntivi?: string[]
  servizi_aggiuntivi_dettaglio?: ServizioAggiuntivoDettaglio[]
  durata_totale_minuti?: number
  inizio: string
  fine: string
  stato: StatoPrenotazione
  stato_pagamento: StatoPagamento
  importo: string
  stato_presenza: StatoPresenza
  note: string
  creato_il: string
}

export interface PrenotazioneInput {
  operatore: string
  servizio: string
  servizi_aggiuntivi?: string[]
  inizio: string
  cliente?: string
  note?: string
}

export interface SlotDisponibile {
  inizio: string
  fine: string
  disponibile?: boolean
}

export type StatoListaAttesa = 'in_attesa' | 'notificato' | 'prenotato' | 'annullato'

export interface RichiestaListaAttesa {
  id: string
  cliente: string
  cliente_nome: string
  servizio: string
  servizio_nome: string
  operatore?: string | null
  operatore_nome?: string | null
  data: string
  ora_preferita?: string | null
  stato: StatoListaAttesa
  note?: string
  notificato_il?: string | null
  creato_il: string
}

export interface RichiestaListaAttesaInput {
  servizio: string
  operatore?: string
  data: string
  ora_preferita?: string
  note?: string
  cliente?: string
}
