// グローバル変数
import { loadQuiz, toggleStats, loadStats, resetQuizStats, applyTheme } from './quiz.js';
import { openMessageModal, closeMessageModal } from './utils.js';
import { handleUploadSubmit, loadArtworks, handleEditSubmit, openEditModal, closeEditModal, deleteArtwork } from './artworks.js';

export let currentGenre = ''; // ジャンルを保持するグローバル変数

// DOMContentLoaded時の初期化
document.addEventListener('DOMContentLoaded', function() {
    // bodyのdata属性からジャンルを取得
    currentGenre = document.body.dataset.genre;

    initializeEventListeners();

    // クイズページでのみ実行
    if (document.getElementById('quiz-area')) {
        applyTheme(currentGenre); // Apply theme on page load
        loadStats(currentGenre);
    }
    // 作品管理ページでのみ実行
    if (document.getElementById('artworks-list')) {
        // 「作品を表示/非表示」ボタンのトグル機能
        const loadBtn = document.getElementById('load-artworks-btn');
        const artworksList = document.getElementById('artworks-list');
        if (loadBtn && artworksList) {
            loadBtn.addEventListener('click', () => {
                // artworksListに中身があるかで表示/非表示を切り替え
                if (artworksList.innerHTML.trim() !== '') {
                    artworksList.innerHTML = ''; // リストをクリア
                    loadBtn.textContent = '作品を表示';
                } else {
                    loadArtworks('', currentGenre); // 作品を読み込み
                    loadBtn.textContent = '非表示にする';
                }
            });
        }
    }

    // メッセージモーダルの閉じるボタンにイベントリスナーを設定
    const closeMessageModalBtn = document.getElementById('closeMessageModal');
    if (closeMessageModalBtn) {
        closeMessageModalBtn.addEventListener('click', closeMessageModal);
    }

    // クイズ関連関数をグローバルスコープに公開
    window.loadQuiz = () => loadQuiz(currentGenre);
    window.toggleStats = () => toggleStats(currentGenre);
    window.loadStats = () => loadStats(currentGenre);
    window.resetQuizStats = () => resetQuizStats(currentGenre);
});

// イベントリスナーの初期化
function initializeEventListeners() {
    const uploadForm = document.getElementById('art-form-upload');
    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => handleUploadSubmit(e, currentGenre));
    }
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', e => {
            e.preventDefault();
            const query = document.getElementById('search-input').value;
            loadArtworks(query, currentGenre);
        });
        
    }
    const editForm = document.getElementById('edit-form');
    if (editForm) {
        editForm.addEventListener('submit', (e) => handleEditSubmit(e, currentGenre));
    }
    const resetBtn = document.getElementById('reset-quiz-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => resetQuizStats(currentGenre));
    }
}