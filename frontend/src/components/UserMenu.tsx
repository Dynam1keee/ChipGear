import { useCallback, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useLogout, useMe } from '../queries'
import { useDismiss } from '../useClickOutside'

// The greeting in the header. A click opens a menu with everything else:
// the profile, the orders, the PC builder, the admin panel (staff only) and the exit.
// A guest sees "Log in" with the login and registration links.
export default function UserMenu() {
  const { data: user, isPending } = useMe()
  const logout = useLogout()
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const close = useCallback(() => setOpen(false), [])
  useDismiss(rootRef, open, close)

  if (isPending) return null

  const label = user ? `Hi, ${user.first_name || user.username}` : 'Hello, guest'

  return (
    <div className="user-menu" ref={rootRef}>
      <button
        type="button"
        className="user-button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <img src="/icons/user_icon.svg" alt="" width={25} height={25} />
        <span className="user-label">{label}</span>
        <span className="chevron" aria-hidden="true" />
      </button>

      {open && (
        // a click on any item (a link or the button) closes the menu
        <div className="menu" role="menu" onClick={close}>
          {user ? (
            <>
              <Link to="/profile" role="menuitem">Profile</Link>
              <Link to="/orders" role="menuitem">Orders</Link>
              <Link to="/builder" role="menuitem">PC Builder</Link>
              {user.is_staff && (
                // the admin panel is not a page of the React app: a normal link, full page load
                <a href="/admin/" role="menuitem">Admin panel</a>
              )}
              <button type="button" role="menuitem" disabled={logout.isPending} onClick={() => logout.mutate()}>
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" role="menuitem">Log in</Link>
              <Link to="/register" role="menuitem">Register</Link>
              <Link to="/builder" role="menuitem">PC Builder</Link>
            </>
          )}
        </div>
      )}
    </div>
  )
}
