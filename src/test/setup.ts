import '@testing-library/jest-dom'

// Mock fetch globally for tests
global.fetch = vi.fn()

// Mock Tauri API 
Object.defineProperty(window, '__TAURI__', {
  value: {
    tauri: {
      invoke: vi.fn(),
    },
    event: {
      listen: vi.fn(),
      emit: vi.fn(),
    },
    dialog: {
      open: vi.fn(),
      save: vi.fn(),
      message: vi.fn(),
    },
    fs: {
      writeTextFile: vi.fn(),
      readTextFile: vi.fn(),
    },
  },
})

// Setup after each test
afterEach(() => {
  vi.clearAllMocks()
})