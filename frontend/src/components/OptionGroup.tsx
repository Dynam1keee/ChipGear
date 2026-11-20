import type { FilterOption } from '../types'

interface OptionGroupProps {
  title: string
  options: FilterOption[]
  selected: string[] // the values chosen now (as text, like in the address)
  onToggle: (value: string) => void
}

function formatOption(value: FilterOption['value']): string {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return String(value)
}

// A group of checkboxes, for example all the manufacturers
export default function OptionGroup({ title, options, selected, onToggle }: OptionGroupProps) {
  if (options.length === 0) return null

  return (
    <details className="option-group" open>
      <summary>{title}</summary>
      {options.map((option) => {
        const value = String(option.value) // the same text goes into the address
        const checked = selected.includes(value)
        // A choice that gives no products is disabled, unless it is already chosen
        const disabled = option.count === 0 && !checked

        return (
          <label key={value} className={disabled ? 'disabled' : undefined}>
            <input
              type="checkbox"
              checked={checked}
              disabled={disabled}
              onChange={() => onToggle(value)}
            />
            {formatOption(option.value)}
            <span className="option-count">{option.count}</span>
          </label>
        )
      })}
    </details>
  )
}
