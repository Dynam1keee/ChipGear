import type { FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useCategories } from '../queries'

// The search form of the header: a category and a text. It opens the catalog with
// the address /?category=...&q=..., the same address that the catalog page reads.
export default function HeaderSearch() {
  const { data: categories = [] } = useCategories()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const category = searchParams.get('category') ?? ''
  const q = searchParams.get('q') ?? ''

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const params = new URLSearchParams()
    const chosenCategory = String(form.get('category') ?? '')
    const text = String(form.get('q') ?? '').trim()
    if (chosenCategory) params.set('category', chosenCategory)
    if (text) params.set('q', text)
    const query = params.toString()
    navigate(query ? `/?${query}` : '/')
  }

  return (
    // key: when the address or the list of categories changes, the form shows the new values
    <form className="header-search" role="search" onSubmit={handleSubmit} key={`${category}|${q}|${categories.length}`}>
      <select name="category" defaultValue={category} aria-label="Category">
        <option value="">All categories</option>
        {categories.map((item) => (
          <option key={item.slug} value={item.slug}>
            {item.name}
          </option>
        ))}
      </select>
      <input name="q" type="search" placeholder="Search..." defaultValue={q} aria-label="Search" autoComplete="off" />
      <button type="submit" aria-label="Search">
        <img src="/icons/search_icon.svg" alt="" width={25} height={25} />
      </button>
    </form>
  )
}
