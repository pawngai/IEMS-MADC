import { MutationCache, QueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/shared/lib/utils";

/**
 * App-wide QueryClient factory.
 *
 * - Query retries are disabled because the platform httpClient already retries
 *   idempotent GETs with backoff; retrying here would multiply attempts.
 * - Mutations surface failures via a single global toast unless the mutation
 *   opts out with `meta: { silenceError: true }` (e.g. when a form maps the
 *   server error onto its own fields).
 */
export function createQueryClient() {
  return new QueryClient({
    mutationCache: new MutationCache({
      onError: (error, _variables, _context, mutation) => {
        if (mutation?.meta?.silenceError) return;
        toast.error(getApiErrorMessage(error, "Request failed"));
      },
    }),
    defaultOptions: {
      queries: {
        retry: false,
        refetchOnWindowFocus: false,
        staleTime: 30_000,
      },
    },
  });
}
