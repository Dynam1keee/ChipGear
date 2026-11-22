import { useEffect, useId, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useCategories, useSuggestions } from '../queries'
import { useDismiss } from '../useClickOutside'

const SUGGEST_DELAY = 250 // ms to wait after the last key before asking the server

// The value follows the input with a delay, so a fast typist sends one request, not one per letter
function useDebounced(value: string, delay: number): string {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

// The search form of the header: a category and a text. It opens the catalog with
// the address /?category=...&q=..., the same address that the catalog page reads.
// While the user types, a dropdown offers up to four matching products.
export default function HeaderSearch() {
  const { data: categories = [] } = useCategories()
  const [searchParams] = useSearchParams()
  const category = searchParams.get('category') ?? ''
  const q = searchParams.get('q') ?? ''

  // key: when the address or the list of categories changes, the form starts again with the new values
  return <SearchForm key={`${category}|${q}|${categories.length}`} initialCategory={category} initialText={q} />
}

interface SearchFormProps {
  initialCategory: string
  initialText: string
}

function SearchForm({ initialCategory, initialText }: SearchFormProps) {
  const { data: categories = [] } = useCategories()
  const navigate = useNavigate()
  const [category, setCategory] = useState(initialCategory)
  const [text, setText] = useState(initialText)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1) // the highlighted suggestion (arrow keys), -1 = none
  const rootRef = useRef<HTMLFormElement>(null)
  const listId = useId()

  const typed = text.trim()
  const suggestions = useSuggestions(useDebounced(typed, SUGGEST_DELAY), category)
  // while the answer for the latest text has not come, do not show the old one for a different text
  const items = typed.length >= 2 ? (suggestions.data ?? []) : []
  const showList = open && items.length > 0

  useDismiss(rootRef, open, () => setOpen(false))

  function search() {
    const params = new URLSearchParams()
    if (category) params.set('category', category)
    if (typed) params.set('q', typed)
    const query = params.toString()
    setOpen(false)
    navigate(query ? `/?${query}` : '/')
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const chosen = items[active]
    if (showList && chosen) {
      setOpen(false)
      navigate(`/products/${chosen.slug}`)
    } else {
      search()
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!showList) return
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActive((index) => (index + 1) % items.length)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((index) => (index <= 0 ? items.length - 1 : index - 1))
    }
  }

  return (
    <form className="header-search" role="search" onSubmit={handleSubmit} ref={rootRef}>
      <select name="category" value={category} aria-label="Category" onChange={(event) => setCategory(event.target.value)}>
        <option value="">All categories</option>
        {categories.map((item) => (
          <option key={item.slug} value={item.slug}>
            {item.name}
          </option>
        ))}
      </select>
      <input
        name="q"
        type="search"
        role="combobox"
        placeholder="Search..."
        aria-label="Search"
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={showList && active >= 0 ? `${listId}-${active}` : undefined}
        autoComplete="off"
        value={text}
        onChange={(event) => {
          setText(event.target.value)
          setActive(-1)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKeyDown}
      />
      <button type="submit" aria-label="Search">
        <img src="/icons/search_icon.svg" alt="" width={25} height={25} />
      </button>

      {showList && (
        <ul className="suggestions" id={listId} role="listbox">
          {items.map((product, index) => (
            <li key={product.id} id={`${listId}-${index}`} role="option" aria-selected={index === active}>
              <Link to={`/products/${product.slug}`} onClick={() => setOpen(false)} tabIndex={-1}>
                <img src={product.image ?? '/icons/image_not_found.jpg'} alt="" width={44} height={44} />
                <span>{product.name}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </form>
  )
}
