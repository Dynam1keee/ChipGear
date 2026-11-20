import type { FormEvent } from 'react'
import { clearFilters, hasActiveFilters, setParam, toggleValue } from '../filters'
import type { Facets } from '../types'
import OptionGroup from './OptionGroup'

interface FilterSidebarProps {
  facets: Facets
  params: URLSearchParams // the current query string of the page
  onChange: (next: URLSearchParams) => void
}

export default function FilterSidebar({ facets, params, onChange }: FilterSidebarProps) {
  const minPrice = params.get('min_price') ?? ''
  const maxPrice = params.get('max_price') ?? ''

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = String(new FormData(event.currentTarget).get('q') ?? '').trim()
    onChange(setParam(params, 'q', text))
  }

  function handlePrice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const min = String(data.get('min_price') ?? '')
    const max = String(data.get('max_price') ?? '')
    onChange(setParam(setParam(params, 'min_price', min), 'max_price', max))
  }

  return (
    <div className="filter-sidebar">
      {/* "key" makes the field show the new value when the address changes (for example after Reset) */}
      <form onSubmit={handleSearch} className="filter-form">
        <h4>Search</h4>
        <input
          key={params.get('q') ?? ''}
          name="q"
          type="search"
          placeholder="Product name"
          defaultValue={params.get('q') ?? ''}
        />
      </form>

      <form onSubmit={handlePrice} className="filter-form">
        <h4>Price, $</h4>
        <div className="price-inputs">
          <input
            key={`min-${minPrice}`}
            name="min_price"
            type="number"
            min={0}
            step="any"
            placeholder={String(facets.price_range.min)}
            defaultValue={minPrice}
          />
          <span>&ndash;</span>
          <input
            key={`max-${maxPrice}`}
            name="max_price"
            type="number"
            min={0}
            step="any"
            placeholder={String(facets.price_range.max)}
            defaultValue={maxPrice}
          />
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
    </div>
  )
}
