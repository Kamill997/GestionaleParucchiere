import { ArrowLeft, FileText } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

export function TerminiPage() {
  return (
    <div className="mx-auto max-w-3xl p-6 sm:p-10">
      <div className="mb-6">
        <Button asChild variant="ghost" size="sm">
          <Link to="/">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Torna indietro
          </Link>
        </Button>
      </div>

      <div className="flex items-center gap-3 border-b border-border pb-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <FileText className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-display text-2xl font-bold text-ink sm:text-3xl">
            Termini e Condizioni di Servizio
          </h1>
          <p className="text-xs text-ink-muted">
            Regole e condizioni per l'utilizzo del sistema di prenotazione del Salone
          </p>
        </div>
      </div>

      <div className="mt-8 space-y-6 text-sm text-ink-muted leading-relaxed">
        <section>
          <h2 className="font-display text-base font-semibold text-ink">1. Oggetto del Servizio</h2>
          <p className="mt-1">
            L'applicazione consente agli utenti di consultare il listino servizi del salone, verificare gli orari disponibili e prenotare appuntamenti in autonomia.
          </p>
        </section>

        <section>
          <h2 className="font-display text-base font-semibold text-ink">2. Politica di Cancellazione</h2>
          <p className="mt-1">
            Gli appuntamenti possono essere cancellati liberamente tramite la sezione "Le mie prenotazioni" con un preavviso minimo di 24 ore rispetto all'orario concordato, consentendo ad altri clienti di usufruire dello slot liberato.
          </p>
        </section>

        <section>
          <h2 className="font-display text-base font-semibold text-ink">3. Politica No-Show (Mancata Presentazione)</h2>
          <p className="mt-1">
            Per tutelare il lavoro degli operatori, le mancate presentazioni senza preavviso vengono conteggiate dal sistema. Al superamento della soglia consentita (3 mancate presentazioni), le prenotazioni future online verranno temporaneamente sospese e sarà necessario contattare direttamente il salone per lo sblocco.
          </p>
        </section>

        <section>
          <h2 className="font-display text-base font-semibold text-ink">4. Pagamenti</h2>
          <p className="mt-1">
            La prenotazione online fissa l'appuntamento. Il corrispettivo del servizio viene regolato direttamente in salone al termine della prestazione, secondo le tariffe in vigore indicate nel listino.
          </p>
        </section>
      </div>
    </div>
  )
}
