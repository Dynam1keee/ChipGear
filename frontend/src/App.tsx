import { useEffect, useState } from 'react'
import { fetchCategories, fetchProducts } from './api'
import CategoryFilter from './components/CategoryFilter'
import Pagination from './components/Pagination'
import ProductCard from './components/ProductCard'
import type { Category, Page, Product } from './types'

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unknown error'
}

export default function App() {
  // State: values that React remembers. When one changes, the component is drawn again.
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [products, setProducts] = useState<Page<Product> | null>(null) // null = loading
  const [error, setError] = useState<string | null>(null)

  // Effect 1: load the categories once, when the page opens ([] = no dependencies)
  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch((e: unknown) => setError(errorMessage(e)))
  }, [])

  // Effect 2: load products again every time the category or the page changes
  useEffect(() => {
    // If the user clicks fast, an old response may arrive after a newer one.
    // The cleanup function below marks the old request as outdated.
    let outdated = false

    setProducts(null)
    setError(null)
    fetchProducts({ category: selectedCategory ?? undefined, page })
      .then((data) => {
        if (!outdated) setProducts(data)
      })
      .catch((e: unknown) => {
        if (!outdated) setError(errorMessage(e))
      })

    return () => {
      outdated = true
    }
  }, [selectedCategory, page])

  function handleCategorySelect(slug: string | null) {
    setSelectedCategory(slug)
    setPage(1) // a new category starts from the first page
  }

  return (
    <div className="app">
      <header>
        <h1>ChipGear</h1>
      </header>

      <main>
        <CategoryFilter
          categories={categories}
          selected={selectedCategory}
          onSelect={handleCategorySelect}
        />

        {error && <p className="error">Could not load data: {error}</p>}
        {!error && products === null && <p>Loading...</p>}

        {products && (
          <>
            <p className="count">{products.count} products</p>
            {products.results.length === 0 && <p>No products found.</p>}
            <div className="product-grid">
              {products.results.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
            <Pagination
              page={page}
              hasPrevious={products.previous !== null}
              hasNext={products.next !== null}
              onChange={setPage}
            />
          </>
        )}
      </main>
    </div>
  )
}
