import type { Build, Cart, Category, Facets, Page, Order, PartOption, Product, ProductDetail, SlotName, User } from './types'

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

// The errors of a form that the server rejected (400): {"username": ["This field is required."]}.
// The errors of the whole form (for example a wrong password) are under "non_field_errors".
export function formErrors(error: unknown): Record<string, string[]> {
  if (!error) return {}

  if (error instanceof ApiError && error.status === 400 && error.details && typeof error.details === 'object') {
    const result: Record<string, string[]> = {}
    for (const [field, messages] of Object.entries(error.details as Record<string, unknown>)) {
      // DRF gives a list of messages, but sometimes a single string
      const list = Array.isArray(messages) ? messages : [messages]
      result[field] = list.filter((message): message is string => typeof message === 'string')
    }
    return result
  }

  return { non_field_errors: [errorText(error)] }
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
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
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

// Discovery: the top sales, the products bought together, the history of views
export function fetchTopSales(signal?: AbortSignal): Promise<Product[]> {
  return request<Product[]>('/api/top-sales/', { signal })
}

export function fetchRelated(slug: string, signal?: AbortSignal): Promise<Product[]> {
  return request<Product[]>(`/api/products/${encodeURIComponent(slug)}/related/`, { signal })
}

export function fetchRecentlyViewed(exclude?: string, signal?: AbortSignal): Promise<Product[]> {
  const query = exclude ? `?exclude=${encodeURIComponent(exclude)}` : ''
  return request<Product[]>(`/api/recently-viewed/${query}`, { signal })
}

export function markViewed(slug: string): Promise<void> {
  return request<void>(`/api/products/${encodeURIComponent(slug)}/view/`, { method: 'POST' })
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

// Users. The server keeps the login in a session cookie.
export async function fetchMe(signal?: AbortSignal): Promise<User | null> {
  const data = await request<{ user: User | null }>('/api/auth/me/', { signal })
  return data.user
}

export interface Credentials {
  username: string
  password: string
}

export async function login(credentials: Credentials): Promise<User> {
  const data = await request<{ user: User }>('/api/auth/login/', { method: 'POST', body: credentials })
  return data.user
}

export interface Registration {
  first_name: string
  last_name: string
  username: string
  email: string
  password1: string
  password2: string
}

// The server creates the user and logs them in at once
export async function register(data: Registration): Promise<User> {
  const result = await request<{ user: User }>('/api/auth/register/', { method: 'POST', body: data })
  return result.user
}

export function logout(): Promise<void> {
  return request<void>('/api/auth/logout/', { method: 'POST' })
}

// Orders (only for logged in users)
export interface NewOrder {
  phone_number: string
  requires_delivery: boolean
  delivery_address: string
  payment_on_get: boolean
}

export function fetchOrders(signal?: AbortSignal): Promise<Order[]> {
  return request<Order[]>('/api/orders/', { signal })
}

export function createOrder(order: NewOrder): Promise<Order> {
  return request<Order>('/api/orders/', { method: 'POST', body: order })
}

// The profile: the name, the username and the email of the logged in user
export type Profile = Pick<User, 'first_name' | 'last_name' | 'username' | 'email'>

export async function updateProfile(profile: Profile): Promise<User> {
  const data = await request<{ user: User }>('/api/auth/me/', { method: 'PATCH', body: profile })
  return data.user
}

// PC builder (only for logged in users)
export function fetchBuild(signal?: AbortSignal): Promise<Build> {
  return request<Build>('/api/builder/', { signal })
}

export function putPart(slot: SlotName, productId: number): Promise<Build> {
  return request<Build>(`/api/builder/${slot}/`, { method: 'PUT', body: { product_id: productId } })
}

export function clearSlot(slot: SlotName): Promise<Build> {
  return request<Build>(`/api/builder/${slot}/`, { method: 'DELETE' })
}

export function clearBuild(): Promise<Build> {
  return request<Build>('/api/builder/', { method: 'DELETE' })
}

export function fetchOptions(slot: SlotName, signal?: AbortSignal): Promise<PartOption[]> {
  return request<PartOption[]>(`/api/builder/${slot}/options/`, { signal })
}

// The parts go to the cart; the answer is the whole cart
export function addBuildToCart(): Promise<Cart> {
  return request<Cart>('/api/builder/add-to-cart/', { method: 'POST' })
}
