import React from 'react';
import { CalendarDays, Landmark, ShieldCheck, Users } from 'lucide-react';
import { cn } from '@/shared/lib/utils';
import { Badge } from '@/shared/ui/badge';
import { Card, CardContent } from '@/shared/ui/card';
import { WorkflowStatusBadge } from '@/modules/service_book/components/serviceBookWorkflowUi';
import { formatDisplayDate } from '@/modules/service_book/components/serviceBookPartHelpers';
import {
  DataField,
  EmptyPartPlaceholder,
} from '@/modules/service_book/components/serviceBookLedgerPrimitives';

const NOMINATION_TYPES = [
  {
    key: 'pcf',
    label: 'PCF Nomination',
    shortLabel: 'PCF',
    description: 'Provident fund nominee allocation.',
    schemaKey: 'SB_IIB_PCF_NOMINATION_ROW',
    dataField: 'pcf_nomination',
    dateField: 'pcf_nomination_date',
    accountField: 'pcf_account_number',
    fields: [{ name: 'pcf_account_number', label: 'PCF Account Number', type: 'text' }],
  },
  {
    key: 'dcrg',
    label: 'DCRG Nomination',
    shortLabel: 'DCRG',
    description: 'Death-cum-retirement gratuity nominees.',
    schemaKey: 'SB_IIB_DCRG_NOMINATION_ROW',
    dataField: 'dcr_gratuity_nomination',
    dateField: 'dcr_gratuity_nomination_date',
    fields: [],
  },
  {
    key: 'nps',
    label: 'NPS Nomination',
    shortLabel: 'NPS',
    description: 'National pension scheme nominees.',
    schemaKey: 'SB_IIB_NPS_NOMINATION_ROW',
    dataField: 'nps_nomination',
    dateField: 'nps_nomination_date',
    fields: [],
  },
  {
    key: 'leave_encashment',
    label: 'Leave Encashment Nomination',
    shortLabel: 'Leave Encashment',
    description: 'Nominee for leave encashment settlement.',
    schemaKey: 'SB_IIB_LEAVE_ENCASHMENT_NOMINATION_ROW',
    dataField: 'leave_encashment_nomination',
    dateField: 'leave_encashment_nomination_date',
    fields: [],
  },
  {
    key: 'family_pension',
    label: 'Family Pension Nomination',
    shortLabel: 'Family Pension',
    description: 'Pension beneficiary details for dependants.',
    schemaKey: 'SB_IIB_FAMILY_PENSION_NOMINATION_ROW',
    dataField: 'family_pension_nomination',
    dateField: 'family_pension_nomination_date',
    fields: [],
  },
];

const BANK_DETAIL_FIELDS = [
  { label: 'PCF Account No.', valueKey: 'pcf_account_number' },
  { label: 'Bank Account No.', valueKey: 'bank_account_number' },
  { label: 'Bank Name', valueKey: 'bank_name' },
  { label: 'Bank IFSC', valueKey: 'bank_ifsc' },
  { label: 'NPS PRAN No.', valueKey: 'nps_pran_number' },
];

function getNomineeCount(rows, dataField) {
  return (rows || []).reduce((total, row) => total + ((row?.[dataField] || []).length || 0), 0);
}

function formatCountLabel(count, singular, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

const PartIIBContent = ({ data }) => {

  const populatedBankDetails = BANK_DETAIL_FIELDS.filter(({ valueKey }) => Boolean(data?.[valueKey])).length;
  const totalFamilyMembers = data?.family_members?.length || 0;
  const nominationCategoryCount = NOMINATION_TYPES.filter((nominationType) => (data?.[nominationType.dataField] || []).length > 0).length;
  const totalNominees = NOMINATION_TYPES.reduce(
    (total, nominationType) => total + getNomineeCount(data?.[nominationType.dataField], nominationType.dataField),
    0,
  );

  if (!data) {
    return <EmptyPartPlaceholder message="No mutable certificates data has been finalized yet." />;
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <Landmark className="h-4 w-4" />
            Records Snapshot
          </div>
          <div className="mt-3 text-2xl font-semibold text-slate-900">{populatedBankDetails}/5</div>
          <p className="mt-1 text-sm text-slate-500">Bank and account references currently on file.</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <Users className="h-4 w-4" />
            Family Sheet
          </div>
          <div className="mt-3 text-2xl font-semibold text-slate-900">{totalFamilyMembers}</div>
          <p className="mt-1 text-sm text-slate-500">
            {data?.family_declaration_date ? `Declared on ${formatDisplayDate(data.family_declaration_date)}` : 'No family declaration date recorded.'}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <ShieldCheck className="h-4 w-4" />
            Nomination Categories
          </div>
          <div className="mt-3 text-2xl font-semibold text-slate-900">{nominationCategoryCount}</div>
          <p className="mt-1 text-sm text-slate-500">Distinct nomination sections with saved entries.</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <CalendarDays className="h-4 w-4" />
            Beneficiaries
          </div>
          <div className="mt-3 text-2xl font-semibold text-slate-900">{totalNominees}</div>
          <p className="mt-1 text-sm text-slate-500">Named nominees across all mutable certificate records.</p>
        </div>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="pt-5">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h4 className="font-medium text-slate-900">Bank and account details</h4>
              <p className="mt-1 text-sm text-slate-500">Core financial references used by nominations and settlement calculations.</p>
            </div>
            <Badge variant="outline" className="border-slate-300 text-slate-600">Mutable record</Badge>
          </div>
          <div className="grid gap-4 text-sm sm:grid-cols-2 xl:grid-cols-3">
            {BANK_DETAIL_FIELDS.map(({ label, valueKey }) => (
              <div key={valueKey} className="rounded-lg border border-slate-200 bg-white p-3">
                <DataField label={label} value={data?.[valueKey]} />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="pt-5">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h4 className="font-medium text-slate-900">Family members</h4>
              <p className="mt-1 text-sm text-slate-500">Declared dependants used for nomination validation and pension references.</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="border-slate-300 text-slate-600">{formatCountLabel(totalFamilyMembers, 'member')}</Badge>
              {data.family_declaration_date && (
                <Badge variant="outline" className="border-slate-300 text-slate-600">Declared {formatDisplayDate(data.family_declaration_date)}</Badge>
              )}
            </div>
          </div>

          {totalFamilyMembers > 0 ? (
            <div className="overflow-auto rounded-lg border border-slate-200">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="border-b border-slate-200 px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">Name</th>
                    <th className="border-b border-slate-200 px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">Relationship</th>
                    <th className="border-b border-slate-200 px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">Date of Birth</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.family_members || []).map((familyMember, index) => (
                    <tr key={`${familyMember.name || familyMember.member_name || 'family'}-${index}`} className="border-t border-slate-200 bg-white">
                      <td className="px-3 py-2 text-slate-900">{familyMember.name || familyMember.member_name || '-'}</td>
                      <td className="px-3 py-2 text-slate-600">{familyMember.relationship || '-'}</td>
                      <td className="px-3 py-2 text-slate-600">{familyMember.date_of_birth ? formatDisplayDate(familyMember.date_of_birth) : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50/70 px-4 py-6 text-center text-sm text-slate-500">
              No family members recorded yet.
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="pt-5">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h4 className="font-medium text-slate-900">Nominations</h4>
              <p className="mt-1 text-sm text-slate-500">Capture each benefit nominee as its own workflow item so submission and approval stay auditable.</p>
            </div>
            <Badge variant="outline" className="border-slate-300 text-slate-600">{formatCountLabel(totalNominees, 'nominee')}</Badge>
          </div>

          <div className="space-y-4">
            {NOMINATION_TYPES.map((nominationType) => {
              const rows = data?.[nominationType.dataField];
              if (!rows?.length) return null;
              return (
                <div key={nominationType.key} className="rounded-xl border border-slate-200 bg-white p-4">
                  <div className="mb-3 flex items-start justify-between gap-4">
                    <div>
                      <h5 className="text-sm font-semibold text-slate-900">{nominationType.label}</h5>
                      <p className="mt-1 text-xs text-slate-500">{nominationType.description}</p>
                    </div>
                    <Badge variant="outline" className="border-slate-300 text-slate-600">
                      {formatCountLabel(getNomineeCount(rows, nominationType.dataField), 'nominee')}
                    </Badge>
                  </div>
                  <div className="space-y-3">
                    {rows.map((nomination, index) => {
                      const nominees = nomination[nominationType.dataField] || [];
                      return (
                        <div
                          key={nomination._meta?.id || index}
                          className={cn(
                            'rounded-xl border p-4 text-sm',
                            nomination._meta?.workflow_state === 'DRAFT' || nomination._meta?.status === 'DRAFT'
                              ? 'border-amber-200 bg-amber-50/70'
                              : 'border-slate-200 bg-slate-50/70',
                          )}
                        >
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div className="space-y-2">
                              <div className="font-medium text-slate-900">{nominationType.shortLabel}</div>
                              <div className="flex flex-wrap gap-2">
                                {nomination[nominationType.dateField] && (
                                  <Badge variant="outline" className="border-slate-300 text-slate-600">{formatDisplayDate(nomination[nominationType.dateField])}</Badge>
                                )}
                                {nominationType.accountField && nomination[nominationType.accountField] && (
                                  <Badge variant="outline" className="border-slate-300 text-slate-600">PCF {nomination[nominationType.accountField]}</Badge>
                                )}
                              </div>
                            </div>
                            {nomination._meta && <WorkflowStatusBadge status={nomination._meta.workflow_state || nomination._meta.status} />}
                          </div>

                          {Array.isArray(nominees) && nominees.length > 0 ? (
                            <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                              {nominees.map((nominee, nomineeIndex) => (
                                <div key={nomineeIndex} className="rounded-lg border border-white/80 bg-white p-3 shadow-sm">
                                  <div className="font-medium text-slate-900">{nominee.name || nominee.nominee_name || '-'}</div>
                                  <div className="mt-1 text-xs text-slate-500">{nominee.relationship || 'Relationship not provided'}</div>
                                  {(nominee.share_percent ?? nominee.share_percentage) != null && (
                                    <div className="mt-3 text-xs font-medium uppercase tracking-wide text-slate-500">
                                      Share {nominee.share_percent ?? nominee.share_percentage}%
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-white/60 px-3 py-4 text-xs text-slate-500">
                              No nominees listed for this entry.
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}

            {NOMINATION_TYPES.every((nominationType) => !data?.[nominationType.dataField]?.length) && (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 px-4 py-8 text-center">
                <div className="text-sm font-medium text-slate-700">No nominations recorded yet</div>
                <p className="mt-1 text-sm text-slate-500">Nominations will appear here once entries are added.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PartIIBContent;
