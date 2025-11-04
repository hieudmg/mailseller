import { ApiEndpointProps, HttpMethod } from '@/types/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import CodeBlock from '@/components/api/code-block';

const getMethodColor = (method: HttpMethod): string => {
  const colors: Record<HttpMethod, string> = {
    GET: 'bg-green-600',
    POST: 'bg-blue-600',
    PUT: 'bg-yellow-600',
    DELETE: 'bg-red-600',
    PATCH: 'bg-purple-600',
  };
  return colors[method];
};
export default function ApiEndpoint({
  method,
  path,
  description,
  queryParams,
  requestExample,
  response,
  responseFields,
  errors,
  notes,
  requiresAuth = true,
}: ApiEndpointProps) {
  const endpointId = path.replace(/\//g, '-');

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Badge className={getMethodColor(method)}>{method}</Badge>
          <a href={'#' + endpointId} id={endpointId} className="scroll-mt-30">
            <span className="font-mono text-base font-normal">{path}</span>
          </a>
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Authentication Info */}
        {!requiresAuth && (
          <div>
            <h4 className="mb-2 font-semibold">Authentication</h4>
            <p className="text-muted-foreground text-sm">This endpoint does not require authentication</p>
          </div>
        )}

        {/* Query Parameters */}
        {queryParams && queryParams.length > 0 && (
          <div>
            <h4 className="mb-2 font-semibold">Query Parameters</h4>
            <div className="space-y-2 text-sm">
              {queryParams.map((param) => (
                <div key={param.name} className="flex items-center gap-2">
                  <code className="rounded bg-slate-800 px-2 py-1 text-purple-400">{param.name}</code>
                  <span className="text-muted-foreground">
                    <code
                      className={cn(
                        param.required ? 'text-primary-foreground' : 'text-muted-foreground',
                        'bg-muted rounded p-1',
                      )}
                    >
                      {param.required ? 'required' : 'optional'}
                    </code>{' '}
                    {param.description}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Example Request */}
        <div>
          <h4 className="mb-2 font-semibold">Example Request</h4>
          <CodeBlock id={`${endpointId}-request`} code={requestExample} />
        </div>

        {/* Response */}
        <div>
          <h4 className="mb-2 font-semibold">Response</h4>
          <CodeBlock id={`${endpointId}-response`} code={JSON.stringify(response, null, 2)} />
        </div>

        {/* Response Fields */}
        {responseFields && responseFields.length > 0 && (
          <div>
            <h4 className="mb-2 font-semibold">Response Fields</h4>
            <div className="space-y-2 text-sm">
              {responseFields.map((field) => (
                <div key={field.name} className="flex gap-2">
                  <code className="rounded bg-slate-800 px-2 py-1 text-purple-400">{field.name}</code>
                  <span className="text-muted-foreground">{field.description}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error Responses */}
        {errors && errors.length > 0 && (
          <div>
            <h4 className="mb-2 font-semibold">Error Responses</h4>
            <div className="space-y-2">
              {errors.map((error, idx) => (
                <div key={idx}>
                  <p className="text-muted-foreground mb-1 text-sm">
                    {error.code} - {error.description}
                  </p>
                  <CodeBlock id={`${endpointId}-error-${error.code}`} code={JSON.stringify(error.example, null, 2)} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Notes */}
        {notes && notes.length > 0 && (
          <div>
            <h4 className="mb-2 font-semibold">Notes</h4>
            <ul className="text-muted-foreground list-inside list-disc space-y-1 text-sm">
              {notes.map((note, idx) => (
                <li key={idx}>{note}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
