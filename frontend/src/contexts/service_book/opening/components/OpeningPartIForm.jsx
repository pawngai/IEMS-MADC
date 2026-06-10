import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { partISchema } from "@/contexts/service_book/opening/schemas/partISchema";
import OpeningPartFormFields from "@/contexts/service_book/opening/components/OpeningPartFormFields";

const OpeningPartIForm = ({ value, onChange, disabled, documents, uploading, onUpload }) => (
  <Card data-testid="opening-part-i-form">
    <CardHeader><CardTitle className="text-lg">Part I - Bio-Data</CardTitle></CardHeader>
    <CardContent>
      <OpeningPartFormFields
        schema={partISchema}
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

export default OpeningPartIForm;
