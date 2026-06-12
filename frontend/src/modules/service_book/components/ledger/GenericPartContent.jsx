import React from 'react';
import { AlertCircle } from 'lucide-react';
import { EmptyPartPlaceholder } from '@/modules/service_book/components/serviceBookLedgerPrimitives';

const GenericPartContent = ({ data, partKey, editMode, canWrite = true }) => {
  if (!data && !editMode) {
    return <EmptyPartPlaceholder message={canWrite ? `Part ${partKey} data not recorded yet. Click 'Add Data' to start.` : `Part ${partKey} has no finalized data yet.`} />;
  }

  if (!data) {
    return (
      <div className="text-center py-8 text-gray-500">
        <AlertCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
        <p>Part {partKey} form coming soon.</p>
        <p className="text-xs mt-1">This part requires specialized fields.</p>
      </div>
    );
  }

  return (
    <div className="text-sm">
      <pre className="bg-gray-50 p-4 rounded-lg overflow-auto text-xs">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
};

export default GenericPartContent;
