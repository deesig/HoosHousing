document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.querySelector(".hamburger");
    const navbarRight = document.querySelector(".navbar-right");
    
    hamburger.addEventListener("click", () => {
      hamburger.classList.toggle("active");
      navbarRight.classList.toggle("active");
    });
    
    // Close the menu when a link is clicked
    document.querySelectorAll(".nav-item").forEach(n => n.addEventListener("click", function() {
      hamburger.classList.remove("active");
      navbarRight.classList.remove("active");
    }));
  });