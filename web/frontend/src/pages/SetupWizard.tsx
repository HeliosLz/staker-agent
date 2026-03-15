import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Loader2, ChevronRight, ChevronLeft } from 'lucide-react';
import { envAPI, configAPI, deployAPI } from '../services/api';
import { usePipelineProgress } from '../hooks/usePipelineProgress';
import type { Network, Client, EnvCheck } from '../types';

import EnvironmentCheck from '../components/setup/EnvironmentCheck';
import NetworkSelection from '../components/setup/NetworkSelection';
import ClientSelection from '../components/setup/ClientSelection';
import KeyGeneration from '../components/setup/KeyGeneration';
import Deployment from '../components/setup/Deployment';

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
  const [error, setError] = useState<string | null>(null);

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
  const [useLidoCSM, setUseLidoCSM] = useState<boolean>(false);
  const [lidoCsmInfo, setLidoCsmInfo] = useState<any>(null);
  const [keystorePassword, setKeystorePassword] = useState<string>('');
  const [showMnemonic, setShowMnemonic] = useState(false);

  // Pipeline hook
  const pipeline = usePipelineProgress();

  // Show mnemonic or redirect on pipeline success
  useEffect(() => {
    if (pipeline.completed && pipeline.success) {
      if (pipeline.mnemonic) {
        setShowMnemonic(true);
      } else {
        const timer = setTimeout(() => navigate('/dashboard'), 3000);
        return () => clearTimeout(timer);
      }
    }
    if (pipeline.completed && !pipeline.success && pipeline.error) {
      setError(pipeline.error);
    }
  }, [pipeline.completed, pipeline.success, pipeline.error, pipeline.mnemonic, navigate]);

  useEffect(() => {
    if (useLidoCSM && selectedNetwork) {
      deployAPI.getLidoCsmInfo(selectedNetwork)
        .then(res => {
          if (res.data.success) {
            setLidoCsmInfo(res.data.data);
            if (res.data.data.withdrawal_vault) {
              setWithdrawalAddress(res.data.data.withdrawal_vault);
            }
          }
        })
        .catch(err => console.error('Failed to load Lido CSM info:', err));
    } else if (!useLidoCSM) {
      setWithdrawalAddress('');
      setLidoCsmInfo(null);
    }
  }, [useLidoCSM, selectedNetwork]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [networksRes, clientsRes] = await Promise.all([
          configAPI.getNetworks(),
          configAPI.getClients(),
        ]);
        setNetworks(networksRes.data.data);
        setClients(clientsRes.data.data);

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

  const runEnvCheck = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await envAPI.check();
      setEnvCheck(response.data.data);
      setEnvPassed(response.data.all_passed);

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

  const handleAutoFix = async (issue: string) => {
    setFixingIssue(issue);
    setError(null);
    try {
      const response = await fetch(`/api/fix/docker/instructions`, { method: 'GET' });
      if (!response.ok) {
        throw new Error(`获取指引失败: ${response.statusText}`);
      }
      const data = await response.json();
      if (data.instructions) {
        setFixInstructions(data.instructions);
      } else if (data.error) {
        setError(data.error);
      }
    } catch (error: any) {
      console.error('Failed to get instructions:', error);
      setError(error.message || '获取安装指引失败');
    } finally {
      setFixingIssue(null);
    }
  };

  const handleDeploy = async () => {
    setLoading(true);
    setError(null);
    pipeline.reset();

    await pipeline.startPipeline({
      network: selectedNetwork,
      client: selectedClient,
      withdrawal_address: withdrawalAddress || undefined,
      num_validators: validatorCount,
      use_lido_csm: useLidoCSM,
      keystore_password: keystorePassword || undefined,
    });

    // loading state is now driven by pipeline.completed
    setLoading(false);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <EnvironmentCheck
            envCheck={envCheck}
            loading={loading}
            error={error}
            fixingIssue={fixingIssue}
            fixInstructions={fixInstructions}
            setFixInstructions={setFixInstructions}
            runEnvCheck={runEnvCheck}
          />
        );
      case 2:
        return (
          <NetworkSelection
            networks={networks}
            selectedNetwork={selectedNetwork}
            setSelectedNetwork={setSelectedNetwork}
          />
        );
      case 3:
        return (
          <ClientSelection
            clients={clients}
            selectedClient={selectedClient}
            setSelectedClient={setSelectedClient}
          />
        );
      case 4:
        return (
          <KeyGeneration
            withdrawalAddress={withdrawalAddress}
            setWithdrawalAddress={setWithdrawalAddress}
            validatorCount={validatorCount}
            setValidatorCount={setValidatorCount}
            useLidoCSM={useLidoCSM}
            setUseLidoCSM={setUseLidoCSM}
            lidoCsmInfo={lidoCsmInfo}
            keystorePassword={keystorePassword}
            setKeystorePassword={setKeystorePassword}
          />
        );
      case 5:
        return (
          <Deployment
            selectedNetwork={selectedNetwork}
            selectedClient={selectedClient}
            validatorCount={validatorCount}
            useLidoCSM={useLidoCSM}
            lidoCsmInfo={lidoCsmInfo}
            loading={loading || (pipeline.steps.length > 0 && !pipeline.completed)}
            error={error}
            setError={setError}
            handleDeploy={handleDeploy}
            pipelineSteps={pipeline.steps}
            pipelineCompleted={pipeline.completed}
            pipelineSuccess={pipeline.success}
          />
        );
      default:
        return null;
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1: return envPassed;
      case 2: return selectedNetwork !== '';
      case 3: return selectedClient !== '';
      case 4: {
        if (keystorePassword.length < 12) return false;
        if (useLidoCSM) return true;
        if (!withdrawalAddress) return true;
        return withdrawalAddress.startsWith('0x') && withdrawalAddress.length === 42;
      }
      case 5: return true;
      default: return false;
    }
  };

  const finalCanProceed = canProceed();
  const pipelineRunning = pipeline.steps.length > 0 && !pipeline.completed;

  return (
    <div className="min-h-screen bg-gray-50 py-8" style={{ background: '#f9fafb', color: '#111827' }}>
      <div className="container mx-auto px-4 max-w-4xl">
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

        <div className="bg-white rounded-xl p-8 shadow-sm mb-6">{renderStep()}</div>

        <div className="flex justify-between">
          <button
            onClick={() => setCurrentStep((prev) => Math.max(1, prev - 1))}
            disabled={currentStep === 1 || pipelineRunning}
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
            disabled={!finalCanProceed || loading || pipelineRunning}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {currentStep === 5 ? '开始部署' : '下一步'}
            {(loading || pipelineRunning) ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Mnemonic Modal */}
      {showMnemonic && pipeline.mnemonic && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-8 shadow-2xl">
            <h3 className="text-xl font-bold text-gray-900 mb-2">请备份您的助记词</h3>
            <p className="text-sm text-red-600 mb-4">
              这是恢复密钥的唯一方式。请将助记词抄写在纸上并妥善保管，关闭后将无法再次查看。
            </p>
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-6">
              <div className="grid grid-cols-4 gap-2">
                {pipeline.mnemonic.split(' ').map((word, i) => (
                  <div key={i} className="bg-white border border-yellow-300 rounded-lg px-2 py-1.5 text-center">
                    <span className="text-xs text-gray-400 mr-1">{i + 1}.</span>
                    <span className="font-mono text-sm font-medium text-gray-900">{word}</span>
                  </div>
                ))}
              </div>
            </div>
            <button
              onClick={() => {
                setShowMnemonic(false);
                navigate('/dashboard');
              }}
              className="w-full bg-blue-600 text-white py-3 rounded-xl font-medium hover:bg-blue-700 transition-colors"
            >
              我已安全备份，进入控制面板
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
