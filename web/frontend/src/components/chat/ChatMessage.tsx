import { memo } from 'react';
import { Bot, User } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '../../types';
import ToolCallCard from './ToolCallCard';

interface Props {
  message: ChatMessageType;
}

export default memo(function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-pink-100 flex items-center justify-center flex-shrink-0 mt-1">
          <Bot className="w-4 h-4 text-pink-600" />
        </div>
      )}
      <div className={`max-w-[75%] space-y-2 ${isUser ? 'order-first' : ''}`}>
        {message.content && (
          <div
            className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
              isUser
                ? 'bg-pink-600 text-white rounded-br-md'
                : 'bg-gray-100 text-gray-800 rounded-bl-md'
            }`}
          >
            {message.content}
          </div>
        )}
        {message.toolCalls?.map((tc) => (
          <ToolCallCard key={tc.tool_id} toolCall={tc} />
        ))}
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 mt-1">
          <User className="w-4 h-4 text-gray-600" />
        </div>
      )}
    </div>
  );
});
