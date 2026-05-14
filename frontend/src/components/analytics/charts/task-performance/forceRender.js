/**
 * Utility to force browser reflow/repaint which helps with chart rendering
 */

/**
 * Forces layout recalculation by triggering multiple browser reflows
 * This helps resolve issues where charts don't appear until zoom changes
 * @param {HTMLElement} element - The container element to force render
 */
export function forceRender(element) {
  if (!element) return

  // Set explicit dimensions
  const originalDisplay = element.style.display

  // Multiple techniques to force reflow

  // 1. Toggle display
  element.style.display = 'none'
  void element.offsetHeight // Force reflow
  element.style.display = originalDisplay

  // 2. Use transform
  element.style.transform = 'translateZ(0)'
  void element.offsetHeight // Force reflow

  // 3. Force browser layout recalculation
  const temp = element.getBoundingClientRect()

  // 4. Force repaints in different ways
  element.style.transform = ''
  void element.offsetHeight

  // 5. Briefly adjust scroll position
  const scrollPosition = window.scrollY
  window.scrollTo(0, scrollPosition + 1)
  window.scrollTo(0, scrollPosition)

  // 6. Briefly adjust zoom
  document.body.style.zoom = '100.1%'
  document.body.style.zoom = '100%'

  // Return container dimensions for debugging
  return {
    width: element.clientWidth,
    height: element.clientHeight,
    rect: temp,
  }
}
