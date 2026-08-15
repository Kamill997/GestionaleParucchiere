import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: unknown) {
    console.error('Errore non gestito:', error)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-6 text-center">
          <p className="font-display text-lg font-semibold text-ink">Qualcosa è andato storto.</p>
          <p className="text-sm text-ink-muted">
            Riprova a ricaricare la pagina. Se il problema persiste, contatta l&apos;amministratore.
          </p>
        </div>
      )
    }
    return this.props.children
  }
}
