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

// The shape of every paginated response from DRF
export interface Page<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
