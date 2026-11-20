// These types describe the JSON that the Django API sends (see api/serializers.py).

export interface Category {
  id: number
  name: string
  slug: string
  image: string | null
}

export interface Product {
  id: number
  name: string
  slug: string
  manufacturer: string
  description: string
  image: string | null
  // Money values are strings, for example "90.00": this avoids rounding errors
  price: string
  discount: number // percentage, 0-100
  sell_price: string // price after the discount
  quantity: number
  in_stock: boolean
  category: string // category slug
}

// A specification value depends on the category (text, number, yes/no, ...)
export type SpecValue = string | number | boolean | null

// GET /api/products/<slug>/ also sends the specifications of the category
export interface ProductDetail extends Product {
  specs: Record<string, SpecValue>
}

// The shape of every paginated response from DRF
export interface Page<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// One choice in a filter group, with the number of products it would give
export interface FilterOption {
  value: string | number | boolean
  count: number
}

export interface SpecFacet {
  name: string // the query parameter, for example "key_switches"
  label: string // for people, for example "Key switches"
  values: FilterOption[]
}

// GET /api/filters/: everything the filter sidebar needs
export interface Facets {
  price_range: { min: number; max: number }
  manufacturers: FilterOption[]
  specs: SpecFacet[] // empty when no category is chosen
}
