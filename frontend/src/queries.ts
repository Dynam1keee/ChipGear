import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  addToCart,
  changeCartItem,
  fetchCart,
  fetchCategories,
  fetchFacets,
  fetchProduct,
  fetchProducts,
  removeCartItem,
} from './api'
import type { Cart } from './types'

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

// --- cart ---
// A query only reads data. A mutation changes data on the server (add, change, remove).
// Every cart response is the whole cart, so after a mutation we simply put it into the cache
// under the key ['cart']: everything that shows the cart (the header, the cart page) updates at once.

export function useCart() {
  return useQuery({
    queryKey: ['cart'],
    queryFn: ({ signal }) => fetchCart(signal),
  })
}

function useCartMutation<Variables>(mutationFn: (variables: Variables) => Promise<Cart>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: (cart) => queryClient.setQueryData(['cart'], cart),
  })
}

export function useAddToCart() {
  return useCartMutation((productId: number) => addToCart(productId))
}

export function useChangeCartItem() {
  return useCartMutation(({ itemId, quantity }: { itemId: number; quantity: number }) =>
    changeCartItem(itemId, quantity),
  )
}

export function useRemoveCartItem() {
  return useCartMutation((itemId: number) => removeCartItem(itemId))
}
