import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../api'
import AddToCartButton from '../components/AddToCartButton'
import NotFound from '../components/NotFound'
import Price from '../components/Price'
import { useProduct } from '../queries'
import type { SpecValue } from '../types'

function formatSpec(value: SpecValue): string {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (value === null) return '-'
  return String(value)
}

export default function ProductPage() {
  // useParams reads ":slug" from the address /products/:slug
  const { slug = '' } = useParams<{ slug: string }>()
  const { data: product, error, isPending, isError } = useProduct(slug)

  if (isPending) return <p>Loading...</p>

  if (isError) {
    if (error instanceof ApiError && error.status === 404) {
      return <NotFound message="Product not found" />
    }
    return <p className="error">Could not load the product: {error.message}</p>
  }

  return (
    <article className="product-page">
      <Link to={`/?category=${product.category}`}>&larr; Back to the catalog</Link>

      <div className="product-page-main">
        {product.image && <img src={product.image} alt={product.name} />}
        <div>
          <h2>{product.name}</h2>
          <p className="manufacturer">{product.manufacturer}</p>
          <Price product={product} />
          <p className={product.in_stock ? 'stock in-stock' : 'stock out-of-stock'}>
            {product.in_stock ? `In stock: ${product.quantity}` : 'Out of stock'}
          </p>
          {product.description !== '-' && <p>{product.description}</p>}
          <AddToCartButton product={product} />
        </div>
      </div>

      {Object.keys(product.specs).length > 0 && (
        <>
          <h3>Specifications</h3>
          <table className="specs">
            <tbody>
              {Object.entries(product.specs).map(([name, value]) => (
                <tr key={name}>
                  <th>{name}</th>
                  <td>{formatSpec(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </article>
  )
}
