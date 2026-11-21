import { Link } from 'react-router-dom'
import { useCart } from '../queries'

// The cart icon in the header, with the number of items
export default function CartLink() {
  const { data: cart } = useCart()
  const count = cart?.total_quantity ?? 0

  return (
    <Link to="/cart" className="cart-link" aria-label="Cart">
      <img src="/icons/cart_icon.svg" alt="" width={25} height={25} />
      <span className={count > 0 ? 'cart-badge' : 'cart-badge empty'}>{count}</span>
    </Link>
  )
}
