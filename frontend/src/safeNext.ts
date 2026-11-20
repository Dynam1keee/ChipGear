// After a login we go to the page from ?next=..., but only inside this site.
// Otherwise a crafted link (?next=https://evil.example) could send the user to another site.
export function safeNext(next: string | null): string {
  if (next && next.startsWith('/') && !next.startsWith('//') && !next.startsWith('/\\')) return next
  return '/'
}
