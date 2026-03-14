import { useState, useEffect } from 'react';
import { Activity, Clock, DollarSign, HardDrive, Network, Play, Square, RotateCw } from 'lucide-react';
import { statusAPI } from '../services/api';

export default function Dashboard() {
  const [, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const response = await statusAPI.get();
      setStatus(response.data.data);
    } catch (error) {
      console.error('Failed to load status:', error);
    }
  };

  const handleAction = async (action: 'start' | 'stop' | 'restart') => {
    setLoading(true);
    try {
      if (action === 'start') await statusAPI.start();
      if (action === 'stop') await statusAPI.stop();
      if (action === 'restart') await statusAPI.restart();
      await loadStatus();
    } catch (error) {
      console.error(`Failed to ${action}:`, error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">节点仪表盘</h1>
            <p className="text-gray-600 mt-1">
              Holesky • Lighthouse
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleAction('start')}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              <Play className="w-4 h-4" /> 启动
            </button>
            <button
              onClick={() => handleAction('stop')}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              <Square className="w-4 h-4" /> 停止
            </button>
            <button
              onClick={() => handleAction('restart')}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <RotateCw className="w-4 h-4" /> 重启
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <StatCard
            icon={<Activity className="w-8 h-8 text-green-600" />}
            title="状态"
            value="运行中"
            color="green"
          />
          <StatCard
            icon={<Clock className="w-8 h-8 text-blue-600" />}
            title="运行时间"
            value="2h 34m"
            color="blue"
          />
          <StatCard
            icon={<DollarSign className="w-8 h-8 text-yellow-600" />}
            title="余额"
            value="0.032 ETH"
            color="yellow"
          />
          <StatCard
            icon={<Activity className="w-8 h-8 text-purple-600" />}
            title="同步进度"
            value="95.2%"
            color="purple"
          />
          <StatCard
            icon={<HardDrive className="w-8 h-8 text-orange-600" />}
            title="磁盘使用"
            value="45%"
            color="orange"
          />
          <StatCard
            icon={<Network className="w-8 h-8 text-indigo-600" />}
            title="节点连接"
            value="8 peers"
            color="indigo"
          />
        </div>

        {/* Sync Progress */}
        <div className="bg-white rounded-xl p-6 shadow-sm mb-8">
          <h3 className="text-lg font-semibold mb-4">📈 同步进度</h3>
          <div className="relative pt-1">
            <div className="overflow-hidden h-4 text-xs flex rounded-full bg-gray-200">
              <div
                style={{ width: '95.2%' }}
                className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-600 transition-all duration-500"
              />
            </div>
            <p className="text-sm text-gray-600 mt-2">95.2% - 预计 30 分钟完成</p>
          </div>
        </div>

        {/* Logs */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">📜 实时日志</h3>
            <div className="flex gap-2">
              <button className="text-sm text-blue-600 hover:underline">全屏</button>
              <button className="text-sm text-blue-600 hover:underline">暂停</button>
            </div>
          </div>
          <div className="bg-gray-900 text-green-400 font-mono text-sm p-4 rounded-lg h-64 overflow-y-auto">
            <div>INFO: Syncing block 1234567</div>
            <div>INFO: Connected to 8 peers</div>
            <div>INFO: Downloading blocks...</div>
            <div>INFO: Memory usage: 2.1GB / 8GB</div>
            <div>INFO: Attestation successful</div>
            <div className="flex items-center">
              <span className="animate-pulse">▌</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, title, value, color }: any) {
  const colorClasses: any = {
    green: 'bg-green-50 border-green-200',
    blue: 'bg-blue-50 border-blue-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    purple: 'bg-purple-50 border-purple-200',
    orange: 'bg-orange-50 border-orange-200',
    indigo: 'bg-indigo-50 border-indigo-200',
  };

  return (
    <div className={`rounded-xl p-6 border ${colorClasses[color] || 'bg-gray-50 border-gray-200'}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
        </div>
        {icon}
      </div>
    </div>
  );
}
