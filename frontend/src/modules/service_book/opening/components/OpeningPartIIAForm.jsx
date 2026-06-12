import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { partIIASchema } from "@/modules/service_book/opening/schemas/partIIASchema";
import OpeningPartFormFields from "@/modules/service_book/opening/components/OpeningPartFormFields";

const OpeningPartIIAForm = ({ value, onChange, disabled, documents, uploading, onUpload }) => (
  <Card data-testid="opening-part-iia-form">
    <CardHeader><CardTitle className="text-lg">Part II-A - Immutable Certificates</CardTitle></CardHeader>
    <CardContent>
      <OpeningPartFormFields
        schema={partIIASchema}
        value={value}
        onChange={onChange}
        disabled={disabled}
        documents={documents}
        uploading={uploading}
        onUpload={onUpload}
      />
    </CardContent>
  </Card>
);

export default OpeningPartIIAForm;
