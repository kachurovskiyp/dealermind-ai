/* Keeps legacy knowledge-page logic independent from a visible select element. */
(() => {
  const originalQuery = document.querySelector.bind(document);
  const profileSelector = {
    value: "",
    insertAdjacentHTML() {},
    addEventListener() {},
  };
  document.querySelector = (selector) => (
    selector === "#profile-select" ? profileSelector : originalQuery(selector)
  );
})();
