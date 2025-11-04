import { useState } from 'react';
import { toast } from 'sonner';
import { Copy, Check } from 'lucide-react';

export default function CodeBlock({ code, id }: { code: string; id: string }) {
  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({});

  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedStates({ ...copiedStates, [id]: true });
    toast.success('Copied to clipboard');
    setTimeout(() => {
      setCopiedStates({ ...copiedStates, [id]: false });
    }, 2000);
  };

  return (
    <div className="relative">
      <pre className="overflow-x-auto rounded-lg bg-slate-900 p-4 text-sm text-slate-100">
        <code>{code}</code>
      </pre>
      <button
        onClick={() => copyToClipboard(code, id)}
        className="absolute top-2 right-2 rounded p-2 text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-100"
      >
        {copiedStates[id] ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
      </button>
    </div>
  );
}
