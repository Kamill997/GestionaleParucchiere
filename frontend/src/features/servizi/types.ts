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

export type ServizioInput = Omit<Servizio, 'id' | 'foto'>
