import React, { useMemo } from 'react';
import { Label } from '@/shared/ui/label';
import { documentsAPI } from '@/modules/documents';
import {
  extractFilename,
  getLinkedDocuments,
} from '@/modules/service_book/components/serviceBookPartHelpers';
import {
  BooleanField,
  DataField,
  EmptyPartPlaceholder,
} from '@/modules/service_book/components/serviceBookLedgerPrimitives';

const DOCUMENT_FIELDS = [
  {
    key: 'medical_fitness_certificate',
    label: 'Medical Fitness Certificate',
    uploadLabel: 'Upload medical certificate',
  },
  {
    key: 'character_verification_done',
    label: 'Character Verification',
    uploadLabel: 'Upload character verification',
  },
  {
    key: 'police_verification_done',
    label: 'Police Verification',
    uploadLabel: 'Upload police verification',
  },
  {
    key: 'oath_of_allegiance_taken',
    label: 'Oath of Allegiance',
    uploadLabel: 'Upload oath of allegiance',
  },
  {
    key: 'oath_of_secrecy_taken',
    label: 'Oath of Secrecy',
    uploadLabel: 'Upload oath of secrecy',
  },
  {
    key: 'entries_confirmed',
    label: 'Confirmation of Entries',
    uploadLabel: 'Upload confirmation document',
  },
];

const getSupportingDocuments = (source) => (
  Array.isArray(source?.supporting_documents) ? source.supporting_documents : []
);

const mapDocumentsWithIndex = (source) => (
  getSupportingDocuments(source).map((doc, index) => ({
    ...doc,
    sourceIndex: index,
  }))
);

const getDocumentsForField = (source, fieldKey) => (
  mapDocumentsWithIndex(source).filter((doc) => doc.field_key === fieldKey)
);

const getLegacyDocuments = (source) => (
  mapDocumentsWithIndex(source).filter((doc) => !doc.field_key)
);

const LinkedDocumentsList = ({ documents }) => {
  if (documents.length === 0) {
    return <p className="text-xs text-muted-foreground">No documents linked yet.</p>;
  }

  return (
    <div className="space-y-1">
      {documents.map((doc, idx) => (
        <div key={`${extractFilename(doc)}-${doc.sourceIndex ?? idx}`} className="flex items-center justify-between rounded border px-2 py-1.5 text-xs">
          <div className="truncate pr-2">
            {doc.original_name || doc.filename || 'Document'}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {extractFilename(doc) && (
              <button
                type="button"
                onClick={() => documentsAPI.downloadDocument(extractFilename(doc), { suggestedName: doc.original_name })}
                className="text-blue-600 hover:text-blue-700"
              >
                Download
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
const PartIIAContent = ({ data }) => {
  const documentSource = data;
  const linkedDocuments = useMemo(() => getLinkedDocuments(documentSource), [documentSource]);
  const legacyDocuments = useMemo(() => getLegacyDocuments(documentSource), [documentSource]);

  const renderFieldDocuments = (fieldKey) => {
    const fieldDocuments = getDocumentsForField(documentSource, fieldKey);
    return <LinkedDocumentsList documents={fieldDocuments} />;
  };

  if (!data) {
    return <EmptyPartPlaceholder message="No certificates have been finalized yet." />;
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div className="rounded-md border p-3 space-y-3 md:col-span-2">
          <BooleanField label="Medical Fitness" value={data.medical_fitness_certificate} date={data.medical_exam_date} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <DataField label="Medical Officer" value={data.medical_officer_name} />
            <DataField label="Medical Category" value={data.medical_category} />
          </div>
          {renderFieldDocuments(DOCUMENT_FIELDS[0].key)}
        </div>

        <div className="rounded-md border p-3 space-y-3">
          <BooleanField label="Character Verification" value={data.character_verification_done} date={data.character_verification_date} />
          {renderFieldDocuments(DOCUMENT_FIELDS[1].key)}
        </div>

        <div className="rounded-md border p-3 space-y-3">
          <BooleanField label="Police Verification" value={data.police_verification_done} date={data.police_verification_date} />
          {renderFieldDocuments(DOCUMENT_FIELDS[2].key)}
        </div>

        <div className="rounded-md border p-3 space-y-3">
          <BooleanField label="Oath of Allegiance" value={data.oath_of_allegiance_taken} date={data.oath_of_allegiance_date} />
          {renderFieldDocuments(DOCUMENT_FIELDS[3].key)}
        </div>

        <div className="rounded-md border p-3 space-y-3">
          <BooleanField label="Oath of Secrecy" value={data.oath_of_secrecy_taken} date={data.oath_of_secrecy_date} />
          {renderFieldDocuments(DOCUMENT_FIELDS[4].key)}
        </div>

        <div className="rounded-md border p-3 space-y-3 md:col-span-2">
          <BooleanField label="Entries Confirmed" value={data.entries_confirmed} date={data.confirmation_date} />
          <DataField label="Confirming Officer" value={data.confirming_officer} />
          {renderFieldDocuments(DOCUMENT_FIELDS[5].key)}
        </div>
      </div>

      {legacyDocuments.length > 0 && (
        <div className="rounded-md border p-3">
          <Label className="text-sm">Legacy Supporting Documents</Label>
          <p className="mt-1 text-xs text-muted-foreground">Documents linked before field-level grouping remain available here.</p>
          <div className="mt-2">
            <LinkedDocumentsList documents={legacyDocuments} />
          </div>
        </div>
      )}

      {!linkedDocuments.length && (
        <div className="rounded-md border p-3">
          <Label className="text-sm">Part II-A Supporting Documents</Label>
          <p className="mt-1 text-xs text-muted-foreground">No supporting documents linked.</p>
        </div>
      )}
    </div>
  );
};

export default PartIIAContent;
