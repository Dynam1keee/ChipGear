const COLUMNS: Record<string, string[]> = {
  Components: ['Home', 'Products', 'Prices', 'FAQ', 'About us'],
  Service: ['Support', 'Warranty', 'Shipping', 'Returns', 'Contacts'],
  Resources: ['Latest news', 'Technical articles', 'Customer reviews', 'Our blog', 'Join us'],
}

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-brand">
        <img src="/icons/favicon.png" alt="ChipGear logo" width={50} height={50} />
        <p>ChipGear &copy; 2024</p>
      </div>
      {Object.entries(COLUMNS).map(([title, items]) => (
        <div key={title}>
          <h5>{title}</h5>
          <ul>
            {items.map((item) => (
              <li key={item}>
                <a href="#">{item}</a>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </footer>
  )
}
