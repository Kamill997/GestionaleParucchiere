export interface User {
  id: string
  email: string
  nome: string
  cognome: string
  stato: 'attivo' | 'invitato' | 'sospeso'
  ruoli: string[]
  is_staff: boolean
  date_joined: string
}
