import { useState, useCallback, useRef } from 'react'
import { useProgressState } from './useProgressState'

interface ProgressStep {
  id: string
  label: string
  completed?: boolean
}

interface UseEnhancedAsyncActionOptions {
  minLoadingTime?: number
  onSuccess?: (result?: any) => void
  onError?: (error: Error) => void
  showSuccessFor?: number
  progressSteps?: ProgressStep[]
  showProgressOverlay?: boolean
  progressTitle?: string
  progressMessage?: string
  onCancel?: () => void
}

interface AsyncActionState<T = any> {
  loading: boolean
  error: string | null
  success: boolean
  data: T | null
  progress: number
  currentStep?: string
  showOverlay: boolean
}

interface UseEnhancedAsyncActionReturn<T = any> {
  state: AsyncActionState<T>
  execute: (action: () => Promise<T>) => Promise<T | undefined>
  executeWithSteps: (action: (progress: ProgressController) => Promise<T>) => Promise<T | undefined>
  reset: () => void
  setData: (data: T | null) => void
  clearError: () => void
  hideOverlay: () => void
}

interface ProgressController {
  setProgress: (progress: number, message?: string) => void
  setCurrentStep: (stepId: string, message?: string) => void
  completeStep: (stepId: string, message?: string) => void
  updateMessage: (message: string) => void
}

export const useEnhancedAsyncAction = <T = any>(
  options: UseEnhancedAsyncActionOptions = {}
): UseEnhancedAsyncActionReturn<T> => {
  const {
    minLoadingTime = 300,
    onSuccess,
    onError,
    showSuccessFor = 3000,
    progressSteps = [],
    showProgressOverlay = false,
    progressTitle = 'Processing',
    progressMessage = 'Please wait...',
    onCancel
  } = options

  const [state, setState] = useState<AsyncActionState<T>>({
    loading: false,
    error: null,
    success: false,
    data: null,
    progress: 0,
    currentStep: undefined,
    showOverlay: false
  })

  const progressState = useProgressState({
    steps: progressSteps,
    minDuration: minLoadingTime
  })

  const cancelRef = useRef<(() => void) | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout>()

  const reset = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setState({
      loading: false,
      error: null,
      success: false,
      data: null,
      progress: 0,
      currentStep: undefined,
      showOverlay: false
    })
    progressState.actions.reset()
  }, [progressState.actions])

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  const setData = useCallback((data: T | null) => {
    setState(prev => ({ ...prev, data }))
  }, [])

  const hideOverlay = useCallback(() => {
    setState(prev => ({ ...prev, showOverlay: false }))
  }, [])

  const execute = useCallback(async (action: () => Promise<T>): Promise<T | undefined> => {
    setState(prev => ({
      ...prev,
      loading: true,
      error: null,
      success: false,
      progress: 0,
      showOverlay: showProgressOverlay
    }))

    if (showProgressOverlay) {
      progressState.actions.start(progressMessage)
    }

    const startTime = Date.now()

    try {
      const result = await action()

      // Ensure minimum loading time for better UX
      const elapsed = Date.now() - startTime
      const remainingTime = minLoadingTime - elapsed

      const completeAction = () => {
        setState(prev => ({
          ...prev,
          loading: false,
          error: null,
          success: true,
          data: result,
          progress: 100
        }))

        if (showProgressOverlay) {
          progressState.actions.complete('Complete!')
          // Keep overlay visible briefly to show completion
          setTimeout(() => {
            setState(prev => ({ ...prev, showOverlay: false }))
          }, 1000)
        }

        onSuccess?.(result)

        // Auto-clear success state after specified time
        if (showSuccessFor > 0) {
          timeoutRef.current = setTimeout(() => {
            setState(prev => ({ ...prev, success: false }))
          }, showSuccessFor)
        }
      }

      if (remainingTime > 0) {
        setTimeout(completeAction, remainingTime)
      } else {
        completeAction()
      }

      return result
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error.message,
        success: false,
        showOverlay: false
      }))

      if (showProgressOverlay) {
        progressState.actions.setError(error.message)
      }

      onError?.(error)
      throw error
    }
  }, [minLoadingTime, onSuccess, onError, showSuccessFor, showProgressOverlay, progressMessage, progressState.actions])

  const executeWithSteps = useCallback(async (
    action: (progress: ProgressController) => Promise<T>
  ): Promise<T | undefined> => {
    setState(prev => ({
      ...prev,
      loading: true,
      error: null,
      success: false,
      progress: 0,
      showOverlay: true
    }))

    progressState.actions.start(progressMessage)

    // Create progress controller for the action
    const progressController: ProgressController = {
      setProgress: (progress: number, message?: string) => {
        setState(prev => ({ ...prev, progress }))
        progressState.actions.setProgress(progress, message)
      },
      setCurrentStep: (stepId: string, message?: string) => {
        setState(prev => ({ ...prev, currentStep: stepId }))
        progressState.actions.setCurrentStep(stepId, message)
      },
      completeStep: (stepId: string, message?: string) => {
        progressState.actions.completeStep(stepId, message)
      },
      updateMessage: (message: string) => {
        progressState.actions.setProgress(progressState.progress, message)
      }
    }

    const startTime = Date.now()

    try {
      const result = await action(progressController)

      // Ensure minimum loading time for better UX
      const elapsed = Date.now() - startTime
      const remainingTime = minLoadingTime - elapsed

      const completeAction = () => {
        setState(prev => ({
          ...prev,
          loading: false,
          error: null,
          success: true,
          data: result,
          progress: 100
        }))

        progressState.actions.complete('Complete!')

        // Keep overlay visible briefly to show completion
        setTimeout(() => {
          setState(prev => ({ ...prev, showOverlay: false }))
        }, 1500)

        onSuccess?.(result)

        // Auto-clear success state after specified time
        if (showSuccessFor > 0) {
          timeoutRef.current = setTimeout(() => {
            setState(prev => ({ ...prev, success: false }))
          }, showSuccessFor)
        }
      }

      if (remainingTime > 0) {
        setTimeout(completeAction, remainingTime)
      } else {
        completeAction()
      }

      return result
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error.message,
        success: false,
        showOverlay: false
      }))

      progressState.actions.setError(error.message)
      onError?.(error)
      throw error
    }
  }, [minLoadingTime, onSuccess, onError, showSuccessFor, progressMessage, progressState.actions])

  // Handle cancel functionality
  const handleCancel = useCallback(() => {
    if (cancelRef.current) {
      cancelRef.current()
    }
    reset()
    onCancel?.()
  }, [reset, onCancel])

  return {
    state: {
      ...state,
      // Merge with progress state for overlay
      progress: progressState.progress || state.progress,
      currentStep: progressState.currentStep || state.currentStep
    },
    execute,
    executeWithSteps,
    reset,
    setData,
    clearError,
    hideOverlay
  }
}

// Specialized hook for file operations with progress tracking
export const useFileOperation = (options: UseEnhancedAsyncActionOptions = {}) => {
  const fileSteps = [
    { id: 'validate', label: 'Validating file...' },
    { id: 'upload', label: 'Uploading file...' },
    { id: 'process', label: 'Processing...' },
    { id: 'complete', label: 'Finalizing...' }
  ]

  return useEnhancedAsyncAction({
    ...options,
    progressSteps: options.progressSteps || fileSteps,
    showProgressOverlay: true,
    progressTitle: options.progressTitle || 'File Operation',
    progressMessage: options.progressMessage || 'Processing file...'
  })
}

// Specialized hook for data export operations
export const useExportOperation = (options: UseEnhancedAsyncActionOptions = {}) => {
  const exportSteps = [
    { id: 'prepare', label: 'Preparing data...' },
    { id: 'format', label: 'Formatting export...' },
    { id: 'generate', label: 'Generating file...' },
    { id: 'download', label: 'Preparing download...' }
  ]

  return useEnhancedAsyncAction({
    ...options,
    progressSteps: options.progressSteps || exportSteps,
    showProgressOverlay: true,
    progressTitle: options.progressTitle || 'Export Data',
    progressMessage: options.progressMessage || 'Preparing your export...'
  })
}

export default useEnhancedAsyncAction