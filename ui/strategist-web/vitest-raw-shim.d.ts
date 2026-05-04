/** Vitest/Vite raw imports used by constitutional page source tests (`import x from "./page.tsx?raw"`). */
declare module "*?raw" {
  const content: string;
  export default content;
}
