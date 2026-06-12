export function canRecordServiceEvent({ can, Permissions }) {
  return Boolean(can?.(Permissions?.SERVICE_BOOK_ENTRY_CREATE));
}
