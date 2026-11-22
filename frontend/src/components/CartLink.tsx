import { Link, useLocation } from 'react-router-dom'
import { errorText } from '../api'
import { useCart, useRemoveCartItem } from '../queries'

// The cart icon in the header with the number of items.
// On a computer, hovering (or focusing) it shows the items; a phone just opens the cart page.
export default function CartLink() {
  const { data: cart } = useCart()
  const removeItem = useRemoveCartItem()
  const { pathname } = useLocation()
  const count = cart?.total_quantity ?? 0
  // the pages that show the whole cart do not need the small list
  const showList = cart !== undefined && cart.items.length > 0 && pathname !== '/cart' && pathname !== '/checkout'

  return (
    <div className="cart-wrap">
      <Link to="/cart" className="cart-link" aria-label={`Cart, ${count} ${count === 1 ? 'item' : 'items'}`}>
        <img src="/icons/cart_icon.svg" alt="" width={25} height={25} />
        <span className={count > 0 ? 'cart-badge' : 'cart-badge empty'}>{count}</span>
      </Link>

      {showList && (
        <div className="cart-popover">
          <ul>
            {cart.items.map((item) => (
              <li key={item.id}>
                <Link to={`/products/${item.product.slug}`}>
                  <img src={item.product.image ?? '/icons/image_not_found.jpg'} alt="" width={56} height={56} />
                </Link>
                <div>
                  <Link to={`/products/${item.product.slug}`}>{item.product.name}</Link>
                  <p>
                    ${item.product.sell_price} &times; <strong>{item.quantity}</strong>
                  </p>
                </div>
                <button
                  type="button"
                  className="icon-button"
                  aria-label={`Remove ${item.product.name}`}
                  disabled={removeItem.isPending}
                  onClick={() => removeItem.mutate(item.id)}
                >
                  <img src="/icons/delete_icon.svg" alt="" width={16} height={16} />
                </button>
              </li>
            ))}
          </ul>
          {removeItem.isError && <p className="error">{errorText(removeItem.error)}</p>}
          <p className="cart-popover-total">
            Total <strong>${cart.total_price}</strong>
          </p>
          <Link to="/cart" className="button-link">
            Go to cart
          </Link>
        </div>
      )}
    </div>
  )
}
