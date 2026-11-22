import { useEffect } from 'react'
import { Link, Route, Routes, useLocation, useSearchParams } from 'react-router-dom'
import CartLink from './components/CartLink'
import HeaderSearch from './components/HeaderSearch'
import SiteFooter from './components/SiteFooter'
import NotFound from './components/NotFound'
import UserMenu from './components/UserMenu'
import BuilderPage from './pages/BuilderPage'
import CartPage from './pages/CartPage'
import CheckoutPage from './pages/CheckoutPage'
import LoginPage from './pages/LoginPage'
import OrdersPage from './pages/OrdersPage'
import ProfilePage from './pages/ProfilePage'
import RegisterPage from './pages/RegisterPage'
import CatalogPage from './pages/CatalogPage'
import HomePage from './pages/HomePage'
import ProductPage from './pages/ProductPage'

// The address "/" shows the categories. With a category or a search text it shows the catalog.
function HomeOrCatalog() {
  const [searchParams] = useSearchParams()
  const isCatalog = searchParams.has('category') || searchParams.has('q')
  return isCatalog ? <CatalogPage /> : <HomePage />
}

// A new page opens at the top (the browser keeps the old scroll position in a single-page app)
function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

// App only holds the page frame and decides which page to show for which address.
export default function App() {
  return (
    <div className="app">
      <ScrollToTop />
      <header className="site-header">
        <Link to="/" className="brand">
          ChipGear
        </Link>
        <HeaderSearch />
        <UserMenu />
        <CartLink />
      </header>

      <main>
        <Routes>
          <Route path="/" element={<HomeOrCatalog />} />
          <Route path="/products/:slug" element={<ProductPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/builder" element={<BuilderPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

      <SiteFooter />
    </div>
  )
}
