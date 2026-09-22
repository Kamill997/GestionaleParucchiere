import { ArrowLeft, Shield } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

export function PrivacyPage() {
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
          <Shield className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-display text-2xl font-bold text-ink sm:text-3xl">
            Informativa sulla Privacy
          </h1>
          <p className="text-xs text-ink-muted">
            Conforme al Regolamento Generale sulla Protezione dei Dati (GDPR - UE 2016/679)
          </p>
        </div>
      </div>

      <div className="mt-8 space-y-6 text-sm text-ink-muted leading-relaxed">
        <section>
          <h2 className="font-display text-base font-semibold text-ink">1. Titolare del Trattamento</h2>
          <p className="mt-1">
            Il titolare del trattamento dei dati è il Salone di Parrucchiere. Per qualsiasi richiesta relativa alla protezione dei dati o all'esercizio dei tuoi diritti, puoi contattare il responsabile all'indirizzo email del salone.
          </p>
        </section>

        <section>
          <h2 className="font-display text-base font-semibold text-ink">2. Dati Raccolti</h2>
          <p className="mt-1">Raccogliamo unicamente i dati necessari alla gestione e all'erogazione dei servizi:</p>
          <ul className="mt-2 list-disc pl-5 space-y-1">
            <li><strong>Dati di contatto</strong>: nome, cognome, indirizzo email e numero di telefono.</li>
            <li><strong>Dati di prenotazione</strong>: data e orario dell'appuntamento, servizio richiesto, operatore assegnato, note tecniche/preferenze (es. allergie a tinture o trattamenti specifici).</li>
            <li><strong>Storico e presenze</strong>: archivio degli appuntamenti passati e stato delle presenze per la gestione della disponibilità e delle politiche di no-show.</li>
          </ul>
        </section>

        <section>
          <h2 className="font-display text-base font-semibold text-ink">3. Finalità del Trattamento</h2>
          <p className="mt-1">I tuoi dati vengono trattati esclusivamente per:</p>
          <ul className="mt-2 list-disc pl-5 space-y-1">
            <li>Confermare, gestire e ricordare gli appuntamenti prenotati tramite notifiche ed email.</li>
            <li>Gestire le note tecniche personalizzate per l'esecuzione ottimale del servizio.</li>
            <li>Adempiere agli obblighi di legge e contabili del salone.</li>
          </ul>
        </section>

        <section>
          <h2 className="font-display text-base font-semibold text-ink">4. Sicurezza e Conservazione</h2>
          <p className="mt-1">
            I dati sono protetti tramite connessioni cifrate HTTPS, password salvate con funzioni crittografiche sicure e cookie di sessione protetti. I dati non vengono ceduti a terze parti per scopi promozionali o di profilazione commerciale esterna.
          </p>
        </section>

        <section>
          <h2 className="font-display text-base font-semibold text-ink">5. I Tuoi Diritti (GDPR)</h2>
          <p className="mt-1">
            Hai il diritto di accedere in qualunque momento ai tuoi dati, chiederne la rettifica, la portabilità o la cancellazione contattando direttamente il salone o accedendo alla sezione del tuo profilo personale.
          </p>
        </section>
      </div>
    </div>
  )
}
