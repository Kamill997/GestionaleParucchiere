export type TipoNotifica =
  | 'conferma_prenotazione'
  | 'cancellazione_prenotazione'
  | 'nuova_prenotazione_ricevuta'
  | 'promemoria_prenotazione'
  | 'soglia_no_show_raggiunta'
  | 'cliente_bloccato'
  | 'cliente_sbloccato'

export interface Notifica {
  id: string
  tipo: TipoNotifica
  titolo: string
  messaggio: string
  link: string
  letta: boolean
  creato_il: string
}
