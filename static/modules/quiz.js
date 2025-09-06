// クイズ機能 (quiz.html)

let currentQuizData = null;
let quizAnswered = false;
import { escapeHtml, openMessageModal } from './utils.js';

export function applyTheme(genre) {
    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode');

    document.body.className = genre; // Start with base genre class

    if (mode === 'review') {
        document.body.classList.add('review-mode');
        const titleElement = document.querySelector('.container h1');
        if(titleElement) titleElement.innerHTML = '【集中復習モード】<span class="subtitle">弱点を克服せよ！</span>';
    }
}

export async function loadQuiz(genre) {
    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode');
    const quizArea = document.getElementById('quiz-area');

    const endpoint = (mode === 'review') ? `/api/${genre}/quiz/review` : `/api/${genre}/quiz/multiple-choice`;

    try {
        const res = await fetch(endpoint);
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "クイズの取得に失敗しました。");
        }
        const data = await res.json();
        currentQuizData = data;
        quizAnswered = false;
        quizArea.innerHTML = ''; // Clear before display
        displayMultipleChoiceQuiz(data, genre);
    } catch (error) {
        quizArea.innerHTML = `<p class="error">${error.message}</p>`;
        const backButton = document.createElement('a');
        backButton.href = '/';
        backButton.className = 'btn btn-secondary';
        backButton.textContent = 'ジャンル選択に戻る';
        quizArea.appendChild(backButton);
    }
}

export function displayMultipleChoiceQuiz(data, genre) {
    const quizArea = document.getElementById('quiz-area');
    displayArtworkInfo(data.artwork, quizArea, genre);
    const questionDiv = document.createElement('div');
    questionDiv.innerHTML = `<h3>${escapeHtml(data.question)}</h3>`;
    quizArea.appendChild(questionDiv);

    const choicesContainer = document.createElement('div');
    
    if (data.question_field === 'image') {
        choicesContainer.className = 'quiz-choices image-choices';
        data.choices.forEach(choice => {
            const img = document.createElement('img');
            const thumbPath = genre === 'japanese' ? 'japanese_thumbnails' : 'thumbnails';
            img.src = `/uploads/${thumbPath}/thumb_${choice}`;
            img.alt = '選択肢の画像';
            img.className = 'choice-image';
            img.dataset.filename = choice;
            img.onclick = () => selectAnswer(choice, genre);
            choicesContainer.appendChild(img);
        });
    } else {
        choicesContainer.className = 'quiz-choices';
        data.choices.forEach((choice, index) => {
            const choiceButton = document.createElement('button');
            choiceButton.className = 'choice-button';
            choiceButton.textContent = `${String.fromCharCode(65 + index)}. ${escapeHtml(choice)}`;
            choiceButton.onclick = () => selectAnswer(choice, genre);
            choicesContainer.appendChild(choiceButton);
        });
    }
    quizArea.appendChild(choicesContainer);
}

export function displayArtworkInfo(artwork, container, genre) {
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
        const thumbPath = genre === 'japanese' ? 'japanese_thumbnails' : 'thumbnails';
        img.src = `/uploads/${thumbPath}/thumb_${filename}`;
        img.alt = '作品画像';
        img.className = 'quiz-image';
        const imagePath = genre === 'japanese' ? 'japanese_images' : 'images';
        img.onclick = () => window.open(`/uploads/${imagePath}/${filename}`, '_blank');
        imageContainer.appendChild(img);
    } else if (filename === "???") {
        imageContainer.innerHTML = '<strong>画像:</strong> ???';
    } else {
        imageContainer.innerHTML = '<strong>画像:</strong> 画像なし';
    }
    container.appendChild(imageContainer);
}

export function selectAnswer(selectedChoice, genre) {
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

    showQuizResult(isCorrect, selectedChoice, genre);
    recordQuizResult(isCorrect, selectedChoice, genre);
}

export function showQuizResult(isCorrect, selectedChoice, genre) {
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

    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode');

    const nextButton = document.createElement('button');
    nextButton.className = 'btn btn-primary mt-3';
    nextButton.textContent = (mode === 'review') ? '次の復習問題へ' : '次のクイズ';
    nextButton.onclick = () => loadQuiz(genre);
    resultDiv.appendChild(nextButton);
    document.getElementById('quiz-area').appendChild(resultDiv);
}

export async function recordQuizResult(isCorrect, userAnswer, genre) {
    const { question_field, correct_answer, full_artwork_data } = currentQuizData;
    try {
        await fetch(`/api/${genre}/quiz/submit`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                artwork_id: full_artwork_data.id,
                question_field, 
                correct_answer, 
                user_answer: userAnswer, 
                is_correct: isCorrect 
            })
        });
    } catch (error) {
        console.error('結果の記録に失敗:', error);
    }
}