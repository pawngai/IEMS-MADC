import ServiceRecordCard from "@/contexts/service_book/records/components/ServiceRecordCard";

const ServiceRecordTimeline = ({
  events,
  canCorrect,
  canVoid,
  canAttach,
  onCorrect,
  onVoid,
  onAttach,
}) => {
  // Sort events by recorded_at descending (newest first)
  const sorted = [...events].sort((a, b) => {
    const dateA = new Date(a.recorded_at || a.created_at || 0);
    const dateB = new Date(b.recorded_at || b.created_at || 0);
    return dateB - dateA;
  });

  return (
    <div className="space-y-3" data-testid="service-record-timeline">
      {/* Timeline connector */}
      <div className="relative">
        {sorted.map((event, idx) => (
          <div key={event.id || event.service_event_id || idx} className="relative">
            {/* Connector line */}
            {idx < sorted.length - 1 && (
              <div className="absolute left-[25px] top-[60px] bottom-[-12px] w-px bg-outline-variant" />
            )}
            {/* Timeline dot */}
            <div className="absolute left-[19px] top-[22px] w-3 h-3 rounded-full border-2 border-outline bg-surface z-10" />
            <div className="ml-12">
              <ServiceRecordCard
                event={event}
                canCorrect={canCorrect}
                canVoid={canVoid}
                canAttach={canAttach}
                onCorrect={onCorrect}
                onVoid={onVoid}
                onAttach={onAttach}
              />
            </div>
            {idx < sorted.length - 1 && <div className="h-3" />}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ServiceRecordTimeline;