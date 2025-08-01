import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import { toast } from 'react-hot-toast';
import { ArrowLeft, Share, Users, Save, Edit2, X, User, Settings, LogOut, ChevronDown } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
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
  const [titleValue, setTitleValue] = useState('');
  const [currentLexicalContent, setCurrentLexicalContent] = useState<string>('');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // 获取文档信息 - 只获取一次，然后传递给编辑器
  useEffect(() => {
    if (!id || !isAuthenticated) return;

    const fetchDocument = async () => {
      try {
        const response = await api.get(`/v1/documents/${id}`);
        const doc = response.data;
        setDocument(doc);
        setTitleValue(doc.title);
        // Initialize currentLexicalContent with existing document content
        // This ensures the save button is enabled for existing documents
        setCurrentLexicalContent(doc.content || '');
        
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

  const handleSaveTitle = async (newTitle: string) => {
    if (!document || !newTitle.trim()) return;


    try {
      // 先更新标题
      await api.put(`/v1/documents/${document.id}`, {
        title: newTitle.trim(),
        content: document.content
      });
      
      // 更新本地状态
      setDocument(prev => prev ? { ...prev, title: newTitle.trim() } : null);
      toast.success('标题已保存');

    } catch (error) {
      console.error('Failed to save title:', error);
      toast.error('保存标题失败');
    }
  };

  // 处理标题编辑事件
  const handleTitleChange = (e: React.FormEvent<HTMLHeadingElement>) => {
    const newTitle = e.currentTarget.textContent || '';
    setTitleValue(newTitle);
  };

  const handleTitleBlur = () => {
    if (titleValue.trim() && titleValue !== document?.title) {
      handleSaveTitle(titleValue);
    }
  };

  const handleTitleKeyDown = (e: React.KeyboardEvent<HTMLHeadingElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.currentTarget.blur(); // 触发blur事件，自动保存
    } else if (e.key === 'Escape') {
      e.preventDefault();
      e.currentTarget.textContent = document?.title || '';
      e.currentTarget.blur();
    }
  };

  // 保存文档（创建新版本）
  const handleSave = async (content?: string) => {
    if (!document) return;

    // 使用传入的content参数，如果没有则使用当前Lexical内容，最后回退到文档原始内容
    const contentToSave = content || currentLexicalContent || document.content;
    
    if (!contentToSave) {
      toast.error('没有内容可保存');
      return;
    }

    setSaving(true);
    try {
      // 使用ShareDB服务同步并创建版本
      const response = await api.post('/v1/sharedb/documents/sync', {
        doc_id: document.id.toString(),
        version: documentState?.version || 0,
        content: contentToSave,
        create_version: true  // 强制创建新版本
      });
      
      if (response.data.success) {
        // 更新本地状态
        setDocumentState(prev => prev ? {
          ...prev,
          content: response.data.content,
          version: response.data.version
        } : null);
        toast.success('文档已保存为新版本');
      } else {
        toast.error('保存失败: ' + (response.data.error || '未知错误'));
      }
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

  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  // 点击外部关闭用户菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    window.addEventListener('mousedown', handleClickOutside);
    return () => {
      window.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

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
        {/* 协作编辑器 */}
        {documentState && (
          <CollaborativeLexicalEditor
            documentId={parseInt(id as string)}
            initialContent={documentState.content}
            initialDocumentState={documentState}
            onContentChange={(content: string) => {
              // 这里content是纯文本，用于预览
              setDocument(prev => prev ? { ...prev, content } : null);
            }}
            onSave={handleSave}
            onLexicalContentChange={(lexicalContent: string) => {
              // 这里lexicalContent是Lexical JSON格式
              setCurrentLexicalContent(lexicalContent);
            }}
            // 传递额外的功能
            documentTitle={document.title}
            onTitleChange={handleTitleChange}
            onTitleBlur={handleTitleBlur}
            onTitleKeyDown={handleTitleKeyDown}
            onBack={handleBack}
            onShare={handleShare}
            saving={saving}
            currentLexicalContent={currentLexicalContent}
            user={user}
            onLogout={handleLogout}
            showUserMenu={showUserMenu}
            setShowUserMenu={setShowUserMenu}
            userMenuRef={userMenuRef}
          />
        )}
      </div>
    </>
  );
}