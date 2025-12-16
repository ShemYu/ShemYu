// State
let currentProfile = {};
let currentSection = 'basics';

// Init
document.addEventListener('DOMContentLoaded', async () => {
    await loadProfile();
    loadSectionEditor();
});

// API Calls
async function loadProfile() {
    const res = await fetch('/api/profile');
    currentProfile = await res.json();
}

async function saveCurrentSection() {
    const editorContainer = document.getElementById('editor-container');

    let updateData;

    if (currentSection === 'basics') {
        updateData = getBasicsFormData();
    } else {
        updateData = getListFormData();
    }

    // Optimistic Update
    currentProfile[currentSection] = updateData;

    // API Call
    const res = await fetch(`/api/profile/${currentSection}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: updateData })
    });

    if (res.ok) {
        alert('Saved successfully!');
        refreshPreview();
    } else {
        alert('Error saving data.');
    }
}

async function runTailoring() {
    const jd = document.getElementById('jd-input').value;
    if (!jd) return alert('Please paste a Job Description.');

    const btn = document.querySelector('.btn-magic');
    const originalText = btn.innerText;
    btn.innerText = '✨ Magic Happening...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/tailor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jd_text: jd })
        });

        const tailoredProfile = await res.json();

        // Update Preview with Custom Data
        updatePreviewWithCustom(tailoredProfile);
        alert('Tailoring complete! Check the preview.');

    } catch (e) {
        alert('Error during tailoring: ' + e);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

async function triggerGenerate() {
    const res = await fetch('/api/generate', { method: 'POST' });
    const data = await res.json();
    alert(`Generation started! Check ${data.output_dir}`);
}

async function updatePreviewWithCustom(profile) {
    // We need to render this via backend to get HTML
    // Assuming we added a preview endpoint for custom json
    const res = await fetch('/preview/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile)
    });
    const html = await res.text();

    // Inject into iframe
    const iframe = document.getElementById('resume-preview');
    iframe.srcdoc = html;
}


// UI Logic
function showSection(id) {
    document.querySelectorAll('.content-section').forEach(el => el.classList.add('hidden'));
    document.getElementById(id + '-section').classList.remove('hidden');

    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
}

function loadSectionEditor() {
    const selector = document.getElementById('section-selector');
    currentSection = selector.value;
    const container = document.getElementById('editor-container');
    container.innerHTML = '';

    const data = currentProfile[currentSection];

    if (currentSection === 'basics') {
        renderBasicsForm(data, container);
    } else {
        renderListForm(data, container);
    }
}

function renderBasicsForm(data, container) {
    // Simple flat fields
    for (const [key, value] of Object.entries(data)) {
        if (typeof value === 'object') continue; // Skip complex nested for now

        const group = document.createElement('div');
        group.className = 'form-group';

        const label = document.createElement('label');
        label.className = 'form-label';
        label.innerText = key;

        const input = key === 'summary' ? document.createElement('textarea') : document.createElement('input');
        input.className = key === 'summary' ? 'form-textarea' : 'form-input';
        input.value = value || '';
        input.dataset.key = key;

        group.appendChild(label);
        group.appendChild(input);
        container.appendChild(group);
    }
}

function renderListForm(listData, container) {
    if (!listData) return;

    listData.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.dataset.index = index;

        const header = document.createElement('div');
        header.className = 'item-card-header';
        header.innerText = item.name || item.institution || item.company || `Item ${index + 1}`;
        card.appendChild(header);

        for (const [key, value] of Object.entries(item)) {
            if (key === 'highlights' || key === 'keywords') {
                // Array fields - simplified as textarea
                const group = document.createElement('div');
                group.className = 'form-group';

                const label = document.createElement('label');
                label.className = 'form-label';
                label.innerText = key + ' (one per line)';

                const input = document.createElement('textarea');
                input.className = 'form-textarea';
                input.value = Array.isArray(value) ? value.join('\n') : value;
                input.dataset.key = key;
                input.dataset.type = 'array';

                group.appendChild(label);
                group.appendChild(input);
                card.appendChild(group);
            } else if (typeof value !== 'object') {
                const group = document.createElement('div');
                group.className = 'form-group';

                const label = document.createElement('label');
                label.className = 'form-label';
                label.innerText = key;

                const input = document.createElement('input');
                input.className = 'form-input';
                input.value = value || '';
                input.dataset.key = key;

                group.appendChild(label);
                group.appendChild(input);
                card.appendChild(group);
            }
        }
        container.appendChild(card);
    });
}

function getBasicsFormData() {
    const data = { ...currentProfile.basics }; // Start with existing to keep nested stuff
    const inputs = document.querySelectorAll('#editor-container .form-input, #editor-container .form-textarea');
    inputs.forEach(input => {
        data[input.dataset.key] = input.value;
    });
    return data;
}

function getListFormData() {
    const items = [];
    const cards = document.querySelectorAll('.item-card');

    cards.forEach(card => {
        const item = {};
        const inputs = card.querySelectorAll('.form-input, .form-textarea');
        inputs.forEach(input => {
            const key = input.dataset.key;
            if (input.dataset.type === 'array') {
                item[key] = input.value.split('\n').filter(line => line.trim() !== '');
            } else {
                item[key] = input.value;
            }
        });
        // We might lose fields that are not rendered (complex nested), 
        // but for this MVP we render mostly everything important.
        items.push(item);
    });

    return items;
}

function refreshPreview() {
    const iframe = document.getElementById('resume-preview');
    iframe.src = '/preview/bible?t=' + new Date().getTime();
    if (iframe.srcdoc) iframe.srcdoc = ''; // Clear srcdoc if it was tailored
}
