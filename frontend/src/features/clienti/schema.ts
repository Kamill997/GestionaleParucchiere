import { z } from 'zod'

export const clienteSchema = z.object({
  nome: z.string().min(1, 'Il nome è obbligatorio'),
  email: z.string().email('Email non valida').optional().or(z.literal('')),
  telefono: z.string().optional().default(''),
  note_preferenze: z.string().optional().default(''),
})

export type ClienteFormValues = z.infer<typeof clienteSchema>
