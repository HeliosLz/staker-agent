import { useState } from 'react';
import { Key, Loader2 } from 'lucide-react';
import { agentAPI } from '../../services/agentApi';

interface Props {
  onConfigured: () => void;
}

export default function ApiKeyModal({ onConfigured }: Props) {
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) return;

    setLoading(true);
    setError('');
    try {
      const res = await agentAPI.setApiKey(apiKey.trim());
      if (res.data.success) {
        onConfigured();
      } else {
        setError(res.data.error || '验证失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || '连接失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-8 shadow-2xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-pink-100 flex items-center justify-center">
            <Key className="w-5 h-5 text-pink-600" />
          </div>
          <h3 className="text-lg font-bold text-gray-900">配置 OpenRouter API Key</h3>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          AI 助手需要您的 OpenRouter API Key 来运行。密钥仅存储在内存中，不会写入磁盘。
          可在 <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer" className="text-pink-600 underline">OpenRouter</a> 获取。
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            value={apiKey}
            onChange={e => setApiKey(e.target.value)}
            placeholder="sk-or-..."
            className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent"
            autoFocus
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button
            type="submit"
            disabled={loading || !apiKey.trim()}
            className="w-full bg-pink-600 text-white py-2.5 rounded-xl font-medium hover:bg-pink-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            {loading ? '验证中...' : '确认'}
          </button>
        </form>
      </div>
    </div>
  );
}
