import type { FormEvent } from 'react'
import { clearFilters, hasActiveFilters, setParam, toggleValue } from '../filters'
import type { Facets } from '../types'
import OptionGroup from './OptionGroup'

interface FilterSidebarProps {
  facets: Facets
  params: URLSearchParams // the current query string of the page
  onChange: (next: URLSearchParams) => void
}

const SORT_OPTIONS = [
  { value: 'default', label: 'Default order' },
  { value: 'price', label: 'Price: Low to High' },
  { value: '-price', label: 'Price: High to Low' },
  { value: 'name', label: 'Name: A to Z' },
  { value: '-name', label: 'Name: Z to A' },
]

export default function FilterSidebar({ facets, params, onChange }: FilterSidebarProps) {
  const minPrice = params.get('min_price') ?? ''
  const maxPrice = params.get('max_price') ?? ''
  const ordering = params.get('ordering') ?? 'default'

  function handlePrice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const min = String(data.get('min_price') ?? '')
    const max = String(data.get('max_price') ?? '')
    onChange(setParam(setParam(params, 'min_price', min), 'max_price', max))
  }

  return (
    <details className="filter-sidebar" open>
      <summary className="filters-title">Filters</summary>
      <fieldset className="sort-options">
        <legend>Sort by:</legend>
        {SORT_OPTIONS.map((option) => (
          <label key={option.value}>
            <input
              type="radio"
              name="ordering"
              checked={ordering === option.value}
              onChange={() => onChange(setParam(params, 'ordering', option.value === 'default' ? '' : option.value))}
            />
            {option.label}
          </label>
        ))}
      </fieldset>

      <form onSubmit={handlePrice} className="filter-form">
        <h4>Price, $</h4>
        <div className="price-inputs">
          <label>
            From
            <input
              key={`min-${minPrice}`}
              name="min_price"
              type="number"
              min={0}
              step="any"
              placeholder={String(facets.price_range.min)}
              defaultValue={minPrice}
            />
          </label>
          <label>
            To
            <input
              key={`max-${maxPrice}`}
              name="max_price"
              type="number"
              min={0}
              step="any"
              placeholder={String(facets.price_range.max)}
              defaultValue={maxPrice}
            />
          </label>
        </div>
        <button type="submit">Apply</button>
      </form>

      <OptionGroup
        title="Manufacturer"
        options={facets.manufacturers}
        selected={params.getAll('manufacturer')}
        onToggle={(value) => onChange(toggleValue(params, 'manufacturer', value))}
      />

      {facets.specs.map((spec) => (
        <OptionGroup
          key={spec.name}
          title={spec.label}
          options={spec.values}
          selected={params.getAll(spec.name)}
          onToggle={(value) => onChange(toggleValue(params, spec.name, value))}
        />
      ))}

      {hasActiveFilters(params) && (
        <button type="button" className="reset-filters" onClick={() => onChange(clearFilters(params))}>
          Reset filters
        </button>
      )}
    </details>
  )
}
