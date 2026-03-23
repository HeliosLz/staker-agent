import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RotateCcw } from 'lucide-react';
import { useAgentChat } from '../hooks/useAgentChat';
import { agentAPI } from '../services/agentApi';
import ChatMessage from '../components/chat/ChatMessage';
import ChatInput from '../components/chat/ChatInput';
import ApiKeyModal from '../components/chat/ApiKeyModal';
import MnemonicModal from '../components/chat/MnemonicModal';

const EXAMPLES = [
  '帮我在 Holesky 测试网上部署一个验证者',
  '检查一下系统环境是否满足要求',
  '查看当前节点运行状态',
];

export default function ChatSetup() {
  const navigate = useNavigate();
  const { messages, isStreaming, mnemonic, sendMessage, resetChat, dismissMnemonic } = useAgentChat();
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [apiKeyChecked, setApiKeyChecked] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollTimerRef = useRef<number | null>(null);

  useEffect(() => {
    agentAPI.getApiKeyStatus().then(res => {
      if (!res.data.configured) {
        setShowApiKeyModal(true);
      }
      setApiKeyChecked(true);
    }).catch(() => {
      setApiKeyChecked(true);
    });
  }, []);

  // Throttled scroll-to-bottom
  useEffect(() => {
    if (scrollTimerRef.current !== null) clearTimeout(scrollTimerRef.current);
    scrollTimerRef.current = window.setTimeout(() => {
      scrollTimerRef.current = null;
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }, [messages]);

  useEffect(() => {
    return () => {
      if (scrollTimerRef.current !== null) clearTimeout(scrollTimerRef.current);
    };
  }, []);

  const handleMnemonicConfirm = useCallback(() => {
    dismissMnemonic();
    navigate('/dashboard');
  }, [dismissMnemonic, navigate]);

  if (!apiKeyChecked) return null;

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200">
        <h1 className="text-lg font-bold text-gray-900">Staker Agent AI 助手</h1>
        <button
          onClick={resetChat}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          重置对话
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-2xl bg-pink-100 flex items-center justify-center mb-4">
              <span className="text-2xl">🤖</span>
            </div>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">你好，我是 Staker Agent AI 助手</h2>
            <p className="text-sm text-gray-500 mb-6 max-w-md">
              告诉我你想做什么，我会帮你完成以太坊验证节点的部署。
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {EXAMPLES.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(ex)}
                  className="px-4 py-2 text-sm border border-gray-200 rounded-full text-gray-600 hover:bg-gray-100 hover:border-gray-300 transition-colors"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map(msg => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {isStreaming && messages.length > 0 && messages[messages.length - 1].role !== 'assistant' && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-pink-100 flex items-center justify-center flex-shrink-0">
              <span className="text-sm">🤖</span>
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-2.5">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={sendMessage} disabled={isStreaming} />

      {/* Modals */}
      {showApiKeyModal && (
        <ApiKeyModal onConfigured={() => setShowApiKeyModal(false)} />
      )}
      {mnemonic && (
        <MnemonicModal mnemonic={mnemonic} onConfirm={handleMnemonicConfirm} />
      )}
    </div>
  );
}
