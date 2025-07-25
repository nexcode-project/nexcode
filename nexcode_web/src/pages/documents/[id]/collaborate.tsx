import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { toast } from 'react-hot-toast';
import { ArrowLeft, Share, Users, Save } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import Layout from '@/components/Layout';
import { CollaborativeLexicalEditor } from '@/components/CollaborativeLexicalEditor';

// 导入类型
import type { Document } from '@/types/api';
import type { DocumentState } from '@/services/sharedb';

export default function DocumentCollaborate() {
  const router = useRouter();
  const { id } = router.query;
  const { isAuthenticated, isLoading } = useAuthStore();
  const [document, setDocument] = useState<Document | null>(null);
  const [documentState, setDocumentState] = useState<DocumentState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // 获取文档信息 - 只获取一次，然后传递给编辑器
  useEffect(() => {
    if (!id || !isAuthenticated) return;

    const fetchDocument = async () => {
      try {
        const response = await api.get(`/v1/documents/${id}`);
        const doc = response.data;
        setDocument(doc);
        
        // 将文档信息转换为DocumentState格式
        setDocumentState({
          doc_id: doc.id.toString(),
          content: doc.content || '',
          version: 1, // 初始版本
          created_at: doc.created_at,
          updated_at: doc.updated_at
        });
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

  // 保存文档
  const handleSave = async (content: string) => {
    if (!document) return;

    setSaving(true);
    try {
      await api.put(`/v1/documents/${document.id}`, {
        title: document.title,
        content
      });
      toast.success('文档已保存');
    } catch (error) {
      console.error('Failed to save document:', error);
      toast.error('保存文档失败');
    } finally {
      setSaving(false);
    }
  };

  // 分享文档
  const handleShare = async () => {
    if (!document) return;

    try {
      await navigator.clipboard.writeText(window.location.href);
      toast.success('协作链接已复制到剪贴板');
    } catch (error) {
      toast.error('复制链接失败');
    }
  };

  // 返回文档列表
  const handleBack = () => {
    router.push('/documents');
  };

  if (isLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    router.push('/login');
    return null;
  }

  if (!document) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">文档不存在</h2>
          <button
            onClick={handleBack}
            className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg"
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
        <title>{document.title} - 协作编辑 | NexCode</title>
      </Head>
      
      <div className="min-h-screen bg-gray-50">
        {/* 顶部导航 */}
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleBack}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                >
                  <ArrowLeft className="h-5 w-5" />
                </button>
                <h1 className="text-xl font-semibold text-gray-900">
                  {document.title}
                </h1>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleShare}
                  className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
                >
                  <Share className="h-4 w-4" />
                  <span>分享</span>
                </button>
                
                <button
                  onClick={() => handleSave(document.content)}
                  disabled={saving}
                  className="flex items-center space-x-2 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white px-4 py-2 rounded-lg"
                >
                  <Save className="h-4 w-4" />
                  <span>{saving ? '保存中...' : '保存'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 协作编辑器 */}
        {documentState && (
          <CollaborativeLexicalEditor
            documentId={parseInt(id as string)}
            initialContent={documentState.content}
            initialDocumentState={documentState}
            onContentChange={(content: string) => {
              setDocument(prev => prev ? { ...prev, content } : null);
            }}
            onSave={handleSave}
          />
        )}
      </div>
    </>
  );
}