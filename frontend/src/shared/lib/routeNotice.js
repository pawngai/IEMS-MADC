const NOTICE_MESSAGE_PARAM = "notice";
const NOTICE_CONTEXT_PARAM = "noticeContext";

const parsePath = (path) => new URL(String(path || "/"), "http://local");

export const appendNoticeToPath = (path, message, context = "") => {
  if (!message) return path;
  const parsed = parsePath(path);
  parsed.searchParams.set(NOTICE_MESSAGE_PARAM, message);
  if (context) parsed.searchParams.set(NOTICE_CONTEXT_PARAM, context);
  else parsed.searchParams.delete(NOTICE_CONTEXT_PARAM);
  return `${parsed.pathname}${parsed.search}${parsed.hash}`;
};

export const readNoticeFromSearch = (search = "") => {
  const params = new URLSearchParams(search || "");
  return {
    message: params.get(NOTICE_MESSAGE_PARAM) || "",
    context: params.get(NOTICE_CONTEXT_PARAM) || "",
  };
};

export const stripNoticeFromSearch = (search = "") => {
  const params = new URLSearchParams(search || "");
  params.delete(NOTICE_MESSAGE_PARAM);
  params.delete(NOTICE_CONTEXT_PARAM);
  const next = params.toString();
  return next ? `?${next}` : "";
};
