import type { Cart, Category, Facets, Page, Product, ProductDetail } from './types'

// An error that remembers the HTTP status (and the JSON the server sent), so the
// pages can react to 404 or show the reason of a 400
export class ApiError extends Error {
  readonly status: number
  readonly details: unknown

  constructor(status: number, details: unknown = null) {
    super(`Request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

// A short text for people, for example "Not enough items in stock."
export function errorText(error: unknown): string {
  if (error instanceof ApiError && error.details && typeof error.details === 'object') {
    const first = Object.values(error.details as Record<string, unknown>)[0]
    const message = Array.isArray(first) ? first[0] : first
    if (typeof message === 'string') return message
  }
  return error instanceof Error ? error.message : 'Unknown error'
}

// Django keeps the CSRF token in a cookie. Requests that change data must send it back
// in the X-CSRFToken header, otherwise Django answers 403.
function getCookie(name: string): string | null {
  const row = document.cookie.split('; ').find((part) => part.startsWith(`${name}=`))
  return row ? decodeURIComponent(row.slice(name.length + 1)) : null
}

async function csrfToken(): Promise<string | null> {
  let token = getCookie('csrftoken')
  if (!token) {
    await fetch('/api/auth/csrf/', { credentials: 'same-origin' }) // this sets the cookie
    token = getCookie('csrftoken')
  }
  return token
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
}

async function request<T>(url: string, { method = 'GET', body, signal }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET') {
    const token = await csrfToken()
    if (token) headers['X-CSRFToken'] = token
  }

  const response = await fetch(url, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    credentials: 'same-origin', // send the session cookie
    signal,
  })

  if (!response.ok) {
    let details: unknown = null
    try {
      details = await response.json()
    } catch {
      // the error response has no JSON (for example the CSRF error page)
    }
    throw new ApiError(response.status, details)
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
}

function withQuery(path: string, params: URLSearchParams): string {
  const query = params.toString()
  return query ? `${path}?${query}` : path
}

export function fetchCategories(signal?: AbortSignal): Promise<Category[]> {
  return request<Category[]>('/api/categories/', { signal })
}

// The address of the catalog page and the API use the same parameter names, for example
// ?category=keyboards&layout=ANSI&min_price=50, so the address can be sent to the API as it is.
export function fetchProducts(params: URLSearchParams, signal?: AbortSignal): Promise<Page<Product>> {
  return request<Page<Product>>(withQuery('/api/products/', params), { signal })
}

export function fetchFacets(params: URLSearchParams, signal?: AbortSignal): Promise<Facets> {
  return request<Facets>(withQuery('/api/filters/', params), { signal })
}

export function fetchProduct(slug: string, signal?: AbortSignal): Promise<ProductDetail> {
  return request<ProductDetail>(`/api/products/${encodeURIComponent(slug)}/`, { signal })
}

// Cart: every call returns the whole cart
export function fetchCart(signal?: AbortSignal): Promise<Cart> {
  return request<Cart>('/api/cart/', { signal })
}

export function addToCart(productId: number): Promise<Cart> {
  return request<Cart>('/api/cart/items/', { method: 'POST', body: { product_id: productId } })
}

export function changeCartItem(itemId: number, quantity: number): Promise<Cart> {
  return request<Cart>(`/api/cart/items/${itemId}/`, { method: 'PATCH', body: { quantity } })
}

export function removeCartItem(itemId: number): Promise<Cart> {
  return request<Cart>(`/api/cart/items/${itemId}/`, { method: 'DELETE' })
}
