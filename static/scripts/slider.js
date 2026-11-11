console.log("Скрипт завантажився");

$(document).ready(function () {
    console.log("jQuery ready працює");
    const rangeInput = document.querySelectorAll(".range-input input");
    const priceInput = document.querySelectorAll(".price-input input");
    const progress = document.querySelector(".slider .progress");

    const priceGap = 1;

    function updateProgress() {
        const min = Number(rangeInput[0].min);
        const max = Number(rangeInput[0].max);
        const minVal = Number(rangeInput[0].value);
        const maxVal = Number(rangeInput[1].value);

        const range = max - min;

        if (range <= 0) return;

        progress.style.left = ((minVal - min) / range) * 100 + "%";
        progress.style.right = ((max - maxVal) / range) * 100 + "%";
        console.log({ min, max, minVal, maxVal });
    }

    // Початкове положення смуги
    updateProgress();

    // Зміна числових полів
    priceInput.forEach((input) => {
        input.addEventListener("input", (e) => {
            let minPrice = Number(priceInput[0].value);
            let maxPrice = Number(priceInput[1].value);

            if (priceInput[0].value === "" || priceInput[1].value === "") {
                return;
            }

            const min = Number(rangeInput[0].min);
            const max = Number(rangeInput[0].max);

            minPrice = Math.max(min, Math.min(minPrice, max));
            maxPrice = Math.max(min, Math.min(maxPrice, max));

            if (maxPrice - minPrice < priceGap) {
                if (e.target.classList.contains("input-min")) {
                    minPrice = maxPrice - priceGap;
                } else {
                    maxPrice = minPrice + priceGap;
                }
            }

            if (minPrice > maxPrice) return;

            rangeInput[0].value = minPrice;
            rangeInput[1].value = maxPrice;

            priceInput[0].value = minPrice;
            priceInput[1].value = maxPrice;

            updateProgress();
        });
    });

    // Зміна повзунків
    rangeInput.forEach((input) => {
        input.addEventListener("input", (e) => {
            let minVal = Number(rangeInput[0].value);
            let maxVal = Number(rangeInput[1].value);

            if (maxVal - minVal < priceGap) {
                if (e.target.classList.contains("range-min")) {
                    rangeInput[0].value = maxVal - priceGap;
                } else {
                    rangeInput[1].value = minVal + priceGap;
                }
            }

            minVal = Number(rangeInput[0].value);
            maxVal = Number(rangeInput[1].value);

            priceInput[0].value = minVal;
            priceInput[1].value = maxVal;

            updateProgress();
        });
    });
});