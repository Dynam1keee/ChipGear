import type { FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { formErrors } from '../api'
import FormField from '../components/FormField'
import { useLogin } from '../queries'

// After the login we go to the page from ?next=..., but only inside this site.
// Otherwise a crafted link (?next=https://evil.example) could send the user to another site.
function safeNext(next: string | null): string {
  if (next && next.startsWith('/') && !next.startsWith('//') && !next.startsWith('/\\')) return next
  return '/'
}

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
      <button type="submit" disabled={login.isPending}>
        {login.isPending ? 'Logging in...' : 'Log in'}
      </button>
    </form>
  )
}
