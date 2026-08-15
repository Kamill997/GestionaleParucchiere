import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect } from 'react'
import { Controller, useForm, type FieldValues, type Resolver } from 'react-hook-form'
import type { ZodType } from 'zod'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

export interface CampoFormModal<T extends FieldValues> {
  name: keyof T & string
  label: string
  type?:
    | 'text'
    | 'number'
    | 'email'
    | 'tel'
    | 'textarea'
    | 'select'
    | 'checkbox-group'
    | 'datetime-local'
  options?: { value: string; label: string }[] // per type: 'select' | 'checkbox-group'
  placeholder?: string
}

interface FormModalProps<T extends FieldValues> {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  schema: ZodType<T>
  fields: CampoFormModal<T>[]
  defaultValues?: Partial<T>
  isSubmitting?: boolean
  submitLabel?: string
  onSubmit: (values: T) => void | Promise<void>
}

/**
 * Modale generico di creazione/modifica guidato da uno schema Zod passato
 * come prop (vedi docs/03-componenti-e-workflow.md, "FormModal"). Ogni
 * feature (Servizi, Operatori...) definisce solo schema+campi, non un
 * modale da zero.
 */
export function FormModal<T extends FieldValues>({
  open,
  onOpenChange,
  title,
  description,
  schema,
  fields,
  defaultValues,
  isSubmitting,
  submitLabel = 'Salva',
  onSubmit,
}: FormModalProps<T>) {
  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<T>({
    resolver: zodResolver(schema as ZodType<T, T>) as unknown as Resolver<T>,
    defaultValues: defaultValues as never,
  })

  // Ripristina i valori di default ogni volta che il modale si riapre
  // (es. passando da "modifica riga A" a "modifica riga B").
  useEffect(() => {
    if (open) reset(defaultValues as never)
  }, [open, defaultValues, reset])

  const submit = handleSubmit(async (values: T) => {
    await onSubmit(values)
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title={title} description={description}>
        <form onSubmit={submit} className="space-y-4" noValidate>
          {fields.map((field) => {
            const errorMessage = errors[field.name]?.message as string | undefined
            return (
              <div key={field.name}>
                <Label htmlFor={field.name}>{field.label}</Label>
                {field.type === 'textarea' ? (
                  <Textarea
                    id={field.name}
                    invalid={!!errorMessage}
                    placeholder={field.placeholder}
                    {...register(field.name as never)}
                  />
                ) : field.type === 'select' ? (
                  <Select
                    id={field.name}
                    invalid={!!errorMessage}
                    {...register(field.name as never)}
                  >
                    <option value="">Seleziona…</option>
                    {field.options?.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </Select>
                ) : field.type === 'checkbox-group' ? (
                  <Controller
                    name={field.name as never}
                    control={control}
                    render={({ field: { value, onChange } }) => (
                      <div className="space-y-1.5">
                        {field.options?.map((opt) => {
                          const selezionati: string[] = Array.isArray(value) ? value : []
                          const attivo = selezionati.includes(opt.value)
                          return (
                            <label
                              key={opt.value}
                              className="flex items-center gap-2 text-sm text-ink"
                            >
                              <input
                                type="checkbox"
                                className="h-4 w-4 rounded border-border text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                                checked={attivo}
                                onChange={(e) =>
                                  onChange(
                                    e.target.checked
                                      ? [...selezionati, opt.value]
                                      : selezionati.filter((v) => v !== opt.value),
                                  )
                                }
                              />
                              {opt.label}
                            </label>
                          )
                        })}
                      </div>
                    )}
                  />
                ) : (
                  <Input
                    id={field.name}
                    type={field.type ?? 'text'}
                    invalid={!!errorMessage}
                    placeholder={field.placeholder}
                    {...register(field.name as never)}
                  />
                )}
                {errorMessage && <p className="mt-1 text-sm text-danger">{errorMessage}</p>}
              </div>
            )
          })}
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Annulla
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Salvataggio…' : submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
