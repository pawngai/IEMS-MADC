import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { toast } from 'sonner';
import { serviceBookAPI } from '@/modules/service_book/api/serviceBookApi';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Card, CardContent } from '@/shared/ui/card';
import { Label } from '@/shared/ui/label';
import { WorkflowActions, WorkflowStatusBadge } from '@/modules/service_book/components/serviceBookWorkflowUi';
import {
  EmptyPartPlaceholder,
  FormField,
  SelectField,
} from '@/modules/service_book/components/serviceBookLedgerPrimitives';

const PartVIIIContent = ({ data, employeeId, onReload, canAddAuditComment, onWorkflowAction, can, Permissions }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newComment, setNewComment] = useState({ audit_type: 'INTERNAL', severity: 'OBSERVATION' });
  const [isSaving, setIsSaving] = useState(false);

  const handleAddComment = async () => {
    try {
      if (!canAddAuditComment) {
        toast.error('You do not have permission to add audit comments');
        return;
      }
      setIsSaving(true);
      await serviceBookAPI.addAuditComment(employeeId, {
        ...newComment,
        comment_date: new Date().toISOString().split('T')[0],
      });
      toast.success('Audit comment added');
      setShowAddForm(false);
      setNewComment({ audit_type: 'INTERNAL', severity: 'OBSERVATION' });
      onReload();
    } catch (err) {
      toast.error('Failed to add comment');
    } finally {
      setIsSaving(false);
    }
  };

  const severityColors = {
    OBSERVATION: 'bg-blue-100 text-blue-700',
    MINOR: 'bg-yellow-100 text-yellow-700',
    MAJOR: 'bg-orange-100 text-orange-700',
    CRITICAL: 'bg-red-100 text-red-700',
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold text-gray-600">{data?.total_comments || 0}</div>
            <div className="text-sm text-gray-500">Total Comments</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold text-orange-600">{data?.open_comments || 0}</div>
            <div className="text-sm text-gray-500">Open</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold text-green-600">{data?.resolved_comments || 0}</div>
            <div className="text-sm text-gray-500">Resolved</div>
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-between items-center">
        <h4 className="font-medium text-gray-700">Audit Comments</h4>
        <Button size="sm" onClick={() => setShowAddForm(!showAddForm)} disabled={!canAddAuditComment}>
          <Plus className="h-4 w-4 mr-1" /> Add Comment
        </Button>
      </div>
      {!canAddAuditComment && (
        <div className="text-xs text-gray-500">Only auditors or Approving Authority can add comments.</div>
      )}

      {showAddForm && (
        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SelectField label="Audit Type" value={newComment.audit_type} onChange={(v) => setNewComment({ ...newComment, audit_type: v })} options={['INTERNAL', 'EXTERNAL', 'AG_AUDIT', 'CAG_AUDIT']} />
              <SelectField label="Severity" value={newComment.severity} onChange={(v) => setNewComment({ ...newComment, severity: v })} options={['OBSERVATION', 'MINOR', 'MAJOR', 'CRITICAL']} />
              <FormField label="Auditor Name" value={newComment.auditor_name} onChange={(v) => setNewComment({ ...newComment, auditor_name: v })} />
              <FormField label="Auditor Designation" value={newComment.auditor_designation} onChange={(v) => setNewComment({ ...newComment, auditor_designation: v })} />
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-700">Comment</Label>
              <textarea
                className="w-full mt-1 p-2 border rounded-md text-sm"
                rows={3}
                value={newComment.comment_text || ''}
                onChange={(e) => setNewComment({ ...newComment, comment_text: e.target.value })}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAddForm(false)}>Cancel</Button>
              <Button onClick={handleAddComment} disabled={isSaving}>
                {isSaving ? 'Adding...' : 'Add Comment'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {data?.comments?.length > 0 ? (
        <div className="space-y-2">
          {data.comments.map((comment, idx) => (
            <div key={comment._meta?.id || comment.id || idx} className={`p-3 rounded-lg border ${comment._meta?.status === 'DRAFT' || comment._meta?.workflow_state === 'DRAFT' ? 'bg-amber-50 border-amber-200' : 'bg-gray-50'}`}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-medium text-gray-900">{comment.auditor_name}</div>
                  <div className="text-sm text-gray-600">{comment.auditor_designation}</div>
                </div>
                <div className="flex gap-2">
                  <Badge className={severityColors[comment.severity]}>{comment.severity}</Badge>
                  <Badge variant="outline">{comment.status}</Badge>
                  {comment._meta && <WorkflowStatusBadge status={comment._meta.workflow_state || comment._meta.status} />}
                </div>
              </div>
              <div className="mt-2 text-sm text-gray-700">{comment.comment_text}</div>
              <div className="mt-2 text-xs text-gray-400">{comment.comment_date} | {comment.audit_type}</div>
              {comment._meta && onWorkflowAction && can && Permissions && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <WorkflowActions meta={comment._meta} onAction={onWorkflowAction} can={can} Permissions={Permissions} />
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyPartPlaceholder message="No audit comments recorded yet." />
      )}
    </div>
  );
};

export default PartVIIIContent;
