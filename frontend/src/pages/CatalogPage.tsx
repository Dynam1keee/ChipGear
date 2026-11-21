import { useSearchParams } from 'react-router-dom'
import Breadcrumbs from '../components/Breadcrumbs'
import FilterSidebar from '../components/FilterSidebar'
import Pagination from '../components/Pagination'
import ProductCard from '../components/ProductCard'
import { facetParams, parsePage, productParams } from '../filters'
import { useCategories, useFacets, useProducts } from '../queries'

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

  function handlePageChange(newPage: number) {
    const next = new URLSearchParams(searchParams)
    if (newPage > 1) next.set('page', String(newPage))
    else next.delete('page')
    setSearchParams(next)
  }

  const { data, error, isPending, isPlaceholderData } = productsQuery
  const facets = facetsQuery.data

  // The title: the name of the category, or "Search results" for a search in all categories
  const categoryName = categoriesQuery.data?.find((item) => item.slug === category)?.name ?? category
  const searchText = searchParams.get('q')
  const title = categoryName ?? 'Search results'

  return (
    <>
      <Breadcrumbs items={[{ label: title }]} />
      <h2 className="catalog-title">{title}</h2>
      {searchText && <p className="search-note">Search: &ldquo;{searchText}&rdquo;</p>}

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
