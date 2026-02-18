/**
 * Tag autocomplete and quick-create functionality for task forms.
 * Depends on getCookie() from base.js and TAG_COLORS global from template.
 */
document.addEventListener('DOMContentLoaded', function() {
    var tagColors = (typeof TAG_COLORS !== 'undefined') ? TAG_COLORS : {};

    // Apply colors to existing tag badges
    var tagSelection = document.getElementById('tag-selection');
    if (tagSelection) {
        tagSelection.querySelectorAll('.tag-select-option').forEach(function(label) {
            var input = label.querySelector('input[type="checkbox"]');
            var badge = label.querySelector('.badge');
            if (input && badge && tagColors[input.value]) {
                badge.style.backgroundColor = tagColors[input.value];
            }
        });
    }

    // Quick-create tag
    var quickBtn = document.getElementById('quick-tag-btn');
    var quickInput = document.getElementById('quick-tag-name');
    var quickFeedback = document.getElementById('quick-tag-feedback');

    if (quickBtn && quickInput) {
        quickBtn.addEventListener('click', function() {
            var name = quickInput.value.trim();
            if (!name) {
                showFeedback('Please enter a tag name.', 'text-warning');
                return;
            }
            quickBtn.disabled = true;
            fetch('/tasks/tags/quick-create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({name: name}),
            })
            .then(function(response) { return response.json().then(function(data) { return {ok: response.ok, data: data}; }); })
            .then(function(result) {
                if (result.ok) {
                    addTagCheckbox(result.data.id, result.data.name, result.data.color);
                    quickInput.value = '';
                    showFeedback('Tag "' + result.data.name + '" created!', 'text-success');
                } else {
                    showFeedback(result.data.error || 'Could not create tag.', 'text-danger');
                }
            })
            .catch(function() {
                showFeedback('Network error. Please try again.', 'text-danger');
            })
            .finally(function() {
                quickBtn.disabled = false;
            });
        });

        quickInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                quickBtn.click();
            }
        });
    }

    // Autocomplete
    var autocompleteTimeout = null;
    var autocompleteDropdown = null;

    if (quickInput) {
        autocompleteDropdown = document.createElement('div');
        autocompleteDropdown.className = 'list-group position-absolute';
        autocompleteDropdown.style.cssText = 'z-index: 1000; max-height: 200px; overflow-y: auto; width: 100%; display: none;';
        quickInput.parentElement.style.position = 'relative';
        quickInput.parentElement.appendChild(autocompleteDropdown);

        quickInput.addEventListener('input', function() {
            clearTimeout(autocompleteTimeout);
            var q = quickInput.value.trim();
            if (q.length < 1) {
                autocompleteDropdown.style.display = 'none';
                return;
            }
            autocompleteTimeout = setTimeout(function() {
                fetch('/tasks/tags/autocomplete/?q=' + encodeURIComponent(q))
                .then(function(r) { return r.json(); })
                .then(function(tags) {
                    autocompleteDropdown.innerHTML = '';
                    if (tags.length === 0) {
                        autocompleteDropdown.style.display = 'none';
                        return;
                    }
                    tags.forEach(function(tag) {
                        var item = document.createElement('button');
                        item.type = 'button';
                        item.className = 'list-group-item list-group-item-action d-flex align-items-center gap-2 py-1';
                        item.innerHTML = '<span class="badge" style="background-color: ' + tag.color + ';">' + tag.name + '</span> <small class="text-muted">Select</small>';
                        item.addEventListener('click', function() {
                            selectExistingTag(tag.id, tag.name, tag.color);
                            quickInput.value = '';
                            autocompleteDropdown.style.display = 'none';
                        });
                        autocompleteDropdown.appendChild(item);
                    });
                    autocompleteDropdown.style.display = 'block';
                });
            }, 300);
        });

        document.addEventListener('click', function(e) {
            if (!quickInput.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
                autocompleteDropdown.style.display = 'none';
            }
        });
    }

    function selectExistingTag(id, name, color) {
        // Check the existing checkbox if it exists
        var checkbox = document.querySelector('#tag-selection input[value="' + id + '"]');
        if (checkbox) {
            checkbox.checked = true;
            return;
        }
        // If not in the form yet, add it
        addTagCheckbox(id, name, color);
    }

    function addTagCheckbox(id, name, color) {
        if (!tagSelection) return;
        // Remove "No tags yet" message if present
        var emptyMsg = tagSelection.querySelector('p.text-muted');
        if (emptyMsg) emptyMsg.remove();

        // Check if checkbox already exists
        var existing = tagSelection.querySelector('input[value="' + id + '"]');
        if (existing) {
            existing.checked = true;
            return;
        }

        var label = document.createElement('label');
        label.className = 'tag-select-option';
        label.style.cursor = 'pointer';
        label.innerHTML = '<input type="checkbox" name="tags" value="' + id + '" checked>' +
            '<span class="badge fs-6" style="background-color: ' + color + '; opacity: 0.6;">' + name + '</span>';
        tagSelection.appendChild(label);
        tagColors[id] = color;
    }

    function showFeedback(msg, cls) {
        if (!quickFeedback) return;
        quickFeedback.textContent = msg;
        quickFeedback.className = 'small mt-1 ' + cls;
        setTimeout(function() { quickFeedback.textContent = ''; }, 3000);
    }
});
