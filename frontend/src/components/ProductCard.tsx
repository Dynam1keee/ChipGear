import type { Product } from '../types'

interface ProductCardProps {
  product: Product
}

export default function ProductCard({ product }: ProductCardProps) {
  const hasDiscount = product.discount > 0

  return (
    <article className="product-card">
      {product.image && <img src={product.image} alt={product.name} loading="lazy" />}
      <h3>{product.name}</h3>
      <p className="manufacturer">{product.manufacturer}</p>
      <p className="price">
        <strong>${product.sell_price}</strong>
        {hasDiscount && (
          <>
            <s className="price-old">${product.price}</s>
            <span className="badge">-{product.discount}%</span>
          </>
        )}
      </p>
      <p className={product.in_stock ? 'stock in-stock' : 'stock out-of-stock'}>
        {product.in_stock ? 'In stock' : 'Out of stock'}
      </p>
    </article>
  )
}
