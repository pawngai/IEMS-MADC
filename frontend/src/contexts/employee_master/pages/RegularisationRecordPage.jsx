import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, FileText, Loader2, Upload, X } from "lucide-react";
import Layout from "@/app/layout/Layout";
import { documentsAPI } from "@/contexts/documents";
import { employeeProfileApi } from "@/contexts/employee_master";
import { mastersAPI } from "@/contexts/organization_master";
import { serviceRecordsApi } from "@/contexts/service_book";
import { buildEmployeeFilePath, getEmployeeEditorScope } from "@/shared/lib/employeeEditorRoutes";
import { appendNoticeToPath } from "@/shared/lib/routeNotice";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { SearchableSelect } from "@/shared/ui/searchable-select";
import { getApiErrorMessage } from "@/shared/lib/utils";
import { toast } from "sonner";

const DOCUMENT_ACCEPT = ".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx,.xls,.xlsx";
const DOCUMENT_SOURCE_CONTEXT = "service_book.records.regularisation";
const DOCUMENT_PURPOSE_KEY = "REGULARISATION_ORDER";
const DOCUMENT_PURPOSE_LABEL = "Regularisation order";

const optionize = (items = []) => items.map((item) => {
  const value = item.code || item.value || item.id || item.employment_type_code;
  const label = item.name || item.label || item.description || value;
  return { value, label, search: `${label} ${value}` };
});

const initialForm = {
  effective_date: "",
  regularisation_order_no: "",
  regularisation_order_date: "",
  new_department_id: "",
  new_office_id: "",
  new_designation_id: "",
  new_service_id: "",
};

const getDocumentRefId = (document) =>
  String(document?.document_id || document?.documentId || document?.filename || "").trim();

const getDocumentHref = (document) => {
  const filename = String(document?.filename || "").trim();
  if (filename) return documentsAPI.getFileUrl(filename);
  return String(document?.url || "").trim();
};

const RegularisationRecordPage = () => {
  const { employeeId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const scope = useMemo(() => getEmployeeEditorScope(location.pathname), [location.pathname]);
  const [form, setForm] = useState(initialForm);
  const [profile, setProfile] = useState(null);
  const [summary, setSummary] = useState(null);
  const [masters, setMasters] = useState({ departments: [], offices: [], designations: [], services: [] });
  const [submitting, setSubmitting] = useState(false);
  const [attachedDocuments, setAttachedDocuments] = useState([]);
  const [uploadingDocument, setUploadingDocument] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([
      employeeProfileApi.get(employeeId).catch(() => ({ data: null })),
      serviceRecordsApi.getServiceSummary(employeeId).catch(() => ({ data: null })),
      mastersAPI.getDepartments().catch(() => ({ data: [] })),
      mastersAPI.getOffices().catch(() => ({ data: [] })),
      mastersAPI.getDesignations().catch(() => ({ data: [] })),
      mastersAPI.getServices().catch(() => ({ data: [] })),
    ]).then(([profileRes, summaryRes, deptRes, officeRes, desigRes, serviceRes]) => {
      if (!active) return;
      setProfile(profileRes?.data || null);
      setSummary(summaryRes?.data || null);
      setMasters({
        departments: deptRes?.data || [],
        offices: officeRes?.data || [],
        designations: desigRes?.data || [],
        services: serviceRes?.data || [],
      });
      setForm((current) => ({
        ...current,
        new_department_id: summaryRes?.data?.current_department_id || "",
        new_office_id: summaryRes?.data?.current_office_id || "",
        new_designation_id: summaryRes?.data?.current_designation_id || "",
        new_service_id: summaryRes?.data?.current_service_id || "",
      }));
    });
    return () => {
      active = false;
    };
  }, [employeeId]);

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const handleUploadDocument = async (file) => {
    if (!file) return;
    setUploadingDocument(true);
    let uploaded = null;
    try {
      const response = await documentsAPI.upload(file, {
        source_context: DOCUMENT_SOURCE_CONTEXT,
        document_type: "ORDER",
        category: DOCUMENT_PURPOSE_KEY,
      });
      uploaded = response?.data ?? null;
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to upload document"));
      return;
    } finally {
      setUploadingDocument(false);
    }

    const documentId = getDocumentRefId(uploaded);
    if (!uploaded || !documentId) return;
    if (attachedDocuments.some((item) => getDocumentRefId(item) === documentId)) return;

    setAttachedDocuments((current) => [
      ...current,
      {
        document_id: uploaded.document_id || documentId,
        filename: uploaded.filename || "",
        original_name: uploaded.original_name || file.name,
        file_size: uploaded.file_size || null,
        content_type: uploaded.content_type || file.type || null,
        url: uploaded.url || "",
        source_context: DOCUMENT_SOURCE_CONTEXT,
        uploaded_at: uploaded.uploaded_at || null,
        document_type: uploaded?.metadata?.document_type || "ORDER",
        purpose_key: DOCUMENT_PURPOSE_KEY,
        purpose_label: DOCUMENT_PURPOSE_LABEL,
      },
    ]);
    toast.success("Document uploaded and attached to this regularisation");
  };

  const handleRemoveAttachedDocument = (documentId) => {
    setAttachedDocuments((current) => current.filter((document) => getDocumentRefId(document) !== documentId));
  };

  const handleSubmit = async () => {
    const missing = ["effective_date", "regularisation_order_no", "regularisation_order_date", "new_department_id", "new_office_id", "new_designation_id", "new_service_id"].filter((field) => !String(form[field] || "").trim());
    if (missing.length) {
      toast.error(`Complete required fields: ${missing.join(", ")}`);
      return;
    }
    setSubmitting(true);
    try {
      await serviceRecordsApi.create({
        employee_id: employeeId,
        record_type: "REGULARISATION_RECORDED",
        record_category: "REGULARISATION",
        effective_date: form.effective_date,
        payload: {
          previous_employment_type_code: summary?.current_employment_type_code || null,
          new_employment_type_code: "REGULAR",
          regularisation_order_no: form.regularisation_order_no,
          regularisation_order_date: form.regularisation_order_date,
          new_department_id: form.new_department_id,
          new_office_id: form.new_office_id,
          new_designation_id: form.new_designation_id,
          new_service_id: form.new_service_id,
        },
        document_ids: attachedDocuments.map(getDocumentRefId).filter(Boolean),
      });
      navigate(appendNoticeToPath(buildEmployeeFilePath(scope, employeeId), "Regularisation record draft created successfully.", "regularisation-created"));
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to create regularisation record"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-6 animate-fade-in" data-testid="regularisation-record-page">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Service Record</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Regularisation</h2>
            <p className="text-sm text-slate-500 mt-1">{profile?.full_name || employeeId}</p>
          </div>
          <Button variant="outline" className="gap-2" onClick={() => navigate(buildEmployeeFilePath(scope, employeeId))}><ArrowLeft className="w-4 h-4" /> Back</Button>
        </div>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><CheckCircle2 className="w-5 h-5" /> Regularisation Record</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Effective Date" type="date" value={form.effective_date} onChange={(value) => update("effective_date", value)} />
            <Field label="Regularisation Order No" value={form.regularisation_order_no} onChange={(value) => update("regularisation_order_no", value)} />
            <Field label="Regularisation Order Date" type="date" value={form.regularisation_order_date} onChange={(value) => update("regularisation_order_date", value)} />
            <SearchField label="Department" value={form.new_department_id} onChange={(value) => update("new_department_id", value)} options={optionize(masters.departments)} />
            <SearchField label="Office" value={form.new_office_id} onChange={(value) => update("new_office_id", value)} options={optionize(masters.offices)} />
            <SearchField label="Designation" value={form.new_designation_id} onChange={(value) => update("new_designation_id", value)} options={optionize(masters.designations)} />
            <SearchField label="Service" value={form.new_service_id} onChange={(value) => update("new_service_id", value)} options={optionize(masters.services)} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" /> Supporting Documents
            </CardTitle>
            <CardDescription>Upload the regularisation order and any supporting paperwork. Attached documents are linked to this record.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <label className={`inline-flex cursor-pointer items-center gap-2 rounded-md border border-dashed px-4 py-2 text-sm transition-colors hover:bg-slate-50 ${uploadingDocument ? "pointer-events-none opacity-60" : ""}`}>
                {uploadingDocument ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                {uploadingDocument ? "Uploading..." : "Upload regularisation document"}
                <input
                  type="file"
                  data-testid="regularisation-document-upload"
                  className="hidden"
                  accept={DOCUMENT_ACCEPT}
                  disabled={uploadingDocument}
                  onChange={async (event) => {
                    const file = event.target.files?.[0];
                    event.target.value = "";
                    if (!file) return;
                    await handleUploadDocument(file);
                  }}
                />
              </label>
            </div>

            {attachedDocuments.length > 0 ? (
              <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50/70 p-3" data-testid="regularisation-attached-documents">
                {attachedDocuments.map((document, index) => {
                  const documentId = getDocumentRefId(document) || `attached-${index}`;
                  const href = getDocumentHref(document);
                  return (
                    <div key={`${documentId}-${index}`} className="flex items-start justify-between gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 shrink-0 text-slate-500" />
                          <span className="truncate font-medium text-slate-700">{document.original_name || document.filename || documentId}</span>
                        </div>
                        <p className="mt-1 truncate text-xs text-slate-400">{documentId}</p>
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {document.purpose_label ? <Badge variant="outline">{document.purpose_label}</Badge> : null}
                          {document.document_type ? <Badge variant="secondary">{document.document_type}</Badge> : null}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {href ? (
                          <a href={href} target="_blank" rel="noopener noreferrer" className="text-sm text-slate-600 underline underline-offset-2">
                            Open
                          </a>
                        ) : null}
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-slate-500 hover:text-rose-600"
                          onClick={() => handleRemoveAttachedDocument(documentId)}
                          aria-label="Remove document"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="rounded-md border border-dashed border-slate-300 px-4 py-6 text-sm text-slate-500">
                No documents attached yet.
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => navigate(buildEmployeeFilePath(scope, employeeId))}>Cancel</Button>
          <Button disabled={submitting} onClick={handleSubmit}>{submitting ? "Creating..." : "Create Regularisation Draft"}</Button>
        </div>
      </div>
    </Layout>
  );
};

const slugify = (value) => String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

const Field = ({ label, value, onChange, type = "text" }) => {
  const fieldId = `regularisation-${slugify(label)}`;
  return (
    <div className="space-y-2">
      <Label htmlFor={fieldId}>{label}</Label>
      <Input
        id={fieldId}
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
};

const SearchField = ({ label, value, onChange, options }) => (
  <div className="space-y-2"><Label>{label}</Label><SearchableSelect value={value} onValueChange={onChange} options={options} placeholder={`Select ${label.toLowerCase()}`} /></div>
);

export default RegularisationRecordPage;
