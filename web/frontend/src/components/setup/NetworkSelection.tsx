import { Check } from 'lucide-react';
import type { Network } from '../../types';

interface NetworkSelectionProps {
  networks: Network[];
  selectedNetwork: string;
  setSelectedNetwork: (network: string) => void;
}

export default function NetworkSelection({
  networks,
  selectedNetwork,
  setSelectedNetwork,
}: NetworkSelectionProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">🌐 选择以太坊网络</h2>
      <p className="text-gray-600">选择您要运行验证节点的网络</p>

      <div className="grid grid-cols-1 gap-4">
        {networks.map((network) => (
          <button
            key={network.id}
            onClick={() => setSelectedNetwork(network.id)}
            className={`p-4 border-2 rounded-lg text-left transition ${
              selectedNetwork === network.id
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold flex items-center gap-2">
                  {network.name}
                  {network.recommended && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                      推荐
                    </span>
                  )}
                </h3>
                <p className="text-sm text-gray-600 mt-1">{network.description}</p>
              </div>
              {selectedNetwork === network.id && (
                <Check className="w-6 h-6 text-blue-600" />
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
