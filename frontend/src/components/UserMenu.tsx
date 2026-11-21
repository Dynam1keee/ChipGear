import { Link } from 'react-router-dom'
import { useLogout, useMe } from '../queries'

// In the header: for a user the profile, the orders and the exit; for a guest "Log in" and "Register"
export default function UserMenu() {
  const { data: user, isPending } = useMe()
  const logout = useLogout()

  if (isPending) return null

  if (user) {
    return (
      <span className="user-menu">
        <Link to="/profile" className="user-link">
          <img src="/icons/user_icon.svg" alt="" width={25} height={25} />
          <span>Hi, {user.first_name || user.username}</span>
        </Link>
        <Link to="/orders">Orders</Link>
        <button type="button" className="icon-button" aria-label="Log out" title="Log out" disabled={logout.isPending} onClick={() => logout.mutate()}>
          <img src="/icons/logout_icon.svg" alt="" width={25} height={25} />
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
