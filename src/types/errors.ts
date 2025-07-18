export class AuthError extends Error {
  readonly name = 'AuthError'
  readonly statusCode: number
  readonly isRetryable = false

  constructor(message: string, statusCode: number = 401) {
    super(message)
    this.statusCode = statusCode
  }
}

export class NetworkError extends Error {
  readonly name = 'NetworkError'
  readonly statusCode?: number
  readonly isRetryable = true
  readonly retryAfter?: number

  constructor(message: string, statusCode?: number, retryAfter?: number) {
    super(message)
    this.statusCode = statusCode
    this.retryAfter = retryAfter
  }
}

export class RateLimitError extends Error {
  readonly name = 'RateLimitError'
  readonly statusCode = 429
  readonly isRetryable = true
  readonly retryAfter: number

  constructor(message: string, retryAfter: number = 60) {
    super(message)
    this.retryAfter = retryAfter
  }
}

export class ValidationError extends Error {
  readonly name = 'ValidationError'
  readonly field: string
  readonly isRetryable = false

  constructor(message: string, field: string) {
    super(message)
    this.field = field
  }
}

export class TimeoutError extends Error {
  readonly name = 'TimeoutError'
  readonly isRetryable = true
  readonly timeout: number

  constructor(message: string, timeout: number) {
    super(message)
    this.timeout = timeout
  }
}

export type ApiError = AuthError | NetworkError | RateLimitError | ValidationError | TimeoutError

export function createErrorFromResponse(response: Response, message?: string): ApiError {
  const statusCode = response.status
  const statusText = response.statusText || 'Unknown error'
  const errorMessage = message || `${statusCode}: ${statusText}`

  switch (statusCode) {
    case 401:
    case 403:
      return new AuthError(errorMessage, statusCode)
    case 429: {
      const retryAfter = parseInt(response.headers.get('Retry-After') || '60', 10)
      return new RateLimitError(errorMessage, retryAfter)
    }
    case 400:
    case 422:
      return new ValidationError(errorMessage, 'request')
    case 500:
    case 502:
    case 503:
    case 504:
      return new NetworkError(errorMessage, statusCode)
    default:
      if (statusCode >= 400 && statusCode < 500) {
        return new ValidationError(errorMessage, 'request')
      }
      return new NetworkError(errorMessage, statusCode)
  }
}

export function isRetryableError(error: Error): boolean {
  if (error instanceof NetworkError || error instanceof RateLimitError || error instanceof TimeoutError) {
    return error.isRetryable
  }
  return false
}

export function getRetryDelay(error: Error, attempt: number): number {
  if (error instanceof RateLimitError) {
    return error.retryAfter * 1000
  }
  
  if (error instanceof NetworkError && error.retryAfter) {
    return error.retryAfter * 1000
  }

  // Exponential backoff with jitter
  const baseDelay = Math.min(1000 * Math.pow(2, attempt), 5000)
  const jitter = Math.random() * 0.1 * baseDelay
  return baseDelay + jitter
}