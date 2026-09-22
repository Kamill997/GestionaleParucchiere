import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Bell, CheckCircle2, Download, ExternalLink, Plus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PageHeader } from '@/components/ui/page-header'
import { Select } from '@/components/ui/select'
import { useToast } from '@/components/ui/toast'
import { useOperatori } from '@/features/operatori/hooks'
import { useServizi } from '@/features/servizi/hooks'
import { formattaErroreApi } from '@/lib/api'
import { cn } from '@/lib/utils'

import { generaGoogleCalendarUrl, scaricaFileIcs } from './calendarUtils'
import { useCreaPrenotazione, useSlotDisponibili } from './hooks'
import { IscrizioneListaAttesaModal } from './IscrizioneListaAttesaModal'
import type { Prenotazione, SlotDisponibile } from './types'

const formattaOra = (iso: string) =>
  new Date(iso).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })

function toYMD(d: Date): string {
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function domaniISO() {
  const domani = new Date()
  domani.setDate(domani.getDate() + 1)
  return toYMD(domani)
}

export function PrenotaPage() {
  const [searchParams] = useSearchParams()
  const [servizioId, setServizioId] = useState(searchParams.get('servizio') || '')
  const [serviziAggiuntiviIds, setServiziAggiuntiviIds] = useState<string[]>([])
  const [operatoreId, setOperatoreId] = useState(searchParams.get('operatore') || '')
  const [data, setData] = useState(searchParams.get('data') || domaniISO())
  const [slotScelto, setSlotScelto] = useState<SlotDisponibile | null>(null)
  const [prenotazioneConfermata, setPrenotazioneConfermata] = useState<Prenotazione | null>(null)
  const [showWaitingModal, setShowWaitingModal] = useState(false)
  const [oraPerListaAttesa, setOraPerListaAttesa] = useState<string | undefined>()

  useEffect(() => {
    const s = searchParams.get('servizio')
    const o = searchParams.get('operatore')
    const d = searchParams.get('data')
    if (s) setServizioId(s)
    if (o) setOperatoreId(o)
    if (d) setData(d)
  }, [searchParams])

  const { data: servizi } = useServizi(1)
  const { data: operatori } = useOperatori(1, true)

  const servizioSelezionato = useMemo(
    () => servizi?.results.find((s) => s.id === servizioId),
    [servizi, servizioId],
  )

  const serviziAggiuntiviSelezionati = useMemo(
    () => (servizi?.results ?? []).filter((s) => serviziAggiuntiviIds.includes(s.id)),
    [servizi, serviziAggiuntiviIds],
  )

  const durataTotaleMinuti = useMemo(() => {
    const base = servizioSelezionato?.durata_minuti ?? 0
    const extra = serviziAggiuntiviSelezionati.reduce((acc, s) => acc + s.durata_minuti, 0)
    return base + extra
  }, [servizioSelezionato, serviziAggiuntiviSelezionati])

  const prezzoTotale = useMemo(() => {
    const base = parseFloat(servizioSelezionato?.prezzo ?? '0')
    const extra = serviziAggiuntiviSelezionati.reduce((acc, s) => acc + parseFloat(s.prezzo), 0)
    return (base + extra).toFixed(2)
  }, [servizioSelezionato, serviziAggiuntiviSelezionati])

  const toggleServizioAggiuntivo = (id: string) => {
    setSlotScelto(null)
    setServiziAggiuntiviIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }

  const {
    data: slot,
    isLoading: caricandoSlot,
    isFetching: aggiornandoSlot,
  } = useSlotDisponibili(operatoreId, servizioId, data, serviziAggiuntiviIds)
  const creaMutation = useCreaPrenotazione()
  const { showToast } = useToast()

  const prontoPerScegliereData = !!servizioId && !!operatoreId

  // Filtro client-side per escludere slot il cui orario d'inizio è già trascorso nella giornata odierna
  const slotFiltrati = useMemo(() => {
    if (!slot) return null
    const oggiYMD = toYMD(new Date())
    const isOggi = data === oggiYMD
    const adesso = Date.now()

    return slot.filter((s) => {
      if (isOggi) {
        const t = new Date(s.inizio).getTime()
        if (t <= adesso) {
          return false
        }
      }
      return true
    })
  }, [slot, data])

  const confermaPrenotazione = async () => {
    if (!slotScelto) return
    try {
      const p = await creaMutation.mutateAsync({
        operatore: operatoreId,
        servizio: servizioId,
        servizi_aggiuntivi: serviziAggiuntiviIds,
        inizio: slotScelto.inizio,
      })
      setPrenotazioneConfermata(p)
      showToast('Prenotazione confermata!')
      setSlotScelto(null)
    } catch (error) {
      showToast(
        formattaErroreApi(error, 'Errore durante la prenotazione, riprova.'),
        'error',
      )
    }
  }

  if (prenotazioneConfermata) {
    return (
      <div className="max-w-2xl">
        <PageHeader
          title="Appuntamento confermato!"
          description="La tua prenotazione è stata registrata con successo."
        />

        <div className="mt-6 rounded-lg border border-success/30 bg-success-surface/40 p-6 space-y-5 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-success text-white">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-display text-lg font-semibold text-ink">
                Appuntamento fissato
              </h3>
              <p className="text-xs text-ink-muted">
                Riceverai anche un promemoria prima dell'appuntamento.
              </p>
            </div>
          </div>

          <div className="grid gap-2 rounded-md border border-border bg-surface p-4 text-sm">
            <div className="flex justify-between border-b border-border/60 pb-2">
              <span className="text-ink-muted">Servizio principale</span>
              <span className="font-medium text-ink">{prenotazioneConfermata.servizio_nome}</span>
            </div>
            {prenotazioneConfermata.servizi_aggiuntivi_dettaglio &&
              prenotazioneConfermata.servizi_aggiuntivi_dettaglio.length > 0 && (
                <div className="flex justify-between border-b border-border/60 py-2">
                  <span className="text-ink-muted">Trattamenti aggiuntivi</span>
                  <span className="font-medium text-ink text-right">
                    {prenotazioneConfermata.servizi_aggiuntivi_dettaglio
                      .map((s) => s.nome)
                      .join(', ')}
                  </span>
                </div>
              )}
            <div className="flex justify-between border-b border-border/60 py-2">
              <span className="text-ink-muted">Collaboratore</span>
              <span className="font-medium text-ink">{prenotazioneConfermata.operatore_nome}</span>
            </div>
            <div className="flex justify-between border-b border-border/60 py-2">
              <span className="text-ink-muted">Quando</span>
              <span className="font-medium text-ink">
                {new Date(prenotazioneConfermata.inizio).toLocaleString('it-IT', {
                  dateStyle: 'full',
                  timeStyle: 'short',
                })}
              </span>
            </div>
            {prenotazioneConfermata.durata_totale_minuti && (
              <div className="flex justify-between border-b border-border/60 py-2">
                <span className="text-ink-muted">Durata stimata</span>
                <span className="font-medium text-ink">
                  {prenotazioneConfermata.durata_totale_minuti} minuti
                </span>
              </div>
            )}
            <div className="flex justify-between pt-2">
              <span className="text-ink-muted">Importo totale</span>
              <span className="font-semibold text-ink">€ {prenotazioneConfermata.importo}</span>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
              Aggiungi al tuo calendario personale
            </p>
            <div className="flex flex-wrap gap-2.5">
              <Button
                variant="secondary"
                onClick={() => scaricaFileIcs(prenotazioneConfermata.id)}
                className="flex items-center gap-2"
              >
                <Download className="h-4 w-4" />
                Scarica file iCal (.ics)
              </Button>
              <Button
                variant="secondary"
                asChild
                className="flex items-center gap-2"
              >
                <a
                  href={generaGoogleCalendarUrl(prenotazioneConfermata)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="h-4 w-4 text-primary" />
                  Aggiungi a Google Calendar
                </a>
              </Button>
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-border pt-4">
            <Button
              variant="ghost"
              onClick={() => {
                setPrenotazioneConfermata(null)
                setSlotScelto(null)
              }}
              className="flex items-center gap-1.5"
            >
              <Plus className="h-4 w-4" />
              Prenota un altro appuntamento
            </Button>
            <Button asChild variant="secondary">
              <Link to="/le-mie-prenotazioni">Le mie prenotazioni</Link>
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Prenota un appuntamento"
        description="Scegli servizio, operatore e orario."
      />

      <div className="grid max-w-2xl gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="servizio">Servizio</Label>
          <Select
            id="servizio"
            value={servizioId}
            onChange={(e) => {
              setServizioId(e.target.value)
              setSlotScelto(null)
            }}
          >
            <option value="">Seleziona un servizio…</option>
            {servizi?.results.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nome} — {s.durata_minuti} min — € {s.prezzo}
              </option>
            ))}
          </Select>
          {(() => {
            const sel = servizi?.results.find((s) => s.id === servizioId)
            if (!sel || (!sel.foto && !sel.descrizione)) return null
            return (
              <div className="mt-2 flex items-center gap-3 rounded-md border border-border bg-surface-alt p-2.5">
                {sel.foto && (
                  <img
                    src={sel.foto}
                    alt={sel.nome}
                    className="h-14 w-14 shrink-0 rounded-md border border-border object-cover"
                  />
                )}
                {sel.descrizione && (
                  <p className="text-xs text-ink-muted leading-relaxed">
                    {sel.descrizione}
                  </p>
                )}
              </div>
            )
          })()}
        </div>

        <div>
          <Label htmlFor="operatore">Operatore</Label>
          <Select
            id="operatore"
            value={operatoreId}
            onChange={(e) => {
              setOperatoreId(e.target.value)
              setSlotScelto(null)
            }}
          >
            <option value="">Seleziona un operatore…</option>
            {operatori?.results.map((o) => (
              <option key={o.id} value={o.id}>
                {o.nome}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Label htmlFor="data">Giorno</Label>
          <Input
            id="data"
            type="date"
            min={toYMD(new Date())}
            value={data}
            onChange={(e) => {
              setData(e.target.value)
              setSlotScelto(null)
            }}
          />
        </div>
      </div>

      {/* Trattamenti aggiuntivi opzionali */}
      {servizioId && (servizi?.results.length ?? 0) > 1 && (
        <div className="mt-4 max-w-2xl rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between mb-1.5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
              Vuoi aggiungere altri servizi allo stesso appuntamento? (opzionale)
            </h4>
            <span className="text-xs font-medium text-primary">
              {serviziAggiuntiviIds.length > 0
                ? `${serviziAggiuntiviIds.length} aggiunt${serviziAggiuntiviIds.length === 1 ? 'o' : 'i'}`
                : 'Nessun extra'}
            </span>
          </div>
          <p className="text-xs text-ink-muted mb-3">
            Puoi prenotare più servizi contemporaneamente (es. Taglio + Barba + Trattamento). Il sistema calcolerà automaticamente la durata totale e troverà gli slot orari consecutivi necessari.
          </p>

          <div className="grid gap-2 sm:grid-cols-2">
            {(servizi?.results ?? [])
              .filter((s) => s.id !== servizioId)
              .map((extra) => {
                const checked = serviziAggiuntiviIds.includes(extra.id)
                return (
                  <label
                    key={extra.id}
                    className={`flex items-start gap-3 p-2.5 rounded-md border cursor-pointer transition-all ${
                      checked
                        ? 'border-primary bg-primary-surface/40 shadow-xs'
                        : 'border-border bg-surface-alt/40 hover:bg-surface-alt'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleServizioAggiuntivo(extra.id)}
                      className="mt-0.5 h-4 w-4 rounded border-border text-primary focus:ring-primary"
                    />
                    <div className="text-xs flex-1">
                      <div className="flex justify-between font-medium text-ink">
                        <span>{extra.nome}</span>
                        <span className="font-mono text-ink">€ {extra.prezzo}</span>
                      </div>
                      <span className="text-[11px] text-ink-muted">{extra.durata_minuti} min</span>
                    </div>
                  </label>
                )
              })}
          </div>

          <div className="mt-3 flex items-center justify-between border-t border-border pt-3 text-xs">
            <span className="text-ink-muted">
              Durata totale stimata:{' '}
              <strong className="text-ink font-mono font-semibold">{durataTotaleMinuti} min</strong>
            </span>
            <span className="text-ink-muted">
              Importo totale:{' '}
              <strong className="text-primary font-mono font-bold text-sm">€ {prezzoTotale}</strong>
            </span>
          </div>
        </div>
      )}

      <div className="mt-6 max-w-2xl">
        {!prontoPerScegliereData ? (
          <p className="text-sm text-ink-muted">
            Scegli servizio e operatore per vedere gli orari liberi.
          </p>
        ) : caricandoSlot ? (
          <p className="text-sm text-ink-muted">Caricamento orari…</p>
        ) : slotFiltrati && slotFiltrati.length === 0 ? (
          <EmptyState
            title="Nessuno slot disponibile"
            description="Tutti gli orari sono occupati o non disponibili per questa data. Puoi metterti in lista d'attesa per essere avvisato non appena si libera un posto!"
            action={
              <Button
                variant="secondary"
                onClick={() => {
                  setOraPerListaAttesa(undefined)
                  setShowWaitingModal(true)
                }}
                className="gap-1.5"
              >
                <Bell className="h-4 w-4 text-primary" />
                Iscriviti alla lista d'attesa
              </Button>
            }
          />
        ) : (
          <div>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-medium text-ink">
                Orari per questa data {aggiornandoSlot && '(aggiornamento…)'}
              </p>
              <div className="flex items-center gap-3 text-xs text-ink-muted">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-primary" />
                  Libero
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-danger" />
                  Occupato (clicca per lista d'attesa)
                </span>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {slotFiltrati?.map((s) => {
                const isOccupato = s.disponibile === false
                const isSelezionato = slotScelto?.inizio === s.inizio

                if (isOccupato) {
                  return (
                    <button
                      key={s.inizio}
                      type="button"
                      onClick={() => {
                        setOraPerListaAttesa(formattaOra(s.inizio))
                        setShowWaitingModal(true)
                      }}
                      title="Orario occupato - Clicca per iscriverti alla lista d'attesa per quest'orario"
                      className="flex items-center gap-1.5 rounded-md border border-danger/30 bg-danger-surface px-3 py-2 text-sm font-medium text-danger hover:border-danger hover:bg-danger-surface/80 transition-colors cursor-pointer"
                    >
                      <span>{formattaOra(s.inizio)}</span>
                      <span className="rounded bg-danger/10 px-1 py-0.2 text-[10px] font-bold uppercase tracking-wider text-danger">
                        Occupato
                      </span>
                    </button>
                  )
                }

                return (
                  <button
                    key={s.inizio}
                    type="button"
                    onClick={() => setSlotScelto(s)}
                    className={cn(
                      'rounded-md border px-3 py-2 text-sm font-medium transition-colors',
                      isSelezionato
                        ? 'border-primary bg-primary text-primary-foreground shadow-xs'
                        : 'border-border bg-surface text-ink hover:border-primary',
                    )}
                  >
                    {formattaOra(s.inizio)}
                  </button>
                )
              })}
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-primary/20 bg-primary-surface/30 p-3 text-xs">
              <div className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-primary shrink-0" />
                <span className="text-ink">
                  Non trovi l'orario perfetto o il tuo orario preferito è occupato?
                </span>
              </div>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => {
                  setOraPerListaAttesa(undefined)
                  setShowWaitingModal(true)
                }}
                className="gap-1 text-xs"
              >
                <Bell className="h-3.5 w-3.5 text-primary" />
                Entra in lista d'attesa
              </Button>
            </div>
          </div>
        )}
      </div>

      {slotScelto && (
        <div className="mt-6 max-w-2xl rounded-lg border border-border bg-surface-alt p-4">
          <p className="text-sm text-ink">
            Confermi l'appuntamento delle <strong>{formattaOra(slotScelto.inizio)}</strong> del{' '}
            <strong>{new Date(data).toLocaleDateString('it-IT')}</strong>?
          </p>
          <div className="mt-2 rounded-md bg-surface p-2.5 text-xs text-ink-muted space-y-1 border border-border/60">
            <div>
              Trattamenti:{' '}
              <strong className="text-ink">{servizioSelezionato?.nome}</strong>
              {serviziAggiuntiviSelezionati.length > 0 && (
                <span className="text-primary font-medium">
                  {' '}+ {serviziAggiuntiviSelezionati.map((s) => s.nome).join(', ')}
                </span>
              )}
            </div>
            <div className="flex items-center gap-4">
              <span>
                Durata stimata: <strong className="text-ink">{durataTotaleMinuti} min</strong>
              </span>
              <span>
                Totale: <strong className="text-ink font-mono font-bold">€ {prezzoTotale}</strong>
              </span>
            </div>
          </div>
          <Button className="mt-3" onClick={confermaPrenotazione} disabled={creaMutation.isPending}>
            {creaMutation.isPending ? 'Conferma in corso…' : 'Conferma prenotazione'}
          </Button>
        </div>
      )}

      <IscrizioneListaAttesaModal
        open={showWaitingModal}
        onOpenChange={setShowWaitingModal}
        servizioId={servizioId}
        servizioNome={servizi?.results.find((s) => s.id === servizioId)?.nome || ''}
        operatoreId={operatoreId}
        operatoreNome={operatori?.results.find((o) => o.id === operatoreId)?.nome}
        data={data}
        oraIniziale={oraPerListaAttesa}
      />
    </div>
  )
}
