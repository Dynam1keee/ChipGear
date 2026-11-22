import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { formErrors } from '../api'
import FormField from '../components/FormField'
import { useMe, useUpdateProfile } from '../queries'

export default function ProfilePage() {
  const { data: user, isPending } = useMe()
  const update = useUpdateProfile()
  const errors = formErrors(update.error)

  if (isPending) return <p>Loading...</p>

  if (!user) {
    return (
      <div className="not-found">
        <h2>Please log in to see your profile</h2>
        <Link to="/login?next=/profile">Log in</Link>
      </div>
    )
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const value = (name: string) => String(form.get(name) ?? '')
    update.mutate({
      first_name: value('first_name'),
      last_name: value('last_name'),
      username: value('username'),
      email: value('email'),
    })
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>Your profile</h2>
      {errors.non_field_errors?.map((message) => (
        <p key={message} className="error">
          {message}
        </p>
      ))}
      <FormField label="First name" name="first_name" defaultValue={user.first_name} errors={errors.first_name} />
      <FormField label="Last name" name="last_name" defaultValue={user.last_name} errors={errors.last_name} />
      <FormField label="Username" name="username" defaultValue={user.username} errors={errors.username} />
      <FormField label="Email" name="email" type="email" defaultValue={user.email} errors={errors.email} />
      <button type="submit" className="primary" disabled={update.isPending}>
        {update.isPending ? 'Saving...' : 'Save'}
      </button>
      {update.isSuccess && <p className="success">Profile updated.</p>}
      <p>
        <Link to="/orders">Your orders</Link>
      </p>
    </form>
  )
}
