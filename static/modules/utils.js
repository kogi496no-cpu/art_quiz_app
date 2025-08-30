// HTMLエスケープ関数
export function escapeHtml(text) {
    if (text === null || typeof text === 'undefined') return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// メッセージ表示機能 (モーダルに表示するように変更)
export function openMessageModal(message, type = 'info') {
    const modal = document.getElementById('messageModal');
    const modalMessage = document.getElementById('modalMessage');
    if (modal && modalMessage) {
        modalMessage.textContent = message;
        // メッセージタイプに応じてスタイルを調整することも可能
        // 例: modalMessage.className = `message-${type}`; 
        modal.style.display = 'block';
    }
}

export function closeMessageModal() {
    const modal = document.getElementById('messageModal');
    if (modal) {
        modal.style.display = 'none';
    }
}