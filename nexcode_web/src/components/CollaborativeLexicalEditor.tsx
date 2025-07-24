import { useEffect, useRef, useState, useCallback } from 'react';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { MarkdownShortcutPlugin } from '@lexical/react/LexicalMarkdownShortcutPlugin';
import { TRANSFORMERS } from '@lexical/markdown';
import { $getRoot, EditorState, $createParagraphNode, $createTextNode } from 'lexical';
import { HeadingNode, QuoteNode } from '@lexical/rich-text';
import { ListItemNode, ListNode } from '@lexical/list';
import { CodeNode, CodeHighlightNode } from '@lexical/code';
import { LinkNode, AutoLinkNode } from '@lexical/link';
import { Eye, EyeOff, Save, Wifi, WifiOff, Users, RefreshCw, Clock, History, FileText } from 'lucide-react';
import { toast } from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { ShareDBClient, DocumentState } from '@/services/sharedb';
// 假设导入 authStore，如果项目有
import { useAuthStore } from '@/store/authStore';  // 如果没有，忽略这行

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

// 统一的智能同步插件 - 替换所有原有的同步插件
function IntelligentSyncPlugin({
  documentId,
  content,
  documentState,
  setDocumentState,
  updateEditorContent,
  onContentChange,
  onCollaborativeUpdate
}: {
  documentId: number;
  content: string;
  documentState: DocumentState | null;
  setDocumentState: (state: DocumentState | null) => void;
  updateEditorContent: (content: string) => void;
  onContentChange?: (synced: boolean) => void;
  onCollaborativeUpdate?: (hasUpdates: boolean) => void;
}) {
  const [editor] = useLexicalComposerContext(); // 获取编辑器实例
  const syncTimer = useRef<NodeJS.Timeout>();
  const versionTimer = useRef<NodeJS.Timeout>();
  const pollTimer = useRef<NodeJS.Timeout>(); // 轮询其他用户更新
  const lastSyncedContent = useRef<string>('');
  const lastUserInputTime = useRef<number>(Date.now());
  const syncInterval = useRef<number>(2000); // 动态同步间隔，初始2秒
  const pollInterval = useRef<number>(5000); // 轮询间隔，检查其他用户更新
  const isUserEditing = useRef<boolean>(false);
  const syncInProgress = useRef<boolean>(false);

  // 从编辑器获取当前内容
  const getCurrentEditorContent = useCallback(() => {
    if (!editor) return content;
    
    let editorContent = '';
    editor.getEditorState().read(() => {
      const root = $getRoot();
      editorContent = root.getTextContent();
    });
    
    return editorContent || content;
  }, [editor, content]);

  // 执行同步的核心函数
  const performSync = useCallback(async (contentToSync?: string, createVersion: boolean = false) => {
    if (syncInProgress.current) return false;
    
    const actualContent = contentToSync || getCurrentEditorContent();
    if (!actualContent) return false;
    
    syncInProgress.current = true;
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No auth token found');
        return false;
      }

      console.log('Syncing content:', {
        length: actualContent.length,
        version: documentState?.version || 0,
        createVersion
      });

      const response = await fetch('/v1/sharedb/documents/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          doc_id: documentId.toString(),
          version: documentState?.version || 0,
          content: actualContent,
          create_version: createVersion
        })
      });

      if (response.ok) {
        const result = await response.json();
        
        // 更新文档状态
        if (documentState) {
          setDocumentState({
            ...documentState,
            content: result.content,
            version: result.version
          });
        }
        
        lastSyncedContent.current = result.content;
        
        // 如果服务器返回的内容与本地不同，说明有其他用户的更新
        if (result.content !== actualContent) {
          console.log('Server content differs, updating editor with collaborative changes');
          updateEditorContent(result.content);
          onCollaborativeUpdate?.(true); // 通知有协作更新
        }
        
        // 动态调整同步间隔
        if (lastSyncedContent.current === actualContent) {
          syncInterval.current = Math.min(syncInterval.current * 1.2, 30000);
        } else {
          syncInterval.current = 2000; // 重置为默认间隔
        }
        
        onContentChange?.(true);
        console.log(createVersion ? 'Version created' : 'Content synced', {
          version: result.version,
          interval: syncInterval.current,
          hasCollaborativeChanges: result.content !== actualContent
        });
        
        return true;
      } else {
        console.error('Sync failed:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Sync error:', error);
      return false;
    } finally {
      syncInProgress.current = false;
    }
  }, [documentId, documentState, setDocumentState, updateEditorContent, onContentChange, onCollaborativeUpdate, getCurrentEditorContent]);

  // 轮询检查其他用户的更新
  const pollForUpdates = useCallback(async () => {
    if (syncInProgress.current) return;
    
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      // 获取服务器最新状态
      const response = await fetch(`/v1/sharedb/documents/${documentId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const serverState = await response.json();
        
        // 检查版本是否有更新
        if (serverState.version > (documentState?.version || 0)) {
          console.log('New version detected from other users:', serverState.version);
          
          // 如果用户当前没有在编辑，直接更新内容
          if (!isUserEditing.current || Date.now() - lastUserInputTime.current > 5000) {
            setDocumentState({
              doc_id: serverState.doc_id,
              content: serverState.content,
              version: serverState.version,
              created_at: serverState.created_at,
              updated_at: serverState.updated_at
            });
            
            updateEditorContent(serverState.content);
            lastSyncedContent.current = serverState.content;
            onCollaborativeUpdate?.(true); // 通知有协作更新
            
            console.log('Updated content from collaborative changes');
          } else {
            // 用户正在编辑，执行合并同步
            console.log('User is editing, performing merge sync');
            await performSync(undefined, false); // 使用当前编辑器内容
          }
        }
        
        // 动态调整轮询间隔并重启定时器
        const newInterval = isUserEditing.current ? 3000 : Math.min(pollInterval.current * 1.1, 15000);
        if (newInterval !== pollInterval.current) {
          pollInterval.current = newInterval;
          
          // 重启轮询定时器以使用新间隔
          if (pollTimer.current) {
            clearInterval(pollTimer.current);
            console.log('Restarting polling with new interval:', pollInterval.current);
            pollTimer.current = setInterval(pollForUpdates, pollInterval.current);
          }
        }
        
        onContentChange?.(true);
      }
    } catch (error) {
      console.error('Poll for updates failed:', error);
      onContentChange?.(false);
    }
  }, [documentId, documentState, setDocumentState, updateEditorContent, onContentChange, performSync, onCollaborativeUpdate]);

  // 轮询其他用户更新 - 只在组件挂载时启动一次
  useEffect(() => {
    console.log('Starting initial collaborative polling');
    pollTimer.current = setInterval(pollForUpdates, pollInterval.current);

    return () => {
      if (pollTimer.current) {
        clearInterval(pollTimer.current);
      }
    };
  }, [pollForUpdates]);

  // 组件初始化时执行一次同步
  useEffect(() => {
    const initSync = setTimeout(() => {
      const initialContent = getCurrentEditorContent();
      if (initialContent && initialContent !== lastSyncedContent.current) {
        console.log('Initial sync on component mount');
        performSync(undefined, false);
      }
    }, 1000); // 延迟1秒确保编辑器已初始化

    return () => clearTimeout(initSync);
  }, [getCurrentEditorContent, performSync]);

  // 用户输入检测和同步调度
  useEffect(() => {
    const currentEditorContent = getCurrentEditorContent();
    
    // 检测是否为用户主动编辑
    if (currentEditorContent !== lastSyncedContent.current) {
      lastUserInputTime.current = Date.now();
      isUserEditing.current = true;
      
      // 重置同步间隔（用户活跃时更频繁同步）
      syncInterval.current = Math.max(syncInterval.current * 0.8, 1000);
      pollInterval.current = 3000; // 用户编辑时更频繁检查协作更新
      
      console.log('User input detected, scheduling sync');
    } else {
      // 用户停止编辑一段时间后，标记为非编辑状态
      if (Date.now() - lastUserInputTime.current > 10000) { // 10秒无操作
        isUserEditing.current = false;
      }
    }

    // 清除之前的定时器
    if (syncTimer.current) {
      clearTimeout(syncTimer.current);
    }
    if (versionTimer.current) {
      clearTimeout(versionTimer.current);
    }

    // 智能同步调度 - 确保真正执行同步
    if (currentEditorContent !== lastSyncedContent.current) {
      syncTimer.current = setTimeout(() => {
        console.log('Executing scheduled sync');
        performSync(undefined, false); // 常规同步，不创建版本
      }, syncInterval.current);
    }

    // 版本创建调度（用户停止编辑1分钟后）
    versionTimer.current = setTimeout(() => {
      const timeSinceLastInput = Date.now() - lastUserInputTime.current;
      const latestContent = getCurrentEditorContent();
      
      if (isUserEditing.current && 
          timeSinceLastInput >= 60000 && // 1分钟无操作
          latestContent !== lastSyncedContent.current) { // 内容有变化
        
        console.log('Creating version due to user inactivity');
        performSync(undefined, true); // 创建版本
        isUserEditing.current = false;
      }
    }, 60000);

    return () => {
      if (syncTimer.current) clearTimeout(syncTimer.current);
      if (versionTimer.current) clearTimeout(versionTimer.current);
    };
  }, [getCurrentEditorContent, performSync]);

  return null;
}

// 版本历史接口
interface DocumentVersion {
  id: number;
  version_number: number;
  title: string;
  content: string;
  changed_by: number;
  change_description: string;
  created_at: string;
}

interface CollaborativeLexicalEditorProps {
  documentId: number;
  initialContent?: string;
  onContentChange?: (content: string) => void;
  onSave?: (content: string) => Promise<void>;
}

export function CollaborativeLexicalEditor({
  documentId,
  initialContent = '',
  onContentChange,
  onSave
}: CollaborativeLexicalEditorProps) {
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [content, setContent] = useState(initialContent);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [documentState, setDocumentState] = useState<DocumentState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [versionHistory, setVersionHistory] = useState<DocumentVersion[]>([]);
  const [hasCollaborativeUpdates, setHasCollaborativeUpdates] = useState(false); // 协作更新指示
  
  // 移除不再需要的状态
  // const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  // const [autoSyncEnabled, setAutoSyncEnabled] = useState(true);
  // const [syncInterval, setSyncInterval] = useState(5000);
  // const [smartVersioningEnabled, setSmartVersioningEnabled] = useState(true);
  
  const sharedbClientRef = useRef<ShareDBClient>();
  const editorRef = useRef<any>();
  const lastUserInputTimeRef = useRef<number>(Date.now()); // 用于跟踪用户输入时间

  // 初始化 ShareDB 客户端并加载文档
  useEffect(() => {
    const client = new ShareDBClient(documentId.toString());
    sharedbClientRef.current = client;

    const loadDocument = async () => {
      try {
        // 1. 首先从ShareDB获取基础文档状态
        const docState = await client.getDocument();
        console.log('Initial document state from ShareDB:', docState);
        
        // 2. 强制与服务器同步，确保获取最新版本
        const token = localStorage.getItem('token');
        if (token) {
          try {
            // 获取服务器上的最新状态
            const response = await fetch(`/v1/sharedb/documents/${documentId}`, {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });
            
            if (response.ok) {
              const latestState = await response.json();
              console.log('Latest server state:', latestState);
              
              // 如果服务器版本更新，使用服务器内容
              if (latestState.version >= docState.version) {
                setDocumentState({
                  doc_id: latestState.doc_id,
                  content: latestState.content,
                  version: latestState.version,
                  created_at: latestState.created_at,
                  updated_at: latestState.updated_at
                });
                setContent(latestState.content || initialContent);
                console.log('Using latest server content');
              } else {
                // 使用ShareDB的内容
                setDocumentState(docState);
                setContent(docState.content || initialContent);
                console.log('Using ShareDB content');
              }
            } else {
              // 降级到ShareDB内容
              setDocumentState(docState);
              setContent(docState.content || initialContent);
              console.log('Using ShareDB content (server unavailable)');
            }
          } catch (fetchError) {
            console.warn('Failed to fetch latest server state:', fetchError);
            // 降级到ShareDB内容
            setDocumentState(docState);
            setContent(docState.content || initialContent);
          }
        } else {
          // 没有token，使用ShareDB内容
          setDocumentState(docState);
          setContent(docState.content || initialContent);
        }
        
        setIsLoading(false);
        setLastSyncTime(new Date());
        setIsOnline(true);
        
      } catch (error) {
        console.error('Failed to load document:', error);
        toast.error('加载文档失败，使用本地版本');
        setContent(initialContent);
        setIsOnline(false);
        setIsLoading(false);
      }
    };

    loadDocument();

    return () => {
      client.destroy();
    };
  }, [documentId, initialContent]);

  // 编辑器初始配置
  const initialConfig = {
    namespace: 'CollaborativeNexCodeEditor',
    theme,
    nodes: editorNodes,
    onError: (error: Error) => {
      console.error('Lexical Error:', error);
      toast.error('编辑器错误');
    },
    editorState: undefined,
  };

  // 更新编辑器内容（同步时使用）- 改进协作处理
  const updateEditorContent = useCallback((newContent: string) => {
    if (!editorRef.current) return;
    
    // 检查用户是否正在活跃编辑
    const now = Date.now();
    const timeSinceLastInput = now - lastUserInputTimeRef.current;
    const isActivelyEditing = timeSinceLastInput < 3000; // 3秒内有输入视为活跃编辑
    
    if (isActivelyEditing) {
      console.log('User is actively editing, deferring content update');
      // 如果用户正在活跃编辑，延迟更新
      setTimeout(() => updateEditorContent(newContent), 2000);
      return;
    }
    
    editorRef.current.update(() => {
      const root = $getRoot();
      const currentContent = root.getTextContent();
      
      // 避免不必要的更新
      if (currentContent === newContent) {
        return;
      }
      
      console.log('Updating editor with collaborative content');
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
    
    // 更新本地内容状态
    setContent(newContent);
  }, []);

  // 跟踪用户输入时间（用于协作冲突检测）
  useEffect(() => {
    const handleUserInput = () => {
      lastUserInputTimeRef.current = Date.now();
    };
    
    // 监听各种用户输入事件
    const events = ['keydown', 'mousedown', 'input', 'paste'];
    events.forEach(event => {
      document.addEventListener(event, handleUserInput, true);
    });
    
    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleUserInput, true);
      });
    };
  }, []);

  // 处理内容变化
  const handleContentChange = useCallback((editorState: EditorState) => {
    editorState.read(() => {
      const root = $getRoot();
      const textContent = root.getTextContent();
      
      if (textContent !== content) {
        setContent(textContent);
        setHasUnsavedChanges(textContent !== (documentState?.content || initialContent));
        onContentChange?.(textContent);
      }
    });
  }, [content, documentState, initialContent, onContentChange]);

  // 手动保存功能（保留用于兼容性）
  const handleManualSave = useCallback(async () => {
    if (!onSave || !hasUnsavedChanges || isSaving) return;
    
    setIsSaving(true);
    try {
      await onSave(content);
      setHasUnsavedChanges(false);
      toast.success('文档已保存');
    } catch (error) {
      console.error('Failed to save:', error);
      toast.error('保存失败');
    } finally {
      setIsSaving(false);
    }
  }, [content, hasUnsavedChanges, isSaving, onSave]);

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

  // 创建版本
  const handleCreateVersion = useCallback(async (versionContent: string) => {
    try {
      const response = await fetch(`/api/v1/documents/${documentId}/versions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          content: versionContent,
          change_description: '自动版本保存'
        })
      });

      if (response.ok) {
        console.log('Version created successfully');
        // 刷新版本历史
        loadVersionHistory();
      }
    } catch (error) {
      console.error('Failed to create version:', error);
    }
  }, [documentId]);

  // 加载版本历史
  const loadVersionHistory = useCallback(async () => {
    try {
      const response = await fetch(`/api/v1/documents/${documentId}/versions`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setVersionHistory(data.versions || []);
      }
    } catch (error) {
      console.error('Failed to load version history:', error);
      toast.error('加载版本历史失败');
    }
  }, [documentId]);

  // 恢复版本
  const handleRestoreVersion = useCallback(async (versionNumber: number) => {
    try {
      const response = await fetch(`/api/v1/documents/${documentId}/versions/${versionNumber}/restore`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setContent(data.content);
        updateEditorContent(data.content);
        setShowVersionHistory(false);
        toast.success('版本已恢复');
        
        // 同步到ShareDB
        if (sharedbClientRef.current) {
          await sharedbClientRef.current.syncDocument(data.content);
        }
      }
    } catch (error) {
      console.error('Failed to restore version:', error);
      toast.error('恢复版本失败');
    }
  }, [documentId, updateEditorContent]);

  // 保存编辑器引用
  const saveEditorRef = useCallback((editor: any) => {
    editorRef.current = editor;
  }, []);

  // 切换版本历史
  const toggleVersionHistory = useCallback(() => {
    if (!showVersionHistory) {
      loadVersionHistory();
    }
    setShowVersionHistory(!showVersionHistory);
  }, [showVersionHistory, loadVersionHistory]);

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
    <div className="lexical-editor h-screen flex flex-col bg-white">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white shadow-sm">
        {/* 左侧：文档状态 */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${hasUnsavedChanges ? 'bg-yellow-500' : 'bg-green-500'}`}></div>
            <span className="text-sm text-gray-600 font-medium">
              {isSaving ? '保存中...' : hasUnsavedChanges ? '未保存' : '已保存'}
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

          {/* 版本信息 */}
          {documentState && (
            <div className="text-sm text-gray-500">
              版本: {documentState.version}
            </div>
          )}

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

        {/* 右侧：操作按钮 */}
        <div className="flex items-center space-x-2">
          {/* 移除自动功能开关，保持界面简洁 */}
          
          <button
            onClick={toggleVersionHistory}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            title="版本历史"
          >
            <History className="h-4 w-4" />
            <span>历史</span>
          </button>
          
          <button
            onClick={() => setIsPreviewMode(prev => !prev)}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            title="切换预览模式"
          >
            {isPreviewMode ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            <span>{isPreviewMode ? '编辑' : '预览'}</span>
          </button>
          
          <button
            onClick={handleSync}
            disabled={!isOnline}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
            title="手动同步文档"
          >
            <RefreshCw className="h-4 w-4" />
            <span>同步</span>
          </button>
          
          <button
            onClick={handleManualSave}
            disabled={!hasUnsavedChanges || isSaving}
            className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              hasUnsavedChanges 
                ? 'text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400' 
                : 'text-gray-500 bg-gray-100 cursor-not-allowed'
            }`}
            title="手动保存文档 (Ctrl+S)"
          >
            <Save className="h-4 w-4" />
            <span>{isSaving ? '保存中...' : '保存'}</span>
          </button>
        </div>
      </div>

      {/* 主要内容区域 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 版本历史侧边栏 */}
        {showVersionHistory && (
          <div className="w-80 border-r border-gray-200 bg-gray-50 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">版本历史</h3>
            </div>
            <div className="flex-1 overflow-auto">
              {versionHistory.length > 0 ? (
                <div className="p-2">
                  {versionHistory.map((version) => (
                    <div
                      key={version.id}
                      className="p-3 mb-2 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-shadow cursor-pointer"
                      onClick={() => handleRestoreVersion(version.version_number)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-900">
                          版本 {version.version_number}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(version.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-1">{version.change_description}</p>
                      <p className="text-xs text-gray-500 truncate">
                        {version.content.slice(0, 100)}...
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-gray-500">
                  暂无版本历史
                </div>
              )}
            </div>
          </div>
        )}

        {/* 编辑器区域 */}
        {!isPreviewMode && (
          <div className="flex-1">
            <LexicalComposer initialConfig={initialConfig}>
              <div className="editor-container h-full">
                <RichTextPlugin
                  contentEditable={
                    <ContentEditable 
                      className="editor-input h-full p-8 outline-none resize-none"
                      style={{
                        fontSize: '16px',
                        lineHeight: '1.8',
                        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
                      }}
                    />
                  }
                  placeholder={
                    <div className="editor-placeholder absolute top-8 left-8 text-gray-400 pointer-events-none">
                      开始编写您的文档...
                    </div>
                  }
                  ErrorBoundary={LexicalErrorBoundary}
                />
                <OnChangePlugin onChange={handleContentChange} />
                <HistoryPlugin />
                <MarkdownShortcutPlugin transformers={TRANSFORMERS} />
                
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
                        // 3秒后清除指示器
                        setTimeout(() => setHasCollaborativeUpdates(false), 3000);
                      }
                    }}
                  />
                )}
                
                {/* 保存编辑器引用 */}
                <EditorRefPlugin onRef={saveEditorRef} />
              </div>
            </LexicalComposer>
          </div>
        )}

        {/* 预览区域 */}
        {isPreviewMode && (
          <div className="flex-1 overflow-auto">
            <div className="p-8 prose prose-lg max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content || '# 开始编写您的文档\n\n在这里输入您的 Markdown 内容...'}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>

      {/* 底部状态栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-t border-gray-200 text-sm text-gray-600">
        <div className="flex items-center space-x-4">
          <span>字符数: {content.length}</span>
          <span>行数: {content.split('\n').length}</span>
          {hasUnsavedChanges && (
            <span className="text-yellow-600 font-medium">● 有未保存的更改</span>
          )}
          {sharedbClientRef.current && (
            <span>待处理操作: {sharedbClientRef.current.getCurrentState().pendingOperations}</span>
          )}
          <span className={isOnline ? 'text-green-600' : 'text-red-600'}>
            ● {isOnline ? '智能同步已启用' : '离线模式'}
          </span>
          {/* 详细同步信息 */}
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

// 用于保存编辑器引用的插件
function EditorRefPlugin({ onRef }: { onRef: (editor: any) => void }) {
  const [editor] = useLexicalComposerContext();
  
  useEffect(() => {
    onRef(editor);
  }, [editor, onRef]);
  
  return null;
} 