export interface Operatore {
  id: string
  email: string
  nome: string
  specializzazioni: string
  foto: string | null
  attivo: boolean
}

export interface OperatoreInput {
  user: string
  nome: string
  specializzazioni?: string
  attivo?: boolean
}
