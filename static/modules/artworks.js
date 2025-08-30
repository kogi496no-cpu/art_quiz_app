// 作品管理機能 (artworks.html)


import { escapeHtml, openMessageModal } from './utils.js';

// 作品登録 (画像アップロード対応)
export async function handleUploadSubmit(e, genre) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const apiUrl = `/api/${genre}/artworks/upload`;

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
export async function loadArtworks(searchQuery = '', genre) {
    const artworksArea = document.getElementById('artworks-list');
    const artworkCountSpan = document.getElementById('artwork-count');
    if (!artworksArea) return;

    try {
        const url = new URL(`/api/${genre}/artworks`, window.location.origin);
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
        data.artworks.forEach(artwork => table.appendChild(createArtworkRow(artwork, genre)));
        tableContainer.appendChild(table);
        artworksArea.innerHTML = '';
        artworksArea.appendChild(tableContainer);
    } catch (error) {
        artworksArea.innerHTML = `<p>データの取得に失敗しました: ${error.message}</p>`;
    }
}

// 作品テーブルの行を作成
export function createArtworkRow(artwork, genre) {
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
        const thumbPath = genre === 'japanese' ? 'japanese_thumbnails' : 'thumbnails';
        img.src = `/uploads/${thumbPath}/thumb_${artwork.image_filename}`;
        img.alt = '作品画像';
        img.className = 'thumbnail-image';
        const imagePath = genre === 'japanese' ? 'japanese_images' : 'images';
        img.onclick = () => window.open(`/uploads/${imagePath}/${artwork.image_filename}`, '_blank');
        imageCell.appendChild(img);
    } else {
        imageCell.textContent = 'なし';
    }

    const actionCell = row.children[6];
    const editBtn = document.createElement('button');
    editBtn.textContent = '編集';
    editBtn.className = 'btn btn-secondary';
    editBtn.onclick = () => openEditModal(artwork, genre);
    actionCell.appendChild(editBtn);

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = '削除';
    deleteBtn.className = 'btn btn-danger';
    deleteBtn.onclick = () => deleteArtwork(artwork.id, genre);
    actionCell.appendChild(deleteBtn);

    return row;
}

// 作品削除
export async function deleteArtwork(artworkId, genre) {
    if (!confirm('この作品を削除してもよろしいですか？')) return;
    try {
        const response = await fetch(`/api/${genre}/artworks/${artworkId}`, { method: 'DELETE' });
        if (response.ok) {
            openMessageModal('作品を削除しました', 'success');
            loadArtworks('', genre);
        } else {
            const errorData = await response.json();
            openMessageModal('エラー: ' + (errorData.detail || '削除に失敗しました'), 'error');
        }
    } catch (error) {
        openMessageModal('ネットワークエラー: ' + error.message, 'error');
    }
}

// 編集モーダルを開く
export function openEditModal(artwork, genre) {
    document.getElementById('edit-artwork-id').value = artwork.id;
    document.getElementById('edit-author').value = artwork.author;
    document.getElementById('edit-title').value = artwork.title;
    document.getElementById('edit-style').value = artwork.style;
    document.getElementById('edit-notes').value = artwork.notes || '';
    document.getElementById('edit-modal').style.display = 'block';
}

// 編集モーダルを閉じる
export function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

// 編集フォーム送信
export async function handleEditSubmit(e, genre) {
    e.preventDefault();
    const artworkId = document.getElementById('edit-artwork-id').value;
    const data = {
        author: document.getElementById('edit-author').value,
        title: document.getElementById('edit-title').value,
        style: document.getElementById('edit-style').value,
        notes: document.getElementById('edit-notes').value,
    };

    try {
        const response = await fetch(`/api/${genre}/artworks/${artworkId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        if (response.ok) {
            openMessageModal('更新しました', 'success');
            closeEditModal();
            loadArtworks('', genre);
        } else {
            const errorData = await response.json();
            openMessageModal('エラー: ' + (errorData.detail || '更新に失敗しました'), 'error');
        }
    } catch (error) {
        openMessageModal('ネットワークエラー: ' + error.message, 'error');
    }
}
