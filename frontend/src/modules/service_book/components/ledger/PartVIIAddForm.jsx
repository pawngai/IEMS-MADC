import React from 'react';
import { Button } from '@/shared/ui/button';
import { Card, CardContent } from '@/shared/ui/card';
import { FormField, SelectField } from '@/modules/service_book/components/serviceBookLedgerPrimitives';

const FORM_LABELS = {
  ltc: 'LTC',
  hba: 'HBA',
  vehicle: 'Vehicle Advance',
  festival: 'Festival Advance',
};

const FORM_FIELDS = {
  ltc: (entry, onChange) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <FormField label="Block Year" value={entry.block_year} onChange={(v) => onChange({ ...entry, block_year: v })} />
      <SelectField label="LTC Type" value={entry.ltc_type} onChange={(v) => onChange({ ...entry, ltc_type: v })} options={['HOME_TOWN', 'ANYWHERE_IN_INDIA']} />
      <FormField label="Availed Date" type="date" value={entry.availed_date} onChange={(v) => onChange({ ...entry, availed_date: v })} />
      <FormField label="Journey From" value={entry.journey_from} onChange={(v) => onChange({ ...entry, journey_from: v })} />
      <FormField label="Journey To" value={entry.journey_to} onChange={(v) => onChange({ ...entry, journey_to: v })} />
      <FormField label="Family Members Availed" type="number" value={entry.family_members_availed} onChange={(v) => onChange({ ...entry, family_members_availed: parseInt(v) || 0 })} />
      <FormField label="Amount Claimed" type="number" value={entry.amount_claimed} onChange={(v) => onChange({ ...entry, amount_claimed: parseFloat(v) || 0 })} />
      <FormField label="Amount Sanctioned" type="number" value={entry.amount_sanctioned} onChange={(v) => onChange({ ...entry, amount_sanctioned: parseFloat(v) || 0 })} />
      <FormField label="Sanction Order No" value={entry.sanction_order_number} onChange={(v) => onChange({ ...entry, sanction_order_number: v })} />
    </div>
  ),
  hba: (entry, onChange) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <FormField label="Sanction Date" type="date" value={entry.sanction_date} onChange={(v) => onChange({ ...entry, sanction_date: v })} />
      <FormField label="Sanction Order No" value={entry.sanction_order_number} onChange={(v) => onChange({ ...entry, sanction_order_number: v })} />
      <FormField label="Amount Sanctioned" type="number" value={entry.amount_sanctioned} onChange={(v) => onChange({ ...entry, amount_sanctioned: parseFloat(v) || 0 })} />
      <FormField label="Purpose" value={entry.purpose} onChange={(v) => onChange({ ...entry, purpose: v })} />
      <FormField label="Property Address" value={entry.property_address} onChange={(v) => onChange({ ...entry, property_address: v })} />
      <FormField label="Monthly Installment" type="number" value={entry.monthly_installment} onChange={(v) => onChange({ ...entry, monthly_installment: parseFloat(v) || 0 })} />
    </div>
  ),
  vehicle: (entry, onChange) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <FormField label="Advance Date" type="date" value={entry.advance_date} onChange={(v) => onChange({ ...entry, advance_date: v })} />
      <FormField label="Amount" type="number" value={entry.amount} onChange={(v) => onChange({ ...entry, amount: parseFloat(v) || 0 })} />
      <FormField label="Vehicle Type" value={entry.vehicle_type} onChange={(v) => onChange({ ...entry, vehicle_type: v })} />
      <FormField label="Order Number" value={entry.order_number} onChange={(v) => onChange({ ...entry, order_number: v })} />
      <FormField label="Recovery Months" type="number" value={entry.recovery_months} onChange={(v) => onChange({ ...entry, recovery_months: parseInt(v) || 0 })} />
    </div>
  ),
  festival: (entry, onChange) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <FormField label="Festival" value={entry.festival} onChange={(v) => onChange({ ...entry, festival: v })} />
      <FormField label="Advance Date" type="date" value={entry.advance_date} onChange={(v) => onChange({ ...entry, advance_date: v })} />
      <FormField label="Amount" type="number" value={entry.amount} onChange={(v) => onChange({ ...entry, amount: parseFloat(v) || 0 })} />
      <FormField label="Recovery Months" type="number" value={entry.recovery_months} onChange={(v) => onChange({ ...entry, recovery_months: parseInt(v) || 0 })} />
      <FormField label="Monthly Deduction" type="number" value={entry.monthly_deduction} onChange={(v) => onChange({ ...entry, monthly_deduction: parseFloat(v) || 0 })} />
      <FormField label="Order Number" value={entry.order_number} onChange={(v) => onChange({ ...entry, order_number: v })} />
    </div>
  ),
};

export default function PartVIIAddForm({ activeForm, newEntry, setNewEntry, onAdd, onCancel, isSaving }) {
  if (!activeForm) return null;

  return (
    <Card className="bg-orange-50 border-orange-200 mb-3">
      <CardContent className="pt-4 space-y-4">
        <h4 className="text-sm font-semibold text-gray-700">New {FORM_LABELS[activeForm]} Record</h4>
        {FORM_FIELDS[activeForm]?.(newEntry, setNewEntry)}
        <FormField label="Remarks" value={newEntry.remarks} onChange={(v) => setNewEntry({ ...newEntry, remarks: v })} />
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>Cancel</Button>
          <Button onClick={onAdd} disabled={isSaving}>
            {isSaving ? 'Adding...' : `Add ${FORM_LABELS[activeForm]}`}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
