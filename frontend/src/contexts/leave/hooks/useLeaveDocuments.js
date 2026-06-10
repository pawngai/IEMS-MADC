import { useCallback, useEffect, useRef } from "react";
import { toast } from "sonner";
import { useDocumentsBrowser } from "@/contexts/documents";

const createLeaveAttachment = (item, fallbackName) => ({
  url: item?.url,
  filename: item?.filename,
  original_name: item?.original_name || fallbackName || item?.filename || "",
  file_size: item?.file_size ?? null,
  content_type: item?.content_type ?? null,
});

export function useLeaveDocuments({ open, recommendedDocumentType = "" }) {
  const docs = useDocumentsBrowser({
    open,
    uploadMetadata: { source_context: "leave.apply" },
  });
  const previousRecommendedTypeRef = useRef("");
  const { documentTypeFilter, setDocumentTypeFilter } = docs;

  useEffect(() => {
    if (!open) {
      previousRecommendedTypeRef.current = recommendedDocumentType || "";
      return;
    }

    const nextRecommendedType = String(recommendedDocumentType || "").trim().toUpperCase();
    const previousRecommendedType = previousRecommendedTypeRef.current;
    const activeFilter = String(documentTypeFilter || "").trim().toUpperCase();
    const shouldSyncFilter = !activeFilter || activeFilter === previousRecommendedType;

    if (shouldSyncFilter && activeFilter !== nextRecommendedType) {
      setDocumentTypeFilter(nextRecommendedType);
    }

    previousRecommendedTypeRef.current = nextRecommendedType;
  }, [documentTypeFilter, open, recommendedDocumentType, setDocumentTypeFilter]);

  const attachExistingDocument = useCallback((document, { attachments, setAttachments }) => {
    if (attachments.some((item) => item.filename === document.filename)) {
      toast.info("Document already attached");
      return;
    }

    setAttachments((prev) => [...prev, createLeaveAttachment(document)]);
    toast.success("Document attached to leave request");
  }, []);

  const uploadFile = useCallback(async (file, { setAttachments }) => {
    const data = await docs.uploadDocument(
      file,
      recommendedDocumentType ? { document_type: recommendedDocumentType } : {}
    );
    if (data?.success) {
      setAttachments((prev) => [...prev, createLeaveAttachment(data, file.name)]);
    }
    return data;
  }, [docs, recommendedDocumentType]);

  const getAttachmentFilename = useCallback((attachment) => {
    if (attachment?.filename) return attachment.filename;
    if (typeof attachment?.url !== "string") return "";
    const lastSegment = attachment.url.split("/").pop() || "";
    return lastSegment.split("?")[0] || "";
  }, []);

  return {
    ...docs,
    attachExistingDocument,
    uploadFile,
    getAttachmentFilename,
  };
}