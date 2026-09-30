let toastTimer;

function showToast(title, message, type = "normal", duration = 3000) {
  const toastComponent = document.getElementById("toast-component");
  const toastTitle = document.getElementById("toast-title");
  const toastMessage = document.getElementById("toast-message");

  if (!toastComponent) {
    return;
  }

  // hapus class tipe sebelumnya
  toastComponent.classList.remove(
    "toast-success",
    "toast-error",
    "toast-normal",
  );

  // terapkan class baru berdasarkan tipe
  if (type === "success") {
    toastComponent.classList.add("toast-success");
  } else if (type === "error") {
    toastComponent.classList.add("toast-error");
  } else {
    toastComponent.classList.add("toast-normal");
  }

  // update content
  toastTitle.textContent = title;
  toastMessage.textContent = message;

  // cancel previous timer if the toast still show up
  clearTimeout(toastTimer);

  // animation appears
  if (!toastComponent.matches(":popover-open")) {
    toastComponent.showPopover();
    void toastComponent.offsetHeight; // force browser to count the style so that the transition runs
  }

  toastComponent.classList.remove("toast-hidden");
  toastComponent.classList.add("toast-show");

  toastTimer = setTimeout(() => {
    toastComponent.classList.remove("toast-show");
    toastComponent.classList.add("toast-hidden");
    toastTimer = setTimeout(() => toastComponent.hidePopover(), 300);
  }, duration);
}
