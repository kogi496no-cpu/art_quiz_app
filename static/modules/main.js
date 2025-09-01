// グローバル変数
import { loadQuiz, toggleStats, loadStats, resetQuizStats } from './quiz.js';
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
        loadStats(currentGenre);
    }
    // 作品管理ページでのみ実行
    if (document.getElementById('artworks-list')) {
        // ボタンクリックで作品を読み込むように変更
        const loadBtn = document.getElementById('load-artworks-btn');
        if (loadBtn) {
            loadBtn.addEventListener('click', () => {
                loadArtworks('', currentGenre);
                loadBtn.style.display = 'none'; // ボタンを非表示にする
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

