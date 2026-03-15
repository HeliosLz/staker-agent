import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Terminal,
  Settings,
  HelpCircle,
  Hexagon,
} from 'lucide-react';

const NAV_SECTIONS = [
  {
    items: [
      { to: '/dashboard', label: '概览', icon: LayoutDashboard },
    ],
  },
  {
    title: 'Node',
    items: [
      { to: '/terminal', label: '终端', icon: Terminal },
    ],
  },
  {
    title: 'Support',
    items: [
      { to: '/setup', label: '设置向导', icon: Settings },
      { to: 'https://ethdocker.com', label: '帮助文档', icon: HelpCircle, external: true },
    ],
  },
];

function linkClass({ isActive }: { isActive: boolean }) {
  return `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
    isActive
      ? 'bg-pink-50 text-pink-600'
      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
  }`;
}

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 bottom-0 w-56 bg-white border-r border-gray-200 flex flex-col z-30">
      {/* Logo */}
      <div className="px-5 py-5 flex items-center gap-2.5 border-b border-gray-100">
        <Hexagon className="w-7 h-7 text-pink-500" />
        <div>
          <span className="font-bold text-base text-gray-900">Staker Agent</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        {NAV_SECTIONS.map((section, si) => (
          <div key={si}>
            {section.title && (
              <p className="px-4 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {section.title}
              </p>
            )}
            <div className="space-y-1">
              {section.items.map((item) =>
                'external' in item && item.external ? (
                  <a
                    key={item.to}
                    href={item.to}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </a>
                ) : (
                  <NavLink key={item.to} to={item.to} className={linkClass}>
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </NavLink>
                )
              )}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-xs text-gray-500">Ethereum</span>
        </div>
      </div>
    </aside>
  );
}
