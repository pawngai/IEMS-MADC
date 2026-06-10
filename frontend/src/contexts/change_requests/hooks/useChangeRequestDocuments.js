import { useCallback } from "react";
import { toast } from "sonner";
import {
  getDocumentFilterOptions,
  useDocumentsBrowser,
} from "@/contexts/documents";

export { getDocumentFilterOptions };

/**
 * Encapsulates document browsing / uploading / deleting for the change-request
 * compose dialog.
 *
 * @param {Object}  deps
 * @param {boolean} deps.open  - Whether the compose dialog is open (gates the initial load)
 */
export function useChangeRequestDocuments({ open }) {
  const docs = useDocumentsBrowser({
    open,
    uploadMetadata: { source_context: "change_requests.upload" },
  });

  const attachExistingDocument = useCallback(
    (doc, { formAttachments, setFormAttachments }) => {
      if (formAttachments.some((item) => item.filename === doc.filename)) {
        toast.info("Document already attached");
        return;
      }
      setFormAttachments((prev) => [
        ...prev,
        {
          url: doc.url,
          filename: doc.filename,
          original_name: doc.filename,
          file_size: doc.file_size,
          content_type: doc.content_type,
        },
      ]);
      toast.success("Document attached to request");
    },
    []
  );

  const handleDeleteDocument = useCallback(
    async (filename, { setFormAttachments }) => {
      const deleted = await docs.deleteDocument(filename);
      if (!deleted) {
        return false;
      }
        setFormAttachments((prev) => prev.filter((item) => item.filename !== filename));
      return true;
    },
    [docs]
  );

  const uploadFile = useCallback(
    async (file, { setFormAttachments }) => {
      const data = await docs.uploadDocument(file);
      if (data?.success) {
        setFormAttachments((prev) => [
          ...prev,
          {
            url: data.url,
            filename: data.filename,
            original_name: data.original_name || file.name,
            file_size: data.file_size,
            content_type: data.content_type,
          },
        ]);
      }
      return data;
    },
    [docs]
  );

  const getAttachmentFilename = useCallback((attachment) => {
    if (attachment?.filename) return attachment.filename;
    if (typeof attachment?.url !== "string") return "";
    const lastSegment = attachment.url.split("/").pop() || "";
    return lastSegment.split("?")[0] || "";
  }, []);

  return {
    ...docs,
    attachExistingDocument,
    handleDeleteDocument,
    uploadFile,
    getAttachmentFilename,
  };
}
