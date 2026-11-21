import { useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api'
import AddToCartButton from '../components/AddToCartButton'
import Breadcrumbs from '../components/Breadcrumbs'
import NotFound from '../components/NotFound'
import { useCategories, useProduct } from '../queries'
import type { SpecValue } from '../types'

const LOW_STOCK = 5 // from this quantity the page says how many are left

function formatSpec(value: SpecValue): string {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (value === null) return '-'
  return String(value)
}

export default function ProductPage() {
  // useParams reads ":slug" from the address /products/:slug
  const { slug = '' } = useParams<{ slug: string }>()
  const { data: product, error, isPending, isError } = useProduct(slug)
  const categories = useCategories()
  const navigate = useNavigate()

  if (isPending) return <p>Loading...</p>

  if (isError) {
    if (error instanceof ApiError && error.status === 404) {
      return <NotFound message="Product not found" />
    }
    return <p className="error">Could not load the product: {error.message}</p>
  }

  const hasDiscount = product.discount > 0
  const categoryName = categories.data?.find((item) => item.slug === product.category)?.name ?? product.category
  const specs = Object.entries(product.specs)

  return (
    <>
      <Breadcrumbs
        items={[
          categories.data
            ? {
                label: categoryName,
                // a quick way to go to another category
                select: {
                  value: product.category,
                  options: categories.data.map((item) => ({ value: item.slug, label: item.name })),
                  onChange: (value) => navigate(`/?category=${encodeURIComponent(value)}`),
                },
              }
            : { label: categoryName, to: `/?category=${product.category}` },
          { label: product.name },
        ]}
      />

      <article className="product-page">
        <div className="product-page-main">
          <img src={product.image ?? '/icons/image_not_found.jpg'} alt={product.name} />

          <div className="product-page-info">
            <h2>{product.name}</h2>

            <div className="product-page-buy">
              <div>
                <p className="product-page-price">
                  {hasDiscount && <s>${product.price}</s>}
                  <strong className={hasDiscount ? 'sale' : undefined}>
                    ${product.sell_price}
                    {hasDiscount && <span className="discount-tag">-{product.discount}%</span>}
                  </strong>
                </p>
                <p className={product.in_stock ? 'stock in-stock' : 'stock out-of-stock'}>
                  {product.in_stock ? 'In stock' : 'Out of stock'}
                  {product.in_stock && product.quantity <= LOW_STOCK && (
                    <span className="low-stock"> &middot; only {product.quantity} left</span>
                  )}
                </p>
                <AddToCartButton product={product} />
              </div>
              <p className="product-id">Product ID: {String(product.id).padStart(7, '0')}</p>
            </div>

            <p className="manufacturer">Manufacturer: {product.manufacturer}</p>
            {product.description !== '-' && <p className="product-description">{product.description}</p>}
          </div>
        </div>

        {specs.length > 0 && (
          <section>
            <h3 className="specs-title">Specifications</h3>
            <table className="specs">
              <tbody>
                {specs.map(([name, value]) => (
                  <tr key={name}>
                    <th>{name}</th>
                    <td>{formatSpec(value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}
      </article>
    </>
  )
}
