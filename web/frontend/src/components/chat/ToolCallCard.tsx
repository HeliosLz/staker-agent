import { useState, useMemo, memo } from 'react';
import { Loader2, CheckCircle2, XCircle, ChevronDown, ChevronRight } from 'lucide-react';
import type { ToolCallInfo } from '../../types';

const TOOL_LABELS: Record<string, string> = {
  check_environment: '环境检查',
  install_eth_docker: '安装 eth-docker',
  generate_config: '生成配置',
  generate_keys: '生成密钥',
  deploy_node: '部署节点',
  check_node_status: '节点状态',
};

interface Props {
  toolCall: ToolCallInfo;
}

export default memo(function ToolCallCard({ toolCall }: Props) {
  const [expanded, setExpanded] = useState(false);
  const label = TOOL_LABELS[toolCall.tool_name] || toolCall.tool_name;
  const resultStr = useMemo(
    () => toolCall.result ? JSON.stringify(toolCall.result, null, 2) : '',
    [toolCall.result],
  );

  const statusIcon =
    toolCall.status === 'running' ? (
      <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
    ) : toolCall.status === 'done' ? (
      <CheckCircle2 className="w-4 h-4 text-green-500" />
    ) : (
      <XCircle className="w-4 h-4 text-red-500" />
    );

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden bg-white text-sm">
      <button
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {statusIcon}
        <span className="font-medium text-gray-700 flex-1 text-left">{label}</span>
        {toolCall.result && (
          expanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />
        )}
      </button>
      {expanded && resultStr && (
        <div className="px-3 py-2 border-t border-gray-100 bg-gray-50">
          <pre className="text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap break-words">
            {resultStr}
          </pre>
        </div>
      )}
    </div>
  );
});
