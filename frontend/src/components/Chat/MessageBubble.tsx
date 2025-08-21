import React from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Bot } from 'lucide-react';
import { ChatMessage } from '../../types';
import { formatTimestamp, classNames } from '../../utils/helpers';
import { MEDICAL_DISCLAIMER } from '../../utils/constants';

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isStreaming }) => {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  return (
    <div className={classNames(
      'flex w-full mb-4 animate-slide-up',
      isUser ? 'justify-end' : 'justify-start'
    )}>
      <div className={classNames(
        'flex max-w-[85%] space-x-3',
        isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'
      )}>
        {/* Avatar */}
        <div className={classNames(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser 
            ? 'bg-primary-100 text-primary-600' 
            : 'bg-medical-100 text-medical-600'
        )}>
          {isUser ? (
            <User className="w-5 h-5" />
          ) : (
            <Bot className="w-5 h-5" />
          )}
        </div>

        {/* Message Content */}
        <div className={classNames(
          'rounded-lg px-4 py-3 shadow-sm',
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-white border border-gray-200 text-gray-900'
        )}>
          {/* Message Text */}
          <div className="message-content">
            {isAssistant ? (
              <ReactMarkdown
                className={classNames(
                  'prose prose-sm max-w-none',
                  'prose-headings:text-gray-900 prose-p:text-gray-700',
                  'prose-code:bg-gray-100 prose-code:text-gray-800 prose-code:px-1 prose-code:rounded',
                  'prose-pre:bg-gray-100 prose-pre:text-gray-800',
                  'prose-strong:text-gray-900 prose-em:text-gray-700',
                  'prose-ul:text-gray-700 prose-ol:text-gray-700',
                  'prose-li:text-gray-700'
                )}
              >
                {message.content}
              </ReactMarkdown>
            ) : (
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            )}
            
            {/* Streaming indicator */}
            {isStreaming && (
              <span className="inline-block w-2 h-4 bg-gray-400 ml-1 animate-pulse" />
            )}
          </div>

          {/* Medical Disclaimer for Assistant Messages */}
          {isAssistant && message.content.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <p className="text-xs text-gray-500 italic">
                {MEDICAL_DISCLAIMER}
              </p>
            </div>
          )}

          {/* Timestamp */}
          {message.timestamp && (
            <div className={classNames(
              'text-xs mt-2',
              isUser ? 'text-primary-100' : 'text-gray-400'
            )}>
              {formatTimestamp(message.timestamp)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
