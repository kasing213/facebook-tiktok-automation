import { useEffect, useRef, useState, useCallback } from 'react'

interface UseScrollAnimationOptions {
  threshold?: number // 0-1, percentage visible before triggering
  rootMargin?: string // CSS margin around root
  triggerOnce?: boolean // Only animate once
  delay?: number // Delay in ms before animation starts
}

interface UseScrollAnimationReturn {
  ref: React.RefObject<HTMLDivElement>
  isVisible: boolean
  hasAnimated: boolean
}

/**
 * Hook for scroll-triggered animations using Intersection Observer
 *
 * @example
 * const { ref, isVisible } = useScrollAnimation({ threshold: 0.2 })
 *
 * return (
 *   <AnimatedDiv ref={ref} $isVisible={isVisible}>
 *     Content appears when scrolled into view
 *   </AnimatedDiv>
 * )
 */
export const useScrollAnimation = (
  options: UseScrollAnimationOptions = {}
): UseScrollAnimationReturn => {
  const {
    threshold = 0.1,
    rootMargin = '0px 0px -50px 0px',
    triggerOnce = true,
    delay = 0,
  } = options

  const ref = useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = useState(false)
  const [hasAnimated, setHasAnimated] = useState(false)

  // Check for reduced motion preference
  const prefersReducedMotion =
    typeof window !== 'undefined'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false

  const handleIntersect = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries

      if (entry.isIntersecting) {
        if (delay > 0 && !prefersReducedMotion) {
          setTimeout(() => {
            setIsVisible(true)
            setHasAnimated(true)
          }, delay)
        } else {
          setIsVisible(true)
          setHasAnimated(true)
        }
      } else if (!triggerOnce) {
        setIsVisible(false)
      }
    },
    [delay, triggerOnce, prefersReducedMotion]
  )

  useEffect(() => {
    // If user prefers reduced motion, show immediately
    if (prefersReducedMotion) {
      setIsVisible(true)
      setHasAnimated(true)
      return
    }

    const observer = new IntersectionObserver(handleIntersect, {
      threshold,
      rootMargin,
    })

    const currentRef = ref.current
    if (currentRef) {
      observer.observe(currentRef)
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef)
      }
    }
  }, [threshold, rootMargin, handleIntersect, prefersReducedMotion])

  return { ref, isVisible, hasAnimated }
}

/**
 * Hook for staggered list animations on mount
 *
 * @example
 * const visibleItems = useStaggeredAnimation(items.length)
 *
 * return items.map((item, index) => (
 *   <Item key={item.id} $isVisible={visibleItems[index]}>
 *     {item.name}
 *   </Item>
 * ))
 */
export const useStaggeredAnimation = (
  itemCount: number,
  baseDelay: number = 50
): boolean[] => {
  const [visibleItems, setVisibleItems] = useState<boolean[]>(
    new Array(itemCount).fill(false)
  )

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches

    if (prefersReducedMotion) {
      setVisibleItems(new Array(itemCount).fill(true))
      return
    }

    const timeouts: ReturnType<typeof setTimeout>[] = []

    for (let i = 0; i < itemCount; i++) {
      const timeout = setTimeout(() => {
        setVisibleItems((prev) => {
          const newState = [...prev]
          newState[i] = true
          return newState
        })
      }, i * baseDelay)
      timeouts.push(timeout)
    }

    return () => {
      timeouts.forEach(clearTimeout)
    }
  }, [itemCount, baseDelay])

  return visibleItems
}

/**
 * Simple hook to track if component has mounted (for entrance animations)
 *
 * @example
 * const isMounted = useMountAnimation(100) // 100ms delay
 *
 * return <Card $isVisible={isMounted}>Content</Card>
 */
export const useMountAnimation = (delay: number = 0): boolean => {
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches

    if (prefersReducedMotion) {
      setIsMounted(true)
      return
    }

    const timeout = setTimeout(() => {
      setIsMounted(true)
    }, delay)

    return () => clearTimeout(timeout)
  }, [delay])

  return isMounted
}

export default useScrollAnimation
