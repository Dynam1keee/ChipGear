import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { formErrors } from '../api'
import FormField from '../components/FormField'
import { useCart, useCreateOrder, useMe } from '../queries'

export default function CheckoutPage() {
  const { data: user, isPending: userPending } = useMe()
  const { data: cart, isPending: cartPending } = useCart()
  const createOrder = useCreateOrder()
  const navigate = useNavigate()
  const [delivery, setDelivery] = useState(false)
  const errors = formErrors(createOrder.error)

  if (userPending || cartPending) return <p>Loading...</p>

  // Only a logged in user can order
  if (!user) {
    return (
      <div className="not-found">
        <h2>Please log in to place an order</h2>
        <Link to="/login?next=/checkout">Log in</Link> or <Link to="/register?next=/checkout">register</Link>
      </div>
    )
  }

  if (cart.items.length === 0) {
    return (
      <div className="not-found">
        <h2>Your cart is empty</h2>
        <Link to="/">Back to the catalog</Link>
      </div>
    )
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    createOrder.mutate(
      {
        phone_number: String(form.get('phone_number') ?? ''),
        requires_delivery: delivery,
        delivery_address: delivery ? String(form.get('delivery_address') ?? '') : '',
        payment_on_get: form.get('payment_on_get') === 'on',
      },
      { onSuccess: () => navigate('/orders') },
    )
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>Place an order</h2>
      <p>
        {cart.total_quantity} {cart.total_quantity === 1 ? 'item' : 'items'}, total:{' '}
        <strong>${cart.total_price}</strong>
      </p>
      {errors.non_field_errors?.map((message) => (
        <p key={message} className="error">
          {message}
        </p>
      ))}
      <FormField label="Phone number (10 digits)" name="phone_number" type="tel" autoComplete="tel" errors={errors.phone_number} />
      <label className="check-field">
        <input type="checkbox" checked={delivery} onChange={(event) => setDelivery(event.target.checked)} />
        <span>Delivery</span>
      </label>
      {delivery && (
        <label className="form-field">
          <span>Delivery address</span>
          <textarea name="delivery_address" rows={2} required aria-invalid={Boolean(errors.delivery_address)} />
          {errors.delivery_address?.map((message) => (
            <span key={message} className="error">
              {message}
            </span>
          ))}
        </label>
      )}
      <label className="check-field">
        <input type="checkbox" name="payment_on_get" />
        <span>Pay on receipt</span>
      </label>
      <button type="submit" className="primary" disabled={createOrder.isPending}>
        {createOrder.isPending ? 'Placing the order...' : 'Place the order'}
      </button>
    </form>
  )
}
