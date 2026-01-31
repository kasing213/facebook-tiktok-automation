import { useState, useCallback } from 'react'
import { withLoadingState, createRefreshHandler } from '../utils/async'

interface UseAsyncActionOptions {
  minLoadingTime?: number
  onSuccess?: (result?: any) => void
  onError?: (error: Error) => void
  showSuccessFor?: number
}

interface AsyncActionState<T = any> {
  loading: boolean
  error: string | null
  success: boolean
  data: T | null
}

interface UseAsyncActionReturn<T = any> {
  state: AsyncActionState<T>
  execute: (action: () => Promise<T>) => Promise<T | undefined>
  refresh: (refreshFn: () => Promise<void>) => Promise<void>
  reset: () => void
  setData: (data: T | null) => void
  clearError: () => void
}

export const useAsyncAction = <T = any>(
  options: UseAsyncActionOptions = {}
): UseAsyncActionReturn<T> => {
  const {
    minLoadingTime = 300,
    onSuccess,
    onError,
    showSuccessFor = 3000
  } = options

  const [state, setState] = useState<AsyncActionState<T>>({
    loading: false,
    error: null,
    success: false,
    data: null
  })

  const reset = useCallback(() => {
    setState({
      loading: false,
      error: null,
      success: false,
      data: null
    })
  }, [])

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  const setData = useCallback((data: T | null) => {
    setState(prev => ({ ...prev, data }))
  }, [])

  const execute = useCallback(async (action: () => Promise<T>): Promise<T | undefined> => {
    setState(prev => ({
      ...prev,
      loading: true,
      error: null,
      success: false
    }))

    const wrappedAction = withLoadingState(action, {
      minLoadingTime,
      onError: (error) => {
        setState(prev => ({
          ...prev,
          loading: false,
          error: error.message,
          success: false
        }))
        onError?.(error)
      }
    })

    try {
      const result = await wrappedAction()

      setState(prev => ({
        ...prev,
        loading: false,
        error: null,
        success: true,
        data: result
      }))

      onSuccess?.(result)

      // Auto-clear success state after specified time
      if (showSuccessFor > 0) {
        setTimeout(() => {
          setState(prev => ({ ...prev, success: false }))
        }, showSuccessFor)
      }

      return result
    } catch (error) {
      // Error handling is done in the withLoadingState wrapper
      throw error
    }
  }, [minLoadingTime, onSuccess, onError, showSuccessFor])

  const refresh = useCallback(async (refreshFn: () => Promise<void>): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    const refreshHandler = createRefreshHandler(refreshFn, {
      minLoadingTime: 500, // Slightly longer for refresh
      onStart: () => {
        setState(prev => ({ ...prev, loading: true, error: null }))
      },
      onEnd: () => {
        setState(prev => ({ ...prev, loading: false }))
      },
      onError: (error) => {
        setState(prev => ({
          ...prev,
          loading: false,
          error: error.message
        }))
        onError?.(error)
      }
    })

    try {
      await refreshHandler()
    } catch (error) {
      // Error handled in refresh handler
      throw error
    }
  }, [onError])

  return {
    state,
    execute,
    refresh,
    reset,
    setData,
    clearError
  }
}

// Specialized hook for refresh actions
export const useRefreshAction = (
  refreshFn: () => Promise<void>,
  options: Omit<UseAsyncActionOptions, 'showSuccessFor'> = {}
) => {
  const { refresh, state, clearError } = useAsyncAction({
    ...options,
    showSuccessFor: 0 // Don't show success for refresh actions
  })

  const handleRefresh = useCallback(async () => {
    try {
      await refresh(refreshFn)
    } catch (error) {
      // Error is already handled in the refresh function
      console.error('Refresh failed:', error)
    }
  }, [refresh, refreshFn])

  return {
    loading: state.loading,
    error: state.error,
    refresh: handleRefresh,
    clearError
  }
}

// Specialized hook for form submissions
export const useFormSubmission = <T = any>(
  options: UseAsyncActionOptions = {}
) => {
  return useAsyncAction<T>({
    minLoadingTime: 500,
    showSuccessFor: 2000,
    ...options
  })
}

// Specialized hook for data fetching
export const useDataFetch = <T = any>(
  options: UseAsyncActionOptions = {}
) => {
  return useAsyncAction<T>({
    minLoadingTime: 200,
    showSuccessFor: 0,
    ...options
  })
}