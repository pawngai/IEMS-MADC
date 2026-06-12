import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Checkbox } from "@/shared/ui/checkbox";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { SearchableSelect } from "@/shared/ui/searchable-select";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { Textarea } from "@/shared/ui/textarea";
import LeaveSupportingDocumentsField from "@/modules/leave_attendance/components/LeaveSupportingDocumentsField";
import {
  COMMUTED_LEAVE_BASIS_OPTIONS,
  getLeaveSupportingDocumentRecommendation,
  getLeaveSupportingDocumentRequirementMessage,
  isChildCareLeave,
  isCommutedLeave,
  isMaternityLeave,
  isPaternityLeave,
} from "@/modules/leave_attendance/model/leaveApplyForm";

const LeaveDashboardApplyForm = ({
  applyForm,
  daysApplied,
  handleApply,
  leaveTypeOptions,
  leaveTypeUnavailableMessage,
  leaveTypes,
  selectedBalance,
  setApplyForm,
  setApplyFormAttachments,
  submitting,
}) => (
  <Card>
    <CardHeader>
      <CardTitle>Apply for Leave</CardTitle>
      <CardDescription>Submit a leave request for approval</CardDescription>
    </CardHeader>
    <CardContent>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label>Leave Type *</Label>
          <SearchableSelect
            value={applyForm.leave_type_code}
            onValueChange={(v) => setApplyForm({ ...applyForm, leave_type_code: v })}
            options={leaveTypeOptions}
            placeholder="Select leave type"
            className="mt-1"
            emptyMessage={leaveTypeUnavailableMessage || "No leave types available"}
          />
          {leaveTypes.length === 0 && (
            <p className="text-xs text-red-600 mt-1">
              {leaveTypeUnavailableMessage || "No leave types available. Ensure leave masters are seeded and your employment type allows leave."}
            </p>
          )}
          {Number.isFinite(selectedBalance?.available_days) && (
            <p className="text-xs text-slate-500 mt-1">Available: {selectedBalance.available_days} days</p>
          )}
        </div>
        <div>
          <Label>Contact During Leave *</Label>
          <Input className="mt-1" value={applyForm.contact_during_leave} onChange={(e) => setApplyForm({ ...applyForm, contact_during_leave: e.target.value })} />
        </div>
        <div>
          <Label>From Date *</Label>
          <Input type="date" className="mt-1" value={applyForm.from_date} onChange={(e) => setApplyForm({ ...applyForm, from_date: e.target.value })} />
        </div>
        <div>
          <Label>To Date *</Label>
          <Input type="date" className="mt-1" value={applyForm.to_date} onChange={(e) => setApplyForm({ ...applyForm, to_date: e.target.value })} />
          {daysApplied > 0 && <p className="text-xs text-slate-500 mt-1">Days: {daysApplied}</p>}
        </div>
        <div>
          <Label>Leave Station</Label>
          <Input className="mt-1" value={applyForm.leave_station} onChange={(e) => setApplyForm({ ...applyForm, leave_station: e.target.value })} />
        </div>
        <div className="md:col-span-2">
          <Label>Reason *</Label>
          <Textarea className="mt-1" rows={3} value={applyForm.reason} onChange={(e) => setApplyForm({ ...applyForm, reason: e.target.value })} />
        </div>
        {isCommutedLeave(applyForm.leave_type_code) && (
          <>
            <div>
              <Label>Commuted Leave Basis</Label>
              <Select
                value={applyForm.commuted_leave_basis || undefined}
                onValueChange={(value) => setApplyForm({ ...applyForm, commuted_leave_basis: value })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Select basis" />
                </SelectTrigger>
                <SelectContent>
                  {COMMUTED_LEAVE_BASIS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 md:self-end">
              <Checkbox
                id="dashboard-medical-certificate"
                checked={Boolean(applyForm.medical_certificate_provided)}
                onCheckedChange={(checked) => setApplyForm({ ...applyForm, medical_certificate_provided: checked === true })}
              />
              <Label htmlFor="dashboard-medical-certificate" className="cursor-pointer">Medical certificate available</Label>
            </div>
          </>
        )}
        {isMaternityLeave(applyForm.leave_type_code) && (
          <>
            <div>
              <Label>Expected Delivery Date</Label>
              <Input type="date" className="mt-1" value={applyForm.expected_delivery_date} onChange={(e) => setApplyForm({ ...applyForm, expected_delivery_date: e.target.value })} />
            </div>
            <div>
              <Label>Childbirth Date</Label>
              <Input type="date" className="mt-1" value={applyForm.childbirth_date} onChange={(e) => setApplyForm({ ...applyForm, childbirth_date: e.target.value })} />
            </div>
          </>
        )}
        {isPaternityLeave(applyForm.leave_type_code) && (
          <>
            <div>
              <Label>Childbirth Date</Label>
              <Input type="date" className="mt-1" value={applyForm.childbirth_date} onChange={(e) => setApplyForm({ ...applyForm, childbirth_date: e.target.value })} />
            </div>
            <div>
              <Label>Adoption Date</Label>
              <Input type="date" className="mt-1" value={applyForm.adoption_date} onChange={(e) => setApplyForm({ ...applyForm, adoption_date: e.target.value })} />
            </div>
          </>
        )}
        {isChildCareLeave(applyForm.leave_type_code) && (
          <>
            <div>
              <Label>Child Date of Birth</Label>
              <Input type="date" className="mt-1" value={applyForm.child_date_of_birth} onChange={(e) => setApplyForm({ ...applyForm, child_date_of_birth: e.target.value })} />
            </div>
            <div>
              <Label>Child Order</Label>
              <Input type="number" min="1" className="mt-1" value={applyForm.child_order} onChange={(e) => setApplyForm({ ...applyForm, child_order: e.target.value })} />
            </div>
            <div className="md:col-span-2 flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2">
              <Checkbox
                id="dashboard-child-disability"
                checked={Boolean(applyForm.child_has_disability)}
                onCheckedChange={(checked) => setApplyForm({ ...applyForm, child_has_disability: checked === true })}
              />
              <Label htmlFor="dashboard-child-disability" className="cursor-pointer">Child has a disability</Label>
            </div>
          </>
        )}
        <LeaveSupportingDocumentsField
          attachments={applyForm.attachments || []}
          setAttachments={setApplyFormAttachments}
          recommendation={getLeaveSupportingDocumentRecommendation(applyForm)}
          requirementMessage={getLeaveSupportingDocumentRequirementMessage(applyForm)}
        />
      </div>
      <div className="flex justify-end mt-4">
        <Button onClick={handleApply} disabled={submitting || leaveTypes.length === 0}>
          {submitting ? "Submitting..." : "Submit Leave"}
        </Button>
      </div>
    </CardContent>
  </Card>
);

export default LeaveDashboardApplyForm;
