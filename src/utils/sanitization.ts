export function sanitizeHtml(html: string): string {
  // Create a temporary div element to leverage browser's built-in HTML parsing
  const tempDiv = document.createElement('div')
  tempDiv.textContent = html
  return tempDiv.innerHTML
}

export function sanitizeText(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;')
}

/**
 * Sanitizes content for safe display in HTML while preserving formatting.
 * Prevents XSS attacks by escaping HTML entities and converting line breaks.
 * 
 * @param content - The content to sanitize
 * @returns HTML-safe content with preserved formatting
 * 
 * @example
 * ```typescript
 * const safeHtml = sanitizeForDisplay("Hello\nWorld & <script>")
 * // Returns: "Hello<br>World &amp; &lt;script&gt;"
 * ```
 */
export function sanitizeForDisplay(content: string): string {
  // First escape HTML entities
  let sanitized = sanitizeText(content)
  
  // Convert line breaks to HTML breaks for display
  sanitized = sanitized.replace(/\n/g, '<br>')
  
  // Convert double spaces to preserve formatting
  sanitized = sanitized.replace(/  /g, ' &nbsp;')
  
  return sanitized
}

export function stripHtml(html: string): string {
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = html
  return tempDiv.textContent || tempDiv.innerText || ''
}

export function sanitizeUrl(url: string): string {
  const trimmedUrl = url.trim()
  
  // Remove javascript: protocol and other dangerous protocols
  if (/^(javascript|data|vbscript|file|about):/i.test(trimmedUrl)) {
    return ''
  }
  
  // Ensure the URL uses a safe protocol
  if (!/^https?:\/\//i.test(trimmedUrl)) {
    return `https://${trimmedUrl.replace(/^\/+/, '')}`
  }
  
  return trimmedUrl
}

export function sanitizeClassName(className: string): string {
  // Remove any characters that aren't valid in CSS class names
  return className
    .replace(/[^a-zA-Z0-9_-]/g, '')
    .replace(/^[0-9]/, '_$&') // Class names can't start with a number
}

export function sanitizeFilename(filename: string): string {
  return filename
    .replace(/[^a-zA-Z0-9._-]/g, '_')
    .replace(/^\.+/, '')
    .substring(0, 255)
}

export const SAFE_HTML_TAGS = new Set([
  'p', 'br', 'strong', 'em', 'u', 'b', 'i', 'span', 'div',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'ul', 'ol', 'li',
  'blockquote', 'pre', 'code'
])

export const SAFE_HTML_ATTRIBUTES = new Set([
  'class', 'id', 'title', 'alt'
])

export function allowOnlySafeTags(html: string): string {
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = html
  
  function sanitizeElement(element: Element): void {
    const tagName = element.tagName.toLowerCase()
    
    if (!SAFE_HTML_TAGS.has(tagName)) {
      // Replace unsafe tags with their text content
      const textNode = document.createTextNode(element.textContent || '')
      element.parentNode?.replaceChild(textNode, element)
      return
    }
    
    // Remove unsafe attributes
    const attributesToRemove: string[] = []
    for (let i = 0; i < element.attributes.length; i++) {
      const attr = element.attributes[i]
      if (!SAFE_HTML_ATTRIBUTES.has(attr.name.toLowerCase())) {
        attributesToRemove.push(attr.name)
      }
    }
    
    attributesToRemove.forEach(attrName => {
      element.removeAttribute(attrName)
    })
    
    // Recursively sanitize child elements
    const children = Array.from(element.children)
    children.forEach(child => sanitizeElement(child))
  }
  
  Array.from(tempDiv.children).forEach(child => sanitizeElement(child))
  
  return tempDiv.innerHTML
}