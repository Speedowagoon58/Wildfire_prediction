// Theme management class
class ThemeManager {
  constructor() {
    this.theme = localStorage.getItem("theme") || "light";
    this.init();
  }

  init() {
    // Apply initial theme
    this.applyTheme(this.theme);

    // Set up theme toggle button
    const themeToggle = document.querySelector(".theme-toggle");
    if (themeToggle) {
      themeToggle.addEventListener("click", () => this.toggleTheme());
      this.updateToggleButton(themeToggle);
    }

    // Listen for system theme changes
    if (window.matchMedia) {
      window.matchMedia("(prefers-color-scheme: dark)").addListener((e) => {
        if (!localStorage.getItem("theme")) {
          this.theme = e.matches ? "dark" : "light";
          this.applyTheme(this.theme);
        }
      });
    }
  }

  applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
    this.theme = theme;

    // Update toggle button if it exists
    const themeToggle = document.querySelector(".theme-toggle");
    if (themeToggle) {
      this.updateToggleButton(themeToggle);
    }

    // Dispatch theme change event
    window.dispatchEvent(new CustomEvent("themechange", { detail: { theme } }));
  }

  toggleTheme() {
    const newTheme = this.theme === "light" ? "dark" : "light";
    this.applyTheme(newTheme);
  }

  updateToggleButton(button) {
    // Update button icon and aria-label
    const icon = button.querySelector("i") || document.createElement("i");
    icon.className = `fas fa-${this.theme === "light" ? "moon" : "sun"}`;
    button.setAttribute(
      "aria-label",
      `Switch to ${this.theme === "light" ? "dark" : "light"} theme`
    );

    if (!button.contains(icon)) {
      button.appendChild(icon);
    }
  }

  // Get current theme
  getCurrentTheme() {
    return this.theme;
  }

  // Check if current theme is dark
  isDarkTheme() {
    return this.theme === "dark";
  }
}

// Create and export theme manager instance
const themeManager = new ThemeManager();
export default themeManager;

// Add theme toggle button to DOM if it doesn't exist
document.addEventListener("DOMContentLoaded", () => {
  if (!document.querySelector(".theme-toggle")) {
    const themeToggle = document.createElement("button");
    themeToggle.className = "theme-toggle";
    themeToggle.setAttribute("aria-label", "Toggle theme");
    document.body.appendChild(themeToggle);
    themeManager.init();
  }
});
