import { ValidationError } from '../types/errors'

export interface ValidationOptions {
  minLength?: number
  maxLength?: number
  allowEmpty?: boolean
  trimWhitespace?: boolean
}

/**
 * Validates and sanitizes user message input.
 * 
 * @param message - The message text to validate
 * @param options - Validation options including length limits
 * @returns The validated and trimmed message
 * @throws {ValidationError} When validation fails
 * 
 * @example
 * ```typescript
 * const validMessage = validateMessage("Hello world!", { maxLength: 1000 })
 * ```
 */
export function validateMessage(message: string, options: ValidationOptions = {}): string {
  const {
    minLength = 1,
    maxLength = 10000,
    allowEmpty = false,
    trimWhitespace = true
  } = options

  let validatedMessage = trimWhitespace ? message.trim() : message

  if (!allowEmpty && validatedMessage.length === 0) {
    throw new ValidationError('Message cannot be empty', 'message')
  }

  if (validatedMessage.length < minLength) {
    throw new ValidationError(`Message must be at least ${minLength} characters long`, 'message')
  }

  if (validatedMessage.length > maxLength) {
    throw new ValidationError(`Message cannot exceed ${maxLength} characters`, 'message')
  }

  // Check for suspicious patterns that might indicate XSS attempts
  const suspiciousPatterns = [
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
    /javascript:/gi,
    /on\w+\s*=/gi,
    /<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi,
    /<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>/gi,
    /<embed\b[^<]*(?:(?!<\/embed>)<[^<]*)*<\/embed>/gi
  ]

  for (const pattern of suspiciousPatterns) {
    if (pattern.test(validatedMessage)) {
      throw new ValidationError('Message contains potentially dangerous content', 'message')
    }
  }

  return validatedMessage
}

export function validateApiKey(apiKey: string, provider: string): string {
  const trimmedKey = apiKey.trim()

  if (trimmedKey.length === 0) {
    throw new ValidationError('API key cannot be empty', 'apiKey')
  }

  // Provider-specific validation patterns
  const patterns: Record<string, { pattern: RegExp; description: string }> = {
    openai: {
      pattern: /^sk-[a-zA-Z0-9]{48,}$/,
      description: 'OpenAI API key must start with "sk-" followed by at least 48 characters'
    },
    anthropic: {
      pattern: /^sk-ant-api03-[a-zA-Z0-9_-]{95}$/,
      description: 'Anthropic API key must start with "sk-ant-api03-" followed by 95 characters'
    }
  }

  const providerPattern = patterns[provider.toLowerCase()]
  if (providerPattern && !providerPattern.pattern.test(trimmedKey)) {
    throw new ValidationError(providerPattern.description, 'apiKey')
  }

  return trimmedKey
}

export function validateConversationId(conversationId: unknown): number {
  if (conversationId === null || conversationId === undefined) {
    throw new ValidationError('Conversation ID cannot be null or undefined', 'conversationId')
  }

  const numericId = typeof conversationId === 'string' ? parseInt(conversationId, 10) : Number(conversationId)

  if (isNaN(numericId) || !isFinite(numericId)) {
    throw new ValidationError('Conversation ID must be a valid number', 'conversationId')
  }

  if (numericId <= 0) {
    throw new ValidationError('Conversation ID must be a positive number', 'conversationId')
  }

  if (!Number.isInteger(numericId)) {
    throw new ValidationError('Conversation ID must be an integer', 'conversationId')
  }

  return numericId
}

export function validateUrl(url: string): string {
  const trimmedUrl = url.trim()

  if (trimmedUrl.length === 0) {
    throw new ValidationError('URL cannot be empty', 'url')
  }

  try {
    const parsedUrl = new URL(trimmedUrl)
    
    // Only allow HTTP and HTTPS protocols
    if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
      throw new ValidationError('URL must use HTTP or HTTPS protocol', 'url')
    }

    return trimmedUrl
  } catch {
    throw new ValidationError('Invalid URL format', 'url')
  }
}

export function sanitizeSearchTerm(searchTerm: string): string {
  return searchTerm
    .trim()
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/[^\w\s\-_.]/g, '') // Keep only alphanumeric, spaces, hyphens, underscores, and periods
    .substring(0, 100) // Limit length
}

export function validateTitle(title: string): string {
  const trimmedTitle = title.trim()

  if (trimmedTitle.length === 0) {
    throw new ValidationError('Title cannot be empty', 'title')
  }

  if (trimmedTitle.length > 200) {
    throw new ValidationError('Title cannot exceed 200 characters', 'title')
  }

  // Remove potential XSS content
  const sanitizedTitle = trimmedTitle.replace(/<[^>]*>/g, '')

  if (sanitizedTitle !== trimmedTitle) {
    throw new ValidationError('Title contains invalid characters', 'title')
  }

  return sanitizedTitle
}