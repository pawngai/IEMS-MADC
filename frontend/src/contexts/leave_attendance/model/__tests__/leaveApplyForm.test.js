import { describe, expect, test } from 'vitest';

import {
  buildLeaveApplicationPayload,
  createInitialLeaveApplyForm,
  getLeaveEligibilityValidationMessage,
  getLeaveSupportingDocumentRecommendation,
  getLeaveSupportingDocumentRequirementMessage,
  getLeaveSupportingDocumentValidationMessage,
} from '@/contexts/leave_attendance/model/leaveApplyForm';

describe('leaveApplyForm', () => {
  test('requires supporting context for commuted leave', () => {
    const form = {
      ...createInitialLeaveApplyForm(),
      leave_type_code: 'CML',
    };

    expect(getLeaveEligibilityValidationMessage(form)).toBe(
      'CML requires a medical certificate or public-interest study basis',
    );
  });

  test('requires childbirth or adoption context for paternity leave', () => {
    const form = {
      ...createInitialLeaveApplyForm(),
      leave_type_code: 'PL',
    };

    expect(getLeaveEligibilityValidationMessage(form)).toBe(
      'Paternity leave requires a childbirth date or adoption date',
    );
  });

  test('requires supporting document for commuted leave after medical context is provided', () => {
    const form = {
      ...createInitialLeaveApplyForm(),
      leave_type_code: 'CML',
      medical_certificate_provided: true,
    };

    expect(getLeaveSupportingDocumentRequirementMessage(form)).toBe(
      'Commuted leave requires a supporting document: upload the medical certificate.',
    );
    expect(getLeaveSupportingDocumentValidationMessage(form)).toBe(
      'Commuted leave requires a supporting document: upload the medical certificate.',
    );
  });

  test('requires supporting document for paternity leave when adoption path is used', () => {
    const form = {
      ...createInitialLeaveApplyForm(),
      leave_type_code: 'PL',
      adoption_date: '2026-04-01',
    };

    expect(getLeaveSupportingDocumentRequirementMessage(form)).toBe(
      'Paternity leave requires a supporting document: upload the adoption record.',
    );
  });

  test('recommends order documents for study-based commuted leave', () => {
    const form = {
      ...createInitialLeaveApplyForm(),
      leave_type_code: 'CML',
      commuted_leave_basis: 'STUDY_PUBLIC_INTEREST',
    };

    expect(getLeaveSupportingDocumentRecommendation(form)).toEqual({
      documentType: 'ORDER',
      documentTypeLabel: 'Order',
    });
  });

  test('recommends certificate documents for child care leave', () => {
    const form = {
      ...createInitialLeaveApplyForm(),
      leave_type_code: 'CCL',
    };

    expect(getLeaveSupportingDocumentRecommendation(form)).toEqual({
      documentType: 'CERTIFICATE',
      documentTypeLabel: 'Certificate',
    });
  });

  test('does not require supporting document once one is attached', () => {
    const form = {
      ...createInitialLeaveApplyForm(),
      leave_type_code: 'CCL',
      child_date_of_birth: '2018-01-01',
      attachments: [{ filename: 'birth-proof.pdf' }],
    };

    expect(getLeaveSupportingDocumentValidationMessage(form)).toBeNull();
  });

  test('builds optional leave payload fields', () => {
    const payload = buildLeaveApplicationPayload({
      ...createInitialLeaveApplyForm(),
      leave_type_code: 'CCL',
      from_date: '2026-04-14',
      to_date: '2026-04-18',
      reason: 'Care of child',
      contact_during_leave: '9999999999',
      child_date_of_birth: '2014-05-01',
      child_has_disability: true,
      child_order: '2',
      attachments: [
        {
          url: '/api/documents/files/support.pdf',
          filename: 'support.pdf',
          original_name: 'supporting-evidence.pdf',
          file_size: '2048',
          content_type: 'application/pdf',
        },
      ],
    });

    expect(payload.child_date_of_birth).toBe('2014-05-01');
    expect(payload.child_has_disability).toBe(true);
    expect(payload.child_order).toBe(2);
    expect(payload.leave_station).toBeNull();
    expect(payload.attachments).toEqual([
      {
        url: '/api/documents/files/support.pdf',
        filename: 'support.pdf',
        original_name: 'supporting-evidence.pdf',
        file_size: 2048,
        content_type: 'application/pdf',
      },
    ]);
  });
});