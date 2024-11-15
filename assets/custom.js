document.addEventListener("DOMContentLoaded", function() {
    function adjustCardCHeight() {
        var cardA = document.getElementById('card-a');
        var cardB = document.getElementById('card-b');
        var cardC = document.getElementById('card-c');

        if (cardA && cardB && cardC) {
            var heightA = cardA.offsetHeight;
            var heightB = cardB.offsetHeight;
            var heightC = heightB - heightA;

            // Ensure heightC is not negative
            if (heightC < 0) {
                heightC = 0;
            }

            // Set the height of Card C
            cardC.style.height = heightC + 'px';
        }
    }

    // Adjust height once on load
    window.onload = adjustCardCHeight;

    // Set up a MutationObserver to detect changes in Cards A and B
    var targetA = document.getElementById('card-a');
    var targetB = document.getElementById('card-b');

    if (targetA && targetB) {
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                adjustCardCHeight();
            });
        });

        var config = { attributes: true, childList: true, subtree: true };
        observer.observe(targetA, config);
        observer.observe(targetB, config);
    }
});
