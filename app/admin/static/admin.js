// JARVIS Admin Dashboard JavaScript Helper
document.addEventListener("DOMContentLoaded", () => {
  // Modal open buttons
  document.querySelectorAll("[data-open-modal]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modalId = btn.getAttribute("data-open-modal");
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.classList.add("active");
        const firstInput = modal.querySelector("input:not([type='hidden']), textarea, select");
        if (firstInput) {
          setTimeout(() => firstInput.focus(), 60);
        }
      }
    });
  });

  // Modal close buttons
  document.querySelectorAll("[data-close-modal]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modal = btn.closest(".modal");
      if (modal) {
        modal.classList.remove("active");
      }
    });
  });

  // Close modal when clicking on backdrop
  document.querySelectorAll(".modal").forEach((modal) => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.remove("active");
      }
    });
  });

  // Keyboard Escape to close any active modal
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const activeModal = document.querySelector(".modal.active");
      if (activeModal) {
        activeModal.classList.remove("active");
      }
    }
  });

  // Form delete confirmation
  document.querySelectorAll("form.delete-form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const entityName = form.getAttribute("data-entity-name") || "this record";
      const confirmed = window.confirm(`Permanently delete ${entityName}?\nThis action cannot be undone.`);
      if (!confirmed) {
        e.preventDefault();
      }
    });
  });
});

// Expose CSRF token helper for client scripts or fetch requests
window.getCSRFToken = function () {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
};
