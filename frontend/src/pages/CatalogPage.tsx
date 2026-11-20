import { useSearchParams } from 'react-router-dom'
import CategoryFilter from '../components/CategoryFilter'
import FilterSidebar from '../components/FilterSidebar'
import Pagination from '../components/Pagination'
import ProductCard from '../components/ProductCard'
import { facetParams, parsePage, productParams, setParam } from '../filters'
import { useCategories, useFacets, useProducts } from '../queries'

const SORT_OPTIONS = [
  { value: 'default', label: 'Default order' },
  { value: 'price', label: 'Price: low to high' },
  { value: '-price', label: 'Price: high to low' },
  { value: 'name', label: 'Name: A to Z' },
  { value: '-name', label: 'Name: Z to A' },
]

export default function CatalogPage() {
  // Everything the user chose lives in the address, for example
  // /?category=keyboards&manufacturer=Acme&layout=ANSI&page=2
  // So the Back button works and the user can share the link.
  const [searchParams, setSearchParams] = useSearchParams()
  const category = searchParams.get('category')
  const page = parsePage(searchParams.get('page'))

  const categoriesQuery = useCategories()
  const productsQuery = useProducts(productParams(searchParams))
  const facetsQuery = useFacets(facetParams(searchParams))

  function handleCategorySelect(slug: string | null) {
    // A new category starts with no filters (each category has its own specifications)
    setSearchParams(slug ? { category: slug } : {})
  }

  function handlePageChange(newPage: number) {
    const next = new URLSearchParams(searchParams)
    if (newPage > 1) next.set('page', String(newPage))
    else next.delete('page')
    setSearchParams(next)
  }

  const { data, error, isPending, isPlaceholderData } = productsQuery
  const facets = facetsQuery.data

  return (
    <>
      <CategoryFilter
        categories={categoriesQuery.data ?? []}
        selected={category}
        onSelect={handleCategorySelect}
      />

      <div className="catalog">
        <aside>
          {facets && (
            <FilterSidebar facets={facets} params={searchParams} onChange={setSearchParams} />
          )}
        </aside>

        <section>
          {isPending && <p>Loading...</p>}
          {error && <p className="error">Could not load products: {error.message}</p>}

          {data && (
            // isPlaceholderData = new results are loading, the old ones are still shown
            <div className={isPlaceholderData ? 'stale' : undefined}>
              <div className="results-header">
                <p className="count">{data.count} products</p>
                <select
                  aria-label="Sort by"
                  value={searchParams.get('ordering') ?? 'default'}
                  onChange={(event) =>
                    setSearchParams(
                      setParam(
                        searchParams,
                        'ordering',
                        event.target.value === 'default' ? '' : event.target.value,
                      ),
                    )
                  }
                >
                  {SORT_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

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
        </section>
      </div>
    </>
  )
}
