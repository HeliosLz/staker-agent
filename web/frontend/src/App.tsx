import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import ChatSetup from './pages/ChatSetup';
import Dashboard from './pages/Dashboard';
import Terminal from './pages/Terminal';
import AppLayout from './components/layout/AppLayout';
import AuthTokenModal from './components/AuthTokenModal';
import { api } from './services/api';
import { getAuthToken, clearAuthToken } from './services/authToken';
import { disconnectSocket, reconnectSocket } from './services/socket';

type AuthState = 'checking' | 'authenticated' | 'needs_auth';

function App() {
  const [authState, setAuthState] = useState<AuthState>(
    getAuthToken() ? 'checking' : 'needs_auth',
  );
  const [authKey, setAuthKey] = useState(0);

  useEffect(() => {
    if (authState !== 'checking') return;
    let cancelled = false;
    api.get('/api/auth/check').then(() => {
      if (!cancelled) setAuthState('authenticated');
    }).catch(() => {
      if (!cancelled) {
        clearAuthToken();
        setAuthState('needs_auth');
      }
    });
    return () => { cancelled = true; };
  }, [authState]);

  useEffect(() => {
    const id = api.interceptors.response.use(
      (res) => res,
      (err) => {
        if (err.response?.status === 401) {
          clearAuthToken();
          disconnectSocket();
          setAuthState('needs_auth');
        }
        return Promise.reject(err);
      },
    );
    return () => api.interceptors.response.eject(id);
  }, []);

  const handleAuthenticated = useCallback(() => {
    reconnectSocket();
    setAuthState('authenticated');
    setAuthKey(k => k + 1);
  }, []);

  return (
    <BrowserRouter>
      {authState === 'needs_auth' ? (
        <>
          <AuthTokenModal onAuthenticated={handleAuthenticated} />
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </>
      ) : authState === 'authenticated' ? (
        <Routes key={authKey}>
          <Route path="/" element={<Landing />} />
          <Route path="/setup" element={<ChatSetup />} />
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/terminal" element={<Terminal />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      ) : null}
    </BrowserRouter>
  );
}

export default App;
