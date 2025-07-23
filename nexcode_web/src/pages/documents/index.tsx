import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { useAuthStore } from '@/store/authStore';
import { api } from '@/lib/api';
import { Plus, FileText, Users, Edit, Trash2, ExternalLink } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface Document {
  id: number;
  title: string;
  content: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export default function Documents() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      router.push('/login');
      return;
    }

    if (isAuthenticated) {
      fetchDocuments();
    }
  }, [isAuthenticated, isLoading, router]);

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/v1/documents');
      setDocuments(response.data.documents);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      toast.error('获取文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDocument = async () => {
    try {
      const response = await api.post('/v1/documents', {
        title: '新文档',
        content: ''
      });
      const newDoc = response.data;
      setDocuments(prev => [newDoc, ...prev]);
      router.push(`/documents/${newDoc.id}/collaborate`);
    } catch (error) {
      console.error('Failed to create document:', error);
      toast.error('创建文档失败');
    }
  };

  const handleDeleteDocument = async (id: number) => {
    if (!confirm('确定要删除这个文档吗？')) return;

    try {
      await api.delete(`/v1/documents/${id}`);
      setDocuments(prev => prev.filter(doc => doc.id !== id));
      toast.success('文档已删除');
    } catch (error) {
      console.error('Failed to delete document:', error);
      toast.error('删除文档失败');
    }
  };

  if (isLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>我的文档 | NexCode</title>
      </Head>
      
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* 页面标题和创建按钮 */}
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-gray-900">我的文档</h1>
            <button
              onClick={handleCreateDocument}
              className="flex items-center space-x-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg"
            >
              <Plus className="h-5 w-5" />
              <span>新建文档</span>
            </button>
          </div>

          {/* 文档列表 */}
          {documents.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">还没有文档</h3>
              <p className="text-gray-500 mb-4">创建您的第一个协作文档</p>
              <button
                onClick={handleCreateDocument}
                className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg"
              >
                创建文档
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {documents.map(doc => (
                <div key={doc.id} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-900 truncate">
                        {doc.title}
                      </h3>
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => router.push(`/documents/${doc.id}/edit`)}
                          className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-gray-100"
                          title="全屏编辑"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => router.push(`/documents/${doc.id}/collaborate`)}
                          className="p-2 text-gray-400 hover:text-primary-600 rounded-lg hover:bg-gray-100"
                          title="协作编辑"
                        >
                          <Users className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteDocument(doc.id)}
                          className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-gray-100"
                          title="删除文档"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                    
                    <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                      {doc.content || '空文档'}
                    </p>
                    
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>
                        创建于 {new Date(doc.created_at).toLocaleDateString()}
                      </span>
                      <span>
                        更新于 {new Date(doc.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  
                  <div className="px-6 py-3 bg-gray-50 border-t flex items-center justify-between">
                    <button
                      onClick={() => router.push(`/documents/${doc.id}/edit`)}
                      className="flex items-center space-x-2 text-blue-600 hover:text-blue-700 font-medium"
                    >
                      <ExternalLink className="h-4 w-4" />
                      <span>全屏编辑</span>
                    </button>
                    <button
                      onClick={() => router.push(`/documents/${doc.id}/collaborate`)}
                      className="flex items-center space-x-2 text-primary-600 hover:text-primary-700 font-medium"
                    >
                      <Users className="h-4 w-4" />
                      <span>协作编辑</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
          </>
    );
  }