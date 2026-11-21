import { Link } from 'react-router-dom'

export interface Crumb {
  label: string
  to?: string // the last crumb is the current page and has no link
}

// "home icon / Category / Product"
export default function Breadcrumbs({ items }: { items: Crumb[] }) {
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <Link to="/" aria-label="Home">
        <img src="/icons/home_icon.svg" alt="" width={20} height={20} />
      </Link>
      {items.map((item) => (
        <span key={item.label} className="crumb">
          <span className="crumb-separator">/</span>
          {item.to ? <Link to={item.to}>{item.label}</Link> : <span aria-current="page">{item.label}</span>}
        </span>
      ))}
    </nav>
  )
}
