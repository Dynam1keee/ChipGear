import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { formErrors } from '../api'
import PartPicker from '../components/PartPicker'
import Price from '../components/Price'
import { useAddBuildToCart, useBuild, useClearBuild, useClearSlot, useMe } from '../queries'
import type { SlotName } from '../types'
import { useDocumentTitle } from '../useDocumentTitle'

const SLOTS: { slot: SlotName; label: string }[] = [
  { slot: 'cpu', label: 'Processor' },
  { slot: 'motherboard', label: 'Motherboard' },
  { slot: 'ram', label: 'Memory' },
  { slot: 'gpu', label: 'Graphics card' },
  { slot: 'storage', label: 'Storage' },
  { slot: 'psu', label: 'Power supply' },
  { slot: 'case', label: 'Case' },
  { slot: 'cooling', label: 'Cooler' },
]

export default function BuilderPage() {
  useDocumentTitle('PC Builder - ChipGear')
  const { data: user, isPending: userPending } = useMe()
  const build = useBuild(Boolean(user))
  const clearSlot = useClearSlot()
  const clearBuild = useClearBuild()
  const addToCart = useAddBuildToCart()
  const navigate = useNavigate()
  const [openSlot, setOpenSlot] = useState<SlotName | null>(null)

  if (userPending) return <p>Loading...</p>

  // The builder is only for registered users
  if (!user) {
    return (
      <div className="not-found">
        <h2>Please log in to use the PC builder</h2>
        <Link to="/login?next=/builder">Log in</Link> or <Link to="/register?next=/builder">register</Link>
      </div>
    )
  }

  if (build.isError) return <p className="error">Could not load the build: {build.error.message}</p>
  if (build.isPending) return <p>Loading...</p>

  const { slots, problems, total_price, estimated_power, recommended_psu } = build.data
  const hasParts = Object.values(slots).some((part) => part !== null)
  const cartErrors = formErrors(addToCart.error).non_field_errors ?? []
  const problemsOf = (slot: SlotName) => problems.filter((problem) => problem.slots.includes(slot))

  return (
    <section className="builder">
      <h2 className="page-title">PC builder</h2>

      <div className="builder-layout">
        <div>
          <ul className="slot-list">
            {SLOTS.map(({ slot, label }) => {
              const part = slots[slot]
              return (
                <li key={slot} className="slot" data-slot={slot}>
                  <span className="slot-label">{label}</span>
                  {part ? (
                    <div className="slot-part">
                      <img src={part.image ?? '/icons/image_not_found.jpg'} alt="" width={56} height={56} />
                      <div className="part-info">
                        <strong>{part.name}</strong>
                        <Price product={part} />
                      </div>
                    </div>
                  ) : (
                    <span className="slot-empty">Not chosen</span>
                  )}
                  <div className="slot-actions">
                    <button type="button" onClick={() => setOpenSlot(openSlot === slot ? null : slot)}>
                      {part ? 'Change' : 'Choose'}
                    </button>
                    {part && (
                      <button type="button" disabled={clearSlot.isPending} onClick={() => clearSlot.mutate(slot)}>
                        Remove
                      </button>
                    )}
                  </div>
                  {problemsOf(slot).map((problem) => (
                    <p key={problem.message} className="error slot-problem">
                      {problem.message}
                    </p>
                  ))}
                  {openSlot === slot && <PartPicker slot={slot} label={label} onClose={() => setOpenSlot(null)} />}
                </li>
              )
            })}
          </ul>
        </div>

        <aside className="builder-summary">
          <h3>Your build</h3>
          <p>
            Total: <strong>${total_price}</strong>
          </p>
          {estimated_power !== null && (
            <p>
              Estimated power: <strong>{estimated_power} W</strong>
              <br />
              Recommended power supply: <strong>{recommended_psu} W</strong>
            </p>
          )}
          {problems.length > 0 && (
            <div className="problems">
              <strong>Problems:</strong>
              <ul>
                {problems.map((problem) => (
                  <li key={problem.message} className="error">
                    {problem.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {problems.length === 0 && hasParts && <p className="success">All parts fit together.</p>}
          {cartErrors.map((message) => (
            <p key={message} className="error">
              {message}
            </p>
          ))}
          <button
            type="button"
            className="primary"
            disabled={!hasParts || problems.length > 0 || addToCart.isPending}
            onClick={() => addToCart.mutate(undefined, { onSuccess: () => navigate('/cart') })}
          >
            Add the build to the cart
          </button>
          <button type="button" disabled={!hasParts || clearBuild.isPending} onClick={() => clearBuild.mutate()}>
            Clear the build
          </button>
        </aside>
      </div>
    </section>
  )
}
