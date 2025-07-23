import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader, Minimize2, Maximize2, X, Lightbulb, Edit, CheckSquare } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AIAssistantProps {
  onInsertText?: (text: string) => void;
  onReplaceSelection?: (text: string) => void;
  selectedText?: string;
}

export function AIAssistant({ onInsertText, onReplaceSelection, selectedText }: AIAssistantProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '你好！我是你的AI写作助手。我可以帮助你：\n\n• 生成内容和想法\n• 改进和润色文本\n• 回答问题\n• 提供写作建议\n\n你需要什么帮助？',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // 构建请求体
      const requestBody = {
        messages: [
          { role: 'system', content: '你是一个专业的写作助手，能够帮助用户创作、改进和优化各种文档内容。' },
          ...messages.map(msg => ({ role: msg.role, content: msg.content })),
          { role: 'user', content: input }
        ],
        max_tokens: 1000,
        temperature: 0.7
      };

      const token = localStorage.getItem('session_token');
      const response = await fetch('http://localhost:8000/v1/openai/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error('请求失败');
      }

      const data = await response.json();
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.choices[0].message.content,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('AI请求失败:', error);
      toast.error('AI助手暂时不可用，请稍后再试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickActions = [
    {
      icon: Lightbulb,
      label: '生成想法',
      prompt: '帮我生成一些关于这个主题的创意想法和内容大纲'
    },
    {
      icon: Edit,
      label: '改进文本',
      prompt: selectedText ? `请帮我改进以下文本：\n\n${selectedText}` : '请选择一些文本，我来帮你改进'
    },
    {
      icon: CheckSquare,
      label: '总结要点',
      prompt: '请帮我总结一下要点，并以清晰的列表形式呈现'
    }
  ];

  const handleQuickAction = (prompt: string) => {
    setInput(prompt);
  };

  const handleInsertResponse = (content: string) => {
    if (onInsertText) {
      onInsertText(content);
      toast.success('内容已插入到文档中');
    }
  };

  const handleReplaceResponse = (content: string) => {
    if (onReplaceSelection && selectedText) {
      onReplaceSelection(content);
      toast.success('选中文本已替换');
    } else {
      toast.error('请先选择要替换的文本');
    }
  };

  if (!isOpen) return null;

  return (
    <div className={`fixed right-4 top-4 bottom-4 w-96 bg-white border border-gray-200 rounded-lg shadow-lg flex flex-col ${isMinimized ? 'h-16' : 'h-auto'} transition-all duration-300 z-50`}>
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-t-lg">
        <div className="flex items-center space-x-2">
          <Bot className="h-5 w-5" />
          <h3 className="font-semibold">AI 写作助手</h3>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 hover:bg-white/20 rounded transition-colors"
          >
            {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-white/20 rounded transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* 消息列表 */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-96">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {message.role === 'assistant' && <Bot className="h-4 w-4 mt-1 flex-shrink-0" />}
                    {message.role === 'user' && <User className="h-4 w-4 mt-1 flex-shrink-0" />}
                    <div className="flex-1">
                      <pre className="whitespace-pre-wrap text-sm font-sans">
                        {message.content}
                      </pre>
                      {message.role === 'assistant' && (
                        <div className="flex space-x-2 mt-2">
                          <button
                            onClick={() => handleInsertResponse(message.content)}
                            className="text-xs bg-white/20 hover:bg-white/30 px-2 py-1 rounded transition-colors"
                          >
                            插入
                          </button>
                          {selectedText && (
                            <button
                              onClick={() => handleReplaceResponse(message.content)}
                              className="text-xs bg-white/20 hover:bg-white/30 px-2 py-1 rounded transition-colors"
                            >
                              替换
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-900 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <Bot className="h-4 w-4" />
                    <Loader className="h-4 w-4 animate-spin" />
                    <span className="text-sm">正在思考...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* 快捷操作 */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex flex-wrap gap-2 mb-3">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickAction(action.prompt)}
                  className="flex items-center space-x-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  disabled={isLoading}
                >
                  <action.icon className="h-3 w-3" />
                  <span>{action.label}</span>
                </button>
              ))}
            </div>

            {/* 输入框 */}
            <div className="flex space-x-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入你的问题或需求..."
                className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={2}
                disabled={isLoading}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="px-3 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white rounded-lg transition-colors"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
} 