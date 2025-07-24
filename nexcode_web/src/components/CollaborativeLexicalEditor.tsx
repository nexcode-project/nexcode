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
import { Eye, EyeOff, Save, Wifi, WifiOff, Users, RefreshCw, Clock } from 'lucide-react';
import { toast } from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { ShareDBClient, DocumentState } from '@/services/sharedb';

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

// 实时同步插件
function RealtimeSyncPlugin({
  sharedbClient,
  onSync,
  isOnline,
  setIsOnline,
  autoSyncEnabled,
  syncInterval
}: {
  sharedbClient: ShareDBClient;
  onSync: (content: string, version: number) => void;
  isOnline: boolean;
  setIsOnline: (online: boolean) => void;
  autoSyncEnabled: boolean;
  syncInterval: number;
}) {
  const [editor] = useLexicalComposerContext();
  const syncTimer = useRef<NodeJS.Timeout>();

  // 定期同步功能
  useEffect(() => {
    if (!autoSyncEnabled) return;

    const performSync = async () => {
      try {
        editor.getEditorState().read(() => {
          const root = $getRoot();
          const content = root.getTextContent();
          
          // 执行同步
          sharedbClient.syncDocument(content).then(result => {
            if (result.success) {
              setIsOnline(true);
              onSync(result.content, result.version);
            }
          }).catch(error => {
            console.error('Auto sync failed:', error);
            setIsOnline(false);
          });
        });
      } catch (error) {
        console.error('Sync error:', error);
        setIsOnline(false);
      }
    };

    const interval = setInterval(performSync, syncInterval);
    return () => clearInterval(interval);
  }, [autoSyncEnabled, syncInterval, sharedbClient, editor, onSync, setIsOnline]);

  // 连接状态检查
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const online = await sharedbClient.checkConnection();
        setIsOnline(online);
      } catch (error) {
        setIsOnline(false);
      }
    };

    const interval = setInterval(checkConnection, 30000); // 每30秒检查一次
    return () => clearInterval(interval);
  }, [sharedbClient, setIsOnline]);

  return null;
}

// 自动保存插件
function AutoSavePlugin({
  onSave,
  content,
  isEnabled,
  saveDelay = 1000
}: {
  onSave: (content: string) => Promise<void>;
  content: string;
  isEnabled: boolean;
  saveDelay?: number;
}) {
  const saveTimer = useRef<NodeJS.Timeout>();
  const lastSavedContent = useRef<string>('');

  useEffect(() => {
    if (!isEnabled || !content || content === lastSavedContent.current) {
      return;
    }

    // 清除之前的定时器
    if (saveTimer.current) {
      clearTimeout(saveTimer.current);
    }

    // 设置新的定时器
    saveTimer.current = setTimeout(async () => {
      try {
        await onSave(content);
        lastSavedContent.current = content;
      } catch (error) {
        console.error('Auto save failed:', error);
      }
    }, saveDelay);

    return () => {
      if (saveTimer.current) {
        clearTimeout(saveTimer.current);
      }
    };
  }, [content, onSave, isEnabled, saveDelay]);

  return null;
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
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  const [autoSyncEnabled, setAutoSyncEnabled] = useState(true);
  const [syncInterval, setSyncInterval] = useState(5000); // 5秒同步一次
  
  const sharedbClientRef = useRef<ShareDBClient>();
  const editorRef = useRef<any>();

  // 初始化 ShareDB 客户端
  useEffect(() => {
    const client = new ShareDBClient(documentId.toString());
    sharedbClientRef.current = client;

    // 加载文档状态
    const loadDocument = async () => {
      try {
        const docState = await client.getDocument();
        setDocumentState(docState);
        setContent(docState.content);
        setIsLoading(false);
        setLastSyncTime(new Date());
      } catch (error) {
        console.error('Failed to load document:', error);
        toast.error('加载文档失败');
        setIsOnline(false);
        setIsLoading(false);
      }
    };

    loadDocument();

    return () => {
      client.destroy();
    };
  }, [documentId]);

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

  // 更新编辑器内容（同步时使用）
  const updateEditorContent = useCallback((newContent: string) => {
    if (!editorRef.current) return;
    
    editorRef.current.update(() => {
      const root = $getRoot();
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

  // 保存功能
  const handleSave = useCallback(async (contentToSave?: string) => {
    const saveContent = contentToSave || content;
    if (!onSave) return;
    
    setIsSaving(true);
    try {
      await onSave(saveContent);
      
      // 同步到 ShareDB
      if (sharedbClientRef.current && isOnline) {
        const result = await sharedbClientRef.current.syncDocument(saveContent);
        if (result.success) {
          setDocumentState(prev => prev ? { ...prev, version: result.version, content: result.content } : null);
          setLastSyncTime(new Date());
        }
      }
      
      setHasUnsavedChanges(false);
      toast.success('文档已保存');
    } catch (error) {
      console.error('Failed to save:', error);
      toast.error('保存失败');
    } finally {
      setIsSaving(false);
    }
  }, [content, onSave, isOnline]);

  // 手动保存按钮
  const handleManualSave = useCallback(() => {
    if (hasUnsavedChanges && !isSaving) {
      handleSave(content);
    }
  }, [content, hasUnsavedChanges, isSaving, handleSave]);

  // 同步文档
  const handleSync = useCallback(async () => {
    if (!sharedbClientRef.current) return;
    
    try {
      const result = await sharedbClientRef.current.syncDocument(content);
      if (result.success) {
        setIsOnline(true);
        setLastSyncTime(new Date());
        
        if (result.content !== content) {
          setContent(result.content);
          updateEditorContent(result.content);
          toast.success('文档已同步，内容已更新');
        } else {
          toast.success('文档已同步');
        }
        
        // 更新文档状态
        setDocumentState(prev => prev ? { ...prev, version: result.version, content: result.content } : null);
      }
    } catch (error) {
      console.error('Sync failed:', error);
      setIsOnline(false);
      toast.error('同步失败');
    }
  }, [content, updateEditorContent]);

  // 处理同步回调
  const handleSyncCallback = useCallback((syncedContent: string, version: number) => {
    if (syncedContent !== content) {
      setContent(syncedContent);
      updateEditorContent(syncedContent);
      setDocumentState(prev => prev ? { ...prev, version, content: syncedContent } : null);
      setLastSyncTime(new Date());
    }
  }, [content, updateEditorContent]);

  // 保存编辑器引用
  const saveEditorRef = useCallback((editor: any) => {
    editorRef.current = editor;
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
        </div>

        {/* 右侧：操作按钮和设置 */}
        <div className="flex items-center space-x-2">
          {/* 自动功能开关 */}
          <div className="flex items-center space-x-2 text-sm">
            <label className="flex items-center space-x-1">
              <input
                type="checkbox"
                checked={autoSaveEnabled}
                onChange={(e) => setAutoSaveEnabled(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span className="text-gray-600">自动保存</span>
            </label>
            <label className="flex items-center space-x-1">
              <input
                type="checkbox"
                checked={autoSyncEnabled}
                onChange={(e) => setAutoSyncEnabled(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span className="text-gray-600">自动同步</span>
            </label>
          </div>
          
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
                
                {/* 实时同步插件 */}
                {sharedbClientRef.current && (
                  <RealtimeSyncPlugin
                    sharedbClient={sharedbClientRef.current}
                    onSync={handleSyncCallback}
                    isOnline={isOnline}
                    setIsOnline={setIsOnline}
                    autoSyncEnabled={autoSyncEnabled}
                    syncInterval={syncInterval}
                  />
                )}
                
                {/* 自动保存插件 */}
                <AutoSavePlugin
                  onSave={handleSave}
                  content={content}
                  isEnabled={autoSaveEnabled}
                  saveDelay={1000}
                />
                
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
          {autoSyncEnabled && (
            <span className="text-blue-600">● 自动同步已启用</span>
          )}
          {autoSaveEnabled && (
            <span className="text-green-600">● 自动保存已启用</span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <span>Lexical 编辑器</span>
          <span>•</span>
          <span>ShareDB 协作</span>
          <span>•</span>
          <span>{isOnline ? '在线' : '离线'}</span>
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