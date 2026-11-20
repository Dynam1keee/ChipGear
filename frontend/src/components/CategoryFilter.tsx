import type { Category } from '../types'

interface CategoryFilterProps {
  categories: Category[]
  selected: string | null // slug of the selected category, or null for "All"
  onSelect: (slug: string | null) => void
}

export default function CategoryFilter({ categories, selected, onSelect }: CategoryFilterProps) {
  return (
    <nav className="category-filter">
      <button className={selected === null ? 'active' : ''} onClick={() => onSelect(null)}>
        All
      </button>
      {categories.map((category) => (
        <button
          key={category.id}
          className={selected === category.slug ? 'active' : ''}
          onClick={() => onSelect(category.slug)}
        >
          {category.name}
        </button>
      ))}
    </nav>
  )
}
