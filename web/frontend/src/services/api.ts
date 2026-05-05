import axios from 'axios';
import { getAuthToken } from './authToken';

const API_BASE_URL = '';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 环境检测
export const envAPI = {
  check: () => api.get('/api/env/check'),
};

// 配置管理
export const configAPI = {
  getNetworks: () => api.get('/api/config/networks'),
  getClients: () => api.get('/api/config/clients'),
  generate: (data: { network: string; client: string }) =>
    api.post('/api/config/generate', data),
};

// 部署管理
export const deployAPI = {
  full: (data: object, socketId?: string) =>
    api.post('/api/deploy/full', data, {
      headers: socketId ? { 'X-Socket-ID': socketId } : {},
    }),
  generateKeys: (data: { network: string; num_validators: number; withdrawal_address: string }, socketId?: string) =>
    api.post('/api/deploy/keys/generate', data, {
      headers: socketId ? { 'X-Socket-ID': socketId } : {},
    }),
  importKeys: (keysPath: string) =>
    api.post('/api/deploy/keys/import', { keys_path: keysPath }),
  start: () => api.post('/api/deploy/start'),
  getLidoCsmInfo: (network: string) =>
    api.get('/api/deploy/lido-csm/info', { params: { network } }),
};

// 节点状态
export const statusAPI = {
  get: () => api.get('/api/status'),
  getLogs: (service: string = 'consensus', lines: number = 100) =>
    api.get('/api/status/logs', { params: { service, lines } }),
  start: () => api.post('/api/status/start'),
  stop: () => api.post('/api/status/stop'),
  restart: () => api.post('/api/status/restart'),
};

// 健康检查
export const healthAPI = {
  check: () => api.get('/api/health'),
};

// Monitor (Phase 2)
export const monitorAPI = {
  getHealth: () => api.get('/api/monitor'),
  getAlerts: () => api.get('/api/monitor/alerts'),
  getEvents: () => api.get('/api/monitor/events'),
};
