import { describe, expect, it, vi } from 'vitest'
import {
  formatUtcForGoogle,
  generaGoogleCalendarUrl,
  scaricaFileIcs,
  type PrenotazionePerCalendario,
} from './calendarUtils'

describe('calendarUtils', () => {
  it('formatUtcForGoogle converte ISO in stringa compatibile UTC YYYYMMDDTHHmmssZ', () => {
    const iso = '2026-08-15T10:30:00.000Z'
    const res = formatUtcForGoogle(iso)
    expect(res).toBe('20260815T103000Z')
  })

  it('generaGoogleCalendarUrl genera link valido con parametri corretti', () => {
    const prenotazione: PrenotazionePerCalendario = {
      inizio: '2026-08-15T10:00:00.000Z',
      fine: '2026-08-15T10:30:00.000Z',
      servizio_nome: 'Taglio Donna',
      operatore_nome: 'Chiara',
      note: 'Preferisco piega liscia',
    }

    const url = generaGoogleCalendarUrl(prenotazione, 'Salone Bellezza')
    expect(url).toContain('https://calendar.google.com/calendar/render?')
    expect(url).toContain('action=TEMPLATE')
    expect(url).toContain('dates=20260815T100000Z%2F20260815T103000Z')
    expect(url).toContain('Taglio+Donna+-+Salone+Bellezza')
    expect(url).toContain('Preferisco+piega+liscia')
    expect(url).toContain('location=Salone+Bellezza')
  })

  it('scaricaFileIcs esegue fetch e avvia il download del blob', async () => {
    const mockBlob = new Blob(['BEGIN:VCALENDAR...'], { type: 'text/calendar' })
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        blob: vi.fn().mockResolvedValue(mockBlob),
      }),
    )

    const createObjectUrlMock = vi.fn().mockReturnValue('blob:http://localhost/fake')
    const revokeObjectUrlMock = vi.fn()
    window.URL.createObjectURL = createObjectUrlMock
    window.URL.revokeObjectURL = revokeObjectUrlMock

    await scaricaFileIcs('prenotazione-123')

    expect(fetch).toHaveBeenCalledWith('/api/v1/prenotazioni/prenotazione-123/ics/', {
      credentials: 'include',
    })
    expect(createObjectUrlMock).toHaveBeenCalledWith(mockBlob)
    expect(revokeObjectUrlMock).toHaveBeenCalledWith('blob:http://localhost/fake')
  })
})
