import { io, Socket } from 'socket.io-client';
import { WebSocketMessage } from '@/types';

export class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(private baseUrl: string = 'ws://localhost:8010') {}

  connect(taskId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Disconnect existing connection
        this.disconnect();

        // Create new WebSocket connection
        this.socket = io(`${this.baseUrl}/api/v1/research/ws/${taskId}`, {
          transports: ['websocket'],
          auth: {
            token: localStorage.getItem('authToken')
          },
          timeout: 10000,
        });

        this.socket.on('connect', () => {
          console.log('WebSocket connected for task:', taskId);
          this.reconnectAttempts = 0;
          resolve();
        });

        this.socket.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          reject(error);
        });

        this.socket.on('disconnect', (reason) => {
          console.log('WebSocket disconnected:', reason);
          this.handleReconnect(taskId);
        });

        this.socket.on('error', (error) => {
          console.error('WebSocket error:', error);
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.reconnectAttempts = 0;
  }

  private handleReconnect(taskId: string): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
      
      setTimeout(() => {
        this.connect(taskId).catch(console.error);
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  onMessage(callback: (message: WebSocketMessage) => void): void {
    if (!this.socket) {
      throw new Error('WebSocket not connected');
    }

    this.socket.on('message', callback);
    this.socket.on('status_update', (data) => {
      callback({ type: 'status_update', data });
    });
    this.socket.on('progress_update', (data) => {
      callback({ type: 'progress_update', data });
    });
    this.socket.on('section_complete', (data) => {
      callback({ type: 'section_complete', data });
    });
    this.socket.on('error_message', (data) => {
      callback({ type: 'error', data });
    });
  }

  offMessage(callback?: (message: WebSocketMessage) => void): void {
    if (!this.socket) return;

    if (callback) {
      this.socket.off('message', callback);
      this.socket.off('status_update', callback);
      this.socket.off('progress_update', callback);
      this.socket.off('section_complete', callback);
      this.socket.off('error_message', callback);
    } else {
      this.socket.off('message');
      this.socket.off('status_update');
      this.socket.off('progress_update');
      this.socket.off('section_complete');
      this.socket.off('error_message');
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getConnectionState(): string {
    if (!this.socket) return 'disconnected';
    return this.socket.connected ? 'connected' : 'disconnected';
  }
}

// Create singleton instance
export const webSocketService = new WebSocketService();

// Alternative implementation using native WebSocket for simpler cases
export class SimpleWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: ((message: WebSocketMessage) => void)[] = [];

  constructor(private baseUrl: string = 'ws://localhost:8010') {}

  connect(taskId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.disconnect();

        const wsUrl = `${this.baseUrl}/api/v1/research/ws/${taskId}`;
        console.log('Attempting to connect to WebSocket:', wsUrl);
        this.ws = new WebSocket(wsUrl);

        let connectionTimeout = setTimeout(() => {
          if (this.ws?.readyState !== WebSocket.OPEN) {
            console.error('WebSocket connection timeout');
            this.ws?.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 5000); // 5 second timeout

        this.ws.onopen = () => {
          console.log('Simple WebSocket connected for task:', taskId);
          clearTimeout(connectionTimeout);
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onerror = (error) => {
          console.error('Simple WebSocket error:', error);
          clearTimeout(connectionTimeout);
          reject(new Error('WebSocket connection failed'));
        };

        this.ws.onclose = (event) => {
          console.log('Simple WebSocket closed:', event.code, event.reason, 'Clean close:', event.wasClean);
          clearTimeout(connectionTimeout);
          
          if (event.code !== 1000 && this.reconnectAttempts === 0) { // Not a normal closure and not already reconnecting
            console.log('WebSocket closed abnormally, attempting to reconnect...');
            this.handleReconnect(taskId);
          }
        };

        this.ws.onmessage = (event) => {
          try {
            console.log('WebSocket message received:', event.data);
            const message: WebSocketMessage = JSON.parse(event.data);
            this.messageHandlers.forEach(handler => handler(message));
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error, 'Raw data:', event.data);
          }
        };

      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    this.reconnectAttempts = 0;
  }

  private handleReconnect(taskId: string): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
      
      setTimeout(() => {
        console.log(`Reconnect attempt ${this.reconnectAttempts} for task ${taskId}`);
        this.connect(taskId).catch((error) => {
          console.error(`Reconnect attempt ${this.reconnectAttempts} failed:`, error);
        });
      }, delay);
    } else {
      console.error('Max WebSocket reconnection attempts reached');
    }
  }

  onMessage(callback: (message: WebSocketMessage) => void): void {
    this.messageHandlers.push(callback);
  }

  offMessage(callback: (message: WebSocketMessage) => void): void {
    const index = this.messageHandlers.indexOf(callback);
    if (index > -1) {
      this.messageHandlers.splice(index, 1);
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  sendMessage(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      throw new Error('WebSocket is not connected');
    }
  }
}

export const simpleWebSocketService = new SimpleWebSocketService();
