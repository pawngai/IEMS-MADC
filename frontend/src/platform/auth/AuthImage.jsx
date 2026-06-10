import React from "react";
import { useAuthImage } from "@/platform/auth/useAuthImage";

/**
 * Renders an <img> that fetches its source through the authenticated API client.
 * Accepts the same props as <img> plus `path` (the relative backend path).
 * While loading or on error, renders `fallback` if provided, otherwise nothing.
 */
export function AuthImage({ path, fallback = null, alt = "", ...imgProps }) {
  const src = useAuthImage(path);

  if (!src) return fallback;
  return <img src={src} alt={alt} {...imgProps} />;
}
