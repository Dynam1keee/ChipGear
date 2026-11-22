import { Link } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import ProductRow from '../components/ProductRow'
import { useCategories, useRecentlyViewed, useTopSales } from '../queries'
import { useDocumentTitle } from '../useDocumentTitle'

// The first page: the categories, the top sales and the products seen lately
export default function HomePage() {
  useDocumentTitle('ChipGear - Home')
  const { data: categories, error, isPending, isError } = useCategories()
  const topSales = useTopSales()
  const recentlyViewed = useRecentlyViewed()

  if (isPending) return <p>Loading...</p>
  if (isError) return <p className="error">Could not load the categories: {error.message}</p>

  return (
    <>
      <section>
        <h2 className="page-title">Component categories</h2>
        <ul className="category-grid">
          {categories.map((category) => (
            <li key={category.id}>
              <Link to={`/?category=${encodeURIComponent(category.slug)}`} className="category-card">
                <img src={category.image ?? '/icons/image_not_found.jpg'} alt="" loading="lazy" />
                <span>{category.name}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {/* The shop shows the best sellers only after enough sales: until then the server sends an empty list */}
      {topSales.data && topSales.data.length > 0 && (
        <section>
          <h2 className="page-title section-gap">Top sales</h2>
          <div className="product-grid">
            {topSales.data.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </section>
      )}

      <ProductRow title="Recently viewed" products={recentlyViewed.data} />
    </>
  )
}
