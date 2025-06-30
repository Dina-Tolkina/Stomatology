document.addEventListener("DOMContentLoaded", function () {
    if (window.location.hash) {
        var targetId = window.location.hash.substring(1); 
        var targetElement = document.getElementById(targetId); 

        if (targetElement) {
            setTimeout(function () {
                var parentCard = targetElement.closest(".p__item"); 
                if (!parentCard) parentCard = targetElement; 
                
                var elementRect = parentCard.getBoundingClientRect();
                var absoluteElementTop = window.scrollY + elementRect.top;
                var elementHeight = elementRect.height;
                
                var middleOffset = absoluteElementTop - (window.innerHeight / 2) + (elementHeight / 2);

                window.scrollTo({
                    top: middleOffset,
                    left: 0
                });
            }, 0);
        }
    }
});