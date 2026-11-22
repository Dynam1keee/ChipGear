import type { Product } from '../types'
import ProductCard from './ProductCard'

interface ProductRowProps {
  title: string
  products: Product[] | undefined
}

// A titled row of cards that scrolls sideways. Nothing is drawn while there are no products,
// so a block without data (no sales yet, empty history) simply does not appear.
export default function ProductRow({ title, products }: ProductRowProps) {
  if (!products || products.length === 0) return null

  return (
    <section className="product-row">
      <h3 className="row-title">{title}</h3>
      <div className="product-row-list">
        {products.map((product) => (
          <div key={product.id} className="product-row-item">
            <ProductCard product={product} />
          </div>
        ))}
      </div>
    </section>
  )
}
