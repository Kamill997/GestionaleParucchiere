export type StatoPrenotazione = 'confermata' | 'cancellata' | 'completata'
export type StatoPagamento = 'non_pagato' | 'pagato'
export type StatoPresenza = 'da_verificare' | 'presente' | 'non_presente'

export interface Prenotazione {
  id: string
  cliente: string
  cliente_nome: string
  operatore: string
  operatore_nome: string
  servizio: string
  servizio_nome: string
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
  inizio: string
  cliente?: string
  note?: string
}

export interface SlotDisponibile {
  inizio: string
  fine: string
}
