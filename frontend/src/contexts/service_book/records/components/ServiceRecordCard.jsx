import { useState } from "react";
import {
  EVENT_TYPE_LABELS,
  EVENT_TYPE_COLORS,
  getFallbackServiceRecordSchema,
  getServiceRecordDisplayType,
} from "@/contexts/service_book/records/model/serviceBookRecordsModel";
import { Card, CardContent } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  Briefcase,
  Award,
  Calendar,
  DollarSign,
  Shield,
  FileText,
  Edit3,
  Trash2,
  Paperclip,
  Clock,
  User,
} from "lucide-react";

const EVENT_TYPE_ICONS = {
  APPOINTMENT: Briefcase,
  PROMOTION: Award,
  PAY: DollarSign,
  INCREMENT: DollarSign,
  ALLOWANCE: DollarSign,
  FINANCIAL_UPGRADATION: DollarSign,
  CPC_PAY_FIXATION: DollarSign,
  DISCIPLINARY: Shield,
  CUSTOM: FileText,
  GENERIC: FileText,
};

const FIELD_DEFINITIONS = getFallbackServiceRecordSchema().fieldDefinitions;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function toTitleCase(value) {
  return String(value || "")
    .trim()
    .replace(/[_-]+/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatDate(dateStr) {
  if (!dateStr) return "\u2014";
  try {
    return new Date(dateStr).toLocaleDateString("en-IN", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function formatDateTime(dateStr) {
  if (!dateStr) return "\u2014";
  try {
    return new Date(dateStr).toLocaleString("en-IN", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

function formatFieldLabel(key) {
  const configuredLabel = FIELD_DEFINITIONS[key]?.label;
  if (configuredLabel) return configuredLabel;
  return toTitleCase(key);
}

function formatFieldValue(key, value) {
  if (value === null || value === undefined || value === "") return "\u2014";
  if (Array.isArray(value)) {
    return value.map((item) => formatFieldValue(key, item)).join(", ");
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "object") {
    const nestedEntries = Object.entries(value).filter(([nestedKey]) => !nestedKey.startsWith("_"));
    if (nestedEntries.length === 0) return "\u2014";
    return nestedEntries
      .map(([nestedKey, nestedValue]) => `${formatFieldLabel(nestedKey)}: ${formatFieldValue(nestedKey, nestedValue)}`)
      .join("; ");
  }

  const text = String(value).trim();
  const fieldType = FIELD_DEFINITIONS[key]?.type;

  if (!text) return "\u2014";
  if (fieldType === "date" || /^\d{4}-\d{2}-\d{2}$/.test(text)) return formatDate(text);
  if (fieldType === "select") return toTitleCase(text);
  if (text === text.toUpperCase() && /[A-Z]/.test(text)) return toTitleCase(text);

  return text;
}

function getNestedFieldEntries(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];
  return Object.entries(value).filter(([nestedKey]) => !nestedKey.startsWith("_"));
}

function resolveActorLabel(event) {
  const candidate =
    event.actor_name
    || event.actor_display
    || event.recorded_by_name
    || event.recorded_by
    || event.actor_id;

  if (!candidate) return null;

  const normalized = String(candidate).trim();
  if (!normalized) return null;
  if (UUID_PATTERN.test(normalized)) return "Internal user";
  return normalized;
}

const ServiceRecordCard = ({
  event,
  canCorrect,
  canVoid,
  canAttach,
  onCorrect,
  onVoid,
  onAttach,
}) => {
  const eventType = event.event_type || event.type || "GENERIC";
  const displayEventType = getServiceRecordDisplayType(event);
  const Icon = EVENT_TYPE_ICONS[displayEventType] || EVENT_TYPE_ICONS[eventType] || FileText;
  const colorClass =
    EVENT_TYPE_COLORS[displayEventType]
    || EVENT_TYPE_COLORS[eventType]
    || EVENT_TYPE_COLORS.GENERIC;
  const label = EVENT_TYPE_LABELS[displayEventType] || EVENT_TYPE_LABELS[eventType] || eventType;
  const isVoided = event.voided || event.status === "VOIDED";
  const isCorrected = event.corrected || event.status === "CORRECTED";
  const actorLabel = resolveActorLabel(event);
  const [showAllFields, setShowAllFields] = useState(false);

  const payload = event.payload || {};
  const payloadEntries = Object.entries(payload).filter(
    ([k]) => !k.startsWith("_")
  );
  const hiddenFieldCount = Math.max(payloadEntries.length - 6, 0);
  const visiblePayloadEntries = showAllFields ? payloadEntries : payloadEntries.slice(0, 6);
  const hiddenFieldLabel = hiddenFieldCount === 1 ? "field" : "fields";

  return (
    <Card
      className={`transition-all ${
        isVoided
          ? "opacity-60 border-red-200 bg-red-50/30"
          : "hover:shadow-md"
      }`}
      data-testid={`service-record-${event.id || event.service_event_id}`}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div
            className={`p-2 rounded-lg flex-shrink-0 ${colorClass
              .replace("text-", "")
              .split(" ")[0]}`}
          >
            <Icon className="w-5 h-5" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className="font-semibold text-foreground">{label}</span>
              {event.part_code && (
                <Badge variant="outline" className="text-xs bg-surface-container-low">
                  Part {event.part_code}
                </Badge>
              )}
              {isVoided && (
                <Badge
                  variant="outline"
                  className="text-xs bg-red-100 text-red-700 border-red-300"
                >
                  VOIDED
                </Badge>
              )}
              {isCorrected && (
                <Badge
                  variant="outline"
                  className="text-xs bg-amber-100 text-amber-700 border-amber-300"
                >
                  CORRECTED
                </Badge>
              )}
            </div>

            {/* Effective dates */}
            <div className="flex items-center gap-4 text-xs text-muted-foreground mb-2">
              {event.effective_from && (
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  From: {formatDate(event.effective_from)}
                </span>
              )}
              {event.effective_to && (
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  To: {formatDate(event.effective_to)}
                </span>
              )}
              {event.recorded_at && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Recorded: {formatDateTime(event.recorded_at)}
                </span>
              )}
              {actorLabel && (
                <span className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  By: {actorLabel}
                </span>
              )}
            </div>

            {/* Payload summary */}
            {payloadEntries.length > 0 && (
              <div className="bg-surface-container-low rounded-md p-2 text-xs space-y-1 mb-2">
                {visiblePayloadEntries.map(([key, value]) => (
                  <div key={key} className="flex gap-2">
                    <span className="font-medium text-muted-foreground min-w-[120px]">
                      {formatFieldLabel(key)}:
                    </span>
                    {getNestedFieldEntries(value).length > 0 ? (
                      <div className="text-foreground min-w-0 space-y-1">
                        {getNestedFieldEntries(value).map(([nestedKey, nestedValue]) => (
                          <div key={nestedKey} className="flex gap-2 flex-wrap">
                            <span className="font-medium text-muted-foreground">
                              {formatFieldLabel(nestedKey)}:
                            </span>
                            <span>{formatFieldValue(nestedKey, nestedValue)}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-foreground truncate">
                        {formatFieldValue(key, value)}
                      </span>
                    )}
                  </div>
                ))}
                {hiddenFieldCount > 0 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      let scrollEl = e.currentTarget.parentElement;
                      while (scrollEl && scrollEl.scrollHeight <= scrollEl.clientHeight) {
                        scrollEl = scrollEl.parentElement;
                      }
                      const savedTop = scrollEl?.scrollTop ?? 0;
                      setShowAllFields((current) => !current);
                      requestAnimationFrame(() => {
                        if (scrollEl) scrollEl.scrollTop = savedTop;
                      });
                    }}
                    className="h-6 px-1 text-xs text-muted-foreground"
                  >
                    {showAllFields
                      ? "Show fewer fields"
                      : `Show ${hiddenFieldCount} more ${hiddenFieldLabel}`}
                  </Button>
                )}
              </div>
            )}

            {/* Correction / void info */}
            {event.void_reason && (
              <div className="text-xs text-red-600 bg-red-50 rounded p-2 mb-2">
                <span className="font-medium">Void reason:</span>{" "}
                {event.void_reason}
              </div>
            )}
            {event.correction_reason && (
              <div className="text-xs text-amber-600 bg-amber-50 rounded p-2 mb-2">
                <span className="font-medium">Correction reason:</span>{" "}
                {event.correction_reason}
              </div>
            )}

            {/* Source reference */}
            {event.source_context && (
              <div className="text-xs text-muted-foreground/60 mt-1">
                Source: {event.source_context}
                {event.source_reference_id &&
                  ` / ${event.source_reference_id}`}
              </div>
            )}

            {/* Documents */}
            {event.documents?.length > 0 && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                <Paperclip className="w-3 h-3" />
                {event.documents.length} document
                {event.documents.length !== 1 ? "s" : ""} attached
              </div>
            )}
          </div>

          {/* Actions */}
          {!isVoided && (canCorrect || canVoid || canAttach) && (
            <div className="flex flex-col gap-1 flex-shrink-0">
              {canCorrect && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onCorrect(event)}
                  className="gap-1 text-xs h-7"
                  title="Correct this event"
                >
                  <Edit3 className="w-3 h-3" />
                  Correct
                </Button>
              )}
              {canVoid && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onVoid(event)}
                  className="gap-1 text-xs h-7 text-red-600 hover:text-red-700"
                  title="Void this event"
                >
                  <Trash2 className="w-3 h-3" />
                  Void
                </Button>
              )}
              {canAttach && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onAttach(event)}
                  className="gap-1 text-xs h-7"
                  title="Attach document"
                >
                  <Paperclip className="w-3 h-3" />
                  Attach
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ServiceRecordCard;
