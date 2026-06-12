import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Save, UserRoundPlus } from "lucide-react";
import { employeeIdentityApi } from "@/modules/employee_master/api/employeeIdentityApi";
import { employeeProfileApi } from "@/modules/employee_master";
import { buildEmployeeIdentityFormSchema } from "@/modules/employee_master/schemas/identityFormSchema";
import { mastersAPI } from "@/modules/organization_master";
import {
  buildEmployeeDirectoryPath,
  buildEmployeeFilePath,
  getEmployeeEditorScope,
} from "@/shared/lib/employeeEditorRoutes";
import { appendNoticeToPath } from "@/shared/lib/routeNotice";
import { applyServerFieldErrors, useZodForm } from "@/shared/forms";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form";
import { Input } from "@/shared/ui/input";
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
  const [employeeCode, setEmployeeCode] = useState("");
  const [nonRegularEmploymentTypes, setNonRegularEmploymentTypes] = useState([]);

  const schema = useMemo(
    () => buildEmployeeIdentityFormSchema({ requireEmploymentType: isNonRegularCreation }),
    [isNonRegularCreation],
  );
  const form = useZodForm({ schema, defaultValues: createEmptyForm() });
  const { reset } = form;
  const submitting = form.formState.isSubmitting;

  useEffect(() => {
    let cancelled = false;

    const loadPageData = async () => {
      setLoading(true);
      try {
        const identityResponse = isEditMode ? await employeeIdentityApi.get(employeeId) : null;
        if (cancelled) return;

        if (identityResponse) {
          reset(mapIdentityToForm(identityResponse.data));
          setEmployeeCode(identityResponse.data?.employee_code || "");
        } else {
          reset(createEmptyForm());
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
  }, [employeeId, isEditMode, isNonRegularCreation, reset]);

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

  const onSubmit = async (values) => {
    try {
      const payload = buildIdentityPayload(values);
      if (isEditMode) {
        await employeeIdentityApi.update(employeeId, payload);
        const targetPath = returnTo || buildEmployeeFilePath(scope, employeeId);
        navigate(appendNoticeToPath(targetPath, "Employee identity updated successfully", "identity-updated"));
        return;
      }

      const response = await employeeIdentityApi.create(payload);
      const createdEmployeeId = response?.data?.employee_id;
      const createdEmployeeCode = response?.data?.employee_code;
      if (!createdEmployeeId) throw new Error("Missing employee_id");

      if (isNonRegularCreation && values.employment_type) {
        await employeeProfileApi.update(createdEmployeeId, {
          employment_type: normalizeEmploymentTypeCode(values.employment_type),
        });
      }

      const successMessage = isNonRegularCreation
        ? `Employee ${createdEmployeeCode || createdEmployeeId} identity created successfully. Complete the non-regular profile after the identity workflow is completed.`
        : `Employee ${createdEmployeeCode || createdEmployeeId} identity created successfully.`;

      navigate(
        appendNoticeToPath(
          buildEmployeeDirectoryPath(scope),
          successMessage,
          "identity-created"
        )
      );
    } catch (error) {
      applyServerFieldErrors(form, error);
      toast.error(
        getApiErrorMessage(error, isEditMode ? "Failed to update identity" : "Failed to create identity")
      );
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto py-8">
        <Card>
          <CardContent className="py-12 text-center text-slate-500">Loading employee identity...</CardContent>
        </Card>
      </div>
    );
  }

  return (
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

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserRoundPlus className="w-5 h-5" />
                Core Identity
              </CardTitle>
              <CardDescription>Canonical identity fields owned by Employee Identity.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="full_name"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Full Name</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="gender"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Gender</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select gender" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {GENDER_OPTIONS.map((option) => (
                          <SelectItem key={option} value={option}>{option}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="date_of_birth"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Date of Birth</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="mobile_primary"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mobile Number</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        maxLength={10}
                        onChange={(event) => field.onChange(event.target.value.replace(/\D/g, "").slice(0, 10))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="email_official"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Official Email</FormLabel>
                    <FormControl>
                      <Input type="email" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {isNonRegularCreation && (
                <FormField
                  control={form.control}
                  name="employment_type"
                  render={({ field }) => (
                    <FormItem className="md:col-span-2">
                      <FormLabel>Non-Regular Employment Type</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select non-regular employment type" />
                          </SelectTrigger>
                        </FormControl>
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
                      <FormMessage />
                    </FormItem>
                  )}
                />
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
      </Form>
    </div>
  );
};

export default EmployeeIdentityEditorPage;
