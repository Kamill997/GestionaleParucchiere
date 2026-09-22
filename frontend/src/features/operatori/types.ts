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

export interface Disponibilita {
  id: string
  operatore: string
  giorno_settimana: number
  ora_inizio: string
  ora_fine: string
}

export interface GiornoTurnoInput {
  giorno_settimana: number
  ora_inizio: string
  ora_fine: string
}

export type TipoEccezione = 'ferie' | 'malattia' | 'permesso' | 'chiusura'

export interface EccezioneDisponibilita {
  id: string
  operatore: string | null
  operatore_nome: string | null
  tipo: TipoEccezione
  data_inizio: string
  data_fine: string
  ora_inizio: string | null
  ora_fine: string | null
  motivo: string
  creato_il: string
}

export interface EccezioneDisponibilitaInput {
  operatore?: string | null
  tipo: TipoEccezione
  data_inizio: string
  data_fine: string
  ora_inizio?: string | null
  ora_fine?: string | null
  motivo?: string
}

