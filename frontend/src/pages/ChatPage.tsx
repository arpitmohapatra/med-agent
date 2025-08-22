import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChatMode, ChatMessage, Source, User, StreamEvent } from '../types';
import { authService } from '../services/auth';
import { apiService } from '../services/api';
import Header from '../components/Layout/Header';
import MessageBubble from '../components/Chat/MessageBubble';
import ChatInput from '../components/Chat/ChatInput';
import SourcePanel from '../components/Chat/SourcePanel';
import { generateId } from '../utils/helpers';
import toast from 'react-hot-toast';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { ScrollArea } from '../components/ui/scroll-area';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../components/ui/collapsible';
import { ChevronLeft, ChevronRight, Bot } from 'lucide-react';

const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [currentMode, setCurrentMode] = useState<ChatMode>('ask');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [_streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [isSourcePanelCollapsed, setIsSourcePanelCollapsed] = useState<boolean>(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    initializeUser();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeUser = async () => {
    try {
      const user = await authService.getCurrentUser();
      if (!user) {
        navigate('/login');
        return;
      }
      setCurrentUser(user);
    } catch (error) {
      console.error('Failed to get current user:', error);
      navigate('/login');
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleModeChange = (mode: ChatMode) => {
    setCurrentMode(mode);
    setSources([]);
    setCurrentQuery('');
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/login');
    }
  };

  const handleSendMessage = async (messageContent: string) => {
    if (isStreaming) {
      return;
    }

    setCurrentQuery(messageContent);

    // Add user message
    const userMessage: ChatMessage = {
      role: 'user',
      content: messageContent,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);

    // Create assistant message placeholder
    const assistantMessageId = generateId();
    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, assistantMessage]);
    setStreamingMessageId(assistantMessageId);
    setIsStreaming(true);

    if (currentMode === 'rag') {
      setSources([]);
    }

    try {
      // Create abort controller for this request
      abortControllerRef.current = new AbortController();

      await apiService.sendStreamingMessage(
        {
          message: messageContent,
          mode: currentMode,
          conversation_history: messages,
          stream: true,
        },
        handleStreamChunk,
        handleStreamError
      );
    } catch (error) {
      handleStreamError(error);
    }
  };

  const handleStreamChunk = (chunk: StreamEvent) => {
    if (chunk.error) {
      handleStreamError(new Error(chunk.error));
      return;
    }

    if (chunk.content) {
      console.log('📝 Received chunk:', JSON.stringify(chunk.content));
      // Update the last assistant message with new content
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage.role === 'assistant') {
          lastMessage.content += chunk.content;
        }
        return newMessages;
      });
    }

    if (chunk.sources && currentMode === 'rag') {
      setSources(chunk.sources);
    }

    if (chunk.action && currentMode === 'agent') {
      // Handle agent actions
      console.log('Agent action:', chunk.action);
      toast.success(`Action: ${chunk.action.action}`);
    }

    if (chunk.done) {
      setIsStreaming(false);
      setStreamingMessageId(null);
      abortControllerRef.current = null;
    }
  };

  const handleStreamError = (error: any) => {
    console.error('Streaming error:', error);
    setIsStreaming(false);
    setStreamingMessageId(null);
    abortControllerRef.current = null;

    // Update the last assistant message with error
    setMessages(prev => {
      const newMessages = [...prev];
      const lastMessage = newMessages[newMessages.length - 1];
      if (lastMessage.role === 'assistant' && !lastMessage.content) {
        lastMessage.content = 'Sorry, I encountered an error. Please try again.';
      }
      return newMessages;
    });

    const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
    toast.error(errorMessage);
  };

  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setStreamingMessageId(null);
  };

  // Toggle function now handled by Collapsible component automatically

  const handleSettingsClick = () => {
    navigate('/settings');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-background flex flex-col">
      {/* Header */}
      <Header
        currentMode={currentMode}
        onModeChange={handleModeChange}
        onSettingsClick={handleSettingsClick}
        onLogout={handleLogout}
        currentUser={currentUser}
      />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Area */}
        <div className={`flex flex-col transition-all duration-500 ease-in-out ${
          currentMode === 'rag' && !isSourcePanelCollapsed 
            ? 'w-1/2' 
            : 'flex-1'
        }`}>
          {/* Messages */}
          <ScrollArea className="flex-1 p-0">
            <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">
              {messages.length === 0 ? (
                <Card className="text-center py-12 border-0 shadow-lg bg-gradient-to-br from-background to-muted/20 animate-in fade-in-50 duration-700">
                  <div className="w-20 h-20 bg-gradient-to-br from-primary to-primary/80 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg animate-in zoom-in-50 duration-700 delay-150">
                    <Bot className="w-10 h-10 text-primary-foreground" />
                  </div>
                  <h2 className="text-3xl font-bold text-foreground mb-3 animate-in slide-in-from-bottom-4 duration-700 delay-300">
                    Welcome to MedQuery
                  </h2>
                  <p className="text-muted-foreground mb-8 text-lg animate-in slide-in-from-bottom-4 duration-700 delay-450">
                    Your AI assistant for medical knowledge and research
                  </p>
                  <Card className="p-6 max-w-md mx-auto bg-primary/5 border-primary/20 animate-in slide-in-from-bottom-4 duration-700 delay-600">
                    <h3 className="font-semibold text-primary mb-3 text-lg">
                      Current Mode: {currentMode.toUpperCase()}
                    </h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {currentMode === 'ask' && 'Ask general medical questions and get comprehensive answers'}
                      {currentMode === 'rag' && 'Query our medicine database with verified sources and references'}
                      {currentMode === 'agent' && 'Advanced AI agent with tool access for deep research'}
                    </p>
                  </Card>
                </Card>
              ) : (
                <div className="space-y-6 animate-in fade-in-50 duration-500">
                  {messages.map((message, index) => (
                    <div 
                      key={index}
                      className="animate-in slide-in-from-bottom-4 duration-500"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <MessageBubble
                        message={message}
                        isStreaming={isStreaming && index === messages.length - 1}
                      />
                    </div>
                  ))}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <ChatInput
              onSendMessage={handleSendMessage}
              disabled={isStreaming}
              mode={currentMode}
              isStreaming={isStreaming}
              onStop={handleStopStreaming}
            />
          </div>
        </div>

        {/* Source Panel (only in RAG mode) */}
        {currentMode === 'rag' && (
          <Collapsible
            open={!isSourcePanelCollapsed}
            onOpenChange={(open) => setIsSourcePanelCollapsed(!open)}
            className={`relative transition-all duration-500 ease-in-out ${
              isSourcePanelCollapsed ? 'w-12' : 'w-1/2'
            } border-l bg-card/50 backdrop-blur supports-[backdrop-filter]:bg-card/30 flex flex-col animate-in slide-in-from-right duration-500`}
          >
            {/* Toggle Button - Left side handle */}
            <CollapsibleTrigger asChild>
              <Button 
                variant="ghost" 
                size="sm"
                className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 w-8 h-16 rounded-l-lg border border-r-0 bg-background/95 hover:bg-muted/80 transition-all duration-300 group shadow-md backdrop-blur"
                title={isSourcePanelCollapsed ? 'Expand sources' : 'Collapse sources'}
              >
                <div className="flex items-center justify-center">
                  {isSourcePanelCollapsed ? (
                    <ChevronLeft className="h-4 w-4 transition-transform duration-300 group-hover:scale-110" />
                  ) : (
                    <ChevronRight className="h-4 w-4 transition-transform duration-300 group-hover:scale-110" />
                  )}
                </div>
              </Button>
            </CollapsibleTrigger>
            
            {/* Source Panel Content */}
            <CollapsibleContent className="flex-1 overflow-hidden animate-in slide-in-from-right duration-300">
              <SourcePanel
                sources={sources}
                isLoading={isStreaming && sources.length === 0}
                query={currentQuery}
              />
            </CollapsibleContent>
          </Collapsible>
        )}
      </div>
    </div>
  );
};

export default ChatPage;
