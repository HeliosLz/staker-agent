import { useState } from 'react';
import { Shield, Loader2 } from 'lucide-react';
import { setAuthToken } from '../services/authToken';
import { reconnectSocket } from '../services/socket';
import { api } from '../services/api';

interface Props {
  onAuthenticated: () => void;
}

export default function AuthTokenModal({ onAuthenticated }: Props) {
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) return;

    setLoading(true);
    setError('');
    try {
      setAuthToken(token.trim());
      await api.get('/api/auth/check');
      reconnectSocket();
      onAuthenticated();
    } catch (err: unknown) {
      const msg = (err as { response?: { status?: number } })?.response?.status === 401
        ? 'Token 无效'
        : '连接失败，请检查后端是否运行';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-8 shadow-2xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-pink-100 flex items-center justify-center">
            <Shield className="w-5 h-5 text-pink-600" />
          </div>
          <h3 className="text-lg font-bold text-gray-900">API 认证</h3>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          请输入服务端配置的 <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">STAKER_AGENT_API_TOKEN</code> 以继续操作。
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            value={token}
            onChange={e => setToken(e.target.value)}
            placeholder="输入 API Token"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent"
            autoFocus
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button
            type="submit"
            disabled={loading || !token.trim()}
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
