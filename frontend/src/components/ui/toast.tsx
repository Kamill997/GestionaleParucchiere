import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { CheckCircle2, X, XCircle } from 'lucide-react'

import { cn } from '@/lib/utils'

interface Toast {
  id: number
  message: string
  variant: 'success' | 'error'
}

interface ToastContextValue {
  showToast: (message: string, variant?: Toast['variant']) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

let nextId = 1

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const showToast = useCallback((message: string, variant: Toast['variant'] = 'success') => {
    const id = nextId++
    setToasts((current) => [...current, { id, message, variant }])
    setTimeout(() => {
      setToasts((current) => current.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  const dismiss = (id: number) => setToasts((current) => current.filter((t) => t.id !== id))

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="alert"
            className={cn(
              'flex items-center gap-2 rounded-lg border px-4 py-3 text-sm shadow-md',
              toast.variant === 'success'
                ? 'border-success/20 bg-surface text-ink'
                : 'border-danger/20 bg-surface text-ink',
            )}
          >
            {toast.variant === 'success' ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-success" />
            ) : (
              <XCircle className="h-4 w-4 shrink-0 text-danger" />
            )}
            <span>{toast.message}</span>
            <button
              onClick={() => dismiss(toast.id)}
              className="ml-2 text-ink-muted hover:text-ink"
              aria-label="Chiudi notifica"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast va usato dentro <ToastProvider>')
  return context
}
