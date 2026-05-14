// Base class for observer pattern
export default class Observable {
  constructor() {
    this.observers = []
  }

  // Add observer to list
  addObserver(observer) {
    // Make sure it has an update method
    if (typeof observer.update !== 'function') {
      throw new Error('Observer must implement update method')
    }

    // Don't add duplicates
    if (!this.observers.includes(observer)) {
      this.observers.push(observer)
    }
  }

  // Remove observer from list
  removeObserver(observer) {
    const index = this.observers.indexOf(observer)
    if (index !== -1) {
      this.observers.splice(index, 1)
    }
  }

  // Tell all observers something changed
  notifyObservers(data) {
    this.observers.forEach(observer => {
      observer.update(data)
    })
  }
}
