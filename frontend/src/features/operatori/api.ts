import { creaClientRisorsa } from '@/lib/api'

import type { Operatore, OperatoreInput } from './types'

export const operatoreApi = creaClientRisorsa<Operatore, OperatoreInput>('/operatori/')
