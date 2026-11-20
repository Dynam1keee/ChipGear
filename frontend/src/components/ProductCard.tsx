import { Link } from 'react-router-dom'
import type { Product } from '../types'
import AddToCartButton from './AddToCartButton'
import Price from './Price'

interface ProductCardProps {
  product: Product
}

export default function ProductCard({ product }: ProductCardProps) {
  // Link changes the address without reloading the page
  const productUrl = `/products/${product.slug}`

  return (
    <article className="product-card">
      {product.image && (
        <Link to={productUrl}>
          <img src={product.image} alt={product.name} loading="lazy" />
        </Link>
      )}
      <h3>
        <Link to={productUrl}>{product.name}</Link>
      </h3>
      <p className="manufacturer">{product.manufacturer}</p>
      <Price product={product} />
      <p className={product.in_stock ? 'stock in-stock' : 'stock out-of-stock'}>
        {product.in_stock ? 'In stock' : 'Out of stock'}
      </p>
      <AddToCartButton product={product} />
    </article>
  )
}
