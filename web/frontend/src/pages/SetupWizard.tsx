import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Loader2, AlertCircle, ChevronRight, ChevronLeft } from 'lucide-react';
import { envAPI, configAPI, deployAPI } from '../services/api';
import type { Network, Client, EnvCheck } from '../types';

const STEPS = [
  { id: 1, name: '环境检查', description: '检测系统环境' },
  { id: 2, name: '选择网络', description: '选择以太坊网络' },
  { id: 3, name: '选择客户端', description: '选择共识客户端' },
  { id: 4, name: '密钥生成', description: '生成验证者密钥' },
  { id: 5, name: '部署节点', description: '启动验证节点' },
];

export default function SetupWizard() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Step 1: Environment Check
  const [envCheck, setEnvCheck] = useState<EnvCheck | null>(null);
  const [envPassed, setEnvPassed] = useState(false);
  const [fixingIssue, setFixingIssue] = useState<string | null>(null);
  const [fixInstructions, setFixInstructions] = useState<string[]>([]);

  // Step 2: Network Selection
  const [networks, setNetworks] = useState<Network[]>([]);
  const [selectedNetwork, setSelectedNetwork] = useState<string>('');

  // Step 3: Client Selection
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<string>('');

  // Step 4: Key Generation
  const [withdrawalAddress, setWithdrawalAddress] = useState<string>('');
  const [validatorCount, setValidatorCount] = useState<number>(1);
  const [mnemonic, setMnemonic] = useState<string>('');

  // Step 5: Deployment
  const [deployStatus, setDeployStatus] = useState<string>('');

  // Load networks and clients on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const [networksRes, clientsRes] = await Promise.all([
          configAPI.getNetworks(),
          configAPI.getClients(),
        ]);
        setNetworks(networksRes.data.data);
        setClients(clientsRes.data.data);

        // Set defaults to recommended
        const defaultNetwork = networksRes.data.data.find((n: Network) => n.recommended);
        const defaultClient = clientsRes.data.data.find((c: Client) => c.recommended);
        if (defaultNetwork) setSelectedNetwork(defaultNetwork.id);
        if (defaultClient) setSelectedClient(defaultClient.id);
      } catch (error) {
        console.error('Failed to load data:', error);
      }
    };
    loadData();
  }, []);

  // Error state
  const [error, setError] = useState<string | null>(null);

  // Step 1: Run environment check
  const runEnvCheck = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await envAPI.check();
      setEnvCheck(response.data.data);
      setEnvPassed(response.data.all_passed);

      // 如果 Docker 未安装,自动尝试修复
      if (!response.data.data.docker.supported) {
        await handleAutoFix('docker');
      }
    } catch (error: any) {
      console.error('Environment check failed:', error);
      const errorMessage = error.response?.data?.message || error.response?.data?.error || '环境检查失败，请重试';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 自动修复问题
  const handleAutoFix = async (issue: string) => {
    setFixingIssue(issue);
    setError(null);
    try {
      const response = await fetch(`http://localhost:5001/api/fix/docker/install`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`修复失败: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success && data.instructions) {
        setFixInstructions(data.instructions);
      } else if (data.error) {
        setError(data.error);
      }
    } catch (error: any) {
      console.error('Auto-fix failed:', error);
      setError(error.message || '自动修复失败，请手动安装');
    } finally {
      setFixingIssue(null);
    }
  };

  // Step 5: Deploy
  const handleDeploy = async () => {
    setLoading(true);
    setError(null);
    try {
      // Step 1: Setup dependencies
      setDeployStatus('安装依赖...');
      await deployAPI.setup();

      // Step 2: Generate config
      setDeployStatus('生成配置...');
      await configAPI.generate({
        network: selectedNetwork,
        client: selectedClient,
      });

      // Step 3: Generate keys (simulated)
      setDeployStatus('生成密钥...');
      // In real scenario, this would call deployAPI.generateKeys()

      // Step 4: Deploy
      setDeployStatus('部署节点...');
      await deployAPI.start();

      setDeployStatus('部署完成!');
      setTimeout(() => navigate('/dashboard'), 2000);
    } catch (error: any) {
      console.error('Deployment failed:', error);
      const errorMessage = error.response?.data?.error || error.message || '部署失败';
      setDeployStatus('');
      setError(`部署失败: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">🔍 环境检查</h2>
            <p className="text-gray-600">检查您的系统是否满足运行验证节点的要求</p>

            {/* Error Alert */}
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

                {/* Agent 自动修复提示 */}
                {fixInstructions.length > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
                    <div className="flex gap-3">
                      <div className="flex-shrink-0">
                        🤖
                      </div>
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
                      <span className="text-yellow-800">
                        🤖 智能助手正在分析问题...
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );

      case 2:
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

      case 3:
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

      case 4:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">🔑 生成验证者密钥</h2>
            <p className="text-gray-600">配置您的验证者密钥参数</p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">验证者数量</label>
                <input
                  type="number"
                  min="1"
                  value={validatorCount}
                  onChange={(e) => setValidatorCount(parseInt(e.target.value))}
                  className="w-full border border-gray-300 rounded-lg px-4 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">提款地址</label>
                <input
                  type="text"
                  placeholder="0x..."
                  value={withdrawalAddress}
                  onChange={(e) => setWithdrawalAddress(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-4 py-2 font-mono"
                />
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

      case 5:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">🚀 准备部署</h2>
            <p className="text-gray-600">确认配置并开始部署</p>

            <div className="bg-gray-50 rounded-lg p-6 space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">网络:</span>
                <span className="font-semibold">{selectedNetwork}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">客户端:</span>
                <span className="font-semibold">{selectedClient}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">验证者数量:</span>
                <span className="font-semibold">{validatorCount}</span>
              </div>
            </div>

            {deployStatus && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-800 flex items-center gap-2">
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  {deployStatus}
                </p>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold text-red-900 mb-1">错误</h4>
                    <p className="text-sm text-red-700">{error}</p>
                    <button
                      onClick={() => {
                        setError(null);
                        handleDeploy();
                      }}
                      className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                    >
                      重试
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return envPassed;
      case 2:
        return selectedNetwork !== '';
      case 3:
        return selectedClient !== '';
      case 4:
        return withdrawalAddress.startsWith('0x') && withdrawalAddress.length === 42;
      case 5:
        return true;
      default:
        return false;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                      currentStep >= step.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {currentStep > step.id ? <Check className="w-6 h-6" /> : step.id}
                  </div>
                  <p className="text-xs mt-2 text-center">{step.name}</p>
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={`h-1 flex-1 mx-2 ${
                      currentStep > step.id ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-xl p-8 shadow-sm mb-6">{renderStep()}</div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={() => setCurrentStep((prev) => Math.max(1, prev - 1))}
            disabled={currentStep === 1}
            className="flex items-center gap-2 px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
            上一步
          </button>

          <button
            onClick={() => {
              if (currentStep === 5) {
                handleDeploy();
              } else {
                setCurrentStep((prev) => Math.min(5, prev + 1));
              }
            }}
            disabled={!canProceed() || loading}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {currentStep === 5 ? '开始部署' : '下一步'}
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}

// Helper component for environment check items
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
