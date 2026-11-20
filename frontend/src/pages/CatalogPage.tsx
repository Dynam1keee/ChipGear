import { useSearchParams } from 'react-router-dom'
import CategoryFilter from '../components/CategoryFilter'
import Pagination from '../components/Pagination'
import ProductCard from '../components/ProductCard'
import { useCategories, useProducts } from '../queries'

function parsePage(value: string | null): number {
  const page = Number(value)
  return Number.isInteger(page) && page > 0 ? page : 1
}

export default function CatalogPage() {
  // The selected category and page live in the address (?category=keyboards&page=2).
  // So the Back button works and the user can share the link.
  const [searchParams, setSearchParams] = useSearchParams()
  const category = searchParams.get('category')
  const page = parsePage(searchParams.get('page'))

  const categoriesQuery = useCategories()
  const productsQuery = useProducts({ category: category ?? undefined, page })

  function handleCategorySelect(slug: string | null) {
    // The page is not in the new parameters, so a new category starts from page 1
    setSearchParams(slug ? { category: slug } : {})
  }

  function handlePageChange(newPage: number) {
    const next = new URLSearchParams(searchParams)
    if (newPage > 1) next.set('page', String(newPage))
    else next.delete('page')
    setSearchParams(next)
  }

  const { data, error, isPending, isPlaceholderData } = productsQuery

  return (
    <>
      <CategoryFilter
        categories={categoriesQuery.data ?? []}
        selected={category}
        onSelect={handleCategorySelect}
      />

      {isPending && <p>Loading...</p>}
      {error && <p className="error">Could not load products: {error.message}</p>}

      {data && (
        // isPlaceholderData = the next page is loading, the old one is still shown
        <div className={isPlaceholderData ? 'stale' : undefined}>
          <p className="count">{data.count} products</p>
          {data.results.length === 0 && <p>No products found.</p>}
          <div className="product-grid">
            {data.results.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
          <Pagination
            page={page}
            hasPrevious={data.previous !== null && !isPlaceholderData}
            hasNext={data.next !== null && !isPlaceholderData}
            onChange={handlePageChange}
          />
        </div>
      )}
    </>
  )
}
