export interface User {
  id: string
  email: string
  nome: string
  cognome: string
  telefono?: string
  stato: 'attivo' | 'invitato' | 'sospeso'
  ruoli: string[]
  is_staff: boolean
  date_joined: string
}

export interface UserSession {
  id: string
  dispositivo: string
  ip_address?: string | null
  user_agent?: string
  creato_il: string
  ultimo_accesso: string
  revocata: boolean
  e_corrente: boolean
}
