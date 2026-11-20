import type { Category, Page, Product } from './types'

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }
  return (await response.json()) as T
}

export function fetchCategories(): Promise<Category[]> {
  return getJson<Category[]>('/api/categories/')
}

export interface ProductParams {
  category?: string
  page?: number
}

export function fetchProducts({ category, page }: ProductParams = {}): Promise<Page<Product>> {
  const query = new URLSearchParams()
  if (category) query.set('category', category)
  if (page && page > 1) query.set('page', String(page))

  const queryString = query.toString()
  return getJson<Page<Product>>(`/api/products/${queryString ? `?${queryString}` : ''}`)
}
