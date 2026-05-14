// Tracks components that need updates when participant selection changes
export default class ParticipantObserver {
  constructor() {
    this.components = []
  }

  // Register a component to receive updates
  addComponent(component) {
    if (!this.components.includes(component)) {
      this.components.push(component)
    }
  }

  // Remove a component from update list
  removeComponent(component) {
    const index = this.components.indexOf(component)
    if (index !== -1) {
      this.components.splice(index, 1)
    }
  }

  // Notify all registered components
  update(data) {
    this.components.forEach(component => {
      if (typeof component.onParticipantUpdate === 'function') {
        component.onParticipantUpdate(data)
      }
    })
  }
}
