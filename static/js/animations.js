/**
 * ScholarMate - Enhanced UI Animations and Interactions
 */
// Fade in elements on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};
const fadeInObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in');
            fadeInObserver.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe all cards and sections
document.addEventListener('DOMContentLoaded', () => {
    const elements = document.querySelectorAll('.card-enhanced, .section-animate');
    elements.forEach(el => fadeInObserver.observe(el));
});

// Smooth scroll to anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Loading state for buttons
function addLoadingState(button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `
        <svg class="animate-spin inline-block w-5 h-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Loading...
    `;
    
    return () => {
        button.disabled = false;
        button.innerHTML = originalText;
    };
}

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 z-50 alert alert-${type} slide-in shadow-xl max-w-md`;
    toast.innerHTML = `
        <div class="flex items-center">
            <span class="mr-2">${getToastIcon(type)}</span>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function getToastIcon(type) {
    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
        warning: '⚠'
    };
    return icons[type] || icons.info;
}

// Copy to clipboard with feedback
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.innerHTML;
        button.innerHTML = '✓ Copied!';
        button.classList.add('bg-green-600');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('bg-green-600');
        }, 2000);
    }).catch(err => {
        showToast('Failed to copy', 'error');
    });
}

// Form validation with visual feedback
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('border-red-500');
            input.classList.remove('border-gray-600');
            isValid = false;
            
            // Add error message
            if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('error-message')) {
                const error = document.createElement('p');
                error.className = 'error-message text-red-500 text-sm mt-1';
                error.textContent = 'This field is required';
                input.parentNode.insertBefore(error, input.nextSibling);
            }
        } else {
            input.classList.remove('border-red-500');
            input.classList.add('border-gray-600');
            
            // Remove error message
            const error = input.nextElementSibling;
            if (error && error.classList.contains('error-message')) {
                error.remove();
            }
        }
    });
    
    return isValid;
}

// Auto-resize textarea
document.querySelectorAll('textarea').forEach(textarea => {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
});

// Progress bar animation
function animateProgressBar(element, targetWidth) {
    let width = 0;
    const interval = setInterval(() => {
        if (width >= targetWidth) {
            clearInterval(interval);
        } else {
            width++;
            element.style.width = width + '%';
        }
    }, 10);
}

// Typing effect for text
function typeWriter(element, text, speed = 50) {
    let i = 0;
    element.innerHTML = '';
    
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    
    type();
}

// Confetti effect for celebrations
function createConfetti() {
    const colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'];
    const confettiCount = 50;
    
    for (let i = 0; i < confettiCount; i++) {
        const confetti = document.createElement('div');
        confetti.style.cssText = `
            position: fixed;
            width: 10px;
            height: 10px;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            top: -10px;
            left: ${Math.random() * 100}%;
            opacity: 1;
            transform: rotate(${Math.random() * 360}deg);
            pointer-events: none;
            z-index: 9999;
        `;
        
        document.body.appendChild(confetti);
        
        const duration = Math.random() * 3 + 2;
        const delay = Math.random() * 0.5;
        
        confetti.animate([
            { transform: `translateY(0) rotate(0deg)`, opacity: 1 },
            { transform: `translateY(${window.innerHeight + 10}px) rotate(${Math.random() * 720}deg)`, opacity: 0 }
        ], {
            duration: duration * 1000,
            delay: delay * 1000,
            easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
        }).onfinish = () => confetti.remove();
    }
}

// Particle background effect
function createParticles(container) {
    const particleCount = 30;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
            position: absolute;
            width: 2px;
            height: 2px;
            background: rgba(59, 130, 246, 0.5);
            border-radius: 50%;
            top: ${Math.random() * 100}%;
            left: ${Math.random() * 100}%;
            animation: float ${Math.random() * 10 + 5}s infinite ease-in-out;
        `;
        
        container.appendChild(particle);
    }
}

// Add CSS for particle animation
const style = document.createElement('style');
style.textContent = `
    @keyframes float {
        0%, 100% {
            transform: translateY(0) translateX(0);
            opacity: 0;
        }
        50% {
            opacity: 1;
        }
        100% {
            transform: translateY(-100px) translateX(${Math.random() * 100 - 50}px);
        }
    }
    
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-20px);
        }
    }
`;
document.head.appendChild(style);

// Initialize tooltips
document.querySelectorAll('[data-tooltip]').forEach(element => {
    const tooltip = document.createElement('span');
    tooltip.className = 'tooltip-text';
    tooltip.textContent = element.getAttribute('data-tooltip');
    element.classList.add('tooltip');
    element.appendChild(tooltip);
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"]');
        if (searchInput) searchInput.focus();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }
});

// Export functions for use in other scripts
window.ScholarMateUI = {
    showToast,
    copyToClipboard,
    validateForm,
    addLoadingState,
    animateProgressBar,
    typeWriter,
    createConfetti,
    createParticles
};
