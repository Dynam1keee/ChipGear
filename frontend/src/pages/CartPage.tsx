import { Link } from 'react-router-dom'
import { errorText } from '../api'
import Price from '../components/Price'
import { useCart, useChangeCartItem, useRemoveCartItem } from '../queries'
import type { CartItem } from '../types'

interface CartItemRowProps {
  item: CartItem
  busy: boolean
  onChange: (quantity: number) => void
  onRemove: () => void
}

function CartItemRow({ item, busy, onChange, onRemove }: CartItemRowProps) {
  const { product, quantity } = item

  return (
    <li className="cart-item">
      {product.image && <img src={product.image} alt={product.name} />}
      <div className="cart-item-info">
        <Link to={`/products/${product.slug}`}>{product.name}</Link>
        <Price product={product} />
      </div>
      <div className="quantity-controls">
        <button
          type="button"
          aria-label="Decrease quantity"
          disabled={busy || quantity <= 1}
          onClick={() => onChange(quantity - 1)}
        >
          &minus;
        </button>
        <span aria-label="Quantity">{quantity}</span>
        <button
          type="button"
          aria-label="Increase quantity"
          disabled={busy || quantity >= product.quantity}
          onClick={() => onChange(quantity + 1)}
        >
          +
        </button>
      </div>
      <strong className="cart-item-total">${item.total}</strong>
      <button type="button" disabled={busy} onClick={onRemove}>
        Remove
      </button>
    </li>
  )
}

export default function CartPage() {
  const { data: cart, error, isPending, isError } = useCart()
  const changeItem = useChangeCartItem()
  const removeItem = useRemoveCartItem()

  if (isPending) return <p>Loading...</p>
  if (isError) return <p className="error">Could not load the cart: {error.message}</p>

  if (cart.items.length === 0) {
    return (
      <div className="not-found">
        <h2>Your cart is empty</h2>
        <Link to="/">Back to the catalog</Link>
      </div>
    )
  }

  const busy = changeItem.isPending || removeItem.isPending
  // Errors of the last change, for example "Not enough items in stock."
  const mutationError = changeItem.error ?? removeItem.error

  return (
    <section className="cart-page">
      <h2>Your cart</h2>
      <ul className="cart-items">
        {cart.items.map((item) => (
          <CartItemRow
            key={item.id}
            item={item}
            busy={busy}
            onChange={(quantity) => changeItem.mutate({ itemId: item.id, quantity })}
            onRemove={() => removeItem.mutate(item.id)}
          />
        ))}
      </ul>

      {mutationError && <p className="error">{errorText(mutationError)}</p>}

      <p className="cart-total">
        {cart.total_quantity} {cart.total_quantity === 1 ? 'item' : 'items'}, total:{' '}
        <strong>${cart.total_price}</strong>
      </p>
    </section>
  )
}
