import { useEffect, useRef, useState, useCallback } from 'react';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { MarkdownShortcutPlugin } from '@lexical/react/LexicalMarkdownShortcutPlugin';
import { TRANSFORMERS } from '@lexical/markdown';
import { $getRoot, EditorState, $createParagraphNode, $createTextNode, $getSelection, $isRangeSelection, FORMAT_TEXT_COMMAND, SELECTION_CHANGE_COMMAND } from 'lexical';
import { $createListItemNode } from '@lexical/list';
import { $getSelectionStyleValueForProperty, $patchStyleText, $setBlocksType } from '@lexical/selection';
import { $createHeadingNode, $createQuoteNode } from '@lexical/rich-text';
import { Bold, Italic, Underline, Strikethrough, Code, Quote, Type, Hash, X, List, ChevronRight, ChevronDown, ArrowLeft, Share, User, Settings, LogOut } from 'lucide-react';
import { KEY_ENTER_COMMAND, KEY_BACKSPACE_COMMAND, COMMAND_PRIORITY_LOW } from 'lexical';
import { HeadingNode, QuoteNode } from '@lexical/rich-text';
import { ListItemNode, ListNode } from '@lexical/list';
import { CodeNode, CodeHighlightNode } from '@lexical/code';
import { LinkNode, AutoLinkNode } from '@lexical/link';
import { Eye, EyeOff, Save, Wifi, WifiOff, Users, RefreshCw, Clock, History, FileText, Send, Bot, Sparkles } from 'lucide-react';
import { toast } from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { $generateNodesFromDOM } from '@lexical/html';
import { $generateHtmlFromNodes } from '@lexical/html';

import { ShareDBClient, DocumentState } from '@/services/sharedb';
import { apiService } from '@/services/api';
// 假设导入 authStore，如果项目有
import { useAuthStore } from '@/store/authStore';  // 如果没有，忽略这行
import Link from 'next/link';

// 编辑器节点配置
const editorNodes = [
  HeadingNode,
  QuoteNode,
  ListNode,
  ListItemNode,
  CodeNode,
  CodeHighlightNode,
  LinkNode,
  AutoLinkNode
];

// 编辑器主题配置
const theme = {
  ltr: 'ltr',
  rtl: 'rtl',
  placeholder: 'editor-placeholder',
  paragraph: 'editor-paragraph',
  quote: 'editor-quote',
  heading: {
    h1: 'editor-heading-h1',
    h2: 'editor-heading-h2',
    h3: 'editor-heading-h3',
    h4: 'editor-heading-h4',
    h5: 'editor-heading-h5',
    h6: 'editor-heading-h6',
  },
  list: {
    nested: {
      listitem: 'editor-nested-listitem',
    },
    ol: 'editor-list-ol',
    ul: 'editor-list-ul',
    listitem: 'editor-listitem',
  },
  image: 'editor-image',
  link: 'editor-link',
  text: {
    bold: 'editor-text-bold',
    italic: 'editor-text-italic',
    overflowed: 'editor-text-overflowed',
    hashtag: 'editor-text-hashtag',
    underline: 'editor-text-underline',
    strikethrough: 'editor-text-strikethrough',
    underlineStrikethrough: 'editor-text-underlineStrikethrough',
    code: 'editor-text-code',
  },
  code: 'editor-code',
  codeHighlight: {
    atrule: 'editor-tokenAttr',
    attr: 'editor-tokenAttr',
    boolean: 'editor-tokenProperty',
    builtin: 'editor-tokenSelector',
    cdata: 'editor-tokenComment',
    char: 'editor-tokenSelector',
    class: 'editor-tokenFunction',
    'class-name': 'editor-tokenFunction',
    comment: 'editor-tokenComment',
    constant: 'editor-tokenProperty',
    deleted: 'editor-tokenProperty',
    doctype: 'editor-tokenComment',
    entity: 'editor-tokenOperator',
    function: 'editor-tokenFunction',
    important: 'editor-tokenVariable',
    inserted: 'editor-tokenSelector',
    keyword: 'editor-tokenAttr',
    namespace: 'editor-tokenVariable',
    number: 'editor-tokenProperty',
    operator: 'editor-tokenOperator',
    prolog: 'editor-tokenComment',
    property: 'editor-tokenProperty',
    punctuation: 'editor-tokenPunctuation',
    regex: 'editor-tokenVariable',
    selector: 'editor-tokenSelector',
    string: 'editor-tokenSelector',
    symbol: 'editor-tokenProperty',
    tag: 'editor-tokenProperty',
    url: 'editor-tokenOperator',
    variable: 'editor-tokenVariable',
  },
};

// 错误边界组件
function LexicalErrorBoundary({ onError }: { onError: (error: Error) => void }) {
  return null;
}

// 从Lexical状态中提取文本内容的辅助函数
function extractTextFromLexicalState(lexicalState: any): string {
  try {
    if (!lexicalState || !lexicalState.root || !lexicalState.root.children) {
      return '';
    }
    
    let text = '';
    
    const extractTextFromNode = (node: any): void => {
      if (node.type === 'text') {
        text += node.text || '';
      } else if (node.children && Array.isArray(node.children)) {
        node.children.forEach((child: any) => {
          extractTextFromNode(child);
        });
        // 在段落和其他块级元素后添加换行
        if (node.type === 'paragraph' || node.type === 'heading') {
          text += '\n';
        }
      }
    };
    
    lexicalState.root.children.forEach((child: any) => {
      extractTextFromNode(child);
    });
    
    return text.trim();
  } catch (error) {
    console.error('Failed to extract text from Lexical state:', error);
    return '';
  }
}

// 统一的智能同步插件 - 替换所有原有的同步插件
function IntelligentSyncPlugin({
  documentId,
  content,
  documentState,
  setDocumentState,
  updateEditorContent,
  onContentChange,
  onCollaborativeUpdate,
  sharedbClient,
  lastUserInputTimeRef,
  setHasCollaborativeUpdates
}: {
  documentId: number;
  content: string;
  documentState: DocumentState | null;
  setDocumentState: (state: DocumentState | null) => void;
  updateEditorContent: (content: string) => void;
  onContentChange?: (synced: boolean) => void;
  onCollaborativeUpdate?: (hasUpdates: boolean) => void;
  sharedbClient: ShareDBClient;
  lastUserInputTimeRef: React.MutableRefObject<number>;
  setHasCollaborativeUpdates: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const [editor] = useLexicalComposerContext();
  const syncTimer = useRef<NodeJS.Timeout>();
  const pollTimer = useRef<NodeJS.Timeout>();
  const lastSyncedContent = useRef<string>('');
  const syncInProgress = useRef<boolean>(false);

  // 获取当前编辑器内容 - 使用JSON序列化保持完整格式
  const getCurrentEditorContent = useCallback(() => {
    if (!editor) return content;
    
    let editorContent = '';
    editor.getEditorState().read(() => {
      try {
        // 使用JSON序列化获取完整的编辑器状态
        const editorStateJSON = editor.getEditorState().toJSON();
        editorContent = JSON.stringify(editorStateJSON);
      } catch (error) {
        console.error('Failed to serialize editor state:', error);
        // 降级为纯文本
        const root = $getRoot();
        editorContent = root.getTextContent();
      }
    });
    
    return editorContent || content;
  }, [editor, content]);

  // 执行同步
  const performSync = useCallback(async () => {
    if (syncInProgress.current) return;
    
    const currentContent = getCurrentEditorContent();
    if (!currentContent || currentContent === lastSyncedContent.current) return;
    
    syncInProgress.current = true;
    
    try {
      console.log('Syncing Lexical content:', { length: currentContent.length });
      const result = await sharedbClient.syncDocument(currentContent);

      if (result.success) {
        if (documentState) {
          setDocumentState({
            ...documentState,
            content: result.content,
            version: result.version
          });
        }
        
        lastSyncedContent.current = result.content;
        
        // 如果服务器内容不同，说明有协作更新
        if (result.content !== currentContent) {
          console.log('Collaborative changes detected, updating editor');
          updateEditorContent(result.content);
          onCollaborativeUpdate?.(true);
        }
        
        onContentChange?.(true);
        console.log('Lexical content synced successfully');
      } else {
        console.error('Sync failed:', result.error);
        onContentChange?.(false);
      }
    } catch (error) {
      console.error('Sync error:', error);
      onContentChange?.(false);
    } finally {
      syncInProgress.current = false;
    }
  }, [documentId, documentState, setDocumentState, updateEditorContent, onContentChange, onCollaborativeUpdate, getCurrentEditorContent, sharedbClient]);

  // 轮询检查更新 - 优化版本比较逻辑
  const pollForUpdates = useCallback(async () => {
    if (syncInProgress.current) return;
    
    try {
      const serverState = await sharedbClient.getDocument();
      
      // 只有版本真正更新时才处理
      if (serverState.version > (documentState?.version || 0)) {
        console.log('New version detected:', serverState.version);
        
        setDocumentState({
          doc_id: serverState.doc_id,
          content: serverState.content,
          version: serverState.version,
          created_at: serverState.created_at,
          updated_at: serverState.updated_at
        });
        
        // 检查用户是否正在编辑
        const now = Date.now();
        const timeSinceLastInput = now - lastUserInputTimeRef.current;
        const userIsEditing = timeSinceLastInput < 5000;
        
        if (serverState.content !== lastSyncedContent.current) {
          if (!userIsEditing) {
            // 用户没有在编辑，直接更新
            updateEditorContent(serverState.content);
            lastSyncedContent.current = serverState.content;
            console.log('Applied collaborative Lexical changes');
          } else {
            // 用户正在编辑，标记有协作更新但不立即应用
            console.log('Deferred collaborative update due to user editing');
            setHasCollaborativeUpdates(true);
          }
          onCollaborativeUpdate?.(true);
        }
        
        onContentChange?.(true);
      }
    } catch (error) {
      console.error('Poll failed:', error);
      onContentChange?.(false);
    }
  }, [documentState, setDocumentState, updateEditorContent, onContentChange, onCollaborativeUpdate, sharedbClient, setHasCollaborativeUpdates]);

  // 使用ref确保轮询函数总是访问最新状态
  const pollForUpdatesRef = useRef(pollForUpdates);
  pollForUpdatesRef.current = pollForUpdates;

  // 启动轮询 - 固定每10秒一次获取其他用户变更
  useEffect(() => {
    console.log('Starting document polling every 10 seconds - fixed interval');
    
    // 立即执行一次
    pollForUpdatesRef.current();
    
    // 设置固定间隔轮询，不受任何其他操作影响
    pollTimer.current = setInterval(() => {
      console.log('Polling for remote changes...');
      pollForUpdatesRef.current();
    }, 10000); // 固定10秒

    return () => {
      if (pollTimer.current) {
        clearInterval(pollTimer.current);
      }
    };
  }, []); // 空依赖数组，确保只初始化一次，不会被重置

  // 用户编辑检测 - 使用固定间隔避免频繁重置
  useEffect(() => {
    // 启动一个固定的同步检查定时器，而不是每次内容变化都重置
    const startSyncCheck = () => {
      syncTimer.current = setTimeout(() => {
        const currentContent = getCurrentEditorContent();
        
        // 检查是否需要同步
        if (currentContent !== lastSyncedContent.current) {
          const contentDiff = Math.abs(currentContent.length - lastSyncedContent.current.length);
          const timeSinceLastInput = Date.now() - lastUserInputTimeRef.current;
          
          // 只在用户停止编辑2秒后且内容有变化时同步
          if (timeSinceLastInput > 2000 && contentDiff > 0) {
            console.log('Content changed and user stopped editing, syncing now');
            performSync().finally(() => {
              // 同步完成后，重新启动检查定时器
              startSyncCheck();
            });
          } else {
            // 继续检查
            startSyncCheck();
          }
        } else {
          // 没有变化，继续检查
          startSyncCheck();
        }
      }, 3000); // 每3秒检查一次
    };

    // 启动检查
    startSyncCheck();

    return () => {
      if (syncTimer.current) {
        clearTimeout(syncTimer.current);
      }
    };
  }, [getCurrentEditorContent, performSync]);

  // 初始同步
  useEffect(() => {
    const initTimer = setTimeout(() => {
      const initialContent = getCurrentEditorContent();
      if (initialContent && initialContent !== lastSyncedContent.current) {
        console.log('Initial sync');
        performSync();
      }
    }, 1000);

    return () => clearTimeout(initTimer);
  }, [getCurrentEditorContent, performSync]);

  return null;
}

// 使用統一的 API 類型
import type { DocumentVersion } from '@/types/api';

interface CollaborativeLexicalEditorProps {
  documentId: number;
  initialContent?: string;
  initialDocumentState?: DocumentState; // 新增：传入初始文档状态
  onContentChange?: (content: string) => void;
  onSave?: (content: string) => Promise<void>;
  onLexicalContentChange?: (lexicalContent: string) => void; // 新增：Lexical格式内容变化回调
  // 新增：标题栏功能
  documentTitle?: string;
  onTitleChange?: (e: React.FormEvent<HTMLHeadingElement>) => void;
  onTitleBlur?: () => void;
  onTitleKeyDown?: (e: React.KeyboardEvent<HTMLHeadingElement>) => void;
  onBack?: () => void;
  onShare?: () => void;
  saving?: boolean;
  currentLexicalContent?: string;
  user?: any;
  onLogout?: () => void;
  showUserMenu?: boolean;
  setShowUserMenu?: (show: boolean) => void;
  userMenuRef?: React.RefObject<HTMLDivElement>;
}

// 新增AI助手组件
function AIAssistant({
  onInsertContent,
  documentContent
}: {
  onInsertContent: (content: string) => void;
  documentContent: string;
}) {
  const [messages, setMessages] = useState<Array<{role: 'user' | 'assistant', content: string}>>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 加载AI模板
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        const templateData = await apiService.getAITemplates();
        setTemplates(templateData);
      } catch (error) {
        console.error('Failed to load AI templates:', error);
      }
    };
    loadTemplates();
  }, []);

  // 发送消息到AI
  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    // 添加用户消息 - 修复类型错误
    const newMessages = [...messages, { role: 'user' as const, content: userMessage }];
    setMessages(newMessages);

    try {
      // 使用apiService调用AI API
      const response = await apiService.aiAssist({
        message: userMessage,
        documentContent: documentContent,
        conversationHistory: newMessages,
        templateId: selectedTemplate?.id
      });
      
      // 添加AI回复 - 修复类型错误
      setMessages([...newMessages, { role: 'assistant' as const, content: response.response }]);
    } catch (error) {
      console.error('AI请求失败:', error);
      setMessages([...newMessages, { 
        role: 'assistant' as const, 
        content: '抱歉，AI服务暂时不可用，请稍后再试。' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // 插入AI回复到文档
  const insertAIResponse = (content: string) => {
    onInsertContent(content);
  };

  // 处理回车键发送
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // 预设的AI提示
  const presetPrompts = [
    '帮我优化这段文档的结构',
    '检查语法和拼写错误',
    '添加更多细节和例子',
    '总结文档的主要观点',
    '转换为更正式的语气'
  ];

  // 使用模板的函数
  const useTemplate = (template: any) => {
    setSelectedTemplate(template);
    setShowTemplateModal(false);
    // 如果模板有user_prompt，将其设置为输入值
    if (template.user_prompt) {
      setInputValue(template.user_prompt.replace('{document}', documentContent || ''));
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 border-l border-gray-200 min-h-0">
      {/* AI助手头部 */}
      <div className="flex-shrink-0 p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bot className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">AI助手</h3>
            <Sparkles className="h-4 w-4 text-yellow-500" />
          </div>
          <button
            onClick={() => setShowTemplateModal(true)}
            className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
          >
            选择模板
          </button>
        </div>
        <div className="flex items-center justify-between mt-1">
          <p className="text-sm text-gray-600">智能写作助手，帮助您提升文档质量</p>
          {selectedTemplate && (
            <div className="flex items-center space-x-1 text-xs text-green-600">
              <span>●</span>
              <span>{selectedTemplate.name}</span>
            </div>
          )}
        </div>
      </div>

      {/* 预设提示 */}
      <div className="flex-shrink-0 p-3 border-b border-gray-200 bg-white">
        <p className="text-xs text-gray-500 mb-2">快速提示：</p>
        <div className="flex flex-wrap gap-1">
          {presetPrompts.map((prompt, index) => (
            <button
              key={index}
              onClick={() => setInputValue(prompt)}
              className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100 transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <Bot className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p className="text-sm">开始与AI助手对话，获得写作建议</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] p-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200'
                }`}
              >
                <div className="flex items-start space-x-2">
                  {message.role === 'assistant' && (
                    <Bot className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    {message.role === 'assistant' && (
                      <button
                        onClick={() => insertAIResponse(message.content)}
                        className="mt-2 text-xs text-blue-600 hover:text-blue-800 underline"
                      >
                        插入到文档
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <Bot className="h-4 w-4 text-blue-600" />
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="flex-shrink-0 p-4 border-t border-gray-200 bg-white">
        <div className="flex space-x-2">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="向AI助手提问..."
            className="flex-1 p-2 text-sm border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center space-x-1"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          按 Enter 发送，Shift + Enter 换行
        </p>
      </div>

      {/* 模板选择模态框 */}
      {showTemplateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">选择AI模板</h3>
              <button
                onClick={() => setShowTemplateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-3">
              <button
                onClick={() => {
                  setSelectedTemplate(null);
                  setShowTemplateModal(false);
                }}
                className={`w-full p-3 text-left border rounded-lg transition-colors ${
                  !selectedTemplate ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-medium text-gray-900">通用模式</div>
                <div className="text-sm text-gray-600">无特定模板，自由对话</div>
              </button>

              {templates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => useTemplate(template)}
                  className={`w-full p-3 text-left border rounded-lg transition-colors ${
                    selectedTemplate?.id === template.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium text-gray-900">{template.name}</div>
                  <div className="text-sm text-gray-600 mb-1">{template.description}</div>
                  <div className="text-xs text-blue-600">{template.category}</div>
                </button>
              ))}

              {templates.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <p>暂无可用模板</p>
                  <p className="text-sm mt-1">管理员可在后台添加AI模板</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function CollaborativeLexicalEditor({
  documentId,
  initialContent = '',
  initialDocumentState, // 新增参数
  onContentChange,
  onSave,
  onLexicalContentChange,
  // 新增：标题栏功能
  documentTitle,
  onTitleChange,
  onTitleBlur,
  onTitleKeyDown,
  onBack,
  onShare,
  saving,
  currentLexicalContent,
  user,
  onLogout,
  showUserMenu,
  setShowUserMenu,
  userMenuRef
}: CollaborativeLexicalEditorProps) {
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [content, setContent] = useState(initialContent);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const [isOnline, setIsOnline] = useState(true);
  const [documentState, setDocumentState] = useState<DocumentState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [versionHistory, setVersionHistory] = useState<DocumentVersion[]>([]);
  const [previewVersion, setPreviewVersion] = useState<{version: DocumentVersion, content: string} | null>(null);
  const [isVersionPreviewMode, setIsVersionPreviewMode] = useState(false);
  const [hasCollaborativeUpdates, setHasCollaborativeUpdates] = useState(false); // 协作更新指示
  const [previewContent, setPreviewContent] = useState(''); // 用于预览的可读文本内容
  const [showTOC, setShowTOC] = useState(true); // 显示目录
  const [tocItems, setTocItems] = useState<Array<{id: string, text: string, level: number}>>([]);
  
  // 移除不再需要的状态
  // const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  // const [autoSyncEnabled, setAutoSyncEnabled] = useState(true);
  // const [syncInterval, setSyncInterval] = useState(5000);
  // const [smartVersioningEnabled, setSmartVersioningEnabled] = useState(true);
  
  const sharedbClientRef = useRef<ShareDBClient>();
  const editorRef = useRef<any>();
  const lastUserInputTimeRef = useRef<number>(Date.now()); // 用于跟踪用户输入时间

  // 获取可读文本内容用于预览和显示
  const getReadableContent = useCallback(() => {
    if (!editorRef.current) return '';
    
    let textContent = '';
    editorRef.current.getEditorState().read(() => {
      const root = $getRoot();
      textContent = root.getTextContent();
    });
    
    return textContent;
  }, []);

  // 初始化 ShareDB 客户端并加载文档
  useEffect(() => {
    const client = new ShareDBClient(documentId.toString());
    sharedbClientRef.current = client;

    const loadDocument = async () => {
      try {
        let finalContent = initialContent;
        let docState = initialDocumentState;

        // 如果没有传入初始状态，才从服务器获取
        if (!docState) {
          console.log('Getting document state from ShareDB');
          docState = await client.getDocument();
          finalContent = docState.content || initialContent;
        } else {
          console.log('Using provided initial document state');
          finalContent = docState.content || initialContent;
        }
        
        setDocumentState(docState);
        setContent(finalContent);
        
        // 通知父组件初始Lexical内容，以便正确设置save按钮状态
        // Always call this to ensure save button state is properly initialized
        if (onLexicalContentChange) {
          onLexicalContentChange(finalContent || '');
        }
        
        // 设置初始预览内容
        try {
          const lexicalState = JSON.parse(finalContent);
          if (lexicalState && typeof lexicalState === 'object' && lexicalState.root) {
            // 如果是JSON格式，尝试从Lexical状态中提取文本内容
            try {
              const textContent = extractTextFromLexicalState(lexicalState);
              setPreviewContent(textContent);
              console.log('Initial preview content set from Lexical state:', textContent.length);
            } catch {
              setPreviewContent('正在加载编辑器内容...');
            }
          } else {
            setPreviewContent(finalContent);
            console.log('Initial preview content set as plain text:', finalContent.length);
          }
        } catch {
          // 纯文本内容
          setPreviewContent(finalContent);
          console.log('Initial preview content set as plain text (fallback):', finalContent.length);
        }
        
        setIsLoading(false);
        setLastSyncTime(new Date());
        setIsOnline(true);
        
        console.log('Document loaded successfully:', {
          contentLength: finalContent.length,
          version: docState?.version,
          hasInitialDocumentState: !!initialDocumentState
        });
        
      } catch (error) {
        console.error('Failed to load document:', error);
        toast.error('加載文檔失敗，使用本地版本');
        setContent(initialContent);
        setIsOnline(false);
        setIsLoading(false);
      }
    };

    loadDocument();

    return () => {
      client.destroy();
      // 清理防抖定时器
      if (contentChangeTimeoutRef.current) {
        clearTimeout(contentChangeTimeoutRef.current);
      }
    };
  }, [documentId, initialContent, initialDocumentState]);

  // 编辑器初始配置
  const initialConfig = {
    namespace: 'CollaborativeNexCodeEditor',
    theme,
    nodes: editorNodes,
    onError: (error: Error) => {
      console.error('Lexical Error:', error);
      toast.error('编辑器错误');
    },
    editorState: content ? (() => {
      try {
        // 尝试解析JSON格式的Lexical状态
        const lexicalState = JSON.parse(content);
        if (lexicalState && typeof lexicalState === 'object' && lexicalState.root) {
          // 如果是有效的Lexical状态，直接使用
          return JSON.stringify(lexicalState);
        }
      } catch {
        // 不是JSON格式，返回undefined让后续处理
      }
      return undefined; // 使用undefined，让updateEditorContent处理
    })() : undefined,
  };

  // 更新编辑器内容（同步时使用）- 支持Lexical JSON格式
  const updateEditorContent = useCallback((newContent: string) => {
    if (!editorRef.current) return;
    
    // 检查用户是否正在活跃编辑 - 简化逻辑
    const now = Date.now();
    const timeSinceLastInput = now - lastUserInputTimeRef.current;
    const isActivelyEditing = timeSinceLastInput < 5000; // 5秒内有输入视为活跃编辑
    
    if (isActivelyEditing) {
      console.log('User is actively editing, skipping collaborative update');
      // 如果用户正在活跃编辑，跳过这次更新，不进行递归调用
      return;
    }
    
    try {
      // 尝试解析为JSON格式的Lexical状态
      let isLexicalJSON = false;
      let lexicalState = null;
      
      try {
        lexicalState = JSON.parse(newContent);
        // 检查是否是有效的Lexical状态格式
        if (lexicalState && typeof lexicalState === 'object' && lexicalState.root) {
          isLexicalJSON = true;
        }
      } catch {
        // 不是JSON格式，作为纯文本处理
        isLexicalJSON = false;
      }
      
      if (isLexicalJSON && lexicalState) {
        console.log('Updating editor with Lexical JSON state');
        // 使用Lexical的状态恢复功能
        try {
          const editorState = editorRef.current.parseEditorState(lexicalState);
          editorRef.current.setEditorState(editorState);
          // 更新本地内容状态
          setContent(newContent);
          // 更新预览内容
          setTimeout(() => {
            const readableText = getReadableContent();
            setPreviewContent(readableText);
          }, 50);
          return; // 成功设置状态，直接返回
        } catch (error) {
          console.error('Failed to parse Lexical state, falling back to text:', error);
          // 降级处理
        }
      }
      
      editorRef.current.update(() => {
        const root = $getRoot();
        
        // 降级处理：作为纯文本内容处理
        const currentContent = root.getTextContent();
        
        // 避免不必要的更新
        if (currentContent === newContent) {
          return;
        }
        
        console.log('Updating editor with plain text content');
        root.clear();
        
        if (newContent.trim()) {
          // 简单地将内容作为段落插入
          const lines = newContent.split('\n');
          lines.forEach((line, index) => {
            const paragraph = $createParagraphNode();
            if (line.trim()) {
              paragraph.append($createTextNode(line));
            }
            root.append(paragraph);
          });
        }
              });
        
        // 更新本地内容状态和预览内容（仅用于降级情况）
        setContent(newContent);
        setTimeout(() => {
          const readableText = getReadableContent();
          setPreviewContent(readableText);
        }, 50);
        
      } catch (error) {
        console.error('Failed to update editor content:', error);
                  // 即使出错也要更新内容状态
          setContent(newContent);
        }
      }, [getReadableContent]);

  // 當內容加載完成時，立即更新編輯器
  useEffect(() => {
    if (!isLoading && content && editorRef.current) {
      console.log('Content loaded, updating editor with initial content:', content.length);
      updateEditorContent(content);
      
      // 延迟更新预览内容（确保编辑器状态已更新）
      setTimeout(() => {
        const readableText = getReadableContent();
        if (readableText) {
          setPreviewContent(readableText);
        }
      }, 100);
    }
  }, [isLoading, content, updateEditorContent, getReadableContent]);

  // 跟踪用户输入时间（用于协作冲突检测）和快捷鍵
  useEffect(() => {
    const handleUserInput = () => {
      lastUserInputTimeRef.current = Date.now();
    };
    
    const handleKeyDown = (event: KeyboardEvent) => {
      // 記錄用戶輸入時間
      handleUserInput();
    

    };
    
    // 监听各种用户输入事件
    const events = ['mousedown', 'input', 'paste'];
    events.forEach(event => {
      document.addEventListener(event, handleUserInput, true);
    });
    
    // 單獨處理鍵盤事件以支持快捷鍵
    document.addEventListener('keydown', handleKeyDown, true);
    
    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleUserInput, true);
      });
      document.removeEventListener('keydown', handleKeyDown, true);
    };
  }, [isPreviewMode]); // 移除 handleManualSave 依賴以避免循環依賴

    // 处理内容变化 - 使用防抖机制减少频繁更新
  const contentChangeTimeoutRef = useRef<NodeJS.Timeout>();
  
  const handleContentChange = useCallback((editorState: EditorState) => {
    // 清除之前的防抖定时器
    if (contentChangeTimeoutRef.current) {
      clearTimeout(contentChangeTimeoutRef.current);
    }
    
    // 立即更新预览内容（纯文本，性能较好）
    editorState.read(() => {
      const root = $getRoot();
      const textContent = root.getTextContent();
      setPreviewContent(textContent);
      onContentChange?.(textContent); // 回调使用可读文本
    });
    
    // 防抖处理JSON序列化（500ms后执行）
    contentChangeTimeoutRef.current = setTimeout(() => {
      try {
        // 使用JSON序列化获取完整的编辑器状态
        const editorStateJSON = editorState.toJSON();
        const serializedContent = JSON.stringify(editorStateJSON, null, 0);
        
        if (serializedContent !== content) {
          setContent(serializedContent);
          setHasUnsavedChanges(serializedContent !== (documentState?.content || initialContent));
          // 调用Lexical内容变化回调
          onLexicalContentChange?.(serializedContent);
        }
      } catch (error) {
        console.error('Failed to handle content change:', error);
        // 降级为纯文本处理
        editorState.read(() => {
          const root = $getRoot();
          const textContent = root.getTextContent();
          
          if (textContent !== content) {
            setContent(textContent);
            setHasUnsavedChanges(textContent !== (documentState?.content || initialContent));
            // 降级情况下也调用Lexical内容变化回调（虽然实际是纯文本）
            onLexicalContentChange?.(textContent);
          }
        });
      }
    }, 500); // 500ms防抖
  }, [content, documentState, initialContent, onContentChange]);



  // 手动同步（强制从服务器获取最新内容）
  const handleSync = useCallback(async () => {
    if (!sharedbClientRef.current) return;
    
    try {
      const docState = await sharedbClientRef.current.getDocument();
      setDocumentState(docState);
      
      if (docState.content !== content) {
        setContent(docState.content);
        updateEditorContent(docState.content);
        toast.success('文档已同步，内容已更新');
      } else {
        toast.success('文档已是最新版本');
      }
      
      setIsOnline(true);
      setLastSyncTime(new Date());
    } catch (error) {
      console.error('Sync failed:', error);
      setIsOnline(false);
      toast.error('同步失败');
    }
  }, [content, updateEditorContent]);

  // 加载版本历史
  const loadVersionHistory = useCallback(async () => {
    try {
      const response = await apiService.getDocumentVersions(documentId, 10);
      setVersionHistory(response.versions || []);
    } catch (error) {
      console.error('Failed to load version history:', error);
      toast.error('加载版本历史失败');
    }
  }, [documentId]);

  // 预览版本
  const handlePreviewVersion = useCallback(async (version: DocumentVersion) => {
    try {
      const data = await apiService.getVersionContent(documentId, version.version_number);
      setPreviewVersion({ version, content: data.content });
      setIsVersionPreviewMode(true);
      // 将预览内容设置到主编辑器
      updateEditorContent(data.content);
    } catch (error) {
      console.error('Failed to preview version:', error);
      toast.error('预览版本失败');
    }
  }, [documentId, updateEditorContent]);

  // 恢复版本
  const handleRestoreVersion = useCallback(async (versionNumber: number) => {
    try {
      const data = await apiService.restoreDocumentVersion(documentId, versionNumber);
      setContent(data.content);
      updateEditorContent(data.content);
      setShowVersionHistory(false);
      setIsVersionPreviewMode(false);
      setPreviewVersion(null);
      toast.success('版本已恢复');
      
      // 同步到ShareDB
      if (sharedbClientRef.current) {
        await sharedbClientRef.current.syncDocument(data.content);
      }
    } catch (error) {
      console.error('Failed to restore version:', error);
      toast.error('恢复版本失败');
    }
  }, [documentId, updateEditorContent]);

  // 取消预览
  const handleCancelPreview = useCallback(() => {
    setIsVersionPreviewMode(false);
    setPreviewVersion(null);
    // 恢复当前内容
    if (content) {
      updateEditorContent(content);
    }
  }, [content, updateEditorContent]);

  // 保存编辑器引用
  const saveEditorRef = useCallback((editor: any) => {
    editorRef.current = editor;
    
    // 编辑器准备好后，立即设置内容（如果有的话）
    if (editor && content && !isLoading) {
      console.log('Editor ready, setting initial content immediately');
      setTimeout(() => {
        updateEditorContent(content);
        // 更新预览内容
        setTimeout(() => {
          const readableText = getReadableContent();
          if (readableText) {
            setPreviewContent(readableText);
            console.log('Preview content updated after editor ready:', readableText.length);
          }
        }, 50);
      }, 100);
    }
  }, [content, isLoading, updateEditorContent, getReadableContent]);

  // 切换版本历史
  const toggleVersionHistory = useCallback(() => {
    if (!showVersionHistory) {
      loadVersionHistory();
    }
    setShowVersionHistory(!showVersionHistory);
    // 如果显示历史记录，则隐藏目录
    if (!showVersionHistory) {
      setShowTOC(false);
    }
  }, [showVersionHistory, loadVersionHistory, setShowTOC]);

  // 更新目录
  const handleTOCUpdate = useCallback((items: Array<{id: string, text: string, level: number}>) => {
    setTocItems(items);
  }, []);

  // 跳转到标题
  const handleTOCItemClick = useCallback((headingKey: string) => {
    if (!editorRef.current) return;
    
    editorRef.current.update(() => {
      const root = $getRoot();
      
      // 直接在根节点的子节点中查找目标节点
      const children = root.getChildren();
      const targetNode = children.find((node: any) => node.getKey() === headingKey);
      if (targetNode) {
        // 创建选择范围并选中标题
        targetNode.selectStart();
        
        // 滚动到目标元素
        setTimeout(() => {
          const element = editorRef.current.getElementByKey(headingKey);
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }, 50);
      }
    });
  }, []);

  // 插入内容到编辑器的函数
  const insertContentToEditor = useCallback((content: string) => {
    if (!editorRef.current) return;

    editorRef.current.update(() => {
      const root = $getRoot();
      const selection = window.getSelection();
      
      if (selection && selection.rangeCount > 0) {
        // 如果有选中文本，替换选中内容
        const range = selection.getRangeAt(0);
        const textNode = $createTextNode(content);
        // 这里需要更复杂的逻辑来处理选中内容的替换
        // 简化处理：在末尾添加内容
        let lastParagraph = root.getLastChild();
        if (lastParagraph && lastParagraph.getType && lastParagraph.getType() === 'paragraph') {
          // 如果最后一个节点是段落，则向其添加文本节点
          (lastParagraph as any).append($createTextNode('\n' + content));
        } else {
          // 否则新建一个段落节点并添加到根节点
          const paragraph = $createParagraphNode();
          paragraph.append($createTextNode(content));
          root.append(paragraph);
        }
        // 在末尾添加内容
        const lastChild = root.getLastChild();
        if (lastChild && lastChild.getType() === 'paragraph') {
          // 如果最后一个节点是段落，则向其添加文本节点
          (lastChild as any).append($createTextNode('\n' + content));
        } else {
          // 否则新建一个段落节点并添加到根节点
          const paragraph = $createParagraphNode();
          paragraph.append($createTextNode(content));
          root.append(paragraph);
        }
      }
    });
  }, []);

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-white">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-5 w-5 animate-spin text-blue-600" />
          <span className="text-gray-600">加载文档中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="lexical-editor h-screen flex flex-col bg-white overflow-hidden">
      {/* 顶部工具栏 */}
      <div className="flex-shrink-0 flex items-center justify-between p-4 border-b border-gray-200 bg-white shadow-sm">
        {/* 左侧：返回按钮和状态信息 */}
        <div className="flex items-center space-x-4">
          {/* 返回按钮 */}
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
          )}
          
          {/* 文档状态 */}
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${hasUnsavedChanges ? 'bg-yellow-500' : 'bg-green-500'}`}></div>
            <span className="text-sm text-gray-600 font-medium">
              {hasUnsavedChanges ? '未保存' : '已保存'}
            </span>
          </div>
          
          {/* 连接状态 */}
          <div className="flex items-center space-x-2">
            {isOnline ? (
              <>
                <Wifi className="h-4 w-4 text-green-500" />
                <span className="text-sm text-green-600">已连接</span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-red-500" />
                <span className="text-sm text-red-600">离线</span>
              </>
            )}
          </div>

          {/* 最后同步时间 */}
          {lastSyncTime && (
            <div className="flex items-center space-x-1 text-sm text-gray-500">
              <Clock className="h-3 w-3" />
              <span>最后同步: {lastSyncTime.toLocaleTimeString()}</span>
            </div>
          )}

          {/* 协作更新指示器 */}
          {hasCollaborativeUpdates && (
            <div className="flex items-center space-x-1 text-sm text-blue-600 animate-pulse">
              <Users className="h-3 w-3" />
              <span>有协作更新</span>
            </div>
          )}
        </div>

        {/* 中间：标题编辑区域 */}
        {documentTitle && onTitleChange && onTitleBlur && onTitleKeyDown && (
          <div className="flex-1 flex justify-center">
            <div className="flex items-center">
              <h1 
                contentEditable
                suppressContentEditableWarning
                onInput={onTitleChange}
                onBlur={onTitleBlur}
                onKeyDown={onTitleKeyDown}
                className="text-lg font-semibold text-gray-900 cursor-text hover:text-blue-600 transition-colors focus:outline-none whitespace-nowrap overflow-hidden text-ellipsis max-w-md text-center"
                title="点击编辑标题（建议简明扼要，回车保存）"
              >
                {documentTitle || "请输入标题"}
              </h1>
            </div>
          </div>
        )}

        {/* 右侧：操作按钮 */}
        <div className="flex items-center space-x-2">
          {/* 分享按钮 */}
          {onShare && (
            <button
              onClick={onShare}
              className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
            >
              <Share className="h-4 w-4" />
              <span>分享</span>
            </button>
          )}
          
          {/* 保存按钮 */}
          {onSave && (
            <button
              onClick={() => onSave(currentLexicalContent || '')}
              disabled={saving || (!currentLexicalContent && !initialContent)}
              className="flex items-center space-x-2 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white px-4 py-2 rounded-lg"
            >
              <Save className="h-4 w-4" />
              <span>{saving ? '保存中...' : '保存为新版本'}</span>
            </button>
          )}
          
          {/* 目录按钮 */}
          <button
            onClick={() => {
              setShowTOC(!showTOC);
              // 如果显示目录，则隐藏历史记录
              if (!showTOC) {
                setShowVersionHistory(false);
              }
            }}
            className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              showTOC 
                ? 'text-blue-700 bg-blue-100 hover:bg-blue-200' 
                : 'text-gray-700 bg-gray-100 hover:bg-gray-200'
            }`}
            title="目录"
          >
            <List className="h-4 w-4" />
            <span>目录</span>
          </button>
          
          {/* 历史按钮 */}
          <button
            onClick={toggleVersionHistory}
            className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              showVersionHistory 
                ? 'text-blue-700 bg-blue-100 hover:bg-blue-200' 
                : 'text-gray-700 bg-gray-100 hover:bg-gray-200'
            }`}
            title="版本历史"
          >
            <History className="h-4 w-4" />
            <span>历史</span>
          </button>

          {/* 用户菜单 */}
          {user && onLogout && showUserMenu !== undefined && setShowUserMenu && userMenuRef && (
            <div className="relative ml-4" ref={userMenuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-blue-600" />
                </div>
                <span className="text-gray-700 font-medium">
                  {user?.username || user?.full_name}
                </span>
                <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${
                  showUserMenu ? 'rotate-180' : ''
                }`} />
              </button>

              {/* 用户下拉菜单 */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                  {/* 用户信息 */}
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">
                      {user?.full_name || user?.username}
                    </p>
                    <p className="text-sm text-gray-500">
                      {user?.email}
                    </p>
                  </div>

                  {/* 菜单项 */}
                  <div className="py-1">
                    <Link
                      href="/settings"
                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <Settings className="w-4 h-4 mr-3" />
                      设置
                    </Link>
                    <button
                      onClick={onLogout}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <LogOut className="w-4 h-4 mr-3" />
                      退出登录
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 主要内容区域 */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* 目录侧边栏 */}
        {showTOC && (
          <div className="w-80 border-r border-gray-200 bg-gray-50 flex flex-col">
            <div className="flex-1 overflow-auto">
              <TableOfContents 
                items={tocItems} 
                onItemClick={handleTOCItemClick}
              />
            </div>
          </div>
        )}

        {/* 版本历史侧边栏 */}
        {showVersionHistory && (
          <div className="w-80 border-r border-gray-200 bg-gray-50 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">历史记录</h3>
            </div>
            <div className="flex-1 overflow-auto">
              {versionHistory.length > 0 ? (
                <div className="p-2">
                  {(() => {
                    // 按日期分组版本历史
                    const groupedVersions = versionHistory.reduce((groups, version) => {
                      const date = new Date(version.created_at);
                      const today = new Date();
                      const yesterday = new Date(today);
                      yesterday.setDate(yesterday.getDate() - 1);
                      
                      let groupKey = '';
                      if (date.toDateString() === today.toDateString()) {
                        groupKey = '今天';
                      } else if (date.toDateString() === yesterday.toDateString()) {
                        groupKey = '昨天';
                      } else {
                        // 获取星期几
                        const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
                        groupKey = weekdays[date.getDay()];
                      }
                      
                      if (!groups[groupKey]) {
                        groups[groupKey] = [];
                      }
                      groups[groupKey].push(version);
                      return groups;
                    }, {} as Record<string, typeof versionHistory>);

                    return Object.entries(groupedVersions)
                      .sort(([, versionsA], [, versionsB]) => {
                        // 按分组中最新版本的时间倒序排列
                        const latestA = Math.max(...versionsA.map(v => new Date(v.created_at).getTime()));
                        const latestB = Math.max(...versionsB.map(v => new Date(v.created_at).getTime()));
                        return latestB - latestA;
                      })
                      .map(([groupKey, versions]) => (
                      <div key={groupKey} className="mb-4">
                        <div className="px-2 py-1 text-xs font-medium text-gray-500 uppercase tracking-wide">
                          {groupKey}
                        </div>
                        {versions.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).map((version, index) => (
                          <div
                            key={version.id}
                            onClick={() => handlePreviewVersion(version)}
                            className={`p-3 mb-1 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-shadow cursor-pointer hover:bg-gray-50 ${
                              isVersionPreviewMode && previewVersion?.version.id === version.id ? 'bg-blue-50 border-blue-200' : ''
                            }`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm text-gray-900">
                                {new Date(version.created_at).toLocaleDateString('zh-CN', {
                                  month: 'numeric',
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </span>
                              <div className="flex items-center space-x-1">
                                {isVersionPreviewMode && previewVersion?.version.id === version.id ? (
                                  <ChevronDown className="h-3 w-3 text-gray-400" />
                                ) : (
                                  <ChevronRight className="h-3 w-3 text-gray-400" />
                                )}
                              </div>
                            </div>
                            <div className="flex items-center space-x-2 mb-1">
                              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                              <span className="text-sm text-gray-700">
                                {version.changed_by?.username || '未知用户'}
                              </span>
                            </div>
                            {/* 根据截图显示特殊状态文本 */}
                            {index === 0 && groupKey === '昨天' && (
                              <p className="text-sm text-gray-500">最近更新</p>
                            )}
                            {index === 1 && groupKey === '昨天' && (
                              <p className="text-sm text-gray-500">本次修改已保存至本地</p>
                            )}
                          </div>
                        ))}
                      </div>
                    ));
                  })()}
                </div>
              ) : (
                <div className="p-4 text-center text-gray-500">
                  暂无历史记录
                </div>
              )}
            </div>
          </div>
        )}

        {/* 主编辑区域 */}
        <div className="flex-1 flex min-h-0 relative">
          {/* 编辑器区域 */}
          <div className={`${isPreviewMode ? 'w-1/2' : 'flex-1'} transition-all duration-300 flex flex-col min-h-0`}>
            <LexicalComposer initialConfig={initialConfig}>
              <div className="editor-container flex-1 flex flex-col min-h-0">
                <FormatToolbar 
                  isVersionPreviewMode={isVersionPreviewMode}
                  previewVersion={previewVersion}
                  onRestoreVersion={() => previewVersion && handleRestoreVersion(previewVersion.version.version_number)}
                  onCancelPreview={handleCancelPreview}
                />
                <RichTextPlugin
                  contentEditable={
                    <ContentEditable 
                      className="editor-input flex-1 p-8 outline-none resize-none overflow-auto"
                      style={{
                        fontSize: '14px',
                        lineHeight: '1.4',
                        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
                      }}
                    />
                  }
                  placeholder={
                    <div className="editor-placeholder absolute top-8 left-8 text-gray-400 pointer-events-none">
                      开始编写您的文档...支持 Markdown 語法
                    </div>
                  }
                  ErrorBoundary={LexicalErrorBoundary}
                />
                <OnChangePlugin onChange={handleContentChange} />
                <HistoryPlugin />
                <MarkdownShortcutPlugin transformers={TRANSFORMERS} />
                <FloatingFormatToolbar />
                <TOCPlugin onTOCUpdate={handleTOCUpdate} />
                <EnterKeyPlugin />
                
                {/* 统一的智能同步插件 */}
                {sharedbClientRef.current && (
                  <IntelligentSyncPlugin
                    documentId={documentId}
                    content={content}
                    documentState={documentState}
                    setDocumentState={setDocumentState}
                    updateEditorContent={updateEditorContent}
                    onContentChange={(synced) => {
                      setIsOnline(synced);
                      if (synced) {
                        setLastSyncTime(new Date());
                        setHasUnsavedChanges(false);
                      }
                    }}
                    onCollaborativeUpdate={(hasUpdates) => {
                      setHasCollaborativeUpdates(hasUpdates);
                      if (hasUpdates) {
                        setTimeout(() => setHasCollaborativeUpdates(false), 3000);
                      }
                    }}
                    sharedbClient={sharedbClientRef.current}
                    lastUserInputTimeRef={lastUserInputTimeRef}
                    setHasCollaborativeUpdates={setHasCollaborativeUpdates}
                  />
                )}
                
                {/* 保存编辑器引用 */}
                <EditorRefPlugin onRef={saveEditorRef} />
                
                {/* 版本预览插件 */}
                {isVersionPreviewMode && previewVersion && (
                  <VersionPreviewPlugin content={previewVersion.content} />
                )}
              </div>
            </LexicalComposer>
          </div>



          {/* AI助手区域 */}
          <div className="w-80 flex flex-col min-h-0">
            <AIAssistant
              onInsertContent={insertContentToEditor}
              documentContent={previewContent}
            />
          </div>

          {/* 实时预览区域 - 只在预览模式下显示 */}
          {isPreviewMode && (
            <div className="w-1/2 overflow-auto bg-gray-50 min-h-0">
              <div className="p-8 prose prose-lg max-w-none bg-white m-4 rounded-lg shadow-sm">
                <div className="markdown-preview">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {previewContent || '# 开始编写您的文档\n\n在左側編輯器中輸入 Markdown 內容，右側會實時顯示渲染效果...'}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 底部状态栏 */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 bg-gray-50 border-t border-gray-200 text-sm text-gray-600">
        <div className="flex items-center space-x-4">
          <span>字符数: {previewContent.length}</span>
          <span>行数: {previewContent.split('\n').length}</span>
          {hasUnsavedChanges && (
            <span className="text-yellow-600 font-medium">● 有未保存的更改</span>
          )}
          {sharedbClientRef.current && (
            <span>待处理操作: {sharedbClientRef.current.getCurrentState().pendingOperations}</span>
          )}
          <span className={isOnline ? 'text-green-600' : 'text-red-600'}>
            ● {isOnline ? '智能同步已启用' : '离线模式'}
          </span>
          {documentState && (
            <span className="text-blue-600">版本: v{documentState.version}</span>
          )}
          {lastSyncTime && (
            <span className="text-gray-500">
              上次同步: {lastSyncTime.toLocaleTimeString()}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <span>Lexical 编辑器</span>
          <span>•</span>
          <span>ShareDB 协作</span>
          <span>•</span>
          <span>AI 助手</span>
          <span>•</span>
          <span>{isOnline ? '在线' : '离线'}</span>
          
          {hasCollaborativeUpdates && (
            <>
              <span>•</span>
              <span className="text-blue-600 animate-pulse">协作更新中</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// 格式工具栏组件
function FormatToolbar({ 
  isVersionPreviewMode, 
  previewVersion, 
  onRestoreVersion, 
  onCancelPreview 
}: {
  isVersionPreviewMode?: boolean;
  previewVersion?: {version: DocumentVersion, content: string} | null;
  onRestoreVersion?: () => void;
  onCancelPreview?: () => void;
}) {
  const [editor] = useLexicalComposerContext();
  const [formatInfo, setFormatInfo] = useState<string>('普通文本');

  useEffect(() => {
    const updateFormatInfo = () => {
      editor.getEditorState().read(() => {
        const selection = $getSelection();
        
        if ($isRangeSelection(selection)) {
          const node = selection.anchor.getNode();
          const parent = node.getParent();
          
          let formatText = '';
          
          // 检查节点类型
          if (parent) {
            const parentType = parent.getType();
            switch (parentType) {
              case 'heading':
                const level = (parent as any).getTag();
                formatText = `${level.toUpperCase()} 标题`;
                break;
              case 'quote':
                formatText = '引用块';
                break;
              case 'listitem':
                const listParent = parent.getParent();
                if (listParent?.getType() === 'list') {
                  const listType = (listParent as any).getListType();
                  formatText = listType === 'bullet' ? '• 无序列表' : '1. 有序列表';
                }
                break;
              case 'code':
                formatText = '代码块';
                break;
              case 'paragraph':
                // 检查文本格式
                if (node.getType() === 'text') {
                  const format = node.getFormat();
                  const formats = [];
                  if (format & 1) formats.push('B');
                  if (format & 2) formats.push('I');
                  if (format & 4) formats.push('U');
                  if (format & 8) formats.push('S');
                  if (format & 16) formats.push('Code');
                  formatText = formats.length > 0 ? `段落 (${formats.join(' ')})` : '段落';
                } else {
                  formatText = '段落';
                }
                break;
              default:
                formatText = '普通文本';
            }
          } else {
            formatText = '普通文本';
          }
          
          setFormatInfo(formatText);
        }
      });
    };

    const unregisterCommand = editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        updateFormatInfo();
      });
    });

    // 初始更新
    updateFormatInfo();

    return unregisterCommand;
  }, [editor]);

  return (
    <div className="flex-shrink-0 px-4 py-2 bg-gray-50 border-b border-gray-200 text-xs text-gray-600 flex items-center justify-between">
      <div>
        <span className="font-medium">格式: </span>
        <span className="text-blue-600">{formatInfo}</span>
      </div>
      
      {/* 版本预览模式下的恢复按钮 */}
      {isVersionPreviewMode && previewVersion && (
        <div className="flex items-center gap-2">
          <span className="text-gray-500">
            预览版本 {previewVersion.version.version_number}
          </span>
          <button
            onClick={onRestoreVersion}
            className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 transition-colors text-xs font-medium"
          >
            恢复
          </button>
          <button
            onClick={onCancelPreview}
            className="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 transition-colors text-xs font-medium"
          >
            取消
          </button>
        </div>
      )}
    </div>
  );
}

// 浮动格式工具栏组件
function FloatingFormatToolbar() {
  const [editor] = useLexicalComposerContext();
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isBelow, setIsBelow] = useState(false); // 工具栏是否显示在选择下方
  const [formatState, setFormatState] = useState({
    isBold: false,
    isItalic: false,
    isUnderline: false,
    isStrikethrough: false,
    isCode: false,
  });

  const updateToolbar = useCallback(() => {
    const selection = $getSelection();
    
    if (!$isRangeSelection(selection) || selection.isCollapsed()) {
      setIsVisible(false);
      return;
    }

    // 获取选中文本的格式状态
    const anchorNode = selection.anchor.getNode();
    const element = editor.getElementByKey(anchorNode.getKey());
    
    if (element) {
      const domSelection = window.getSelection();
      if (domSelection && domSelection.rangeCount > 0) {
        const rect = domSelection.getRangeAt(0).getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          // 计算工具栏的宽度（大约 300px）
          const toolbarWidth = 300;
          const toolbarHeight = 45;
          
          // 计算居中位置
          let x = rect.left + rect.width / 2;
          let y = rect.top - 10;
          
          // 确保工具栏不超出左边界
          if (x - toolbarWidth / 2 < 10) {
            x = toolbarWidth / 2 + 10;
          }
          
          // 确保工具栏不超出右边界
          if (x + toolbarWidth / 2 > window.innerWidth - 10) {
            x = window.innerWidth - toolbarWidth / 2 - 10;
          }
          
          // 确保工具栏不超出上边界
          let showBelow = false;
          if (y - toolbarHeight < 10) {
            y = rect.bottom + 10; // 如果上方空间不够，显示在下方
            showBelow = true;
          }
          
          setPosition({ x, y });
          setIsBelow(showBelow);
          setIsVisible(true);
        }
      }
    }

    // 更新格式状态
    setFormatState({
      isBold: selection.hasFormat('bold'),
      isItalic: selection.hasFormat('italic'),
      isUnderline: selection.hasFormat('underline'),
      isStrikethrough: selection.hasFormat('strikethrough'),
      isCode: selection.hasFormat('code'),
    });
  }, [editor]);

  useEffect(() => {
    const updateListener = editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        updateToolbar();
      });
    });

    const selectionListener = editor.registerCommand(
      SELECTION_CHANGE_COMMAND,
      () => {
        updateToolbar();
        return false;
      },
      1
    );

    return () => {
      updateListener();
      selectionListener();
    };
  }, [editor, updateToolbar]);

  const toggleFormat = (format: 'bold' | 'italic' | 'underline' | 'strikethrough' | 'code') => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, format);
  };

  const convertToHeading = (level: number) => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        $setBlocksType(selection, () => $createHeadingNode(`h${level}` as any));
      }
    });
    setIsVisible(false);
  };

  const convertToQuote = () => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        $setBlocksType(selection, () => $createQuoteNode());
      }
    });
    setIsVisible(false);
  };

  const convertToParagraph = () => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        $setBlocksType(selection, () => $createParagraphNode());
      }
    });
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div
      className="fixed z-50 bg-gray-800 text-white rounded-lg shadow-lg"
      style={{
        left: position.x,
        top: position.y - 45,
        transform: 'translateX(-50%)',
        minWidth: 'max-content',
      }}
    >
      <div className="flex items-center px-3 py-2 space-x-1">
        {/* 文本格式按钮 */}
        <button
          className={`p-1.5 rounded hover:bg-gray-700 transition-colors ${formatState.isBold ? 'bg-gray-600' : ''}`}
          onClick={() => toggleFormat('bold')}
          title="粗体 (Ctrl+B)"
        >
          <Bold className="h-4 w-4" />
        </button>

        <button
          className={`p-1.5 rounded hover:bg-gray-700 transition-colors ${formatState.isItalic ? 'bg-gray-600' : ''}`}
          onClick={() => toggleFormat('italic')}
          title="斜体 (Ctrl+I)"
        >
          <Italic className="h-4 w-4" />
        </button>

        <button
          className={`p-1.5 rounded hover:bg-gray-700 transition-colors ${formatState.isUnderline ? 'bg-gray-600' : ''}`}
          onClick={() => toggleFormat('underline')}
          title="下划线 (Ctrl+U)"
        >
          <Underline className="h-4 w-4" />
        </button>

        <button
          className={`p-1.5 rounded hover:bg-gray-700 transition-colors ${formatState.isStrikethrough ? 'bg-gray-600' : ''}`}
          onClick={() => toggleFormat('strikethrough')}
          title="删除线"
        >
          <Strikethrough className="h-4 w-4" />
        </button>

        <button
          className={`p-1.5 rounded hover:bg-gray-700 transition-colors ${formatState.isCode ? 'bg-gray-600' : ''}`}
          onClick={() => toggleFormat('code')}
          title="行内代码"
        >
          <Code className="h-4 w-4" />
        </button>

        {/* 分隔线 */}
        <div className="w-px h-6 bg-gray-600 mx-1"></div>

        {/* 块级格式按钮 */}
        <button
          className="p-1.5 rounded hover:bg-gray-700 transition-colors"
          onClick={convertToParagraph}
          title="转换为普通段落"
        >
          <Type className="h-4 w-4" />
        </button>

        <button
          className="p-1.5 rounded hover:bg-gray-700 transition-colors"
          onClick={() => convertToHeading(1)}
          title="转换为一级标题"
        >
          <span className="text-xs font-bold px-1">H1</span>
        </button>

        <button
          className="p-1.5 rounded hover:bg-gray-700 transition-colors"
          onClick={() => convertToHeading(2)}
          title="转换为二级标题"
        >
          <span className="text-xs font-bold px-1">H2</span>
        </button>

        <button
          className="p-1.5 rounded hover:bg-gray-700 transition-colors"
          onClick={() => convertToHeading(3)}
          title="转换为三级标题"
        >
          <span className="text-xs font-bold px-1">H3</span>
        </button>

        <button
          className="p-1.5 rounded hover:bg-gray-700 transition-colors"
          onClick={convertToQuote}
          title="转换为引用块"
        >
          <Quote className="h-4 w-4" />
        </button>

        {/* 关闭按钮 */}
        <div className="w-px h-6 bg-gray-600 mx-1"></div>
        <button
          className="p-1.5 rounded hover:bg-gray-700 text-gray-400 transition-colors"
          onClick={() => setIsVisible(false)}
          title="关闭工具栏"
        >
          <X className="h-3 w-3" />
        </button>
      </div>

      {/* 小三角形指向选中文本 */}
      {isBelow ? (
        <div
          className="absolute bottom-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-b-4 border-l-transparent border-r-transparent border-b-gray-800"
        ></div>
      ) : (
        <div
          className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-800"
        ></div>
      )}
    </div>
  );
}

// 目录更新插件
function TOCPlugin({ onTOCUpdate }: { onTOCUpdate: (items: Array<{id: string, text: string, level: number}>) => void }) {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    const updateTOC = () => {
      editor.getEditorState().read(() => {
        const root = $getRoot();
        const headings: Array<{id: string, text: string, level: number}> = [];
        
        // 直接遍历根节点的直接子节点
        const children = root.getChildren();
        children.forEach((node: any) => {
          if (node.getType() === 'heading') {
            const text = node.getTextContent();
            const level = parseInt(node.getTag().substring(1)); // h1 -> 1, h2 -> 2, etc.
            
            headings.push({
              id: node.getKey(), // 使用节点的key作为唯一标识符
              text: text || `标题 ${level}`,
              level
            });
          }
        });
        
        onTOCUpdate(headings);
      });
    };

    const removeUpdateListener = editor.registerUpdateListener(() => {
      updateTOC();
    });

    // 初始化时也更新一次
    updateTOC();

    return removeUpdateListener;
  }, [editor, onTOCUpdate]);

  return null;
}

// 目录组件
function TableOfContents({ 
  items, 
  onItemClick 
}: { 
  items: Array<{id: string, text: string, level: number}>;
  onItemClick: (id: string) => void;
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="pt-4 px-3">
      <div className="space-y-1">
        {items.map((item, index) => {
          const levelStyles = {
            1: 'text-gray-800 font-medium text-sm',
            2: 'text-gray-600 text-sm',
            3: 'text-gray-500 text-xs'
          };
          
          return (
            <div
              key={index}
              className={`cursor-pointer hover:text-blue-600 py-0.5 transition-colors ${levelStyles[item.level as keyof typeof levelStyles] || 'text-gray-500 text-xs'}`}
              style={{ 
                paddingLeft: `${(item.level - 1) * 16}px`
              }}
              onClick={() => onItemClick(item.id)}
              title={item.text}
            >
              <span className="truncate block leading-relaxed">
                {item.text}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// 回车键和退格键处理插件
function EnterKeyPlugin() {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    // 处理回车键
    const enterUnregister = editor.registerCommand(
      KEY_ENTER_COMMAND,
      (event) => {
        const selection = $getSelection();
        if ($isRangeSelection(selection)) {
          const anchorNode = selection.anchor.getNode();
          let parentNode = anchorNode.getParent();
          
          // 查找块级父节点
          while (parentNode && !['paragraph', 'heading', 'quote', 'listitem'].includes(parentNode.getType())) {
            const grandParent = parentNode.getParent();
            if (grandParent) {
              parentNode = grandParent;
            } else {
              break;
            }
          }

          if (parentNode && (parentNode.getType() === 'heading' || parentNode.getType() === 'quote')) {
            event?.preventDefault();
            
            // 处理文本分割
            const anchorNode = selection.anchor.getNode();
            if (anchorNode.getType() === 'text') {
              const offset = selection.anchor.offset;
              const textContent = anchorNode.getTextContent();
              
              // 创建新段落
              const newParagraph = $createParagraphNode();
              
              if (offset < textContent.length) {
                // 有光标后的内容需要移动
                const afterText = textContent.substring(offset);
                
                // 在新段落中添加后续文本
                if (afterText) {
                  const newTextNode = $createTextNode(afterText);
                  newParagraph.append(newTextNode);
                }
                
                // 从当前文本节点中删除光标后的内容
                // 设置选择范围为光标后的所有文本，然后删除
                const textNode = anchorNode as any;
                textNode.select(offset, textContent.length);
                const newSelection = $getSelection();
                if ($isRangeSelection(newSelection)) {
                  newSelection.removeText();
                }
              }
              
              // 插入新段落到当前块后面
              parentNode.insertAfter(newParagraph);
              
              // 将光标移动到新段落
              if (newParagraph.getChildrenSize() > 0) {
                newParagraph.selectStart();
              } else {
                newParagraph.select();
              }
            } else {
              // 如果不在文本节点中，只创建空的新段落
              const newParagraph = $createParagraphNode();
              parentNode.insertAfter(newParagraph);
              newParagraph.select();
            }
            
            return true;
          }
          
          // 处理列表项的回车行为
          if (parentNode && parentNode.getType() === 'listitem') {
            event?.preventDefault();
            
            const anchorNode = selection.anchor.getNode();
            const offset = selection.anchor.offset;
            
            // 检查是否在列表项的开头
            if (anchorNode.getType() === 'text') {
              const textContent = anchorNode.getTextContent();
              
              // 如果光标在开头，删除列表项并创建段落
              if (offset === 0) {
                const newParagraph = $createParagraphNode();
                if (textContent.trim()) {
                  const newTextNode = $createTextNode(textContent);
                  newParagraph.append(newTextNode);
                }
                parentNode.replace(newParagraph);
                newParagraph.select();
                return true;
              }
            }
            
            // 其他情况让默认行为处理（创建新的列表项）
            return false;
          }
        }
        
        // 对于普通段落，让默认行为处理（会自动创建新段落）
        return false;
      },
      COMMAND_PRIORITY_LOW
    );

    // 处理退格键
    const backspaceUnregister = editor.registerCommand(
      KEY_BACKSPACE_COMMAND,
      (event) => {
        const selection = $getSelection();
        if ($isRangeSelection(selection)) {
          const anchorNode = selection.anchor.getNode();
          let parentNode = anchorNode.getParent();
          
          // 查找块级父节点
          while (parentNode && !['paragraph', 'heading', 'quote', 'listitem'].includes(parentNode.getType())) {
            const grandParent = parentNode.getParent();
            if (grandParent) {
              parentNode = grandParent;
            } else {
              break;
            }
          }

          // 处理列表项的空内容退格
          if (parentNode && parentNode.getType() === 'listitem') {
            const textContent = parentNode.getTextContent();
            
            // 检查是否在列表项的开头，且列表项为空或只有空白字符
            if (selection.anchor.offset === 0 && (!textContent || !textContent.trim())) {
              event?.preventDefault();
              
              // 检查列表结构
              const listParent = parentNode.getParent();
              if (listParent && listParent.getType() === 'list') {
                const listChildren = listParent.getChildren();
                
                // 如果这是列表中唯一的项目，将整个列表转换为段落
                if (listChildren.length === 1) {
                  const newParagraph = $createParagraphNode();
                  listParent.replace(newParagraph);
                  newParagraph.select();
                } else {
                  // 如果还有其他项目，只删除当前列表项，保持在同一位置
                  const newParagraph = $createParagraphNode();
                  parentNode.replace(newParagraph);
                  newParagraph.select();
                }
              }
              
              return true;
            }
            
            // 如果列表项有内容，但在开头按backspace，也转换为段落
            if (selection.anchor.offset === 0 && textContent && textContent.trim()) {
              event?.preventDefault();
              
              // 创建新段落并保留内容
              const newParagraph = $createParagraphNode();
              const newTextNode = $createTextNode(textContent);
              newParagraph.append(newTextNode);
              
              // 替换列表项
              parentNode.replace(newParagraph);
              newParagraph.select();
              
              return true;
            }
          }
        }
        
        // 其他情况让默认行为处理
        return false;
      },
      COMMAND_PRIORITY_LOW
    );

    return () => {
      enterUnregister();
      backspaceUnregister();
    };
  }, [editor]);

  return null;
}

// 用于保存编辑器引用的插件
function EditorRefPlugin({ onRef }: { onRef: (editor: any) => void }) {
  const [editor] = useLexicalComposerContext();
  
  useEffect(() => {
    onRef(editor);
  }, [editor, onRef]);
  
  return null;
}

function VersionPreviewPlugin({ content }: { content: string }) {
  const [editor] = useLexicalComposerContext();
  
  useEffect(() => {
    if (content) {
      try {
        // 尝试解析为 Lexical 状态
        const parsedContent = JSON.parse(content);
        editor.setEditorState(editor.parseEditorState(JSON.stringify(parsedContent)));
      } catch (error) {
        // 如果不是 JSON 格式，作为纯文本处理
        console.log('Content is not JSON format, treating as plain text');
        editor.update(() => {
          const root = $getRoot();
          root.clear();
          const paragraph = $createParagraphNode();
          paragraph.append($createTextNode(content));
          root.append(paragraph);
        });
      }
    }
  }, [content, editor]);
  
  return null;
} 