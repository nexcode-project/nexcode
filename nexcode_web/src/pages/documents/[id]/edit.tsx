import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { useAuthStore } from '@/store/authStore';
import { CollaborativeLexicalEditor } from '@/components/CollaborativeLexicalEditor';
import { api } from '@/lib/api';
import { toast } from 'react-hot-toast';

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

  // 获取文档信息
  useEffect(() => {
    if (!id || !isAuthenticated) return;

    const fetchDocument = async () => {
      try {
        const response = await api.get(`/v1/documents/${id}`);
        setDocument(response.data);
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
      
      <CollaborativeLexicalEditor
        documentId={document.id}
        initialContent={document.content}
        onContentChange={handleContentChange}
        onSave={handleSaveDocument}
      />
    </>
  );
} 