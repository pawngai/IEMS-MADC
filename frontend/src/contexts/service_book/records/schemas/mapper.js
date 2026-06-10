export function mapRecordServiceEventFormToCommand(values) {
  return {
    employee_id: values.employee_id,
    event_type: values.event_type,
    effective_from: values.effective_from,
    order_number: values.order_number,
    order_date: values.order_date,
    issuing_authority: values.issuing_authority,
    payload: values.payload || {},
  };
}
