import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  addToCart,
  changeCartItem,
  fetchCart,
  fetchCategories,
  addBuildToCart,
  clearBuild,
  clearSlot,
  createOrder,
  fetchFacets,
  fetchBuild,
  fetchMe,
  fetchOptions,
  fetchOrders,
  fetchProduct,
  fetchRecentlyViewed,
  fetchRelated,
  fetchSuggestions,
  fetchTopSales,
  markViewed,
  fetchProducts,
  login,
  logout,
  register,
  putPart,
  removeCartItem,
  updateProfile,
} from './api'
import type { Credentials, NewOrder, Profile, Registration } from './api'
import type { Build, Cart, SlotName, User } from './types'

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

// Top sales stay empty until the shop has enough sales; the home page then hides the block
export function useTopSales() {
  return useQuery({
    queryKey: ['top-sales'],
    queryFn: ({ signal }) => fetchTopSales(signal),
    staleTime: 60 * 1000,
  })
}

export function useRelated(slug: string) {
  return useQuery({
    queryKey: ['related', slug],
    queryFn: ({ signal }) => fetchRelated(slug, signal),
    staleTime: 60 * 1000,
  })
}

// The products for the dropdown of the search box. The text is already debounced by the caller.
export function useSuggestions(text: string, category: string) {
  return useQuery({
    queryKey: ['suggestions', category, text],
    queryFn: ({ signal }) => fetchSuggestions(text, category, signal),
    enabled: text.length >= 2,
    staleTime: 30 * 1000,
  })
}

// exclude: the product that is open now, it is not shown in its own history
export function useRecentlyViewed(exclude?: string) {
  return useQuery({
    queryKey: ['recently-viewed', exclude ?? null],
    queryFn: ({ signal }) => fetchRecentlyViewed(exclude, signal),
  })
}

// Remember that the product was opened. The history changes, so its queries are reloaded.
export function useMarkViewed() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (slug: string) => markViewed(slug),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['recently-viewed'] }),
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

// --- the logged in user ---
// The data is the user, or null for a guest.

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: ({ signal }) => fetchMe(signal),
    staleTime: Infinity, // it changes only when we log in or out, and then we update it ourselves
  })
}

// After a login or a logout the cart on the server is another one (the guest cart is merged
// into the user's cart), so we ask for the cart again.
function useAuthMutation<Variables, Result>(
  mutationFn: (variables: Variables) => Promise<Result>,
  getUser: (result: Result) => User | null,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: (result) => {
      queryClient.setQueryData(['me'], getUser(result))
      void queryClient.invalidateQueries({ queryKey: ['cart'] })
      // the builder and the orders belong to a user
      void queryClient.invalidateQueries({ queryKey: ['builder'] })
      void queryClient.invalidateQueries({ queryKey: ['orders'] })
      // the history of views is kept per user, a guest has its own
      void queryClient.invalidateQueries({ queryKey: ['recently-viewed'] })
    },
  })
}

export function useLogin() {
  return useAuthMutation((credentials: Credentials) => login(credentials), (user) => user)
}

export function useLogout() {
  return useAuthMutation(() => logout(), () => null)
}

export function useRegister() {
  return useAuthMutation((data: Registration) => register(data), (user) => user)
}

// --- orders ---

export function useOrders(enabled: boolean) {
  return useQuery({
    queryKey: ['orders'],
    queryFn: ({ signal }) => fetchOrders(signal),
    enabled, // guests have no orders: the server would answer 403
  })
}

// An order takes the products from the cart and from the stock, so both are changed on the server
export function useCreateOrder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (order: NewOrder) => createOrder(order),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cart'] })
      void queryClient.invalidateQueries({ queryKey: ['orders'] })
      void queryClient.invalidateQueries({ queryKey: ['products'] })
      void queryClient.invalidateQueries({ queryKey: ['product'] })
    },
  })
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (profile: Profile) => updateProfile(profile),
    // The answer of the server is the updated user, so the header shows the new name at once
    onSuccess: (user) => queryClient.setQueryData(['me'], user),
  })
}

// --- PC builder ---
// All the builder queries start with 'builder', so one invalidate refreshes the build and the options.

export function useBuild(enabled: boolean) {
  return useQuery({
    queryKey: ['builder'],
    queryFn: ({ signal }) => fetchBuild(signal),
    enabled,
  })
}

export function useSlotOptions(slot: SlotName | null) {
  return useQuery({
    queryKey: ['builder', 'options', slot],
    queryFn: ({ signal }) => fetchOptions(slot as SlotName, signal),
    enabled: slot !== null,
  })
}

// Every change of the build answers with the whole build. We keep it, and the lists of
// options are asked again, because what fits depends on the chosen parts.
function useBuildMutation<Variables>(mutationFn: (variables: Variables) => Promise<Build>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: (build) => {
      queryClient.setQueryData(['builder'], build)
      void queryClient.invalidateQueries({ queryKey: ['builder', 'options'] })
    },
  })
}

export function usePutPart() {
  return useBuildMutation(({ slot, productId }: { slot: SlotName; productId: number }) => putPart(slot, productId))
}

export function useClearSlot() {
  return useBuildMutation((slot: SlotName) => clearSlot(slot))
}

export function useClearBuild() {
  return useBuildMutation(() => clearBuild())
}

export function useAddBuildToCart() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => addBuildToCart(),
    onSuccess: (cart) => queryClient.setQueryData(['cart'], cart),
  })
}
