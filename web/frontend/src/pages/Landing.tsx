import { Link } from 'react-router-dom';
import { Sparkles, Zap, Shield, DollarSign, Clock, ArrowRight, Github, BookOpen } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white overflow-hidden">
      {/* Gradient Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-[128px]" />
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-[128px]" />
        <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-cyan-500/10 rounded-full blur-[128px]" />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 border-b border-white/10 backdrop-blur-xl">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <span className="text-xl font-semibold">Staker Agent</span>
            </div>
            <div className="flex items-center gap-6">
              <a href="https://github.com/HeliosLz/staker-agent" target="_blank" rel="noopener noreferrer"
                 className="text-gray-400 hover:text-white transition">
                <Github className="w-5 h-5" />
              </a>
              <Link to="/setup"
                    className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition text-sm font-medium">
                开始使用
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative z-10 container mx-auto px-6 pt-20 pb-32">
        <div className="max-w-5xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8 backdrop-blur-xl">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm text-gray-300">AI-Powered Ethereum Staking</span>
          </div>

          {/* Main Heading */}
          <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight">
            <span className="gradient-text">
              Deploy Your Validator
            </span>
            <br />
            <span className="text-white/90">in 5 Minutes</span>
          </h1>

          {/* Description */}
          <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto leading-relaxed">
            AI Agent 自动化部署以太坊验证节点。
            <span className="text-white/80"> 无需运维经验，智能检测环境，一键解决问题。</span>
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-20">
            <Link
              to="/setup"
              className="group px-8 py-4 rounded-xl bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 transition-all duration-300 font-semibold flex items-center gap-2 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 hover:scale-105"
            >
              开始部署
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a
              href="https://github.com/HeliosLz/staker-agent"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all duration-300 font-semibold flex items-center gap-2 backdrop-blur-xl"
            >
              <Github className="w-5 h-5" />
              查看源码
            </a>
          </div>

          {/* Demo Preview */}
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-purple-500 to-blue-500 rounded-2xl blur-xl opacity-25 group-hover:opacity-40 transition duration-500" />
            <div className="relative glass-card p-1">
              <div className="bg-[#151515] rounded-xl overflow-hidden border border-white/10">
                {/* Terminal Header */}
                <div className="bg-[#1F1F1F] px-4 py-3 border-b border-white/10 flex items-center gap-2">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/80" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                    <div className="w-3 h-3 rounded-full bg-green-500/80" />
                  </div>
                  <span className="text-sm text-gray-400 ml-4 font-mono">staker-agent</span>
                </div>
                {/* Terminal Content */}
                <div className="p-6 font-mono text-sm space-y-2 text-left">
                  <div className="text-gray-500">$ python3 cli.py check</div>
                  <div className="text-green-400">✓ OS: macOS 14.0</div>
                  <div className="text-green-400">✓ Python: 3.12.4</div>
                  <div className="text-yellow-400">⚠ Docker: Not installed</div>
                  <div className="text-blue-400 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 animate-pulse" />
                    <span>🤖 Agent: Installing Docker for you...</span>
                  </div>
                  <div className="text-green-400">✓ Docker: 24.0.7 installed</div>
                  <div className="text-gray-500 mt-4">$ python3 cli.py deploy</div>
                  <div className="text-cyan-400">🚀 Deploying validator node...</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="relative z-10 container mx-auto px-6 py-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">为什么选择 Staker Agent?</h2>
            <p className="text-gray-400 text-lg">AI 驱动的智能部署，让 Solo Staking 变得简单</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="glass-card p-8 group hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <Zap className="w-6 h-6 text-purple-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">5 分钟部署</h3>
              <p className="text-gray-400 leading-relaxed">
                传统方式需要 2-3 天学习和配置。我们的 AI Agent 帮你 5 分钟搞定一切。
              </p>
            </div>

            {/* Feature 2 */}
            <div className="glass-card p-8 group hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <Sparkles className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">AI 自动修复</h3>
              <p className="text-gray-400 leading-relaxed">
                检测到问题？Agent 自动分析并提供解决方案。Docker 没装？自动帮你装好。
              </p>
            </div>

            {/* Feature 3 */}
            <div className="glass-card p-8 group hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500/20 to-green-500/10 border border-green-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <DollarSign className="w-6 h-6 text-green-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">节省 $28,000+</h3>
              <p className="text-gray-400 leading-relaxed">
                5 年云服务器成本 vs 本地部署。选择本地，省下的钱够买更多 ETH。
              </p>
            </div>

            {/* Feature 4 */}
            <div className="glass-card p-8 group hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <Shield className="w-6 h-6 text-cyan-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">100% 自托管</h3>
              <p className="text-gray-400 leading-relaxed">
                完全控制你的私钥和节点。无需信任第三方，真正的去中心化。
              </p>
            </div>

            {/* Feature 5 */}
            <div className="glass-card p-8 group hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500/20 to-orange-500/10 border border-orange-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <Clock className="w-6 h-6 text-orange-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">实时监控</h3>
              <p className="text-gray-400 leading-relaxed">
                Web UI + CLI 双界面。Grafana 仪表盘实时监控节点状态和收益。
              </p>
            </div>

            {/* Feature 6 */}
            <div className="glass-card p-8 group hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500/20 to-pink-500/10 border border-pink-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <BookOpen className="w-6 h-6 text-pink-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">开源透明</h3>
              <p className="text-gray-400 leading-relaxed">
                基于 eth-docker，代码开源可审计。社区驱动，持续更新。
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="relative z-10 container mx-auto px-6 py-20">
        <div className="max-w-4xl mx-auto glass-card p-12">
          <div className="grid md:grid-cols-3 gap-12 text-center">
            <div>
              <div className="text-5xl font-bold gradient-text mb-2">5 min</div>
              <div className="text-gray-400">平均部署时间</div>
            </div>
            <div>
              <div className="text-5xl font-bold gradient-text mb-2">$28K+</div>
              <div className="text-gray-400">5年节省成本</div>
            </div>
            <div>
              <div className="text-5xl font-bold gradient-text mb-2">100%</div>
              <div className="text-gray-400">私钥自托管</div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative z-10 container mx-auto px-6 py-32">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-5xl font-bold mb-6">
            Ready to Become a
            <span className="gradient-text"> Validator?</span>
          </h2>
          <p className="text-xl text-gray-400 mb-10">
            加入全球数千名 Solo Staker，为以太坊去中心化贡献力量
          </p>
          <Link
            to="/setup"
            className="inline-flex items-center gap-2 px-10 py-5 rounded-xl bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 transition-all duration-300 font-semibold text-lg shadow-2xl shadow-purple-500/25 hover:shadow-purple-500/40 hover:scale-105"
          >
            开始部署
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>

      {/* Footer */}
      <div className="relative z-10 border-t border-white/10 backdrop-blur-xl">
        <div className="container mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between text-gray-400 text-sm">
            <div className="flex items-center gap-2 mb-4 md:mb-0">
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                <Sparkles className="w-4 h-4" />
              </div>
              <span>Staker Agent</span>
            </div>
            <div className="flex items-center gap-6">
              <span>Powered by eth-docker</span>
              <span>•</span>
              <a href="https://github.com/HeliosLz/staker-agent" target="_blank" rel="noopener noreferrer"
                 className="hover:text-white transition flex items-center gap-2">
                <Github className="w-4 h-4" />
                GitHub
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
