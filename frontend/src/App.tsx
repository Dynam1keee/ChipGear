import { Link, Route, Routes } from 'react-router-dom'
import CartLink from './components/CartLink'
import NotFound from './components/NotFound'
import UserMenu from './components/UserMenu'
import CartPage from './pages/CartPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
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
        <nav className="header-links">
          <UserMenu />
          <CartLink />
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<CatalogPage />} />
          <Route path="/products/:slug" element={<ProductPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  )
}
