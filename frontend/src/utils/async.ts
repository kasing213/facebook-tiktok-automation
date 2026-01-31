/**
 * Utility functions for handling asynchronous operations with loading states
 */

/**
 * Sleep function for introducing delays
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Wraps an async function with loading state management
 */
export const withLoadingState = <T extends any[], R>(
  asyncFn: (...args: T) => Promise<R>,
  options: {
    minLoadingTime?: number
    onStart?: () => void
    onEnd?: () => void
    onError?: (error: Error) => void
  } = {}
) => {
  const { minLoadingTime = 300, onStart, onEnd, onError } = options

  return async (...args: T): Promise<R> => {
    onStart?.()
    const startTime = Date.now()

    try {
      const [result] = await Promise.all([
        asyncFn(...args),
        sleep(minLoadingTime)
      ])

      // Ensure minimum loading time has passed
      const elapsed = Date.now() - startTime
      if (elapsed < minLoadingTime) {
        await sleep(minLoadingTime - elapsed)
      }

      return result
    } catch (error) {
      // Ensure minimum loading time even on error
      const elapsed = Date.now() - startTime
      if (elapsed < minLoadingTime) {
        await sleep(minLoadingTime - elapsed)
      }

      if (error instanceof Error) {
        onError?.(error)
      }
      throw error
    } finally {
      onEnd?.()
    }
  }
}

/**
 * Creates a refresh handler with loading state
 */
export const createRefreshHandler = <T extends any[]>(
  refreshFn: (...args: T) => Promise<void>,
  options: {
    minLoadingTime?: number
    onStart?: () => void
    onEnd?: () => void
    onError?: (error: Error) => void
  } = {}
) => {
  return withLoadingState(refreshFn, {
    minLoadingTime: 500, // Slightly longer for refresh actions
    ...options
  })
}

/**
 * Debounce function for preventing rapid successive calls
 */
export const debounce = <T extends any[]>(
  func: (...args: T) => void,
  wait: number
): ((...args: T) => void) => {
  let timeout: number | null = null

  return (...args: T) => {
    if (timeout) {
      clearTimeout(timeout)
    }

    timeout = window.setTimeout(() => {
      func(...args)
    }, wait)
  }
}

/**
 * Throttle function for limiting call frequency
 */
export const throttle = <T extends any[]>(
  func: (...args: T) => void,
  limit: number
): ((...args: T) => void) => {
  let inThrottle: boolean = false

  return (...args: T) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      window.setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * Retry function for failed async operations
 */
export const retry = async <T>(
  asyncFn: () => Promise<T>,
  options: {
    maxRetries?: number
    delay?: number
    backoff?: number
  } = {}
): Promise<T> => {
  const { maxRetries = 3, delay = 1000, backoff = 1.5 } = options

  let lastError: Error | null = null
  let currentDelay = delay

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await asyncFn()
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error))

      if (attempt === maxRetries) {
        throw lastError
      }

      await sleep(currentDelay)
      currentDelay *= backoff
    }
  }

  throw lastError
}