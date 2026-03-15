import { AlertCircle } from 'lucide-react';

interface KeyGenerationProps {
  withdrawalAddress: string;
  setWithdrawalAddress: (address: string) => void;
  validatorCount: number;
  setValidatorCount: (count: number) => void;
  useLidoCSM: boolean;
  setUseLidoCSM: (use: boolean) => void;
  lidoCsmInfo: any;
  keystorePassword: string;
  setKeystorePassword: (pw: string) => void;
}

export default function KeyGeneration({
  withdrawalAddress,
  setWithdrawalAddress,
  validatorCount,
  setValidatorCount,
  useLidoCSM,
  setUseLidoCSM,
  lidoCsmInfo,
  keystorePassword,
  setKeystorePassword,
}: KeyGenerationProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">🔑 生成验证者密钥</h2>
      <p className="text-gray-600">配置您的验证者密钥参数</p>

      <div className="space-y-4">
        {/* Lido CSM Toggle */}
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={useLidoCSM}
              onChange={(e) => setUseLidoCSM(e.target.checked)}
              className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <span className="font-semibold text-gray-900">使用 Lido CSM (社区质押模块)</span>
              <p className="text-sm text-gray-600 mt-1">
                只需 2.4 ETH 即可成为验证者 (早期采用者 1.5 ETH)
              </p>
            </div>
          </label>
        </div>

        {/* Lido CSM Info */}
        {useLidoCSM && lidoCsmInfo && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-2">📋 Lido CSM 信息</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-blue-700">网络:</span>
                <span className="font-mono text-blue-900">{lidoCsmInfo.network}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-700">质押要求:</span>
                <span className="font-semibold text-blue-900">{lidoCsmInfo.bond_amount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-700">接受代币:</span>
                <span className="font-mono text-blue-900">{lidoCsmInfo.accepted_tokens.join(', ')}</span>
              </div>
              <div className="mt-3 pt-3 border-t border-blue-200">
                <a
                  href={lidoCsmInfo.widget_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
                >
                  打开 Lido CSM Widget →
                </a>
              </div>
            </div>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700">验证者数量</label>
          <input
            type="number"
            min="1"
            value={validatorCount}
            onChange={(e) => setValidatorCount(parseInt(e.target.value))}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700">
            提款地址
            {useLidoCSM && <span className="ml-2 text-xs text-blue-600">(已自动填充 Lido Vault)</span>}
          </label>
          <input
            type="text"
            placeholder="0x..."
            value={withdrawalAddress}
            onChange={(e) => setWithdrawalAddress(e.target.value)}
            disabled={useLidoCSM}
            className={`w-full border border-gray-300 rounded-lg px-4 py-2 font-mono bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              useLidoCSM ? 'opacity-60 cursor-not-allowed' : ''
            }`}
          />
          <p className="mt-1 text-xs text-gray-500">
            {useLidoCSM
              ? '使用 Lido CSM 时，提款地址由 Lido 协议管理'
              : '验证者的提款地址，无法更改'}
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700">
            Keystore 密码
            <span className="ml-1 text-xs text-gray-400">(至少 12 位)</span>
          </label>
          <input
            type="password"
            placeholder="设置密钥库密码"
            value={keystorePassword}
            onChange={(e) => setKeystorePassword(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="mt-1 text-xs text-gray-500">
            此密码用于加密 keystore 文件，部署验证者时需要再次输入
          </p>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
            <div>
              <h4 className="font-semibold text-yellow-800 mb-1">⚠️ 重要提示</h4>
              <p className="text-sm text-yellow-700">
                请务必保管好生成的助记词！这是恢复密钥的唯一方式。
                建议将助记词写在纸上,存放在安全的地方。
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
