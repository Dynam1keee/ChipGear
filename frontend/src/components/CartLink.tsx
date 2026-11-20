import { Link } from 'react-router-dom'
import { useCart } from '../queries'

// The cart link in the header, with the number of items
export default function CartLink() {
  const { data: cart } = useCart()

  return (
    <Link to="/cart" className="cart-link">
      Cart ({cart?.total_quantity ?? 0})
    </Link>
  )
}
