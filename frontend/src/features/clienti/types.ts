export interface Cliente {
  id: string
  user: string | null
  nome: string
  email: string
  telefono: string
  note_preferenze: string
}

export type ClienteInput = Omit<Cliente, 'id' | 'user' | 'email'> & { email?: string }
