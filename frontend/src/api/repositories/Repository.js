// Base Repository class for data access
export default class Repository {
  constructor() {
    if (this.constructor === Repository) {
      throw new Error(
        'Repository is an abstract class and cannot be instantiated directly',
      )
    }
  }

  // Fetch all items
  async findAll() {
    throw new Error('Method findAll() must be implemented by subclass')
  }

  // Find an item by ID
  // id - Item identifier
  async findById(id) {
    throw new Error('Method findById() must be implemented by subclass')
  }

  // Save an item
  // item - Data to save
  async save(item) {
    throw new Error('Method save() must be implemented by subclass')
  }

  // Delete an item
  // id - Item identifier to remove
  async delete(id) {
    throw new Error('Method delete() must be implemented by subclass')
  }
}
