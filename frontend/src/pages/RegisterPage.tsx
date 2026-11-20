import type { FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { formErrors } from '../api'
import FormField from '../components/FormField'
import { useRegister } from '../queries'
import { safeNext } from '../safeNext'

const FIELDS = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2'] as const

export default function RegisterPage() {
  const register = useRegister()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const errors = formErrors(register.error)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const [first_name, last_name, username, email, password1, password2] = FIELDS.map((name) =>
      String(form.get(name) ?? ''),
    )
    register.mutate(
      { first_name, last_name, username, email, password1, password2 },
      { onSuccess: () => navigate(safeNext(searchParams.get('next'))) },
    )
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>Register</h2>
      {errors.non_field_errors?.map((message) => (
        <p key={message} className="error">
          {message}
        </p>
      ))}
      <FormField label="First name" name="first_name" autoComplete="given-name" errors={errors.first_name} />
      <FormField label="Last name" name="last_name" autoComplete="family-name" errors={errors.last_name} />
      <FormField label="Username" name="username" autoComplete="username" errors={errors.username} />
      <FormField label="Email" name="email" type="email" autoComplete="email" errors={errors.email} />
      <FormField
        label="Password"
        name="password1"
        type="password"
        autoComplete="new-password"
        errors={errors.password1}
      />
      <FormField
        label="Repeat password"
        name="password2"
        type="password"
        autoComplete="new-password"
        errors={errors.password2}
      />
      <button type="submit" disabled={register.isPending}>
        {register.isPending ? 'Registering...' : 'Register'}
      </button>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </form>
  )
}
