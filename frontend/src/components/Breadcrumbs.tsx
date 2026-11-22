import { Link } from 'react-router-dom'

// A crumb that is a drop-down list: a quick way to go to another category
export interface CrumbSelect {
  value: string
  options: { value: string; label: string }[]
  onChange: (value: string) => void
}

export interface Crumb {
  label: string
  to?: string // a crumb with an address is a link; the last crumb is the current page
  select?: CrumbSelect // a crumb with "select" is a drop-down list
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
          {item.select ? (
            // The visible text decides the width; the real <select> lies above it and is invisible.
            // So the list is a native one (keyboard, phone), and the width follows the chosen option.
            <span className="crumb-select">
              <span className="crumb-select-text">
                {item.select.options.find((option) => option.value === item.select?.value)?.label ?? item.label}
              </span>
              <select
                aria-label="Go to category"
                value={item.select.value}
                onChange={(event) => item.select?.onChange(event.target.value)}
              >
                {item.select.options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </span>
          ) : item.to ? (
            <Link to={item.to}>{item.label}</Link>
          ) : (
            <span aria-current="page">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  )
}
