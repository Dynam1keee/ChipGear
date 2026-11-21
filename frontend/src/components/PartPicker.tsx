import { useState } from 'react'
import { formErrors } from '../api'
import { usePutPart, useSlotOptions } from '../queries'
import type { SlotName } from '../types'
import Price from './Price'

interface PartPickerProps {
  slot: SlotName
  label: string
  onClose: () => void
}

// The list of the parts for one slot. A part that does not fit the chosen parts
// is shown with the reasons, and it cannot be chosen.
export default function PartPicker({ slot, label, onClose }: PartPickerProps) {
  const options = useSlotOptions(slot)
  const put = usePutPart()
  const [onlyCompatible, setOnlyCompatible] = useState(false)
  const errors = formErrors(put.error)

  const parts = (options.data ?? []).filter((part) => !onlyCompatible || part.compatible)

  return (
    <section className="part-picker" aria-label={`Choose: ${label}`}>
      <header>
        <h3>Choose: {label}</h3>
        <label className="check-field">
          <input type="checkbox" checked={onlyCompatible} onChange={(event) => setOnlyCompatible(event.target.checked)} />
          <span>Only compatible</span>
        </label>
        <button type="button" onClick={onClose}>
          Close
        </button>
      </header>

      {errors.non_field_errors?.map((message) => (
        <p key={message} className="error">
          {message}
        </p>
      ))}
      {options.isPending && <p>Loading...</p>}
      {options.isError && <p className="error">Could not load the parts: {options.error.message}</p>}
      {options.data && parts.length === 0 && <p>No parts to show.</p>}

      <ul className="part-list">
        {parts.map((part) => (
          <li key={part.id} className={part.compatible ? 'part' : 'part incompatible'}>
            <img src={part.image ?? '/icons/image_not_found.jpg'} alt="" width={64} height={64} loading="lazy" />
            <div className="part-info">
              <strong>{part.name}</strong>
              <Price product={part} />
              {part.reasons.map((reason) => (
                <span key={reason} className="error">
                  {reason}
                </span>
              ))}
            </div>
            <button
              type="button"
              disabled={!part.compatible || put.isPending}
              onClick={() => put.mutate({ slot, productId: part.id }, { onSuccess: onClose })}
            >
              Choose
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
