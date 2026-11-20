import { errorText } from '../api'
import { useAddToCart } from '../queries'
import type { Product } from '../types'

interface AddToCartButtonProps {
  product: Pick<Product, 'id' | 'in_stock'>
}

export default function AddToCartButton({ product }: AddToCartButtonProps) {
  const addToCart = useAddToCart()

  if (!product.in_stock) return null

  return (
    <div className="add-to-cart">
      <button type="button" onClick={() => addToCart.mutate(product.id)} disabled={addToCart.isPending}>
        {addToCart.isPending ? 'Adding...' : 'Add to cart'}
      </button>
      {addToCart.isSuccess && <span className="added">Added</span>}
      {addToCart.isError && <p className="error">{errorText(addToCart.error)}</p>}
    </div>
  )
}
