import { useState, useEffect } from 'react';
import { getSocket } from '../services/socket';
import type { HealthReport, HealthAlert } from '../types';

export function useHealthMonitor() {
  const [report, setReport] = useState<HealthReport | null>(null);
  const [alerts, setAlerts] = useState<HealthAlert[]>([]);

  useEffect(() => {
    const socket = getSocket();
    socket.emit('subscribe_health', {});

    socket.on('health_update', (data: HealthReport) => {
      setReport(data);
    });

    socket.on('health_alert', (data: HealthAlert) => {
      setAlerts(prev => [{ ...data, timestamp: data.timestamp ?? Date.now() / 1000 }, ...prev].slice(0, 50));
    });

    return () => {
      socket.emit('unsubscribe_health', {});
      socket.off('health_update');
      socket.off('health_alert');
    };
  }, []);

  return { report, alerts };
}
