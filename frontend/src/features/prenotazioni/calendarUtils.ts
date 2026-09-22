export interface PrenotazionePerCalendario {
  id?: string
  inizio: string
  fine: string
  servizio_nome: string
  operatore_nome: string
  note?: string
}

export function formatUtcForGoogle(isoDate: string): string {
  const d = new Date(isoDate)
  return d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
}

export function generaGoogleCalendarUrl(
  prenotazione: PrenotazionePerCalendario,
  nomeSalone = 'Salone',
): string {
  const dates = `${formatUtcForGoogle(prenotazione.inizio)}/${formatUtcForGoogle(prenotazione.fine)}`
  const text = `${prenotazione.servizio_nome} - ${nomeSalone}`
  let details = `Appuntamento per ${prenotazione.servizio_nome} con ${prenotazione.operatore_nome}.`
  if (prenotazione.note) {
    details += ` Note: ${prenotazione.note}`
  }
  const location = nomeSalone

  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text,
    dates,
    details,
    location,
  })

  return `https://calendar.google.com/calendar/render?${params.toString()}`
}

export async function scaricaFileIcs(prenotazioneId: string): Promise<void> {
  const res = await fetch(`/api/v1/prenotazioni/${prenotazioneId}/ics/`, {
    credentials: 'include',
  })
  if (!res.ok) {
    throw new Error('Impossibile scaricare il file del calendario.')
  }
  const blob = await res.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `prenotazione-${prenotazioneId}.ics`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}
