export function getSearchParam(name: string): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get(name);
}

export function updateSearchParam(name: string, value: string | null) {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (value && value.length) {
    url.searchParams.set(name, value);
  } else {
    url.searchParams.delete(name);
  }
  const nextUrl = `${url.pathname}${url.search}${url.hash}`;
  window.history.replaceState({}, "", nextUrl);
}

export function isOpenParam(name: string): boolean {
  const value = getSearchParam(name);
  return value === "open" || value === "1" || value === "true";
}
