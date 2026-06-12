import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { partIIISchema } from "@/modules/service_book/opening/schemas/partIIISchema";
import OpeningPartFormFields from "@/modules/service_book/opening/components/OpeningPartFormFields";

const OpeningPartIIIForm = ({ value, onChange, disabled, documents, uploading, onUpload }) => (
  <Card data-testid="opening-part-iii-form">
    <CardHeader><CardTitle className="text-lg">Part III</CardTitle></CardHeader>
    <CardContent>
      <OpeningPartFormFields
        schema={partIIISchema}
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

export default OpeningPartIIIForm;