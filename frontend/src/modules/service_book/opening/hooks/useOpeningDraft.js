import { useMemo, useState } from "react";
import { getOpeningCompletion } from "@/modules/service_book/opening/services/openingDomainService";

export const useOpeningDraft = (initialDraft) => {
  const [draft, setDraft] = useState(initialDraft);

  const updatePart = (partId, values) => {
    setDraft((current) => ({
      ...(current || {}),
      parts: {
        ...(current?.parts || {}),
        [partId]: {
          ...(current?.parts?.[partId] || {}),
          ...(values || {}),
        },
      },
    }));
  };

  const completion = useMemo(() => getOpeningCompletion(draft), [draft]);

  return {
    draft,
    setDraft,
    updatePart,
    completion,
  };
};

export default useOpeningDraft;
