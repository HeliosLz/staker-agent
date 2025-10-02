import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import SetupWizard from './pages/SetupWizard';
import Dashboard from './pages/Dashboard';
import Terminal from './pages/Terminal';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/setup" element={<SetupWizard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/terminal" element={<Terminal />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
