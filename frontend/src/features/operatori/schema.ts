import { z } from 'zod'

export const operatoreSchema = z.object({
  user: z.string().min(1, 'Seleziona un account utente'),
  nome: z.string().min(1, 'Il nome è obbligatorio'),
  specializzazioni: z.string().optional().default(''),
  attivo: z.coerce.boolean().default(true),
})

export type OperatoreFormValues = z.infer<typeof operatoreSchema>
