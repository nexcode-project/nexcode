import { useEffect, useRef, useState, useCallback } from 'react';
import { Users, Wifi, WifiOff, Eye, EyeOff, Save, Bot } from 'lucide-react';
import { toast } from 'react-hot-toast';
// import { AIAssistant } from './AIAssistant';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface User {
  id: number;
  username: string;
  avatar?: string;
}

interface MarkdownEditorProps {
  documentId: number;
  initialContent?: string;
  onContentChange?: (content: string) => void;
  onSave?: (content: string) => Promise<void>;
}

export function MarkdownEditor({
  documentId,
  initialContent = '',
  onContentChange,
  onSave
}: MarkdownEditorProps) {
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const [content, setContent] = useState(initialContent);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const [showAI, setShowAI] = useState(false); // 暂时禁用 AI 助手
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // 处理内容变化
  const handleContentChange = useCallback((newContent: string) => {
    setContent(newContent);
    setHasUnsavedChanges(newContent !== initialContent);
    onContentChange?.(newContent);
  }, [initialContent, onContentChange]);

  // 处理编辑器输入
  const handleInput = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    handleContentChange(newContent);
  }, [handleContentChange]);

  // 处理文本选择
  const handleTextSelection = useCallback(() => {
    if (editorRef.current) {
      const start = editorRef.current.selectionStart;
      const end = editorRef.current.selectionEnd;
      const selectedText = content.slice(start, end);
      setSelectedText(selectedText);
    }
  }, [content]);

  // 处理焦点事件
  const handleFocus = useCallback(() => {
    setIsEditing(true);
  }, []);

  const handleBlur = useCallback(() => {
    setIsEditing(false);
  }, []);

  // 保存文档
  const handleSave = useCallback(async () => {
    if (!hasUnsavedChanges || isSaving) return;

    setIsSaving(true);
    try {
      if (onSave) {
        await onSave(content);
        setHasUnsavedChanges(false);
        toast.success('文档已保存');
      }
    } catch (error) {
      console.error('Failed to save document:', error);
      toast.error('保存失败，请重试');
    } finally {
      setIsSaving(false);
    }
  }, [content, hasUnsavedChanges, isSaving, onSave]);

  // 处理键盘快捷键
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    // Ctrl/Cmd + S: 保存
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      handleSave();
    }
    
    // Ctrl/Cmd + Enter: 切换预览模式
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      setIsPreviewMode(prev => !prev);
    }
  }, [handleSave]);

  // 页面离开前提醒保存
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '您有未保存的更改，确定要离开吗？';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  return (
    <div className="markdown-editor h-screen flex flex-col bg-white">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white shadow-sm">
        {/* 左侧：文档状态 */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${hasUnsavedChanges ? 'bg-yellow-500' : 'bg-green-500'}`}></div>
            <span className="text-sm text-gray-600 font-medium">
              {hasUnsavedChanges ? '未保存' : '已保存'}
            </span>
          </div>
          
          {isEditing && (
            <span className="text-sm text-blue-600">正在编辑...</span>
          )}
        </div>

        {/* 右侧：操作按钮 */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsPreviewMode(prev => !prev)}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            title="切换预览模式 (Ctrl+Enter)"
          >
            {isPreviewMode ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            <span>{isPreviewMode ? '编辑' : '预览'}</span>
          </button>
          
          <button
            onClick={handleSave}
            disabled={!hasUnsavedChanges || isSaving}
            className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              hasUnsavedChanges 
                ? 'text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400' 
                : 'text-gray-500 bg-gray-100 cursor-not-allowed'
            }`}
            title="保存文档 (Ctrl+S)"
          >
            <Save className="h-4 w-4" />
            <span>{isSaving ? '保存中...' : '保存'}</span>
          </button>
        </div>
      </div>

      {/* 主要内容区域 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 编辑器区域 */}
        <div className={`flex-1 ${isPreviewMode ? 'hidden' : 'block'}`}>
          <textarea
            ref={editorRef}
            value={content}
            onChange={handleInput}
            onFocus={handleFocus}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            onSelect={handleTextSelection}
            className="w-full h-full p-8 text-gray-900 bg-white resize-none border-none outline-none text-base leading-relaxed"
            placeholder="开始编写您的文档..."
            style={{
              fontSize: '16px',
              lineHeight: '1.8',
              fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
            }}
          />
        </div>

        {/* 预览区域 */}
        <div className={`flex-1 ${isPreviewMode ? 'block' : 'hidden'} overflow-auto`}>
          <div className="p-8 prose prose-lg max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content || '# 开始编写您的文档\n\n在这里输入您的 Markdown 内容...'}
            </ReactMarkdown>
          </div>
        </div>
      </div>

      {/* 底部状态栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-t border-gray-200 text-sm text-gray-600">
        <div className="flex items-center space-x-4">
          <span>字符数: {content.length}</span>
          <span>行数: {content.split('\n').length}</span>
          {hasUnsavedChanges && (
            <span className="text-yellow-600 font-medium">● 有未保存的更改</span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <span>Markdown 编辑器</span>
          <span>•</span>
          <span>本地编辑</span>
        </div>
      </div>
    </div>
  );
} 