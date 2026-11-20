interface PaginationProps {
  page: number
  hasPrevious: boolean
  hasNext: boolean
  onChange: (page: number) => void
}

export default function Pagination({ page, hasPrevious, hasNext, onChange }: PaginationProps) {
  return (
    <div className="pagination">
      <button disabled={!hasPrevious} onClick={() => onChange(page - 1)}>
        Previous
      </button>
      <span>Page {page}</span>
      <button disabled={!hasNext} onClick={() => onChange(page + 1)}>
        Next
      </button>
    </div>
  )
}
