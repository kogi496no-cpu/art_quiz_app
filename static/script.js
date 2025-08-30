// グローバル変数

let currentQuizData = null;
let quizAnswered = false;
let currentGenre = ''; // ジャンルを保持するグローバル変数

// DOMContentLoaded時の初期化
document.addEventListener('DOMContentLoaded', function() {
    // bodyのdata属性からジャンルを取得
    currentGenre = document.body.dataset.genre;

    initializeEventListeners();

    // クイズページでのみ実行
    if (document.getElementById('quiz-area')) {
        loadStats();
    }
    initializeEventListeners();

    // クイズページでのみ実行
    if (document.getElementById('quiz-area')) {
        loadStats();
    }
    // 作品管理ページでのみ実行
    if (document.getElementById('artworks-list')) {
        // ボタンクリックで作品を読み込むように変更
        const loadBtn = document.getElementById('load-artworks-btn');
        if (loadBtn) {
            loadBtn.addEventListener('click', () => {
                loadArtworks();
                loadBtn.style.display = 'none'; // ボタンを非表示にする
            });
        }
    }

    // メッセージモーダルの閉じるボタンにイベントリスナーを設定
    const closeMessageModalBtn = document.getElementById('closeMessageModal');
    if (closeMessageModalBtn) {
        closeMessageModalBtn.addEventListener('click', closeMessageModal);
    }
});

// イベントリスナーの初期化
function initializeEventListeners() {
    const uploadForm = document.getElementById('art-form-upload');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUploadSubmit);
    }
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', e => {
            e.preventDefault();
            const query = document.getElementById('search-input').value;
            loadArtworks(query);
        });
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                loadArtworks(searchInput.value);
            });
        }
    }
    const editForm = document.getElementById('edit-form');
    if (editForm) {
        editForm.addEventListener('submit', handleEditSubmit);
    }
    const resetBtn = document.getElementById('reset-quiz-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetQuizStats);
    }
}

// HTMLエスケープ関数
function escapeHtml(text) {
    if (text === null || typeof text === 'undefined') return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// --- 作品管理機能 (artworks.html) ---

// 作品登録 (画像アップロード対応)
async function handleUploadSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const apiUrl = `/api/${currentGenre}/artworks/upload`;

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            const result = await response.json();
            openMessageModal(result.message, 'success'); // ポップアップ表示に変更
            e.target.reset();
            loadArtworks();
        } else {
            const errorData = await response.json();
            openMessageModal('エラー: ' + (errorData.detail || '保存に失敗しました'), 'error'); // ポップアップ表示に変更
        }
    } catch (error) {
        openMessageModal('ネットワークエラー: ' + error.message, 'error'); // ポップアップ表示に変更
    }
}

// 作品一覧読込
async function loadArtworks(searchQuery = '') {
    const artworksArea = document.getElementById('artworks-list');
    const artworkCountSpan = document.getElementById('artwork-count');
    if (!artworksArea) return;

    try {
        const url = new URL(`/api/${currentGenre}/artworks`, window.location.origin);
        if (searchQuery) {
            url.searchParams.append('q', searchQuery);
        }
        
        const res = await fetch(url);
        const data = await res.json();

        // 検索クエリがない場合のみ作品数を更新
        if (searchQuery === '' && artworkCountSpan) {
            artworkCountSpan.textContent = data.artworks.length;
        }
        
        if (data.artworks.length === 0) {
            // 検索結果が0件の場合と初期状態で0件の場合でメッセージを分ける
            if (searchQuery !== '') {
                artworksArea.innerHTML = '<p>該当する作品がありません。</p>';
            } else {
                artworksArea.innerHTML = '<p>登録されている作品はありません。</p>';
            }
            return;
        }
        const tableContainer = document.createElement('div');
        tableContainer.className = 'table-container';
        const table = document.createElement('table');
        const headerRow = document.createElement('tr');
        ['ID', '作者', '作品名', '様式', '備考', '画像', '操作'].forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            headerRow.appendChild(th);
        });
        table.appendChild(headerRow);
        data.artworks.forEach(artwork => table.appendChild(createArtworkRow(artwork)));
        tableContainer.appendChild(table);
        artworksArea.innerHTML = '';
        artworksArea.appendChild(tableContainer);
    } catch (error) {
        artworksArea.innerHTML = `<p>データの取得に失敗しました: ${error.message}</p>`;
    }
}

// 作品テーブルの行を作成
function createArtworkRow(artwork) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${artwork.id}</td>
        <td>${escapeHtml(artwork.author)}</td>
        <td>${escapeHtml(artwork.title)}</td>
        <td>${escapeHtml(artwork.style)}</td>
        <td class="notes-cell">${escapeHtml(artwork.notes)}</td>
        <td></td>
        <td></td>
    `;

    const imageCell = row.children[5];
    if (artwork.image_filename) {
        const img = document.createElement('img');
        const thumbPath = currentGenre === 'japanese' ? 'japanese_thumbnails' : 'thumbnails';
        img.src = `/uploads/${thumbPath}/thumb_${artwork.image_filename}`;
        img.alt = '作品画像';
        img.className = 'thumbnail-image';
        const imagePath = currentGenre === 'japanese' ? 'japanese_images' : 'images';
        img.onclick = () => window.open(`/uploads/${imagePath}/${artwork.image_filename}`, '_blank');
        imageCell.appendChild(img);
    } else {
        imageCell.textContent = 'なし';
    }

    const actionCell = row.children[6];
    const editBtn = document.createElement('button');
    editBtn.textContent = '編集';
    editBtn.className = 'btn btn-secondary';
    editBtn.onclick = () => openEditModal(artwork);
    actionCell.appendChild(editBtn);

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = '削除';
    deleteBtn.className = 'btn btn-danger';
    deleteBtn.onclick = () => deleteArtwork(artwork.id);
    actionCell.appendChild(deleteBtn);

    return row;
}

// 作品削除
async function deleteArtwork(artworkId) {
    if (!confirm('この作品を削除してもよろしいですか？')) return;
    try {
        const response = await fetch(`/api/${currentGenre}/artworks/${artworkId}`, { method: 'DELETE' });
        if (response.ok) {
            openMessageModal('作品を削除しました', 'success'); // ポップアップ表示に変更
            loadArtworks();
        } else {
            const errorData = await response.json();
            openMessageModal('エラー: ' + (errorData.detail || '削除に失敗しました'), 'error'); // ポップアップ表示に変更
        }
    } catch (error) {
        openMessageModal('ネットワークエラー: ' + error.message, 'error'); // ポップアップ表示に変更
    }
}

// 編集モーダルを開く
function openEditModal(artwork) {
    document.getElementById('edit-artwork-id').value = artwork.id;
    document.getElementById('edit-author').value = artwork.author;
    document.getElementById('edit-title').value = artwork.title;
    document.getElementById('edit-style').value = artwork.style;
    document.getElementById('edit-notes').value = artwork.notes || '';
    document.getElementById('edit-modal').style.display = 'block';
}

// 編集モーダルを閉じる
function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

// 編集フォーム送信
async function handleEditSubmit(e) {
    e.preventDefault();
    const artworkId = document.getElementById('edit-artwork-id').value;
    const data = {
        author: document.getElementById('edit-author').value,
        title: document.getElementById('edit-title').value,
        style: document.getElementById('edit-style').value,
        notes: document.getElementById('edit-notes').value,
    };

    try {
        const response = await fetch(`/api/${currentGenre}/artworks/${artworkId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        if (response.ok) {
            openMessageModal('更新しました', 'success'); // ポップアップ表示に変更
            closeEditModal();
            loadArtworks();
        } else {
            const errorData = await response.json();
            openMessageModal('エラー: ' + (errorData.detail || '更新に失敗しました'), 'error'); // ポップアップ表示に変更
        }
    } catch (error) {
        openMessageModal('ネットワークエラー: ' + error.message, 'error'); // ポップアップ表示に変更
    }
}


// --- クイズ機能 (quiz.html) ---



// クイズ読込
async function loadQuiz() {
    const endpoint = `/api/${currentGenre}/quiz/multiple-choice`;
    try {
        const res = await fetch(endpoint);
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "クイズの取得に失敗しました。");
        }
        const data = await res.json();
        currentQuizData = data;
        quizAnswered = false;
        const quizArea = document.getElementById('quiz-area');
        quizArea.innerHTML = '';
        displayMultipleChoiceQuiz(data);
    } catch (error) {
        document.getElementById('quiz-area').innerHTML = `<p class="error">${error.message}</p>`;
    }
}

// 4択クイズ表示
function displayMultipleChoiceQuiz(data) {
    const quizArea = document.getElementById('quiz-area');
    displayArtworkInfo(data.artwork, quizArea);
    const questionDiv = document.createElement('div');
    questionDiv.innerHTML = `<h3>${escapeHtml(data.question)}</h3>`;
    quizArea.appendChild(questionDiv);

    const choicesContainer = document.createElement('div');
    
    if (data.question_field === 'image') {
        choicesContainer.className = 'quiz-choices image-choices';
        data.choices.forEach(choice => {
            const img = document.createElement('img');
            const thumbPath = currentGenre === 'japanese' ? 'japanese_thumbnails' : 'thumbnails';
            img.src = `/uploads/${thumbPath}/thumb_${choice}`;
            img.alt = '選択肢の画像';
            img.className = 'choice-image';
            img.dataset.filename = choice;
            img.onclick = () => selectAnswer(choice);
            choicesContainer.appendChild(img);
        });
    } else {
        choicesContainer.className = 'quiz-choices';
        data.choices.forEach((choice, index) => {
            const choiceButton = document.createElement('button');
            choiceButton.className = 'choice-button';
            choiceButton.textContent = `${String.fromCharCode(65 + index)}. ${escapeHtml(choice)}`;
            choiceButton.onclick = () => selectAnswer(choice);
            choicesContainer.appendChild(choiceButton);
        });
    }
    quizArea.appendChild(choicesContainer);
}

// 作品情報表示 (クイズ用)
function displayArtworkInfo(artwork, container) {
    const fields = [
        { label: '作者', value: artwork.author },
        { label: '作品名', value: artwork.title },
        { label: '美術様式', value: artwork.style }
    ];
    fields.forEach(field => {
        const p = document.createElement('p');
        p.innerHTML = `<strong>${field.label}:</strong> ${escapeHtml(field.value)}`;
        container.appendChild(p);
    });
    
    const imageContainer = document.createElement('div');
    const filename = artwork.image_filename;
    if (filename && filename !== "???") {
        const img = document.createElement('img');
        const thumbPath = currentGenre === 'japanese' ? 'japanese_thumbnails' : 'thumbnails';
        img.src = `/uploads/${thumbPath}/thumb_${filename}`;
        img.alt = '作品画像';
        img.className = 'quiz-image';
        const imagePath = currentGenre === 'japanese' ? 'japanese_images' : 'images';
        img.onclick = () => window.open(`/uploads/${imagePath}/${filename}`, '_blank');
        imageContainer.appendChild(img);
    } else if (filename === "???") {
        imageContainer.innerHTML = '<strong>画像:</strong> ???';
    } else {
        imageContainer.innerHTML = '<strong>画像:</strong> 画像なし';
    }
    container.appendChild(imageContainer);
}

// 回答選択
function selectAnswer(selectedChoice) {
    if (quizAnswered || !currentQuizData) return;
    quizAnswered = true;
    const { correct_answer, question_field } = currentQuizData;
    const isCorrect = selectedChoice === correct_answer;

    if (question_field === 'image') {
        document.querySelectorAll('.choice-image').forEach(img => {
            img.classList.add('disabled');
            if (img.dataset.filename === correct_answer) img.classList.add('correct');
            else if (img.dataset.filename === selectedChoice) img.classList.add('incorrect');
        });
    } else {
        document.querySelectorAll('.choice-button').forEach(button => {
            button.classList.add('disabled');
            if (button.textContent.includes(correct_answer)) button.classList.add('correct');
            else if (button.textContent.includes(selectedChoice)) button.classList.add('incorrect');
        });
    }

    showQuizResult(isCorrect, selectedChoice);
    recordQuizResult(isCorrect, selectedChoice);
}

// クイズ結果表示
function showQuizResult(isCorrect, selectedChoice) {
    const resultDiv = document.createElement('div');
    const { correct_answer, full_artwork_data } = currentQuizData;
    resultDiv.className = `quiz-result ${isCorrect ? 'correct' : 'incorrect'}`;

    if (isCorrect) {
        resultDiv.innerHTML = `<h3>正解です！</h3>`;
    }
    else {
        resultDiv.innerHTML = `<h3>❌ 不正解</h3><p><strong>正解:</strong> ${escapeHtml(correct_answer)}</p>`;
    }

    if (full_artwork_data.notes) {
        resultDiv.innerHTML += `<p><strong>備考:</strong> ${escapeHtml(full_artwork_data.notes)}</p>`;
    }

    const nextButton = document.createElement('button');
    nextButton.className = 'btn btn-primary mt-3';
    nextButton.textContent = '次のクイズ';
    nextButton.onclick = loadQuiz;
    resultDiv.appendChild(nextButton);
    document.getElementById('quiz-area').appendChild(resultDiv);
}

// クイズ結果記録
async function recordQuizResult(isCorrect, userAnswer) {
    const { question_field, correct_answer } = currentQuizData;
    try {
        await fetch(`/api/${currentGenre}/quiz/submit`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ question_field, correct_answer, user_answer: userAnswer, is_correct: isCorrect })
        });
        loadStats();
    } catch (error) {
        console.error('結果の記録に失敗:', error);
    }
}

// 統計表示切替
function toggleStats() {
    const statsContent = document.getElementById('stats-content');
    if (!statsContent) return;
    statsContent.classList.toggle('hidden');
    const btn = statsContent.previousElementSibling;
    if (btn) btn.textContent = statsContent.classList.contains('hidden') ? '統計を表示' : '統計を非表示';

    if (!statsContent.classList.contains('hidden')) {
        loadStats();
    }
}

// 統計読込
async function loadStats() {
    const statsContent = document.getElementById('stats-content');
    if (!statsContent) return;
    try {
        const res = await fetch(`/api/${currentGenre}/quiz/stats`);
        const stats = await res.json();
        const fieldNames = {author:'作者', title:'作品名', style:'様式', image: '画像'};
        statsContent.innerHTML = `
            <div class="stats-grid">
                <div class="stats-card"><div>${stats.total_attempts}</div><div>総回答数</div></div>
                <div class="stats-card"><div>${stats.correct_attempts}</div><div>正解数</div></div>
                <div class="stats-card"><div>${stats.overall_accuracy}%</div><div>正答率</div></div>
            </div>
            <h4>分野別統計</h4>
            <div class="stats-grid">
                ${(stats.field_stats.map(f => `
                    <div class="stats-card">
                        <div>${f.accuracy}%</div>
                        <div>${fieldNames[f.field] || f.field}</div>
                    </div>`
                )).join('')}
            </div>
        `;
    } catch (error) {
        console.error('統計の読み込みに失敗:', error);
        statsContent.innerHTML = '<p>統計の読み込みに失敗しました。</p>';
    }
}

// クイズ統計リセット
async function resetQuizStats() {
    if (!confirm('本当にこのジャンルのクイズ結果をリセットしますか？')) return;
    try {
        const res = await fetch(`/api/${currentGenre}/quiz/reset`, { method: 'POST' });
        if (res.ok) {
            openMessageModal('クイズ結果をリセットしました', 'success'); // ポップアップ表示に変更
            loadStats();
            document.getElementById('quiz-area').innerHTML = '';
        } else {
            const err = await res.json();
            openMessageModal('リセット失敗: ' + (err.detail || '不明なエラー'), 'error'); // ポップアップ表示に変更
        }
    } catch (error) {
        openMessageModal('ネットワークエラー: ' + error.message, 'error'); // ポップアップ表示に変更
    }
}

// メッセージ表示機能 (モーダルに表示するように変更)
function openMessageModal(message, type = 'info') {
    const modal = document.getElementById('messageModal');
    const modalMessage = document.getElementById('modalMessage');
    if (modal && modalMessage) {
        modalMessage.textContent = message;
        // メッセージタイプに応じてスタイルを調整することも可能
        // 例: modalMessage.className = `message-${type}`; 
        modal.style.display = 'block';
    }
}

function closeMessageModal() {
    const modal = document.getElementById('messageModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// イベントリスナーの初期化
function initializeEventListeners() {
    const uploadForm = document.getElementById('art-form-upload');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUploadSubmit);
    }
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', e => {
            e.preventDefault();
            const query = document.getElementById('search-input').value;
            loadArtworks(query);
        });
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                loadArtworks(searchInput.value);
            });
        }
    }
    const editForm = document.getElementById('edit-form');
    if (editForm) {
        editForm.addEventListener('submit', handleEditSubmit);
    }
    const resetBtn = document.getElementById('reset-quiz-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetQuizStats);
    }
}

// HTMLエスケープ関数
function escapeHtml(text) {
    if (text === null || typeof text === 'undefined') return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// --- 作品管理機能 (artworks.html) ---

// 作品登録 (画像アップロード対応)
async function handleUploadSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const apiUrl = `/api/${currentGenre}/artworks/upload`;

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            const result = await response.json();
            showMessage(result.message, 'success');
            e.target.reset();
            loadArtworks();
        } else {
            const errorData = await response.json();
            showMessage('エラー: ' + (errorData.detail || '保存に失敗しました'), 'error');
        }
    } catch (error) {
        showMessage('ネットワークエラー: ' + error.message, 'error');
    }
}

// 作品一覧読込
async function loadArtworks(searchQuery = '') {
    const artworksArea = document.getElementById('artworks-list');
    const artworkCountSpan = document.getElementById('artwork-count');
    if (!artworksArea) return;

    try {
        const url = new URL(`/api/${currentGenre}/artworks`, window.location.origin);
        if (searchQuery) {
            url.searchParams.append('q', searchQuery);
        }
        
        const res = await fetch(url);
        const data = await res.json();

        // 検索クエリがない場合のみ作品数を更新
        if (searchQuery === '' && artworkCountSpan) {
            artworkCountSpan.textContent = data.artworks.length;
        }
        
        if (data.artworks.length === 0) {
            // 検索結果が0件の場合と初期状態で0件の場合でメッセージを分ける
            if (searchQuery !== '') {
                artworksArea.innerHTML = '<p>該当する作品がありません。</p>';
            } else {
                artworksArea.innerHTML = '<p>登録されている作品はありません。</p>';
            }
            return;
        }
        const tableContainer = document.createElement('div');
        tableContainer.className = 'table-container';
        const table = document.createElement('table');
        const headerRow = document.createElement('tr');
        ['ID', '作者', '作品名', '様式', '備考', '画像', '操作'].forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            headerRow.appendChild(th);
        });
        table.appendChild(headerRow);
        data.artworks.forEach(artwork => table.appendChild(createArtworkRow(artwork)));
        tableContainer.appendChild(table);
        artworksArea.innerHTML = '';
        artworksArea.appendChild(tableContainer);
    } catch (error) {
        artworksArea.innerHTML = `<p>データの取得に失敗しました: ${error.message}</p>`;
    }
}

// 作品テーブルの行を作成
function createArtworkRow(artwork) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${artwork.id}</td>
        <td>${escapeHtml(artwork.author)}</td>
        <td>${escapeHtml(artwork.title)}</td>
        <td>${escapeHtml(artwork.style)}</td>
        <td class="notes-cell">${escapeHtml(artwork.notes)}</td>
        <td></td>
        <td></td>
    `;

    const imageCell = row.children[5];
    if (artwork.image_filename) {
        const img = document.createElement('img');
        const thumbPath = currentGenre === 'japanese' ? 'japanese_thumbnails' : 'thumbnails';
        img.src = `/uploads/${thumbPath}/thumb_${artwork.image_filename}`;
        img.alt = '作品画像';
        img.className = 'thumbnail-image';
        const imagePath = currentGenre === 'japanese' ? 'japanese_images' : 'images';
        img.onclick = () => window.open(`/uploads/${imagePath}/${artwork.image_filename}`, '_blank');
        imageCell.appendChild(img);
    } else {
        imageCell.textContent = 'なし';
    }

    const actionCell = row.children[6];
    const editBtn = document.createElement('button');
    editBtn.textContent = '編集';
    editBtn.className = 'btn btn-secondary';
    editBtn.onclick = () => openEditModal(artwork);
    actionCell.appendChild(editBtn);

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = '削除';
    deleteBtn.className = 'btn btn-danger';
    deleteBtn.onclick = () => deleteArtwork(artwork.id);
    actionCell.appendChild(deleteBtn);

    return row;
}

// 作品削除
async function deleteArtwork(artworkId) {
    if (!confirm('この作品を削除してもよろしいですか？')) return;
    try {
        const response = await fetch(`/api/${currentGenre}/artworks/${artworkId}`, { method: 'DELETE' });
        if (response.ok) {
            showMessage('作品を削除しました', 'success');
            loadArtworks();
        } else {
            const errorData = await response.json();
            showMessage('エラー: ' + (errorData.detail || '削除に失敗しました'), 'error');
        }
    } catch (error) {
        showMessage('ネットワークエラー: ' + error.message, 'error');
    }
}

// 編集モーダルを開く
function openEditModal(artwork) {
    document.getElementById('edit-artwork-id').value = artwork.id;
    document.getElementById('edit-author').value = artwork.author;
    document.getElementById('edit-title').value = artwork.title;
    document.getElementById('edit-style').value = artwork.style;
    document.getElementById('edit-notes').value = artwork.notes || '';
    document.getElementById('edit-modal').style.display = 'block';
}

// 編集モーダルを閉じる
function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

// 編集フォーム送信
async function handleEditSubmit(e) {
    e.preventDefault();
    const artworkId = document.getElementById('edit-artwork-id').value;
    const data = {
        author: document.getElementById('edit-author').value,
        title: document.getElementById('edit-title').value,
        style: document.getElementById('edit-style').value,
        notes: document.getElementById('edit-notes').value,
    };

    try {
        const response = await fetch(`/api/${currentGenre}/artworks/${artworkId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showMessage('更新しました', 'success');
            closeEditModal();
            loadArtworks();
        } else {
            const errorData = await response.json();
            showMessage('エラー: ' + (errorData.detail || '更新に失敗しました'), 'error');
        }
    } catch (error) {
        showMessage('ネットワークエラー: ' + error.message, 'error');
    }
}


// --- クイズ機能 (quiz.html) ---



// クイズ読込
async function loadQuiz() {
    const endpoint = `/api/${currentGenre}/quiz/multiple-choice`;
    try {
        const res = await fetch(endpoint);
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "クイズの取得に失敗しました。");
        }
        const data = await res.json();
        currentQuizData = data;
        quizAnswered = false;
        const quizArea = document.getElementById('quiz-area');
        quizArea.innerHTML = '';
        displayMultipleChoiceQuiz(data);
    } catch (error) {
        document.getElementById('quiz-area').innerHTML = `<p class="error">${error.message}</p>`;
    }
}

// 4択クイズ表示
function displayMultipleChoiceQuiz(data) {
    const quizArea = document.getElementById('quiz-area');
    displayArtworkInfo(data.artwork, quizArea);
    const questionDiv = document.createElement('div');
    questionDiv.innerHTML = `<h3>${escapeHtml(data.question)}</h3>`;
    quizArea.appendChild(questionDiv);

    const choicesContainer = document.createElement('div');
    
    if (data.question_field === 'image') {
        choicesContainer.className = 'quiz-choices image-choices';
        data.choices.forEach(choice => {
            const img = document.createElement('img');
            const thumbPath = currentGenre === 'japanese' ? 'japanese_thumbnails' : 'thumbnails';
            img.src = `/uploads/${thumbPath}/thumb_${choice}`;
            img.alt = '選択肢の画像';
            img.className = 'choice-image';
            img.dataset.filename = choice;
            img.onclick = () => selectAnswer(choice);
            choicesContainer.appendChild(img);
        });
    } else {
        choicesContainer.className = 'quiz-choices';
        data.choices.forEach((choice, index) => {
            const choiceButton = document.createElement('button');
            choiceButton.className = 'choice-button';
            choiceButton.textContent = `${String.fromCharCode(65 + index)}. ${escapeHtml(choice)}`;
            choiceButton.onclick = () => selectAnswer(choice);
            choicesContainer.appendChild(choiceButton);
        });
    }
    quizArea.appendChild(choicesContainer);
}

// 作品情報表示 (クイズ用)
function displayArtworkInfo(artwork, container) {
    const fields = [
        { label: '作者', value: artwork.author },
        { label: '作品名', value: artwork.title },
        { label: '美術様式', value: artwork.style }
    ];
    fields.forEach(field => {
        const p = document.createElement('p');
        p.innerHTML = `<strong>${field.label}:</strong> ${escapeHtml(field.value)}`;
        container.appendChild(p);
    });
    
    const imageContainer = document.createElement('div');
    const filename = artwork.image_filename;
    if (filename && filename !== "???") {
        const img = document.createElement('img');
        const thumbPath = currentGenre === 'japanese' ? 'japanese_thumbnails' : 'thumbnails';
        img.src = `/uploads/${thumbPath}/thumb_${filename}`;
        img.alt = '作品画像';
        img.className = 'quiz-image';
        const imagePath = currentGenre === 'japanese' ? 'japanese_images' : 'images';
        img.onclick = () => window.open(`/uploads/${imagePath}/${filename}`, '_blank');
        imageContainer.appendChild(img);
    } else if (filename === "???") {
        imageContainer.innerHTML = '<strong>画像:</strong> ???';
    } else {
        imageContainer.innerHTML = '<strong>画像:</strong> 画像なし';
    }
    container.appendChild(imageContainer);
}

// 回答選択
function selectAnswer(selectedChoice) {
    if (quizAnswered || !currentQuizData) return;
    quizAnswered = true;
    const { correct_answer, question_field } = currentQuizData;
    const isCorrect = selectedChoice === correct_answer;

    if (question_field === 'image') {
        document.querySelectorAll('.choice-image').forEach(img => {
            img.classList.add('disabled');
            if (img.dataset.filename === correct_answer) img.classList.add('correct');
            else if (img.dataset.filename === selectedChoice) img.classList.add('incorrect');
        });
    } else {
        document.querySelectorAll('.choice-button').forEach(button => {
            button.classList.add('disabled');
            if (button.textContent.includes(correct_answer)) button.classList.add('correct');
            else if (button.textContent.includes(selectedChoice)) button.classList.add('incorrect');
        });
    }

    showQuizResult(isCorrect, selectedChoice);
    recordQuizResult(isCorrect, selectedChoice);
}

// クイズ結果表示
function showQuizResult(isCorrect, selectedChoice) {
    const resultDiv = document.createElement('div');
    const { correct_answer, full_artwork_data } = currentQuizData;
    resultDiv.className = `quiz-result ${isCorrect ? 'correct' : 'incorrect'}`;

    if (isCorrect) {
        resultDiv.innerHTML = `<h3>正解です！</h3>`;
    } else {
        resultDiv.innerHTML = `<h3>❌ 不正解</h3><p><strong>正解:</strong> ${escapeHtml(correct_answer)}</p>`;
    }

    if (full_artwork_data.notes) {
        resultDiv.innerHTML += `<p><strong>備考:</strong> ${escapeHtml(full_artwork_data.notes)}</p>`;
    }

    const nextButton = document.createElement('button');
    nextButton.className = 'btn btn-primary mt-3';
    nextButton.textContent = '次のクイズ';
    nextButton.onclick = loadQuiz;
    resultDiv.appendChild(nextButton);
    document.getElementById('quiz-area').appendChild(resultDiv);
}

// クイズ結果記録
async function recordQuizResult(isCorrect, userAnswer) {
    const { question_field, correct_answer } = currentQuizData;
    try {
        await fetch(`/api/${currentGenre}/quiz/submit`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ question_field, correct_answer, user_answer: userAnswer, is_correct: isCorrect })
        });
        loadStats();
    } catch (error) {
        console.error('結果の記録に失敗:', error);
    }
}

// 統計表示切替
function toggleStats() {
    const statsContent = document.getElementById('stats-content');
    if (!statsContent) return;
    statsContent.classList.toggle('hidden');
    const btn = statsContent.previousElementSibling;
    if (btn) btn.textContent = statsContent.classList.contains('hidden') ? '統計を表示' : '統計を非表示';

    if (!statsContent.classList.contains('hidden')) {
        loadStats();
    }
}

// 統計読込
async function loadStats() {
    const statsContent = document.getElementById('stats-content');
    if (!statsContent) return;
    try {
        const res = await fetch(`/api/${currentGenre}/quiz/stats`);
        const stats = await res.json();
        const fieldNames = {author:'作者', title:'作品名', style:'様式', image: '画像'};
        statsContent.innerHTML = `
            <div class="stats-grid">
                <div class="stats-card"><div>${stats.total_attempts}</div><div>総回答数</div></div>
                <div class="stats-card"><div>${stats.correct_attempts}</div><div>正解数</div></div>
                <div class="stats-card"><div>${stats.overall_accuracy}%</div><div>正答率</div></div>
            </div>
            <h4>分野別統計</h4>
            <div class="stats-grid">
                ${(stats.field_stats.map(f => `
                    <div class="stats-card">
                        <div>${f.accuracy}%</div>
                        <div>${fieldNames[f.field] || f.field}</div>
                    </div>`
                )).join('')}
            </div>
        `;
    } catch (error) {
        console.error('統計の読み込みに失敗:', error);
        statsContent.innerHTML = '<p>統計の読み込みに失敗しました。</p>';
    }
}

// クイズ統計リセット
async function resetQuizStats() {
    if (!confirm('本当にこのジャンルのクイズ結果をリセットしますか？')) return;
    try {
        const res = await fetch(`/api/${currentGenre}/quiz/reset`, { method: 'POST' });
        if (res.ok) {
            showMessage('クイズ結果をリセットしました', 'success');
            loadStats();
            document.getElementById('quiz-area').innerHTML = '';
        } else {
            const err = await res.json();
            showMessage('リセット失敗: ' + (err.detail || '不明なエラー'), 'error');
        }
    } catch (error) {
        showMessage('ネットワークエラー: ' + error.message, 'error');
    }
}

// メッセージ表示機能
function showMessage(message, type = 'info') {
    const container = document.querySelector('.app-container') || document.body;
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    container.insertBefore(messageDiv, container.firstChild);
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        setTimeout(() => messageDiv.remove(), 500);
    }, 3000);
}