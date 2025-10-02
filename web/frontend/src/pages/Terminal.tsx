import { useState } from 'react';
import { Terminal as TerminalIcon, Send } from 'lucide-react';

export default function Terminal() {
  const [command, setCommand] = useState('');
  const [history, setHistory] = useState<Array<{ type: 'input' | 'output'; text: string }>>([
    { type: 'output', text: 'Welcome to Staker Agent Terminal' },
    { type: 'output', text: 'Type "help" for available commands' },
    { type: 'output', text: '' },
  ]);

  const executeCommand = (cmd: string) => {
    // Add command to history
    setHistory((prev) => [...prev, { type: 'input', text: `$ ${cmd}` }]);

    // Simulate command execution
    let output = '';
    switch (cmd.toLowerCase().trim()) {
      case 'help':
        output = `Available commands:
  status  - Show node status
  logs    - Show recent logs
  restart - Restart the node
  stop    - Stop the node
  start   - Start the node
  clear   - Clear terminal`;
        break;
      case 'status':
        output = `✅ Node Status:
  Network: Holesky
  Client: Lighthouse + Geth
  Status: Running
  Uptime: 2h 34m
  Peers: 8 connected`;
        break;
      case 'logs':
        output = `Recent logs:
  INFO: Syncing block 1234567
  INFO: Connected to 8 peers
  INFO: Attestation successful`;
        break;
      case 'clear':
        setHistory([]);
        setCommand('');
        return;
      case '':
        return;
      default:
        output = `Command not found: ${cmd}. Type "help" for available commands.`;
    }

    setHistory((prev) => [...prev, { type: 'output', text: output }, { type: 'output', text: '' }]);
    setCommand('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (command.trim()) {
      executeCommand(command);
    }
  };

  const quickCommands = ['status', 'logs', 'restart', 'stop'];

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="container mx-auto max-w-6xl">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <TerminalIcon className="w-8 h-8 text-green-400" />
          <h1 className="text-2xl font-bold text-white">Staker Agent Terminal</h1>
        </div>

        {/* Terminal Window */}
        <div className="bg-black rounded-lg shadow-2xl overflow-hidden border border-gray-700">
          {/* Terminal Header */}
          <div className="bg-gray-800 px-4 py-2 flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="ml-4 text-sm text-gray-400 font-mono">staker-agent@local:~</span>
          </div>

          {/* Terminal Content */}
          <div className="p-4 h-96 overflow-y-auto font-mono text-sm">
            {history.map((item, index) => (
              <div
                key={index}
                className={`${
                  item.type === 'input' ? 'text-green-400' : 'text-gray-300'
                } whitespace-pre-wrap`}
              >
                {item.text}
              </div>
            ))}

            {/* Input Line */}
            <form onSubmit={handleSubmit} className="flex items-center mt-2">
              <span className="text-green-400 mr-2">$</span>
              <input
                type="text"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                className="flex-1 bg-transparent text-green-400 outline-none caret-green-400"
                autoFocus
              />
              <button type="submit" className="hidden">
                Submit
              </button>
            </form>
            <div className="text-green-400 animate-pulse inline-block">▌</div>
          </div>

          {/* Quick Commands */}
          <div className="bg-gray-800 px-4 py-3 border-t border-gray-700">
            <p className="text-xs text-gray-400 mb-2">Quick Commands:</p>
            <div className="flex gap-2 flex-wrap">
              {quickCommands.map((cmd) => (
                <button
                  key={cmd}
                  onClick={() => executeCommand(cmd)}
                  className="px-3 py-1 bg-gray-700 text-gray-300 rounded text-sm hover:bg-gray-600 transition"
                >
                  {cmd}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Info */}
        <div className="mt-6 text-gray-400 text-sm">
          <p>💡 Tip: You can also use the CLI directly: <code className="text-green-400 bg-gray-800 px-2 py-1 rounded">python3 cli.py [command]</code></p>
        </div>
      </div>
    </div>
  );
}
