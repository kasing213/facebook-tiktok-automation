import { useState, useCallback, useRef } from 'react'

interface ProgressStep {
  id: string
  label: string
  completed?: boolean
}

interface ProgressState {
  loading: boolean
  progress: number
  currentStep?: string
  steps: ProgressStep[]
  error?: string
  message?: string
}

interface UseProgressStateOptions {
  steps?: ProgressStep[]
  onComplete?: () => void
  onError?: (error: string) => void
  minDuration?: number
}

export const useProgressState = (options: UseProgressStateOptions = {}) => {
  const { steps = [], onComplete, onError, minDuration = 300 } = options

  const [state, setState] = useState<ProgressState>({
    loading: false,
    progress: 0,
    currentStep: undefined,
    steps: steps,
    error: undefined,
    message: undefined
  })

  const startTimeRef = useRef<number>()
  const timeoutRef = useRef<NodeJS.Timeout>()

  const start = useCallback((message?: string) => {
    startTimeRef.current = Date.now()
    setState(prev => ({
      ...prev,
      loading: true,
      progress: 0,
      error: undefined,
      message,
      currentStep: steps.length > 0 ? steps[0].id : undefined
    }))
  }, [steps])

  const setProgress = useCallback((progress: number, message?: string) => {
    setState(prev => ({
      ...prev,
      progress: Math.min(100, Math.max(0, progress)),
      message
    }))
  }, [])

  const setCurrentStep = useCallback((stepId: string, message?: string) => {
    setState(prev => ({
      ...prev,
      currentStep: stepId,
      message,
      steps: prev.steps.map(step => ({
        ...step,
        completed: step.id === stepId ? false : step.completed
      }))
    }))
  }, [])

  const completeStep = useCallback((stepId: string, message?: string) => {
    setState(prev => {
      const updatedSteps = prev.steps.map(step => ({
        ...step,
        completed: step.id === stepId ? true : step.completed
      }))

      const currentIndex = prev.steps.findIndex(s => s.id === stepId)
      const nextStep = prev.steps[currentIndex + 1]

      return {
        ...prev,
        message,
        steps: updatedSteps,
        currentStep: nextStep?.id || prev.currentStep,
        progress: ((currentIndex + 1) / prev.steps.length) * 100
      }
    })
  }, [])

  const setError = useCallback((error: string) => {
    setState(prev => ({
      ...prev,
      error,
      loading: false
    }))
    onError?.(error)
  }, [onError])

  const complete = useCallback((message?: string) => {
    const ensureMinDuration = () => {
      setState(prev => ({
        ...prev,
        loading: false,
        progress: 100,
        message: message || 'Complete',
        steps: prev.steps.map(step => ({ ...step, completed: true }))
      }))
      onComplete?.()
    }

    if (startTimeRef.current && minDuration > 0) {
      const elapsed = Date.now() - startTimeRef.current
      const remaining = minDuration - elapsed

      if (remaining > 0) {
        timeoutRef.current = setTimeout(ensureMinDuration, remaining)
      } else {
        ensureMinDuration()
      }
    } else {
      ensureMinDuration()
    }
  }, [minDuration, onComplete])

  const reset = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setState({
      loading: false,
      progress: 0,
      currentStep: undefined,
      steps: steps.map(step => ({ ...step, completed: false })),
      error: undefined,
      message: undefined
    })
  }, [steps])

  // Auto-advancing progress simulation
  const simulateProgress = useCallback(async (
    duration: number = 2000,
    steps: number = 10,
    message?: string
  ) => {
    start(message || 'Processing...')

    const interval = duration / steps

    for (let i = 1; i <= steps; i++) {
      await new Promise(resolve => setTimeout(resolve, interval))
      setProgress((i / steps) * 100)
    }
  }, [start, setProgress])

  return {
    state,
    actions: {
      start,
      setProgress,
      setCurrentStep,
      completeStep,
      setError,
      complete,
      reset,
      simulateProgress
    },
    // Convenience getters
    isLoading: state.loading,
    progress: state.progress,
    error: state.error,
    message: state.message,
    currentStep: state.currentStep,
    steps: state.steps
  }
}

export default useProgressState