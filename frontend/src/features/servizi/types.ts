export interface Servizio {
  id: string
  nome: string
  descrizione: string
  categoria: string
  durata_minuti: number
  prezzo: string
  foto: string | null
  attivo: boolean
}

export interface ServizioInput {
  nome: string
  descrizione?: string
  categoria: string
  durata_minuti: number
  prezzo: number | string
  foto?: File | null
  attivo?: boolean
}
