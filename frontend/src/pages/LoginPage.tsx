import type { FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { formErrors } from '../api'
import FormField from '../components/FormField'
import { safeNext } from '../safeNext'
import { useLogin } from '../queries'

export default function LoginPage() {
  const login = useLogin()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const errors = formErrors(login.error)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    login.mutate(
      { username: String(data.get('username') ?? ''), password: String(data.get('password') ?? '') },
      { onSuccess: () => navigate(safeNext(searchParams.get('next'))) },
    )
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>Log in</h2>
      {errors.non_field_errors?.map((message) => (
        <p key={message} className="error">
          {message}
        </p>
      ))}
      <FormField label="Username" name="username" autoComplete="username" errors={errors.username} />
      <FormField
        label="Password"
        name="password"
        type="password"
        autoComplete="current-password"
        errors={errors.password}
      />
      <button type="submit" className="primary" disabled={login.isPending}>
        {login.isPending ? 'Logging in...' : 'Log in'}
      </button>
      <p>
        No account? <Link to="/register">Register</Link>
      </p>
    </form>
  )
}
