import { useState, useEffect } from 'react';
import {
  Activity, Clock, HardDrive, Network, Play, Square, RotateCw,
  CircleDot, AlertTriangle, RefreshCw, Server,
} from 'lucide-react';
import { statusAPI } from '../services/api';

interface Container {
  Name: string;
  Service: string;
  State: string;
  Status: string;
  RunningFor: string;
  Image: string;
  Labels: string;
}

function parseLabel(containers: Container[], key: string): string {
  for (const c of containers) {
    const re = new RegExp(`${key}=([^,]+)`);
    const m = c.Labels?.match(re);
    if (m) return m[1];
  }
  return 'unknown';
}

function stateColor(state: string) {
  if (state === 'running') return 'text-green-600';
  if (state === 'restarting') return 'text-amber-500';
  return 'text-red-500';
}

function stateBg(state: string) {
  if (state === 'running') return 'bg-green-50 border-green-200';
  if (state === 'restarting') return 'bg-amber-50 border-amber-200';
  return 'bg-red-50 border-red-200';
}

function stateLabel(state: string) {
  if (state === 'running') return '运行中';
  if (state === 'restarting') return '同步中';
  if (state === 'exited') return '已停止';
  return state;
}

function roleName(service: string) {
  if (service === 'execution') return '执行层';
  if (service === 'consensus') return '共识层';
  if (service === 'validator') return '验证者';
  return service;
}

function roleIcon(service: string) {
  if (service === 'execution') return <HardDrive className="w-5 h-5 text-blue-500" />;
  if (service === 'consensus') return <Network className="w-5 h-5 text-purple-500" />;
  if (service === 'validator') return <Server className="w-5 h-5 text-pink-500" />;
  return <Activity className="w-5 h-5 text-gray-500" />;
}

export default function Dashboard() {
  const [containers, setContainers] = useState<Container[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const response = await statusAPI.get();
      const data = response.data?.data;
      setContainers(Array.isArray(data) ? data : []);
      setError(null);
      setLastRefresh(new Date());
    } catch {
      setError('无法连接到后端');
    }
  };

  const handleAction = async (action: 'start' | 'stop' | 'restart') => {
    setLoading(true);
    try {
      if (action === 'start') await statusAPI.start();
      if (action === 'stop') await statusAPI.stop();
      if (action === 'restart') await statusAPI.restart();
      await loadStatus();
    } catch {
      setError(`操作失败: ${action}`);
    } finally {
      setLoading(false);
    }
  };

  const network = containers.length > 0 ? parseLabel(containers, 'metrics.network') : '-';
  const runningCount = containers.filter(c => c.State === 'running').length;
  const totalCount = containers.length;
  const allRunning = totalCount > 0 && runningCount === totalCount;
  const anyRestarting = containers.some(c => c.State === 'restarting');

  // Extract client names from images
  const clClient = containers.find(c => c.Service === 'consensus')?.Image?.split(':')[0] || '-';
  const elClient = containers.find(c => c.Service === 'execution')?.Image?.split(':')[0] || '-';

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Overview</h1>
      </div>

      {/* Top stat pills — Polkadot style */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <StatPill
          value={`${runningCount} / ${totalCount}`}
          label="Active Containers"
          color={allRunning ? 'pink' : anyRestarting ? 'amber' : 'red'}
        />
        <StatPill
          value={network}
          label="Network"
          color="pink"
        />
        <StatPill
          value={allRunning ? 'Healthy' : anyRestarting ? 'Syncing' : totalCount === 0 ? 'Offline' : 'Degraded'}
          label="Node Status"
          color={allRunning ? 'pink' : anyRestarting ? 'amber' : 'red'}
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 flex items-center gap-2 text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4" /> {error}
        </div>
      )}

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
        {/* Left: Node Info card */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-semibold text-gray-900">Node Info</h2>
            <div className="flex items-center gap-2">
              {lastRefresh && (
                <span className="text-xs text-gray-400">
                  {lastRefresh.toLocaleTimeString()}
                </span>
              )}
              <button
                onClick={loadStatus}
                className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Ring chart placeholder + info */}
          <div className="flex items-center gap-8">
            {/* Donut ring */}
            <div className="relative w-36 h-36 flex-shrink-0">
              <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
                <circle cx="60" cy="60" r="50" fill="none" stroke="#f3f4f6" strokeWidth="12" />
                {totalCount > 0 && (
                  <circle
                    cx="60" cy="60" r="50" fill="none"
                    stroke={allRunning ? '#ec4899' : anyRestarting ? '#f59e0b' : '#ef4444'}
                    strokeWidth="12"
                    strokeDasharray={`${(runningCount / totalCount) * 314} 314`}
                    strokeLinecap="round"
                  />
                )}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-bold text-gray-900">{runningCount}</span>
                <span className="text-xs text-gray-400">/ {totalCount}</span>
              </div>
            </div>

            {/* Key-value info */}
            <div className="space-y-3 flex-1 text-sm">
              <InfoRow label="执行层" value={elClient} />
              <InfoRow label="共识层" value={clClient} />
              <InfoRow label="网络" value={network} />
              <InfoRow label="容器数" value={`${totalCount} 个`} />
            </div>
          </div>
        </div>

        {/* Right: Actions card */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-6">Actions</h2>
          <div className="space-y-3">
            <ActionButton
              icon={<Play className="w-4 h-4" />}
              label="启动节点"
              sub="Start all containers"
              onClick={() => handleAction('start')}
              disabled={loading}
              color="green"
            />
            <ActionButton
              icon={<Square className="w-4 h-4" />}
              label="停止节点"
              sub="Stop all containers"
              onClick={() => handleAction('stop')}
              disabled={loading}
              color="red"
            />
            <ActionButton
              icon={<RotateCw className="w-4 h-4" />}
              label="重启节点"
              sub="Restart all containers"
              onClick={() => handleAction('restart')}
              disabled={loading}
              color="blue"
            />
          </div>
        </div>
      </div>

      {/* Container table */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Containers</h2>
        {containers.length === 0 ? (
          <p className="text-gray-400 text-sm py-8 text-center">暂无运行中的容器</p>
        ) : (
          <div className="space-y-2">
            {containers.map((c) => (
              <div
                key={c.Name}
                className={`flex items-center justify-between p-4 rounded-xl border ${stateBg(c.State)}`}
              >
                <div className="flex items-center gap-4">
                  {roleIcon(c.Service)}
                  <div>
                    <p className="font-medium text-gray-900 text-sm">{roleName(c.Service)}</p>
                    <p className="text-xs text-gray-500">{c.Image}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="flex items-center gap-1.5 justify-end">
                      <CircleDot className={`w-3.5 h-3.5 ${stateColor(c.State)}`} />
                      <span className={`text-sm font-medium ${stateColor(c.State)}`}>
                        {stateLabel(c.State)}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 flex items-center gap-1 justify-end mt-0.5">
                      <Clock className="w-3 h-3" /> {c.RunningFor}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ---- Sub-components ---- */

function StatPill({ value, label, color }: { value: string; label: string; color: string }) {
  const colors: Record<string, string> = {
    pink: 'bg-pink-50 border-pink-200 text-pink-600',
    amber: 'bg-amber-50 border-amber-200 text-amber-600',
    red: 'bg-red-50 border-red-200 text-red-600',
  };
  const cls = colors[color] || colors.pink;

  return (
    <div className={`rounded-xl border px-5 py-4 ${cls}`}>
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-white/60 flex items-center justify-center">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <p className="text-lg font-bold">{value}</p>
          <p className="text-xs opacity-80">{label}</p>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900 capitalize">{value}</span>
    </div>
  );
}

function ActionButton({
  icon, label, sub, onClick, disabled, color,
}: {
  icon: React.ReactNode; label: string; sub: string;
  onClick: () => void; disabled: boolean; color: string;
}) {
  const base = 'w-full flex items-center gap-3 p-3 rounded-xl border transition-colors text-left';
  const styles: Record<string, string> = {
    green: 'border-green-200 hover:bg-green-50 text-green-700',
    red: 'border-red-200 hover:bg-red-50 text-red-700',
    blue: 'border-blue-200 hover:bg-blue-50 text-blue-700',
  };

  return (
    <button onClick={onClick} disabled={disabled} className={`${base} ${styles[color]} disabled:opacity-50`}>
      <div className="w-8 h-8 rounded-lg bg-white border border-gray-100 flex items-center justify-center flex-shrink-0">
        {icon}
      </div>
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-gray-400">{sub}</p>
      </div>
    </button>
  );
}
