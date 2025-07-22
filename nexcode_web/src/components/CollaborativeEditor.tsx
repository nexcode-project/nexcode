import { useEffect, useRef, useState, useCallback } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Users, Wifi, WifiOff } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface User {
  id: number;
  username: string;
  avatar?: string;
}

interface Operation {
  type: 'insert' | 'delete' | 'retain';
  position: number;
  content?: string;
  length?: number;
}

interface CollaborativeEditorProps {
  documentId: number;
  initialContent?: string;
  onContentChange?: (content: string) => void;
}

export function CollaborativeEditor({
  documentId,
  initialContent = '',
  onContentChange
}: CollaborativeEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null);
  const [content, setContent] = useState(initialContent);
  const [onlineUsers, setOnlineUsers] = useState<User[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  // 防抖处理
  const debounceTimer = useRef<NodeJS.Timeout>();
  const lastSentContent = useRef(initialContent);

  // 获取 token
  const token = typeof window !== 'undefined' ? localStorage.getItem('session_token') : null;

  const wsUrl = `ws://localhost:8000/v1/documents/${documentId}/collaborate`;

  const { sendMessage, lastMessage, connectionStatus } = useWebSocket(wsUrl, {
    token: token || undefined, // 传递 token
    onOpen: () => {
      toast.success('已连接到协作服务');
    },
    onClose: () => {
      toast.error('与协作服务断开连接');
    },
    onError: () => {
      toast.error('连接协作服务失败');
    }
  });

  // 计算操作差异
  const calculateOperation = useCallback((oldContent: string, newContent: string): Operation | null => {
    if (oldContent === newContent) return null;

    // 找到第一个不同的位置
    let start = 0;
    while (start < Math.min(oldContent.length, newContent.length) &&
      oldContent[start] === newContent[start]) {
      start++;
    }

    // 找到最后一个不同的位置
    let oldEnd = oldContent.length;
    let newEnd = newContent.length;
    while (oldEnd > start && newEnd > start &&
      oldContent[oldEnd - 1] === newContent[newEnd - 1]) {
      oldEnd--;
      newEnd--;
    }

    // 确定操作类型
    if (oldEnd === start && newEnd > start) {
      // 插入操作
      return {
        type: 'insert',
        position: start,
        content: newContent.slice(start, newEnd)
      };
    } else if (newEnd === start && oldEnd > start) {
      // 删除操作
      return {
        type: 'delete',
        position: start,
        length: oldEnd - start
      };
    } else if (oldEnd > start && newEnd > start) {
      // 替换操作（先删除再插入）
      return {
        type: 'insert',
        position: start,
        content: newContent.slice(start, newEnd)
      };
    }

    return null;
  }, []);

  // 处理内容变化
  const handleContentChange = useCallback((newContent: string) => {
    setContent(newContent);
    onContentChange?.(newContent);

    // 防抖发送完整内容
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      sendMessage({
        type: 'content_update',
        content: newContent
      });
      lastSentContent.current = newContent;
    }, 500); // 增加防抖时间，避免频繁发送
  }, [sendMessage, onContentChange]);

  // 应用远程操作
  const applyRemoteOperation = useCallback((operation: Operation) => {
    setContent(prevContent => {
      let newContent = prevContent;

      switch (operation.type) {
        case 'insert':
          newContent = prevContent.slice(0, operation.position) +
            (operation.content || '') +
            prevContent.slice(operation.position);
          break;
        case 'delete':
          newContent = prevContent.slice(0, operation.position) +
            prevContent.slice(operation.position + (operation.length || 0));
          break;
      }

      // 更新编辑器内容
      if (editorRef.current && !isEditing) {
        editorRef.current.innerHTML = newContent;
      }

      lastSentContent.current = newContent;
      onContentChange?.(newContent);
      return newContent;
    });
  }, [isEditing, onContentChange]);

  // 处理WebSocket消息
  useEffect(() => {
    if (!lastMessage) return;

    try {
      const message = JSON.parse(lastMessage.data);

      switch (message.type) {
        case 'connected':
          // 设置当前用户信息
          setCurrentUser(message.user);
          break;
        case 'operation':
          applyRemoteOperation(message.operation);
          break;
        case 'content_update':
          // 处理完整内容更新
          if (message.sender_id !== currentUser?.id) { // 避免自己发送的内容更新自己
            setContent(message.content);
            lastSentContent.current = message.content;
            onContentChange?.(message.content);
            
            // 更新编辑器内容
            if (editorRef.current && !isEditing) {
              editorRef.current.innerHTML = message.content;
            }
          }
          break;
        case 'user_joined':
          setOnlineUsers(prev => {
            if (prev.find(u => u.id === message.user.id)) return prev;
            return [...prev, message.user];
          });
          toast.success(`${message.user.username} 加入了协作`);
          break;
        case 'user_left':
          setOnlineUsers(prev => prev.filter(u => u.id !== message.user_id));
          break;
        case 'online_users':
          setOnlineUsers(message.users);
          break;
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, [lastMessage, applyRemoteOperation]);

  // 处理编辑器输入
  const handleInput = useCallback((e: React.FormEvent<HTMLDivElement>) => {
    const newContent = e.currentTarget.textContent || '';
    handleContentChange(newContent);
  }, [handleContentChange]);

  // 处理焦点事件
  const handleFocus = useCallback(() => {
    setIsEditing(true);
  }, []);

  const handleBlur = useCallback(() => {
    setIsEditing(false);
  }, []);

  return (
    <div className="collaborative-editor h-full flex flex-col">
      {/* 工具栏 */}
      <div className="flex items-center justify-between p-4 border-b bg-white">
        {/* 在线用户 */}
        <div className="flex items-center space-x-2">
          <Users className="h-5 w-5 text-gray-500" />
          <span className="text-sm text-gray-600">
            {onlineUsers.length} 人在线
          </span>
          <div className="flex -space-x-2">
            {onlineUsers.slice(0, 5).map(user => (
              <div
                key={user.id}
                className="w-8 h-8 rounded-full bg-primary-500 text-white text-xs flex items-center justify-center border-2 border-white"
                title={user.username}
              >
                {user.username.charAt(0).toUpperCase()}
              </div>
            ))}
            {onlineUsers.length > 5 && (
              <div className="w-8 h-8 rounded-full bg-gray-400 text-white text-xs flex items-center justify-center border-2 border-white">
                +{onlineUsers.length - 5}
              </div>
            )}
          </div>
        </div>

        {/* 连接状态 */}
        <div className="flex items-center space-x-2">
          {connectionStatus === 'Open' ? (
            <>
              <Wifi className="h-4 w-4 text-green-500" />
              <span className="text-sm text-green-600">已连接</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-red-500" />
              <span className="text-sm text-red-600">
                {connectionStatus === 'Connecting' ? '连接中...' : '已断开'}
              </span>
            </>
          )}
        </div>
      </div>

      {/* 编辑器 */}
      <div className="flex-1 p-4 bg-gray-50">
        <div
          ref={editorRef}
          contentEditable
          className="w-full h-full p-6 bg-white rounded-lg shadow-sm border focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          style={{
            minHeight: '500px',
            lineHeight: '1.6',
            fontSize: '16px'
          }}
          onInput={handleInput}
          onFocus={handleFocus}
          onBlur={handleBlur}
          dangerouslySetInnerHTML={{ __html: content }}
          data-placeholder="开始输入文档内容..."
        />
      </div>
    </div>
  );
}
