import { useEffect, useState, useCallback } from 'react';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { PlainTextPlugin } from '@lexical/react/LexicalPlainTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { MarkdownShortcutPlugin } from '@lexical/react/LexicalMarkdownShortcutPlugin';
import { TRANSFORMERS } from '@lexical/markdown';
import { $generateHtmlFromNodes, $generateNodesFromDOM } from '@lexical/html';
import { $getRoot, $insertNodes, EditorState } from 'lexical';
import { Eye, EyeOff, Save, Users } from 'lucide-react';
import { toast } from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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

// 自动保存插件
function AutoSavePlugin({ 
  onSave, 
  hasUnsavedChanges, 
  setHasUnsavedChanges 
}: {
  onSave: (content: string) => Promise<void>;
  hasUnsavedChanges: boolean;
  setHasUnsavedChanges: (value: boolean) => void;
}) {
  const [editor] = useLexicalComposerContext();
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = useCallback(async () => {
    if (!hasUnsavedChanges || isSaving) return;

    setIsSaving(true);
    try {
      editor.update(() => {
        const root = $getRoot();
        const content = root.getTextContent();
        onSave(content).then(() => {
          setHasUnsavedChanges(false);
          toast.success('文档已保存');
        }).catch((error) => {
          console.error('Failed to save:', error);
          toast.error('保存失败');
        });
      });
    } finally {
      setIsSaving(false);
    }
  }, [editor, hasUnsavedChanges, isSaving, onSave, setHasUnsavedChanges]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        handleSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSave]);

  return null;
}

interface LexicalEditorProps {
  documentId: number;
  initialContent?: string;
  onContentChange?: (content: string) => void;
  onSave?: (content: string) => Promise<void>;
}

export function LexicalEditor({
  documentId,
  initialContent = '',
  onContentChange,
  onSave
}: LexicalEditorProps) {
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [content, setContent] = useState(initialContent);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // 编辑器初始配置
  const initialConfig = {
    namespace: 'NexCodeEditor',
    theme,
    onError: (error: Error) => {
      console.error('Lexical Error:', error);
      toast.error('编辑器错误');
    },
    editorState: undefined,
  };

  // 处理内容变化
  const handleContentChange = useCallback((editorState: EditorState) => {
    editorState.read(() => {
      const root = $getRoot();
      const textContent = root.getTextContent();
      
      if (textContent !== content) {
        setContent(textContent);
        setHasUnsavedChanges(textContent !== initialContent);
        onContentChange?.(textContent);
      }
    });
  }, [content, initialContent, onContentChange]);

  // 保存功能
  const handleSave = useCallback(async (contentToSave: string) => {
    if (!onSave) return;
    
    setIsSaving(true);
    try {
      await onSave(contentToSave);
      setHasUnsavedChanges(false);
      toast.success('文档已保存');
    } catch (error) {
      console.error('Failed to save:', error);
      toast.error('保存失败');
    } finally {
      setIsSaving(false);
    }
  }, [onSave]);

  // 手动保存按钮
  const handleManualSave = useCallback(() => {
    if (hasUnsavedChanges && !isSaving) {
      handleSave(content);
    }
  }, [content, hasUnsavedChanges, isSaving, handleSave]);

  return (
    <div className="lexical-editor h-screen flex flex-col bg-white">
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
        </div>

        {/* 右侧：操作按钮 */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsPreviewMode(prev => !prev)}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            title="切换预览模式"
          >
            {isPreviewMode ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            <span>{isPreviewMode ? '编辑' : '预览'}</span>
          </button>
          
          <button
            onClick={handleManualSave}
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
        {!isPreviewMode && (
          <div className="flex-1">
            <LexicalComposer initialConfig={initialConfig}>
              <div className="editor-container h-full">
                <PlainTextPlugin
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
                <AutoSavePlugin 
                  onSave={handleSave}
                  hasUnsavedChanges={hasUnsavedChanges}
                  setHasUnsavedChanges={setHasUnsavedChanges}
                />
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
        </div>
        <div className="flex items-center space-x-2">
          <span>Lexical 编辑器</span>
          <span>•</span>
          <span>Markdown 支持</span>
        </div>
      </div>
    </div>
  );
} 