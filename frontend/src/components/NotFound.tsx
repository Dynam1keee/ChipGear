import { Link } from 'react-router-dom'

interface NotFoundProps {
  message?: string
}

export default function NotFound({ message = 'Page not found' }: NotFoundProps) {
  return (
    <div className="not-found">
      <h2>{message}</h2>
      <Link to="/">Back to the catalog</Link>
    </div>
  )
}
