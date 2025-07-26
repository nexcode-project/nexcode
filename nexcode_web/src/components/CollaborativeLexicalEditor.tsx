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
import { $generateNodesFromDOM } from '@lexical/html';
import { $generateHtmlFromNodes } from '@lexical/html';

import { ShareDBClient, DocumentState } from '@/services/sharedb';
import { apiService } from '@/services/api';
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
}

export function CollaborativeLexicalEditor({
  documentId,
  initialContent = '',
  initialDocumentState, // 新增参数
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
  const [previewContent, setPreviewContent] = useState(''); // 用于预览的可读文本内容
  
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
      
      // 快捷鍵：Ctrl+P (或 Cmd+P) 切換預覽模式
      if ((event.ctrlKey || event.metaKey) && event.key === 'p') {
        event.preventDefault();
        setIsPreviewMode(prev => !prev);
        toast.success(`${isPreviewMode ? '已關閉' : '已開啟'}分屏預覽`);
      }
      
      // 快捷鍵：Ctrl+S (或 Cmd+S) 手動保存
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        handleManualSave();
      }
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
          }
        });
      }
    }, 500); // 500ms防抖
  }, [content, documentState, initialContent, onContentChange]);

  // 手动保存功能（保留用于兼容性）
  const handleManualSave = useCallback(async () => {
    if (!onSave || !hasUnsavedChanges || isSaving) return;
    
    setIsSaving(true);
    try {
      // 保存时使用JSON序列化的内容（包含完整格式）
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

  // 恢复版本
  const handleRestoreVersion = useCallback(async (versionNumber: number) => {
    try {
      const data = await apiService.restoreDocumentVersion(documentId, versionNumber);
      setContent(data.content);
      updateEditorContent(data.content);
      setShowVersionHistory(false);
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
            title="切换分屏预览模式 (Ctrl+P)"
          >
            {isPreviewMode ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            <span>{isPreviewMode ? '纯编辑' : '分屏预览'}</span>
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

        {/* 主編輯區域 */}
        <div className="flex-1 flex">
          {/* 编辑器區域 */}
          <div className={`${isPreviewMode ? 'w-1/2 border-r border-gray-200' : 'flex-1'} transition-all duration-300`}>
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
                      开始编写您的文档...支持 Markdown 語法
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
                    sharedbClient={sharedbClientRef.current}
                    lastUserInputTimeRef={lastUserInputTimeRef}
                    setHasCollaborativeUpdates={setHasCollaborativeUpdates}
                  />
                )}
                
                {/* 保存编辑器引用 */}
                <EditorRefPlugin onRef={saveEditorRef} />
              </div>
            </LexicalComposer>
          </div>

          {/* 实时预览区域 - 只在預覽模式下顯示 */}
          {isPreviewMode && (
            <div className="w-1/2 overflow-auto bg-gray-50">
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
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-t border-gray-200 text-sm text-gray-600">
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
          {isPreviewMode && (
            <>
              <span>•</span>
              <span className="text-green-600">分屏预览模式</span>
            </>
          )}
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