import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { fetchCategories, fetchFacets, fetchProduct, fetchProducts } from './api'

// useQuery loads data and gives back { data, error, isPending, ... }.
// The queryKey is the "name" of the data: the same key means the same cached data,
// and when the key changes, the data is loaded again.
// TanStack Query passes an AbortSignal, so an outdated request is cancelled.

export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: ({ signal }) => fetchCategories(signal),
    staleTime: 5 * 60 * 1000, // categories rarely change: do not reload for 5 minutes
  })
}

// params is the query string of the catalog page. A string is used in the key,
// because React Query compares keys by value and URLSearchParams has no useful value.
export function useProducts(params: URLSearchParams) {
  return useQuery({
    queryKey: ['products', params.toString()],
    queryFn: ({ signal }) => fetchProducts(params, signal),
    // While the next page loads, keep showing the previous one (no flicker)
    placeholderData: keepPreviousData,
  })
}

export function useFacets(params: URLSearchParams) {
  return useQuery({
    queryKey: ['facets', params.toString()],
    queryFn: ({ signal }) => fetchFacets(params, signal),
    placeholderData: keepPreviousData,
  })
}

export function useProduct(slug: string) {
  return useQuery({
    queryKey: ['product', slug],
    queryFn: ({ signal }) => fetchProduct(slug, signal),
  })
}
