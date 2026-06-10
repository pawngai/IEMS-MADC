import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { partIIBSchema } from "@/contexts/service_book/opening/schemas/partIIBSchema";
import OpeningPartFormFields from "@/contexts/service_book/opening/components/OpeningPartFormFields";

const OpeningPartIIBForm = ({ value, onChange, disabled, documents, uploading, onUpload }) => (
  <Card data-testid="opening-part-iib-form">
    <CardHeader><CardTitle className="text-lg">Part II-B - Mutable Certificates</CardTitle></CardHeader>
    <CardContent>
      <OpeningPartFormFields
        schema={partIIBSchema}
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

export default OpeningPartIIBForm;
