document.addEventListener('DOMContentLoaded', function () {
    function isTypingContext() {
        var tag = document.activeElement ? document.activeElement.tagName : '';
        return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT'
            || (document.activeElement && document.activeElement.isContentEditable);
    }

    var focusedTaskIndex = -1;

    document.addEventListener('keydown', function (e) {
        // AC1 — Ctrl/Cmd+N: new task
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            var url = document.body.dataset.urlNewTask;
            if (url) { e.preventDefault(); window.location.href = url; }
            return;
        }

        // AC4 — Ctrl/Cmd+F: focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            var searchInput = document.getElementById('task-search');
            if (searchInput) { e.preventDefault(); searchInput.focus(); searchInput.select(); }
            return;
        }

        // AC4 — Ctrl/Cmd+T: focus tag filter
        if ((e.ctrlKey || e.metaKey) && e.key === 't') {
            var tagFilter = document.getElementById('quick-tag-filter');
            if (tagFilter) {
                e.preventDefault();
                tagFilter.scrollIntoView({ behavior: 'smooth', block: 'center' });
                var firstLink = tagFilter.querySelector('a');
                if (firstLink) firstLink.focus();
            }
            return;
        }

        // AC3 — number keys 1–4: view navigation
        var viewMap = { '1': 'urlTaskList', '2': 'urlGraphView', '3': 'urlSplitView', '4': 'urlTagList' };
        if (!isTypingContext() && viewMap[e.key]) {
            var navUrl = document.body.dataset[viewMap[e.key]];
            if (navUrl) window.location.href = navUrl;
            return;
        }

        // AC2 — arrow keys + Space/Enter: task list navigation
        var taskListContainer = document.getElementById('task-list-container');
        if (taskListContainer && !isTypingContext()) {
            var items = taskListContainer.querySelectorAll('[data-task-pk]');
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                items.forEach(function (i) { i.classList.remove('kb-focused'); });
                if (e.key === 'ArrowDown') {
                    focusedTaskIndex = Math.min(focusedTaskIndex + 1, items.length - 1);
                } else {
                    focusedTaskIndex = Math.max(focusedTaskIndex - 1, 0);
                }
                if (items[focusedTaskIndex]) {
                    items[focusedTaskIndex].classList.add('kb-focused');
                    items[focusedTaskIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
                return;
            }
            if ((e.key === ' ' || e.key === 'Enter') && focusedTaskIndex >= 0 && items[focusedTaskIndex]) {
                e.preventDefault();
                var toggleForm = items[focusedTaskIndex].querySelector('form[action]');
                if (toggleForm) {
                    fetch(toggleForm.action, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': getCookie('csrftoken') },
                        body: new FormData(toggleForm),
                    }).then(function () { window.location.reload(); });
                }
                return;
            }
        }

        // AC6 — # key: focus tag input
        if (e.key === '#' && !isTypingContext()) {
            var tagInput = document.getElementById('quick-tag-name');
            if (tagInput) { e.preventDefault(); tagInput.focus(); }
            return;
        }

        // AC7 — ? key: help modal
        if (e.key === '?' && !isTypingContext()) {
            e.preventDefault();
            var helpModal = document.getElementById('shortcut-help-modal');
            if (helpModal && typeof bootstrap !== 'undefined') {
                bootstrap.Modal.getOrCreateInstance(helpModal).toggle();
            }
            return;
        }
    });

    // AC4 — search Enter key: navigate with ?q=
    var searchInput = document.getElementById('task-search');
    var suggestDropdown = document.getElementById('search-suggest-dropdown');
    if (searchInput) {
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                var params = new URLSearchParams(window.location.search);
                var q = searchInput.value.trim();
                if (q) { params.set('q', q); } else { params.delete('q'); }
                params.delete('page');
                window.location.search = params.toString();
            }
            if (e.key === 'Escape' && suggestDropdown) {
                suggestDropdown.classList.add('d-none');
                suggestDropdown.innerHTML = '';
            }
        });

        // Search-suggest autocomplete (AC6)
        if (suggestDropdown) {
            var suggestTimer = null;
            searchInput.addEventListener('input', function () {
                clearTimeout(suggestTimer);
                var q = searchInput.value.trim();
                if (q.length < 2) {
                    suggestDropdown.classList.add('d-none');
                    suggestDropdown.innerHTML = '';
                    return;
                }
                suggestTimer = setTimeout(function () {
                    fetch('/tasks/search-suggest/?q=' + encodeURIComponent(q))
                        .then(function (r) { return r.json(); })
                        .then(function (data) {
                            suggestDropdown.innerHTML = '';
                            if (!data.length) {
                                suggestDropdown.classList.add('d-none');
                                return;
                            }
                            data.forEach(function (item) {
                                var li = document.createElement('li');
                                li.className = 'list-group-item list-group-item-action';
                                li.setAttribute('role', 'option');
                                li.textContent = item.title;
                                li.addEventListener('mousedown', function (e) {
                                    e.preventDefault();
                                    searchInput.value = item.title;
                                    var params = new URLSearchParams(window.location.search);
                                    params.set('q', item.title);
                                    params.delete('page');
                                    window.location.search = params.toString();
                                });
                                suggestDropdown.appendChild(li);
                            });
                            suggestDropdown.classList.remove('d-none');
                        })
                        .catch(function () {
                            suggestDropdown.classList.add('d-none');
                        });
                }, 250);
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', function (e) {
                if (!suggestDropdown.contains(e.target) && e.target !== searchInput) {
                    suggestDropdown.classList.add('d-none');
                    suggestDropdown.innerHTML = '';
                }
            });
        }
    }

    // Date range inputs: navigate on change (AC3)
    document.querySelectorAll('.date-range-input').forEach(function (input) {
        input.addEventListener('change', function () {
            var params = new URLSearchParams(window.location.search);
            if (this.value) { params.set(this.dataset.param, this.value); }
            else { params.delete(this.dataset.param); }
            params.delete('page');
            window.location.search = params.toString();
        });
    });

    // Share Search button: copy URL to clipboard (AC8)
    var shareBtn = document.getElementById('share-search-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', function () {
            if (!navigator.clipboard) return;
            navigator.clipboard.writeText(window.location.href).then(function () {
                var orig = shareBtn.title;
                shareBtn.title = 'Copied!';
                shareBtn.setAttribute('aria-label', 'Copied!');
                setTimeout(function () {
                    shareBtn.title = orig;
                    shareBtn.setAttribute('aria-label', 'Share search');
                }, 2000);
            }).catch(function () {});
        });
    }
});
