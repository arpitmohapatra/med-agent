import React from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Bot } from 'lucide-react';
import { ChatMessage } from '../../types';
import { formatTimestamp, cn } from '../../utils/helpers';
import { MEDICAL_DISCLAIMER } from '../../utils/constants';
import { Card, CardContent } from '../ui/card';
import { Avatar, AvatarFallback } from '../ui/avatar';

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isStreaming }) => {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  return (
    <div className={cn(
      'flex w-full mb-6 animate-in slide-in-from-bottom-4 duration-500',
      isUser ? 'justify-end' : 'justify-start'
    )}>
      <div className={cn(
        'flex max-w-[85%] space-x-4',
        isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'
      )}>
        {/* Avatar */}
        <Avatar className={cn(
          'w-10 h-10 transition-all duration-300 hover:scale-105',
          isUser ? '' : 'ring-2 ring-primary/20'
        )}>
          <AvatarFallback className={cn(
            'transition-colors duration-300',
            isUser 
              ? 'bg-primary text-primary-foreground' 
              : 'bg-secondary text-secondary-foreground'
          )}>
            {isUser ? (
              <User className="w-5 h-5" />
            ) : (
              <Bot className="w-5 h-5" />
            )}
          </AvatarFallback>
        </Avatar>

        {/* Message Content */}
        <Card className={cn(
          'transition-all duration-300 hover:shadow-md border-0',
          isUser
            ? 'bg-primary text-primary-foreground shadow-lg'
            : 'bg-card shadow-sm hover:shadow-md'
        )}>
          <CardContent className="p-4">
          {/* Message Text */}
          <div className="message-content">
            {isAssistant ? (
              <ReactMarkdown
                className={cn(
                  'prose prose-sm max-w-none',
                  'prose-headings:text-foreground prose-p:text-muted-foreground',
                  'prose-code:bg-muted prose-code:text-foreground prose-code:px-1 prose-code:rounded',
                  'prose-pre:bg-muted prose-pre:text-foreground prose-pre:p-3 prose-pre:rounded-lg',
                  'prose-strong:text-foreground prose-em:text-muted-foreground',
                  'prose-ul:text-muted-foreground prose-ol:text-muted-foreground',
                  'prose-li:text-muted-foreground prose-a:text-primary hover:prose-a:text-primary/80',
                  'prose-blockquote:border-primary prose-blockquote:text-muted-foreground'
                )}
              >
                {message.content}
              </ReactMarkdown>
            ) : (
              <p className="text-primary-foreground leading-relaxed font-medium">{message.content}</p>
            )}
            
            {/* Streaming indicator */}
            {isStreaming && isAssistant && (
              <div className="flex items-center space-x-2 mt-3 animate-in fade-in-50 duration-500">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                </div>
                <span className="text-xs text-muted-foreground">AI is thinking...</span>
              </div>
            )}
          </div>

          {/* Timestamp */}
          {message.timestamp && (
            <div className={cn(
              'text-xs mt-3 pt-2 border-t opacity-70 transition-opacity duration-300',
              isUser 
                ? 'text-primary-foreground/70 border-primary-foreground/20' 
                : 'text-muted-foreground border-border'
            )}>
              {formatTimestamp(message.timestamp)}
            </div>
          )}
          
          {/* Medical Disclaimer for assistant messages */}
          {isAssistant && message.content.length > 50 && (
            <div className="mt-3 pt-3 border-t border-border">
              <p className="text-xs text-muted-foreground italic leading-relaxed">
                {MEDICAL_DISCLAIMER}
              </p>
            </div>
          )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MessageBubble;
