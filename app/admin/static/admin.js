// JARVIS Admin Dashboard JavaScript Helper
document.addEventListener("DOMContentLoaded", () => {
  // Modal open buttons
  document.querySelectorAll("[data-open-modal]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modalId = btn.getAttribute("data-open-modal");
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.classList.add("active");
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

  // Close modal when clicking outside modal content
  document.querySelectorAll(".modal").forEach((modal) => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.remove("active");
      }
    });
  });

  // Form delete confirmation
  document.querySelectorAll("form.delete-form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const entityName = form.getAttribute("data-entity-name") || "this item";
      const confirmed = window.confirm(`Are you sure you want to delete ${entityName}? This action cannot be undone.`);
      if (!confirmed) {
        e.preventDefault();
      }
    });
  });
});
