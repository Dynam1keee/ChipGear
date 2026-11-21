import { errorText } from '../api'
import { useAddToCart } from '../queries'
import type { Product } from '../types'

interface AddToCartButtonProps {
  product: Pick<Product, 'id' | 'in_stock'>
  // "icon": only the cart icon (for the cards); otherwise a button with a text
  variant?: 'icon' | 'text'
}

export default function AddToCartButton({ product, variant = 'text' }: AddToCartButtonProps) {
  const addToCart = useAddToCart()

  if (!product.in_stock) return null

  return (
    <div className="add-to-cart">
      {variant === 'icon' ? (
        <button
          type="button"
          className="icon-button"
          aria-label="Add to cart"
          title="Add to cart"
          onClick={() => addToCart.mutate(product.id)}
          disabled={addToCart.isPending}
        >
          <img src="/icons/cart_add.svg" alt="" width={50} height={50} />
        </button>
      ) : (
        <button type="button" onClick={() => addToCart.mutate(product.id)} disabled={addToCart.isPending}>
          {addToCart.isPending ? 'Adding...' : 'Add to cart'}
        </button>
      )}
      {addToCart.isSuccess && <span className="added">Added</span>}
      {addToCart.isError && <p className="error">{errorText(addToCart.error)}</p>}
    </div>
  )
}
