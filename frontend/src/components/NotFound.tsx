import { Link } from 'react-router-dom'
import { useDocumentTitle } from '../useDocumentTitle'

interface NotFoundProps {
  message?: string
}

export default function NotFound({ message = 'Page not found' }: NotFoundProps) {
  useDocumentTitle('Page not found - ChipGear')
  return (
    <div className="not-found">
      <h2>{message}</h2>
      <Link to="/">Back to the catalog</Link>
    </div>
  )
}
