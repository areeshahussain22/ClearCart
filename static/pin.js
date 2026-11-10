// Draw each PIN box as four candy bubbles: one fills for each digit typed.
// The real password input stays in place, so screen readers and keyboards use it as normal.
(function () {
  "use strict";
  function sync(input) {
    const field = input.closest(".pin-field");
    if (field) field.dataset.count = String(Math.min(4, input.value.length));
  }
  window.ccPinSync = sync;
  document.querySelectorAll(".pin-field input").forEach(function (input) {
    input.addEventListener("input", function () {
      input.value = input.value.replace(/\D/g, "").slice(0, 4);
      sync(input);
    });
    sync(input);
  });
})();
