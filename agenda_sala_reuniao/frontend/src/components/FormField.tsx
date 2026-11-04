import { useId, type ComponentProps } from 'react';

type Props = ComponentProps<'input'> & { label: string; error?: string };

export function FormField({ label, error, id, ...props }: Props) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  return <div className="form-field">
    <label htmlFor={fieldId}>{label}</label>
    <input {...props} id={fieldId} aria-invalid={error ? true : undefined} aria-describedby={error ? `${fieldId}-help` : undefined} />
    {error && <small id={`${fieldId}-help`} className="field-error">{error}</small>}
  </div>;
}
