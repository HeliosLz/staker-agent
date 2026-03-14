import { Loader2, Check, Circle, XCircle, AlertCircle } from 'lucide-react';
import type { PipelineStep } from '../../hooks/usePipelineProgress';

interface DeploymentProps {
  selectedNetwork: string;
  selectedClient: string;
  validatorCount: number;
  useLidoCSM: boolean;
  lidoCsmInfo: any;
  loading: boolean;
  error: string | null;
  setError: (error: string | null) => void;
  handleDeploy: () => void;
  pipelineSteps: PipelineStep[];
  pipelineCompleted: boolean;
  pipelineSuccess: boolean;
}

function StepIcon({ status }: { status: PipelineStep['status'] }) {
  switch (status) {
    case 'done':
      return <Check className="w-5 h-5 text-green-600" />;
    case 'running':
      return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
    case 'failed':
      return <XCircle className="w-5 h-5 text-red-600" />;
    default:
      return <Circle className="w-5 h-5 text-gray-400" />;
  }
}

function borderColor(status: PipelineStep['status']) {
  switch (status) {
    case 'done':
      return 'border-green-400';
    case 'running':
      return 'border-blue-500';
    case 'failed':
      return 'border-red-400';
    default:
      return 'border-gray-200';
  }
}

export default function Deployment({
  selectedNetwork,
  selectedClient,
  validatorCount,
  useLidoCSM,
  lidoCsmInfo,
  loading,
  error,
  setError,
  handleDeploy,
  pipelineSteps,
  pipelineCompleted,
  pipelineSuccess,
}: DeploymentProps) {
  const hasSteps = pipelineSteps.length > 0;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">准备部署</h2>
      <p className="text-gray-600">确认配置并开始部署</p>

      {/* Config summary */}
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
        {useLidoCSM && (
          <>
            <div className="flex justify-between">
              <span className="text-gray-600">质押方式:</span>
              <span className="font-semibold text-purple-600">Lido CSM</span>
            </div>
            {lidoCsmInfo && (
              <div className="flex justify-between">
                <span className="text-gray-600">质押要求:</span>
                <span className="font-semibold text-purple-600">{lidoCsmInfo.bond_amount}</span>
              </div>
            )}
          </>
        )}
      </div>

      {useLidoCSM && lidoCsmInfo && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h4 className="font-semibold text-purple-900 mb-2">Lido CSM 下一步</h4>
          <ol className="text-sm text-purple-800 space-y-2 list-decimal list-inside">
            {lidoCsmInfo.steps.map((step: string, idx: number) => (
              <li key={idx}>{step}</li>
            ))}
          </ol>
          <a
            href={lidoCsmInfo.widget_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-block text-purple-600 hover:text-purple-800 font-medium"
          >
            打开 Lido CSM Widget
          </a>
        </div>
      )}

      {/* Pipeline stepper */}
      {hasSteps && (
        <div className="space-y-2">
          {pipelineSteps.map((s) => (
            <div
              key={s.step}
              className={`flex items-center gap-3 border-l-4 ${borderColor(s.status)} pl-4 py-2`}
            >
              <StepIcon status={s.status} />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm">{s.name}</p>
                {s.message && <p className="text-xs text-gray-500 truncate">{s.message}</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pipeline complete banner */}
      {pipelineCompleted && pipelineSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 font-medium">部署成功！即将跳转到控制面板…</p>
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
}
