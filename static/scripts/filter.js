$(document).ready(function () {
    let timeout = null;
    const priceGap = 0;

    const sliderDelay = 500;
    const priceInputDelay = 1000;

    initEventHandlers();

    // Update the slider's progress bar
    function updateProgress(rangeInput, range) {
        const min = Number(rangeInput[0].min);
        const max = Number(rangeInput[0].max);
        const minVal = Number(rangeInput[0].value);
        const maxVal = Number(rangeInput[1].value);
        const difference = max - min;

        if (difference <= 0) {
            return;
        }

        range.style.left =
            ((minVal - min) / difference) * 100 + "%";

        range.style.right =
            ((max - maxVal) / difference) * 100 + "%";
    }

    // Show the overlay immediately and debounce the AJAX request
    function scheduleUpdate(delay = sliderDelay) {
        if (timeout) {
            clearTimeout(timeout);
        }

        $('#products-overlay')
            .removeClass('d-none')
            .addClass('d-block');

        timeout = setTimeout(function () {
            normalizePriceInputs();
            updateData(false);
        }, delay);
    }

    // Validate and synchronize the price inputs and sliders
    function normalizePriceInputs() {
        const rangeInput = document.querySelectorAll(
            '.range-input input'
        );

        const priceInput = document.querySelectorAll(
            '.price-input input'
        );

        const range = document.querySelector('.slider .progress');

        if (
            rangeInput.length < 2 ||
            priceInput.length < 2 ||
            !range
        ) {
            return;
        }

        const min = Number(rangeInput[0].min);
        const max = Number(rangeInput[0].max);

        let minValue = Number(priceInput[0].value.trim());
        let maxValue = Number(priceInput[1].value.trim());

        // Restore default values if the input is invalid
        if (
            priceInput[0].value.trim() === '' ||
            !Number.isFinite(minValue) ||
            minValue < min ||
            minValue > max
        ) {
            minValue = min;
        }

        if (
            priceInput[1].value.trim() === '' ||
            !Number.isFinite(maxValue) ||
            maxValue < min ||
            maxValue > max
        ) {
            maxValue = max;
        }

        // Restore the full range if the minimum exceeds the maximum
        if (minValue > maxValue) {
            minValue = min;
            maxValue = max;
        }

        priceInput[0].value = minValue;
        priceInput[1].value = maxValue;

        rangeInput[0].value = minValue;
        rangeInput[1].value = maxValue;

        updateProgress(rangeInput, range);
    }

    function initEventHandlers() {
        const rangeInput = document.querySelectorAll(
            '.range-input input'
        );

        const priceInput = document.querySelectorAll(
            '.price-input input'
        );

        const range = document.querySelector('.slider .progress');

        if (
            rangeInput.length < 2 ||
            priceInput.length < 2 ||
            !range
        ) {
            return;
        }

        updateProgress(rangeInput, range);

        // Manual price input
        priceInput.forEach(function (input) {
            input.oninput = function () {
                const minText = priceInput[0].value.trim();
                const maxText = priceInput[1].value.trim();

                // Synchronize sliders only when both values are valid
                if (minText !== '' && maxText !== '') {
                    const minValue = Number(minText);
                    const maxValue = Number(maxText);

                    const min = Number(rangeInput[0].min);
                    const max = Number(rangeInput[0].max);

                    if (
                        Number.isFinite(minValue) &&
                        Number.isFinite(maxValue) &&
                        minValue >= min &&
                        maxValue <= max &&
                        minValue <= maxValue
                    ) {
                        rangeInput[0].value = minValue;
                        rangeInput[1].value = maxValue;

                        updateProgress(rangeInput, range);
                    }
                }

                // Wait 1200 ms after the last keystroke
                scheduleUpdate(priceInputDelay);
            };
        });

        // Range sliders
        rangeInput.forEach(function (input) {
            input.oninput = function (event) {
                let minValue = Number(rangeInput[0].value);
                let maxValue = Number(rangeInput[1].value);

                if (maxValue - minValue < priceGap) {
                    if (
                        event.target.classList.contains('range-min')
                    ) {
                        rangeInput[0].value =
                            maxValue - priceGap;
                    } else {
                        rangeInput[1].value =
                            minValue + priceGap;
                    }
                }

                minValue = Number(rangeInput[0].value);
                maxValue = Number(rangeInput[1].value);

                priceInput[0].value = minValue;
                priceInput[1].value = maxValue;

                updateProgress(rangeInput, range);

                scheduleUpdate(sliderDelay);
            };
        });

        // Other filters
        $('#filter-form input, #filter-form select')
            .not(
                '#min-price-input, ' +
                '#max-price-input, ' +
                '#min-price-slider, ' +
                '#max-price-slider'
            )
            .off('input.filter change.filter')
            .on('input.filter change.filter', function () {
                scheduleUpdate(sliderDelay);
            });

        // Reset filters
        $('#reset-button')
            .off('click.priceFilter')
            .on('click.priceFilter', function (event) {
                event.preventDefault();

                if (timeout) {
                    clearTimeout(timeout);
                }

                $('#products-overlay')
                    .removeClass('d-none')
                    .addClass('d-block');

                timeout = setTimeout(function () {
                    updateData(true);
                }, sliderDelay);
            });
    }

    // Fetch updated products and filters
    function updateData(reset) {
        const form = $('#filter-form');
        const url = form.attr('action');

        let data = form.serializeArray();

        const qValue = getQueryParam('q');

        if (qValue) {
            data.push({
                name: 'q',
                value: qValue
            });
        }

        if (reset) {
            data = qValue
                ? [{ name: 'q', value: qValue }]
                : [];
        }

        $.ajax({
            url: url,
            type: 'GET',
            data: data,

            success: function (response) {
                const container = $('#filters-and-goods');
                const responseHtml = $(response);

                // Update product quantity
                const newQuantity = responseHtml
                    .find('#products-quantity')
                    .html();

                if (newQuantity !== undefined) {
                    $('#products-quantity').html(newQuantity);
                }

                // Get updated catalog content
                const newContent = responseHtml
                    .find('#filters-and-goods')
                    .html();

                if (newContent === undefined) {
                    console.error(
                        'Не вдалося знайти #filters-and-goods у відповіді.'
                    );

                    return;
                }

                // Save expanded filter groups
                const expandedFilters = [];

                container.find('.collapse.show').each(function () {
                    expandedFilters.push(this.id);
                });

                // Save scroll positions inside filter lists
                const scrollPositions = {};

                container.find('.collapse .overflow-auto').each(function () {
                    const collapseId = $(this)
                        .closest('.collapse')
                        .attr('id');

                    if (collapseId) {
                        scrollPositions[collapseId] = this.scrollTop;
                    }
                });

                // Replace catalog content
                container.html(newContent);

                // Restore expanded filter groups
                expandedFilters.forEach(function (id) {
                    const element = document.getElementById(id);

                    if (element && container[0].contains(element)) {
                        element.classList.add('show');

                        const trigger = container[0].querySelector(
                            '[href="#' + id + '"]'
                        );

                        if (trigger) {
                            trigger.setAttribute('aria-expanded', 'true');
                        }
                    }
                });

                // Restore scroll positions
                container.find('.collapse .overflow-auto').each(function () {
                    const collapseId = $(this)
                        .closest('.collapse')
                        .attr('id');

                    if (
                        collapseId &&
                        scrollPositions[collapseId] !== undefined
                    ) {
                        this.scrollTop = scrollPositions[collapseId];
                    }
                });

                $('#show-filters').addClass('show');

                $('#products-overlay')
                    .removeClass('d-block')
                    .addClass('d-none');

                // Reinitialize handlers for the new DOM elements
                initEventHandlers();
            },

            error: function () {
                console.error('Помилка оновлення товарів');

                $('#products-overlay')
                    .removeClass('d-block')
                    .addClass('d-none');
            },

            complete: function () {
                $('#products-overlay')
                    .removeClass('d-block')
                    .addClass('d-none');
            }
        });
    }

    function getQueryParam(name) {
        const urlParams = new URLSearchParams(
            window.location.search
        );

        return urlParams.get(name);
    }
});