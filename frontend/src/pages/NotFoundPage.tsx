import { FileQuestion, Home } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center p-6 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-alt text-primary shadow-sm">
        <FileQuestion className="h-8 w-8" />
      </div>
      <h1 className="font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">
        404
      </h1>
      <h2 className="mt-2 text-xl font-semibold text-ink">
        Pagina non trovata
      </h2>
      <p className="mt-2 max-w-md text-sm text-ink-muted">
        L'indirizzo che hai digitato non esiste o è stato spostato. Verifica l'URL o torna alla pagina principale del salone.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Button asChild variant="primary">
          <Link to="/">
            <Home className="mr-2 h-4 w-4" />
            Torna alla Dashboard
          </Link>
        </Button>
      </div>
    </div>
  )
}
