import { useEffect, useState } from "react";
import { apiClient } from "@/platform/api/httpClient";

/**
 * Fetches an image via the authenticated API client and returns a blob URL
 * suitable for use as an <img src>.  Revokes the object URL on unmount.
 *
 * @param {string|null|undefined} path  Relative API path, e.g. "/documents/photos/abc.jpg"
 * @returns {string} blob URL or empty string while loading / on error
 */
export function useAuthImage(path) {
  const [src, setSrc] = useState("");

  useEffect(() => {
    if (!path) {
      setSrc("");
      return;
    }

    let revoked = false;
    let objectUrl = "";

    // Strip leading /api if present; apiClient.baseURL already includes it.
    const cleanPath = path.startsWith("/api/") ? path.slice(4) : path;

    apiClient
      .get(cleanPath, { responseType: "blob" })
      .then((res) => {
        if (revoked) return;
        objectUrl = URL.createObjectURL(res.data);
        setSrc(objectUrl);
      })
      .catch(() => {
        if (!revoked) setSrc("");
      });

    return () => {
      revoked = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [path]);

  return src;
}
