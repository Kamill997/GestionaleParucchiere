import { useMemo, useState } from 'react'
import {
  CalendarOff,
  ChevronLeft,
  ChevronRight,
  Palmtree,
  User as UserIcon,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { useCurrentUser } from '@/features/auth/hooks'
import { useEccezioni, useOperatori } from '@/features/operatori/hooks'
import type { Operatore } from '@/features/operatori/types'

import { DettaglioPrenotazioneDialog } from './DettaglioPrenotazioneDialog'
import { usePrenotazioniCalendario } from './hooks'
import type { Prenotazione } from './types'

const ORE_GIORNATA = [
  '08:00',
  '09:00',
  '10:00',
  '11:00',
  '12:00',
  '13:00',
  '14:00',
  '15:00',
  '16:00',
  '17:00',
  '18:00',
  '19:00',
]

const GIORNI_SETTIMANA = [
  'Lunedì',
  'Martedì',
  'Mercoledì',
  'Giovedì',
  'Venerdì',
  'Sabato',
  'Domenica',
]

function toYMD(d: Date): string {
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getStartOfWeek(d: Date): Date {
  const date = new Date(d)
  const day = date.getDay()
  const diff = date.getDate() - day + (day === 0 ? -6 : 1) // Lunedi come inizio
  date.setDate(diff)
  date.setHours(0, 0, 0, 0)
  return date
}

function addDays(d: Date, days: number): Date {
  const res = new Date(d)
  res.setDate(res.getDate() + days)
  return res
}

export function CalendarioOperatori() {
  const { data: user } = useCurrentUser()
  const isAmministratore = !!user && user.ruoli.includes('Amministratore')

  const [modalita, setModalita] = useState<'giorno' | 'settimana'>('giorno')
  const [dataRiferimento, setDataRiferimento] = useState<Date>(() => new Date())
  const [operatoreSelezionato, setOperatoreSelezionato] = useState<string>('tutti')
  const [filtroLegenda, setFiltroLegenda] = useState<string | null>(null)
  const [prenotazioneDettaglio, setPrenotazioneDettaglio] = useState<Prenotazione | null>(null)

  const { data: operatoriData } = useOperatori(1, true)
  const operatori = useMemo(() => operatoriData?.results ?? [], [operatoriData])

  // Calcolo intervallo date per la query API
  const { dataDa, dataA, giorniSettimanaList } = useMemo(() => {
    if (modalita === 'giorno') {
      const ymd = toYMD(dataRiferimento)
      return { dataDa: ymd, dataA: ymd, giorniSettimanaList: [dataRiferimento] }
    } else {
      const lunedi = getStartOfWeek(dataRiferimento)
      const domenica = addDays(lunedi, 6)
      const lista: Date[] = []
      for (let i = 0; i < 7; i++) {
        lista.push(addDays(lunedi, i))
      }
      return {
        dataDa: toYMD(lunedi),
        dataA: toYMD(domenica),
        giorniSettimanaList: lista,
      }
    }
  }, [modalita, dataRiferimento])

  const { data: prenotazioniData, isLoading } = usePrenotazioniCalendario(
    dataDa,
    dataA,
    operatoreSelezionato === 'tutti' ? undefined : operatoreSelezionato,
  )

  const prenotazioni = useMemo(() => prenotazioniData?.results ?? [], [prenotazioniData])

  const { data: eccezioniData } = useEccezioni({ data_da: dataDa, data_a: dataA })
  const eccezioni = useMemo(() => eccezioniData?.results ?? [], [eccezioniData])

  // Navigazione date
  const handlePrecedente = () => {
    setDataRiferimento((prev) => addDays(prev, modalita === 'giorno' ? -1 : -7))
  }

  const handleSuccessivo = () => {
    setDataRiferimento((prev) => addDays(prev, modalita === 'giorno' ? 1 : 7))
  }

  const handleOggi = () => {
    setDataRiferimento(new Date())
  }

  // Operatori da mostrare nelle colonne (in vista Giorno)
  const operatoriVisualizzati: Operatore[] = useMemo(() => {
    if (operatoreSelezionato !== 'tutti') {
      return operatori.filter((op) => op.id === operatoreSelezionato)
    }
    return operatori
  }, [operatori, operatoreSelezionato])

  // Chiusura totale salone per la giornata selezionata (in vista giorno)
  const chiusuraSaloneOggi = useMemo(() => {
    const ymd = toYMD(dataRiferimento)
    return eccezioni.find(
      (ecc) =>
        ecc.operatore === null &&
        ymd >= ecc.data_inizio &&
        ymd <= ecc.data_fine &&
        !ecc.ora_inizio &&
        !ecc.ora_fine,
    )
  }, [eccezioni, dataRiferimento])

  // Helper per verificare se l'intero salone è chiuso in una data
  const getChiusuraSaloneData = (dataYmd: string) => {
    return eccezioni.find(
      (ecc) =>
        ecc.operatore === null &&
        dataYmd >= ecc.data_inizio &&
        dataYmd <= ecc.data_fine &&
        !ecc.ora_inizio &&
        !ecc.ora_fine,
    )
  }

  // Helper per verificare se un operatore è assente per l'intera giornata
  const getAssenzaInteraGiornataOperatore = (dataYmd: string, operatoreId: string) => {
    return eccezioni.find(
      (ecc) =>
        ecc.operatore === operatoreId &&
        dataYmd >= ecc.data_inizio &&
        dataYmd <= ecc.data_fine &&
        !ecc.ora_inizio &&
        !ecc.ora_fine,
    )
  }

  // Helper per verificare se uno slot orario coincide con un'eccezione (ferie, chiusura, permesso)
  const getEccezioneSlot = (dataYmd: string, oraStr: string, operatoreId?: string) => {
    const oraNum = parseInt(oraStr.split(':')[0], 10)
    return eccezioni.find((ecc) => {
      // 1. Verifica data
      if (dataYmd < ecc.data_inizio || dataYmd > ecc.data_fine) return false

      // 2. Verifica associazione operatore (null = salone intero)
      if (ecc.operatore !== null && operatoreId && ecc.operatore !== operatoreId) return false
      if (!operatoreId && ecc.operatore !== null) return false

      // 3. Verifica orario se specificato
      if (ecc.ora_inizio && ecc.ora_fine) {
        const hInizio = parseInt(ecc.ora_inizio.split(':')[0], 10)
        const hFine = parseInt(ecc.ora_fine.split(':')[0], 10)

        if (ecc.data_inizio === ecc.data_fine) {
          if (oraNum < hInizio || oraNum >= hFine) return false
        } else {
          if (dataYmd === ecc.data_inizio && oraNum < hInizio) return false
          if (dataYmd === ecc.data_fine && oraNum >= hFine) return false
        }
      }
      return true
    })
  }

  // Formattazione titolo data
  const titoloData = useMemo(() => {
    if (modalita === 'giorno') {
      return dataRiferimento.toLocaleDateString('it-IT', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      })
    }
    const lunedi = giorniSettimanaList[0]
    const domenica = giorniSettimanaList[6]
    return `Settimana ${lunedi.getDate()} ${lunedi.toLocaleDateString('it-IT', { month: 'short' })} – ${domenica.getDate()} ${domenica.toLocaleDateString('it-IT', { month: 'short', year: 'numeric' })}`
  }, [modalita, dataRiferimento, giorniSettimanaList])

  const matchFiltroLegenda = (p: Prenotazione) => {
    if (!filtroLegenda) return true
    if (filtroLegenda === 'confermata')
      return p.stato === 'confermata' && p.stato_pagamento === 'pagato' && p.stato_presenza !== 'presente'
    if (filtroLegenda === 'da_pagare')
      return p.stato_pagamento === 'non_pagato' && p.stato !== 'cancellata'
    if (filtroLegenda === 'presente')
      return p.stato_presenza === 'presente'
    if (filtroLegenda === 'completata')
      return p.stato === 'completata'
    if (filtroLegenda === 'cancellata')
      return p.stato === 'cancellata'
    return true
  }

  // Helper per ottenere le prenotazioni che cadono in una certa ora e giorno/operatore
  const getPrenotazioniSlot = (dataYmd: string, oraStr: string, operatoreId?: string) => {
    const oraNum = parseInt(oraStr.split(':')[0], 10)
    return prenotazioni.filter((p) => {
      const pInizio = new Date(p.inizio)
      const pYmd = toYMD(pInizio)
      const pOra = pInizio.getHours()
      const matchaGiorno = pYmd === dataYmd
      const matchaOra = pOra === oraNum
      const matchaOperatore = !operatoreId || p.operatore === operatoreId
      return matchaGiorno && matchaOra && matchaOperatore && matchFiltroLegenda(p)
    })
  }

  // Stile del blocco in base allo stato
  const getVarianteBlocco = (p: Prenotazione) => {
    if (p.stato === 'cancellata') {
      return 'bg-danger-surface border-danger text-danger'
    }
    if (p.stato === 'completata') {
      return 'bg-surface-hover border-border text-ink-muted'
    }
    if (p.stato_pagamento === 'non_pagato') {
      return 'bg-warning-surface/80 border-warning text-ink'
    }
    if (p.stato_presenza === 'presente') {
      return 'bg-primary/10 border-primary text-ink'
    }
    return 'bg-success-surface border-success text-ink'
  }

  return (
    <div className="space-y-4">
      {/* Barra di Controllo Calendario */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-surface border border-border p-4 rounded-lg shadow-sm">
        {/* Navigazione temporale */}
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={handleOggi}>
            Oggi
          </Button>
          <div className="flex items-center rounded-md border border-border bg-bg">
            <button
              type="button"
              onClick={handlePrecedente}
              className="p-1.5 hover:bg-surface text-ink-muted hover:text-ink transition-colors"
              aria-label="Precedente"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={handleSuccessivo}
              className="p-1.5 hover:bg-surface text-ink-muted hover:text-ink transition-colors"
              aria-label="Successivo"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
          <h2 className="font-display font-semibold text-ink text-base sm:text-lg capitalize ml-2">
            {titoloData}
          </h2>
        </div>

        {/* Filtri e Modalità */}
        <div className="flex items-center gap-3">
          {/* Selettore Operatore (per Admin) */}
          {isAmministratore && (
            <div className="w-48">
              <Select
                value={operatoreSelezionato}
                onChange={(e) => setOperatoreSelezionato(e.target.value)}
              >
                <option value="tutti">Tutte le operatrici</option>
                {operatori.map((op) => (
                  <option key={op.id} value={op.id}>
                    {op.nome}
                  </option>
                ))}
              </Select>
            </div>
          )}

          {/* Toggle Vista Giorno / Settimana */}
          <div className="flex rounded-md border border-border bg-surface-hover/50 p-0.5">
            <button
              type="button"
              onClick={() => setModalita('giorno')}
              className={`px-3 py-1 text-xs font-medium rounded transition-all ${
                modalita === 'giorno'
                  ? 'bg-surface text-primary shadow-xs font-semibold'
                  : 'text-ink-muted hover:text-ink'
              }`}
            >
              Giorno
            </button>
            <button
              type="button"
              onClick={() => setModalita('settimana')}
              className={`px-3 py-1 text-xs font-medium rounded transition-all ${
                modalita === 'settimana'
                  ? 'bg-surface text-primary shadow-xs font-semibold'
                  : 'text-ink-muted hover:text-ink'
              }`}
            >
              Settimana
            </button>
          </div>
        </div>
      </div>

      {/* Legenda Colori Interattiva (Filtro rapido su clic) */}
      <div className="flex flex-wrap items-center gap-2 px-1 text-xs text-ink-muted">
        <span className="font-semibold text-ink mr-1">Legenda / Filtra per stato:</span>
        <button
          type="button"
          onClick={() => setFiltroLegenda(filtroLegenda === 'confermata' ? null : 'confermata')}
          className={`flex items-center gap-1.5 px-2 py-1 rounded transition-all cursor-pointer ${
            filtroLegenda === 'confermata'
              ? 'bg-success-surface font-semibold ring-2 ring-success text-ink'
              : 'hover:bg-surface border border-transparent'
          }`}
          title="Filtra solo prenotazioni confermate"
        >
          <span className="w-3 h-3 rounded-xs bg-success-surface border border-success" />
          <span>Confermata</span>
        </button>

        <button
          type="button"
          onClick={() => setFiltroLegenda(filtroLegenda === 'da_pagare' ? null : 'da_pagare')}
          className={`flex items-center gap-1.5 px-2 py-1 rounded transition-all cursor-pointer ${
            filtroLegenda === 'da_pagare'
              ? 'bg-warning-surface font-semibold ring-2 ring-warning text-ink'
              : 'hover:bg-surface border border-transparent'
          }`}
          title="Filtra prenotazioni ancora da saldare"
        >
          <span className="w-3 h-3 rounded-xs bg-warning-surface border border-warning" />
          <span>Da pagare</span>
        </button>

        <button
          type="button"
          onClick={() => setFiltroLegenda(filtroLegenda === 'presente' ? null : 'presente')}
          className={`flex items-center gap-1.5 px-2 py-1 rounded transition-all cursor-pointer ${
            filtroLegenda === 'presente'
              ? 'bg-primary/20 font-semibold ring-2 ring-primary text-ink'
              : 'hover:bg-surface border border-transparent'
          }`}
          title="Filtra clienti attualmente presenti in salone"
        >
          <span className="w-3 h-3 rounded-xs bg-primary/20 border border-primary" />
          <span>Presente</span>
        </button>

        <button
          type="button"
          onClick={() => setFiltroLegenda(filtroLegenda === 'completata' ? null : 'completata')}
          className={`flex items-center gap-1.5 px-2 py-1 rounded transition-all cursor-pointer ${
            filtroLegenda === 'completata'
              ? 'bg-surface-hover font-semibold ring-2 ring-border text-ink'
              : 'hover:bg-surface border border-transparent'
          }`}
          title="Filtra prenotazioni già completate"
        >
          <span className="w-3 h-3 rounded-xs bg-surface-hover border border-border" />
          <span>Completata</span>
        </button>

        <button
          type="button"
          onClick={() => setFiltroLegenda(filtroLegenda === 'cancellata' ? null : 'cancellata')}
          className={`flex items-center gap-1.5 px-2 py-1 rounded transition-all cursor-pointer ${
            filtroLegenda === 'cancellata'
              ? 'bg-danger-surface font-semibold ring-2 ring-danger text-danger'
              : 'hover:bg-surface border border-transparent'
          }`}
          title="Filtra prenotazioni cancellate"
        >
          <span className="w-3 h-3 rounded-xs bg-danger-surface border border-danger" />
          <span>Cancellata</span>
        </button>

        <div className="flex items-center gap-1.5 px-2 py-1 opacity-75">
          <span className="w-3 h-3 rounded-xs border border-dashed border-success/40 bg-surface" />
          <span>Slot libero</span>
        </div>

        <div className="flex items-center gap-1.5 px-2 py-1 opacity-75">
          <span className="w-3 h-3 rounded-xs bg-warning-surface/80 border border-warning" />
          <span>Ferie / Assenza</span>
        </div>

        {filtroLegenda && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setFiltroLegenda(null)}
            className="text-xs text-primary underline hover:text-primary-hover h-7 px-2"
          >
            Azzera filtro
          </Button>
        )}
      </div>

      {/* Banner Chiusura Salone (se attivo oggi) */}
      {modalita === 'giorno' && chiusuraSaloneOggi && (
        <div className="bg-danger-surface border border-danger/40 text-danger px-4 py-3 rounded-lg flex items-center gap-3 text-xs sm:text-sm">
          <CalendarOff className="h-5 w-5 shrink-0" />
          <div>
            <span className="font-semibold">Salone Chiuso per l'intera giornata: </span>
            <span>{chiusuraSaloneOggi.motivo || 'Chiusura straordinaria programmata.'}</span>
          </div>
        </div>
      )}

      {/* Griglia Calendario */}
      <div className="overflow-x-auto rounded-lg border border-border bg-surface shadow-sm">
        {isLoading ? (
          <div className="p-12 text-center text-sm text-ink-muted">Caricamento calendario…</div>
        ) : modalita === 'giorno' ? (
          /* ================= VISTA GIORNO ================= */
          <div className="min-w-[650px]">
            {/* Intestazione Colonne Operatori */}
            <div className="grid grid-cols-[80px_repeat(auto-fit,minmax(180px,1fr))] border-b border-border bg-surface-hover/50 font-medium text-xs text-ink">
              <div className="p-3 border-r border-border text-center text-ink-muted">Ora</div>
              {operatoriVisualizzati.length > 0 ? (
                operatoriVisualizzati.map((op) => {
                  const assenzaOggi = getAssenzaInteraGiornataOperatore(toYMD(dataRiferimento), op.id)
                  return (
                    <div key={op.id} className="p-2.5 border-r border-border last:border-r-0 flex flex-col items-center justify-center gap-1 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <UserIcon className="h-3.5 w-3.5 text-primary" />
                        <span>{op.nome}</span>
                      </div>
                      {assenzaOggi && (
                        <Badge variant={assenzaOggi.tipo === 'ferie' ? 'warning' : 'danger'} className="text-[10px] py-0">
                          {assenzaOggi.tipo === 'ferie' ? '🌴 In Ferie' : assenzaOggi.tipo === 'malattia' ? '🏥 Malattia' : assenzaOggi.tipo}
                        </Badge>
                      )}
                    </div>
                  )
                })
              ) : (
                <div className="p-3 text-center text-ink-muted">Nessun operatore</div>
              )}
            </div>

            {/* Righe Orarie */}
            <div className="divide-y divide-border">
              {ORE_GIORNATA.map((ora) => (
                <div
                  key={ora}
                  className="grid grid-cols-[80px_repeat(auto-fit,minmax(180px,1fr))] min-h-[64px]"
                >
                  {/* Etichetta Ora */}
                  <div className="p-2 border-r border-border text-xs text-ink-muted font-mono flex items-start justify-center pt-2">
                    {ora}
                  </div>

                  {/* Celle Operatori */}
                  {operatoriVisualizzati.map((op) => {
                    const dataYmd = toYMD(dataRiferimento)
                    const slotPrenotazioni = getPrenotazioniSlot(dataYmd, ora, op.id)
                    const eccezione = getEccezioneSlot(dataYmd, ora, op.id)

                    return (
                      <div
                        key={op.id}
                        className="p-1.5 border-r border-border last:border-r-0 relative flex flex-col gap-1.5 justify-center"
                      >
                        {slotPrenotazioni.length > 0 ? (
                          slotPrenotazioni.map((p) => (
                            <button
                              key={p.id}
                              type="button"
                              onClick={() => setPrenotazioneDettaglio(p)}
                              className={`w-full text-left p-2 rounded border text-xs shadow-xs transition-all hover:scale-[1.01] ${getVarianteBlocco(
                                p,
                              )}`}
                            >
                              <div className="flex justify-between items-center font-semibold mb-0.5">
                                <span className="truncate">{p.cliente_nome}</span>
                                <span className="text-[10px] font-mono shrink-0 ml-1">
                                  {new Date(p.inizio).toLocaleTimeString('it-IT', {
                                    hour: '2-digit',
                                    minute: '2-digit',
                                  })}
                                </span>
                              </div>
                              <div className="text-[11px] truncate opacity-90">
                                {p.servizio_nome}
                              </div>
                            </button>
                          ))
                        ) : eccezione ? (
                          <div
                            className={`h-full w-full rounded border px-2 py-1.5 flex flex-col justify-center text-xs ${
                              eccezione.operatore === null || eccezione.tipo === 'chiusura'
                                ? 'bg-danger-surface/70 border-danger/40 text-danger'
                                : eccezione.tipo === 'ferie'
                                ? 'bg-warning-surface/70 border-warning/40 text-ink'
                                : 'bg-surface-alt border-border text-ink-muted'
                            }`}
                          >
                            <div className="flex items-center gap-1 font-semibold text-[11px]">
                              {eccezione.operatore === null || eccezione.tipo === 'chiusura' ? (
                                <CalendarOff className="h-3 w-3 shrink-0" />
                              ) : (
                                <Palmtree className="h-3 w-3 shrink-0 text-warning" />
                              )}
                              <span className="capitalize">
                                {eccezione.operatore === null ? 'Salone Chiuso' : eccezione.tipo}
                              </span>
                            </div>
                            {eccezione.motivo && (
                              <span className="text-[10px] truncate opacity-80">{eccezione.motivo}</span>
                            )}
                          </div>
                        ) : (
                          <div className="h-full w-full rounded border border-dashed border-success/30 hover:bg-success-surface/30 flex items-center justify-center transition-colors">
                            <span className="text-[10px] text-ink-muted/60">Disponibile</span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* ================= VISTA SETTIMANA ================= */
          <div className="min-w-[850px]">
            {/* Intestazione Giorni della Settimana */}
            <div className="grid grid-cols-[80px_repeat(7,1fr)] border-b border-border bg-surface-hover/50 font-medium text-xs text-ink">
              <div className="p-3 border-r border-border text-center text-ink-muted">Ora</div>
              {giorniSettimanaList.map((giorno, idx) => {
                const ymd = toYMD(giorno)
                const isToday = ymd === toYMD(new Date())
                const chiusuraGiorno = getChiusuraSaloneData(ymd)

                return (
                  <div
                    key={ymd}
                    className={`p-2.5 border-r border-border last:border-r-0 text-center ${
                      isToday ? 'bg-primary/5 text-primary font-semibold' : ''
                    }`}
                  >
                    <div>{GIORNI_SETTIMANA[idx]}</div>
                    <div className="text-ink-muted font-normal text-[11px]">
                      {giorno.getDate()} {giorno.toLocaleDateString('it-IT', { month: 'short' })}
                    </div>
                    {chiusuraGiorno && (
                      <Badge variant="danger" className="text-[9px] px-1.5 py-0 mt-0.5 font-normal">
                        Salone chiuso
                      </Badge>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Righe Orarie Settimana */}
            <div className="divide-y divide-border">
              {ORE_GIORNATA.map((ora) => (
                <div key={ora} className="grid grid-cols-[80px_repeat(7,1fr)] min-h-[64px]">
                  <div className="p-2 border-r border-border text-xs text-ink-muted font-mono flex items-start justify-center pt-2">
                    {ora}
                  </div>

                  {giorniSettimanaList.map((giorno) => {
                    const ymd = toYMD(giorno)
                    const opFiltro = operatoreSelezionato === 'tutti' ? undefined : operatoreSelezionato
                    const slotPrenotazioni = getPrenotazioniSlot(ymd, ora, opFiltro)
                    const eccezione = getEccezioneSlot(ymd, ora, opFiltro)
                    const isToday = ymd === toYMD(new Date())

                    return (
                      <div
                        key={ymd}
                        className={`p-1.5 border-r border-border last:border-r-0 relative flex flex-col gap-1 justify-center ${
                          isToday ? 'bg-primary/2' : ''
                        }`}
                      >
                        {slotPrenotazioni.length > 0 ? (
                          slotPrenotazioni.map((p) => (
                            <button
                              key={p.id}
                              type="button"
                              onClick={() => setPrenotazioneDettaglio(p)}
                              className={`w-full text-left p-1.5 rounded border text-xs shadow-xs transition-all hover:scale-[1.01] ${getVarianteBlocco(
                                p,
                              )}`}
                            >
                              <div className="flex justify-between items-center font-medium">
                                <span className="truncate">{p.cliente_nome}</span>
                              </div>
                              <div className="text-[10px] text-ink-muted truncate">
                                {p.servizio_nome}
                              </div>
                            </button>
                          ))
                        ) : eccezione ? (
                          <div
                            className={`h-full w-full rounded border px-1.5 py-1 flex flex-col justify-center text-[10px] ${
                              eccezione.operatore === null || eccezione.tipo === 'chiusura'
                                ? 'bg-danger-surface/70 border-danger/40 text-danger'
                                : eccezione.tipo === 'ferie'
                                ? 'bg-warning-surface/70 border-warning/40 text-ink'
                                : 'bg-surface-alt border-border text-ink-muted'
                            }`}
                          >
                            <span className="font-semibold capitalize truncate">
                              {eccezione.operatore === null ? 'Salone Chiuso' : eccezione.tipo}
                            </span>
                          </div>
                        ) : (
                          <div className="h-full w-full rounded border border-dashed border-border hover:border-success/40 hover:bg-success-surface/20 flex items-center justify-center transition-colors">
                            <span className="text-[10px] text-ink-muted/40">Libero</span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Dialog Modale con Dettagli e Azioni Rapide */}
      <DettaglioPrenotazioneDialog
        prenotazione={prenotazioneDettaglio}
        onClose={() => setPrenotazioneDettaglio(null)}
      />
    </div>
  )
}
