import { documentsAPI } from "@/modules/documents";

const extractAttachmentFilename = (attachment) => {
  const filename = String(attachment?.filename || "").trim();
  if (filename) return filename;
  const directUrl = String(attachment?.url || "").trim();
  if (directUrl.startsWith("/api/documents/files/")) {
    return directUrl.slice("/api/documents/files/".length).split("/")[0] || "";
  }
  return "";
};

const LeaveAttachmentLinks = ({ attachments = [] }) => {
  const visibleAttachments = (attachments || []).filter((attachment) => extractAttachmentFilename(attachment));

  if (visibleAttachments.length === 0) {
    return null;
  }

  return (
    <div className="mt-1.5 flex flex-wrap gap-1.5">
      {visibleAttachments.map((attachment, index) => {
        const filename = extractAttachmentFilename(attachment);
        const label = attachment?.original_name || attachment?.filename || `Attachment ${index + 1}`;
        return (
          <button
            type="button"
            key={`${attachment?.filename || attachment?.url || "attachment"}-${index}`}
            onClick={() => documentsAPI.openDocument(filename)}
            className="inline-flex items-center rounded-full border border-slate-200 px-2.5 py-0.5 text-[11px] font-medium text-slate-600 hover:bg-slate-50"
          >
            {label}
          </button>
        );
      })}
    </div>
  );
};

export default LeaveAttachmentLinks;
