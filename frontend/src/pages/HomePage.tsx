import { Link } from 'react-router-dom'
import { useCategories } from '../queries'

// The first page: the categories with their pictures
export default function HomePage() {
  const { data: categories, error, isPending, isError } = useCategories()

  if (isPending) return <p>Loading...</p>
  if (isError) return <p className="error">Could not load the categories: {error.message}</p>

  return (
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
  )
}
