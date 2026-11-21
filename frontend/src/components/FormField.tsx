interface FormFieldProps {
  label: string
  name: string
  type?: string
  autoComplete?: string
  defaultValue?: string
  errors?: string[]
}

// A label, an input and the error messages of the server for this field
export default function FormField({
  label,
  name,
  type = 'text',
  autoComplete,
  defaultValue,
  errors = [],
}: FormFieldProps) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <input
        name={name}
        type={type}
        autoComplete={autoComplete}
        defaultValue={defaultValue}
        required
        aria-invalid={errors.length > 0}
      />
      {errors.map((message) => (
        <span key={message} className="error">
          {message}
        </span>
      ))}
    </label>
  )
}
