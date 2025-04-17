// Navigation active
document.addEventListener('DOMContentLoaded', function() {
    // Récupère le chemin actuel
    const currentPath = window.location.pathname;
    
    // Récupère tous les liens de navigation
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    // Marque le lien actif
    navLinks.forEach(link => {
      if (link.getAttribute('href') === currentPath) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  
    // Créer un logo placeholder si nécessaire
    createLogoIfMissing();
  });
  
  // Fonction pour créer un logo textuel si l'image de logo est manquante
  function createLogoIfMissing() {
    const logoImg = document.querySelector('.navbar-brand img');
    if (logoImg) {
      logoImg.onerror = function() {
        this.style.display = 'none';
        const brand = document.querySelector('.navbar-brand');
        brand.innerHTML = 'Cogi <span class="badge bg-light text-success">AI</span>';
      };
    }
  }
  
  // Fonction pour formater la date et l'heure pour les messages
  function formatTimestamp() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
  }