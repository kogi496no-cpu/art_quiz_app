// 美術検定クイズアプリ - JavaScript機能

// グローバル変数
let currentQuizMode = 'multiple'; // 'simple' または 'multiple'
let currentQuizData = null;
let quizAnswered = false;

// DOMContentLoaded時の初期化
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();

    // クイズページでのみ実行する初期化処理
    if (document.getElementById('quiz-area')) {
        setQuizMode('multiple');
        loadStats();
    }
});

// イベントリスナーの初期化
function initializeEventListeners() {
    // 画像アップロード対応フォーム
    const uploadForm = document.getElementById('art-form-upload');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUploadSubmit);
    }

    // 作品管理の表示/非表示切り替え
    const toggleBtn = document.getElementById('toggle-artworks-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleArtworksDisplay);
    }

    // 検索フォーム
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', e => {
            e.preventDefault();
            const query = document.getElementById('search-input').value;
            loadArtworks(query);
        });

        const searchInput = document.getElementById('search-input');
        searchInput.addEventListener('input', () => {
            loadArtworks(searchInput.value);
        });
    }

    // 編集フォーム
    const editForm = document.getElementById('edit-form');
    if (editForm) {
        editForm.addEventListener('submit', handleEditSubmit);
    }

    // 正答率リセットボタン
    const resetBtn = document.getElementById('reset-quiz-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetQuizStats);
    }
// クイズ統計リセット
async function resetQuizStats() {
    if (!confirm('本当にクイズ結果をリセットしますか？')) return;
    try {
        const res = await fetch('/quiz/reset', { method: 'POST' });
        if (res.ok) {
            showMessage('クイズ結果をリセットしました', 'success');
            loadStats();
        } else {
            const err = await res.json();
            showMessage('リセット失敗: ' + (err.detail || '不明なエラー'), 'error');
        }
    } catch (error) {
        showMessage('ネットワークエラーが発生しました', 'error');
    }
}
}

// HTMLエスケープ関数
function escapeHtml(text) {
    if (text === null || typeof text === 'undefined') {
        return '';
    }
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// URL検証関数
function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
        return false;
    }
}

// 画像アップロードフォームの送信処理
async function handleUploadSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);

    try {
        const response = await fetch('/api/artworks/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            showMessage(result.message + (result.image_uploaded ? '（画像付き）' : ''), 'success');
            e.target.reset();
            const artworksList = document.getElementById('artworks-list');
            if (artworksList && !artworksList.classList.contains('hidden')) {
                loadArtworks();
            }
        } else {
            const errorData = await response.json();
            showMessage('エラー: ' + (errorData.detail || '保存に失敗しました'), 'error');
        }
    } catch (error) {
        showMessage('エラー: ' + (error.message || error || 'ネットワークエラーが発生しました'), 'error', error);
    }
}

// メッセージ表示機能
function showMessage(message, type = 'info', e) {
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    document.body.appendChild(messageDiv);
    setTimeout(() => messageDiv.remove(), 3000);
    console.log(message);
    if (e) console.error(e);
}

// クイズ表示機能
async function loadQuiz() {
    const endpoint = currentQuizMode === 'multiple' ? '/quiz/multiple-choice' : '/quiz';
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

        if (currentQuizMode === 'multiple') {
            displayMultipleChoiceQuiz(data);
        } else {
            displaySimpleQuiz(data);
        }
    } catch (error) {
        document.getElementById('quiz-area').innerHTML = `<p>${error.message}</p>`;
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
            img.src = `/uploads/thumbnails/thumb_${choice}`;
            img.alt = '選択肢の画像';
            img.className = 'choice-image';
            // data-* 属性にファイル名を保存
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

// 簡単クイズ表示
function displaySimpleQuiz(data) {
    const quizArea = document.getElementById('quiz-area');
    displayArtworkInfo(data.quiz, quizArea);
    const answerButton = document.createElement('button');
    answerButton.textContent = '答えを見る';
    answerButton.className = 'btn btn-secondary';
    answerButton.onclick = () => showSimpleQuizAnswer();
    quizArea.appendChild(answerButton);
}

// 簡単クイズの答え表示
function showSimpleQuizAnswer() {
    if (quizAnswered) return;
    quizAnswered = true;
    const { answer_field, answer, notes } = currentQuizData;
    const resultDiv = document.createElement('div');
    resultDiv.className = 'quiz-result correct';
    resultDiv.innerHTML = `<h3>答え</h3><p><strong>${escapeHtml(answer_field)}:</strong> ${escapeHtml(answer)}</p>`;
    if (notes) {
        const notesP = document.createElement('p');
        notesP.innerHTML = `<strong>備考:</strong> ${escapeHtml(notes)}`;
        resultDiv.appendChild(notesP);
    }
    document.getElementById('quiz-area').appendChild(resultDiv);
}

// クイズ画像表示
function displayQuizImage(artwork, container) {
    const imageContainer = document.createElement('div');
    imageContainer.innerHTML = '<strong>画像:</strong> ';
    const imageToShow = artwork.image || artwork;

    const filename = imageToShow.filename || imageToShow.image_filename;

    // ファイル名が存在し、かつそれが「???」でないことを確認
    if (filename && filename !== "???") {
        const img = document.createElement('img');
        img.src = `/uploads/thumbnails/thumb_${filename}`;
        img.alt = '作品画像';
        img.className = 'quiz-image';
        img.onclick = () => window.open(`/uploads/images/${filename}`, '_blank');
        imageContainer.appendChild(img);
    } else if (filename === "???") {
        // クイズで画像が隠されている場合
        imageContainer.appendChild(document.createTextNode('???'));
    } else if (imageToShow.url && isValidUrl(imageToShow.url)) {
        const link = document.createElement('a');
        link.href = imageToShow.url;
        link.target = '_blank';
        link.textContent = '画像を見る';
        imageContainer.appendChild(link);
    } else {
        imageContainer.appendChild(document.createTextNode('画像なし'));
    }
    container.appendChild(imageContainer);
}

// 作品情報表示
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
    displayQuizImage(artwork, container);
}

// クイズモード切替
function setQuizMode(mode) {
    currentQuizMode = mode;
    const simpleBtn = document.getElementById('simple-mode-btn');
    const multipleBtn = document.getElementById('multiple-mode-btn');
    simpleBtn.className = mode === 'simple' ? 'btn btn-primary' : 'btn btn-secondary';
    multipleBtn.className = mode === 'multiple' ? 'btn btn-primary' : 'btn btn-secondary';
    document.getElementById('quiz-area').innerHTML = '';
    document.getElementById('stats-area').classList.toggle('hidden', mode !== 'multiple');
}

// 回答選択 (4択)
function selectAnswer(selectedChoice) {
    if (quizAnswered || !currentQuizData) return;
    quizAnswered = true;
    const { correct_answer, question_field } = currentQuizData;
    const isCorrect = selectedChoice === correct_answer;

    if (question_field === 'image') {
        document.querySelectorAll('.choice-image').forEach(img => {
            img.classList.add('disabled');
            // 正解の画像に correct クラスを付与
            if (img.dataset.filename === correct_answer) {
                img.classList.add('correct');
            }
            // 不正解で、かつ選択された画像だった場合に incorrect クラスを付与
            else if (img.dataset.filename === selectedChoice) {
                img.classList.add('incorrect');
            }
        });
    } else {
        document.querySelectorAll('.choice-button').forEach(button => {
            button.classList.add('disabled');
            if (button.textContent.includes(correct_answer)) {
                button.classList.add('correct');
            } else if (button.textContent.includes(selectedChoice) && !isCorrect) {
                button.classList.add('incorrect');
            }
        });
    }

    showQuizResult(isCorrect, selectedChoice);
    recordQuizResult(isCorrect, selectedChoice);
}

// クイズ結果表示 (4択)
function showQuizResult(isCorrect, selectedChoice) {
    const resultDiv = document.createElement('div');
    const { correct_answer, full_artwork_data, question_field } = currentQuizData;
    resultDiv.className = `quiz-result ${isCorrect ? 'correct' : 'incorrect'}`;

    if (isCorrect) {
        resultDiv.innerHTML = `<h3>🎉 正解です！</h3>`;
        if (question_field !== 'image') {
            resultDiv.innerHTML += `<p><strong>正答:</strong> ${escapeHtml(correct_answer)}</p>`;
        }
    } else {
        resultDiv.innerHTML = `<h3>❌ 不正解</h3>`;
        if (question_field !== 'image') {
            resultDiv.innerHTML += `<p><strong>あなたの回答:</strong> ${escapeHtml(selectedChoice)}</p><p><strong>正解:</strong> ${escapeHtml(correct_answer)}</p>`;
        }
    }

    if (isCorrect && full_artwork_data.notes) {
        const notesP = document.createElement('p');
        notesP.innerHTML = `<strong>備考:</strong> ${escapeHtml(full_artwork_data.notes)}`;
        resultDiv.appendChild(notesP);
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
        await fetch('/quiz/submit', {
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
    statsContent.classList.toggle('hidden');
    statsContent.previousElementSibling.textContent = statsContent.classList.contains('hidden') ? '統計を表示' : '統計を非表示';
    if (!statsContent.classList.contains('hidden')) loadStats();
}

// 統計読込
async function loadStats() {
    const statsContent = document.getElementById('stats-content');
    if (!statsContent || statsContent.classList.contains('hidden')) return;
    try {
        const res = await fetch('/quiz/stats');
        const stats = await res.json();
        statsContent.innerHTML = `
            <div class="stats-grid">
                <div class="stats-card"><div>${stats.total_attempts}</div><div>総回答数</div></div>
                <div class="stats-card"><div>${stats.correct_attempts}</div><div>正解数</div></div>
                <div class="stats-card"><div>${stats.overall_accuracy}%</div><div>正答率</div></div>
            </div>
            <h4>分野別統計</h4>
            <div class="stats-grid">${(stats.field_stats.map(f => `<div class="stats-card"><div>${f.accuracy}%</div><div>${{author:'作者',title:'作品名',style:'様式'}[f.field]||f.field}</div></div>`)).join('')}</div>
        `;
    } catch (error) {
        console.error('統計の読み込みに失敗:', error);
    }
}

// 作品一覧表示切替
function toggleArtworksDisplay() {
    const artworksList = document.getElementById('artworks-list');
    const toggleBtn = document.getElementById('toggle-artworks-btn');
    const isHidden = artworksList.classList.toggle('hidden');
    toggleBtn.textContent = isHidden ? '作品一覧を表示' : '作品一覧を非表示';
    toggleBtn.className = isHidden ? 'btn btn-toggle' : 'btn btn-secondary';
    if (!isHidden) {
        const query = document.getElementById('search-input')?.value || '';
        loadArtworks(query);
    }
}

// 作品一覧読込
async function loadArtworks(searchQuery = '') {
    try {
        const url = new URL('/api/artworks', window.location.origin);
        if (searchQuery) {
            url.searchParams.append('q', searchQuery);
        }
        
        const res = await fetch(url);
        const data = await res.json();
        const artworksArea = document.getElementById('artworks-list');
        
        if (data.artworks.length === 0) {
            artworksArea.innerHTML = '<p>該当する作品がありません。</p>';
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
        document.getElementById('artworks-list').innerHTML = '<p>データの取得に失敗しました。</p>';
    }
}

// 作品行作成
function createArtworkRow(artwork) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${artwork.id}</td>
        <td>${escapeHtml(artwork.author)}</td>
        <td>${escapeHtml(artwork.title)}</td>
        <td>${escapeHtml(artwork.style)}</td>
        <td>${escapeHtml(artwork.notes)}</td>
        <td></td>
        <td></td>
    `;

    const imageCell = row.children[5];
    if (artwork.image_filename) {
        const img = document.createElement('img');
        img.src = `/uploads/thumbnails/thumb_${artwork.image_filename}`;
        img.alt = '作品画像';
        img.className = 'thumbnail-image';
        img.onclick = () => window.open(`/uploads/images/${artwork.image_filename}`, '_blank');
        imageCell.appendChild(img);
    } else if (artwork.image_url) {
        const link = document.createElement('a');
        link.href = artwork.image_url;
        link.target = '_blank';
        link.textContent = 'URL';
        imageCell.appendChild(link);
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
    if (!confirm('この作品を削除してもよろしいですか？\n関連する画像ファイルも削除されます。')) return;
    try {
        const response = await fetch(`/api/artworks/${artworkId}`, { method: 'DELETE' });
        if (response.ok) {
            showMessage('作品を削除しました', 'success');
            loadArtworks();
        } else {
            const errorData = await response.json();
            showMessage('エラー: ' + (errorData.detail || '削除に失敗しました'), 'error');
        }
    } catch (error) {
        showMessage('ネットワークエラーが発生しました', 'error');
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
        const response = await fetch(`/api/artworks/${artworkId}`, {
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
        showMessage('ネットワークエラーが発生しました', 'error');
    }
}
