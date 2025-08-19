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

const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [currentMode, setCurrentMode] = useState<ChatMode>('ask');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  
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
    <div className="min-h-screen bg-gray-50 flex flex-col">
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
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <div className="max-w-4xl mx-auto px-6 py-6">
              {messages.length === 0 ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-gradient-to-br from-medical-500 to-primary-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <span className="text-white font-bold text-2xl">M</span>
                  </div>
                  <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                    Welcome to MedQuery
                  </h2>
                  <p className="text-gray-600 mb-6">
                    Your AI assistant for medical knowledge and research
                  </p>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto">
                    <h3 className="font-medium text-blue-900 mb-2">Current Mode: {currentMode.toUpperCase()}</h3>
                    <p className="text-sm text-blue-700">
                      {currentMode === 'ask' && 'Ask general medical questions'}
                      {currentMode === 'rag' && 'Query medicine database with sources'}
                      {currentMode === 'agent' && 'AI agent with tool access for research'}
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((message, index) => (
                    <MessageBubble
                      key={index}
                      message={message}
                      isStreaming={isStreaming && index === messages.length - 1}
                    />
                  ))}
                </>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input */}
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={isStreaming}
            mode={currentMode}
            isStreaming={isStreaming}
            onStop={handleStopStreaming}
          />
        </div>

        {/* Source Panel (only in RAG mode) */}
        {currentMode === 'rag' && (
          <SourcePanel
            sources={sources}
            isLoading={isStreaming && sources.length === 0}
            query={currentQuery}
          />
        )}
      </div>
    </div>
  );
};

export default ChatPage;
