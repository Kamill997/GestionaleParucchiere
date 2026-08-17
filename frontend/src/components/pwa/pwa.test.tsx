import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { InstallButton } from './InstallButton'
import { OfflineBanner } from './OfflineBanner'

describe('OfflineBanner', () => {
  const originalOnLine = navigator.onLine

  afterEach(() => {
    Object.defineProperty(navigator, 'onLine', { value: originalOnLine, configurable: true })
  })

  it('non mostra nulla quando online', () => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true })
    render(<OfflineBanner />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('mostra il banner quando va offline', () => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true })
    render(<OfflineBanner />)

    act(() => {
      Object.defineProperty(navigator, 'onLine', { value: false, configurable: true })
      window.dispatchEvent(new Event('offline'))
    })

    expect(screen.getByRole('status')).toHaveTextContent(/sei offline/i)
  })
})

describe('InstallButton', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  it('non mostra nulla finché il browser non emette beforeinstallprompt', () => {
    render(<InstallButton />)
    expect(screen.queryByRole('button', { name: /installa app/i })).not.toBeInTheDocument()
  })

  it('mostra il pulsante dopo beforeinstallprompt e chiama prompt() al click', async () => {
    render(<InstallButton />)

    const promptSpy = vi.fn().mockResolvedValue(undefined)
    const event = new Event('beforeinstallprompt', { cancelable: true }) as Event & {
      prompt: () => Promise<void>
      userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
    }
    event.prompt = promptSpy
    event.userChoice = Promise.resolve({ outcome: 'accepted' })

    await act(async () => {
      window.dispatchEvent(event)
    })

    const button = await screen.findByRole('button', { name: /installa app/i })
    await act(async () => {
      button.click()
    })

    expect(promptSpy).toHaveBeenCalledTimes(1)
  })
})
