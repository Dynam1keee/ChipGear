import { useEffect } from 'react'

const DEFAULT_TITLE = 'ChipGear'
const DEFAULT_DESCRIPTION =
  'ChipGear computer components online store: processors, graphics cards, motherboards and other equipment at the best prices.'

function setDescription(text: string) {
  let tag = document.querySelector<HTMLMetaElement>('meta[name="description"]')
  if (!tag) {
    tag = document.createElement('meta')
    tag.name = 'description'
    document.head.appendChild(tag)
  }
  tag.content = text
}

// Every page of a single-page app shares one HTML file, so each page sets its own tab title
// and description (search engines and the browser history use them).
// When the page goes away, the default values come back.
export function useDocumentTitle(title: string, description: string = DEFAULT_DESCRIPTION) {
  useEffect(() => {
    document.title = title
    setDescription(description)
    return () => {
      document.title = DEFAULT_TITLE
      setDescription(DEFAULT_DESCRIPTION)
    }
  }, [title, description])
}
