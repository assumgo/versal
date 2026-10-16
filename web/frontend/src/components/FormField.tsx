import { useId, type ComponentProps } from 'react';
type Props = ComponentProps<'input'> & { label: string; error?: string; hint?: string };
export function FormField({ label, error, hint, id, ...props }: Props) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  return <div className="form-field"><label htmlFor={fieldId}>{label}</label><input {...props} id={fieldId} aria-invalid={error ? true : undefined} aria-describedby={error || hint ? `${fieldId}-help` : undefined} />{(error || hint) && <small id={`${fieldId}-help`} className={error ? 'field-error' : ''}>{error ?? hint}</small>}</div>;
}
