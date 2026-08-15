import { creaClientRisorsa } from '@/lib/api'

import type { Servizio, ServizioInput } from './types'

export const servizioApi = creaClientRisorsa<Servizio, ServizioInput>('/servizi/')
