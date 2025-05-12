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

  // =============================================
  // RECONNAISSANCE VOCALE AMÉLIORÉE
  // =============================================
  const micBtn = document.getElementById('micBtn');
  const userInput = document.getElementById('user-input');
  const voiceStatus = document.createElement('div'); // Création dynamique du statut
  
  // Configuration du statut vocal
  voiceStatus.id = 'voice-status';
  voiceStatus.className = 'voice-status';
  voiceStatus.textContent = 'Micro: inactif';
  micBtn.parentNode.insertBefore(voiceStatus, micBtn.nextSibling);

  let recognition;

  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'fr-FR';

      micBtn.addEventListener('click', function() {
          if (micBtn.classList.contains('recording')) {
              recognition.stop();
          } else {
              try {
                  recognition.start();
                  voiceStatus.textContent = "Micro: écoute en cours...";
                  voiceStatus.classList.add('voice-active');
                  micBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
                  micBtn.classList.add('recording');
              } catch (error) {
                  voiceStatus.textContent = "Erreur: " + error.message;
              }
          }
      });

      recognition.onresult = function(event) {
          const transcript = event.results[0][0].transcript;
          userInput.value = transcript;
          resetMicUI();
      };

      recognition.onerror = function(event) {
          voiceStatus.textContent = `Erreur: ${event.error}`;
          resetMicUI();
      };

      recognition.onend = function() {
          if (!micBtn.classList.contains('recording')) return;
          resetMicUI();
      };

      function resetMicUI() {
          voiceStatus.textContent = "Micro: inactif";
          voiceStatus.classList.remove('voice-active');
          micBtn.innerHTML = '<i class="bi bi-mic"></i>';
          micBtn.classList.remove('recording');
      }
  } else {
      micBtn.disabled = true;
      voiceStatus.textContent = "Micro: non supporté";
      micBtn.title = "Reconnaissance vocale non supportée par votre navigateur";
  }
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
recognition.onresult = function(event) {
  const transcript = event.results[0][0].transcript;
  userInput.value = transcript;
  
  // Déclenche l'envoi automatique
  const sendBtn = document.getElementById('send-btn');
  if (sendBtn) {
      sendBtn.click();  // Déclenche l'événement submit du formulaire
  }
  resetMicUI();
};