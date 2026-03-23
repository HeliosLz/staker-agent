interface Props {
  mnemonic: string;
  onConfirm: () => void;
}

export default function MnemonicModal({ mnemonic, onConfirm }: Props) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-8 shadow-2xl">
        <h3 className="text-xl font-bold text-gray-900 mb-2">请备份您的助记词</h3>
        <p className="text-sm text-red-600 mb-4">
          这是恢复密钥的唯一方式。请将助记词抄写在纸上并妥善保管，关闭后将无法再次查看。
        </p>
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-6">
          <div className="grid grid-cols-4 gap-2">
            {mnemonic.split(' ').map((word, i) => (
              <div key={i} className="bg-white border border-yellow-300 rounded-lg px-2 py-1.5 text-center">
                <span className="text-xs text-gray-400 mr-1">{i + 1}.</span>
                <span className="font-mono text-sm font-medium text-gray-900">{word}</span>
              </div>
            ))}
          </div>
        </div>
        <button
          onClick={onConfirm}
          className="w-full bg-blue-600 text-white py-3 rounded-xl font-medium hover:bg-blue-700 transition-colors"
        >
          我已安全备份，进入控制面板
        </button>
      </div>
    </div>
  );
}
