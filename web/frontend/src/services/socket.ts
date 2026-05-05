import { io, Socket } from 'socket.io-client';
import { getAuthToken } from './authToken';

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    socket = io('/', {
      transports: ['websocket', 'polling'],
      auth: { token: getAuthToken() ?? '' },
      reconnectionDelay: 1000,
      reconnectionDelayMax: 30000,
      randomizationFactor: 0.5,
    });
  }
  return socket;
}

export function reconnectSocket(): void {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
  getSocket();
}

export function disconnectSocket(): void {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}
