// Small functions that change the query string of the catalog page.
// They never change the given URLSearchParams: they return a new one.
// Any change of a filter removes "page", because the user should see the first page again.

// Parameters that are not filters: the category and the search text say WHAT we look at,
// the page is a position. The sorting is not here, so the reset button also resets it.
const NOT_FILTERS = ['category', 'q', 'page']

// Add the value if it is not chosen yet, remove it if it is (a checkbox was clicked)
export function toggleValue(params: URLSearchParams, name: string, value: string): URLSearchParams {
  const current = params.getAll(name)
  const updated = current.includes(value) ? current.filter((v) => v !== value) : [...current, value]

  const next = new URLSearchParams(params)
  next.delete(name)
  updated.forEach((v) => next.append(name, v))
  next.delete('page')
  return next
}

// Set a parameter, or remove it if the value is empty
export function setParam(params: URLSearchParams, name: string, value: string): URLSearchParams {
  const next = new URLSearchParams(params)
  if (value) next.set(name, value)
  else next.delete(name)
  next.delete('page')
  return next
}

// True when there is something to reset: a filter or a sorting
export function hasActiveFilters(params: URLSearchParams): boolean {
  return Array.from(params.keys()).some((name) => !NOT_FILTERS.includes(name))
}

// Remove all the filters and the sorting, but keep the category and the search text
// (without both of them the address would be "/", which is the home page)
export function clearFilters(params: URLSearchParams): URLSearchParams {
  const next = new URLSearchParams()
  for (const name of ['category', 'q']) {
    const value = params.get(name)
    if (value) next.set(name, value)
  }
  return next
}

// The page number from the address; wrong values mean the first page
export function parsePage(value: string | null): number {
  const page = Number(value)
  return Number.isInteger(page) && page > 0 ? page : 1
}

// The query string for the products: the page is written only when it is not the first one
export function productParams(params: URLSearchParams): URLSearchParams {
  const next = new URLSearchParams(params)
  next.delete('page')
  const page = parsePage(params.get('page'))
  if (page > 1) next.set('page', String(page))
  return next
}

// The query string for the filter options: they do not depend on the page or the sorting
export function facetParams(params: URLSearchParams): URLSearchParams {
  const next = new URLSearchParams(params)
  next.delete('page')
  next.delete('ordering')
  return next
}
