// 무한 스크롤용 훅
import { useEffect, useRef, useState } from 'react'

export const useIntersectionObserver = (
  threshold = 0.1,
  rootMargin = '0px'
) => {
  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null)
  const elementRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const element = elementRef.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => setEntry(entry),
      { threshold, rootMargin }
    )

    observer.observe(element)

    return () => observer.disconnect()
  }, [threshold, rootMargin])

  return [elementRef, entry] as const
}