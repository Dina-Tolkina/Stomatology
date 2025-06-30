document.querySelectorAll('.dropdown details').forEach(detail => {
    detail.addEventListener('toggle', function() {
        const parentItem = this.closest('.p__item'); 
        if (this.open) {
            parentItem.classList.add('open'); 
        } else {
            if (!parentItem.querySelector('details[open]')) {
                parentItem.classList.remove('open');
            }
        }
    });
});
