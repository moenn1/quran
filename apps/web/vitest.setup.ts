import "@testing-library/jest-dom/vitest";

class MemoryStorage implements Storage {
  private readonly entries = new Map<string, string>();

  clear() {
    this.entries.clear();
  }

  getItem(key: string) {
    return this.entries.has(key) ? this.entries.get(key) ?? null : null;
  }

  key(index: number) {
    return Array.from(this.entries.keys())[index] ?? null;
  }

  removeItem(key: string) {
    this.entries.delete(key);
  }

  setItem(key: string, value: string) {
    this.entries.set(key, value);
  }

  get length() {
    return this.entries.size;
  }
}

const memoryStorage = new MemoryStorage();

Object.defineProperty(window, "localStorage", {
  configurable: true,
  value: memoryStorage,
});

Object.defineProperty(globalThis, "localStorage", {
  configurable: true,
  value: memoryStorage,
});
