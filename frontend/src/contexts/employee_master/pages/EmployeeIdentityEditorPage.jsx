import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Save, UserRoundPlus } from "lucide-react";
import Layout from "@/app/layout/Layout";
import { employeeIdentityApi } from "@/contexts/employee_master/api/employeeIdentityApi";
import { employeeProfileApi } from "@/contexts/employee_master";
import { mastersAPI } from "@/contexts/organization_master";
import {
  buildEmployeeDirectoryPath,
  buildEmployeeFilePath,
  getEmployeeEditorScope,
} from "@/shared/lib/employeeEditorRoutes";
import { appendNoticeToPath } from "@/shared/lib/routeNotice";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/shared/lib/utils";

const GENDER_OPTIONS = ["Male", "Female", "Other"];

const normalizeEmploymentTypeCode = (value) =>
  String(value || "").trim().toUpperCase().replace(/[-\s]+/g, "_");

const isNonRegularEmploymentMaster = (record) => {
  if (!record) return false;
  if (record.employment_class) {
    return String(record.employment_class).trim().toUpperCase() === "NON_REGULAR";
  }
  return record.eligible_for_service_book === false;
};

const createEmptyForm = (defaults = {}) => ({
  full_name: "",
  gender: "",
  date_of_birth: "",
  mobile_primary: "",
  email_official: "",
  employment_type: "",
  ...defaults,
});

const mapIdentityToForm = (identity) => ({
  ...createEmptyForm(),
  full_name: identity?.full_name || "",
  gender: identity?.gender || "",
  date_of_birth: identity?.date_of_birth || "",
  mobile_primary: identity?.mobile_primary || "",
  email_official: identity?.email_official || "",
});

const buildIdentityPayload = (formData) =>
  Object.fromEntries(
    Object.entries({
      full_name: String(formData.full_name || "").trim(),
      gender: formData.gender || undefined,
      date_of_birth: formData.date_of_birth || undefined,
      mobile_primary: formData.mobile_primary || undefined,
      email_official: String(formData.email_official || "").trim().toLowerCase() || undefined,
    }).filter(([, value]) => value !== undefined && value !== "")
  );

const validateIdentityForm = (formData, { requireEmploymentType = false } = {}) => {
  const nextErrors = {};
  if (!String(formData.full_name || "").trim()) nextErrors.full_name = "Full name is required";
  if (!formData.gender) nextErrors.gender = "Gender is required";
  if (!formData.date_of_birth) nextErrors.date_of_birth = "Date of birth is required";
  if (formData.mobile_primary && !/^[6-9]\d{9}$/.test(formData.mobile_primary)) {
    nextErrors.mobile_primary = "Enter a valid 10-digit mobile number";
  }
  if (formData.email_official && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(String(formData.email_official).trim())) {
    nextErrors.email_official = "Enter a valid official email";
  }
  if (requireEmploymentType && !formData.employment_type) {
    nextErrors.employment_type = "Employment type is required for non-regular employees";
  }
  return nextErrors;
};

const EmployeeIdentityEditorPage = () => {
  const { employeeId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const isEditMode = Boolean(employeeId);
  const scope = useMemo(() => getEmployeeEditorScope(location.pathname), [location.pathname]);
  const returnTo = location.state?.returnTo;
  const creationMode = String(location.state?.creationMode || "").trim();
  const isNonRegularCreation = !isEditMode && creationMode === "non_regular";

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});
  const [formData, setFormData] = useState(createEmptyForm());
  const [employeeCode, setEmployeeCode] = useState("");
  const [nonRegularEmploymentTypes, setNonRegularEmploymentTypes] = useState([]);

  useEffect(() => {
    let cancelled = false;

    const loadPageData = async () => {
      setLoading(true);
      try {
        const identityResponse = isEditMode ? await employeeIdentityApi.get(employeeId) : null;
        if (cancelled) return;

        if (identityResponse) {
          setFormData(mapIdentityToForm(identityResponse.data));
          setEmployeeCode(identityResponse.data?.employee_code || "");
        } else {
          setFormData(createEmptyForm());
          setEmployeeCode("");
        }
      } catch (error) {
        if (!cancelled) {
          toast.error(getApiErrorMessage(error, "Failed to load employee identity editor"));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    loadPageData();
    return () => {
      cancelled = true;
    };
  }, [employeeId, isEditMode, isNonRegularCreation]);

  useEffect(() => {
    if (!isNonRegularCreation) {
      setNonRegularEmploymentTypes([]);
      return undefined;
    }
    let cancelled = false;
    mastersAPI.getEmploymentTypes()
      .then((response) => {
        if (cancelled) return;
        const items = Array.isArray(response?.data) ? response.data : [];
        setNonRegularEmploymentTypes(items.filter(isNonRegularEmploymentMaster));
      })
      .catch(() => {
        if (!cancelled) setNonRegularEmploymentTypes([]);
      });
    return () => {
      cancelled = true;
    };
  }, [isNonRegularCreation]);

  const fallbackReturnPath = useMemo(() => {
    if (isEditMode) return buildEmployeeFilePath(scope, employeeId);
    return buildEmployeeDirectoryPath(scope);
  }, [employeeId, isEditMode, scope]);

  const handleCancel = () => {
    navigate(returnTo || fallbackReturnPath);
  };

  const updateField = (field, value) => {
    setFormData((current) => ({ ...current, [field]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextErrors = validateIdentityForm(formData, {
      requireEmploymentType: isNonRegularCreation,
    });
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    try {
      const payload = buildIdentityPayload(formData);
      if (isEditMode) {
        await employeeIdentityApi.update(employeeId, payload);
        const targetPath = returnTo || buildEmployeeFilePath(scope, employeeId);
        navigate(appendNoticeToPath(targetPath, "Employee identity updated successfully", "identity-updated"));
        return;
      }

      const response = await employeeIdentityApi.create(payload);
      const createdEmployeeId = response?.data?.employee_id;
      const employeeCode = response?.data?.employee_code;
      if (!createdEmployeeId) throw new Error("Missing employee_id");

      if (isNonRegularCreation && formData.employment_type) {
        await employeeProfileApi.update(createdEmployeeId, {
          employment_type: normalizeEmploymentTypeCode(formData.employment_type),
        });
      }

      const successMessage = isNonRegularCreation
        ? `Employee ${employeeCode || createdEmployeeId} identity created successfully. Complete the non-regular profile after the identity workflow is completed.`
        : `Employee ${employeeCode || createdEmployeeId} identity created successfully.`;

      navigate(
        appendNoticeToPath(
          buildEmployeeDirectoryPath(scope),
          successMessage,
          "identity-created"
        )
      );
    } catch (error) {
      const detail = error?.response?.data?.detail;
      if (Array.isArray(detail)) {
        const fieldErrors = {};
        detail.forEach((issue) => {
          const field = issue?.loc?.[1] || issue?.field || issue?.field_id;
          if (field) fieldErrors[field] = issue?.msg || issue?.message || "Invalid value";
        });
        setErrors(fieldErrors);
      }
      toast.error(
        getApiErrorMessage(error, isEditMode ? "Failed to update identity" : "Failed to create identity")
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="max-w-5xl mx-auto py-8">
          <Card>
            <CardContent className="py-12 text-center text-slate-500">Loading employee identity...</CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-6 animate-fade-in" data-testid="employee-identity-editor-page">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Employee Identity</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">
              {isEditMode ? "Edit Employee Identity" : "Create Employee Identity"}
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              {isNonRegularCreation
                ? "Create the core identity first. It will move through the normal identity workflow, then non-regular details can be completed from the employee file after activation."
                : "This workflow captures core identity only. Profile extension stays separate and can be completed next or later from the employee file."}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="gap-2" onClick={handleCancel}>
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
            {isEditMode && employeeCode && (
              <Badge variant="outline" className="font-mono text-xs h-fit">
                {employeeCode}
              </Badge>
            )}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserRoundPlus className="w-5 h-5" />
                Core Identity
              </CardTitle>
              <CardDescription>Canonical identity fields owned by Employee Identity.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2 space-y-2">
                <Label htmlFor="full_name">Full Name</Label>
                <Input id="full_name" value={formData.full_name} onChange={(event) => updateField("full_name", event.target.value)} />
                {errors.full_name && <p className="text-xs text-red-500">{errors.full_name}</p>}
              </div>

              <div className="space-y-2">
                <Label>Gender</Label>
                <Select value={formData.gender} onValueChange={(value) => updateField("gender", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select gender" />
                  </SelectTrigger>
                  <SelectContent>
                    {GENDER_OPTIONS.map((option) => (
                      <SelectItem key={option} value={option}>{option}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.gender && <p className="text-xs text-red-500">{errors.gender}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="date_of_birth">Date of Birth</Label>
                <Input id="date_of_birth" type="date" value={formData.date_of_birth} onChange={(event) => updateField("date_of_birth", event.target.value)} />
                {errors.date_of_birth && <p className="text-xs text-red-500">{errors.date_of_birth}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="mobile_primary">Mobile Number</Label>
                <Input
                  id="mobile_primary"
                  value={formData.mobile_primary}
                  maxLength={10}
                  onChange={(event) => updateField("mobile_primary", event.target.value.replace(/\D/g, "").slice(0, 10))}
                />
                {errors.mobile_primary && <p className="text-xs text-red-500">{errors.mobile_primary}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="email_official">Official Email</Label>
                <Input
                  id="email_official"
                  type="email"
                  value={formData.email_official}
                  onChange={(event) => updateField("email_official", event.target.value)}
                />
                {errors.email_official && <p className="text-xs text-red-500">{errors.email_official}</p>}
              </div>

              {isNonRegularCreation && (
                <div className="md:col-span-2 space-y-2">
                  <Label htmlFor="employment_type">Non-Regular Employment Type</Label>
                  <Select
                    value={formData.employment_type}
                    onValueChange={(value) => updateField("employment_type", value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select non-regular employment type" />
                    </SelectTrigger>
                    <SelectContent>
                      {nonRegularEmploymentTypes.map((item) => {
                        const code = String(
                          item.employment_type_code || item.code || item.value || item.id || ""
                        );
                        const label = item.name || item.label || item.description || code;
                        if (!code) return null;
                        return (
                          <SelectItem key={code} value={code}>{label}</SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">
                    Seeds the profile extension so the editor opens in non-regular mode after activation.
                  </p>
                  {errors.employment_type && <p className="text-xs text-red-500">{errors.employment_type}</p>}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={handleCancel}>Cancel</Button>
            <Button type="submit" className="gap-2" disabled={submitting}>
              <Save className="w-4 h-4" />
              {submitting ? "Saving..." : isEditMode ? "Save Identity" : "Create Identity"}
            </Button>
          </div>
        </form>
      </div>
    </Layout>
  );
};

export default EmployeeIdentityEditorPage;
