const STORAGE_KEY = 'staker_agent_auth_token';

export function getAuthToken(): string | null {
  return sessionStorage.getItem(STORAGE_KEY);
}

export function setAuthToken(token: string): void {
  sessionStorage.setItem(STORAGE_KEY, token);
}

export function clearAuthToken(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}
