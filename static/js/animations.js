// Animation utility functions
const animations = {
  fadeIn: (element, duration = 300) => {
    element.style.opacity = 0;
    element.style.display = "block";

    let start = null;
    const animate = (timestamp) => {
      if (!start) start = timestamp;
      const progress = timestamp - start;

      element.style.opacity = Math.min(progress / duration, 1);

      if (progress < duration) {
        window.requestAnimationFrame(animate);
      }
    };

    window.requestAnimationFrame(animate);
  },

  fadeOut: (element, duration = 300) => {
    let start = null;
    const initialOpacity = parseFloat(window.getComputedStyle(element).opacity);

    const animate = (timestamp) => {
      if (!start) start = timestamp;
      const progress = timestamp - start;

      element.style.opacity = Math.max(initialOpacity - progress / duration, 0);

      if (progress < duration) {
        window.requestAnimationFrame(animate);
      } else {
        element.style.display = "none";
      }
    };

    window.requestAnimationFrame(animate);
  },

  slideDown: (element, duration = 300) => {
    element.style.display = "block";
    const height = element.scrollHeight;
    element.style.height = "0px";
    element.style.overflow = "hidden";
    element.style.transition = `height ${duration}ms ease-in-out`;

    setTimeout(() => {
      element.style.height = height + "px";
    }, 10);

    setTimeout(() => {
      element.style.height = "";
      element.style.overflow = "";
      element.style.transition = "";
    }, duration);
  },

  slideUp: (element, duration = 300) => {
    const height = element.scrollHeight;
    element.style.height = height + "px";
    element.style.overflow = "hidden";
    element.style.transition = `height ${duration}ms ease-in-out`;

    setTimeout(() => {
      element.style.height = "0px";
    }, 10);

    setTimeout(() => {
      element.style.display = "none";
      element.style.height = "";
      element.style.overflow = "";
      element.style.transition = "";
    }, duration);
  },

  shake: (element, distance = 10, duration = 500) => {
    const originalPosition = element.style.transform || "translateX(0)";
    const steps = 6;
    const interval = duration / steps;

    let currentStep = 0;

    const shake = () => {
      if (currentStep >= steps) {
        element.style.transform = originalPosition;
        return;
      }

      const direction = currentStep % 2 === 0 ? distance : -distance;
      element.style.transform = `translateX(${direction}px)`;

      currentStep++;
      setTimeout(shake, interval);
    };

    shake();
  },

  pulse: (element, scale = 1.1, duration = 200) => {
    element.style.transition = `transform ${duration}ms ease-in-out`;
    element.style.transform = `scale(${scale})`;

    setTimeout(() => {
      element.style.transform = "scale(1)";
    }, duration);

    setTimeout(() => {
      element.style.transition = "";
    }, duration * 2);
  },
};

// Loading spinner animation
class LoadingSpinner {
  constructor(container) {
    this.container = container;
    this.spinner = document.createElement("div");
    this.spinner.className = "loading-spinner";
    this.setupStyles();
  }

  setupStyles() {
    const style = document.createElement("style");
    style.textContent = `
            .loading-spinner {
                width: 50px;
                height: 50px;
                border: 5px solid var(--border-color);
                border-top: 5px solid var(--primary-color);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
    document.head.appendChild(style);
  }

  show() {
    this.container.appendChild(this.spinner);
  }

  hide() {
    if (this.spinner.parentNode === this.container) {
      this.container.removeChild(this.spinner);
    }
  }
}

// Progress bar animation
class ProgressBar {
  constructor(container) {
    this.container = container;
    this.progress = 0;
    this.element = document.createElement("div");
    this.element.className = "progress-bar";
    this.setupStyles();
  }

  setupStyles() {
    const style = document.createElement("style");
    style.textContent = `
            .progress-bar {
                width: 100%;
                height: 4px;
                background-color: var(--border-color);
                position: relative;
                overflow: hidden;
            }
            
            .progress-bar::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                height: 100%;
                background-color: var(--primary-color);
                transition: width 0.3s ease-in-out;
            }
        `;
    document.head.appendChild(style);
  }

  setProgress(value) {
    this.progress = Math.min(Math.max(value, 0), 100);
    this.element.style.setProperty("--progress", `${this.progress}%`);
  }

  show() {
    this.container.appendChild(this.element);
  }

  hide() {
    if (this.element.parentNode === this.container) {
      this.container.removeChild(this.element);
    }
  }
}

// Export the animation utilities
export { animations, LoadingSpinner, ProgressBar };
