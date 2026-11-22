import { useEffect } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api'
import AddToCartButton from '../components/AddToCartButton'
import Breadcrumbs from '../components/Breadcrumbs'
import NotFound from '../components/NotFound'
import ProductRow from '../components/ProductRow'
import { useCategories, useMarkViewed, useProduct, useRecentlyViewed, useRelated } from '../queries'
import type { SpecValue } from '../types'
import { useDocumentTitle } from '../useDocumentTitle'

const LOW_STOCK = 5 // from this quantity the page says how many are left
const HIGHLIGHTS = 4 // how many specifications are shown next to the price

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
  const related = useRelated(slug)
  const recentlyViewed = useRecentlyViewed(slug)
  const markViewed = useMarkViewed()
  const navigate = useNavigate()
  useDocumentTitle(
    product ? `${product.name} - ChipGear` : 'ChipGear',
    product ? `Buy ${product.name} online - High performance at a great price` : undefined,
  )

  // Put the product into the history of views once it has been loaded.
  // mutate has a stable identity, so only a change of the product runs it again.
  const found = product !== undefined
  const { mutate: remember } = markViewed
  useEffect(() => {
    if (found) remember(slug)
  }, [found, slug, remember])

  if (isPending) return <p>Loading...</p>

  if (isError) {
    if (error instanceof ApiError && error.status === 404) {
      return <NotFound message="Product not found" />
    }
    return <p className="error">Could not load the product: {error.message}</p>
  }

  const hasDiscount = product.discount > 0
  const saving = hasDiscount ? (Number(product.price) - Number(product.sell_price)).toFixed(2) : null
  const categoryName = categories.data?.find((item) => item.slug === product.category)?.name ?? product.category
  const specs = Object.entries(product.specs)
  // the first short values (not Yes/No) tell the main thing about the product at a glance
  const highlights = specs.filter(([, value]) => typeof value !== 'boolean' && value !== null).slice(0, HIGHLIGHTS)

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

      <article className="pp">
        <div className="pp-top">
          <div className="pp-gallery">
            {hasDiscount && <span className="pp-badge">-{product.discount}%</span>}
            <img src={product.image ?? '/icons/image_not_found.jpg'} alt={product.name} />
          </div>

          <div className="pp-info">
            <p className="pp-meta">
              <Link to={`/?category=${product.category}`}>{categoryName}</Link>
              <span>{product.manufacturer}</span>
              <span>ID {String(product.id).padStart(7, '0')}</span>
            </p>
            <h2 className="pp-title">{product.name}</h2>
            {product.description !== '-' && <p className="pp-description">{product.description}</p>}

            {highlights.length > 0 && (
              <ul className="pp-highlights">
                {highlights.map(([name, value]) => (
                  <li key={name}>
                    <span>{name}</span>
                    <strong>{formatSpec(value)}</strong>
                  </li>
                ))}
              </ul>
            )}

            <div className="pp-buy">
              <div className="pp-price">
                <strong className={hasDiscount ? 'sale' : undefined}>${product.sell_price}</strong>
                {hasDiscount && (
                  <span className="pp-old">
                    <s>${product.price}</s> You save ${saving}
                  </span>
                )}
              </div>
              <div className="pp-action">
                <p className={product.in_stock ? 'stock in-stock' : 'stock out-of-stock'}>
                  {product.in_stock ? 'In stock' : 'Out of stock'}
                  {product.in_stock && product.quantity <= LOW_STOCK && (
                    <span className="low-stock"> &middot; only {product.quantity} left</span>
                  )}
                </p>
                <AddToCartButton product={product} />
              </div>
            </div>
          </div>
        </div>

        {specs.length > 0 && (
          <section className="pp-specs">
            <h3>Specifications</h3>
            <dl>
              {specs.map(([name, value]) => (
                <div key={name}>
                  <dt>{name}</dt>
                  <dd>{formatSpec(value)}</dd>
                </div>
              ))}
            </dl>
          </section>
        )}
      </article>

      <ProductRow title="Customers also buy with this item" products={related.data} />
      <ProductRow title="Recently viewed products" products={recentlyViewed.data} />
    </>
  )
}
