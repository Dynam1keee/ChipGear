import { Link, Route, Routes } from 'react-router-dom'
import CartLink from './components/CartLink'
import NotFound from './components/NotFound'
import CartPage from './pages/CartPage'
import CatalogPage from './pages/CatalogPage'
import ProductPage from './pages/ProductPage'

// App only holds the page frame and decides which page to show for which address.
export default function App() {
  return (
    <div className="app">
      <header className="site-header">
        <Link to="/">
          <h1>ChipGear</h1>
        </Link>
        <CartLink />
      </header>

      <main>
        <Routes>
          <Route path="/" element={<CatalogPage />} />
          <Route path="/products/:slug" element={<ProductPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  )
}
