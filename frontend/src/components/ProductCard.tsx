import { Link } from 'react-router-dom'
import type { Product } from '../types'
import AddToCartButton from './AddToCartButton'

interface ProductCardProps {
  product: Product
}

// A card of the catalog: the picture with the discount, the name, a short description,
// the price and the cart button
export default function ProductCard({ product }: ProductCardProps) {
  // Link changes the address without reloading the page
  const productUrl = `/products/${product.slug}`
  const hasDiscount = product.discount > 0

  return (
    <article className={product.in_stock ? 'product-card' : 'product-card unavailable'}>
      <Link to={productUrl} className="product-card-image">
        <img src={product.image ?? '/icons/image_not_found.jpg'} alt={product.name} loading="lazy" />
        {hasDiscount && <span className="discount-badge">-{product.discount}%</span>}
      </Link>
      <h3>
        <Link to={productUrl}>{product.name}</Link>
      </h3>
      <p className="product-card-description">{product.description}</p>
      <div className="product-card-buy">
        <p className="card-price">
          {hasDiscount && <s>${product.price}</s>}
          <strong className={hasDiscount ? 'sale' : undefined}>${product.sell_price}</strong>
        </p>
        <AddToCartButton product={product} variant="icon" />
      </div>
      <p className={product.in_stock ? 'stock in-stock' : 'stock out-of-stock'}>
        {product.in_stock ? 'In stock' : 'Out of stock'}
      </p>
    </article>
  )
}
