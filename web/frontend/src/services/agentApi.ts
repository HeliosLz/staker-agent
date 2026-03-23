import { api } from './api';

export const agentAPI = {
  setApiKey: (apiKey: string) =>
    api.post('/api/agent/apikey', { api_key: apiKey }),
  getApiKeyStatus: () =>
    api.get<{ configured: boolean }>('/api/agent/apikey/status'),
};
