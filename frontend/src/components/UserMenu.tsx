import { Link } from 'react-router-dom'
import { useLogout, useMe } from '../queries'

// In the header: the name and "Log out" for a user, "Log in" for a guest
export default function UserMenu() {
  const { data: user, isPending } = useMe()
  const logout = useLogout()

  if (isPending) return null

  if (user) {
    return (
      <span className="user-menu">
        <span>Hi, {user.first_name || user.username}</span>
        <button type="button" disabled={logout.isPending} onClick={() => logout.mutate()}>
          Log out
        </button>
      </span>
    )
  }

  return (
    <span className="user-menu">
      <Link to="/login">Log in</Link>
      <Link to="/register">Register</Link>
    </span>
  )
}
