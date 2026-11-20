import type { Category, Page, Product, ProductDetail } from './types'

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

export function fetchCategories(signal?: AbortSignal): Promise<Category[]> {
  return getJson<Category[]>('/api/categories/', signal)
}

export interface ProductParams {
  category?: string
  page?: number
}

export function fetchProducts(
  { category, page }: ProductParams = {},
  signal?: AbortSignal,
): Promise<Page<Product>> {
  const query = new URLSearchParams()
  if (category) query.set('category', category)
  if (page && page > 1) query.set('page', String(page))

  const queryString = query.toString()
  return getJson<Page<Product>>(`/api/products/${queryString ? `?${queryString}` : ''}`, signal)
}

export function fetchProduct(slug: string, signal?: AbortSignal): Promise<ProductDetail> {
  return getJson<ProductDetail>(`/api/products/${encodeURIComponent(slug)}/`, signal)
}
