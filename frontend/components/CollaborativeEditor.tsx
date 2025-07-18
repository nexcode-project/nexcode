import { useEffect, useRef, useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';

interface Operation {
  type: 'insert' | 'delete' | 'retain';
  position: number;
  content?: string;
  length?: number;
}

export function CollaborativeEditor({ documentId }: { documentId: number }) {
  const editorRef = useRef<HTMLDivElement>(null);
  const [content, setContent] = useState('');
  const [onlineUsers, setOnlineUsers] = useState<User[]>([]);
  const wsUrl = `ws://localhost:8000/v1/documents/${documentId}/collaborate`;
  
  const { sendMessage, lastMessage, connectionStatus } = useWebSocket(wsUrl);
  
  // 防抖处理用户输入
  const debounceTimer = useRef<NodeJS.Timeout>();
  
  const handleContentChange = (newContent: string) => {
    setContent(newContent);
    
    // 计算操作差异
    const operation = calculateOperation(content, newContent);
    
    // 防抖发送操作
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    
    debounceTimer.current = setTimeout(() => {
      sendMessage({
        type: 'operation',
        operation
      });
    }, 300);
  };
  
  const calculateOperation = (oldContent: string, newContent: string): Operation => {
    // 简化的差异计算，实际需要更精确的算法
    if (newContent.length > oldContent.length) {
      // 插入操作
      const position = findInsertPosition(oldContent, newContent);
      return {
        type: 'insert',
        position,
        content: newContent.slice(position, position + (newContent.length - oldContent.length))
      };
    } else if (newContent.length < oldContent.length) {
      // 删除操作
      const position = findDeletePosition(oldContent, newContent);
      return {
        type: 'delete',
        position,
        length: oldContent.length - newContent.length
      };
    }
    
    return { type: 'retain', position: 0 };
  };
  
  // 处理WebSocket消息
  useEffect(() => {
    if (!lastMessage) return;
    
    const message = JSON.parse(lastMessage.data);
    
    switch (message.type) {
      case 'operation':
        applyRemoteOperation(message.operation);
        break;
      case 'user_joined':
        setOnlineUsers(prev => [...prev, message.user]);
        break;
      case 'user_left':
        setOnlineUsers(prev => prev.filter(u => u.id !== message.user_id));
        break;
      case 'online_users':
        setOnlineUsers(message.users);
        break;
    }
  }, [lastMessage]);
  
  const applyRemoteOperation = (operation: Operation) => {
    let newContent = content;
    
    switch (operation.type) {
      case 'insert':
        newContent = content.slice(0, operation.position) + 
                    operation.content + 
                    content.slice(operation.position);
        break;
      case 'delete':
        newContent = content.slice(0, operation.position) + 
                    content.slice(operation.position + operation.length!);
        break;
    }
    
    setContent(newContent);
    
    // 更新编辑器内容
    if (editorRef.current) {
      editorRef.current.innerHTML = newContent;
    }
  };
  
  return (
    <div className="collaborative-editor">
      {/* 在线用户显示 */}
      <div className="online-users">
        {onlineUsers.map(user => (
          <div key={user.id} className="user-avatar">
            {user.username}
          </div>
        ))}
      </div>
      
      {/* 连接状态 */}
      <div className="connection-status">
        状态: {connectionStatus}
      </div>
      
      {/* 编辑器 */}
      <div
        ref={editorRef}
        contentEditable
        className="editor-content"
        onInput={(e) => handleContentChange(e.currentTarget.textContent || '')}
        dangerouslySetInnerHTML={{ __html: content }}
      />
    </div>
  );
}