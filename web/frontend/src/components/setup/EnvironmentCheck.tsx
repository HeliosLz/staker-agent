import { Loader2, AlertCircle, Check } from 'lucide-react';
import type { EnvCheck } from '../../types';

interface EnvironmentCheckProps {
  envCheck: EnvCheck | null;
  loading: boolean;
  error: string | null;
  fixingIssue: string | null;
  fixInstructions: string[];
  setFixInstructions: (instructions: string[]) => void;
  runEnvCheck: () => void;
}

export default function EnvironmentCheck({
  envCheck,
  loading,
  error,
  fixingIssue,
  fixInstructions,
  setFixInstructions,
  runEnvCheck,
}: EnvironmentCheckProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">🔍 环境检查</h2>
      <p className="text-gray-600">检查您的系统是否满足运行验证节点的要求</p>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <div>
              <h4 className="font-semibold text-red-900 mb-1">错误</h4>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {!envCheck ? (
        <button
          onClick={runEnvCheck}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          开始检查
        </button>
      ) : (
        <div className="space-y-4">
          <div className="space-y-3">
            <CheckItem
              label="操作系统"
              value={envCheck.os.name}
              status={envCheck.os.supported ? 'success' : 'error'}
              error={envCheck.os.error}
            />
            <CheckItem
              label="Python"
              value={envCheck.python.name}
              status={envCheck.python.supported ? 'success' : 'error'}
              error={envCheck.python.error}
            />
            <CheckItem
              label="Docker"
              value={envCheck.docker.name}
              status={envCheck.docker.supported ? 'success' : 'error'}
              error={envCheck.docker.error}
            />
            <CheckItem
              label="磁盘空间"
              value={envCheck.disk.name}
              status={envCheck.disk.supported ? 'success' : 'error'}
              error={envCheck.disk.error}
            />
            <CheckItem
              label="网络连接"
              value={envCheck.network.name}
              status={envCheck.network.supported ? 'success' : 'error'}
              error={envCheck.network.error}
            />
          </div>

          {fixInstructions.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
              <div className="flex gap-3">
                <div className="flex-shrink-0">🤖</div>
                <div className="flex-1">
                  <h4 className="font-semibold text-blue-900 mb-2">
                    智能助手检测到问题，为您提供解决方案
                  </h4>
                  <div className="text-sm text-blue-800 space-y-1 font-mono bg-blue-100 p-3 rounded">
                    {fixInstructions.map((instruction, index) => (
                      <div key={index}>{instruction}</div>
                    ))}
                  </div>
                  <button
                    onClick={() => setFixInstructions([])}
                    className="mt-3 text-sm text-blue-600 hover:text-blue-800"
                  >
                    知道了
                  </button>
                </div>
              </div>
            </div>
          )}

          {fixingIssue && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-yellow-600" />
                <span className="text-yellow-800">🤖 智能助手正在分析问题...</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CheckItem({ label, value, status, error }: { label: string; value: string; status: string; error?: string }) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex-1">
        <p className="font-medium">{label}</p>
        <p className="text-sm text-gray-600">{value}</p>
        {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
      </div>
      {status === 'success' ? (
        <Check className="w-6 h-6 text-green-600" />
      ) : (
        <AlertCircle className="w-6 h-6 text-red-600" />
      )}
    </div>
  );
}
