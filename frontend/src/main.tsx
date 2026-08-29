import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './app/App.tsx'

// Ascolta i messaggi NAVIGATE inviati dal service worker quando l'utente
// clicca su una notifica push nativa (vedi src/sw.ts, handler notificationclick).
// Il service worker non puo' usare client.navigate() su client non controllati,
// quindi usa postMessage come canale di comunicazione verso l'app.
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.addEventListener('message', (event) => {
    if (event.data?.type === 'NAVIGATE' && typeof event.data.url === 'string') {
      // React Router e' gia' inizializzato dentro App: usa history direttamente
      // (window.history.pushState) invece di importare il router qui, cosi'
      // non c'e' un accoppiamento diretto tra main.tsx e il router.
      window.history.pushState({}, '', event.data.url)
      // Dispatch un evento popstate per far reagire React Router al cambio
      // di URL: senza questo il routing interno non si aggiorna.
      window.dispatchEvent(new PopStateEvent('popstate'))
    }
  })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
