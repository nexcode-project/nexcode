import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { useAuthStore } from '@/store/authStore';
import { CollaborativeLexicalEditor } from '@/components/CollaborativeLexicalEditor';
import { api } from '@/lib/api';
import { toast } from 'react-hot-toast';
import { Edit2, Save, X } from 'lucide-react';

interface Document {
  id: number;
  title: string;
  content: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export default function DocumentEdit() {
  const router = useRouter();
  const { id } = router.query;
  const { isAuthenticated, isLoading } = useAuthStore();
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState('');
  const [savingTitle, setSavingTitle] = useState(false);

  // 获取文档信息
  useEffect(() => {
    if (!id || !isAuthenticated) return;

    const fetchDocument = async () => {
      try {
        const response = await api.get(`/v1/documents/${id}`);
        setDocument(response.data);
        setTitleValue(response.data.title);
      } catch (error) {
        console.error('Failed to fetch document:', error);
        toast.error('获取文档失败');
        router.push('/documents');
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
  }, [id, isAuthenticated, router]);

  // 开始编辑标题
  const handleStartEditTitle = () => {
    setIsEditingTitle(true);
    setTitleValue(document?.title || '');
  };

  // 取消编辑标题
  const handleCancelEditTitle = () => {
    setIsEditingTitle(false);
    setTitleValue(document?.title || '');
  };

  // 保存标题
  const handleSaveTitle = async () => {
    if (!document || !titleValue.trim()) return;

    setSavingTitle(true);
    try {
      await api.put(`/v1/documents/${document.id}`, {
        title: titleValue.trim(),
        content: document.content
      });
      
      // 更新本地状态
      setDocument(prev => prev ? { ...prev, title: titleValue.trim() } : null);
      setIsEditingTitle(false);
      toast.success('标题已保存');
    } catch (error) {
      console.error('Failed to save title:', error);
      toast.error('保存标题失败');
    } finally {
      setSavingTitle(false);
    }
  };

  // 保存文档函数
  const handleSaveDocument = async (content: string) => {
    if (!document) return;

    try {
      await api.put(`/v1/documents/${document.id}`, {
        title: document.title,
        content
      });
      // 更新本地状态
      setDocument(prev => prev ? { ...prev, content } : null);
    } catch (error) {
      console.error('Failed to save document:', error);
      throw error; // 重新抛出错误，让组件处理
    }
  };

  // 处理内容变化（用于本地状态更新）
  const handleContentChange = (content: string) => {
    setDocument(prev => prev ? { ...prev, content } : null);
  };

  // 处理标题输入框的键盘事件
  const handleTitleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveTitle();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEditTitle();
    }
  };

  if (isLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    router.push('/login');
    return null;
  }

  if (!document) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">文档不存在</h2>
          <button
            onClick={() => router.push('/documents')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            返回文档列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>{document.title} | NexCode</title>
        <meta name="description" content="协作式 Markdown 文档编辑器" />
      </Head>
      
      {/* 标题编辑区域 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          {isEditingTitle ? (
            <div className="flex items-center space-x-3">
              <input
                type="text"
                value={titleValue}
                onChange={(e) => setTitleValue(e.target.value)}
                onKeyDown={handleTitleKeyDown}
                className="flex-1 text-2xl font-bold text-gray-900 border-2 border-blue-500 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="输入文档标题..."
                autoFocus
              />
              <button
                onClick={handleSaveTitle}
                disabled={savingTitle || !titleValue.trim()}
                className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition-colors"
              >
                <Save className="h-4 w-4" />
                <span>{savingTitle ? '保存中...' : '保存'}</span>
              </button>
              <button
                onClick={handleCancelEditTitle}
                disabled={savingTitle}
                className="flex items-center space-x-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
              >
                <X className="h-4 w-4" />
                <span>取消</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-gray-900 flex-1">
                {document.title}
              </h1>
              <button
                onClick={handleStartEditTitle}
                className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="编辑标题"
              >
                <Edit2 className="h-4 w-4" />
                <span>编辑标题</span>
              </button>
            </div>
          )}
        </div>
      </div>
      
      <CollaborativeLexicalEditor
        documentId={document.id}
        initialContent={document.content}
        onContentChange={handleContentChange}
        onSave={handleSaveDocument}
      />
    </>
  );
} 