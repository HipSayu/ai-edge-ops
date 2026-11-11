import { useEffect, useState } from 'react'
import { authBlobUrl } from '@/helpers/media'

// An image behind the login: fetched with the Authorization header and shown from a blob URL.
export default function AuthImage({ src, alt = '', className }: { src: string; alt?: string; className?: string }) {
  const [shown, setShown] = useState<string>()
  useEffect(() => {
    let current = true
    authBlobUrl(src).then(
      (url) => current && setShown(url),
      () => current && setShown(undefined),
    )
    return () => {
      current = false
    }
  }, [src])
  return <img src={shown} alt={alt} className={className} />
}
