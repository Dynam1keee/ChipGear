import { useState } from 'react'
import { clearFilters, hasActiveFilters, setParam, toggleValue } from '../filters'
import type { Facets } from '../types'
import OptionGroup from './OptionGroup'
import PriceFilter from './PriceFilter'

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
  // On a phone the filters start closed, so the products are visible at once.
  // Only the first value is used: later the browser keeps the open/closed state itself.
  const [startOpen] = useState(() => !window.matchMedia || window.matchMedia('(min-width: 801px)').matches)
  const minPrice = params.get('min_price') ?? ''
  const maxPrice = params.get('max_price') ?? ''
  const ordering = params.get('ordering') ?? 'default'

  return (
    <details className="filter-sidebar" open={startOpen}>
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

      <PriceFilter
        range={facets.price_range}
        min={minPrice}
        max={maxPrice}
        onApply={(min, max) => onChange(setParam(setParam(params, 'min_price', min), 'max_price', max))}
      />

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
