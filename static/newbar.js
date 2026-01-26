const linkItems = document.querySelectorAll(".link-item");

function setActive() {
    const path = window.location.pathname;
    let found = false;

    linkItems.forEach((linkItem) => {
        const href = linkItem.getAttribute('href');
        if (path === href || (href !== '/' && path.startsWith(href))) {
            document.querySelector(".active")?.classList.remove("active");
            linkItem.classList.add("active");
            found = true;
        }
    });

    if (!found && path === '/') {
        linkItems[0].classList.add("active");
    }
}

// Initial state
setActive();

// Handle clicks (reloads mostly)
linkItems.forEach(item => {
    item.addEventListener('click', () => {
        document.querySelector(".active")?.classList.remove("active");
        item.classList.add("active");
    });
});