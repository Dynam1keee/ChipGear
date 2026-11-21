import { Link } from 'react-router-dom'
import { useMe, useOrders } from '../queries'

export default function OrdersPage() {
  const { data: user, isPending: userPending } = useMe()
  const orders = useOrders(Boolean(user))

  if (userPending) return <p>Loading...</p>

  if (!user) {
    return (
      <div className="not-found">
        <h2>Please log in to see your orders</h2>
        <Link to="/login?next=/orders">Log in</Link>
      </div>
    )
  }

  if (orders.isError) return <p className="error">Could not load the orders: {orders.error.message}</p>
  if (orders.isPending) return <p>Loading...</p>

  if (orders.data.length === 0) {
    return (
      <div className="not-found">
        <h2>You have no orders yet</h2>
        <Link to="/">Back to the catalog</Link>
      </div>
    )
  }

  return (
    <section className="orders-page">
      <h2>Your orders</h2>
      {orders.data.map((order) => (
        <article key={order.id} className="order">
          <header>
            <strong>Order #{order.id}</strong>
            <span>{new Date(order.created_timestamp).toLocaleDateString()}</span>
            <span className="order-status">{order.status}</span>
          </header>
          <ul>
            {order.items.map((item) => (
              <li key={item.id}>
                {item.name} &times; {item.quantity} <span>${item.total}</span>
              </li>
            ))}
          </ul>
          <p>
            {order.requires_delivery ? `Delivery: ${order.delivery_address}` : 'Pickup'}
            {' · '}
            {order.payment_on_get ? 'Pay on receipt' : 'Paid online'}
          </p>
          <p>
            Total: <strong>${order.total_price}</strong>
          </p>
        </article>
      ))}
    </section>
  )
}
