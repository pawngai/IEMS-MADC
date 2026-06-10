import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/shared/lib/utils";
import {
  PROFILE_CATEGORIES,
  SERVICE_BOOK_CATEGORIES,
  CATEGORY_TO_PART_KEY,
} from "@/contexts/change_requests/model/changeRequestFieldSchema";
import {
  PROFILE_FIELD_ALIASES,
  PROFILE_FIELD_PATHS,
  getValueByPath,
  entryLabel,
} from "@/contexts/change_requests/services/changeRequestFieldResolver";

/**
 * Encapsulates all form state and logic for the ESS change-request compose flow.
 *
 * @param {Object}  deps
 * @param {Object}  deps.profile           - Employee profile data
 * @param {Object}  deps.serviceBook       - Service book data
 * @param {boolean} deps.serviceBookEligible
 * @param {Function} deps.submitChangeRequest - From useChangeRequestActions
 * @param {Function} deps.onSuccess        - Called after a successful submission
 */
export function useChangeRequestForm({
  profile,
  serviceBook,
  serviceBookEligible,
  submitChangeRequest,
  onSuccess,
}) {
  // ---- primitive state ----
  const [formType, setFormType] = useState("PROFILE");
  const [formCategory, setFormCategory] = useState("");
  const [formEntrySection, setFormEntrySection] = useState("");
  const [formEntryId, setFormEntryId] = useState("");
  const [formFields, setFormFields] = useState([]);
  const [formReason, setFormReason] = useState("");
  const [formSupportingInfo, setFormSupportingInfo] = useState("");
  const [formAttachments, setFormAttachments] = useState([]);

  // ---- derived: categories ----
  const availableCategories = useMemo(() => {
    if (formType === "PROFILE") {
      return Object.entries(PROFILE_CATEGORIES).map(([key, v]) => ({
        value: key,
        label: v.label,
      }));
    }
    if (!serviceBookEligible) return [];
    return Object.entries(SERVICE_BOOK_CATEGORIES).map(([key, v]) => ({
      value: key,
      label: v.label,
    }));
  }, [formType, serviceBookEligible]);

  useEffect(() => {
    if (!serviceBookEligible && formType === "SERVICE_BOOK") {
      setFormType("PROFILE");
      setFormCategory("");
      setFormEntrySection("");
      setFormEntryId("");
      setFormFields([{ field_name: "", current_value: "", requested_value: "", field_label: "" }]);
    }
  }, [serviceBookEligible, formType]);

  // ---- derived: entry-based config ----
  const categoryConfig = useMemo(() => {
    if (formType === "SERVICE_BOOK" && formCategory) {
      return SERVICE_BOOK_CATEGORIES[formCategory] || null;
    }
    return null;
  }, [formType, formCategory]);

  const isEntryBased = categoryConfig?.entryBased || false;

  const entrySections = useMemo(() => {
    if (!isEntryBased || !categoryConfig?.entrySections) return [];
    return categoryConfig.entrySections;
  }, [isEntryBased, categoryConfig]);

  const activeEntrySection = useMemo(() => {
    if (!isEntryBased) return null;
    if (entrySections.length === 1) return entrySections[0];
    return entrySections.find((s) => s.key === formEntrySection) || null;
  }, [isEntryBased, entrySections, formEntrySection]);

  const availableEntries = useMemo(() => {
    if (!isEntryBased || !activeEntrySection || !serviceBook) return [];
    const partKey = CATEGORY_TO_PART_KEY[formCategory];
    const partData = partKey ? serviceBook[partKey] : null;
    if (!partData) return [];
    const partRoot = partData?.data && typeof partData.data === "object" ? partData.data : partData;
    const arr = partRoot[activeEntrySection.key];
    if (!Array.isArray(arr)) return [];
    return arr.map((e, idx) => ({
      id: e.id || String(idx),
      label: entryLabel(e, activeEntrySection.entryType),
      data: e,
    }));
  }, [isEntryBased, activeEntrySection, serviceBook, formCategory]);

  const selectedEntry = useMemo(() => {
    if (!formEntryId) return null;
    return availableEntries.find((e) => e.id === formEntryId) || null;
  }, [availableEntries, formEntryId]);

  const availableFields = useMemo(() => {
    if (!formCategory) return [];
    if (formType === "PROFILE") {
      return PROFILE_CATEGORIES[formCategory]?.fields || [];
    }
    if (isEntryBased && activeEntrySection) {
      return activeEntrySection.fields || [];
    }
    return categoryConfig?.fields || [];
  }, [formType, formCategory, isEntryBased, activeEntrySection, categoryConfig]);

  // ---- resolve current value ----
  const resolveCurrentValueForField = useCallback(
    (fieldName) => {
      if (!fieldName?.trim()) return "";

      let dataSource = null;
      const normalizedFieldName = PROFILE_FIELD_ALIASES[fieldName] || fieldName;
      if (formType === "PROFILE" && profile) {
        dataSource = profile;
      } else if (formType === "SERVICE_BOOK" && formCategory) {
        if (isEntryBased && selectedEntry) {
          dataSource = selectedEntry.data;
        } else if (serviceBook) {
          const partKey = CATEGORY_TO_PART_KEY[formCategory];
          const rawPart = partKey ? serviceBook[partKey] : null;
          dataSource = rawPart?.data && typeof rawPart.data === "object" ? rawPart.data : rawPart;
        }
      }

      if (!dataSource) return "";
      const currentVal = (() => {
        if (formType === "PROFILE") {
          const candidates = [
            ...(PROFILE_FIELD_PATHS[fieldName] || []),
            ...(PROFILE_FIELD_PATHS[normalizedFieldName] || []),
            fieldName,
            normalizedFieldName,
            `contact.${fieldName}`,
            `contact.${normalizedFieldName}`,
            `identifiers.${fieldName}`,
            `identifiers.${normalizedFieldName}`,
          ];
          for (const candidate of candidates) {
            const val = getValueByPath(dataSource, candidate);
            if (val != null && val !== "") return val;
          }
          return "";
        }
        return dataSource[fieldName] ?? dataSource[normalizedFieldName];
      })();

      if (currentVal == null) return "";
      return typeof currentVal === "object" ? JSON.stringify(currentVal) : String(currentVal);
    },
    [formType, profile, formCategory, isEntryBased, selectedEntry, serviceBook]
  );

  // Auto-populate current_value when dependencies change
  useEffect(() => {
    setFormFields((prev) =>
      prev.map((field) => {
        if (!field.field_name?.trim()) return field;
        return { ...field, current_value: resolveCurrentValueForField(field.field_name) };
      })
    );
  }, [resolveCurrentValueForField]);

  // ---- field operations ----
  const addField = useCallback(() => {
    setFormFields((prev) => [
      ...prev,
      { field_name: "", current_value: "", requested_value: "", field_label: "" },
    ]);
  }, []);

  const updateField = useCallback(
    (index, key, value) => {
      setFormFields((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], [key]: value };
        if (key === "field_name") {
          const fieldDef = availableFields.find((f) => f.name === value);
          if (fieldDef) next[index].field_label = fieldDef.label;
          next[index].current_value = resolveCurrentValueForField(value);
        }
        return next;
      });
    },
    [availableFields, resolveCurrentValueForField]
  );

  const removeField = useCallback((index) => {
    setFormFields((prev) => prev.filter((_, i) => i !== index));
  }, []);

  // ---- reset ----
  const resetForm = useCallback(() => {
    setFormType("PROFILE");
    setFormCategory("");
    setFormEntrySection("");
    setFormEntryId("");
    setFormFields([]);
    setFormReason("");
    setFormSupportingInfo("");
    setFormAttachments([]);
  }, []);

  // ---- setters that cascade resets ----
  const switchType = useCallback((type) => {
    setFormType(type);
    setFormCategory("");
    setFormEntrySection("");
    setFormEntryId("");
    setFormFields([{ field_name: "", current_value: "", requested_value: "", field_label: "" }]);
  }, []);

  const switchCategory = useCallback((cat) => {
    setFormCategory(cat);
    setFormEntrySection("");
    setFormEntryId("");
    setFormFields([{ field_name: "", current_value: "", requested_value: "", field_label: "" }]);
  }, []);

  const switchEntrySection = useCallback((key) => {
    setFormEntrySection(key);
    setFormEntryId("");
    setFormFields([{ field_name: "", current_value: "", requested_value: "", field_label: "" }]);
  }, []);

  const switchEntryId = useCallback((id) => {
    setFormEntryId(id);
    setFormFields([{ field_name: "", current_value: "", requested_value: "", field_label: "" }]);
  }, []);

  // ---- submit ----
  const handleSubmit = useCallback(async () => {
    if (!formCategory) {
      toast.error("Please select a category");
      return;
    }
    const validFields = formFields.filter(
      (f) => f.field_name.trim() && f.requested_value.trim()
    );
    if (validFields.length === 0) {
      toast.error("Please add at least one field to change");
      return;
    }
    if (formReason.trim().length < 10) {
      toast.error("Please provide a reason (at least 10 characters)");
      return;
    }

    try {
      const payload = {
        request_type: formType,
        category: formCategory,
        fields: validFields.map((f) => ({
          field_name: f.field_name,
          current_value: f.current_value || null,
          requested_value: f.requested_value,
          field_label: f.field_label || f.field_name,
        })),
        reason: formReason.trim(),
        supporting_info: formSupportingInfo.trim() || null,
        attachments: formAttachments.map((a) => ({
          url: a.url,
          filename: a.filename,
          original_name: a.original_name,
          file_size: a.file_size,
          content_type: a.content_type,
        })),
      };
      if (isEntryBased && formEntryId) {
        payload.entry_id = formEntryId;
        payload.entry_section = activeEntrySection?.key || null;
        payload.entry_label = selectedEntry?.label || null;
      }
      const success = await submitChangeRequest(payload);
      if (!success) return;
      onSuccess?.();
      resetForm();
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Failed to submit change request"));
    }
  }, [
    formCategory,
    formFields,
    formReason,
    formSupportingInfo,
    formAttachments,
    formType,
    isEntryBased,
    formEntryId,
    activeEntrySection,
    selectedEntry,
    submitChangeRequest,
    onSuccess,
    resetForm,
  ]);

  // ---- validation helpers (for UI) ----
  const hasCategory = Boolean(formCategory);
  const hasEntrySelection =
    !isEntryBased || Boolean(formEntryId) || (categoryConfig?.fields?.length > 0 && !formEntryId);
  const validFields = formFields.filter(
    (f) => f.field_name.trim() && f.requested_value.trim()
  );
  const hasValidFields = validFields.length > 0;
  const reasonLength = formReason.trim().length;
  const isReasonValid = reasonLength >= 10;

  return {
    // state
    formType,
    formCategory,
    formEntrySection,
    formEntryId,
    formFields,
    formReason,
    setFormReason,
    formSupportingInfo,
    setFormSupportingInfo,
    formAttachments,
    setFormAttachments,
    // derived
    availableCategories,
    categoryConfig,
    isEntryBased,
    entrySections,
    activeEntrySection,
    availableEntries,
    selectedEntry,
    availableFields,
    // validation
    hasCategory,
    hasEntrySelection,
    hasValidFields,
    reasonLength,
    isReasonValid,
    // operations
    switchType,
    switchCategory,
    switchEntrySection,
    switchEntryId,
    addField,
    updateField,
    removeField,
    resetForm,
    handleSubmit,
  };
}
