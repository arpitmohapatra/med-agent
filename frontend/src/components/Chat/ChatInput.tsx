import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Square } from 'lucide-react';
import { ChatMode } from '../../types';
import { SAMPLE_QUERIES } from '../../utils/constants';
import { classNames } from '../../utils/helpers';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  mode: ChatMode;
  isStreaming?: boolean;
  onStop?: () => void;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled = false,
  mode,
  isStreaming = false,
  onStop,
}) => {
  const [message, setMessage] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const sampleQueries = SAMPLE_QUERIES[mode] || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      setShowSuggestions(false);
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion);
    setShowSuggestions(false);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [message]);

  return (
    <div className="border-t border-gray-200 bg-white">
      {/* Sample Queries */}
      {showSuggestions && sampleQueries.length > 0 && (
        <div className="px-6 py-3 border-b border-gray-100">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-sm font-medium text-gray-700">Sample Queries:</span>
            <button
              onClick={() => setShowSuggestions(false)}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              Hide
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {sampleQueries.map((query, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(query)}
                className="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
              >
                {query}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form */}
      <div className="px-6 py-4">
        <form onSubmit={handleSubmit} className="flex items-end space-x-3">
          {/* Suggestions Button */}
          {sampleQueries.length > 0 && (
            <button
              type="button"
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="flex-shrink-0 p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Show sample queries"
            >
              <span className="text-xl">💡</span>
            </button>
          )}

          {/* Message Input */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Ask me anything${mode === 'rag' ? ' about medicines' : mode === 'agent' ? ' (I can use tools)' : ''}...`}
              disabled={disabled}
              rows={1}
              className={classNames(
                'w-full px-4 py-3 border border-gray-300 rounded-lg resize-none',
                'focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder-gray-500 text-gray-900',
                'disabled:bg-gray-50 disabled:text-gray-500',
                'custom-scrollbar'
              )}
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            {/* Voice Input (placeholder) */}
            <button
              type="button"
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Voice input (coming soon)"
              disabled
            >
              <Mic className="w-5 h-5" />
            </button>

            {/* Stop/Send Button */}
            {isStreaming ? (
              <button
                type="button"
                onClick={onStop}
                className="flex-shrink-0 p-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                title="Stop generation"
              >
                <Square className="w-5 h-5" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!message.trim() || disabled}
                className={classNames(
                  'flex-shrink-0 p-2 rounded-lg transition-colors',
                  message.trim() && !disabled
                    ? 'bg-primary-600 text-white hover:bg-primary-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                )}
                title="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            )}
          </div>
        </form>

        {/* Helper Text */}
        <div className="mt-2 text-xs text-gray-500 flex items-center justify-between">
          <span>Press Enter to send, Shift+Enter for new line</span>
          {mode === 'rag' && (
            <span className="text-medical-600">Responses include source citations</span>
          )}
          {mode === 'agent' && (
            <span className="text-purple-600">AI agent with tool access</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
