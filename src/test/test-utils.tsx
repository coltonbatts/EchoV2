import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'

// Custom render function that includes any providers
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, options)
}

// Helper to create mock API responses
export const createMockApiResponse = (data: any, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: () => Promise.resolve(data),
  text: () => Promise.resolve(JSON.stringify(data)),
})

// Helper to create mock fetch
export const mockFetch = (response: any, status = 200) => {
  const mockResponse = createMockApiResponse(response, status)
  vi.mocked(fetch).mockResolvedValueOnce(mockResponse as any)
}

// Helper to create mock error response
export const mockFetchError = (error: string) => {
  vi.mocked(fetch).mockRejectedValueOnce(new Error(error))
}

// Mock message data
export const createMockMessage = (overrides = {}) => ({
  id: Date.now().toString(),
  text: 'Test message',
  sender: 'user' as const,
  timestamp: new Date(),
  ...overrides,
})

// Mock conversation data
export const createMockConversation = (overrides = {}) => ({
  id: 1,
  title: 'Test Conversation',
  messages: [],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  ...overrides,
})

// Export everything
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'
export { customRender as render }