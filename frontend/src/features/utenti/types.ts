export interface UtenteAdmin {
  id: string
  email: string
  nome: string
  cognome: string
  stato: 'attivo' | 'invitato' | 'sospeso'
  ruoli: string[]
  date_joined: string
}

export interface UtenteAdminInput {
  email: string
  nome?: string
  cognome?: string
  stato?: UtenteAdmin['stato']
  ruoli?: string[]
  password?: string
}
