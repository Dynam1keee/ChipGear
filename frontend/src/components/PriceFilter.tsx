import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'

interface PriceFilterProps {
  range: { min: number; max: number } // the cheapest and the most expensive product
  min: string // the chosen limits from the address ('' = no limit)
  max: string
  onApply: (min: string, max: string) => void
}

// Price: two number fields and a slider with two handles.
// While a handle moves, only this component changes. The address (and the request to the
// server) changes when the user lets the handle go, leaves a field or presses Enter.
// When the address changes from outside (Reset, the Back button, a new category), the fields follow it.
export default function PriceFilter({ range, min, max, onApply }: PriceFilterProps) {
  const [low, setLow] = useState(min || String(range.min))
  const [high, setHigh] = useState(max || String(range.max))
  const canSlide = range.max > range.min

  // The fields follow the address when it changes. The component is not created again,
  // so a handle that has the focus keeps it while the user moves it with the keyboard.
  const [seen, setSeen] = useState({ min, max, rangeMin: range.min, rangeMax: range.max })
  if (seen.min !== min || seen.max !== max || seen.rangeMin !== range.min || seen.rangeMax !== range.max) {
    setSeen({ min, max, rangeMin: range.min, rangeMax: range.max })
    setLow(min || String(range.min))
    setHigh(max || String(range.max))
  }

  // Keys repeat quickly, so the keyboard change waits a little for the next key
  const timer = useRef<number | undefined>(undefined)
  useEffect(() => () => window.clearTimeout(timer.current), [])
  function applyLater() {
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => apply(), 400)
  }

  function apply(nextLow = low, nextHigh = high) {
    // The ends of the range are "no limit", so they do not go to the address
    onApply(nextLow === String(range.min) ? '' : nextLow, nextHigh === String(range.max) ? '' : nextHigh)
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    apply()
  }

  const span = Math.max(range.max - range.min, 1)
  const percent = (value: string) => ((Number(value) - range.min) / span) * 100
  // when both handles are at the right end, the left one must be on top, or it cannot be moved
  const lowOnTop = Number(low) > range.min + span / 2

  return (
    <form className="filter-form price-filter" onSubmit={handleSubmit}>
      <h4>Price, $</h4>
      <div className="price-inputs">
        <label>
          From
          <input
            name="min_price"
            type="number"
            min={range.min}
            max={range.max}
            step="any"
            value={low}
            onChange={(event) => setLow(event.target.value)}
            onBlur={() => apply()}
          />
        </label>
        <label>
          To
          <input
            name="max_price"
            type="number"
            min={range.min}
            max={range.max}
            step="any"
            value={high}
            onChange={(event) => setHigh(event.target.value)}
            onBlur={() => apply()}
          />
        </label>
      </div>
      {/* Without a submit button the Enter key does nothing in a form with two fields */}
      <button type="submit" hidden>
        Apply
      </button>

      {canSlide && (
        <div className="range-slider">
          <div className="range-track" />
          <div className="range-fill" style={{ left: `${percent(low)}%`, right: `${100 - percent(high)}%` }} />
          <input
            type="range"
            aria-label="Minimum price"
            min={range.min}
            max={range.max}
            value={Number(low)}
            style={{ zIndex: lowOnTop ? 3 : 1 }}
            onChange={(event) => setLow(String(Math.min(Number(event.target.value), Number(high))))}
            onPointerUp={() => apply()}
            onKeyUp={applyLater}
          />
          <input
            type="range"
            aria-label="Maximum price"
            min={range.min}
            max={range.max}
            value={Number(high)}
            style={{ zIndex: 2 }}
            onChange={(event) => setHigh(String(Math.max(Number(event.target.value), Number(low))))}
            onPointerUp={() => apply()}
            onKeyUp={applyLater}
          />
        </div>
      )}
    </form>
  )
}
