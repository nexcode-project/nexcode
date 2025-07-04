import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Settings, Key } from 'lucide-react';
import { chatAPI, Message, ChatMessage, ChatCompletionRequest } from '@/lib/api';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [useOpenAI, setUseOpenAI] = useState(false);
  const [openaiApiKey, setOpenaiApiKey] = useState('');
  const [modelName, setModelName] = useState('gpt-3.5-turbo');
  const [temperature, setTemperature] = useState(0.7);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      let assistantMessage: Message;

      if (useOpenAI) {
        // 使用标准 OpenAI Chat Completion 接口（需要用户提供 API Key）
        if (!openaiApiKey.trim()) {
          toast.error('请先设置 OpenAI API Key');
          setIsLoading(false);
          return;
        }

        // 转换消息格式为 OpenAI 格式
        const chatMessages: ChatMessage[] = [
          { role: 'system', content: '你是一个专业的AI编程助手，能够帮助用户解决编程问题、分析代码、生成代码等。请用中文回复。' },
          ...messages.slice(-10).map(msg => ({
            role: msg.role as 'user' | 'assistant',
            content: msg.content
          })),
          { role: 'user', content: userMessage.content }
        ];

        const request: ChatCompletionRequest = {
          model: modelName,
          messages: chatMessages,
          temperature: temperature,
          max_tokens: 1500,
        };

        const response = await chatAPI.chatCompletion(request, openaiApiKey);
        
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.choices[0].message.content,
          timestamp: new Date(),
        };
      } else {
        // 内置模式也使用标准 chat/completions 接口（使用服务器配置的 API Key）
        const chatMessages: ChatMessage[] = [
          { role: 'system', content: '你是一个专业的AI编程助手，能够帮助用户解决编程问题、分析代码、生成代码等。请用中文回复。' },
          ...messages.slice(-10).map(msg => ({
            role: msg.role as 'user' | 'assistant',
            content: msg.content
          })),
          { role: 'user', content: userMessage.content }
        ];

        const request: ChatCompletionRequest = {
          model: 'codedrive-chat', // 内置模式使用默认模型
          messages: chatMessages,
          temperature: 0.7,
          max_tokens: 1500,
        };

        // 不传递 API Key，使用服务器配置
        const response = await chatAPI.chatCompletion(request);
        
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.choices[0].message.content,
          timestamp: new Date(),
        };
      }

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Failed to send message:', error);
      
      // 处理服务器配置问题
      if (error.response?.data?.choices?.[0]?.message?.content?.includes('OPENAI_API_KEY')) {
        toast.error('服务器未配置 OpenAI API Key，请联系管理员或切换到用户 API Key 模式');
      } else if (error.response?.data?.choices?.[0]?.message?.content?.includes('Error calling LLM API')) {
        toast.error('AI 服务暂时不可用，请稍后重试或切换到用户 API Key 模式');
      } else {
        const errorMsg = error.response?.data?.detail || error.message || '发送消息失败';
        toast.error(errorMsg);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-t-xl border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">AI 智能助手</h2>
              <p className="text-sm text-gray-500">
                {useOpenAI ? `OpenAI ${modelName} (用户 API Key)` : '标准 Chat Completion (服务器配置)'} - 我可以帮助您解决编程问题
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 p-4 bg-gray-50 rounded-lg border"
          >
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="useOpenAI"
                  checked={useOpenAI}
                  onChange={(e) => setUseOpenAI(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <label htmlFor="useOpenAI" className="text-sm font-medium text-gray-700">
                  使用用户 API Key（而非服务器配置）
                </label>
              </div>

              {useOpenAI && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <Key className="w-4 h-4 inline mr-1" />
                      OpenAI API Key
                    </label>
                    <input
                      type="password"
                      value={openaiApiKey}
                      onChange={(e) => setOpenaiApiKey(e.target.value)}
                      placeholder="sk-..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">模型</label>
                      <select
                        value={modelName}
                        onChange={(e) => setModelName(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      >
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        <option value="gpt-4">GPT-4</option>
                        <option value="gpt-4-turbo-preview">GPT-4 Turbo</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        温度 ({temperature})
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={temperature}
                        onChange={(e) => setTemperature(parseFloat(e.target.value))}
                        className="w-full"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 bg-white border-l border-r border-gray-200 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Bot className="w-12 h-12 mb-4 text-gray-300" />
            <p className="text-lg font-medium mb-2">开始对话</p>
            <p className="text-sm text-center">
              您可以询问编程问题、请求代码审查、生成提交消息等
              <br />
              {useOpenAI ? '当前使用用户 API Key' : '当前使用服务器配置'}
            </p>
          </div>
        ) : (
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`flex space-x-3 max-w-3xl ${
                    message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {message.role === 'user' ? (
                      <User className="w-4 h-4" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                  </div>
                  <div
                    className={`px-4 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    <p
                      className={`text-xs mt-1 ${
                        message.role === 'user' ? 'text-primary-200' : 'text-gray-500'
                      }`}
                    >
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
        
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div className="flex space-x-3 max-w-3xl">
              <div className="w-8 h-8 bg-gray-100 text-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="px-4 py-2 rounded-lg bg-gray-100">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-gray-600">AI 正在思考...</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white rounded-b-xl border border-gray-200 p-4">
        <div className="flex space-x-3">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={useOpenAI ? "与 OpenAI 对话..." : "输入您的问题..."}
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
            rows={1}
            style={{ minHeight: '40px', maxHeight: '120px' }}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading || (useOpenAI && !openaiApiKey.trim())}
            className="btn-primary flex items-center space-x-2 px-4 py-2"
          >
            <Send className="w-4 h-4" />
            <span>发送</span>
          </button>
        </div>
      </div>
    </div>
  );
} 