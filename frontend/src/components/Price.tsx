import type { Product } from '../types'

interface PriceProps {
  product: Pick<Product, 'price' | 'sell_price' | 'discount'>
}

export default function Price({ product }: PriceProps) {
  return (
    <p className="price">
      <strong>${product.sell_price}</strong>
      {product.discount > 0 && (
        <>
          <s className="price-old">${product.price}</s>
          <span className="badge">-{product.discount}%</span>
        </>
      )}
    </p>
  )
}
