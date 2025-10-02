import { Link } from 'react-router-dom';
import { Rocket, Clock, DollarSign, Shield, Network, Cpu } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          {/* Logo & Title */}
          <div className="flex items-center justify-center gap-3 mb-6">
            <Rocket className="w-12 h-12 text-blue-600" />
            <h1 className="text-5xl font-bold text-gray-900">Staker Agent</h1>
          </div>

          {/* Tagline */}
          <p className="text-2xl text-gray-600 mb-8">
            Deploy Your Ethereum Validator in 5 Minutes
          </p>

          {/* CTA Buttons */}
          <div className="flex gap-4 justify-center mb-16">
            <Link
              to="/setup"
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition flex items-center gap-2"
            >
              开始部署 <Rocket className="w-5 h-5" />
            </Link>
            <a
              href="https://github.com/eth-educators/eth-docker"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white text-gray-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-50 transition border border-gray-300"
            >
              查看文档
            </a>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <Clock className="w-10 h-10 text-blue-600 mb-4 mx-auto" />
              <h3 className="text-xl font-semibold mb-2">5 分钟部署</h3>
              <p className="text-gray-600">
                简单几步即可完成验证节点部署,无需复杂配置
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm">
              <DollarSign className="w-10 h-10 text-green-600 mb-4 mx-auto" />
              <h3 className="text-xl font-semibold mb-2">节省成本</h3>
              <p className="text-gray-600">
                5 年节省 $28,000+,本地部署更经济实惠
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm">
              <Shield className="w-10 h-10 text-purple-600 mb-4 mx-auto" />
              <h3 className="text-xl font-semibold mb-2">100% 安全</h3>
              <p className="text-gray-600">
                完全控制您的密钥,符合以太坊去中心化精神
              </p>
            </div>
          </div>

          {/* Supported Networks & Clients */}
          <div className="bg-white rounded-xl p-8 shadow-sm">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Network className="w-6 h-6 text-blue-600" />
                  <h3 className="text-lg font-semibold">支持的网络</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                    Mainnet
                  </span>
                  <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                    Holesky ⭐
                  </span>
                  <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                    Hoodi (Lido)
                  </span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                    Sepolia
                  </span>
                </div>
              </div>

              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Cpu className="w-6 h-6 text-blue-600" />
                  <h3 className="text-lg font-semibold">支持的客户端</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm">
                    Lighthouse ⭐
                  </span>
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                    Prysm
                  </span>
                  <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm">
                    Teku
                  </span>
                  <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm">
                    Nimbus
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center py-8 text-gray-500">
        <p>Powered by eth-docker • Made with ❤️ for Ethereum Stakers</p>
      </div>
    </div>
  );
}
