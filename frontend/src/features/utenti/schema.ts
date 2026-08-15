import { z } from 'zod'

const baseSchema = {
  email: z.string().min(1, "L'email è obbligatoria").email('Email non valida'),
  nome: z.string().optional().default(''),
  cognome: z.string().optional().default(''),
  stato: z.enum(['attivo', 'invitato', 'sospeso']).default('attivo'),
  ruoli: z.array(z.string()).optional().default([]),
}

export const utenteAdminCreateSchema = z.object({
  ...baseSchema,
  password: z.string().min(8, 'Almeno 8 caratteri'),
})

export const utenteAdminEditSchema = z.object({
  ...baseSchema,
  password: z.string().min(8, 'Almeno 8 caratteri').optional().or(z.literal('')),
})

export type UtenteAdminFormValues = z.infer<typeof utenteAdminEditSchema>
