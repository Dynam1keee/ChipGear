document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('search-input');
    const suggestions = document.getElementById('search-suggestions');

    if (!input || !suggestions) return;

    let debounceTimer;
    let controller;

    function hideSuggestions() {
        suggestions.style.display = 'none';
        suggestions.replaceChildren();
    }

    function renderSuggestions(results) {
        suggestions.replaceChildren();

        if (!results.length) {
            hideSuggestions();
            return;
        }

        results.forEach((product) => {
            const link = document.createElement('a');
            link.href = product.url;
            link.className = 'search-suggestion-item';

            if (product.image) {
                const image = document.createElement('img');
                image.src = product.image;
                image.alt = '';
                image.className = 'search-suggestion-image';
                link.appendChild(image);
            }

            const name = document.createElement('span');
            name.className = 'search-suggestion-name';
            name.textContent = product.name;

            link.appendChild(name);
            suggestions.appendChild(link);
        });

        suggestions.style.display = 'block';
    }

    async function fetchSuggestions() {
        const query = input.value.trim();

        if (query.length < 2) {
            if (controller) controller.abort();
            hideSuggestions();
            return;
        }

        if (controller) controller.abort();
        controller = new AbortController();

        const params = new URLSearchParams({
            q: query,
            suggestions: '1',
        });

        const category = input.dataset.category;

        if (category && category !== 'all') {
            params.set('category', category);
        }

        try {
            const response = await fetch(
                `${input.dataset.suggestionsUrl}?${params}`,
                {
                    signal: controller.signal,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Не вдалося отримати результати пошуку');
            }

            const data = await response.json();

            // Не показуємо результати для застарілого запиту
            if (input.value.trim() !== query) return;

            renderSuggestions(data.results);
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error(error);
                hideSuggestions();
            }
        }
    }

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(fetchSuggestions, 250);
    });

    document.addEventListener('click', (event) => {
        if (!input.contains(event.target) &&
            !suggestions.contains(event.target)) {
            hideSuggestions();
        }
    });

    input.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            hideSuggestions();
        }
    });

    $('#category-select').change(function () {
        var categorySlug = $(this).val();
        var form = $('#search-form');
        var newActionUrl;
        if (categorySlug == 'all') {
            newActionUrl = form.data('url-all');
        } else {
            newActionUrl = form.data('url-category').replace('placeholder', categorySlug);
        }
        form.attr('action', newActionUrl);
    });
});