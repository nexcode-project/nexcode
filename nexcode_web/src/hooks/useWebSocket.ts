import { useEffect, useRef, useState } from 'react';

interface UseWebSocketOptions {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  token?: string; // 添加 token 参数
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const [connectionStatus, setConnectionStatus] = useState<'Connecting' | 'Open' | 'Closing' | 'Closed'>('Closed');
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<NodeJS.Timeout>();

  const {
    onOpen,
    onClose,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    token
  } = options;

  const connect = () => {
    try {
      // 构建带 token 的 URL
      const wsUrl = token ? `${url}?token=${token}` : url;
      ws.current = new WebSocket(wsUrl);
      setConnectionStatus('Connecting');

      ws.current.onopen = () => {
        setConnectionStatus('Open');
        reconnectAttempts.current = 0;
        onOpen?.();
      };

      ws.current.onclose = () => {
        setConnectionStatus('Closed');
        onClose?.();

        // 自动重连
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          reconnectTimer.current = setTimeout(connect, reconnectInterval);
        }
      };

      ws.current.onerror = (error) => {
        setConnectionStatus('Closed');
        onError?.(error);
      };

      ws.current.onmessage = (event) => {
        setLastMessage(event);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      setConnectionStatus('Closed');
    }
  };

  const sendMessage = (message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };

  const disconnect = () => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }
    ws.current?.close();
  };

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [url]);

  return {
    connectionStatus,
    lastMessage,
    sendMessage,
    disconnect
  };
}
