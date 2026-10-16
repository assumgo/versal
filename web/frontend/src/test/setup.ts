import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';
afterEach(cleanup);

// jsdom has no media query engine; viewport behavior is covered in Playwright.
Object.defineProperty(window, 'matchMedia', { value: () => ({ matches: false, addEventListener() {}, removeEventListener() {} }) });
