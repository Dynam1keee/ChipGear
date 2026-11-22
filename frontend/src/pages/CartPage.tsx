import { Link } from 'react-router-dom'
import { errorText } from '../api'
import { useCart, useChangeCartItem, useRemoveCartItem } from '../queries'
import type { CartItem } from '../types'
import { useDocumentTitle } from '../useDocumentTitle'

interface CartItemRowProps {
  item: CartItem
  busy: boolean
  onChange: (quantity: number) => void
  onRemove: () => void
}

function CartItemRow({ item, busy, onChange, onRemove }: CartItemRowProps) {
  const { product, quantity } = item
  const hasDiscount = product.discount > 0

  return (
    <li className="cart-item">
      <Link to={`/products/${product.slug}`}>
        <img src={product.image ?? '/icons/image_not_found.jpg'} alt={product.name} />
      </Link>

      <div className="cart-item-info">
        <Link to={`/products/${product.slug}`}>{product.name}</Link>
        <p className="price">
          <strong>${product.sell_price}</strong>
          {hasDiscount && <s className="price-old">${product.price}</s>}
          {hasDiscount && <span className="discount-tag">-{product.discount}%</span>}
        </p>
        {quantity >= product.quantity && <p className="cart-item-note">The maximum in stock</p>}
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

      <button type="button" className="icon-button" aria-label={`Remove ${product.name}`} title="Remove" disabled={busy} onClick={onRemove}>
        <img src="/icons/delete_icon.svg" alt="" width={22} height={22} />
      </button>
    </li>
  )
}

export default function CartPage() {
  useDocumentTitle('Cart - ChipGear')
  const { data: cart, error, isPending, isError } = useCart()
  const changeItem = useChangeCartItem()
  const removeItem = useRemoveCartItem()

  if (isPending) return <p>Loading...</p>
  if (isError) return <p className="error">Could not load the cart: {error.message}</p>

  if (cart.items.length === 0) {
    return (
      <div className="not-found">
        <h2>Your cart is empty</h2>
        <p>Add something from the catalog, or build a PC from the parts.</p>
        <p>
          <Link to="/" className="button-link">
            Browse the catalog
          </Link>
        </p>
      </div>
    )
  }

  const busy = changeItem.isPending || removeItem.isPending
  // Errors of the last change, for example "Not enough items in stock."
  const mutationError = changeItem.error ?? removeItem.error

  return (
    <section className="cart-page">
      <h2 className="page-title left">Shopping cart</h2>

      <div className="cart-layout">
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

        <aside className="cart-summary">
          <h3>Order summary</h3>
          <p className="cart-total">
            <span>
              {cart.total_quantity} {cart.total_quantity === 1 ? 'item' : 'items'}
            </span>
            <strong>${cart.total_price}</strong>
          </p>
          {mutationError && <p className="error">{errorText(mutationError)}</p>}
          <Link to="/checkout" className="button-link">
            Checkout
          </Link>
          <Link to="/" className="continue-link">
            Continue shopping
          </Link>
        </aside>
      </div>
    </section>
  )
}
