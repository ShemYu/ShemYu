// State
let currentProfile = {};
let currentSection = 'basics';

// Init
document.addEventListener('DOMContentLoaded', async () => {
    await loadProfile();
    loadSectionEditor();
});

// --- API Logic ---

async function loadProfile() {
    const res = await fetch('/api/profile');
    currentProfile = await res.json();
}

async function saveCurrentSection() {
    const btn = document.querySelector('.btn-save');
    const originalText = btn.innerText;
    btn.innerText = 'Saving...';
    btn.disabled = true;

    try {
        const updateData = getCurrentFormData();

        // Optimistic Update
        currentProfile[currentSection] = updateData;

        // API Call
        const res = await fetch(`/api/profile/${currentSection}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data: updateData })
        });

        if (res.ok) {
            refreshPreview();
            setTimeout(() => { btn.innerText = 'Saved!'; }, 200);
            setTimeout(() => { btn.innerText = originalText; btn.disabled = false; }, 1500);
        } else {
            alert('Error saving data.');
            btn.innerText = originalText;
            btn.disabled = false;
        }
    } catch (e) {
        console.error(e);
        alert('Save failed');
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

async function runTailoring() {
    const jd = document.getElementById('jd-input').value;
    if (!jd) return alert('Please paste a Job Description.');

    const btn = document.querySelector('.btn-magic');
    const originalText = btn.innerHTML;
    btn.innerHTML = '✨ AI Working...';
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
        alert('Tailoring complete! Check preview.');

    } catch (e) {
        alert('Error during tailoring: ' + e);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function triggerGenerate() {
    const res = await fetch('/api/generate', { method: 'POST' });
    const data = await res.json();
    alert(`Generation started! Check ${data.output_dir}`);
}

async function triggerGeneratePDF() {
    const res = await fetch('/api/generate/pdf', { method: 'POST' });
    const data = await res.json();
    alert(`PDF Generation started! Check ${data.output_dir}`);
}

async function updatePreviewWithCustom(profile) {
    const res = await fetch('/preview/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile)
    });
    const html = await res.text();
    const iframe = document.getElementById('resume-preview');
    iframe.srcdoc = html;
}


// --- UI Logic ---

function showSection(id) {
    document.querySelectorAll('.content-section').forEach(el => el.classList.add('hidden'));
    document.getElementById(id + '-section').classList.remove('hidden');

    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    // Find nav item that called this
    const navItems = document.querySelectorAll('.nav-item');
    // Simple hack to highlight based on text content usually works or passed `event`
    // For now handled by onclick in HTML
    event.currentTarget.classList.add('active');
}

function loadSectionEditor() {
    const selector = document.getElementById('section-selector');
    currentSection = selector.value;
    const container = document.getElementById('editor-container');
    container.innerHTML = '';

    const data = currentProfile[currentSection];

    console.log(`Loading editor for: ${currentSection}`);

    // Switch Based on Section Type for specialized editors
    if (currentSection === 'basics') {
        renderBasicsEditor(data, container);
    } else if (['work', 'projects', 'education', 'certificates'].includes(currentSection)) {
        renderListEditor(data, container, currentSection);
    } else if (currentSection === 'skills') {
        renderListEditor(data, container, 'skills'); // Can be specialized further later
    } else {
        // Fallback
        renderListEditor(data, container, currentSection);
    }
}

// --- Component Renderers ---

function renderBasicsEditor(data, container) {
    // Basics is flat object mostly
    const card = createCard('Profile Details');

    const fields = [
        { key: 'name', label: 'Full Name' },
        { key: 'label', label: 'Professional Title' },
        { key: 'email', label: 'Email' },
        { key: 'phone', label: 'Phone' },
        { key: 'url', label: 'Website' },
        { key: 'location', label: 'Location (City, Country)' },
        { key: 'summary', label: 'Professional Summary', type: 'textarea' }
    ];

    fields.forEach(field => {
        card.appendChild(createField(field.key, field.label, data[field.key], field.type));
    });

    container.appendChild(card);

    // Profiles (Network)
    if (data.profiles) {
        const profileCard = createCard('Social Profiles');
        const listContainer = document.createElement('div');
        listContainer.className = 'dynamic-list-container';

        data.profiles.forEach((p, idx) => {
            const row = document.createElement('div');
            row.className = 'dynamic-item form-group';
            row.style.display = 'grid';
            row.style.gridTemplateColumns = '1fr 2fr';
            row.style.gap = '8px';

            const netInput = createInput(p.network || '', 'Network (e.g. GitHub)');
            netInput.dataset.key = 'network';
            netInput.dataset.isList = 'true';
            netInput.dataset.listIndex = idx;

            const urlInput = createInput(p.url || '', 'URL');
            urlInput.dataset.key = 'url';
            urlInput.dataset.isList = 'true';
            urlInput.dataset.listIndex = idx;

            row.appendChild(netInput);
            row.appendChild(urlInput);
            listContainer.appendChild(row);
        });
        profileCard.appendChild(listContainer);
        container.appendChild(profileCard);
    }
}

function renderListEditor(listData, container, type) {
    if (!listData) listData = [];

    listData.forEach((item, index) => {
        // Title logic
        let title = `Item ${index + 1}`;
        if (type === 'work') title = item.company || 'New Position';
        if (type === 'projects') title = item.name || 'New Project';
        if (type === 'education') title = item.institution || 'New School';
        if (type === 'skills') title = item.name || 'Skill Category';

        const card = createCard(title);
        card.dataset.index = index;
        card.className += ' list-item-card'; // Marker for collector

        // Fields based on type
        if (type === 'work') {
            const grid = createGrid(2);
            grid.appendChild(createField('company', 'Company', item.company));
            grid.appendChild(createField('position', 'Position', item.position));
            grid.appendChild(createField('startDate', 'Start Date', item.startDate));
            grid.appendChild(createField('endDate', 'End Date', item.endDate));
            card.appendChild(grid);

            card.appendChild(createField('summary', 'Summary', item.summary, 'textarea'));

            // Dynamic Highlights
            card.appendChild(createLabel('Highlights (Bullet Points)'));
            card.appendChild(createDynamicList(item.highlights || []));

        } else if (type === 'projects') {
            const grid = createGrid(2);
            grid.appendChild(createField('name', 'Project Name', item.name));
            grid.appendChild(createField('url', 'Project URL', item.url));
            grid.appendChild(createField('startDate', 'Start Date', item.startDate));
            grid.appendChild(createField('endDate', 'End Date', item.endDate));
            card.appendChild(grid);

            card.appendChild(createField('description', 'Description', item.description, 'textarea'));

            card.appendChild(createLabel('Highlights / Tech Stack'));
            card.appendChild(createDynamicList(item.highlights || []));

        } else if (type === 'skills') {
            card.appendChild(createField('name', 'Category Name', item.name));
            // Keywords as Tags or List? List is safer
            card.appendChild(createLabel('Keywords (Skills)'));
            card.appendChild(createDynamicList(item.keywords || []));
        } else {
            // Generic fallback
            for (const [k, v] of Object.entries(item)) {
                if (typeof v !== 'object') {
                    card.appendChild(createField(k, k, v));
                }
            }
        }

        container.appendChild(card);
    });
}


// --- Helper Components ---

function createCard(titleText) {
    const card = document.createElement('div');
    card.className = 'item-card';
    const header = document.createElement('div');
    header.className = 'item-card-header';
    header.innerText = titleText;
    card.appendChild(header);
    return card;
}

function createGrid(cols) {
    const div = document.createElement('div');
    div.style.display = 'grid';
    div.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    div.style.gap = '16px';
    div.style.marginBottom = '16px';
    return div;
}

function createLabel(text) {
    const label = document.createElement('label');
    label.className = 'form-label';
    label.innerText = text;
    return label;
}

function createInput(val, placeholder = '') {
    const input = document.createElement('input');
    input.className = 'form-input';
    input.value = val || '';
    input.placeholder = placeholder;
    return input;
}

function createField(key, labelText, value, type = 'text') {
    const group = document.createElement('div');
    group.className = 'form-group';

    group.appendChild(createLabel(labelText));

    const input = type === 'textarea' ? document.createElement('textarea') : document.createElement('input');
    input.className = type === 'textarea' ? 'form-textarea' : 'form-input';
    input.value = value || '';
    input.dataset.key = key;

    group.appendChild(input);
    return group;
}

function createDynamicList(items) {
    const container = document.createElement('div');
    container.className = 'dynamic-list';

    // Function to add a row
    const addRow = (text = '') => {
        const row = document.createElement('div');
        row.className = 'dynamic-item';

        const input = document.createElement('input');
        input.className = 'form-input dynamic-input';
        input.value = text;

        const btnRemove = document.createElement('button');
        btnRemove.className = 'btn-icon';
        btnRemove.innerHTML = '×';
        btnRemove.onclick = () => row.remove();

        row.appendChild(input);
        row.appendChild(btnRemove);
        container.appendChild(row);
    };

    // Render existing
    items.forEach(item => addRow(item));

    // Add Button
    const btnAdd = document.createElement('button');
    btnAdd.className = 'btn btn-secondary btn-add';
    btnAdd.innerText = '+ Add Item';
    btnAdd.onclick = (e) => { e.preventDefault(); addRow(); };

    // We append the button OUTSIDE the list container usually, or at the end
    const wrapper = document.createElement('div');
    wrapper.appendChild(container);
    wrapper.appendChild(btnAdd);

    return wrapper;
}

// --- Data Collection Logic ---

function getCurrentFormData() {
    // Strategy: We can't reuse the simple logic because DOM is complex now.
    // Specialize extraction based on section.

    if (currentSection === 'basics') {
        const data = { ...currentProfile.basics };
        // Simple fields
        const inputs = document.querySelectorAll('#editor-container .form-input, #editor-container .form-textarea');
        inputs.forEach(input => {
            if (input.closest('.dynamic-item')) return; // handled separately
            if (input.dataset.key) data[input.dataset.key] = input.value;
        });

        // Profiles? (Simplified: we didn't fully implement adding new profiles yet, just editing existing)
        // If we want to support profiles properly we need list collector logic.
        return data;
    }
    else {
        // List Sections
        const items = [];
        const cards = document.querySelectorAll('.list-item-card');

        cards.forEach(card => {
            const item = {};

            // Text Fields
            const inputs = card.querySelectorAll('.form-group > .form-input, .form-group > .form-textarea');
            inputs.forEach(input => {
                if (input.dataset.key) item[input.dataset.key] = input.value;
            });

            // Dynamic Lists (Highlights/Keywords)
            // Strategy: Find dynamic-list inside card
            const lists = card.querySelectorAll('.dynamic-list');
            lists.forEach(list => {
                // Determine key from the container or previous sibling label
                // Let's rely on data attributes which we need to set in renderListEditor
                // Wait, we need to update renderListEditor to set data-key on the label or container?
                // Simpler: Just check currentSection again, or stick to the hardcoded mapping for MVP robustness.

                let baseKey = 'highlights';
                if (currentSection === 'skills') baseKey = 'keywords';

                // Override if we add more lists later. For now, this covers Work/Projects (highlights) and Skills (keywords).

                const collected = [];
                list.querySelectorAll('.dynamic-input').forEach(inp => {
                    if (inp.value.trim()) collected.push(inp.value.trim());
                });

                item[baseKey] = collected;
            });

            items.push(item);
        });

        return items;
    }
}

function refreshPreview() {
    const iframe = document.getElementById('resume-preview');
    iframe.src = '/preview/bible?t=' + new Date().getTime();
    if (iframe.srcdoc) iframe.srcdoc = '';
}
