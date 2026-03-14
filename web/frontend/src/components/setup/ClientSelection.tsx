import { Check } from 'lucide-react';
import type { Client } from '../../types';

interface ClientSelectionProps {
  clients: Client[];
  selectedClient: string;
  setSelectedClient: (client: string) => void;
}

export default function ClientSelection({
  clients,
  selectedClient,
  setSelectedClient,
}: ClientSelectionProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">🦀 选择共识客户端</h2>
      <p className="text-gray-600">选择您要使用的共识层客户端</p>

      <div className="grid grid-cols-1 gap-4">
        {clients.map((client) => (
          <button
            key={client.id}
            onClick={() => setSelectedClient(client.id)}
            className={`p-4 border-2 rounded-lg text-left transition ${
              selectedClient === client.id
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold flex items-center gap-2">
                  {client.name}
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                    {client.language}
                  </span>
                  {client.recommended && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                      推荐
                    </span>
                  )}
                </h3>
                <p className="text-sm text-gray-600 mt-1">{client.description}</p>
              </div>
              {selectedClient === client.id && (
                <Check className="w-6 h-6 text-blue-600" />
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
