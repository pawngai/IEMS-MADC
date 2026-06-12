import { useEffect, useState } from "react";
import { serviceBookRecordsAPI } from "@/modules/service_book/records/api/serviceBookRecordsApi";
import {
  getFallbackServiceRecordSchema,
  normalizeServiceRecordSchema,
} from "@/modules/service_book/records/model/serviceBookRecordsModel";

export const useRecordServiceBookRecordData = ({
  employeeId,
  eventCategory,
  setEventCategory,
}) => {
  const [schema, setSchema] = useState(() => getFallbackServiceRecordSchema());
  const [usingFallbackSchema, setUsingFallbackSchema] = useState(false);
  const [employeeEvents, setEmployeeEvents] = useState([]);

  useEffect(() => {
    let active = true;

    const loadSchema = async () => {
      try {
        const response = await serviceBookRecordsAPI.getRecordSchema();
        const normalizedSchema = normalizeServiceRecordSchema(response?.data);
        if (!active) return;
        setSchema(normalizedSchema);
        setUsingFallbackSchema(false);
        if (!normalizedSchema.canonicalCategoryOptions.some((item) => item.value === eventCategory)) {
          setEventCategory(normalizedSchema.canonicalCategoryOptions[0]?.value || eventCategory);
        }
      } catch {
        if (active) {
          setUsingFallbackSchema(true);
        }
      }
    };

    loadSchema();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    const loadEmployeeEvents = async () => {
      if (!employeeId) {
        setEmployeeEvents([]);
        return;
      }
      try {
        const response = await serviceBookRecordsAPI.getEventStream(employeeId);
        const data = response?.data || response;
        if (!active) return;
        setEmployeeEvents(Array.isArray(data) ? data : data.events || []);
      } catch {
        if (active) {
          setEmployeeEvents([]);
        }
      }
    };

    loadEmployeeEvents();
    return () => {
      active = false;
    };
  }, [employeeId]);

  return {
    employeeEvents,
    schema,
    usingFallbackSchema,
  };
};
