import { useState, useEffect, useCallback, useRef } from 'react';
import { getSocket } from '../services/socket';
import type { ChatMessage, ToolCallInfo } from '../types';

let nextId = 0;
function uid() {
  return `msg-${Date.now()}-${nextId++}`;
}

type MessageUpdater = (msg: ChatMessage) => ChatMessage;

/**
 * Get or create the current assistant message, apply an updater to it.
 */
function upsertAssistant(
  prev: ChatMessage[],
  refId: string | null,
  updater: MessageUpdater,
  idRef: React.MutableRefObject<string | null>,
): ChatMessage[] {
  const last = prev[prev.length - 1];
  if (last && last.role === 'assistant' && last.id === refId) {
    const updated = updater(last);
    if (updated === last) return prev;
    return [...prev.slice(0, -1), updated];
  }
  const id = uid();
  idRef.current = id;
  const base: ChatMessage = { id, role: 'assistant', content: '' };
  return [...prev, updater(base)];
}

export function useAgentChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [mnemonic, setMnemonic] = useState<string | null>(null);
  const assistantIdRef = useRef<string | null>(null);

  // Throttled text delta buffer
  const textBufferRef = useRef('');
  const flushTimerRef = useRef<number | null>(null);

  const flushTextBuffer = useCallback(() => {
    const buf = textBufferRef.current;
    if (!buf) return;
    textBufferRef.current = '';
    setMessages(prev =>
      upsertAssistant(prev, assistantIdRef.current, msg => ({
        ...msg,
        content: msg.content + buf,
      }), assistantIdRef)
    );
  }, []);

  useEffect(() => {
    const socket = getSocket();

    socket.on('agent_text_delta', (data: { delta: string }) => {
      textBufferRef.current += data.delta;
      if (flushTimerRef.current === null) {
        flushTimerRef.current = window.requestAnimationFrame(() => {
          flushTimerRef.current = null;
          flushTextBuffer();
        });
      }
    });

    socket.on('agent_tool_start', (data: { tool_name: string; tool_input: Record<string, unknown>; tool_id: string }) => {
      // Flush any pending text before adding tool card
      flushTextBuffer();
      const toolCall: ToolCallInfo = {
        tool_name: data.tool_name,
        tool_input: data.tool_input,
        tool_id: data.tool_id,
        status: 'running',
      };
      setMessages(prev =>
        upsertAssistant(prev, assistantIdRef.current, msg => ({
          ...msg,
          toolCalls: [...(msg.toolCalls || []), toolCall],
        }), assistantIdRef)
      );
    });

    socket.on('agent_tool_result', (data: { tool_name: string; tool_id: string; result: Record<string, unknown>; success: boolean }) => {
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (!last || last.role !== 'assistant' || !last.toolCalls) return prev;
        let changed = false;
        const toolCalls = last.toolCalls.map(tc => {
          if (tc.tool_id === data.tool_id && tc.status === 'running') {
            changed = true;
            return { ...tc, status: (data.success ? 'done' : 'failed') as ToolCallInfo['status'], result: data.result };
          }
          return tc;
        });
        if (!changed) return prev;
        return [...prev.slice(0, -1), { ...last, toolCalls }];
      });
    });

    socket.on('agent_mnemonic', (data: { mnemonic: string }) => {
      setMnemonic(data.mnemonic);
    });

    socket.on('agent_turn_complete', () => {
      flushTextBuffer();
      setIsStreaming(false);
      assistantIdRef.current = null;
    });

    socket.on('agent_error', (data: { error: string }) => {
      flushTextBuffer();
      setIsStreaming(false);
      assistantIdRef.current = null;
      setMessages(prev => [
        ...prev,
        { id: uid(), role: 'assistant', content: `**Error:** ${data.error}` },
      ]);
    });

    return () => {
      socket.off('agent_text_delta');
      socket.off('agent_tool_start');
      socket.off('agent_tool_result');
      socket.off('agent_mnemonic');
      socket.off('agent_turn_complete');
      socket.off('agent_error');
      if (flushTimerRef.current !== null) {
        cancelAnimationFrame(flushTimerRef.current);
      }
    };
  }, [flushTextBuffer]);

  const sendMessage = useCallback((text: string) => {
    if (!text.trim() || isStreaming) return;
    const id = uid();
    setMessages(prev => [...prev, { id, role: 'user', content: text }]);
    setIsStreaming(true);
    assistantIdRef.current = null;
    const socket = getSocket();
    socket.emit('agent_message', { message: text });
  }, [isStreaming]);

  const resetChat = useCallback(() => {
    const socket = getSocket();
    socket.emit('agent_reset', {});
    setMessages([]);
    setMnemonic(null);
    setIsStreaming(false);
    assistantIdRef.current = null;
  }, []);

  const dismissMnemonic = useCallback(() => {
    setMnemonic(null);
  }, []);

  return { messages, isStreaming, mnemonic, sendMessage, resetChat, dismissMnemonic };
}
