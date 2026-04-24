import re

with open("f:/h1tn3s/github/project-verison1/starlift/templates/events.html", "r", encoding="utf-8") as f:
    content = f.read()

# Replace static grid with dynamic container
content = re.sub(
    r'<div class="events-grid">.*?</div>\s*</div>\s*<script>',
    '<div class="events-grid" id="eventsContainer"></div>\n</div>\n<script>\n',
    content,
    flags=re.DOTALL
)

# Replace script block entirely
script_block = """<script>
let eventsDataCache = {};

async function fetchEvents() {
    try {
        const response = await fetch('/api/events/');
        const events = await response.json();
        
        const container = document.getElementById('eventsContainer');
        if (!container) return;
        container.innerHTML = '';
        
        events.forEach(ev => {
            eventsDataCache[ev.id] = ev;
            
            const statusClass = ev.status === 'past' ? 'badge-inactive' : 'badge-active';
            const statusText = ev.status === 'past' ? 'Прошедшее' : 'Предстоящее';
            
            const card = document.createElement('article');
            card.className = 'event-card-large';
            card.dataset.eventId = ev.id;
            
            let cardLink = '';
            if (ev.link && ev.link !== 'None' && ev.link !== '') {
                cardLink = `<a href="${ev.link}" target="_blank" style="color: var(--sber-green); font-weight: 600; text-decoration: none;">Перейти на сайт</a>`;
            }

            let desc = ev.description && ev.description !== 'None' ? ev.description : '';
            if (desc.length > 120) desc = desc.substring(0, 120) + '...';

            card.innerHTML = `
                <div class="event-card-top">
                    <div class="event-date-box">
                        <span class="event-date-main">${ev.date && ev.date !== 'None' ? ev.date : 'Дата не указана'}</span>
                        <span class="event-date-sub">${ev.location && ev.location !== 'None' ? ev.location : 'Онлайн'}</span>
                    </div>
                    <span class="${statusClass}">${statusText}</span>
                </div>
                <h2 class="event-title-card" style="margin-top: 10px;">${ev.title}</h2>
                <p class="event-description-card">${desc}</p>
                <div class="event-card-bottom" style="margin-top:auto;">
                    ${cardLink}
                </div>
            `;
            
            card.addEventListener('click', () => openEventModal(ev.id));
            container.appendChild(card);
        });
    } catch(err) {
        console.error('Error fetching events:', err);
    }
}

function renderEventModal(eventId) {
    const ev = eventsDataCache[eventId];
    if (!ev) return;

    const statusClass = ev.status === 'past' ? 'badge-inactive' : 'badge-active';
    const statusText = ev.status === 'past' ? 'Завершено' : 'Запланировано';

    const badge = document.getElementById('eventStatusBadge');
    if (badge) {
        badge.className = statusClass;
        badge.textContent = statusText;
    }
    
    document.getElementById('eventModalTitle').textContent = ev.title;
    document.getElementById('eventModalDescription').textContent = ev.description && ev.description !== 'None' ? ev.description : 'Описание отсутствует';
    
    const coverAvatar = document.getElementById('eventCoverAvatar');
    if (coverAvatar) coverAvatar.style.display = 'none';
    
    document.getElementById('eventLocationLine').textContent = ev.location && ev.location !== 'None' ? ev.location : 'Онлайн/Офлайн';
    document.getElementById('eventCountLine').textContent = ev.date && ev.date !== 'None' ? ev.date : 'Дата уточняется';
    
    let formatHtml = 'Информация недоступна';
    if(ev.link && ev.link !== 'None') {
        formatHtml = `<a href="${ev.link}" target="_blank">Сайт конференции</a>`;
    }
    document.getElementById('eventFormatLine').innerHTML = formatHtml;

    document.getElementById('eventSpeakersList').innerHTML = '<p style="color:var(--text-muted);font-size:14px;">Информация по спикерам недоступна.</p>';
    document.getElementById('eventScheduleList').innerHTML = '<p style="color:var(--text-muted);font-size:14px;">Смотрите подробное расписание на официальном сайте мероприятия.</p>';
}

function openEventModal(eventId) {
    renderEventModal(eventId);
    const overlay = document.getElementById('eventModalOverlay');
    if (overlay) overlay.style.display = 'flex';
}

function initEventsPage() {
    fetchEvents();
}

initEventsPage();
document.addEventListener('spa-page-loaded', () => {
    if (document.getElementById('eventModalOverlay')) {
        initEventsPage();
    }
});
</script>"""

content = re.sub(
    r'<script>.*?</script>',
    script_block,
    content,
    flags=re.DOTALL
)

with open("f:/h1tn3s/github/project-verison1/starlift/templates/events.html", "w", encoding="utf-8") as f:
    f.write(content)
