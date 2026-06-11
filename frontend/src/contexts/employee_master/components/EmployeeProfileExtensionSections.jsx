import { Checkbox } from "@/shared/ui/checkbox";
import { Label } from "@/shared/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { AlertTriangle, Camera, PenLine } from "lucide-react";
import {
  BLOOD_GROUP_OPTIONS,
  MARITAL_STATUS_OPTIONS,
  MediaUploadField,
  SelectField,
  TextField,
  renderTypeSpecificField,
} from "@/contexts/employee_master/components/EmployeeProfileExtensionEditor.support";

export const EmployeeProfileImmutableNotice = () => (
  <Card className="border-amber-200 bg-amber-50/60">
    <CardContent className="py-4 flex items-start gap-3">
      <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
      <div className="space-y-1 text-sm text-amber-900">
        <p className="font-medium">Service Book biodata is immutable here.</p>
        <p>This screen updates only profile-extension fields. Service Book Part I corrections must stay in Service Book flows.</p>
      </div>
    </CardContent>
  </Card>
);

export const EmployeeProfileTypeSpecificFieldsCard = ({
  employmentType,
  typeSpecificFields,
  formData,
  errors,
  updateField,
  payLevelOptions,
}) => {
  if (!typeSpecificFields.length) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Employment Details</CardTitle>
        <CardDescription>Fields specific to {employmentType.toLowerCase()} employees.</CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {typeSpecificFields.map((field) => renderTypeSpecificField({
          field,
          value: formData[field.id],
          onChange: updateField,
          error: errors[field.id],
          payLevelOptions,
        }))}
      </CardContent>
    </Card>
  );
};

export const EmployeeProfileStandardSections = ({
  showModernNonRegularEditor,
  formData,
  errors,
  updateField,
  essMode,
  hasPermanentAddressValue,
  areAddressesSynced,
  onCopyPermanentAddress,
  uploadingPhoto,
  uploadingSignature,
  handleMediaUpload,
}) => (
  <>
    {showModernNonRegularEditor && (
      <Card>
        <CardHeader>
          <CardTitle>Personal Profile</CardTitle>
          <CardDescription>Additional demographic details stored on the employee-owned profile extension.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <TextField id="father_name" label="Father's Name" value={formData.father_name} onChange={updateField} error={errors.father_name} />
          <TextField id="mother_name" label="Mother's Name" value={formData.mother_name} onChange={updateField} error={errors.mother_name} />
          <TextField id="nationality" label="Nationality" value={formData.nationality} onChange={updateField} error={errors.nationality} />
          <TextField id="category" label="Category" value={formData.category} onChange={updateField} error={errors.category} placeholder="General / ST / SC / OBC" />
          <TextField id="religion" label="Religion" value={formData.religion} onChange={updateField} error={errors.religion} />
          <SelectField
            id="blood_group"
            label="Blood Group"
            value={formData.blood_group}
            onChange={updateField}
            options={BLOOD_GROUP_OPTIONS}
            error={errors.blood_group}
            placeholder="Select blood group"
          />
          <SelectField
            id="marital_status"
            label="Marital Status"
            value={formData.marital_status}
            onChange={updateField}
            options={MARITAL_STATUS_OPTIONS}
            error={errors.marital_status}
            placeholder="Select marital status"
          />
          {formData.marital_status === "MARRIED" && (
            <TextField id="spouse_name" label="Spouse Name" value={formData.spouse_name} onChange={updateField} error={errors.spouse_name} />
          )}
        </CardContent>
      </Card>
    )}

    <Card>
      <CardHeader>
        <CardTitle>Contact Details</CardTitle>
        <CardDescription>Employee-owned contact and communication details.</CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TextField id="mobile_primary" label="Primary Mobile" value={formData.mobile_primary} onChange={updateField} error={errors.mobile_primary} />
        <TextField id="mobile_alternate" label="Alternate Mobile" value={formData.mobile_alternate} onChange={updateField} error={errors.mobile_alternate} />
        <TextField id="email_personal" label="Personal Email" type="email" value={formData.email_personal} onChange={updateField} error={errors.email_personal} />
        {!essMode && (
          <TextField id="email_official" label="Official Email" type="email" value={formData.email_official} onChange={updateField} error={errors.email_official} />
        )}
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Address</CardTitle>
        <CardDescription>Permanent and present address details.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Permanent Address</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TextField id="address_line1" label="Address Line 1" value={formData.address_line1} onChange={updateField} error={errors.address_line1} />
            <TextField id="address_line2" label="Address Line 2" value={formData.address_line2} onChange={updateField} error={errors.address_line2} />
            <TextField id="city" label="City" value={formData.city} onChange={updateField} error={errors.city} />
            <TextField id="district" label="District" value={formData.district} onChange={updateField} error={errors.district} />
            <TextField id="state" label="State" value={formData.state} onChange={updateField} error={errors.state} />
            <TextField id="pincode" label="Pincode" value={formData.pincode} onChange={updateField} error={errors.pincode} />
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Present Address</p>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Checkbox
                id="copy-address"
                checked={hasPermanentAddressValue && areAddressesSynced}
                disabled={!hasPermanentAddressValue}
                onCheckedChange={(checked) => {
                  if (!checked || !hasPermanentAddressValue) return;
                  onCopyPermanentAddress();
                }}
              />
              <Label htmlFor="copy-address">Same as permanent address</Label>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TextField id="present_address_line1" label="Address Line 1" value={formData.present_address_line1} onChange={updateField} error={errors.present_address_line1} />
            <TextField id="present_address_line2" label="Address Line 2" value={formData.present_address_line2} onChange={updateField} error={errors.present_address_line2} />
            <TextField id="present_city" label="City" value={formData.present_city} onChange={updateField} error={errors.present_city} />
            <TextField id="present_district" label="District" value={formData.present_district} onChange={updateField} error={errors.present_district} />
            <TextField id="present_state" label="State" value={formData.present_state} onChange={updateField} error={errors.present_state} />
            <TextField id="present_pincode" label="Pincode" value={formData.present_pincode} onChange={updateField} error={errors.present_pincode} />
          </div>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Photo and Signature</CardTitle>
        <CardDescription>Upload profile media as part of the profile extension.</CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <MediaUploadField id="profile-extension-photo-upload" label="Profile Photo" value={formData.photo_url} icon={Camera} uploading={uploadingPhoto} onUpload={(event) => handleMediaUpload({ event, type: "photo" })} buttonLabel="Upload Photo" />
        <MediaUploadField id="profile-extension-signature-upload" label="Signature" value={formData.signature_url} icon={PenLine} uploading={uploadingSignature} onUpload={(event) => handleMediaUpload({ event, type: "signature" })} buttonLabel="Upload Signature" previewClassName="h-16 max-w-full object-contain" />
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Emergency Contact</CardTitle>
        <CardDescription>Profile-managed emergency contact details.</CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TextField id="emergency_name" label="Emergency Contact Name" value={formData.emergency_name} onChange={updateField} error={errors.emergency_name} />
        <TextField id="emergency_phone" label="Emergency Contact Phone" value={formData.emergency_phone} onChange={updateField} error={errors.emergency_phone} />
        <TextField id="emergency_relation" label="Emergency Contact Relation" value={formData.emergency_relation} onChange={updateField} error={errors.emergency_relation} />
      </CardContent>
    </Card>
  </>
);
