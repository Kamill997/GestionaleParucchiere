import { z } from 'zod'

export const servizioSchema = z.object({
  nome: z.string().min(1, 'Il nome è obbligatorio'),
  categoria: z.string().min(1, 'La categoria è obbligatoria'),
  descrizione: z.string().optional().default(''),
  durata_minuti: z.coerce.number().int().min(1, 'Durata minima 1 minuto'),
  prezzo: z.coerce.number().min(0, 'Il prezzo non può essere negativo').transform(String),
  attivo: z.coerce.boolean().default(true),
})

export type ServizioFormValues = z.infer<typeof servizioSchema>
