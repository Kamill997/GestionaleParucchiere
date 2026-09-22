import { useQuery } from '@tanstack/react-query'

import { useCurrentUser } from '@/features/auth/hooks'
import { apiFetch } from '@/lib/api'

export interface KPIDashboard {
  prenotazioni_oggi: number
  prenotazioni_settimana: number
  servizio_piu_richiesto: { nome: string; conteggio: number } | null
  tasso_occupazione_oggi: number
  fatturato_settimana: string
  tasso_no_show: number
}

const RUOLI_STAFF = ['Amministratore', 'Operatore']

export function useKPIDashboard() {
  const { data: user } = useCurrentUser()
  const eStaff = !!user && user.ruoli.some((r) => RUOLI_STAFF.includes(r))

  return useQuery({
    queryKey: ['dashboard', 'kpi'],
    queryFn: () => apiFetch<KPIDashboard>('/dashboard/kpi/'),
    enabled: eStaff,
  })
}

export interface GuadagnoRiga {
  nome: string
  totale: string
}

export interface ClienteVicinoBlocco {
  nome: string
  contatore_no_show: number
  soglia: number
}

export interface ReportGuadagni {
  per_servizio: GuadagnoRiga[]
  per_operatore: GuadagnoRiga[]
  top_clienti: GuadagnoRiga[]
  clienti_vicini_al_blocco: ClienteVicinoBlocco[]
}

/**
 * docs/08-pagamenti.md, "Dashboard guadagni (lato Amministratore)": a
 * differenza di useKPIDashboard (Amministratore+Operatore), qui solo
 * Amministratore - il backend rifiuterebbe comunque un Operatore (403),
 * ma niente fetch inutile se sappiamo gia' che non e' abilitato.
 */
export function useReportGuadagni() {
  const { data: user } = useCurrentUser()
  const eAmministratore = !!user && user.ruoli.includes('Amministratore')

  return useQuery({
    queryKey: ['dashboard', 'report-guadagni'],
    queryFn: () => apiFetch<ReportGuadagni>('/dashboard/report-guadagni/'),
    enabled: eAmministratore,
  })
}

export interface AndamentoGiorno {
  data: string
  etichetta: string
  totale: number
  appuntamenti: number
}

export interface CategoriaFatturato {
  categoria: string
  totale: number
  appuntamenti: number
  percentuale: number
}

export interface OperatoreFatturato {
  operatore: string
  totale: number
  appuntamenti: number
}

export interface AndamentoProfitti {
  totale_periodo: number
  media_giornaliera: number
  giorni: AndamentoGiorno[]
  categorie: CategoriaFatturato[]
  operatori: OperatoreFatturato[]
}

export function useAndamentoProfitti(giorni: number = 30) {
  const { data: user } = useCurrentUser()
  const eAmministratore = !!user && user.ruoli.includes('Amministratore')

  return useQuery({
    queryKey: ['dashboard', 'andamento-profitti', giorni],
    queryFn: () => apiFetch<AndamentoProfitti>(`/dashboard/andamento-profitti/?giorni=${giorni}`),
    enabled: eAmministratore,
  })
}
