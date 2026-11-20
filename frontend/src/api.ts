import type { Category, Facets, Page, Product, ProductDetail } from './types'

// An error that remembers the HTTP status, so the pages can react to 404
export class ApiError extends Error {
  readonly status: number

  constructor(status: number) {
    super(`Request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
  }
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal })
  if (!response.ok) {
    throw new ApiError(response.status)
  }
  return (await response.json()) as T
}

function withQuery(path: string, params: URLSearchParams): string {
  const query = params.toString()
  return query ? `${path}?${query}` : path
}

export function fetchCategories(signal?: AbortSignal): Promise<Category[]> {
  return getJson<Category[]>('/api/categories/', signal)
}

// The address of the catalog page and the API use the same parameter names, for example
// ?category=keyboards&layout=ANSI&min_price=50, so the address can be sent to the API as it is.
export function fetchProducts(params: URLSearchParams, signal?: AbortSignal): Promise<Page<Product>> {
  return getJson<Page<Product>>(withQuery('/api/products/', params), signal)
}

export function fetchFacets(params: URLSearchParams, signal?: AbortSignal): Promise<Facets> {
  return getJson<Facets>(withQuery('/api/filters/', params), signal)
}

export function fetchProduct(slug: string, signal?: AbortSignal): Promise<ProductDetail> {
  return getJson<ProductDetail>(`/api/products/${encodeURIComponent(slug)}/`, signal)
}
